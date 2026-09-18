"""Data ingestion module.

Fetches historical Brazilian economic series from the Central Bank SGS API
and converts them into Spark DataFrames.
"""

from datetime import date

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, StringType, StructField, StructType

from src.api.bcb_sgs import SERIES, fetch_series
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Schema for the raw data returned by the SGS API
RAW_SCHEMA = StructType(
    [
        StructField("data", StringType(), nullable=False),
        StructField("valor", StringType(), nullable=False),
    ]
)


def ingest_series(
    spark: SparkSession,
    series_key: str,
    start: date,
    end: date,
) -> DataFrame:
    """Ingest a single SGS series into a Spark DataFrame.

    Args:
        spark: Active Spark session.
        series_key: Key in SERIES dict (e.g., "selic").
        start: Start date.
        end: End date.

    Returns:
        DataFrame with columns: series, date, value.
    """
    config = SERIES[series_key]
    raw_records = fetch_series(series_key, start, end)

    if not raw_records:
        logger.warning("No records returned for series '%s'", series_key)
        return spark.createDataFrame([], schema=RAW_SCHEMA).withColumn(
            "series", F.lit(series_key)
        )

    df_raw = spark.createDataFrame(raw_records, schema=RAW_SCHEMA)

    df = (
        df_raw.withColumn("series", F.lit(series_key))
        .withColumn(
            "date",
            F.to_date(F.to_timestamp("data", "dd/MM/yyyy")),
        )
        .withColumn("value", F.col("valor").cast(DoubleType()))
        .withColumn("unit", F.lit(config.unit))
        .withColumn("frequency", F.lit(config.frequency))
        .withColumn("ingested_at", F.current_timestamp())
        .select("series", "date", "value", "unit", "frequency", "ingested_at")
    )

    logger.info(
        "Ingested series '%s': %d rows, %s to %s",
        series_key,
        df.count(),
        df.agg(F.min("date")).collect()[0][0],
        df.agg(F.max("date")).collect()[0][0],
    )

    return df


def ingest_all_series(
    spark: SparkSession,
    start: date,
    end: date,
) -> DataFrame:
    """Ingest all configured series and union them into a single DataFrame.

    Args:
        spark: Active Spark session.
        start: Start date.
        end: End date.

    Returns:
        Union of all series DataFrames.
    """
    frames = []
    for series_key in SERIES:
        try:
            frames.append(ingest_series(spark, series_key, start, end))
        except Exception:
            logger.exception("Failed to ingest series '%s'", series_key)

    if not frames:
        raise RuntimeError("No series could be ingested.")

    result = frames[0]
    for frame in frames[1:]:
        result = result.unionByName(frame)

    return result