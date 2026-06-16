"""Phase 1 — Community Detection.

Detect structural communities of channels from the V1 channel interaction layer
``(Channel)-[:INTERACTS_WITH]->(Channel)`` and generate descriptive keywords for
each community.

Inputs  (read from V1 outputs):
    neo4j/import/aletheia_pt_v1/interacts_with.csv   (channel interaction edges)
    data/aletheia_clean_pt.csv                       (message text for keywords)

Outputs (written to neo4j/import/aletheia_pt_v2/):
    communities.csv         id, size, density, modularity, algorithm,
                            community_name, descriptive_keywords, keyword_method
    channel_community.csv   channel_id, community_id

Heavy dependencies are imported lazily so this module stays importable without
them:  python-igraph + leidenalg (Leiden), or networkx (Louvain fallback),
and scikit-learn (descriptive keywords).
"""
import pandas as pd
from loguru import logger

from scripts.analysis.config import CONFIG
from scripts.analysis.io_utils import write_artifact, list_to_pipe
from scripts.utils.logger import setup_logger


setup_logger(__file__)

# A compact Portuguese stopword list for descriptive keyword extraction. Noise
# from hashes/URLs is already stripped upstream in the canonical text_clean
# column (scripts/dataset/cleaning.py); these are genuine high-frequency words.
PT_STOPWORDS = [
    "a", "o", "e", "é", "de", "do", "da", "dos", "das", "em", "no", "na",
    "nos", "nas", "um", "uma", "uns", "umas", "para", "por", "com", "sem",
    "que", "se", "as", "os", "ao", "aos", "à", "às", "mais", "mas", "como",
    "ou", "já", "não", "sim", "também", "muito", "muita", "ser", "está",
    "este", "esta", "isso", "isto", "esse", "essa", "the", "to",
    "br", "me", "eu", "você", "ele", "ela", "nós",
    "eles", "elas", "foi", "são", "tem", "vai", "está", "pra", "pro", "lá",
    "aqui", "todo", "toda", "todos", "todas", "seu", "sua", "seus", "suas",
]

# Keep only alphabetic tokens (incl. Portuguese accents), 2+ chars. This drops
# pure-digit and digit-prefixed fragments (e.g. binary-corruption remnants like
# "5m5") that survive as tokens but carry no descriptive value.
KEYWORD_TOKEN_PATTERN = r"(?u)\b[^\W\d_][^\W\d_]+\b"


def load_interaction_edges() -> pd.DataFrame:
    """
    Load the V1 channel interaction edges from the prepared CSV.

    Args:
        None.

    Returns:
        DataFrame with source, target, and interaction_weight columns.
    """
    path = CONFIG.v1_import_dir / "interacts_with.csv"
    logger.info(f"Loading interaction edges: {path}")

    edges = pd.read_csv(path)

    # Keep only the columns needed to build the weighted channel graph.
    edges = edges[["source", "target", CONFIG.interaction_weight_property]].copy()
    edges = edges.rename(columns={CONFIG.interaction_weight_property: "weight"})

    logger.info(f"Loaded interaction edges rows={len(edges)}")
    return edges


def _undirected_weighted(edges: pd.DataFrame) -> pd.DataFrame:
    """
    Collapse directed interaction edges into undirected weighted edges.

    Args:
        edges: Directed edges with source, target, weight.

    Returns:
        DataFrame with one row per unordered channel pair and summed weight.
    """
    # Order each pair so reciprocal directed edges collapse onto one row.
    a = edges[["source", "target", "weight"]].copy()
    lo = a[["source", "target"]].min(axis=1)
    hi = a[["source", "target"]].max(axis=1)
    a["u"] = lo
    a["v"] = hi

    undirected = (
        a.groupby(["u", "v"], as_index=False)["weight"].sum()
        .rename(columns={"u": "source", "v": "target"})
    )
    return undirected


def detect_communities(edges: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Detect channel communities using the configured algorithm preference.

    Tries Leiden (python-igraph + leidenalg) first, then Louvain. Raises a clear
    ImportError if no supported backend is installed.

    Args:
        edges: Directed interaction edges with source, target, weight.

    Returns:
        Tuple of (assignment DataFrame [channel_id, community_id], metrics dict).
        metrics carries algorithm, modularity, and per-community density.
    """
    undirected = _undirected_weighted(edges)

    for algorithm in CONFIG.community_algorithms:
        try:
            if algorithm == "leiden":
                return _detect_leiden(undirected)
            if algorithm == "louvain":
                return _detect_louvain(undirected)
        except ImportError as exc:
            logger.warning(f"Algorithm '{algorithm}' unavailable: {exc}")

    raise ImportError(
        "No community detection backend available. Install either "
        "'python-igraph leidenalg' (Leiden) or 'networkx' (Louvain)."
    )


def _build_igraph(undirected: pd.DataFrame):
    """
    Build a weighted python-igraph graph from undirected channel edges.

    Args:
        undirected: Undirected edges with source, target, weight.

    Returns:
        Tuple of (igraph.Graph, list of channel-id vertex names).
    """
    import igraph as ig

    # Assign a contiguous integer index to each channel id.
    nodes = sorted(set(undirected["source"]).union(undirected["target"]))
    index = {name: i for i, name in enumerate(nodes)}

    graph = ig.Graph()
    graph.add_vertices(len(nodes))
    graph.add_edges(
        list(zip(undirected["source"].map(index), undirected["target"].map(index)))
    )
    graph.es["weight"] = undirected["weight"].tolist()
    return graph, nodes


def _detect_leiden(undirected: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Detect communities with the Leiden algorithm.

    Args:
        undirected: Undirected edges with source, target, weight.

    Returns:
        Tuple of (assignment DataFrame, metrics dict).
    """
    import leidenalg

    graph, nodes = _build_igraph(undirected)

    partition = leidenalg.find_partition(
        graph,
        leidenalg.ModularityVertexPartition,
        weights="weight",
        seed=CONFIG.random_seed,
    )

    membership = partition.membership
    assignment = pd.DataFrame(
        {"channel_id": nodes, "community_id": membership}
    )
    metrics = {
        "algorithm": "leiden",
        "modularity": float(partition.modularity),
        "density": _community_density(graph, membership),
    }
    logger.info(
        f"Leiden found {len(set(membership))} communities "
        f"modularity={metrics['modularity']:.4f}"
    )
    return assignment, metrics


def _detect_louvain(undirected: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Detect communities with the Louvain algorithm via networkx.

    Args:
        undirected: Undirected edges with source, target, weight.

    Returns:
        Tuple of (assignment DataFrame, metrics dict).
    """
    import networkx as nx
    from networkx.algorithms.community import louvain_communities, modularity

    graph = nx.Graph()
    for _, row in undirected.iterrows():
        graph.add_edge(row["source"], row["target"], weight=row["weight"])

    communities = louvain_communities(
        graph, weight="weight", seed=CONFIG.random_seed
    )

    rows = []
    density = {}
    for cid, members in enumerate(communities):
        sub = graph.subgraph(members)
        density[cid] = nx.density(sub)
        for channel in members:
            rows.append({"channel_id": channel, "community_id": cid})

    assignment = pd.DataFrame(rows)
    metrics = {
        "algorithm": "louvain",
        "modularity": float(modularity(graph, communities, weight="weight")),
        "density": density,
    }
    logger.info(
        f"Louvain found {len(communities)} communities "
        f"modularity={metrics['modularity']:.4f}"
    )
    return assignment, metrics


def _community_density(graph, membership: list) -> dict:
    """
    Compute the edge density of each community subgraph (igraph backend).

    Args:
        graph: igraph.Graph used for detection.
        membership: Per-vertex community assignment.

    Returns:
        Mapping of community_id to subgraph density.
    """
    density = {}
    for cid in set(membership):
        vertices = [i for i, m in enumerate(membership) if m == cid]
        sub = graph.subgraph(vertices)
        density[cid] = sub.density()
    return density


def descriptive_keywords(assignment: pd.DataFrame) -> dict:
    """
    Generate descriptive keywords per community from member channel messages.

    Uses TF-IDF over the concatenated message text of each community. Falls back
    to an empty mapping if scikit-learn is not installed.

    Args:
        assignment: DataFrame with channel_id and community_id.

    Returns:
        Mapping of community_id to a list of descriptive keyword strings.
    """
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
    except ImportError:
        logger.warning("scikit-learn missing; skipping descriptive keywords.")
        return {}

    logger.info(f"Loading message text for keywords: {CONFIG.raw_csv}")
    messages = pd.read_csv(
        CONFIG.raw_csv, usecols=["channel_id", "text_clean"]
    )
    messages["text_clean"] = messages["text_clean"].fillna("")

    # Attach the community of each message via its channel.
    channel_to_comm = dict(zip(assignment["channel_id"], assignment["community_id"]))
    messages["community_id"] = messages["channel_id"].map(channel_to_comm)
    messages = messages.dropna(subset=["community_id"])

    # Concatenate all message text per community into one document.
    docs = (
        messages.groupby("community_id")["text_clean"]
        .apply(lambda s: " ".join(s))
    )

    vectorizer = TfidfVectorizer(
        stop_words=PT_STOPWORDS,
        token_pattern=KEYWORD_TOKEN_PATTERN,
        max_features=5000,
        ngram_range=(1, 1),
    )
    matrix = vectorizer.fit_transform(docs.values)
    terms = vectorizer.get_feature_names_out()

    keywords = {}
    for i, community_id in enumerate(docs.index):
        row = matrix[i].toarray().ravel()
        top_idx = row.argsort()[::-1][: CONFIG.descriptive_keywords_top_n]
        keywords[int(community_id)] = [terms[j] for j in top_idx if row[j] > 0]

    return keywords


def build_community_records(
    assignment: pd.DataFrame, metrics: dict, keywords: dict
) -> pd.DataFrame:
    """
    Build the Community node records combining sizes, metrics, and keywords.

    Args:
        assignment: DataFrame with channel_id and community_id.
        metrics: Detection metrics dict (algorithm, modularity, density).
        keywords: Mapping of community_id to descriptive keyword list.

    Returns:
        DataFrame of community node records ready for CSV export.
    """
    sizes = assignment.groupby("community_id").size()

    rows = []
    for community_id, size in sizes.items():
        community_id = int(community_id)
        kw = keywords.get(community_id, [])
        rows.append(
            {
                "id": community_id,
                "size": int(size),
                "density": round(float(metrics["density"].get(community_id, 0.0)), 6),
                "modularity": round(metrics["modularity"], 6),
                "algorithm": metrics["algorithm"],
                "community_name": " · ".join(kw) if kw else f"community_{community_id}",
                "descriptive_keywords": list_to_pipe(kw),
                "keyword_method": "tfidf_descriptive_keywords",
            }
        )

    return pd.DataFrame(rows).sort_values("size", ascending=False).reset_index(drop=True)


def main() -> None:
    """
    Run Phase 1 and write Community node and BELONGS_TO edge artifacts.

    Args:
        None.

    Returns:
        None.
    """
    logger.info("Starting Phase 1 — community detection.")

    edges = load_interaction_edges()
    assignment, metrics = detect_communities(edges)
    keywords = descriptive_keywords(assignment)
    communities = build_community_records(assignment, metrics, keywords)

    write_artifact(communities, CONFIG.f_communities)
    write_artifact(
        assignment.rename(columns={"community_id": "community_id"}),
        CONFIG.f_channel_community,
    )

    logger.info(
        f"Phase 1 complete: {len(communities)} communities, "
        f"{len(assignment)} channel assignments."
    )


if __name__ == "__main__":
    main()
