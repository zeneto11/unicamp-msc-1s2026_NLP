import pandas as pd
from loguru import logger

from scripts.analysis.config import CONFIG


def write_artifact(df: pd.DataFrame, name: str) -> None:
    """
    Write a DataFrame to the V2 artifact directory for Neo4j import.

    Mirrors the V1 write_csv convention: empty strings instead of NA so that
    Neo4j LOAD CSV reads clean values.

    Args:
        df: DataFrame to write.
        name: Output CSV file name.

    Returns:
        None.
    """
    # Ensure the artifact directory exists before writing.
    CONFIG.ensure_artifact_dir()

    path = CONFIG.artifact_dir / name

    # Work on a copy so missing-value handling does not affect callers.
    df = df.copy()

    # Neo4j LOAD CSV handles empty strings better than pandas NA values.
    df = df.fillna("")

    # Write the CSV and report the generated file size by row count.
    df.to_csv(path, index=False)
    logger.info(f"Wrote {path} rows={len(df)}")


def list_to_pipe(values: list) -> str:
    """
    Join a list into a pipe-delimited string for LOAD CSV split() parsing.

    Cypher reads these back with split(value, '|'), avoiding an APOC JSON
    dependency for list/array properties such as keywords and embeddings.

    Args:
        values: List of scalar values to join.

    Returns:
        Pipe-delimited string representation.
    """
    return "|".join(str(v) for v in values)
