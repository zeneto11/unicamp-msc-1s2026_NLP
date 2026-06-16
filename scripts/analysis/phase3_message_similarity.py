"""Phase 3 — Message Similarity.

Create semantic ``(Message)-[:SIMILAR_TO]->(Message)`` links from the Phase 2
embeddings using approximate nearest neighbours and a cosine threshold.

Inputs (neo4j/import/aletheia_pt_v2/):
    message_embeddings.npy
    message_embeddings_index.csv
    message_topics.csv          (optional, for the same_topic filter)

Output (neo4j/import/aletheia_pt_v2/):
    message_similarity.csv      source_message_id, target_message_id,
                                cosine_similarity, rank, method, embedding_model

FAISS is imported lazily; a brute-force numpy fallback is used when FAISS is not
installed. Embeddings from Phase 2 are already L2-normalized, so inner product
equals cosine similarity.
"""
import numpy as np
import pandas as pd
from loguru import logger

from scripts.analysis.config import CONFIG
from scripts.analysis.io_utils import write_artifact
from scripts.utils.logger import setup_logger


setup_logger(__file__)


def load_embeddings() -> tuple[np.ndarray, pd.Series]:
    """
    Load the Phase 2 embedding matrix and its message-id index.

    Args:
        None.

    Returns:
        Tuple of (embedding matrix, message_id Series aligned by row).
    """
    emb_path = CONFIG.artifact_dir / CONFIG.f_message_embeddings
    idx_path = CONFIG.artifact_dir / CONFIG.f_embeddings_index

    logger.info(f"Loading embeddings: {emb_path}")
    embeddings = np.load(emb_path).astype("float32")
    index = pd.read_csv(idx_path)["message_id"]

    if len(index) != len(embeddings):
        raise ValueError(
            f"Embedding rows ({len(embeddings)}) != index rows ({len(index)})."
        )
    return embeddings, index


def _search_faiss(embeddings: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
    """
    Run exact inner-product kNN search with FAISS.

    Args:
        embeddings: L2-normalized embedding matrix.
        k: Number of neighbours to retrieve (including self).

    Returns:
        Tuple of (similarity scores, neighbour indices).
    """
    import faiss

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)
    scores, neighbours = index.search(embeddings, k)
    return scores, neighbours


def _search_numpy(embeddings: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
    """
    Brute-force inner-product kNN fallback when FAISS is unavailable.

    Processes in row blocks to bound memory. Suitable for this dataset size but
    slower than FAISS for very large corpora.

    Args:
        embeddings: L2-normalized embedding matrix.
        k: Number of neighbours to retrieve (including self).

    Returns:
        Tuple of (similarity scores, neighbour indices).
    """
    logger.warning("FAISS missing; using brute-force numpy kNN fallback.")
    n = embeddings.shape[0]
    all_scores = np.empty((n, k), dtype="float32")
    all_idx = np.empty((n, k), dtype="int64")

    block = 1024
    for start in range(0, n, block):
        end = min(start + block, n)
        sims = embeddings[start:end] @ embeddings.T
        # Take the top-k columns per row (unsorted), then order them.
        part = np.argpartition(-sims, kth=k - 1, axis=1)[:, :k]
        rows = np.arange(end - start)[:, None]
        part_scores = sims[rows, part]
        order = np.argsort(-part_scores, axis=1)
        all_idx[start:end] = part[rows, order]
        all_scores[start:end] = part_scores[rows, order]

    return all_scores, all_idx


def build_similarity_edges(
    embeddings: np.ndarray, message_ids: pd.Series
) -> pd.DataFrame:
    """
    Build filtered SIMILAR_TO edges from nearest-neighbour search.

    Applies the cosine threshold, top_k limit, self-exclusion, and the optional
    same-topic filter from the configuration.

    Args:
        embeddings: L2-normalized embedding matrix.
        message_ids: Message ids aligned with the embedding rows.

    Returns:
        DataFrame of similarity edges ready for CSV export.
    """
    # Retrieve one extra neighbour to absorb the self-match.
    k = CONFIG.similarity_top_k + 1

    try:
        scores, neighbours = _search_faiss(embeddings, k)
    except ImportError:
        scores, neighbours = _search_numpy(embeddings, k)

    # Optional topic id per message for the same-topic filter.
    topic_of = {}
    if CONFIG.similarity_same_topic_only:
        mt = pd.read_csv(CONFIG.artifact_dir / CONFIG.f_message_topics)
        topic_of = dict(zip(mt["message_id"], mt["topic_id"]))

    ids = message_ids.values
    rows = []
    for i in range(len(ids)):
        rank = 0
        for score, j in zip(scores[i], neighbours[i]):
            # Exclude self-match.
            if CONFIG.similarity_exclude_same_message and j == i:
                continue
            # Apply the cosine threshold.
            if score < CONFIG.similarity_threshold:
                continue
            # Optional same-topic constraint.
            if CONFIG.similarity_same_topic_only:
                if topic_of.get(ids[i]) != topic_of.get(ids[j]):
                    continue

            rank += 1
            rows.append(
                {
                    "source_message_id": ids[i],
                    "target_message_id": ids[j],
                    "cosine_similarity": round(float(score), 6),
                    "rank": rank,
                    "method": CONFIG.similarity_method,
                    "embedding_model": CONFIG.embedding_model,
                }
            )
            if rank >= CONFIG.similarity_top_k:
                break

    logger.info(f"Built {len(rows)} SIMILAR_TO edges.")
    return pd.DataFrame(
        rows,
        columns=[
            "source_message_id",
            "target_message_id",
            "cosine_similarity",
            "rank",
            "method",
            "embedding_model",
        ],
    )


def main() -> None:
    """
    Run Phase 3 and write the message similarity artifact.

    Args:
        None.

    Returns:
        None.
    """
    logger.info("Starting Phase 3 — message similarity.")

    embeddings, message_ids = load_embeddings()
    edges = build_similarity_edges(embeddings, message_ids)
    write_artifact(edges, CONFIG.f_message_similarity)

    logger.info(f"Phase 3 complete: {len(edges)} similarity edges.")


if __name__ == "__main__":
    main()
