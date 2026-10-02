"""Reads data from Delta Lake tables.

Encapsulates all direct Delta access so the routers stay thin.
"""

from typing import Optional


from src.api_server.config import (
    PROCESSED_MONTHLY_AGGREGATES,
    PROCESSED_SUMMARIES,
)
from src.api_server.services.spark_manager import get_session
from src.utils.logging import get_logger

logger = get_logger(__name__)


def is_delta_accessible() -> bool:
    """Check whether the Delta tables are accessible."""
    try:
        spark = get_session()
        spark.read.format("delta").load(PROCESSED_MONTHLY_AGGREGATES).limit(1).count()
        return True
    except Exception:
        logger.exception("Delta Lake is not accessible.")
        return False


def get_latest_for_series(series: str) -> Optional[dict]:
    """Return the latest month for a series."""
    spark = get_session()
    df = (
        spark.read.format("delta")
        .load(PROCESSED_MONTHLY_AGGREGATES)
        .filter(f"series = '{series}'")
        .orderBy("year_month", ascending=False)
        .limit(1)
    )
    rows = df.collect()
    if not rows:
        return None
    return rows[0].asDict()


def get_history_for_series(series: str, limit: int = 24) -> list[dict]:
    """Return the last `limit` months for a series, oldest first."""
    spark = get_session()
    df = (
        spark.read.format("delta")
        .load(PROCESSED_MONTHLY_AGGREGATES)
        .filter(f"series = '{series}'")
        .orderBy("year_month", ascending=False)
        .limit(limit)
        .orderBy("year_month", ascending=True)
    )
    return [row.asDict() for row in df.collect()]


def get_latest_summary() -> Optional[dict]:
    """Return the most recent executive summary."""
    spark = get_session()
    df = (
        spark.read.format("delta")
        .load(PROCESSED_SUMMARIES)
        .orderBy("generated_at", ascending=False)
        .limit(1)
    )
    rows = df.collect()
    if not rows:
        return None
    return rows[0].asDict()


def get_all_series_names() -> list[str]:
    """Return the distinct series names from the monthly aggregates."""
    spark = get_session()
    df = (
        spark.read.format("delta")
        .load(PROCESSED_MONTHLY_AGGREGATES)
        .select("series")
        .distinct()
    )
    return sorted(row["series"] for row in df.collect())
