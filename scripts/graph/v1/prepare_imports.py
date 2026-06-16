import re

import pandas as pd
from loguru import logger

from scripts.graph.v1.config import CONFIG
from scripts.utils.logger import setup_logger


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------
setup_logger(__file__)

CHANNEL_PATTERN = re.compile(r"(<CHANNEL_HASH:[^>]+>)")

RAW_REQUIRED_COLUMNS = [
    "message_id",
    "user_id",
    "channel_id",
    "text_content",
    "date_parsed",
    "reply_to",
    "forward_from",
    "forward_from_n_forwards",
    "forward_from_reactions",
    "forward_from_views",
    "n_forwards",
    "reactions",
    "views",
]

TEXT_COLUMNS = [
    "message_id",
    "user_id",
    "channel_id",
    "text_content",
    "reply_to",
    "forward_from",
]

NUMERIC_COLUMNS = [
    "views",
    "reactions",
    "n_forwards",
    "forward_from_n_forwards",
    "forward_from_reactions",
    "forward_from_views",
]

# ------------------------------------------------------------
# Graph import preparation steps
# ------------------------------------------------------------


def extract_channel_hash(value: object) -> str:
    """
    Extract '<CHANNEL_HASH:...>' from fields such as:

    '<CHANNEL_HASH:abc>_123'
    '<CHANNEL_HASH:abc>'
    '<USER_HASH:abc>'
    NaN / empty

    Returns pd.NA when no channel hash is present.
    """
    # Treat null values as missing channel references.
    if pd.isna(value):
        return pd.NA

    # Normalize the value before checking for a hash token.
    text = str(value).strip()
    if not text:
        return pd.NA

    # Search for the channel hash pattern inside the normalized text.
    match = CHANNEL_PATTERN.search(text)
    if not match:
        return pd.NA

    return match.group(1)


def validate_raw_columns(df: pd.DataFrame) -> None:
    """
    Validate that the raw DataFrame contains required columns.

    Args:
        df: Raw message DataFrame to validate.

    Returns:
        None.
    """
    # Track all missing columns from the expected raw schema.
    missing = [col for col in RAW_REQUIRED_COLUMNS if col not in df.columns]

    # Some columns are optional in practice, but these are required for v1.
    hard_required = [
        "message_id",
        "user_id",
        "channel_id",
        "text_content",
        "date_parsed",
        "reply_to",
        "forward_from",
        "n_forwards",
        "reactions",
        "views",
    ]

    # Reject inputs that lack columns needed to build the graph.
    hard_missing = [col for col in hard_required if col not in df.columns]
    if hard_missing:
        raise ValueError(
            "CSV is missing required columns for graph v1: "
            + ", ".join(hard_missing)
        )

    # Warn when optional schema fields are absent.
    if missing:
        logger.warning(
            "Optional columns missing and will be filled when possible: "
            + ", ".join(missing)
        )


def normalize_text_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert available text columns to pandas string dtype.

    Args:
        df: Message DataFrame to normalize.

    Returns:
        The DataFrame with normalized text columns.
    """
    # Convert only columns that are present in the input DataFrame.
    for col in TEXT_COLUMNS:
        if col in df.columns:
            df[col] = df[col].astype("string")

    return df


def normalize_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert numeric columns to numeric values and fill missing columns with zero.

    Args:
        df: Message DataFrame to normalize.

    Returns:
        The DataFrame with normalized numeric columns.
    """
    # Ensure every numeric column exists before coercing values.
    for col in NUMERIC_COLUMNS:
        if col not in df.columns:
            df[col] = 0

        # Coerce invalid numeric values to zero.
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df


def add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add date, text, reply, and forwarding fields derived from raw columns.

    Args:
        df: Message DataFrame to enrich.

    Returns:
        The DataFrame with derived columns added.
    """
    # Parse message dates and derive a monthly period string.
    df["date_parsed"] = pd.to_datetime(df["date_parsed"], errors="coerce")
    df["month"] = df["date_parsed"].dt.to_period("M").astype("string")

    # Normalize text content before deriving text metrics.
    df["text_content"] = df["text_content"].fillna("").astype("string")
    df["text_length"] = df["text_content"].str.len().fillna(0).astype(int)

    # Count whitespace-separated tokens in each message.
    df["word_count"] = (
        df["text_content"]
        .str.split()
        .str.len()
        .fillna(0)
        .astype(int)
    )

    # Extract channel references from reply and forward fields.
    df["reply_to_channel"] = df["reply_to"].apply(
        extract_channel_hash).astype("string")
    df["forward_from_channel"] = (
        df["forward_from"]
        .apply(extract_channel_hash)
        .astype("string")
    )

    # Mark rows that contain a non-empty reply reference.
    df["is_reply"] = df["reply_to"].notna() & (
        df["reply_to"].astype("string").str.len() > 0
    )

    # Mark rows that contain a non-empty forward reference.
    df["is_forwarded"] = (
        df["forward_from"].notna()
        & (df["forward_from"].astype("string").str.len() > 0)
    )

    return df


def load_raw() -> pd.DataFrame:
    """
    Load and normalize the raw CSV configured for graph import.

    Args:
        None.

    Returns:
        The normalized raw message DataFrame.
    """
    # Load the raw dataset from the configured CSV path.
    logger.info(f"Loading raw CSV: {CONFIG.raw_csv}")
    df = pd.read_csv(CONFIG.raw_csv)

    # Validate schema before applying normalization steps.
    validate_raw_columns(df)

    # Apply column type normalization and derived-field creation.
    df = normalize_text_columns(df)
    df = normalize_numeric_columns(df)
    df = add_derived_columns(df)

    logger.info(f"Loaded and normalized raw CSV rows={len(df)}")

    return df


def write_csv(df: pd.DataFrame, name: str) -> None:
    """
    Write a DataFrame to the configured graph import directory.

    Args:
        df: DataFrame to write.
        name: Output CSV file name.

    Returns:
        None.
    """
    # Ensure the graph import directory exists before writing.
    CONFIG.graph_import_dir.mkdir(parents=True, exist_ok=True)

    path = CONFIG.graph_import_dir / name

    # Work on a copy so missing-value handling does not affect callers.
    df = df.copy()

    # Neo4j LOAD CSV handles empty strings better than pandas NA values.
    df = df.fillna("")

    # Write the CSV and report the generated file size by row count.
    df.to_csv(path, index=False)
    logger.info(f"Wrote {path} rows={len(df)}")


def build_channels(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build channel node records from message, reply, and forward data.

    Args:
        df: Normalized message DataFrame.

    Returns:
        DataFrame containing channel node records.
    """
    # Aggregate metrics for channels present in the dataset.
    dataset_channels = (
        df.groupby("channel_id", dropna=True)
        .agg(
            total_messages=("message_id", "count"),
            total_users=("user_id", "nunique"),
            active_start=("date_parsed", "min"),
            active_end=("date_parsed", "max"),
            total_views=("views", "sum"),
            total_forwards=("n_forwards", "sum"),
            total_reactions=("reactions", "sum"),
        )
        .reset_index()
        .rename(columns={"channel_id": "id"})
    )

    dataset_channels["is_dataset_channel"] = True

    # Collect channels referenced only through forwards or replies.
    forward_source_ids = set(df["forward_from_channel"].dropna().unique())
    reply_source_ids = set(df["reply_to_channel"].dropna().unique())

    source_channels = pd.DataFrame(
        {
            "id": sorted(forward_source_ids.union(reply_source_ids)),
        }
    )

    # Combine dataset channels with externally referenced channels.
    all_channels = (
        pd.concat(
            [
                dataset_channels[["id"]],
                source_channels[["id"]],
            ],
            ignore_index=True,
        )
        .drop_duplicates()
        .reset_index(drop=True)
    )

    # Attach dataset metrics where they exist.
    channels = all_channels.merge(dataset_channels, on="id", how="left")

    # Fill missing metric values for channels not present in the dataset.
    channels["total_messages"] = channels["total_messages"].fillna(
        0).astype(int)
    channels["total_users"] = channels["total_users"].fillna(0).astype(int)
    channels["total_views"] = channels["total_views"].fillna(0)
    channels["total_forwards"] = channels["total_forwards"].fillna(0)
    channels["total_reactions"] = channels["total_reactions"].fillna(
        0).astype(int)

    # Convert active date bounds to strings for CSV export.
    channels["active_start"] = channels["active_start"].astype(
        "string").fillna("")
    channels["active_end"] = channels["active_end"].astype("string").fillna("")

    # Normalize channel role flags.
    channels["is_dataset_channel"] = (
        channels["is_dataset_channel"]
        .fillna(False)
        .astype(bool)
    )

    channels["is_forward_source"] = channels["id"].isin(forward_source_ids)
    channels["is_reply_source"] = channels["id"].isin(reply_source_ids)

    return channels[
        [
            "id",
            "total_messages",
            "total_users",
            "active_start",
            "active_end",
            "total_views",
            "total_forwards",
            "total_reactions",
            "is_dataset_channel",
            "is_forward_source",
            "is_reply_source",
        ]
    ]


def build_users(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build user node records from message activity.

    Args:
        df: Normalized message DataFrame.

    Returns:
        DataFrame containing user node records.
    """
    # Aggregate message and channel counts per user.
    users = (
        df.groupby("user_id", dropna=True)
        .agg(
            total_messages=("message_id", "count"),
            channel_count=("channel_id", "nunique"),
        )
        .reset_index()
        .rename(columns={"user_id": "id"})
    )

    return users[
        [
            "id",
            "total_messages",
            "channel_count",
        ]
    ]


def build_messages(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build message node records from normalized message fields.

    Args:
        df: Normalized message DataFrame.

    Returns:
        DataFrame containing message node records.
    """
    # Select message attributes needed for graph nodes.
    messages = df[
        [
            "message_id",
            "text_content",
            "date_parsed",
            "month",
            "text_length",
            "word_count",
            "views",
            "reactions",
            "n_forwards",
            "is_reply",
            "is_forwarded",
        ]
    ].copy()

    # Rename the message identifier to the graph node id.
    messages = messages.rename(columns={"message_id": "id"})

    # Normalize export columns to string-compatible values.
    messages["date_parsed"] = messages["date_parsed"].astype("string")
    messages["month"] = messages["month"].astype("string")
    messages["text_content"] = messages["text_content"].fillna("")

    return messages[
        [
            "id",
            "text_content",
            "date_parsed",
            "month",
            "text_length",
            "word_count",
            "views",
            "reactions",
            "n_forwards",
            "is_reply",
            "is_forwarded",
        ]
    ]


def build_edges(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """
    Build relationship CSV DataFrames for graph import.

    Args:
        df: Normalized message DataFrame.

    Returns:
        Dictionary mapping edge CSV file names to DataFrames.
    """
    # Link each message to the user who posted it.
    posted = df[["user_id", "message_id"]].copy()

    # Link each message to the dataset channel where it appeared.
    in_channel = df[["message_id", "channel_id"]].copy()

    # Create message-to-message reply relationships.
    replies_to = (
        df.loc[
            df["reply_to"].notna()
            & (df["reply_to"].astype("string").str.len() > 0),
            ["message_id", "reply_to"],
        ]
        .copy()
        .rename(columns={"reply_to": "target_message_id"})
    )

    # Create message-to-channel relationships for replied-into channels.
    replied_into = (
        df.loc[
            df["reply_to_channel"].notna()
            & (df["reply_to_channel"].astype("string").str.len() > 0),
            ["message_id", "reply_to_channel"],
        ]
        .copy()
        .rename(columns={"reply_to_channel": "channel_id"})
    )

    # Create message-to-channel relationships for forwarded source channels.
    forwarded_from = (
        df.loc[
            df["forward_from_channel"].notna()
            & (df["forward_from_channel"].astype("string").str.len() > 0),
            ["message_id", "forward_from_channel"],
        ]
        .copy()
        .rename(columns={"forward_from_channel": "channel_id"})
    )

    # Aggregate user activity within each dataset channel.
    active_in = (
        df.groupby(["user_id", "channel_id"], dropna=True)
        .agg(
            total_messages=("message_id", "count"),
            total_views=("views", "sum"),
            total_reactions=("reactions", "sum"),
            total_forwards=("n_forwards", "sum"),
        )
        .reset_index()
    )

    return {
        "posted.csv": posted[
            [
                "user_id",
                "message_id",
            ]
        ],
        "in_channel.csv": in_channel[
            [
                "message_id",
                "channel_id",
            ]
        ],
        "replies_to.csv": replies_to[
            [
                "message_id",
                "target_message_id",
            ]
        ],
        "replied_into.csv": replied_into[
            [
                "message_id",
                "channel_id",
            ]
        ],
        "forwarded_from.csv": forwarded_from[
            [
                "message_id",
                "channel_id",
            ]
        ],
        "active_in.csv": active_in[
            [
                "user_id",
                "channel_id",
                "total_messages",
                "total_views",
                "total_reactions",
                "total_forwards",
            ]
        ],
    }


def build_interacts_with(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build aggregated INTERACTS_WITH channel-to-channel edges from three signals.

    Signals:
    - Shared users: both channels share a user that posted in each.
    - Forwarding: a message in the target channel was forwarded from the source.
    - Replies: a message in the target channel replied to one in the source.

    Args:
        df: Normalized message DataFrame.

    Returns:
        DataFrame with one directed row per (source, target) channel pair.
    """
    # Signal 1: shared users — cross-join each user's active channels.
    user_ch = df[["user_id", "channel_id"]].drop_duplicates()
    shared = (
        user_ch.rename(columns={"channel_id": "source"})
        .merge(user_ch.rename(columns={"channel_id": "target"}), on="user_id")
    )
    shared = shared[shared["source"] != shared["target"]]
    shared_counts = (
        shared.groupby(["source", "target"])["user_id"]
        .nunique()
        .reset_index(name="shared_users_count")
    )

    # Signal 2: forwarding — source is forward_from_channel, target is channel_id.
    fwd_mask = (
        df["forward_from_channel"].notna()
        & (df["forward_from_channel"].astype("string").str.len() > 0)
    )
    fwd_pairs = (
        df.loc[fwd_mask, ["forward_from_channel", "channel_id"]]
        .copy()
        .rename(columns={"forward_from_channel": "source", "channel_id": "target"})
    )
    fwd_pairs = fwd_pairs[fwd_pairs["source"] != fwd_pairs["target"]]
    fwd_counts = (
        fwd_pairs.groupby(["source", "target"])
        .size()
        .reset_index(name="forward_count")
    )

    # Signal 3: replies — source is reply_to_channel, target is channel_id.
    reply_mask = (
        df["reply_to_channel"].notna()
        & (df["reply_to_channel"].astype("string").str.len() > 0)
    )
    reply_pairs = (
        df.loc[reply_mask, ["reply_to_channel", "channel_id"]]
        .copy()
        .rename(columns={"reply_to_channel": "source", "channel_id": "target"})
    )
    reply_pairs = reply_pairs[reply_pairs["source"] != reply_pairs["target"]]
    reply_counts = (
        reply_pairs.groupby(["source", "target"])
        .size()
        .reset_index(name="reply_count")
    )

    # Union all unique (source, target) pairs, then left-join each signal.
    all_pairs = (
        pd.concat(
            [
                shared_counts[["source", "target"]],
                fwd_counts[["source", "target"]],
                reply_counts[["source", "target"]],
            ],
            ignore_index=True,
        )
        .drop_duplicates()
        .reset_index(drop=True)
    )

    result = (
        all_pairs
        .merge(shared_counts, on=["source", "target"], how="left")
        .merge(fwd_counts, on=["source", "target"], how="left")
        .merge(reply_counts, on=["source", "target"], how="left")
    )

    result["shared_users_count"] = result["shared_users_count"].fillna(0).astype(int)
    result["forward_count"] = result["forward_count"].fillna(0).astype(int)
    result["reply_count"] = result["reply_count"].fillna(0).astype(int)
    result["interaction_count"] = (
        result["shared_users_count"]
        + result["forward_count"]
        + result["reply_count"]
    )
    result["interaction_weight"] = result["interaction_count"].astype(float)
    result["has_shared_user_signal"] = result["shared_users_count"] > 0
    result["has_forward_signal"] = result["forward_count"] > 0
    result["has_reply_signal"] = result["reply_count"] > 0

    return result[
        [
            "source",
            "target",
            "shared_users_count",
            "forward_count",
            "reply_count",
            "interaction_count",
            "interaction_weight",
            "has_shared_user_signal",
            "has_forward_signal",
            "has_reply_signal",
        ]
    ]


def print_summary(df: pd.DataFrame) -> None:
    """
    Print summary counts for the normalized raw dataset.

    Args:
        df: Normalized message DataFrame.

    Returns:
        None.
    """
    # Log high-level dataset counts.
    logger.info("Raw dataset")
    logger.info(f"Rows: {len(df)}")
    logger.info(f"Messages: {df['message_id'].nunique()}")
    logger.info(f"Users: {df['user_id'].nunique()}")
    logger.info(f"Dataset channels: {df['channel_id'].nunique()}")

    # Log relationship-specific counts.
    logger.info(f"Reply rows: {df['is_reply'].sum()}")
    logger.info(f"Forwarded rows: {df['is_forwarded'].sum()}")
    logger.info(
        f"Reply source channels: {df['reply_to_channel'].dropna().nunique()}")
    logger.info(
        f"Forward source channels: {df['forward_from_channel'].dropna().nunique()}"
    )


def main() -> None:
    """
    Generate all graph import CSV files from the configured raw dataset.

    Args:
        None.

    Returns:
        None.
    """
    # Load and normalize the source data.
    logger.info("Starting graph import CSV preparation.")
    df = load_raw()

    # Print a summary before writing graph files.
    print_summary(df)

    # Write graph node CSV files.
    write_csv(build_channels(df), "channels.csv")
    write_csv(build_users(df), "users.csv")
    write_csv(build_messages(df), "messages.csv")

    # Write graph relationship CSV files.
    for filename, edge_df in build_edges(df).items():
        write_csv(edge_df, filename)

    # Write derived channel-to-channel interaction graph.
    write_csv(build_interacts_with(df), "interacts_with.csv")

    logger.info("Graph import CSV preparation complete.")


if __name__ == "__main__":
    main()
