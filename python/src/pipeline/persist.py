"""Data persistence module.

Writes DataFrames to Delta Lake tables, both locally and to ADLS Gen2.
"""

import os

from pyspark.sql import DataFrame

from src.utils.logging import get_logger

logger = get_logger(__name__)

# Default local paths (relative to project root)
DEFAULT_RAW_PATH = "./spark-warehouse/raw"
DEFAULT_PROCESSED_PATH = "./spark-warehouse/processed"


def write_delta(
    df: DataFrame,
    path: str,
    mode: str = "overwrite",
    partition_by: list[str] | None = None,
) -> None:
    """Write a DataFrame to a Delta table.

    Args:
        df: DataFrame to write.
        path: Target path (local or abfss://).
        mode: Write mode ("overwrite", "append", "error").
        partition_by: Optional list of partition columns.
    """
    writer = df.write.format("delta").mode(mode)

    if partition_by:
        writer = writer.partitionBy(*partition_by)

    writer.save(path)
    logger.info("Wrote %d rows to %s (mode=%s)", df.count(), path, mode)


def write_raw(df: DataFrame, base_path: str = DEFAULT_RAW_PATH) -> None:
    """Write raw ingested data to Delta, partitioned by series."""
    write_delta(df, base_path, mode="overwrite", partition_by=["series"])


def write_processed(
    df: DataFrame,
    table_name: str,
    base_path: str = DEFAULT_PROCESSED_PATH,
) -> None:
    """Write processed data to a named Delta table."""
    path = os.path.join(base_path, table_name)
    write_delta(df, path, mode="overwrite")


def read_delta(spark, path: str) -> DataFrame:
    """Read a Delta table from the given path."""
    return spark.read.format("delta").load(path)