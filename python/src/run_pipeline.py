"""Main entry point for the local pipeline execution.

Usage:
    python -m src.run_pipeline --start 2024-01-01 --end 2025-12-31
"""
# Workaround for Python 3.12 + PySpark 3.5.3: distutils was removed from stdlib
# setuptools provides a vendored copy that becomes available upon import.
# See SPARK-47613: https://issues.apache.org/jira/browse/SPARK-47613
import setuptools  # noqa: F401  # isort: skip

import argparse
from datetime import date, datetime

from src.pipeline.ingest import ingest_all_series
from src.pipeline.persist import write_processed, write_raw
from src.pipeline.transform import (
    add_time_dimensions,
    aggregate_monthly,
    compute_variation,
    transform_daily_to_annualized,
)
from src.pipeline.validate import validate_raw
from src.utils.logging import get_logger
from src.utils.spark import get_spark_session

logger = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the local data pipeline")
    parser.add_argument(
        "--start",
        type=str,
        default=(date.today().replace(year=date.today().year - 1)).isoformat(),
        help="Start date (YYYY-MM-DD). Default: 1 year ago.",
    )
    parser.add_argument(
        "--end",
        type=str,
        default=date.today().isoformat(),
        help="End date (YYYY-MM-DD). Default: today.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    start = datetime.strptime(args.start, "%Y-%m-%d").date()
    end = datetime.strptime(args.end, "%Y-%m-%d").date()

    logger.info("Starting pipeline: %s to %s", start, end)

    spark = get_spark_session()

    # 1. Ingest
    logger.info("=== Step 1: Ingestion ===")
    raw_df = ingest_all_series(spark, start, end)

    # 2. Validate
    logger.info("=== Step 2: Validation ===")
    validated_df = validate_raw(raw_df)

    # 3. Persist raw
    logger.info("=== Step 3: Persist raw ===")
    write_raw(validated_df)

    # 4. Transform
    logger.info("=== Step 4: Transformation ===")
    with_time = add_time_dimensions(validated_df)
    annualized = transform_daily_to_annualized(with_time)
    variations = compute_variation(annualized)

    # 5. Aggregate
    logger.info("=== Step 5: Aggregation ===")
    monthly = aggregate_monthly(validated_df)

    # 6. Persist processed
    logger.info("=== Step 6: Persist processed ===")
    write_processed(variations, "variations")
    write_processed(monthly, "monthly_aggregates")

    logger.info("Pipeline completed successfully.")

    # 7. Quick validation query
    logger.info("=== Preview: Monthly aggregates ===")
    spark.read.format("delta").load("./spark-warehouse/processed/monthly_aggregates").orderBy(
        "series", "year_month"
    ).show(20, truncate=False)

    spark.stop()


if __name__ == "__main__":
    main()