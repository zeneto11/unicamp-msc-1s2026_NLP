"""Phase 2 — Topic Modeling.

Extract latent topics from Portuguese messages, assign each modeled message a
topic, and summarise topic dominance per community.

Inputs:
    data/aletheia_clean_pt.csv                       (message text + metadata)
    neo4j/import/aletheia_pt_v2/channel_community.csv (Phase 1 assignment)

Outputs (neo4j/import/aletheia_pt_v2/):
    message_embeddings.npy          float matrix, one row per modeled message
    message_embeddings_index.csv    message_id order for the embedding matrix
    topics.csv                      id, label, keywords, coherence_score,
                                    message_count, embedding
    message_topics.csv              message_id, topic_id, probability, rank
    community_topics.csv            community_id, topic_id, message_count, share

Heavy dependencies are imported lazily: sentence-transformers (embeddings) and
BERTopic (topic model). Embeddings are normalized so Phase 3 can use cosine.
"""
import numpy as np
import pandas as pd
from loguru import logger

from scripts.analysis.config import CONFIG
from scripts.analysis.io_utils import write_artifact, list_to_pipe
from scripts.utils.logger import setup_logger


setup_logger(__file__)



def preprocess_messages() -> pd.DataFrame:
    """
    Load messages and apply modeling-specific filtering for topic modeling.

    Reads the canonical text_clean column (hashes, URLs, and binary noise already
    stripped in scripts/dataset/cleaning.py) and drops empty, too-short
    (< min_words), and duplicated boilerplate messages. These filters are
    modeling-specific and deliberately not part of canonical cleaning, so the
    graph keeps every real message.

    Args:
        None.

    Returns:
        DataFrame with message_id, channel_id, and cleaned text columns.
    """
    logger.info(f"Loading messages: {CONFIG.raw_csv}")
    df = pd.read_csv(
        CONFIG.raw_csv,
        usecols=["message_id", "channel_id", "text_clean"],
    )

    # text_clean is the canonical analysis text (hashes, URLs, and binary noise
    # already stripped in scripts/dataset/cleaning.py). Modeling-specific
    # filtering below stays here, not in canonical cleaning, so the graph keeps
    # every real message.
    df["text"] = df["text_clean"].fillna("").astype(str).str.strip()

    before = len(df)

    # Drop empty messages (pure-URL messages are now empty after cleaning).
    df = df[df["text"].str.len() > 0]

    # Drop messages below the minimum word count.
    df = df[df["text"].str.split().str.len() >= CONFIG.min_words]

    # Drop duplicated boilerplate, keeping the first occurrence.
    df = df.drop_duplicates(subset=["text"], keep="first")

    logger.info(f"Preprocessing kept {len(df)}/{before} messages for modeling.")
    return df[["message_id", "channel_id", "text"]].reset_index(drop=True)


def generate_embeddings(texts: list[str]) -> np.ndarray:
    """
    Embed messages with the configured multilingual sentence transformer.

    Embeddings are L2-normalized so cosine similarity reduces to inner product
    in Phase 3.

    Args:
        texts: Message texts to embed.

    Returns:
        Float32 embedding matrix of shape (len(texts), dim).
    """
    from sentence_transformers import SentenceTransformer

    logger.info(f"Embedding {len(texts)} messages with {CONFIG.embedding_model}")
    model = SentenceTransformer(CONFIG.embedding_model)
    embeddings = model.encode(
        texts,
        batch_size=64,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    return embeddings.astype("float32")


def run_topic_model(texts: list[str], embeddings: np.ndarray):
    """
    Fit BERTopic over precomputed embeddings.

    Args:
        texts: Message texts.
        embeddings: Precomputed message embeddings.

    Returns:
        Tuple of (fitted BERTopic model, topic ids per message, probabilities).
    """
    from bertopic import BERTopic

    logger.info("Fitting BERTopic model.")
    topic_model = BERTopic(
        embedding_model=CONFIG.embedding_model,
        calculate_probabilities=True,
        verbose=True,
    )
    topics, probs = topic_model.fit_transform(texts, embeddings=embeddings)
    logger.info(f"BERTopic produced {len(set(topics))} topics (incl. noise).")
    return topic_model, topics, probs


def build_topic_records(topic_model) -> pd.DataFrame:
    """
    Build Topic node records from a fitted BERTopic model.

    Args:
        topic_model: Fitted BERTopic model.

    Returns:
        DataFrame of topic node records ready for CSV export.
    """
    info = topic_model.get_topic_info()

    # Topic embeddings as a pipe-delimited string for LOAD CSV split() parsing.
    topic_embeddings = getattr(topic_model, "topic_embeddings_", None)

    rows = []
    for _, r in info.iterrows():
        topic_id = int(r["Topic"])

        # Top keywords for this topic, dropping empty c-TF-IDF tokens.
        keywords = [w for w, _ in topic_model.get_topic(topic_id) or [] if w]
        label = " · ".join(keywords[:4]) if keywords else f"topic_{topic_id}"

        embedding = ""
        if topic_embeddings is not None and topic_id != CONFIG.noise_topic_id:
            # topic_embeddings_ is indexed by topic_id offset by the noise topic.
            idx = topic_id + 1 if CONFIG.noise_topic_id == -1 else topic_id
            if 0 <= idx < len(topic_embeddings):
                embedding = list_to_pipe(
                    [round(float(x), 6) for x in topic_embeddings[idx]]
                )

        rows.append(
            {
                "id": topic_id,
                "label": label,
                "keywords": list_to_pipe(keywords[:10]),
                "coherence_score": "",  # optional; compute with gensim if needed
                "message_count": int(r["Count"]),
                "embedding": embedding,
            }
        )

    return pd.DataFrame(rows)


def build_message_topics(
    message_ids: pd.Series, topics: list[int], probs
) -> pd.DataFrame:
    """
    Build per-message topic assignment records.

    Args:
        message_ids: Message ids aligned with the modeled texts.
        topics: Primary topic id per message.
        probs: Per-message topic probabilities (matrix or vector).

    Returns:
        DataFrame with message_id, topic_id, probability, rank.
    """
    probs = np.asarray(probs)

    # Probability of the assigned primary topic; rank is 1 for the primary topic.
    if probs.ndim == 2:
        probability = probs.max(axis=1)
    else:
        probability = probs

    out = pd.DataFrame(
        {
            "message_id": message_ids.values,
            "topic_id": [int(t) for t in topics],
            "probability": np.round(np.nan_to_num(probability, nan=0.0), 6),
            "rank": 1,
        }
    )
    return out


def aggregate_community_topics(message_topics: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate message-level topics into community topic dominance records.

    Joins each modeled message to its community via the Phase 1 channel
    assignment, then keeps topics whose share exceeds the dominance threshold.

    Args:
        message_topics: Per-message topic assignments with channel_id attached.

    Returns:
        DataFrame with community_id, topic_id, message_count, share.
    """
    channel_community = pd.read_csv(
        CONFIG.artifact_dir / CONFIG.f_channel_community
    )
    channel_to_comm = dict(
        zip(channel_community["channel_id"], channel_community["community_id"])
    )

    df = message_topics.copy()
    df["community_id"] = df["channel_id"].map(channel_to_comm)

    # Exclude noise topic and messages whose channel has no community.
    df = df[df["topic_id"] != CONFIG.noise_topic_id]
    df = df.dropna(subset=["community_id"])

    counts = (
        df.groupby(["community_id", "topic_id"]).size().reset_index(name="message_count")
    )
    totals = df.groupby("community_id").size().rename("community_total")
    counts = counts.join(totals, on="community_id")
    counts["share"] = (counts["message_count"] / counts["community_total"]).round(6)

    # Keep only dominant topics per the configured share threshold.
    dominant = counts[counts["share"] >= CONFIG.topic_dominance_min_share].copy()
    dominant["community_id"] = dominant["community_id"].astype(int)

    return dominant[["community_id", "topic_id", "message_count", "share"]]


def main() -> None:
    """
    Run Phase 2 and write topic, message-topic, and community-topic artifacts.

    Args:
        None.

    Returns:
        None.
    """
    logger.info("Starting Phase 2 — topic modeling.")

    messages = preprocess_messages()
    texts = messages["text"].tolist()

    embeddings = generate_embeddings(texts)

    # Persist embeddings and their message-id order for Phase 3 reuse.
    CONFIG.ensure_artifact_dir()
    np.save(CONFIG.artifact_dir / CONFIG.f_message_embeddings, embeddings)
    write_artifact(messages[["message_id"]], CONFIG.f_embeddings_index)

    topic_model, topics, probs = run_topic_model(texts, embeddings)

    topic_records = build_topic_records(topic_model)
    message_topics = build_message_topics(messages["message_id"], topics, probs)

    # Attach channel id for community aggregation, then drop it for the edge CSV.
    message_topics_with_channel = message_topics.merge(
        messages[["message_id", "channel_id"]], on="message_id", how="left"
    )
    community_topics = aggregate_community_topics(message_topics_with_channel)

    write_artifact(topic_records, CONFIG.f_topics)
    write_artifact(message_topics, CONFIG.f_message_topics)
    write_artifact(community_topics, CONFIG.f_community_topics)

    logger.info(
        f"Phase 2 complete: {len(topic_records)} topics, "
        f"{len(message_topics)} assignments, {len(community_topics)} dominance edges."
    )


if __name__ == "__main__":
    main()
