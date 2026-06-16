from loguru import logger
from neo4j import GraphDatabase

from scripts.graph.v1.config import CONFIG
from scripts.utils.logger import setup_logger

setup_logger(__file__)


def main() -> None:
    """
    Connect to Neo4j and delete all graph data from the configured database.

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
        # Verify the database connection before running the delete query.
        driver.verify_connectivity()

        # Delete every node and relationship from the configured database.
        driver.execute_query(
            """
            MATCH (n)
            DETACH DELETE n
            """,
            database_=CONFIG.neo4j_database,
        )

        logger.info("deleted all nodes and relationships")

    finally:
        # Always close the driver after the database operation.
        driver.close()


if __name__ == "__main__":
    main()
