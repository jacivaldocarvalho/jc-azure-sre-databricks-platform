"""Data validation module.

Applies schema and quality checks to ingested DataFrames using Pandera.
"""

import pandera.pyspark as pa
from pandera.pyspark import Check, Column, DataFrameSchema
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import DateType, DoubleType, StringType, TimestampType

from src.utils.logging import get_logger
from src.utils.pipeline_metrics import initialize as initialize_metrics

logger = get_logger(__name__)


# Declarative schema for the ingested raw data
RAW_SCHEMA = DataFrameSchema(
    columns={
        "series": Column(
            StringType(),
            checks=Check.isin(["selic", "cdi", "ipca"]),
            nullable=False,
        ),
        "date": Column(
            DateType(),
            nullable=False,
        ),
        "value": Column(
            DoubleType(),
            nullable=False,
        ),
        "unit": Column(
            StringType(),
            nullable=False,
        ),
        "frequency": Column(
            StringType(),
            checks=Check.isin(["daily", "monthly"]),
            nullable=False,
        ),
        "ingested_at": Column(
            TimestampType(),
            nullable=False,
        ),
    },
    strict=True,
    coerce=False,
)


def validate_raw(df: DataFrame, raise_on_failure: bool = True) -> DataFrame:
    """Validate the ingested DataFrame against the expected schema.

    Uses Pandera to enforce:
        - Correct column types
        - Allowed values for 'series' and 'frequency'
        - No null values in any column
        - No extra columns (strict schema)

    Additionally performs quality checks for duplicates and empty input.

    Args:
        df: DataFrame to validate.
        raise_on_failure: If True, raises on schema violation. If False,
            logs a warning and returns the DataFrame unchanged.

    Returns:
        The validated DataFrame (same as input).

    Raises:
        ValueError: If the DataFrame is empty.
        pa.errors.SchemaError: If schema validation fails (when raise_on_failure=True).
    """
    logger.info("Validating ingested DataFrame against schema...")

    metrics = initialize_metrics()

    # Check for empty input before schema validation
    total = df.count()
    if total == 0:
        raise ValueError("DataFrame is empty, cannot validate.")

    # Apply Pandera schema validation
    # Note: pandera.pyspark performs lazy validation by default. We pass
    # lazy=False to surface schema violations immediately as exceptions.
    try:
        validated_df = RAW_SCHEMA.validate(df, lazy=False)
        logger.info("Schema validation passed for %d rows.", total)
    except (pa.errors.SchemaError, pa.errors.SchemaErrors) as exc:
        logger.error("Schema validation failed: %s", exc)
        if raise_on_failure:
            raise
        logger.warning("Continuing despite schema violations (raise_on_failure=False).")
        validated_df = df

    # Additional quality check: duplicates by (series, date)
    duplicate_count = (
        validated_df.groupBy("series", "date")
        .count()
        .filter(F.col("count") > 1)
        .count()
    )
    if duplicate_count > 0:
        logger.warning(
            "Found %d duplicate (series, date) combinations.",
            duplicate_count,
        )
        metrics.rows_rejected_total.add(
            duplicate_count,
            attributes={"reason": "duplicate"},
        )

    # Summary of the validated data
    date_stats = validated_df.agg(
        F.min("date").alias("min_date"),
        F.max("date").alias("max_date"),
        F.countDistinct("series").alias("distinct_series"),
    ).collect()[0]

    logger.info(
        "Validation summary: %d rows, %d series, date range %s to %s",
        total,
        date_stats["distinct_series"],
        date_stats["min_date"],
        date_stats["max_date"],
    )

    return validated_df