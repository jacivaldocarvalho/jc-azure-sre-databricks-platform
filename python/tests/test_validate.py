"""Unit tests for validation functions."""

from datetime import date, datetime

import pytest

from src.pipeline.validate import validate_raw


@pytest.fixture
def valid_df(spark_session):
    """DataFrame that should pass validation."""
    data = [
        ("selic", date(2024, 1, 2), 0.039167, "% per day", "daily", datetime(2024, 1, 2, 12, 0, 0)),
        ("cdi", date(2024, 1, 2), 0.039167, "% per day", "daily", datetime(2024, 1, 2, 12, 0, 0)),
        ("ipca", date(2024, 1, 1), 0.42, "% per month", "monthly", datetime(2024, 1, 1, 12, 0, 0)),
    ]
    return spark_session.createDataFrame(
        data,
        ["series", "date", "value", "unit", "frequency", "ingested_at"],
    )


@pytest.fixture
def invalid_series_df(spark_session):
    """DataFrame with an invalid series value."""
    data = [
        ("bitcoin", date(2024, 1, 2), 0.039, "% per day", "daily", datetime(2024, 1, 2, 12, 0, 0)),
    ]
    return spark_session.createDataFrame(
        data,
        ["series", "date", "value", "unit", "frequency", "ingested_at"],
    )


def test_valid_dataframe_passes(valid_df):
    """A well-formed DataFrame passes validation."""
    result = validate_raw(valid_df)
    assert result.count() == 3


def test_invalid_series_raises(invalid_series_df):
    """An invalid series value raises a schema error.

    Pandera pyspark performs lazy validation. The validate_raw function
    forces execution via cache().count(), so violations are surfaced
    as schema errors.
    """
    import pandera.pyspark as pa

    schema_errors = (
        pa.errors.SchemaError,
        pa.errors.SchemaErrors,
    )

    with pytest.raises(schema_errors):
        validate_raw(invalid_series_df)


def test_invalid_series_does_not_raise_when_disabled(invalid_series_df):
    """With raise_on_failure=False, validation logs but does not raise."""
    result = validate_raw(invalid_series_df, raise_on_failure=False)
    assert result.count() == 1


def test_empty_dataframe_raises(spark_session):
    """An empty DataFrame raises ValueError."""
    empty = spark_session.createDataFrame(
        [],
        "series string, date date, value double, unit string, frequency string, ingested_at timestamp",
    )
    with pytest.raises(ValueError, match="DataFrame is empty"):
        validate_raw(empty)