"""Spark session helpers for local development.

Provides a factory for a local Spark session configured with Delta Lake.
In Databricks, this module is not used because the platform provides
SparkSession and Delta out of the box.
"""

import os
from pathlib import Path
from typing import Optional

from delta import configure_spark_with_delta_pip
from pyspark.sql import SparkSession


def _resolve_warehouse_dir(warehouse_dir: Optional[str]) -> str:
    """Resolve the Spark warehouse directory.

    Resolution order:
        1. Explicit argument
        2. DELTA_WAREHOUSE_PATH environment variable
        3. Default: <project_root>/spark-warehouse, computed relative to
           this file, which only works when the code runs from a source
           checkout. Inside a container, DELTA_WAREHOUSE_PATH must be set.
    """
    if warehouse_dir is not None:
        return warehouse_dir

    env_path = os.getenv("DELTA_WAREHOUSE_PATH")
    if env_path:
        return env_path

    # Fallback: compute from the source tree layout.
    # This only works when running from a source checkout, not in a container.
    project_root = Path(__file__).resolve().parents[2]
    return str(project_root / "spark-warehouse")


def get_local_spark_session(
    app_name: str = "jc-sre-pipeline",
    warehouse_dir: Optional[str] = None,
) -> SparkSession:
    """Create a local Spark session with Delta Lake configured.

    Args:
        app_name: Spark application name.
        warehouse_dir: Directory for the Spark warehouse. If None, the
            DELTA_WAREHOUSE_PATH environment variable is used, and if
            that is also not set, a path relative to the source tree.

    Returns:
        Configured SparkSession.
    """
    resolved_dir = _resolve_warehouse_dir(warehouse_dir)

    # Only try to create the directory if it does not exist.
    # If it already exists (e.g., mounted as a read-only volume),
    # do not attempt to create it.
    if not os.path.isdir(resolved_dir):
        try:
            os.makedirs(resolved_dir, exist_ok=True)
        except PermissionError:
            # In read-only environments (e.g., mounted volumes in Kubernetes),
            # the directory must already exist and be writable only for reading.
            # Spark can read from a read-only warehouse as long as it does not
            # try to write. This is acceptable for the API server.
            pass

    builder = (
        SparkSession.builder.appName(app_name)
        .master("local[*]")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config(
            "spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        )
        .config("spark.sql.warehouse.dir", resolved_dir)
        .config("spark.databricks.delta.snapshotPartitions", "2")
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.ui.enabled", "false")
    )

    spark = configure_spark_with_delta_pip(builder).getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    return spark


def get_spark_session() -> SparkSession:
    """Return a SparkSession, preferring the existing one.

    In Databricks, returns the active session. In local development,
    creates a new one if needed.
    """
    return SparkSession.getActiveSession() or get_local_spark_session()