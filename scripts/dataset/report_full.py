"""
dt_report_full.py

Generate exploratory markdown report
for cleaned Aletheia full dataset.

Outputs:
- reports/aletheia_full_report.md
- reports/figures/full_report/*
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from loguru import logger
import matplotlib.pyplot as plt

from scripts.utils.logger import setup_logger

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------
setup_logger(__file__)

INPUT_FILE = "data/aletheia_clean_full.csv"

REPORT_FILE = "reports/aletheia_full_report.md"
FIGURES_DIR = "reports/figures/full_report"

Path(FIGURES_DIR).mkdir(parents=True, exist_ok=True)
Path(REPORT_FILE).parent.mkdir(parents=True, exist_ok=True)

DATE_COLUMN = "date_parsed"
TEXT_COLUMN = "text_content"

MAIN_COLUMNS = [
    "channel_id",
    "message_id",
    "user_id",
    "date_parsed",
    "time_bin",
    "language",
    "is_vaccine_related",
    "media_type",
    "views",
    "n_forwards",
    "reactions",
    "text_content",
]


COLUMN_DESCRIPTIONS = {
    "channel_id": "Anonymized identifier for the Telegram channel.",
    "message_id": "Unique identifier for each Telegram message.",
    "user_id": "Anonymized identifier of the message author.",
    "collected_date": "Timestamp when the message was collected.",
    "date": "Original timestamp in Unix milliseconds.",
    "edit_date": "Timestamp of last edit, if available.",
    "date_parsed": "Human-readable message timestamp.",
    "time_bin": "Temporal bin used for aggregation.",
    "text_content": "Text content of the Telegram message.",
    "language": "Detected language.",
    "is_vaccine_related": "Indicator for vaccine-related content.",
    "media_type": "Type of media attached to the message.",
    "media_title": "Title of attached media content.",
    "media_description": "Description of attached media content.",
    "media_url": "External media URL.",
    "media_path": "Local path to media file.",
    "forward_from": "Source channel or user of a forwarded message.",
    "forward_from_n_forwards": "Forward count of original forwarded message.",
    "forward_from_reactions": "Reaction count of original forwarded message.",
    "forward_from_views": "View count of original forwarded message.",
    "n_forwards": "Number of forwards for this message.",
    "views": "Number of views.",
    "reactions": "Number of reactions.",
    "reply_to": "Identifier of the replied-to message.",
}


NUMERIC_COLUMNS = [
    "date",
    "views",
    "n_forwards",
    "reactions",
    "forward_from_n_forwards",
    "forward_from_reactions",
    "forward_from_views",
]


# ------------------------------------------------------------
# Loading and normalization
# ------------------------------------------------------------


def load_dataset(path: Path) -> pd.DataFrame:
    """
    Loads the cleaned Aletheia dataset.

    Args:
        path:
            Path to cleaned CSV file.

    Returns:
        Loaded dataframe.
    """

    logger.info(f"Loading dataset: {path}")

    # Read the CSV with mixed-type handling delegated to pandas.
    df = pd.read_csv(path, low_memory=False)

    logger.info(f"Loaded dataframe with shape {df.shape}")

    return df


def normalize_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalizes datetime and numeric columns.

    Args:
        df:
            Input dataframe.

    Returns:
        Dataframe with normalized types.
    """

    logger.info("Normalizing column types.")

    # Convert known timestamp fields when they are present.
    for col in [
        "collected_date",
        "edit_date",
        "date_parsed",
        "time_bin",
    ]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Convert expected numeric fields and preserve invalid values as NaN.
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds derived variables useful for reporting.

    Args:
        df:
            Input dataframe.

    Returns:
        Dataframe with derived columns.
    """

    logger.info("Creating derived columns.")

    # Derive text-size metrics from message content.
    if TEXT_COLUMN in df.columns:
        df["text_length"] = (
            df[TEXT_COLUMN]
            .fillna("")
            .astype(str)
            .str.len()
        )

        df["word_count"] = (
            df[TEXT_COLUMN]
            .fillna("")
            .astype(str)
            .str.split()
            .str.len()
        )

    # Mark messages with non-empty media metadata.
    if "media_type" in df.columns:
        df["has_media"] = (
            df["media_type"]
            .fillna("")
            .astype(str)
            .str.strip()
            .ne("")
        )

    # Add boolean flags for reply and forwarding status.
    if "reply_to" in df.columns:
        df["is_reply"] = df["reply_to"].notna()

    if "forward_from" in df.columns:
        df["is_forwarded"] = df["forward_from"].notna()

    return df


# ------------------------------------------------------------
# Summary tables
# ------------------------------------------------------------

def compute_overview(df: pd.DataFrame) -> dict:
    """
    Computes high-level dataset metrics.

    Args:
        df:
            Input dataframe.

    Returns:
        Dictionary with overview metrics.
    """

    logger.info("Computing overview metrics.")

    # Build top-level counts and totals only for available columns.
    overview = {
        "Rows": len(df),
        "Columns": len(df.columns),
        "Duplicate message IDs": (
            df["message_id"].duplicated().sum()
            if "message_id" in df.columns
            else np.nan
        ),
        "Unique channels": (
            df["channel_id"].nunique()
            if "channel_id" in df.columns
            else np.nan
        ),
        "Unique users": (
            df["user_id"].nunique()
            if "user_id" in df.columns
            else np.nan
        ),
        "Date start": (
            df[DATE_COLUMN].min()
            if DATE_COLUMN in df.columns
            else pd.NaT
        ),
        "Date end": (
            df[DATE_COLUMN].max()
            if DATE_COLUMN in df.columns
            else pd.NaT
        ),
        "Total views": (
            df["views"].sum()
            if "views" in df.columns
            else np.nan
        ),
        "Total forwards": (
            df["n_forwards"].sum()
            if "n_forwards" in df.columns
            else np.nan
        ),
        "Total reactions": (
            df["reactions"].sum()
            if "reactions" in df.columns
            else np.nan
        ),
    }

    return overview


def build_missing_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Builds missing-value summary table.

    Args:
        df:
            Input dataframe.

    Returns:
        Missing-value dataframe.
    """

    logger.info("Computing missing-value table.")

    # Count null values per column.
    missing = (
        df.isna()
        .sum()
        .rename("missing")
        .to_frame()
    )

    # Add percentage and dtype context for each column.
    missing["missing_pct"] = missing["missing"] / len(df) * 100

    missing["dtype"] = df.dtypes.astype(str)

    # Sort by missing count to surface sparse columns first.
    missing = (
        missing
        .sort_values("missing", ascending=False)
        .reset_index()
        .rename(columns={"index": "column"})
    )

    return missing


def build_column_profile(df: pd.DataFrame) -> pd.DataFrame:
    """
    Builds column-level profiling table.

    Args:
        df:
            Input dataframe.

    Returns:
        Column profile dataframe.
    """

    logger.info("Computing column profile.")

    rows = []

    # Collect per-column metadata and frequency information.
    for col in df.columns:
        series = df[col]

        top_value = None
        top_count = None

        # Find the most frequent non-null value when any exist.
        if len(series.dropna()) > 0:
            value_counts = series.value_counts(dropna=True)

            if not value_counts.empty:
                top_value = str(value_counts.index[0])[:80]
                top_count = int(value_counts.iloc[0])

        rows.append(
            {
                "column": col,
                "description": COLUMN_DESCRIPTIONS.get(col, ""),
                "dtype": str(series.dtype),
                "missing": int(series.isna().sum()),
                "missing_pct": round(series.isna().mean() * 100, 2),
                "unique": int(series.nunique(dropna=True)),
                "top_value": top_value,
                "top_count": top_count,
            }
        )

    return pd.DataFrame(rows)


def build_numeric_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Builds numeric summary table.

    Args:
        df:
            Input dataframe.

    Returns:
        Numeric summary dataframe.
    """

    logger.info("Computing numeric summary.")

    # Restrict summary statistics to configured numeric columns in the data.
    numeric_cols = [
        col for col in NUMERIC_COLUMNS
        if col in df.columns
    ]

    if not numeric_cols:
        return pd.DataFrame()

    summary = (
        df[numeric_cols]
        .describe()
        .T
        .reset_index()
        .rename(columns={"index": "column"})
    )

    return summary


def build_main_column_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Builds compact summary for main columns.

    Args:
        df:
            Input dataframe.

    Returns:
        Main-column summary dataframe.
    """

    logger.info("Computing main-column summary.")

    rows = []

    # Summarize only configured main columns that exist in the dataframe.
    for col in MAIN_COLUMNS:
        if col not in df.columns:
            continue

        rows.append(
            {
                "column": col,
                "description": COLUMN_DESCRIPTIONS.get(col, ""),
                "missing": int(df[col].isna().sum()),
                "missing_pct": round(df[col].isna().mean() * 100, 2),
                "unique": int(df[col].nunique(dropna=True)),
                "dtype": str(df[col].dtype),
            }
        )

    return pd.DataFrame(rows)


# ------------------------------------------------------------
# Plot helpers
# ------------------------------------------------------------

def report_image_path(filename: str) -> str:
    """
    Builds markdown-relative path for a figure.

    Args:
        filename:
            Figure filename.

    Returns:
        Relative path from the report file.
    """

    # Match figure paths to the markdown report location
    return str(Path("figures") / "full_report" / filename)


def save_bar_plot(
    series: pd.Series,
    title: str,
    xlabel: str,
    ylabel: str,
    filename: str,
    top_n: int = 20,
) -> str:
    """
    Saves a bar plot from value counts.

    Args:
        series:
            Series to plot.

        title:
            Plot title.

        xlabel:
            X-axis label.

        ylabel:
            Y-axis label.

        filename:
            Output filename.

        top_n:
            Number of top categories.

    Returns:
        Relative figure path.
    """

    logger.info(f"Creating plot: {filename}")

    # Keep the most common non-null categories for a compact chart.
    counts = (
        series
        .dropna()
        .astype(str)
        .value_counts()
        .head(top_n)
        .sort_values()
    )

    fig_path = Path(FIGURES_DIR) / filename

    # Render and save the horizontal bar chart.
    plt.figure(figsize=(10, 6))

    counts.plot(kind="barh")

    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.tight_layout()
    plt.savefig(fig_path, dpi=150)
    plt.close()

    return report_image_path(filename)


def save_hist_plot(
    series: pd.Series,
    title: str,
    xlabel: str,
    ylabel: str,
    filename: str,
    log_transform: bool = False,
    bins: int = 50,
) -> str:
    """
    Saves a histogram plot.

    Args:
        series:
            Numeric series.

        title:
            Plot title.

        xlabel:
            X-axis label.

        ylabel:
            Y-axis label.

        filename:
            Output filename.

        log_transform:
            Whether to plot log1p values.

        bins:
            Number of histogram bins.

    Returns:
        Relative figure path.
    """

    logger.info(f"Creating plot: {filename}")

    # Coerce values to numeric and remove invalid entries before plotting.
    values = pd.to_numeric(series, errors="coerce").dropna()

    if log_transform:
        values = np.log1p(values)
        xlabel = f"log1p({xlabel})"

    fig_path = Path(FIGURES_DIR) / filename

    # Render and save the histogram.
    plt.figure(figsize=(10, 6))

    plt.hist(values, bins=bins)

    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.tight_layout()
    plt.savefig(fig_path, dpi=150)
    plt.close()

    return report_image_path(filename)


def save_line_plot(
    series: pd.Series,
    title: str,
    xlabel: str,
    ylabel: str,
    filename: str,
) -> str:
    """
    Saves a line plot.

    Args:
        series:
            Indexed numeric series.

        title:
            Plot title.

        xlabel:
            X-axis label.

        ylabel:
            Y-axis label.

        filename:
            Output filename.

    Returns:
        Relative figure path.
    """

    logger.info(f"Creating plot: {filename}")

    fig_path = Path(FIGURES_DIR) / filename

    # Render and save the indexed line chart.
    plt.figure(figsize=(12, 6))

    series.plot()

    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.tight_layout()
    plt.savefig(fig_path, dpi=150)
    plt.close()

    return report_image_path(filename)


# ------------------------------------------------------------
# Dataset plots
# ------------------------------------------------------------

def create_plots(df: pd.DataFrame) -> dict:
    """
    Creates report plots.

    Args:
        df:
            Input dataframe.

    Returns:
        Mapping of plot names to relative paths.
    """

    logger.info("Generating report plots.")

    plots = {}

    # Generate categorical distribution plots when source columns exist.
    if "language" in df.columns:
        plots["language_distribution"] = save_bar_plot(
            df["language"],
            "Language distribution",
            "Messages",
            "Language",
            "language_distribution.png",
            top_n=15,
        )

    if "media_type" in df.columns:
        plots["media_types"] = save_bar_plot(
            df["media_type"],
            "Media type distribution",
            "Messages",
            "Media type",
            "media_types.png",
            top_n=20,
        )

    if "channel_id" in df.columns:
        plots["top_channels"] = save_bar_plot(
            df["channel_id"],
            "Top channels by message count",
            "Messages",
            "Channel",
            "top_channels.png",
            top_n=20,
        )

    # Aggregate messages by month for the temporal activity plot.
    if DATE_COLUMN in df.columns:
        monthly = (
            df.dropna(subset=[DATE_COLUMN])
            .set_index(DATE_COLUMN)
            .resample("ME")
            .size()
        )

        plots["messages_over_time"] = save_line_plot(
            monthly,
            "Messages over time",
            "Month",
            "Messages",
            "messages_over_time.png",
        )

    # Generate log-scaled histograms for skewed engagement fields.
    if "views" in df.columns:
        plots["views_distribution"] = save_hist_plot(
            df["views"],
            "Views distribution",
            "views",
            "Messages",
            "views_distribution.png",
            log_transform=True,
        )

    if "n_forwards" in df.columns:
        plots["forwards_distribution"] = save_hist_plot(
            df["n_forwards"],
            "Forwards distribution",
            "n_forwards",
            "Messages",
            "forwards_distribution.png",
            log_transform=True,
        )

    if "reactions" in df.columns:
        plots["reactions_distribution"] = save_hist_plot(
            df["reactions"],
            "Reactions distribution",
            "reactions",
            "Messages",
            "reactions_distribution.png",
            log_transform=True,
        )

    if "text_length" in df.columns:
        plots["text_length_distribution"] = save_hist_plot(
            df["text_length"],
            "Message text length distribution",
            "text_length",
            "Messages",
            "text_length_distribution.png",
            log_transform=True,
        )

    if "word_count" in df.columns:
        plots["word_count_distribution"] = save_hist_plot(
            df["word_count"],
            "Message word count distribution",
            "word_count",
            "Messages",
            "word_count_distribution.png",
            log_transform=True,
        )

    return plots


# ------------------------------------------------------------
# Specialized analysis
# ------------------------------------------------------------

def build_media_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Summarizes media type by engagement.

    Args:
        df:
            Input dataframe.

    Returns:
        Media summary dataframe.
    """

    # Return an empty table when media categories are unavailable.
    if "media_type" not in df.columns:
        return pd.DataFrame()

    logger.info("Computing media summary.")

    # Select available engagement metrics for media grouping.
    metrics = [
        col for col in [
            "views",
            "n_forwards",
            "reactions",
        ]
        if col in df.columns
    ]

    if not metrics:
        return pd.DataFrame()

    summary = (
        df.groupby("media_type")[metrics]
        .agg(
            [
                "count",
                "mean",
                "median",
            ]
        )
    )

    # Flatten hierarchical aggregation column names.
    summary.columns = [
        "_".join(col).strip()
        for col in summary.columns.values
    ]

    # Keep the most common media types by the first metric count.
    summary = (
        summary
        .sort_values(f"{metrics[0]}_count", ascending=False)
        .reset_index()
        .head(20)
    )

    return summary


def build_channel_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Summarizes top channels by volume and engagement.

    Args:
        df:
            Input dataframe.

    Returns:
        Channel summary dataframe.
    """

    # Return an empty table when channel IDs are unavailable.
    if "channel_id" not in df.columns:
        return pd.DataFrame()

    logger.info("Computing channel summary.")

    agg_dict = {
        "message_id": "count",
    }

    # Add available engagement aggregations to the channel summary.
    for col in [
        "views",
        "n_forwards",
        "reactions",
    ]:
        if col in df.columns:
            agg_dict[col] = [
                "sum",
                "mean",
                "median",
            ]

    summary = (
        df.groupby("channel_id")
        .agg(agg_dict)
    )

    # Flatten aggregation columns after groupby.
    summary.columns = [
        "_".join(col).strip("_")
        if isinstance(col, tuple)
        else col
        for col in summary.columns.values
    ]

    # Rename the volume field and keep the most active channels.
    summary = (
        summary
        .rename(columns={"message_id_count": "messages"})
        .sort_values("messages", ascending=False)
        .reset_index()
        .head(20)
    )

    return summary


# ------------------------------------------------------------
# Markdown helpers
# ------------------------------------------------------------

def md_table(df: pd.DataFrame, max_rows: int = 30) -> str:
    """
    Converts dataframe to markdown table.

    Args:
        df:
            Dataframe to convert.

        max_rows:
            Maximum number of rows.

    Returns:
        Markdown table string.
    """

    # Provide a readable placeholder for empty report sections.
    if df is None or df.empty:
        return "_No data available._"

    return df.head(max_rows).to_markdown(index=False)


def md_image(path: str, caption: str) -> str:
    """
    Builds markdown image reference.

    Args:
        path:
            Relative figure path.

        caption:
            Figure caption.

    Returns:
        Markdown image string.
    """

    # Format a relative image link for the markdown report.
    return f"![{caption}]({path})"


# ------------------------------------------------------------
# Markdown report
# ------------------------------------------------------------

def build_report(
    df: pd.DataFrame,
    overview: dict,
    missing: pd.DataFrame,
    column_profile: pd.DataFrame,
    main_columns: pd.DataFrame,
    numeric_summary: pd.DataFrame,
    media_summary: pd.DataFrame,
    channel_summary: pd.DataFrame,
    plots: dict,
) -> str:
    """
    Builds the markdown report text.

    Args:
        df:
            Input dataframe.

        overview:
            Overview metrics.

        missing:
            Missing-value table.

        column_profile:
            Full column profile.

        main_columns:
            Main-column summary.

        numeric_summary:
            Numeric summary table.

        media_summary:
            Media summary.

        channel_summary:
            Channel summary.

        plots:
            Plot path mapping.

    Returns:
        Markdown report as string.
    """

    logger.info("Building markdown report.")

    # Convert overview metrics to a markdown-ready table.
    overview_table = pd.DataFrame(
        [
            {
                "Metric": key,
                "Value": value,
            }
            for key, value in overview.items()
        ]
    )

    lines = []

    # Assemble dataset context and summary sections.
    lines.append("# Aletheia Dataset Report")
    lines.append("")
    lines.append(
        "Generated automatically from the cleaned Aletheia Telegram dataset.")
    lines.append("")
    lines.append("## Dataset Context")
    lines.append("")
    lines.append(
        "This dataset contains Telegram messages collected from Brazilian antivaccine "
        "channels and groups. Each row corresponds to one Telegram message. The data "
        "include identifiers, timestamps, message content, media metadata, forwarding "
        "information, and engagement metrics."
    )
    lines.append("")
    lines.append("## Dataset Overview")
    lines.append("")
    lines.append(md_table(overview_table))
    lines.append("")
    lines.append("## Main Columns")
    lines.append("")
    lines.append(md_table(main_columns))
    lines.append("")
    lines.append("## Missing Values")
    lines.append("")
    lines.append(
        "The table below summarizes missing values by column. High missingness is "
        "expected for optional fields such as media metadata, replies, edits, and "
        "forwarding information."
    )
    lines.append("")
    lines.append(md_table(missing))
    lines.append("")
    lines.append("## Column Profile")
    lines.append("")
    lines.append(md_table(column_profile, max_rows=80))
    lines.append("")
    lines.append("## Numeric Summary")
    lines.append("")
    lines.append(md_table(numeric_summary))
    lines.append("")

    # Add temporal and categorical visual sections when plots exist.
    lines.append("## Temporal Activity")
    lines.append("")
    if "messages_over_time" in plots:
        lines.append(
            md_image(
                plots["messages_over_time"],
                "Messages over time",
            )
        )
    lines.append("")

    lines.append("## Language Distribution")
    lines.append("")
    if "language_distribution" in plots:
        lines.append(
            md_image(
                plots["language_distribution"],
                "Language distribution",
            )
        )
    lines.append("")

    lines.append("## Media Analysis")
    lines.append("")
    if "media_types" in plots:
        lines.append(
            md_image(
                plots["media_types"],
                "Media type distribution",
            )
        )
    lines.append("")
    lines.append(md_table(media_summary))
    lines.append("")

    lines.append("## Channel Activity")
    lines.append("")
    if "top_channels" in plots:
        lines.append(
            md_image(
                plots["top_channels"],
                "Top channels by message count",
            )
        )
    lines.append("")
    lines.append(md_table(channel_summary))
    lines.append("")

    # Add engagement and text distribution images.
    lines.append("## Engagement Distributions")
    lines.append("")
    if "views_distribution" in plots:
        lines.append(
            md_image(
                plots["views_distribution"],
                "Views distribution",
            )
        )
        lines.append("")

    if "forwards_distribution" in plots:
        lines.append(
            md_image(
                plots["forwards_distribution"],
                "Forwards distribution",
            )
        )
        lines.append("")

    if "reactions_distribution" in plots:
        lines.append(
            md_image(
                plots["reactions_distribution"],
                "Reactions distribution",
            )
        )
        lines.append("")

    lines.append("## Text Length")
    lines.append("")
    if "text_length_distribution" in plots:
        lines.append(
            md_image(
                plots["text_length_distribution"],
                "Text length distribution",
            )
        )
        lines.append("")

    if "word_count_distribution" in plots:
        lines.append(
            md_image(
                plots["word_count_distribution"],
                "Word count distribution",
            )
        )
        lines.append("")

    return "\n".join(lines)


# ------------------------------------------------------------
# Save report
# ------------------------------------------------------------

def save_report(
    report_text: str,
    path: Path,
):
    """
    Saves markdown report.

    Args:
        report_text:
            Markdown content.

        path:
            Output report path.

    Returns:
        None
    """

    logger.info(f"Saving markdown report: {path}")

    # Write the generated report using UTF-8 for markdown compatibility.
    path.write_text(report_text, encoding="utf-8")


# ------------------------------------------------------------
# Main pipeline
# ------------------------------------------------------------

def main():
    """
    Executes the report generation workflow.

    Returns:
        None
    """

    logger.info("Starting Aletheia dataset reporting.")

    # Load, normalize, and enrich the source dataset.
    df = load_dataset(Path(INPUT_FILE))
    df = normalize_types(df)
    df = add_derived_columns(df)

    # Build all tabular summaries sed by the report.
    overview = compute_overview(df)
    missing = build_missing_table(df)
    column_profile = build_column_profile(df)
    main_columns = build_main_column_summary(df)
    numeric_summary = build_numeric_summary(df)
    media_summary = build_media_summary(df)
    channel_summary = build_channel_summary(df)

    # Generate figures and assemble the final markdown text.
    plots = create_plots(df)

    report_text = build_report(
        df=df,
        overview=overview,
        missing=missing,
        column_profile=column_profile,
        main_columns=main_columns,
        numeric_summary=numeric_summary,
        media_summary=media_summary,
        channel_summary=channel_summary,
        plots=plots,
    )

    save_report(report_text, Path(REPORT_FILE))

    logger.info("Report completed.")
    logger.info(f"Markdown report: {REPORT_FILE}")
    logger.info(f"Figures directory: {FIGURES_DIR}")


if __name__ == "__main__":
    main()
