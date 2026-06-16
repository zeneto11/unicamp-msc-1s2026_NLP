from pathlib import Path

from loguru import logger
from neo4j import GraphDatabase

from scripts.graph.v2.config import CONFIG
from scripts.utils.logger import setup_logger

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

setup_logger(__file__)

CYPHER_DIR = Path(__file__).resolve().parent / "cypher"

# Each load step lists the artifact CSVs it requires. A step is skipped when any
# required artifact is missing, so partial pipeline runs still load cleanly.
# constraints/metadata have no data dependencies and always run.
LOAD_STEPS: list[tuple[str, list[str]]] = [
    ("constraints.cypher", []),
    ("metadata.cypher", []),
    ("load_communities.cypher", ["communities.csv", "channel_community.csv"]),
    ("load_topics.cypher", ["topics.csv", "message_topics.csv"]),
    ("load_similarity.cypher", ["message_similarity.csv"]),
    ("load_emotions.cypher", ["message_emotions.csv"]),
]

# ------------------------------------------------------------
# Load graph into Neo4j
# ------------------------------------------------------------


def split_cypher_statements(text: str) -> list[str]:
    """
    Split Cypher text into individual non-empty statements.

    Args:
        text: Cypher script text to split.

    Returns:
        List of stripped Cypher statements.
    """
    # Split on semicolons and discard empty statements.
    return [stmt.strip() for stmt in text.split(";") if stmt.strip()]


def run_file(driver, filename: str) -> None:
    """
    Execute all Cypher statements from a file against the configured database.

    Args:
        driver: Neo4j driver used to execute statements.
        filename: Name of the Cypher file to run.

    Returns:
        None.
    """
    # Read the target Cypher script from the local cypher directory.
    path = CYPHER_DIR / filename
    text = path.read_text(encoding="utf-8")

    # Execute each parsed statement in the configured Neo4j database.
    for statement in split_cypher_statements(text):
        logger.info(f"Running: {filename}")
        driver.execute_query(statement, database_=CONFIG.neo4j_database)


def artifacts_present(required: list[str]) -> bool:
    """
    Check that every required artifact exists in the V2 import directory.

    Args:
        required: Artifact file names the load step depends on.

    Returns:
        True when all required artifacts are present.
    """
    missing = [
        name for name in required
        if not (CONFIG.graph_import_dir / name).exists()
    ]
    if missing:
        logger.warning(f"Missing artifacts {missing}; skipping dependent load step.")
        return False
    return True


def main() -> None:
    """
    Connect to Neo4j and run the V2 enrichment Cypher files in order.

    Steps whose artifacts are absent are skipped so the loader tolerates partial
    analysis runs (for example loading only the emotion layer).

    Args:
        None.

    Returns:
        None.
    """
    # Create a Neo4j driver using configured connection settings.
    driver = GraphDatabase.driver(
        CONFIG.neo4j_uri,
        auth=(CONFIG.neo4j_user, CONFIG.neo4j_password),
    )

    try:
        # Verify the connection before running enrichment scripts.
        driver.verify_connectivity()

        # Run each load step when its required artifacts are present.
        for filename, required in LOAD_STEPS:
            if artifacts_present(required):
                run_file(driver, filename)
    finally:
        # Always close the driver after import execution.
        driver.close()

    logger.info("Graph V2 enrichment loaded")


if __name__ == "__main__":
    main()
