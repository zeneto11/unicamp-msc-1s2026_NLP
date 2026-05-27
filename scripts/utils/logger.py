"""Configure shared Loguru logging for project scripts."""

import sys
from pathlib import Path

from loguru import logger


LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level:<8}</level> | "
    "{function:<25} | "
    "{message}"
)


def build_log_name(script_path: Path) -> str:
    """
    Build a log file name from the script path below the scripts directory.

    Args:
        script_path: Path to the script being executed.

    Returns:
        Log file name derived from the script folder path and file stem.
    """
    script_path = script_path.resolve()

    # Find the scripts directory in the current file path.
    scripts_dir = next(
        parent for parent in script_path.parents if parent.name == "scripts"
    )

    # Use the path below scripts, excluding the file extension.
    relative_stem = script_path.relative_to(scripts_dir).with_suffix("")

    return "_".join(relative_stem.parts) + ".log"


def setup_logger(script_file: str | Path) -> Path:
    """
    Configure Loguru for terminal and file logging.

    Args:
        script_file: __file__ value from the calling script.

    Returns:
        Path to the configured log file.
    """
    script_path = Path(script_file).resolve()

    # Resolve project root as the parent of the scripts directory.
    scripts_dir = next(
        parent for parent in script_path.parents if parent.name == "scripts"
    )
    project_root = scripts_dir.parent

    # Build logs/name based on script path below scripts.
    log_file = project_root / "logs" / build_log_name(script_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Clear the previous run log before adding the file sink.
    log_file.write_text("", encoding="utf-8")

    # Remove default logger so only configured formats are used.
    logger.remove()

    # Log to terminal with colors.
    logger.add(
        sys.stdout,
        format=LOG_FORMAT,
        colorize=True,
    )

    # Log to file for reproducible script runs.
    logger.add(
        log_file,
        format=LOG_FORMAT,
        level="INFO",
        enqueue=True,
    )

    return log_file
