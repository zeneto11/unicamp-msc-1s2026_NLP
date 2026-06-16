import sys
from pathlib import Path

from loguru import logger
from neo4j import GraphDatabase

from scripts.graph.v1.config import CONFIG
from scripts.utils.logger import setup_logger

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

setup_logger(__file__)

CYPHER_DIR = Path(__file__).resolve().parent / "cypher"

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
    return [
        stmt.strip()
        for stmt in text.split(";")
        if stmt.strip()
    ]


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


def main() -> None:
    """
    Connect to Neo4j and run the graph import Cypher files.

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
        # Verify the connection before running import scripts.
        driver.verify_connectivity()

        # Run schema, metadata, node, and relationship loading scripts.
        run_file(driver, "constraints.cypher")
        run_file(driver, "metadata.cypher")
        run_file(driver, "load_nodes.cypher")
        run_file(driver, "load_relationships.cypher")
        # Derived relations depend on all base relationships being loaded first.
        run_file(driver, "load_derived.cypher")
    finally:
        # Always close the driver after import execution.
        driver.close()

    logger.info("Graph loaded")


if __name__ == "__main__":
    main()
