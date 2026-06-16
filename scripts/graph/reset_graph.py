import time
import subprocess
from pathlib import Path

from loguru import logger
from neo4j import GraphDatabase

from scripts.graph.v1.config import CONFIG
from scripts.utils.logger import setup_logger

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

setup_logger(__file__)

PROJECT_ROOT = CONFIG.project_root

NEO4J_DIR = PROJECT_ROOT / "neo4j"
NEO4J_DATA_DIR = NEO4J_DIR / "data"
NEO4J_LOGS_DIR = NEO4J_DIR / "logs"
NEO4J_IMPORT_DIR = NEO4J_DIR / "import"
NEO4J_PLUGINS_DIR = NEO4J_DIR / "plugins"

# ------------------------------------------------------------
# Docker and Neo4j management functions
# ------------------------------------------------------------


def run_command(command: list[str], cwd: Path = PROJECT_ROOT) -> None:
    """
    Run a subprocess command and raise an error if it fails.

    Args:
        command: Command and arguments to execute.
        cwd: Working directory for the subprocess.

    Returns:
        None.
    """
    # Log the command before execution for visibility.
    logger.info(f"Running: {' '.join(command)}")

    # Capture subprocess output so it can be logged and checked.
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
    )

    # Log captured standard output when present.
    if result.stdout:
        logger.info(result.stdout)

    # Log captured standard error when present.
    if result.stderr:
        logger.error(result.stderr)

    # Stop execution when the subprocess reports failure.
    if result.returncode != 0:
        raise RuntimeError(
            f"command failed with exit code {result.returncode}: {' '.join(command)}"
        )


def docker_delete_owned_path(path: Path) -> None:
    """
    Delete files that may be owned by the Neo4j Docker user.

    Uses an ephemeral Alpine container with the project directory mounted.
    This avoids sudo and avoids host permission errors.
    """
    # Convert the target to a project-relative path for the mounted container.
    relative_path = path.relative_to(PROJECT_ROOT)

    logger.info(f"Removing with docker: {relative_path}")

    # Remove the path inside an ephemeral container to avoid host permissions.
    run_command(
        [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{PROJECT_ROOT}:/workspace",
            "-w",
            "/workspace",
            "alpine:latest",
            "sh",
            "-c",
            f"rm -rf '{relative_path}'",
        ]
    )


def ensure_dirs() -> None:
    """
    Create required Neo4j host directories when they do not exist.

    Args:
        None.

    Returns:
        None.
    """
    # Ensure all mounted Neo4j directories exist before starting Docker.
    for path in [
        NEO4J_DATA_DIR,
        NEO4J_LOGS_DIR,
        NEO4J_IMPORT_DIR,
        NEO4J_PLUGINS_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured: {path}")


def wait_for_neo4j(timeout_seconds: int = 90) -> None:
    """
    Wait until Neo4j accepts connections or the timeout expires.

    Args:
        timeout_seconds: Maximum number of seconds to wait.

    Returns:
        None.
    """
    # Compute the time limit for connection attempts.
    deadline = time.time() + timeout_seconds

    # Retry connectivity checks until Neo4j responds or time expires.
    while time.time() < deadline:
        try:
            driver = GraphDatabase.driver(
                CONFIG.neo4j_uri,
                auth=(CONFIG.neo4j_user, CONFIG.neo4j_password),
            )

            try:
                # Verify that the database is reachable through the driver.
                driver.verify_connectivity()
                logger.info("Neo4j is reachable")
                return
            finally:
                # Close each temporary driver after the connection check.
                driver.close()

        except Exception as exc:
            # Keep waiting while the database container finishes startup.
            logger.info(f"Waiting for neo4j: {exc}")
            time.sleep(2)

    raise TimeoutError("neo4j did not become reachable in time")


def main() -> None:
    """
    Recreate the Neo4j Docker environment and verify connectivity.

    Args:
        None.

    Returns:
        None.
    """
    # Stop any existing Docker Compose services.
    run_command(["docker", "compose", "down"])

    # Remove Neo4j state and log directories through Docker.
    docker_delete_owned_path(NEO4J_DATA_DIR)
    docker_delete_owned_path(NEO4J_LOGS_DIR)

    # Recreate required host directories for Docker mounts.
    ensure_dirs()

    # Start the Docker Compose services in detached mode.
    run_command(["docker", "compose", "up", "-d"])

    # Wait for Neo4j to accept driver connections.
    wait_for_neo4j()

    logger.info("Hard reset complete")


if __name__ == "__main__":
    main()
