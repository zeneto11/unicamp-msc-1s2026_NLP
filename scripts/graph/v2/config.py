from pathlib import Path
from dataclasses import dataclass

from scripts.graph.v1.config import CONFIG as V1_CONFIG


@dataclass(frozen=True)
class GraphV2Config:
    """
    Store immutable paths and Neo4j settings for the V2 graph enrichment.

    V2 enriches the existing V1 graph in the same Neo4j database, so connection
    settings are reused from the V1 config. The import directory points at the
    V2 analysis artifacts produced under scripts.analysis.

    Args:
        None.

    Returns:
        GraphV2Config instance with default V2 graph configuration values.
    """
    # Name used for the V2 import directory (matches the analysis artifact dir).
    graph_name: str = "aletheia_pt_v2"

    # Resolve the repository root from this configuration file.
    project_root: Path = Path(__file__).resolve().parents[3]

    # V2 artifacts are written here by the analysis phases and loaded via file:///.
    import_root: Path = project_root / "neo4j" / "import"
    graph_import_dir: Path = import_root / graph_name

    # Reuse the V1 Neo4j connection settings (same database, enriched in place).
    neo4j_uri: str = V1_CONFIG.neo4j_uri
    neo4j_user: str = V1_CONFIG.neo4j_user
    neo4j_password: str = V1_CONFIG.neo4j_password
    neo4j_database: str = V1_CONFIG.neo4j_database


# Instantiate the shared V2 graph configuration.
CONFIG = GraphV2Config()
