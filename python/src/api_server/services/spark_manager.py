"""Manages a shared SparkSession for the API server.

Creating a SparkSession is expensive (~5 seconds). The API server
creates one at startup and reuses it across requests.
"""

from typing import Optional

from pyspark.sql import SparkSession

from src.utils.logging import get_logger

logger = get_logger(__name__)

_session: Optional[SparkSession] = None


def get_session() -> SparkSession:
    """Return the shared SparkSession, creating it if necessary."""
    global _session

    if _session is not None:
        return _session

    # Try to reuse an existing session (in case one is already active)
    existing = SparkSession.getActiveSession()
    if existing is not None:
        _session = existing
        logger.info("Reusing existing SparkSession.")
        return _session

    logger.info("Creating a new SparkSession for the API server.")
    from src.utils.spark import get_local_spark_session

    _session = get_local_spark_session(app_name="jc-sre-api")
    logger.info("SparkSession created.")
    return _session


def stop_session() -> None:
    """Stop the shared SparkSession."""
    global _session

    if _session is None:
        return

    try:
        _session.stop()
        logger.info("SparkSession stopped.")
    except Exception:
        logger.exception("Error stopping SparkSession.")
    finally:
        _session = None
