from pathlib import Path
from dataclasses import dataclass


@dataclass(frozen=True)
class GraphConfig:
    """
    Store immutable paths and Neo4j connection settings for graph workflows.

    Args:
        None.

    Returns:
        GraphConfig instance with default graph configuration values.
    """
    # Name used for the graph-specific import directory.
    graph_name: str = "aletheia_pt_v1"

    # Resolve the repository root from this configuration file.
    project_root: Path = Path(__file__).resolve().parents[3]

    # Define source data and Neo4j import paths.
    raw_csv: Path = project_root / "data" / "aletheia_clean_pt.csv"
    import_root: Path = project_root / "neo4j" / "import"
    graph_import_dir: Path = import_root / graph_name

    # Define Neo4j connection settings.
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "aletheia2026"
    neo4j_database: str = "neo4j"


# Instantiate the shared graph configuration.
CONFIG = GraphConfig()
