"""Main entry point for the local pipeline execution.

Usage:
    python -m src.run_pipeline --start 2024-01-01 --end 2025-12-31
"""

# Workaround for Python 3.12 + PySpark 3.5.3: distutils was removed from stdlib.
# setuptools provides a vendored copy that becomes available upon import.
# See SPARK-47613: https://issues.apache.org/jira/browse/SPARK-47613
import setuptools  # noqa: F401  # isort: skip

import argparse
import time
from datetime import date, datetime

from dotenv import load_dotenv

# Load environment variables from .env before any module reads them
load_dotenv()

from src.pipeline.ingest import ingest_all_series  # noqa: E402
from src.pipeline.persist import write_processed, write_raw  # noqa: E402
from src.pipeline.transform import (  # noqa: E402
    add_time_dimensions,
    aggregate_monthly,
    compute_variation,
    transform_daily_to_annualized,
)
from src.pipeline.validate import validate_raw  # noqa: E402
from src.utils.logging import get_logger  # noqa: E402
from src.utils.metrics import (  # noqa: E402
    setup_metrics,
    shutdown_metrics,
    track_duration,
)
from src.utils.pipeline_metrics import initialize as initialize_metrics  # noqa: E402
from src.utils.spark import get_spark_session  # noqa: E402

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

    # Initialize observability before any business logic
    setup_metrics()
    metrics = initialize_metrics()

    spark = get_spark_session()
    pipeline_start = time.time()
    run_status = "success"

    try:
        # 1. Ingest
        logger.info("=== Step 1: Ingestion ===")
        with track_duration(metrics.duration_seconds, {"stage": "ingest"}):
            raw_df = ingest_all_series(spark, start, end)

        # 2. Validate
        logger.info("=== Step 2: Validation ===")
        with track_duration(metrics.duration_seconds, {"stage": "validate"}):
            validated_df = validate_raw(raw_df)

        # 3. Persist raw
        logger.info("=== Step 3: Persist raw ===")
        with track_duration(metrics.duration_seconds, {"stage": "persist_raw"}):
            write_raw(validated_df)

        # 4. Transform
        logger.info("=== Step 4: Transformation ===")
        with track_duration(metrics.duration_seconds, {"stage": "transform"}):
            with_time = add_time_dimensions(validated_df)
            annualized = transform_daily_to_annualized(with_time)
            variations = compute_variation(annualized)

        # 5. Aggregate
        logger.info("=== Step 5: Aggregation ===")
        with track_duration(metrics.duration_seconds, {"stage": "aggregate"}):
            monthly = aggregate_monthly(validated_df)

        # 6. Persist processed
        logger.info("=== Step 6: Persist processed ===")
        with track_duration(metrics.duration_seconds, {"stage": "persist_processed"}):
            write_processed(variations, "variations")
            write_processed(monthly, "monthly_aggregates")

        logger.info("Pipeline completed successfully.")

        # Emit success metrics
        metrics.last_success_timestamp.add(int(time.time()), attributes={})
        metrics.runs_total.add(1, attributes={"status": "success"})

    except Exception:
        run_status = "failure"
        metrics.runs_total.add(1, attributes={"status": "failure"})
        logger.exception("Pipeline failed.")
        raise

    finally:
        total_duration = time.time() - pipeline_start
        metrics.duration_seconds.record(
            total_duration, attributes={"stage": "total"}
        )
        logger.info("Total pipeline duration: %.2f seconds", total_duration)

        # Preview only when the run succeeded
        if run_status == "success":
            logger.info("=== Preview: Monthly aggregates ===")
            spark.read.format("delta").load(
                "./spark-warehouse/processed/monthly_aggregates"
            ).orderBy("series", "year_month").show(20, truncate=False)

        shutdown_metrics()
        spark.stop()


if __name__ == "__main__":
    main()