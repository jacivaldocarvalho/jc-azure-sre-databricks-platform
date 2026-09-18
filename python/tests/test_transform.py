"""Unit tests for transformation functions."""

from datetime import date

import pytest

from src.pipeline.transform import (
    add_time_dimensions,
    compute_variation,
    transform_daily_to_annualized,
)


@pytest.fixture
def sample_df(spark_session):
    """Create a sample daily rates DataFrame for testing."""
    data = [
        ("selic", date(2024, 1, 2), 0.039167, "% per day", "daily"),
        ("selic", date(2024, 1, 3), 0.039167, "% per day", "daily"),
        ("selic", date(2024, 1, 4), 0.039167, "% per day", "daily"),
    ]
    return spark_session.createDataFrame(data, ["series", "date", "value", "unit", "frequency"])


def test_annualization(sample_df):
    """Annualized value is correctly computed from daily rate."""
    result = transform_daily_to_annualized(sample_df)
    row = result.first()

    # Expected: ((1 + 0.039167/100)^252 - 1) * 100 ≈ 10.35
    expected = ((1 + 0.039167 / 100) ** 252 - 1) * 100
    assert abs(row["value_annualized"] - expected) < 0.01


def test_add_time_dimensions(sample_df):
    """Time dimensions are correctly extracted."""
    result = add_time_dimensions(sample_df)
    row = result.first()

    assert row["year"] == 2024
    assert row["month"] == 1
    assert row["day"] == 2
    assert row["weekday"] == 3  # Tuesday (dayofweek: 1=Sunday)


def test_compute_variation(sample_df):
    """Variation is correctly computed between consecutive rows."""
    result = compute_variation(sample_df)
    rows = result.orderBy("date").collect()

    # First row has no previous value
    assert rows[0]["variation_absolute"] is None

    # Subsequent rows have zero variation (same value)
    assert rows[1]["variation_absolute"] == 0.0
