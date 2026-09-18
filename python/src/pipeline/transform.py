"""Data transformation module.

Applies business logic: enrichment, aggregation, derived fields.
"""

from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F

from src.utils.logging import get_logger

logger = get_logger(__name__)

# Average number of business days per year used for annualization
BUSINESS_DAYS_PER_YEAR = 252


def transform_daily_to_annualized(df: DataFrame) -> DataFrame:
    """Convert daily rates to annualized rates.

    For daily series (Selic, CDI), the annualized rate is computed as:
        annualized = ((1 + daily/100)^252 - 1) * 100

    This is the standard convention for Brazilian fixed income[citation:9].
    """
    daily_df = df.filter(F.col("frequency") == "daily")

    annualized_df = daily_df.withColumn(
        "value_annualized",
        (F.pow(1 + F.col("value") / 100, F.lit(BUSINESS_DAYS_PER_YEAR)) - 1) * 100,
    ).withColumn("unit_annualized", F.lit("% per year"))

    return annualized_df


def add_time_dimensions(df: DataFrame) -> DataFrame:
    """Add derived time dimensions (year, month, day, weekday)."""
    return (
        df.withColumn("year", F.year("date"))
        .withColumn("month", F.month("date"))
        .withColumn("day", F.dayofmonth("date"))
        .withColumn("weekday", F.dayofweek("date"))
    )


def aggregate_monthly(df: DataFrame) -> DataFrame:
    """Aggregate daily series into monthly statistics.

    Produces per-series, per-month metrics:
        - mean_value: average daily value in the month
        - min_value, max_value: extremes in the month
        - stddev_value: volatility within the month
        - observation_count: number of data points in the month
    """
    monthly = (
        df.withColumn("year_month", F.date_format("date", "yyyy-MM"))
        .groupBy("series", "year_month")
        .agg(
            F.avg("value").alias("mean_value"),
            F.min("value").alias("min_value"),
            F.max("value").alias("max_value"),
            F.stddev("value").alias("stddev_value"),
            F.count("value").alias("observation_count"),
        )
        .withColumn("year", F.year(F.to_date("year_month", "yyyy-MM")))
        .withColumn("month", F.month(F.to_date("year_month", "yyyy-MM")))
    )

    return monthly


def compute_variation(df: DataFrame) -> DataFrame:
    """Compute day-over-day and month-over-month variation for each series."""
    window = Window.partitionBy("series").orderBy("date")

    return (
        df.withColumn("previous_value", F.lag("value").over(window))
        .withColumn(
            "variation_absolute",
            F.col("value") - F.col("previous_value"),
        )
        .withColumn(
            "variation_percent",
            F.when(
                F.col("previous_value").isNotNull()
                & (F.col("previous_value") != 0),
                ((F.col("value") - F.col("previous_value")) / F.col("previous_value"))
                * 100,
            ),
        )
        .drop("previous_value")
    )