"""Pytest fixtures shared across tests."""

import sys
from pathlib import Path

import pytest

# Ensure the src package is importable
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="session")
def spark_session():
    """Provide a local Spark session for tests that need it.

    Session-scoped to avoid starting Spark multiple times.
    """
    from src.utils.spark import get_local_spark_session

    spark = get_local_spark_session(app_name="jc-sre-test")
    yield spark
    spark.stop()