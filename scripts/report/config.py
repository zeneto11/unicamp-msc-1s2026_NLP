"""Configuration for the Graph V2 Markdown report generator.

Centralizes input artifact locations (reused from the analysis pipeline), output
paths, presentation constants (top-N caps, thresholds), and the shared matplotlib
style. Reading the V1/V2 import CSVs directly keeps the report reproducible and
free of any live-Neo4j dependency — those CSVs are the graph definition.
"""
from pathlib import Path
from dataclasses import dataclass

from scripts.analysis.config import EMOTION_CATEGORIES, POLARITY_CATEGORIES


@dataclass(frozen=True)
class ReportConfig:
    """
    Immutable paths and presentation parameters for the V2 report.

    Args:
        None.

    Returns:
        ReportConfig instance with default report configuration values.
    """
    # Resolve the repository root from this configuration file.
    project_root: Path = Path(__file__).resolve().parents[2]

    # Inputs: the V1 import CSVs and V2 enrichment artifacts.
    import_root: Path = project_root / "neo4j" / "import"
    v1_dir: Path = import_root / "aletheia_pt_v1"
    v2_dir: Path = import_root / "aletheia_pt_v2"

    # Outputs: the markdown report and its figure directory.
    report_path: Path = project_root / "reports" / "final_report.md"
    figures_dir: Path = project_root / "reports" / "figures" / "final_report"
    # Path prefix written into markdown image links (relative to the report file).
    figures_rel: str = "figures/final_report"

    # Emotion / polarity vocabularies shared with Phase 4.
    emotion_categories: tuple[str, ...] = tuple(EMOTION_CATEGORIES)
    polarity_categories: tuple[str, ...] = tuple(POLARITY_CATEGORIES)

    # The BERTopic noise/outlier topic id, excluded from topic rankings.
    noise_topic_id: int = -1
    # Phase 3 cosine threshold (used for narrative, not recomputation).
    similarity_threshold: float = 0.80

    # Presentation caps — main-body tables stay compact; large ones go to appendix.
    top_n_table: int = 10
    top_n_table_wide: int = 15
    top_communities: int = 8
    top_topics: int = 12
    top_emotion_communities: int = 8

    # Matplotlib defaults applied once at startup.
    fig_dpi: int = 150
    fig_size: tuple[int, int] = (10, 6)

    def ensure_dirs(self) -> None:
        """
        Create the report and figure output directories when missing.

        Args:
            None.

        Returns:
            None.
        """
        self.figures_dir.mkdir(parents=True, exist_ok=True)
        self.report_path.parent.mkdir(parents=True, exist_ok=True)


# Instantiate the shared report configuration.
CONFIG = ReportConfig()
