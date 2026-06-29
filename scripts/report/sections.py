"""Section builders for the Graph V2 Markdown report.

Each ``section_NN_*`` function consumes the loaded :class:`ReportData` plus a
shared ``ctx`` dict of precomputed aggregates and returns a markdown string,
saving any figures it needs as a side effect. The orchestrator in
``generate.py`` concatenates them in order.

Style targets (from the report spec): compact tables (4-7 columns, top-N rows),
plots only where they add value, and a short interpretation under each — what it
shows, why it matters, what question it answers.
"""
import re

import numpy as np
import pandas as pd
import networkx as nx
from loguru import logger

from scripts.report.config import CONFIG
from scripts.report.loader import ReportData
from scripts.report import viz


_HEX = re.compile(r"([0-9a-fA-F]{12,})")

# Emotions commonly read as negative-valence, used for polarity-leaning summaries.
_NEGATIVE_EMOTIONS = {"anger", "fear", "sadness", "disgust"}


def _short_ch(x) -> str:
    """
    Shorten a hashed channel id to its first 8 hex characters for display.

    Args:
        x: Channel id string.

    Returns:
        Compact channel label.
    """
    m = _HEX.search(str(x))
    return m.group(1)[:8] if m else str(x)[:10]


def _short_msg(x) -> str:
    """
    Shorten a hashed message id to ``<hash8>_<suffix>`` for display.

    Args:
        x: Message id string.

    Returns:
        Compact message label.
    """
    s = str(x)
    m = _HEX.search(s)
    head = m.group(1)[:8] if m else s[:8]
    suffix = s.split("_")[-1] if "_" in s else ""
    return f"{head}_{suffix}" if suffix else head


def _pct(x) -> str:
    """
    Format a 0-1 fraction as a one-decimal percentage string.

    Args:
        x: Fraction value.

    Returns:
        Percentage string such as '12.3%'.
    """
    return f"{100 * float(x):.1f}%"


def _dimensions_plot(dims: dict, title: str, filename: str) -> str:
    """
    Plot entity (node) and relation (edge) cardinalities of a graph version.

    Nodes and edges are coloured differently and drawn on a log scale so counts
    spanning orders of magnitude (hundreds → tens of thousands) stay readable.

    Args:
        dims: Mapping with ``nodes`` and ``edges`` dicts of label -> count.
        title: Plot title.
        filename: Output figure file name.

    Returns:
        Output figure file name.
    """
    node_color, edge_color = "#2e7d32", "#3b6ea5"
    labels, values, colors = [], [], []
    for label, count in dims["nodes"].items():
        labels.append(f"{label} (node)")
        values.append(count)
        colors.append(node_color)
    for label, count in dims["edges"].items():
        labels.append(f"{label} (edge)")
        values.append(count)
        colors.append(edge_color)

    # Largest at the top of the horizontal bar chart.
    series = pd.Series(values, index=labels).sort_values()
    colors = [colors[labels.index(i)] for i in series.index]
    return viz.bar(
        series, title, "count (log scale)", "", filename,
        color=colors, log=True,
    )


# ----------------------------------------------------------------------------
# Topic distinctiveness + size-normalized diversity
# ----------------------------------------------------------------------------
def _topic_distinctiveness(modeled: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Compute per-community topic lift and size-normalized topic diversity.

    ``lift(c, t) = (share of topic t within community c) / (share of t in the
    modeled corpus)`` identifies topics a community is built around, as opposed
    to the raw mode (which is just the globally largest topic almost everywhere).

    Distinct-topic *counts* grow mechanically with message volume (a rarefaction
    artifact), so diversity is also reported size-normalized: topics per 1k
    messages, Shannon entropy, and Pielou evenness.

    Args:
        modeled: Per-message frame restricted to non-noise topic assignments,
            carrying community_id and topic_id.

    Returns:
        Tuple of (diversity DataFrame indexed by community_id, distinctive-topics
        dict mapping community_id -> list of (topic_id, lift, message_count)).
    """
    m = modeled.dropna(subset=["community_id", "topic_id"]).copy()
    m["community_id"] = m["community_id"].astype(int)
    m["topic_id"] = m["topic_id"].astype(int)

    corpus_share = m["topic_id"].value_counts(normalize=True)

    rows, distinctive = [], {}
    for c, sub in m.groupby("community_id"):
        n = len(sub)
        counts = sub["topic_id"].value_counts()
        p = counts / n

        # Shannon entropy + Pielou evenness over this community's topic mix.
        ent = float(-(p * np.log(p)).sum())
        k = int((counts > 0).sum())
        evenness = float(ent / np.log(k)) if k > 1 else 0.0
        rows.append({
            "community_id": c,
            "distinct_topics": k,
            "topics_per_1k": round(k / n * 1000, 2),
            "topic_entropy": round(ent, 4),
            "topic_evenness": round(evenness, 4),
        })

        # Distinctive topics: over-represented vs corpus, with minimum support.
        supported = counts[counts >= CONFIG.lift_min_support].index
        lift = (p / corpus_share.reindex(p.index)).loc[p.index.isin(supported)]
        lift = lift[lift >= CONFIG.lift_min_lift].sort_values(ascending=False)
        distinctive[c] = [
            (int(t), float(l), int(counts[t]))
            for t, l in lift.head(CONFIG.distinctive_per_community).items()
        ]

    div = pd.DataFrame(rows).set_index("community_id")
    return div, distinctive


# ----------------------------------------------------------------------------
# Shared context
# ----------------------------------------------------------------------------
def build_context(data: ReportData) -> dict:
    """
    Precompute aggregates reused across multiple sections.

    Builds the channel interaction graph, the per-community profile table,
    inter-community links, and message->channel/community lookups so individual
    sections do not re-derive them.

    Args:
        data: Loaded report data.

    Returns:
        Dict of shared frames, graph objects, and headline metrics.
    """
    logger.info("Building shared report context.")
    msg = data.msg

    # --- Channel interaction graph (V1 INTERACTS_WITH), undirected weighted. ---
    graph = nx.Graph()
    for _, r in data.interacts_with.iterrows():
        w = float(r["interaction_weight"])
        if graph.has_edge(r["source"], r["target"]):
            graph[r["source"]][r["target"]]["weight"] += w
        else:
            graph.add_edge(r["source"], r["target"], weight=w)

    # --- Lookups. ---
    msg_to_channel = dict(zip(data.in_channel["message_id"], data.in_channel["channel_id"]))
    msg_to_comm = data.message_to_community
    ch_to_comm = data.channel_to_community

    # --- Dataset-channel flag per community. ---
    dataset_channels = set(
        data.channels.loc[data.channels["is_dataset_channel"] == True, "id"]  # noqa: E712
    )

    # --- Per-community message / user / topic / emotion aggregates. ---
    comm_msgs = msg.groupby("community_id").size().rename("messages")

    active = data.active_in.copy()
    active["community_id"] = active["channel_id"].map(ch_to_comm)
    comm_users = active.groupby("community_id")["user_id"].nunique().rename("users")

    # Topic diversity + distinctiveness. Raw distinct-topic counts are kept for
    # continuity, but size-normalized diversity (entropy/evenness/per-1k) and
    # per-community lift are the load-bearing metrics downstream.
    modeled = msg[msg["topic_id"].notna() & (msg["topic_id"] != CONFIG.noise_topic_id)]
    diversity, distinctive = _topic_distinctiveness(modeled)
    comm_topic_div = diversity["distinct_topics"].rename("topic_diversity")

    # Per-community noise rate: among messages that reached the topic model, the
    # share left in the outlier bucket. Surfaces uneven topic coverage.
    assigned = msg[msg["topic_id"].notna()]
    comm_noise = (
        assigned.assign(is_noise=assigned["topic_id"] == CONFIG.noise_topic_id)
        .groupby("community_id")["is_noise"].mean().rename("noise_rate")
    )

    # Mean polarity scores per community.
    comm_pol = msg.groupby("community_id")[["positive_score", "negative_score"]].mean()

    # Dominant non-neutral emotion + its share per community.
    def _dom_emotion(sub: pd.Series) -> str:
        counts = sub[sub != "neutral"].value_counts()
        return counts.index[0] if len(counts) else "neutral"

    comm_dom = msg.groupby("community_id")["dominant_emotion"].agg(_dom_emotion)

    # Intra-community average similarity.
    sim = data.similarity.copy()
    sim["src_comm"] = sim["source_message_id"].map(msg_to_comm)
    sim["tgt_comm"] = sim["target_message_id"].map(msg_to_comm)
    intra = sim[sim["src_comm"] == sim["tgt_comm"]]
    comm_sim = intra.groupby("src_comm")["cosine_similarity"].mean().rename("avg_similarity")
    comm_sim.index.name = "community_id"

    # Number of dataset channels (message-bearing) per community.
    cc = data.channel_community.copy()
    cc["is_dataset"] = cc["channel_id"].isin(dataset_channels)
    comm_dataset_ch = cc.groupby("community_id")["is_dataset"].sum().rename("dataset_channels")

    # --- Assemble the community profile. ---
    profile = data.communities.set_index("id")[
        ["size", "density", "modularity", "community_name", "descriptive_keywords"]
    ].copy()
    profile = profile.rename(columns={"size": "channels"})
    profile = profile.join([comm_dataset_ch, comm_msgs, comm_users,
                            comm_topic_div, comm_sim])
    # Size-normalized diversity metrics (entropy, evenness, topics per 1k).
    profile = profile.join(diversity[["topics_per_1k", "topic_entropy", "topic_evenness"]])
    profile = profile.join(comm_noise)
    profile = profile.join(comm_pol)
    profile["dominant_emotion"] = comm_dom
    profile["net_polarity"] = profile["positive_score"] - profile["negative_score"]
    profile = profile.fillna({
        "topic_diversity": 0, "avg_similarity": 0,
        "topics_per_1k": 0, "topic_entropy": 0, "topic_evenness": 0,
        "noise_rate": 0,
    })
    profile.index.name = "community_id"

    # --- Inter-community links (cross-community INTERACTS_WITH weight). ---
    iw = data.interacts_with.copy()
    iw["src_comm"] = iw["source"].map(ch_to_comm)
    iw["tgt_comm"] = iw["target"].map(ch_to_comm)
    cross = iw[(iw["src_comm"] != iw["tgt_comm"])
               & iw["src_comm"].notna() & iw["tgt_comm"].notna()].copy()
    cross["pair"] = cross.apply(
        lambda r: tuple(sorted((int(r["src_comm"]), int(r["tgt_comm"])))), axis=1
    )
    inter_links = (
        cross.groupby("pair")
        .agg(interaction_weight=("interaction_weight", "sum"),
             edges=("interaction_weight", "size"))
        .reset_index()
        .sort_values("interaction_weight", ascending=False)
    )

    # --- V1 / V2 graph dimensions (entity and relation cardinalities). ---
    def _rows(path) -> int:
        """Count CSV rows cheaply (single column), 0 if the file is absent."""
        return len(pd.read_csv(path, usecols=[0])) if path.exists() else 0

    v1 = CONFIG.v1_dir
    n_topics = int((data.topics["id"] != CONFIG.noise_topic_id).sum())
    v1_dims = {
        "nodes": {
            "Channel": len(data.channels),
            "User": int(data.users["id"].nunique()),
            "Message": len(msg),
        },
        "edges": {
            "POSTED": _rows(v1 / "posted.csv"),
            "IN_CHANNEL": len(data.in_channel),
            "ACTIVE_IN": len(data.active_in),
            "REPLIES_TO": _rows(v1 / "replies_to.csv"),
            "FORWARDED_FROM": _rows(v1 / "forwarded_from.csv"),
            "REPLIED_INTO": _rows(v1 / "replied_into.csv"),
            "INTERACTS_WITH": len(data.interacts_with),
        },
    }
    v2_dims = {
        "nodes": {
            "Community": len(data.communities),
            "Topic": n_topics,
        },
        "edges": {
            "BELONGS_TO": len(data.channel_community),
            "BELONGS_TO_TOPIC": len(data.message_topics),
            "DOMINATED_BY": len(data.community_topics),
            "SIMILAR_TO": len(data.similarity),
        },
    }

    return {
        "graph": graph,
        "msg_to_channel": msg_to_channel,
        "dataset_channels": dataset_channels,
        "profile": profile,
        "inter_links": inter_links,
        "sim": sim,                       # similarity with community columns attached
        "modeled": modeled,
        "distinctive": distinctive,       # community_id -> [(topic_id, lift, count)]
        "v1_dims": v1_dims,
        "v2_dims": v2_dims,
    }


# ----------------------------------------------------------------------------
# Section 1 — Executive Summary  (written last conceptually, placed first)
# ----------------------------------------------------------------------------
def section_01_summary(data: ReportData, ctx: dict) -> str:
    """
    Build the executive summary as concise headline bullets.

    Args:
        data: Loaded report data.
        ctx: Shared context.

    Returns:
        Markdown for the executive summary section.
    """
    profile = ctx["profile"]
    n_msg = len(data.msg)
    n_comm = len(data.communities)
    modularity = float(data.communities["modularity"].iloc[0])
    n_topics = int((data.topics["id"] != CONFIG.noise_topic_id).sum())
    noise_share = float(
        (data.message_topics["topic_id"] == CONFIG.noise_topic_id).mean()
    )
    n_sim = len(data.similarity)
    sim = ctx["sim"]
    inter_share = float((sim["src_comm"] != sim["tgt_comm"]).mean())

    emo_counts = data.msg["dominant_emotion"].value_counts()
    top_emos = [e for e in emo_counts.index if e != "neutral"][:3]

    biggest = profile.sort_values("messages", ascending=False).iloc[0]
    biggest_kw = str(biggest["community_name"]).split(" · ")[:3]

    n_dataset = int((data.channels["is_dataset_channel"] == True).sum())  # noqa: E712
    neutral_share = float((data.msg["dominant_emotion"] == "neutral").mean())

    return "\n".join([
        "## 1. Executive Summary",
        "",
        "- **Structure (V1).**",
        f"  - {len(data.channels)} channels ({n_dataset} core + external sources) and "
        f"{data.users['id'].nunique():,} users.",
        f"  - {data.interacts_with.shape[0]:,} channel-interaction edges (shared users, "
        "forwards, replies).",
        "- **Communities (V2 / Phase 1).**",
        f"  - Leiden finds **{n_comm} communities** over {int(profile['channels'].sum())} channels.",
        f"  - Modularity **{modularity:.2f}** — a clear, well-separated structure.",
        "- **Topics (V2 / Phase 2).**",
        f"  - **{n_topics} topics** from {len(data.message_topics):,} modeled messages.",
        f"  - {_pct(noise_share)} residual noise after outlier reassignment (down from ~48% "
        "default); each community has *characteristic* topics revealed by lift.",
        "- **Semantics (V2 / Phase 3).**",
        f"  - **{n_sim:,} near-duplicate message pairs** (cosine ≥ {CONFIG.similarity_threshold:.2f}).",
        f"  - {_pct(inter_share)} of them link *different* communities — measurable "
        "cross-group narrative reuse.",
        "- **Emotion (V2 / Phase 4).**",
        f"  - Dominant tone is **{', '.join(top_emos)}**.",
        f"  - {_pct(neutral_share)} of messages carry no lexicon emotion (neutral).",
        "- **Most active community.**",
        f"  - `C{int(biggest.name)}` with {int(biggest['messages']):,} messages — "
        f"{' · '.join(biggest_kw)}.",
        "",
        "> The graph is highly centralized: a few large channels and communities carry most "
        "messages. Communities have distinct thematic identities (anti-vaccine, "
        "alternative-medicine, geopolitical, religious-extremist) yet cross-post shared "
        "templates; tone is neutral-heavy with anger/fear leading among emotional messages.",
        "",
    ])


# ----------------------------------------------------------------------------
# Section 2 — Dataset & Graph Overview
# ----------------------------------------------------------------------------
def section_02_overview(data: ReportData, ctx: dict) -> str:
    """
    Build the dataset and V1-vs-V2 comparison overview.

    Args:
        data: Loaded report data.
        ctx: Shared context.

    Returns:
        Markdown for the overview section.
    """
    msg = data.msg
    start, end = msg["date_parsed"].min(), msg["date_parsed"].max()

    n_channels = len(data.channels)
    n_dataset = int((data.channels["is_dataset_channel"] == True).sum())  # noqa: E712
    n_users = data.users["id"].nunique()
    n_msg = len(msg)

    comparison = pd.DataFrame(
        [
            ["Node: Channel", f"{n_channels}", f"{n_channels}"],
            ["Node: User", f"{n_users:,}", f"{n_users:,}"],
            ["Node: Message", f"{n_msg:,}", f"{n_msg:,}"],
            ["Node: Community", "—", f"{len(data.communities)}"],
            ["Node: Topic", "—", f"{int((data.topics['id'] != CONFIG.noise_topic_id).sum())}"],
            ["Edge: structural", "POSTED, IN_CHANNEL, ACTIVE_IN, REPLIES_TO, FORWARDED_FROM", "(inherited)"],
            ["Edge: INTERACTS_WITH", f"{len(data.interacts_with):,}", "(inherited)"],
            ["Edge: BELONGS_TO", "—", f"{len(data.channel_community):,}"],
            ["Edge: BELONGS_TO_TOPIC", "—", f"{len(data.message_topics):,}"],
            ["Edge: SIMILAR_TO", "—", f"{len(data.similarity):,}"],
            ["Msg attr: emotion scores", "—", f"{len(data.emotions):,} messages"],
        ],
        columns=["Element", "Graph V1", "Graph V2 (adds)"],
    )

    # Monthly message volume.
    monthly = msg.groupby("month").size()
    fig = viz.line(
        monthly.to_frame("messages"),
        "Monthly message volume",
        "month", "messages", "overview_messages_over_time.png",
    )

    return "\n".join([
        "## 2. Dataset and Graph Overview",
        "",
        "The graph models a Portuguese misinformation Telegram corpus. **V1** captures "
        "*who said what, where, and to whom* (channels, users, messages, and their "
        "interaction edges). **V2** layers *meaning* on top: community structure, topics, "
        "semantic similarity, and emotion — without rebuilding any V1 node or edge.",
        "",
        f"- **Time range:** {start:%Y-%m-%d} → {end:%Y-%m-%d} (~{(end-start).days // 30} months)",
        f"- **Core channels:** {n_dataset} (the V1 interaction graph also includes "
        f"{n_channels - n_dataset} external forward/reply source channels)",
        "- **Missing data:** forwarding and reply metadata are sparse by nature "
        "(most messages are neither forwarded nor replies); this is expected, not corruption.",
        "",
        "### V1 vs V2 at a glance",
        "",
        viz.md_table(comparison, max_rows=20, floatfmt=".0f"),
        "",
        viz.md_image(fig, "Monthly message volume"),
        "",
        "_Activity is uneven across the 5-year span, with pronounced surges — useful "
        "context for the temporal analysis in Section 9._",
        "",
    ])


# ----------------------------------------------------------------------------
# Section 3 — Graph V1 Structural Analysis
# ----------------------------------------------------------------------------
def section_03_v1_structure(data: ReportData, ctx: dict) -> str:
    """
    Build the V1 structural analysis of the channel interaction graph.

    Args:
        data: Loaded report data.
        ctx: Shared context.

    Returns:
        Markdown for the V1 structural section.
    """
    g = ctx["graph"]
    n, m = g.number_of_nodes(), g.number_of_edges()
    degrees = [d for _, d in g.degree()]
    avg_deg = float(np.mean(degrees))
    med_deg = float(np.median(degrees))
    density = nx.density(g)
    components = list(nx.connected_components(g))
    largest = max(components, key=len)
    all_channels = set(data.channel_community["channel_id"])
    isolated = len(all_channels - set(g.nodes()))

    # Degree distribution figure.
    fig = viz.hist(
        pd.Series(degrees), "Channel degree distribution (INTERACTS_WITH)",
        "degree (number of connected channels)", "v1_degree_distribution.png", bins=30,
    )

    # Top channels by weighted degree (strength) + betweenness for bridges.
    strength = pd.Series(dict(g.degree(weight="weight")))
    btw = pd.Series(nx.betweenness_centrality(g, weight="weight", normalized=True))
    central = pd.DataFrame({
        "channel": [_short_ch(c) for c in strength.index],
        "community": [data.channel_to_community.get(c, "—") for c in strength.index],
        "degree": [g.degree(c) for c in strength.index],
        "weighted_degree": strength.values,
        "betweenness": btw.reindex(strength.index).values,
    }).sort_values("weighted_degree", ascending=False)

    stats = pd.DataFrame(
        [
            ["Channels in interaction graph", f"{n}"],
            ["Interaction edges (undirected)", f"{m:,}"],
            ["Average degree", f"{avg_deg:.1f}"],
            ["Median degree", f"{med_deg:.0f}"],
            ["Graph density", f"{density:.4f}"],
            ["Connected components", f"{len(components)}"],
            ["Largest component (channels)", f"{len(largest)} ({_pct(len(largest)/n)})"],
            ["Isolated channels", f"{isolated}"],
        ],
        columns=["Metric", "Value"],
    )

    # V1 entity / relation cardinalities + figure.
    dims = ctx["v1_dims"]
    dims_tbl = pd.DataFrame(
        [["Channel", "node", dims["nodes"]["Channel"], "actors — Telegram channels"],
         ["User", "node", dims["nodes"]["User"], "actors — message authors"],
         ["Message", "node", dims["nodes"]["Message"], "individual posts"],
         ["POSTED", "edge", dims["edges"]["POSTED"], "User → Message"],
         ["IN_CHANNEL", "edge", dims["edges"]["IN_CHANNEL"], "Message → Channel"],
         ["ACTIVE_IN", "edge", dims["edges"]["ACTIVE_IN"], "User → Channel (aggregated)"],
         ["REPLIES_TO", "edge", dims["edges"]["REPLIES_TO"], "Message → Message"],
         ["FORWARDED_FROM", "edge", dims["edges"]["FORWARDED_FROM"], "Message → source Channel"],
         ["REPLIED_INTO", "edge", dims["edges"]["REPLIED_INTO"], "Message → replied Channel"],
         ["INTERACTS_WITH", "edge", dims["edges"]["INTERACTS_WITH"], "Channel ↔ Channel (derived)"]],
        columns=["Element", "Type", "Count", "Meaning"],
    )
    fig_dims = _dimensions_plot(dims, "Graph V1 — entities and relations", "v1_graph_dimensions.png")

    return "\n".join([
        "## 3. Graph Version 1 — Basic Structural Analysis",
        "",
        "V1 is the structural layer: three entity types (Channel, User, Message) connected "
        "by authorship, membership, reply, and forwarding relations. From these, a derived "
        "`INTERACTS_WITH` edge projects the network onto a weighted channel-to-channel graph.",
        "",
        "### Entities and relations",
        "",
        viz.md_table(dims_tbl, max_rows=12, floatfmt=".0f"),
        "",
        viz.md_image(fig_dims, "Graph V1 entities and relations"),
        "",
        "_The graph is message-centric: `POSTED` and `IN_CHANNEL` scale with the 32k "
        "messages, while reply/forward edges are far sparser — most posts are standalone._",
        "",
        "### Channel interaction graph",
        "",
        "The remaining structural analysis runs on the `INTERACTS_WITH` projection, which "
        "summarizes shared users, forwards, and replies into weighted channel edges — the "
        "same graph community detection consumes in Phase 1.",
        "",
        viz.md_table(stats, floatfmt=".4f"),
        "",
        viz.md_image(fig, "Channel degree distribution"),
        "",
        "_The degree distribution is right-skewed: most channels connect to few others "
        "while a handful are hubs — the hallmark of a centralized diffusion network._",
        "",
        "### Most central channels",
        "",
        "Weighted degree measures total interaction strength; betweenness flags channels "
        "that sit on many shortest paths (structural bridges).",
        "",
        viz.md_table(central, max_rows=CONFIG.top_n_table, floatfmt=".4f"),
        "",
        f"_The graph is effectively one connected core ({_pct(len(largest)/n)} of channels "
        "in the largest component); high-betweenness channels are the brokers that hold "
        "otherwise distinct groups together — a question revisited as community bridges in Section 5._",
        "",
    ])


# ----------------------------------------------------------------------------
# Section 4 — Graph V2 Expanded
# ----------------------------------------------------------------------------
def section_04_v2_expanded(data: ReportData, ctx: dict) -> str:
    """
    Describe how V2 enriches V1 and summarize the added layers.

    Args:
        data: Loaded report data.
        ctx: Shared context.

    Returns:
        Markdown for the V2 expansion section.
    """
    fig_dims = _dimensions_plot(
        ctx["v2_dims"], "Graph V2 — added entities and relations", "v2_graph_dimensions.png"
    )

    return "\n".join([
        "## 4. Graph Version 2 — Expanded Structural and Semantic Analysis",
        "",
        "V2 keeps every V1 node and edge untouched and adds two new entity types "
        "(Community, Topic) plus semantic relations and per-message emotion scores. The "
        "plot below mirrors Section 3, showing only what each analysis phase *adds*:",
        "",
        viz.md_image(fig_dims, "Graph V2 added entities and relations"),
        "",
        f"_Enrichment is dominated by `BELONGS_TO_TOPIC` ({len(data.message_topics):,}) and "
        f"`SIMILAR_TO` ({len(data.similarity):,}) — message-level edges — while the new "
        "Community/Topic nodes are comparatively few but anchor the whole semantic layer._",
        "",
        "**What each phase adds**",
        "",
        "1. *Community detection* — partitions the channel interaction graph into structural "
        "groups (Phase 1).",
        "2. *Topic modeling* — BERTopic over multilingual embeddings assigns each modeled "
        "message a topic and rolls topics up to community dominance (Phase 2).",
        "3. *Message similarity* — the same embeddings become `SIMILAR_TO` edges, exposing "
        "near-duplicate / reused content (Phase 3).",
        "4. *Emotion scoring* — the Portuguese NRC lexicon attaches eight emotion scores, "
        "polarity, and a dominant emotion to every message (Phase 4).",
        "",
    ])


# ----------------------------------------------------------------------------
# Section 5 — Community Analysis
# ----------------------------------------------------------------------------
def section_05_communities(data: ReportData, ctx: dict) -> str:
    """
    Build basic and deeper community analysis.

    Args:
        data: Loaded report data.
        ctx: Shared context.

    Returns:
        Markdown for the community analysis section.
    """
    profile = ctx["profile"].copy()
    sizes = profile["channels"]

    # Size distribution figure (channels per community).
    size_series = sizes.sort_values(ascending=True)
    size_series.index = [f"C{int(i)}" for i in size_series.index]
    fig_size = viz.bar(
        size_series, "Channels per community", "channels", "community",
        "community_sizes.png",
    )

    # Messages per community — exposes the volume imbalance behind the structure.
    msg_series = (
        profile["messages"].fillna(0).sort_values(ascending=True)
    )
    msg_series.index = [f"C{int(i)}" for i in msg_series.index]
    fig_msgs = viz.bar(
        msg_series, "Messages per community", "messages", "community",
        "community_messages.png", color="#a5673b",
    )

    summary_stats = pd.DataFrame(
        [
            ["Communities", f"{len(profile)}"],
            ["Channels covered", f"{int(sizes.sum())}"],
            ["Mean size", f"{sizes.mean():.1f}"],
            ["Median size", f"{sizes.median():.0f}"],
            ["Size variance", f"{sizes.var():.1f}"],
            ["Largest / smallest", f"{int(sizes.max())} / {int(sizes.min())}"],
        ],
        columns=["Metric", "Value"],
    )

    # All communities by message volume.
    top = profile.sort_values("messages", ascending=False)
    top_tbl = pd.DataFrame({
        "community": [f"C{int(i)}" for i in top.index],
        "channels": top["channels"].astype(int).values,
        "messages": top["messages"].fillna(0).astype(int).values,
        "users": top["users"].fillna(0).astype(int).values,
        "density": top["density"].values,
        "keywords": [" · ".join(str(k).split(" · ")[:4]) for k in top["community_name"]],
    })

    # Strongest inter-community links.
    inter = ctx["inter_links"].head(CONFIG.top_n_table).copy()
    inter_tbl = pd.DataFrame({
        "community_pair": [f"C{a} ↔ C{b}" for a, b in inter["pair"]],
        "interaction_weight": inter["interaction_weight"].values,
        "bridging_edges": inter["edges"].astype(int).values,
    })

    # Bridge users: users active in channels spanning more than one community.
    active = data.active_in.copy()
    active["community_id"] = active["channel_id"].map(data.channel_to_community)
    user_span = active.groupby("user_id")["community_id"].nunique()
    bridge_users = int((user_span > 1).sum())

    return "\n".join([
        "## 5. Community Analysis",
        "",
        "### Basic statistics",
        "",
        viz.md_table(summary_stats),
        "",
        viz.md_image(fig_size, "Channels per community"),
        "",
        "_Community sizes are strongly imbalanced — a few large communities dominate the "
        "structure while several are small satellites._",
        "",
        viz.md_image(fig_msgs, "Messages per community"),
        "",
        "_Volume is even more skewed than channel count: the ranking by messages differs "
        "from the ranking by channels, so structural size does not equal activity._",
        "",
        "### Communities by message volume",
        "",
        viz.md_table(top_tbl, max_rows=20, floatfmt=".3f"),
        "",
        "_Message and user counts come only from the core channels; size (channels) "
        "additionally includes external forward/reply sources clustered with them._",
        "",
        "### Bridges between communities",
        "",
        "Cross-community `INTERACTS_WITH` weight reveals which communities are most "
        "tightly coupled — the strongest candidates for shared audiences or content flow.",
        "",
        viz.md_table(inter_tbl, max_rows=CONFIG.top_n_table, floatfmt=".1f"),
        "",
        f"- **{bridge_users:,} users** are active across more than one community, acting "
        "as human bridges that carry content between otherwise separate groups.",
        "",
        "_What this answers: the dominant communities are structurally central (largest, "
        "densest), and a measurable set of shared users plus weighted cross-links shows "
        "the communities are not isolated silos but a coupled ecosystem._",
        "",
    ])


# ----------------------------------------------------------------------------
# Section 6 — Topic Analysis
# ----------------------------------------------------------------------------
def section_06_topics(data: ReportData, ctx: dict) -> str:
    """
    Build basic and deeper topic analysis.

    Args:
        data: Loaded report data.
        ctx: Shared context.

    Returns:
        Markdown for the topic analysis section.
    """
    topics = data.topics
    real = topics[topics["id"] != CONFIG.noise_topic_id].copy()
    noise_share = float((data.message_topics["topic_id"] == CONFIG.noise_topic_id).mean())

    # Top topics by message count.
    top = real.sort_values("message_count", ascending=False).head(CONFIG.top_topics)
    top_tbl = pd.DataFrame({
        "topic": top["id"].astype(int).values,
        "messages": top["message_count"].astype(int).values,
        "label / keywords": [str(l) for l in top["label"]],
    })

    fig = viz.bar(
        pd.Series(top["message_count"].values[::-1],
                  index=[f"T{int(i)}" for i in top["id"].values[::-1]]),
        "Top topics by message count", "messages", "topic",
        "topic_top_counts.png",
    )

    label_of = dict(zip(topics["id"], topics["label"]))
    profile = ctx["profile"]

    # Most common (mode) topic per community + its plurality share. The mode is
    # usually just the globally largest topic, so its share is reported to show
    # how weak "dominance" actually is.
    ct = data.community_topics.merge(
        topics[["id", "label"]], left_on="topic_id", right_on="id", how="left"
    )
    dom = ct.sort_values(["community_id", "share"], ascending=[True, False])
    dom_top = (
        dom.groupby("community_id").head(1)
        .sort_values("message_count", ascending=False)
    )
    mode_tbl = pd.DataFrame({
        "community": [f"C{int(i)}" for i in dom_top["community_id"]],
        "mode_topic": dom_top["topic_id"].astype(int).values,
        "plurality": dom_top["share"].values,
        "label / keywords": [str(l) for l in dom_top["label"]],
    })
    # Sort alphabetically by community for consistent comparison with dist_tbl
    mode_tbl = mode_tbl.sort_values("community", key=lambda x: x.str.extract(r'C(\d+)')[0].astype(int)).reset_index(drop=True)
    max_plurality = float(dom_top["share"].max())

    # Distinctive topics per community (lift = community share / corpus share):
    # the topics a community is actually built around, not just its biggest one.
    prof_by_vol = profile.sort_values("messages", ascending=False)
    dist_rows = []
    for cid in prof_by_vol.index:
        items = ctx["distinctive"].get(int(cid), [])
        if not items:
            continue
        tid, lift, cnt = items[0]
        dist_rows.append({
            "community": f"C{int(cid)}",
            "topic": int(tid),
            "lift": round(lift, 1),
            "messages": int(cnt),
            "label / keywords": str(label_of.get(tid, "")),
        })
    dist_tbl = pd.DataFrame(dist_rows)
    # Sort alphabetically by community for consistent comparison with mode_tbl
    dist_tbl = dist_tbl.sort_values("community", key=lambda x: x.str.extract(r'C(\d+)')[0].astype(int)).reset_index(drop=True)

    # Noise reduced via outlier reassignment; report the residual and its spread.
    noise_lo = float(profile["noise_rate"].min())
    noise_hi = float(profile["noise_rate"].max())

    # Topic diversity per community (raw distinct-topic count). Kept for context,
    # but flagged as sample-size-driven — see Section 10 for the normalized view.
    div_series = profile["topic_diversity"].sort_values(ascending=True)
    div_series.index = [f"C{int(i)}" for i in div_series.index]
    fig_div = viz.bar(
        div_series, "Topic diversity per community (distinct topics)",
        "distinct topics", "community", "topic_diversity_by_community.png",
        color="#6a3ba5",
    )

    return "\n".join([
        "## 6. Topic Analysis",
        "",
        f"BERTopic produced **{len(real)} topics** from {len(data.message_topics):,} "
        "modeled messages. Default HDBSCAN leaves ~48% of short social-media messages "
        "as outliers — and those outliers are **not** shorter than clustered messages, "
        "so the bucket is a clustering artifact, not a data-quality signal. We therefore "
        "reassign outliers to their nearest topic above a cosine floor, leaving a residual "
        f"noise bucket of **{_pct(noise_share)}** of assignments (genuinely un-clusterable "
        "content).",
        "",
        "### Most frequent topics",
        "",
        viz.md_table(top_tbl, max_rows=CONFIG.top_topics),
        "",
        viz.md_image(fig, "Top topics by message count"),
        "",
        "_A few large topics capture mainstream narratives; the long tail of small topics "
        "reflects niche or fast-moving content._",
        "",
        "### Distinctive topics per community (lift)",
        "",
        "Lift = a topic's share inside a community divided by its share in the whole "
        "corpus. Unlike the raw mode, lift reveals what each community is *characteristically* "
        "about rather than which global topic happens to be largest.",
        "",
        viz.md_table(dist_tbl, max_rows=20, floatfmt=".1f"),
        "",
        "_These over-represented topics separate the communities into recognisable "
        "misinformation genres — anti-vaccine, alternative-medicine, geopolitical, "
        "religious-extremist — that the raw 'most common topic' completely hides._",
        "",
        "### Most common topic per community (for contrast)",
        "",
        viz.md_table(mode_tbl, max_rows=20, floatfmt=".3f"),
        "",
        f"- The modal topic captures at most **{_pct(max_plurality)}** of a community's "
        "messages — these are weak pluralities over a flat, long-tailed distribution, not "
        "true dominance. The same one or two globally-large topics top many communities, "
        "which is why the lift view above is the more informative cut.",
        "",
        "### Topic coverage and breadth",
        "",
        viz.md_image(fig_div, "Topic diversity per community"),
        "",
        f"- **Noise coverage is uneven:** the residual outlier rate ranges from "
        f"{_pct(noise_lo)} to {_pct(noise_hi)} across communities, so per-community topic "
        "figures rest on different fractions of each group's messages.",
        "- Distinct-topic *counts* rise with message volume — a rarefaction effect. "
        "Section 10 normalizes for size and shows breadth-per-message actually **falls** as "
        "communities grow.",
        "",
        "_What this answers: communities are thematically distinct once you control for the "
        "globally-popular topics (via lift); apparent 'shared dominance' is mostly an "
        "artifact of a few large topics plus a flat per-community distribution._",
        "",
    ])


# ----------------------------------------------------------------------------
# Section 7 — Semantic Similarity
# ----------------------------------------------------------------------------
def section_07_similarity(data: ReportData, ctx: dict) -> str:
    """
    Build basic and deeper semantic similarity analysis.

    Args:
        data: Loaded report data.
        ctx: Shared context.

    Returns:
        Markdown for the similarity section.
    """
    sim = ctx["sim"]
    scores = sim["cosine_similarity"]
    msg_to_channel = ctx["msg_to_channel"]

    fig = viz.hist(
        scores, "Distribution of message-pair cosine similarity",
        "cosine similarity", "similarity_score_distribution.png", bins=30,
    )

    stats = pd.DataFrame(
        [
            ["Similar pairs (edges)", f"{len(sim):,}"],
            ["Mean similarity", f"{scores.mean():.3f}"],
            ["Median similarity", f"{scores.median():.3f}"],
            ["Min / Max", f"{scores.min():.3f} / {scores.max():.3f}"],
            ["Intra-community pairs", f"{int((sim['src_comm']==sim['tgt_comm']).sum()):,}"],
            ["Cross-community pairs", f"{int((sim['src_comm']!=sim['tgt_comm']).sum()):,}"],
        ],
        columns=["Metric", "Value"],
    )

    # Top similar pairs.
    top = sim.sort_values("cosine_similarity", ascending=False).head(CONFIG.top_n_table)
    top_tbl = pd.DataFrame({
        "source": [_short_msg(s) for s in top["source_message_id"]],
        "target": [_short_msg(t) for t in top["target_message_id"]],
        "cosine": top["cosine_similarity"].values,
        "same_community": (top["src_comm"] == top["tgt_comm"]).values,
    })

    # Channels that most repeat similar content internally (same-channel edges).
    s2 = sim.copy()
    s2["src_ch"] = s2["source_message_id"].map(msg_to_channel)
    s2["tgt_ch"] = s2["target_message_id"].map(msg_to_channel)
    same_ch = s2[s2["src_ch"] == s2["tgt_ch"]]
    repeat = same_ch["src_ch"].value_counts().head(CONFIG.top_n_table)
    repeat_tbl = pd.DataFrame({
        "channel": [_short_ch(c) for c in repeat.index],
        "internal_similar_pairs": repeat.values,
    })

    # Central messages: appear in edges spanning the most distinct communities.
    endpoints = pd.concat([
        sim[["source_message_id", "tgt_comm"]].rename(
            columns={"source_message_id": "message_id", "tgt_comm": "other_comm"}),
        sim[["target_message_id", "src_comm"]].rename(
            columns={"target_message_id": "message_id", "src_comm": "other_comm"}),
    ])
    central = (
        endpoints.dropna().groupby("message_id")["other_comm"].nunique()
        .sort_values(ascending=False).head(CONFIG.top_n_table)
    )
    central_tbl = pd.DataFrame({
        "message": [_short_msg(m) for m in central.index],
        "linked_communities": central.values,
    })

    cross_share = float((sim["src_comm"] != sim["tgt_comm"]).mean())

    return "\n".join([
        "## 7. Semantic Similarity Analysis",
        "",
        f"Phase 3 retains message pairs with cosine ≥ {CONFIG.similarity_threshold:.2f} "
        "(top-5 neighbours each). Because the threshold is a hard floor, the score "
        "distribution starts there and decays toward 1.0.",
        "",
        viz.md_table(stats, floatfmt=".3f"),
        "",
        viz.md_image(fig, "Cosine similarity distribution"),
        "",
        f"_About **{_pct(cross_share)}** of similar pairs cross community boundaries: the "
        "same or near-identical content is being reposted across structurally distinct groups._",
        "",
        "### Strongest similar pairs",
        "",
        viz.md_table(top_tbl, max_rows=CONFIG.top_n_table, floatfmt=".3f"),
        "",
        "### Most semantically redundant channels",
        "",
        "Channels with many *internal* similar pairs repeat their own content most often.",
        "",
        viz.md_table(repeat_tbl, max_rows=CONFIG.top_n_table),
        "",
        "### Cross-community bridge messages",
        "",
        "Messages whose similar neighbours span the most communities act as semantic hubs "
        "— the same idea echoed everywhere.",
        "",
        viz.md_table(central_tbl, max_rows=CONFIG.top_n_table),
        "",
        "_What this answers: redundancy is concentrated in specific channels, and a small "
        "set of messages function as cross-community templates — a fingerprint of coordinated reuse._",
        "",
    ])


# ----------------------------------------------------------------------------
# Section 8 — Sentiment & Emotion
# ----------------------------------------------------------------------------
def section_08_emotion(data: ReportData, ctx: dict) -> str:
    """
    Build basic and deeper sentiment/emotion analysis.

    Args:
        data: Loaded report data.
        ctx: Shared context.

    Returns:
        Markdown for the emotion section.
    """
    msg = data.msg
    emotions = list(CONFIG.emotion_categories)

    # Dominant emotion distribution.
    dist = msg["dominant_emotion"].value_counts()
    fig_dist = viz.bar(
        dist.sort_values(), "Dominant emotion distribution (all messages)",
        "messages", "dominant emotion", "emotion_distribution.png",
    )

    # Emotion x community heatmap (share of dominant emotion within each community).
    share = (
        pd.crosstab(msg["community_id"], msg["dominant_emotion"], normalize="index")
        .reindex(columns=emotions + ["neutral"], fill_value=0)
    )
    # Label each community row with its top descriptive keywords so the emotional
    # profile reads on its own, without cross-referencing the community table.
    kw_map = {
        int(cid): " · ".join(str(name).split(" · ")[:3])
        for cid, name in zip(data.communities["id"], data.communities["community_name"])
    }
    share.index = [
        f"C{int(i)}: {kw_map[int(i)]}" if kw_map.get(int(i)) else f"C{int(i)}"
        for i in share.index
    ]
    fig_heat = viz.heatmap(
        share[emotions], "Emotion share by community (with descriptive keywords)",
        "emotion_by_community.png", cbar_label="share of messages",
    )

    # Communities with the highest concentration of each emotion.
    full_share = pd.crosstab(msg["community_id"], msg["dominant_emotion"], normalize="index")
    rows = []
    for e in emotions:
        if e in full_share.columns:
            cid = full_share[e].idxmax()
            rows.append([e, f"C{int(cid)}", full_share.loc[cid, e]])
    conc_tbl = pd.DataFrame(rows, columns=["emotion", "top_community", "share"])

    # Channels with the most distinctive (concentrated) emotion profile.
    ch_emo = pd.crosstab(msg["channel_id"], msg["dominant_emotion"], normalize="index")
    ch_counts = msg.groupby("channel_id").size()
    eligible = ch_counts[ch_counts >= 50].index
    ch_emo = ch_emo.loc[ch_emo.index.intersection(eligible)]
    ch_emo_real = ch_emo[[c for c in emotions if c in ch_emo.columns]]
    distinct = ch_emo_real.max(axis=1).sort_values(ascending=False).head(CONFIG.top_n_table)
    distinct_tbl = pd.DataFrame({
        "channel": [_short_ch(c) for c in distinct.index],
        "messages": ch_counts.reindex(distinct.index).astype(int).values,
        "top_emotion": ch_emo_real.loc[distinct.index].idxmax(axis=1).values,
        "share": distinct.values,
    })

    pos, neg = msg["positive_score"].mean(), msg["negative_score"].mean()

    # Surface neutral: it is excluded from the per-community "dominant emotion"
    # (which reports the leading *non-neutral* register), but it is frequently the
    # actual plurality, so the dominant-emotion labels overstate affect.
    neutral_share = float((msg["dominant_emotion"] == "neutral").mean())
    full_share_all = pd.crosstab(msg["community_id"], msg["dominant_emotion"], normalize="index")
    n_neutral_plurality = int((full_share_all.idxmax(axis=1) == "neutral").sum())
    n_comms = full_share_all.shape[0]

    return "\n".join([
        "## 8. Sentiment and Emotion Analysis",
        "",
        f"All {len(data.emotions):,} messages carry NRC emotion scores. Mean polarity is "
        f"**{pos:.2f} positive / {neg:.2f} negative** — the corpus leans slightly negative.",
        "",
        viz.md_image(fig_dist, "Dominant emotion distribution"),
        "",
        f"> **Read the dominant-emotion labels with care.** `neutral` (no lexicon match) is "
        f"the single largest class at **{_pct(neutral_share)}** of messages and is the actual "
        f"plurality in **{n_neutral_plurality}/{n_comms}** communities. The per-community and "
        "per-channel 'dominant emotion' reported below is the leading *non-neutral* register, "
        "so it overstates how emotionally-charged the average message is.",
        "",
        "_Among non-neutral emotions, anger, trust, and anticipation lead; surprise and joy "
        "are rare._",
        "",
        "### Emotion profile by community",
        "",
        viz.md_image(fig_heat, "Emotion share by community"),
        "",
        "_Communities differ in tone: some are anger-dominated, others trust- or "
        "anticipation-leaning, despite drawing on overlapping topics._",
        "",
        "### Where each emotion concentrates",
        "",
        viz.md_table(conc_tbl, max_rows=10, floatfmt=".3f"),
        "",
        "### Channels with the most distinctive emotional profile",
        "",
        "Channels (≥50 messages) where a single emotion captures the largest share — the "
        "clearest emotional 'signatures'.",
        "",
        viz.md_table(distinct_tbl, max_rows=CONFIG.top_n_table, floatfmt=".3f"),
        "",
        "_What this answers: emotion is not uniform — specific communities and channels "
        "specialize in specific affective registers, which Section 10 ties back to topics._",
        "",
    ])


# ----------------------------------------------------------------------------
# Section 9 — Temporal Analysis
# ----------------------------------------------------------------------------
def section_09_temporal(data: ReportData, ctx: dict) -> str:
    """
    Build temporal analysis of volume, community activity, and emotion.

    Args:
        data: Loaded report data.
        ctx: Shared context.

    Returns:
        Markdown for the temporal section.
    """
    msg = data.msg.copy()
    emotions = list(CONFIG.emotion_categories)

    # Community activity over time (all communities).
    pivot = msg.pivot_table(
        index="month", columns="community_id", values="message_id",
        aggfunc="count", fill_value=0,
    )
    pivot.columns = [f"C{int(c)}" for c in pivot.columns]
    fig_comm = viz.line(
        pivot, "Monthly activity by community",
        "month", "messages", "temporal_community_activity.png",
    )

    # Dominant emotion over time (monthly share, stacked area).
    emo_month = (
        pd.crosstab(msg["month"], msg["dominant_emotion"], normalize="index")
        .reindex(columns=emotions, fill_value=0)
    )
    # Keep readable: bucket sparse months are fine; index is sorted YYYY-MM strings.
    fig_emo = viz.stacked_area(
        emo_month, "Emotion composition over time (monthly share)",
        "month", "share of messages", "temporal_emotion_share.png",
    )

    # Quarterly emotion trends — coarser bins + un-stacked lines make each
    # emotion's direction (rising/falling) far easier to read than the area chart.
    msg["quarter"] = msg["date_parsed"].dt.to_period("Q").astype(str)
    # Show every emotion (including the rare joy/disgust/surprise), not just the
    # leading few — the per-quarter normalization is unchanged.
    emo_q = (
        pd.crosstab(msg["quarter"], msg["dominant_emotion"], normalize="index")
        .reindex(columns=emotions, fill_value=0)
    )
    fig_q = viz.quarter_line(
        emo_q, "Emotion share by quarter (all emotions)",
        "share of messages", "temporal_emotion_quarterly.png",
    )

    # Early vs late shift: first 12 months vs last 12 months of activity.
    dates = msg["date_parsed"]
    early_cut = dates.min() + pd.DateOffset(months=12)
    late_cut = dates.max() - pd.DateOffset(months=12)
    early = msg[dates < early_cut]["dominant_emotion"].value_counts(normalize=True)
    late = msg[dates >= late_cut]["dominant_emotion"].value_counts(normalize=True)
    emo_cols = list(CONFIG.emotion_categories)
    early = early.reindex(emo_cols, fill_value=0)
    late = late.reindex(emo_cols, fill_value=0)
    delta = (late - early) * 100
    trend_tbl = pd.DataFrame({
        "emotion": emo_cols,
        "early %": (early.values * 100),
        "late %": (late.values * 100),
        "change (pp)": delta.values,
    }).sort_values("change (pp)", key=lambda s: s.abs(), ascending=False)

    def _movement(emotion: str) -> str:
        """Phrase one emotion's early→late shift in percentage points."""
        d = float(delta.get(emotion, 0.0))
        verb = "rose" if d >= 0 else "fell"
        return f"{emotion} {verb} {abs(d):.1f} pp"

    movers = ", ".join(_movement(e) for e in trend_tbl["emotion"].head(2))

    # Sentiment volatility per community: std of monthly net polarity.
    msg["net"] = msg["positive_score"] - msg["negative_score"]
    monthly_net = msg.pivot_table(index="month", columns="community_id",
                                  values="net", aggfunc="mean")
    volatility = monthly_net.std().sort_values(ascending=False)
    vol_tbl = pd.DataFrame({
        "community": [f"C{int(i)}" for i in volatility.index],
        "net_polarity_volatility": volatility.values,
        "mean_net_polarity": monthly_net.mean().reindex(volatility.index).values,
    })

    return "\n".join([
        "## 9. Temporal Analysis",
        "",
        "Message timestamps (2020–2025) let us track how structure and tone evolve.",
        "",
        "### Community activity over time",
        "",
        viz.md_image(fig_comm, "Monthly activity by community"),
        "",
        "_Communities rise and fall at different times — activity is event-driven, not "
        "steady, and leadership of the conversation shifts between groups._",
        "",
        "### Emotion over time",
        "",
        viz.md_image(fig_emo, "Monthly emotion composition"),
        "",
        "_The emotional mix is not stable: periods of elevated anger/fear alternate with "
        "calmer trust/anticipation phases, suggesting reactive responses to external events._",
        "",
        "### Emotion shift, quarterly",
        "",
        "The monthly area chart shows churn but hides direction. Aggregating to quarters and "
        "drawing each emotion as its own line makes net rises and falls explicit.",
        "",
        viz.md_image(fig_q, "Emotion share by quarter"),
        "",
        f"Comparing the first 12 months of activity with the last 12: **{movers}** (largest "
        "movers). Full breakdown:",
        "",
        viz.md_table(trend_tbl, max_rows=10, floatfmt=".1f"),
        "",
        "_What this answers: beyond month-to-month noise, the corpus shows a directional "
        "emotional drift — some registers structurally gain ground while others recede._",
        "",
        "### Sentiment volatility by community",
        "",
        "Standard deviation of monthly net polarity (positive − negative) measures "
        "emotional stability: high values = volatile mood, low = consistent tone.",
        "",
        viz.md_table(vol_tbl, max_rows=20, floatfmt=".4f"),
        "",
        "_What this answers: some communities keep a stable emotional profile while others "
        "swing sharply — the volatile ones are the most reactive to events._",
        "",
    ])


def _pearson_ci(r: float, n: int, z: float = 1.96) -> tuple[float, float]:
    """
    Approximate 95% confidence interval for a Pearson r via Fisher's z.

    With only ~12 communities, point correlations are very uncertain; the CI
    makes that explicit instead of quoting a bare r.

    Args:
        r: Pearson correlation coefficient.
        n: Number of observations.
        z: Normal critical value (1.96 for ~95%).

    Returns:
        (low, high) correlation bounds, clipped to [-1, 1].
    """
    if n < 4 or abs(r) >= 1.0:
        return (r, r)
    zr = np.arctanh(r)
    se = 1.0 / np.sqrt(n - 3)
    lo, hi = np.tanh(zr - z * se), np.tanh(zr + z * se)
    return (float(np.clip(lo, -1, 1)), float(np.clip(hi, -1, 1)))


# ----------------------------------------------------------------------------
# Section 10 — Cross-Layer Analysis
# ----------------------------------------------------------------------------
def section_10_cross_layer(data: ReportData, ctx: dict) -> str:
    """
    Combine structural, topical, semantic, and emotional layers.

    Args:
        data: Loaded report data.
        ctx: Shared context.

    Returns:
        Markdown for the cross-layer section.
    """
    msg = data.msg
    profile = ctx["profile"].copy()
    emotions = list(CONFIG.emotion_categories)

    # Emotion x topic heatmap for the top topics.
    real = msg[msg["topic_id"].notna() & (msg["topic_id"] != CONFIG.noise_topic_id)]
    top_topics = real["topic_id"].value_counts().head(10).index
    sub = real[real["topic_id"].isin(top_topics)]
    et = (
        pd.crosstab(sub["topic_id"], sub["dominant_emotion"], normalize="index")
        .reindex(columns=emotions, fill_value=0)
    )
    et.index = [f"T{int(t)}: {str(data.topic_label.get(int(t), '')).split(' · ')[0]}"
                for t in et.index]
    fig_et = viz.heatmap(
        et, "Dominant emotion by topic (top topics)",
        "crosslayer_emotion_by_topic.png", cbar_label="share",
    )

    # Community-level correlation among layer metrics. Both the raw distinct-topic
    # count and the size-normalized diversity are included so the sampling
    # confound is visible rather than hidden.
    metrics = profile[["messages", "users", "topic_diversity", "topics_per_1k",
                       "topic_evenness", "avg_similarity", "negative_score"]].copy()
    metrics = metrics.rename(columns={
        "negative_score": "neg_polarity",
        "topic_diversity": "topic_count",
        "topics_per_1k": "topics_per_1k",
        "topic_evenness": "evenness",
    }).astype(float)
    corr = metrics.corr()
    fig_corr = viz.heatmap(
        corr, "Community-level metric correlations",
        "crosslayer_correlation.png", cmap="coolwarm", cbar_label="Pearson r",
    )

    # Scatter: community size vs raw distinct-topic count (the rarefaction trap).
    fig_sc = viz.scatter(
        profile["messages"].astype(float), profile["topic_diversity"].astype(float),
        [f"C{int(i)}" for i in profile.index],
        "Community message volume vs distinct topic count",
        "messages", "distinct topics", "crosslayer_size_vs_diversity.png",
    )

    # Correlations with 95% CIs (n is small, so report the interval).
    n = len(profile)
    r_count = float(metrics["messages"].corr(metrics["topic_count"]))
    r_norm = float(metrics["messages"].corr(metrics["topics_per_1k"]))
    r_even = float(metrics["messages"].corr(metrics["evenness"]))
    r_neg_sim = float(metrics["neg_polarity"].corr(metrics["avg_similarity"]))
    ci_count, ci_norm = _pearson_ci(r_count, n), _pearson_ci(r_norm, n)

    return "\n".join([
        "## 10. Cross-Layer Analysis",
        "",
        "Combining the four layers exposes relationships no single layer shows.",
        "",
        "### Emotion × Topic",
        "",
        viz.md_image(fig_et, "Dominant emotion by topic"),
        "",
        "_Topics carry distinct emotional signatures — some narratives are reliably "
        "anger-driven, others fear- or trust-driven, regardless of which community posts them._",
        "",
        "### Community-level correlations",
        "",
        f"> **Caveat:** each correlation below is over only **n = {n} communities**, so "
        "the 95% confidence intervals are wide. Read these as directional, not precise.",
        "",
        viz.md_image(fig_corr, "Community metric correlations"),
        "",
        viz.md_image(fig_sc, "Community size vs distinct topic count"),
        "",
        "**Does size drive thematic diversity? Only as an artifact.**",
        "",
        f"- Volume vs distinct topic *count*: **r = {r_count:.2f}** "
        f"(95% CI {ci_count[0]:.2f}–{ci_count[1]:.2f}). But a topic *count* mechanically "
        "grows with sample size (rarefaction): more messages hit more topic buckets.",
        f"- Volume vs **topics per 1k messages**: **r = {r_norm:.2f}** "
        f"(95% CI {ci_norm[0]:.2f}–{ci_norm[1]:.2f}) — the sign **flips**. Normalized for "
        "size, larger communities are *less* diverse per message, not more.",
        f"- Volume vs topic **evenness** (Pielou): **r = {r_even:.2f}** — essentially flat. "
        "Diversity of the topic *mix* is unrelated to how active a community is.",
        f"- Negative polarity vs internal similarity: **r = {r_neg_sim:.2f}** — "
        + ("more negative communities also repeat content more" if r_neg_sim > 0.2 else
           "emotional negativity and content redundancy look largely independent")
        + " (but see the n caveat).",
        "",
        "_What this answers: the headline 'bigger communities are more diverse' is a "
        "sampling artifact — once you divide by message volume it reverses. Emotion aligns "
        "with topic far more than with raw community size._",
        "",
    ])


# ----------------------------------------------------------------------------
# Section 11 — Statistical Summary
# ----------------------------------------------------------------------------
def section_11_statistics(data: ReportData, ctx: dict) -> str:
    """
    Build a compact descriptive-statistics summary across communities.

    Args:
        data: Loaded report data.
        ctx: Shared context.

    Returns:
        Markdown for the statistical summary section.
    """
    profile = ctx["profile"].copy()
    n = len(profile)
    cols = {
        "channels": "channels",
        "messages": "messages",
        "users": "users",
        "topic_diversity": "topic_count",
        "topics_per_1k": "topics_per_1k",
        "topic_evenness": "evenness",
        "avg_similarity": "avg_sim",
        "net_polarity": "net_polarity",
    }
    desc = profile[list(cols)].rename(columns=cols).astype(float).describe().T
    desc = desc[["mean", "std", "min", "50%", "max"]].rename(columns={"50%": "median"})
    desc.insert(0, "metric", desc.index)

    return "\n".join([
        "## 11. Statistical Summary",
        "",
        f"Descriptive statistics across the {n} communities (each community is one "
        "observation). This quantifies the imbalance described qualitatively above.",
        "",
        viz.md_table(desc, max_rows=10, floatfmt=".2f"),
        "",
        f"> With **n = {n}**, community-level summaries and correlations are low-power: "
        "standard deviations are large and any single community can move a statistic. The "
        "figures describe *this* corpus; they do not support strong population-level claims.",
        "",
        "_Large standard deviations relative to means (especially for messages and users) "
        "confirm a heavy-tailed structure: a few communities dominate raw volume. Note the "
        "split in the diversity metrics — the distinct-topic *count* is heavy-tailed, but "
        "evenness (the size-normalized mix) is tight, underlining that 'breadth' is mostly "
        "a volume effect._",
        "",
    ])


# ----------------------------------------------------------------------------
# Section 12 — Key Findings
# ----------------------------------------------------------------------------
def section_12_findings(data: ReportData, ctx: dict) -> str:
    """
    Distil the analysis into titled, evidence-backed findings.

    Args:
        data: Loaded report data.
        ctx: Shared context.

    Returns:
        Markdown for the key findings section.
    """
    profile = ctx["profile"]
    sim = ctx["sim"]
    modularity = float(data.communities["modularity"].iloc[0])
    cross_share = float((sim["src_comm"] != sim["tgt_comm"]).mean())
    noise_share = float((data.message_topics["topic_id"] == CONFIG.noise_topic_id).mean())
    biggest = profile.sort_values("messages", ascending=False).iloc[0]
    biggest_share = float(biggest["messages"]) / float(profile["messages"].sum())
    neutral_share = float((data.msg["dominant_emotion"] == "neutral").mean())
    neg_lead = data.msg["dominant_emotion"].value_counts()
    top_emo = [e for e in neg_lead.index if e != "neutral"][0]
    pos_m = float(data.msg["positive_score"].mean())
    neg_m = float(data.msg["negative_score"].mean())

    # Distinctiveness coverage + a representative lift figure. Use the max lift
    # among the larger communities (those shown in the Section 6 table) so the
    # cited number matches the table rather than an extreme from a 2-channel group.
    n_distinctive = sum(1 for v in ctx["distinctive"].values() if v)
    items = [(c, t, lift, n) for c, lst in ctx["distinctive"].items() for (t, lift, n) in lst]
    big_comms = set(
        int(i) for i in profile.sort_values("messages", ascending=False)
        .head(CONFIG.top_communities).index
    )
    top_lift = max((lift for c, _, lift, _ in items if int(c) in big_comms), default=0.0)

    # Size-normalized diversity correlation (the rarefaction reversal).
    m = profile.astype({"messages": float, "topics_per_1k": float})
    r_norm = float(m["messages"].corr(m["topics_per_1k"]))

    findings = [
        ("Well-separated community structure",
         f"Leiden modularity = {modularity:.2f} across {len(data.communities)} communities.",
         "The channel network has genuine, non-random group structure — communities are a "
         "meaningful unit of analysis, not an artefact.",
         "V2 / Phase 1"),
        ("Activity is highly concentrated",
         f"The largest community alone holds {_pct(biggest_share)} of all messages.",
         "A handful of channels/communities drive the corpus; moderation or study effort "
         "targeted there covers most of the volume.",
         "V1 structure + V2 / Phase 1"),
        ("Communities have distinct thematic identities",
         f"{n_distinctive} communities carry topics over-represented vs the corpus (lift up "
         f"to ×{top_lift:.0f}) — e.g. anti-vaccine, alternative-medicine, geopolitical, and "
         "religious-extremist clusters.",
         "Beneath a few globally-popular topics, the groups specialise in recognisable "
         "misinformation genres — visible via lift, hidden by the raw modal topic.",
         "V2 / Phase 2"),
        ("Narratives are also reused across communities",
         f"{_pct(cross_share)} of {len(sim):,} near-duplicate pairs cross community lines.",
         "Distinct identities coexist with shared templates: the same content is repackaged "
         "across structurally separate groups — consistent with coordinated diffusion.",
         "V2 / Phases 2 & 3"),
        ("Tone is neutral-heavy with a mild negative lean",
         f"`neutral` is the plurality ({_pct(neutral_share)}); among non-neutral messages "
         f"'{top_emo}' leads and mean negative polarity ({neg_m:.2f}) marginally exceeds "
         f"positive ({pos_m:.2f}).",
         "Affective framing skews to anger/fear when present, but most messages carry no "
         "lexicon emotion — the negative lean is real but modest.",
         "V2 / Phase 4"),
        ("Topic diversity is a sample-size artifact, not a real effect",
         f"Distinct-topic count rises with volume, but topics-per-message *falls* "
         f"(r = {r_norm:.2f}) and evenness is flat.",
         "Larger communities are not more thematically diverse once normalized for activity; "
         "the raw count correlation is rarefaction.",
         "V2 / Cross-layer"),
        ("Topic noise was a clustering artifact, now controlled",
         f"Default HDBSCAN flagged ~48% of messages as outliers though they are not shorter "
         f"than clustered ones; reassignment leaves a {_pct(noise_share)} residual.",
         "The original noise rate reflected default parameters on short text, not data "
         "quality; reassigned outliers are lower-confidence and flagged as such.",
         "V2 / Phase 2"),
    ]

    out = ["## 12. Key Findings", ""]
    for i, (title, evidence, interp, src) in enumerate(findings, 1):
        out += [
            f"### {i}. {title}",
            f"- **Evidence:** {evidence}",
            f"- **Interpretation:** {interp}",
            f"- **Supported by:** {src}",
            "",
        ]
    return "\n".join(out)


# ----------------------------------------------------------------------------
# Section 13 — Limitations
# ----------------------------------------------------------------------------
def section_13_limitations(data: ReportData, ctx: dict) -> str:
    """
    State the main methodological limitations.

    Args:
        data: Loaded report data.
        ctx: Shared context.

    Returns:
        Markdown for the limitations section.
    """
    noise_share = float((data.message_topics["topic_id"] == CONFIG.noise_topic_id).mean())
    return "\n".join([
        "## 13. Limitations",
        "",
        "- **Outlier reassignment.** Default HDBSCAN flags ~48% of messages as outliers; we "
        "reassign those above an embedding-cosine floor to their nearest topic, leaving a "
        f"{_pct(noise_share)} residual. Reassigned messages are lower-confidence (low "
        "assignment probability) and should be read as best-fit, not firm, topic membership.",
        "- **Low statistical power (n = 12).** Community-level statistics and correlations "
        "rest on twelve observations; confidence intervals are wide and individual "
        "communities can swing a coefficient.",
        "- **Lexicon emotion.** NRC is a bag-of-words lexicon: it misses negation, "
        "sarcasm, irony, and context, and Portuguese coverage is imperfect; `neutral` (no "
        "match) is the largest class. Scores are indicative, not ground truth.",
        "- **Language detection.** Non-Portuguese messages are dropped via langdetect before "
        "modeling, which is itself imperfect on very short text.",
        "- **Community detection scope.** Communities are detected on the channel "
        "interaction graph only; users and messages inherit a community via their channel.",
        "- **Similarity truncation.** `SIMILAR_TO` keeps only pairs ≥ "
        f"{CONFIG.similarity_threshold:.2f} with top-5 neighbours, so redundancy counts are "
        "lower bounds.",
        "- **Incomplete reply/forward recovery.** Many reply/forward sources are external "
        "or unrecovered, so cross-channel structure is partially observed.",
        "- **Descriptive keywords ≠ topics.** Per-community keywords (Phase 1) are TF-IDF "
        "descriptors, not the formal BERTopic topics of Phase 2.",
        "",
    ])


# ----------------------------------------------------------------------------
# Appendix — oversized tables kept out of the main body
# ----------------------------------------------------------------------------
def section_99_appendix(data: ReportData, ctx: dict) -> str:
    """
    Build the appendix with the full community table and emotion matrix.

    Args:
        data: Loaded report data.
        ctx: Shared context.

    Returns:
        Markdown for the appendix section.
    """
    profile = ctx["profile"].copy()
    full = pd.DataFrame({
        "community": [f"C{int(i)}" for i in profile.index],
        "channels": profile["channels"].astype(int).values,
        "messages": profile["messages"].fillna(0).astype(int).values,
        "users": profile["users"].fillna(0).astype(int).values,
        "topics": profile["topic_diversity"].astype(int).values,
        "dominant_emotion": profile["dominant_emotion"].values,
        "keywords": [" · ".join(str(k).split(" · ")[:5]) for k in profile["community_name"]],
    })

    # Full emotion-share matrix by community.
    emotions = list(CONFIG.emotion_categories)
    share = (
        pd.crosstab(data.msg["community_id"], data.msg["dominant_emotion"], normalize="index")
        .reindex(columns=emotions + ["neutral"], fill_value=0)
    )
    share.insert(0, "community", [f"C{int(i)}" for i in share.index])

    return "\n".join([
        "## Appendix",
        "",
        "### A1. All communities",
        "",
        viz.md_table(full, max_rows=50),
        "",
        "### A2. Full emotion-share matrix by community",
        "",
        viz.md_table(share, max_rows=50, floatfmt=".3f"),
        "",
    ])


# Ordered section builders consumed by generate.py.
SECTIONS = [
    section_01_summary,
    section_02_overview,
    section_03_v1_structure,
    section_04_v2_expanded,
    section_05_communities,
    section_06_topics,
    section_07_similarity,
    section_08_emotion,
    section_09_temporal,
    section_10_cross_layer,
    section_11_statistics,
    section_12_findings,
    section_13_limitations,
    section_99_appendix,
]
