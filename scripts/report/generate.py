"""Generate the Aletheia Graph V2 Markdown report.

Loads the V1/V2 CSV artifacts, builds shared aggregates, runs every section
builder in order, and writes a single markdown file plus its figures.

Run from the repository root:

    python -m scripts.report.generate
"""
from datetime import date

from loguru import logger

from scripts.report.config import CONFIG
from scripts.report.loader import load_report_data
from scripts.report import sections, viz
from scripts.utils.logger import setup_logger


setup_logger(__file__)


def _header() -> str:
    """
    Build the report title and generation banner.

    Args:
        None.

    Returns:
        Markdown header string.
    """
    return "\n".join([
        "# Aletheia-PT — Graph V2 Analytical Report",
        "",
        "_Structural, community, topic, semantic, and emotional analysis of the "
        "Portuguese Aletheia Telegram corpus. Generated automatically by "
        "`scripts/report/generate.py` from the V1/V2 graph artifacts._",
        "",
        f"_Generated: {date.today():%Y-%m-%d}_",
        "",
        "---",
        "",
    ])


def main() -> None:
    """
    Build and write the full V2 markdown report.

    Args:
        None.

    Returns:
        None.
    """
    logger.info("Starting Graph V2 report generation.")
    CONFIG.ensure_dirs()
    viz.setup_style()

    data = load_report_data()
    ctx = sections.build_context(data)

    parts = [_header()]
    for builder in sections.SECTIONS:
        logger.info(f"Building {builder.__name__}")
        parts.append(builder(data, ctx))
        parts.append("---\n")

    # Drop the trailing separator for a clean ending.
    if parts and parts[-1] == "---\n":
        parts.pop()

    report = "\n".join(parts)
    CONFIG.report_path.write_text(report, encoding="utf-8")

    logger.info(
        f"Report written: {CONFIG.report_path} "
        f"({len(report.splitlines())} lines, figures in {CONFIG.figures_dir})."
    )


if __name__ == "__main__":
    main()
