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


def get_local_spark_session(
    app_name: str = "jc-sre-pipeline",
    warehouse_dir: Optional[str] = None,
) -> SparkSession:
    """Create a local Spark session with Delta Lake configured.

    Args:
        app_name: Spark application name.
        warehouse_dir: Directory for the Spark warehouse. Defaults to
            ./spark-warehouse relative to the project root.

    Returns:
        Configured SparkSession.
    """
    if warehouse_dir is None:
        project_root = Path(__file__).resolve().parents[3]
        warehouse_dir = str(project_root / "spark-warehouse")

    os.makedirs(warehouse_dir, exist_ok=True)

    builder = (
        SparkSession.builder.appName(app_name)
        .master("local[*]")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config(
            "spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        )
        .config("spark.sql.warehouse.dir", warehouse_dir)
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