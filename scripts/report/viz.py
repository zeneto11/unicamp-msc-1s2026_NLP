"""Markdown and plotting helpers for the V2 report.

Thin wrappers over pandas ``to_markdown`` and matplotlib so the section builders
stay declarative. Every plot is titled and axis-labelled, saved at a consistent
DPI, and returned as a repo-relative markdown link. Section text supplies the
one-line interpretation below each figure.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")  # Headless backend for script-time figure generation.
import matplotlib.pyplot as plt
from loguru import logger

from scripts.report.config import CONFIG


def setup_style() -> None:
    """
    Apply shared matplotlib defaults for all report figures.

    Args:
        None.

    Returns:
        None.
    """
    plt.rcParams.update(
        {
            "figure.figsize": CONFIG.fig_size,
            "figure.dpi": 110,
            "savefig.dpi": CONFIG.fig_dpi,
            "axes.grid": True,
            "grid.alpha": 0.3,
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
            "font.size": 10,
        }
    )


# ----------------------------------------------------------------------------
# Markdown helpers
# ----------------------------------------------------------------------------
def md_table(df: pd.DataFrame, max_rows: int = 20, floatfmt: str = ".3f") -> str:
    """
    Render a DataFrame as a GitHub markdown table, capped at max_rows.

    Args:
        df: DataFrame to render.
        max_rows: Maximum number of rows to include.
        floatfmt: Float format string passed to tabulate.

    Returns:
        Markdown table string (or an italic note if empty).
    """
    if df is None or len(df) == 0:
        return "_No data available._"
    return df.head(max_rows).to_markdown(index=False, floatfmt=floatfmt)


def md_image(filename: str, caption: str) -> str:
    """
    Build a markdown image link with alt text for a saved figure.

    Args:
        filename: Figure file name (already saved under the figures dir).
        caption: Alt/caption text.

    Returns:
        Markdown image string with a repo-relative path.
    """
    return f"![{caption}]({CONFIG.figures_rel}/{filename})"


def _save(filename: str) -> str:
    """
    Save the current matplotlib figure and return its markdown-relative path.

    Args:
        filename: Output figure file name.

    Returns:
        Repo-relative figure path string.
    """
    path = CONFIG.figures_dir / filename
    plt.tight_layout()
    plt.savefig(path, dpi=CONFIG.fig_dpi)
    plt.close()
    logger.info(f"Saved figure {path.name}")
    return f"{CONFIG.figures_rel}/{filename}"


# ----------------------------------------------------------------------------
# Plot helpers — each returns the figure file name for md_image()
# ----------------------------------------------------------------------------
def bar(
    series: pd.Series,
    title: str,
    xlabel: str,
    ylabel: str,
    filename: str,
    horizontal: bool = True,
    color="#3b6ea5",
    log: bool = False,
) -> str:
    """
    Render a bar chart from a labelled series (index = categories).

    Args:
        series: Values to plot, indexed by category.
        title: Plot title.
        xlabel: X-axis label.
        ylabel: Y-axis label.
        filename: Output figure file name.
        horizontal: Draw horizontal bars when True.
        color: Bar colour, or a list of per-bar colours.
        log: Use a logarithmic value axis (helps when bars span orders of magnitude).

    Returns:
        Output figure file name.
    """
    plt.figure()
    kind = "barh" if horizontal else "bar"
    series.plot(kind=kind, color=color)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    if log:
        (plt.xscale if horizontal else plt.yscale)("log")
    if not horizontal:
        plt.xticks(rotation=45, ha="right")
    _save(filename)
    return filename


def hist(
    values: pd.Series,
    title: str,
    xlabel: str,
    filename: str,
    bins: int = 40,
    color: str = "#3b6ea5",
) -> str:
    """
    Render a histogram of numeric values.

    Args:
        values: Numeric series.
        title: Plot title.
        xlabel: X-axis label.
        filename: Output figure file name.
        bins: Number of histogram bins.
        color: Bar colour.

    Returns:
        Output figure file name.
    """
    values = pd.to_numeric(values, errors="coerce").dropna()
    plt.figure()
    plt.hist(values, bins=bins, color=color, edgecolor="white", linewidth=0.3)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel("count")
    _save(filename)
    return filename


def line(
    df: pd.DataFrame,
    title: str,
    xlabel: str,
    ylabel: str,
    filename: str,
    rotate: bool = True,
) -> str:
    """
    Render one or more lines from a DataFrame indexed by the x-axis.

    Args:
        df: DataFrame whose index is the x-axis and columns are series.
        title: Plot title.
        xlabel: X-axis label.
        ylabel: Y-axis label.
        filename: Output figure file name.
        rotate: Rotate x tick labels when True.

    Returns:
        Output figure file name.
    """
    plt.figure()
    if df.shape[1] > 8:
        # tab20 gives 20 distinct colors; avoids color cycling when there are
        # more series than the default tab10 cycle (10 colors).
        colors = [plt.cm.tab20(i / max(df.shape[1] - 1, 1)) for i in range(df.shape[1])]
        plt.gca().set_prop_cycle(color=colors)
    df.plot(ax=plt.gca(), marker="", linewidth=1.6)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    if df.shape[1] > 1:
        ncol = 3 if df.shape[1] > 6 else 2
        plt.legend(fontsize=8, ncol=ncol)
    if rotate:
        plt.xticks(rotation=45, ha="right")
    _save(filename)
    return filename


def stacked_area(
    df: pd.DataFrame,
    title: str,
    xlabel: str,
    ylabel: str,
    filename: str,
) -> str:
    """
    Render a stacked area chart (e.g. monthly composition shares).

    Args:
        df: DataFrame indexed by x-axis; columns stack as areas.
        title: Plot title.
        xlabel: X-axis label.
        ylabel: Y-axis label.
        filename: Output figure file name.

    Returns:
        Output figure file name.
    """
    plt.figure()
    plt.stackplot(df.index, df.T.values, labels=list(df.columns))
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.legend(fontsize=8, ncol=3, loc="upper left")
    plt.xticks(rotation=45, ha="right")
    plt.margins(x=0)
    _save(filename)
    return filename


def heatmap(
    df: pd.DataFrame,
    title: str,
    filename: str,
    cmap: str = "magma",
    annotate: bool = True,
    cbar_label: str = "",
) -> str:
    """
    Render a labelled heatmap from a 2D DataFrame.

    Args:
        df: DataFrame of values (rows and columns become axis ticks).
        title: Plot title.
        filename: Output figure file name.
        cmap: Matplotlib colormap name.
        annotate: Write cell values when True.
        cbar_label: Colour bar label.

    Returns:
        Output figure file name.
    """
    plt.figure(figsize=(max(6, 0.7 * len(df.columns) + 3), max(4, 0.5 * len(df) + 2)))
    data = df.to_numpy(dtype=float)
    im = plt.imshow(data, aspect="auto", cmap=cmap)
    plt.colorbar(im, label=cbar_label, fraction=0.046, pad=0.04)
    plt.xticks(range(len(df.columns)), df.columns, rotation=45, ha="right")
    plt.yticks(range(len(df.index)), df.index)
    if annotate:
        vmax = np.nanmax(data) if data.size else 1.0
        for i in range(data.shape[0]):
            for j in range(data.shape[1]):
                val = data[i, j]
                if np.isnan(val):
                    continue
                plt.text(
                    j, i, f"{val:.2f}",
                    ha="center", va="center", fontsize=7,
                    color="white" if val < 0.6 * vmax else "black",
                )
    plt.title(title)
    plt.grid(False)
    _save(filename)
    return filename


def scatter(
    x: pd.Series,
    y: pd.Series,
    labels: pd.Series,
    title: str,
    xlabel: str,
    ylabel: str,
    filename: str,
) -> str:
    """
    Render a labelled scatter plot of two community/channel-level metrics.

    Args:
        x: X values.
        y: Y values.
        labels: Point labels (drawn next to markers).
        title: Plot title.
        xlabel: X-axis label.
        ylabel: Y-axis label.
        filename: Output figure file name.

    Returns:
        Output figure file name.
    """
    plt.figure()
    plt.scatter(x, y, s=60, color="#3b6ea5", alpha=0.8, edgecolor="white")
    for xi, yi, lab in zip(x, y, labels):
        plt.annotate(str(lab), (xi, yi), fontsize=8, xytext=(4, 3),
                     textcoords="offset points")
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    _save(filename)
    return filename
