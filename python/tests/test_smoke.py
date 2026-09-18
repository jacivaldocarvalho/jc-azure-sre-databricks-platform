"""Smoke tests to validate the environment setup."""

from src.utils.logging import get_logger


def test_logger_creation():
    """Logger can be created and used."""
    logger = get_logger("test")
    assert logger is not None
    assert logger.name == "test"


def test_spark_session_available(spark_session):
    """Spark session is available and functional."""
    assert spark_session is not None
    assert spark_session.version.startswith("3.5")

    # Simple operations to confirm Spark works
    df = spark_session.createDataFrame([(1, "a"), (2, "b")], ["id", "value"])
    assert df.count() == 2
    assert df.columns == ["id", "value"]


def test_delta_extension_loaded(spark_session):
    """Delta Lake extension is loaded and usable."""
    from delta.tables import DeltaTable  # noqa: F401

    # Creating a Delta table is the definitive test
    df = spark_session.createDataFrame([(1, "a")], ["id", "value"])
    df.write.format("delta").mode("overwrite").save("/tmp/jc-sre-test-delta")

    result = spark_session.read.format("delta").load("/tmp/jc-sre-test-delta")
    assert result.count() == 1
