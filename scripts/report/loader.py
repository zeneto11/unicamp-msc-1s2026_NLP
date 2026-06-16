"""Load V1/V2 artifacts and assemble the in-memory model for the report.

All graph data is read from the import CSVs (the same files the Neo4j loaders
ingest). The centrepiece is a single enriched per-message DataFrame that joins
structural, community, topic, and emotion layers so the analytical sections can
slice one table instead of repeatedly re-joining.
"""
from dataclasses import dataclass

import pandas as pd
from loguru import logger

from scripts.report.config import CONFIG


@dataclass
class ReportData:
    """
    Container for every artifact frame plus the enriched message frame.

    Args:
        None (populated by load_report_data).

    Returns:
        ReportData instance holding all loaded and derived frames.
    """
    # V1 structural frames.
    channels: pd.DataFrame
    users: pd.DataFrame
    messages: pd.DataFrame
    interacts_with: pd.DataFrame
    active_in: pd.DataFrame
    in_channel: pd.DataFrame

    # V2 enrichment frames.
    communities: pd.DataFrame
    channel_community: pd.DataFrame
    topics: pd.DataFrame
    message_topics: pd.DataFrame
    community_topics: pd.DataFrame
    similarity: pd.DataFrame
    emotions: pd.DataFrame

    # Derived: one row per dataset message with all layers joined.
    msg: pd.DataFrame

    # Lookup maps reused across sections.
    channel_to_community: dict
    message_to_community: dict
    topic_label: dict


def _read(path, **kwargs) -> pd.DataFrame:
    """
    Read a CSV artifact with a log line and a clear error if it is missing.

    Args:
        path: Path to the CSV file.
        **kwargs: Extra keyword arguments forwarded to pandas.read_csv.

    Returns:
        Loaded DataFrame.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"Required artifact missing: {path}. Run the V1 graph prep and the "
            f"analysis phases (1-4) before generating the report."
        )
    df = pd.read_csv(path, **kwargs)
    logger.info(f"Loaded {path.name} rows={len(df)}")
    return df


def _build_enriched_messages(
    messages: pd.DataFrame,
    in_channel: pd.DataFrame,
    channel_community: pd.DataFrame,
    message_topics: pd.DataFrame,
    emotions: pd.DataFrame,
) -> pd.DataFrame:
    """
    Join structural, community, topic, and emotion layers per message.

    Args:
        messages: V1 message frame (id-based).
        in_channel: message_id -> channel_id edges.
        channel_community: channel_id -> community_id assignment.
        message_topics: message_id -> topic_id assignment.
        emotions: per-message emotion scores and dominant emotion.

    Returns:
        Enriched message DataFrame keyed by message_id.
    """
    msg = messages.rename(columns={"id": "message_id"}).copy()

    # Parse timestamps once; month is already a 'YYYY-MM' string in the source.
    msg["date_parsed"] = pd.to_datetime(msg["date_parsed"], errors="coerce")

    # message -> channel -> community.
    msg = msg.merge(in_channel, on="message_id", how="left")
    channel_to_comm = dict(
        zip(channel_community["channel_id"], channel_community["community_id"])
    )
    msg["community_id"] = msg["channel_id"].map(channel_to_comm)

    # message -> topic (modeled subset only; others stay NaN).
    msg = msg.merge(
        message_topics[["message_id", "topic_id", "probability"]],
        on="message_id",
        how="left",
    )

    # message -> emotion scores + dominant emotion.
    msg = msg.merge(emotions, on="message_id", how="left")

    logger.info(
        f"Enriched message frame: {len(msg)} rows, "
        f"{msg['community_id'].notna().sum()} with community, "
        f"{msg['topic_id'].notna().sum()} with topic, "
        f"{msg['dominant_emotion'].notna().sum()} with emotion."
    )
    return msg


def load_report_data() -> ReportData:
    """
    Load all V1/V2 artifacts and build the enriched message frame.

    Args:
        None.

    Returns:
        Fully populated ReportData instance.
    """
    v1, v2 = CONFIG.v1_dir, CONFIG.v2_dir
    logger.info("Loading report artifacts.")

    channels = _read(v1 / "channels.csv")
    users = _read(v1 / "users.csv")
    messages = _read(v1 / "messages.csv")
    interacts_with = _read(v1 / "interacts_with.csv")
    active_in = _read(v1 / "active_in.csv")
    in_channel = _read(v1 / "in_channel.csv")

    communities = _read(v2 / "communities.csv")
    channel_community = _read(v2 / "channel_community.csv")
    # Drop the bulky topic embedding column; it is not used in the report.
    topics = _read(
        v2 / "topics.csv",
        usecols=["id", "label", "keywords", "coherence_score", "message_count"],
    )
    message_topics = _read(v2 / "message_topics.csv")
    community_topics = _read(v2 / "community_topics.csv")
    similarity = _read(v2 / "message_similarity.csv")
    emotions = _read(v2 / "message_emotions.csv")

    msg = _build_enriched_messages(
        messages, in_channel, channel_community, message_topics, emotions
    )

    return ReportData(
        channels=channels,
        users=users,
        messages=messages,
        interacts_with=interacts_with,
        active_in=active_in,
        in_channel=in_channel,
        communities=communities,
        channel_community=channel_community,
        topics=topics,
        message_topics=message_topics,
        community_topics=community_topics,
        similarity=similarity,
        emotions=emotions,
        msg=msg,
        channel_to_community=dict(
            zip(channel_community["channel_id"], channel_community["community_id"])
        ),
        message_to_community=dict(
            zip(msg["message_id"], msg["community_id"])
        ),
        topic_label=dict(zip(topics["id"], topics["label"])),
    )
