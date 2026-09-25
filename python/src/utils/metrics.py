"""Metrics collection and export for the pipeline.

Provides a Prometheus-compatible API surface backed by OpenTelemetry.
Metrics are exported to Azure Monitor Workspace via OTLP.

When the Azure Monitor endpoint is not configured, metrics are only
recorded locally (no export). This allows running the pipeline in
environments without observability configured.
"""

import os
import time
from contextlib import contextmanager
from typing import Optional

from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource

from src.utils.logging import get_logger

logger = get_logger(__name__)

# Module-level provider, initialized once
_provider: Optional[MeterProvider] = None
_meter: Optional[metrics.Meter] = None


def _create_resource() -> Resource:
    """Create the OTel resource describing this service."""
    return Resource.create(
        {
            "service.name": "jc-sre-databricks-pipeline",
            "service.namespace": "sre-databricks",
            "service.version": "0.1.0",
            "deployment.environment": os.getenv("ENVIRONMENT", "dev"),
        }
    )


def _create_exporter():
    """Create the Azure Monitor exporter if the endpoint is configured.

    Returns None if the connection string is not set, in which case
    metrics are collected but not exported.
    """
    connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if not connection_string:
        logger.warning(
            "APPLICATIONINSIGHTS_CONNECTION_STRING not set. "
            "Metrics will be recorded but not exported."
        )
        return None

    try:
        from azure.monitor.opentelemetry.exporter import AzureMonitorMetricExporter

        exporter = AzureMonitorMetricExporter(
            connection_string=connection_string
        )
        logger.info("Azure Monitor metrics exporter configured.")
        return exporter
    except Exception:
        logger.exception("Failed to create Azure Monitor exporter.")
        return None


def setup_metrics(export_interval_seconds: int = 30) -> None:
    """Initialize the metrics provider and exporter.

    Should be called once at pipeline startup, before creating any
    instruments.

    Args:
        export_interval_seconds: How often metrics are flushed to the
            backend. Defaults to 30 seconds.
    """
    global _provider, _meter

    if _provider is not None:
        logger.debug("Metrics already initialized.")
        return

    resource = _create_resource()
    exporter = _create_exporter()

    if exporter is not None:
        reader = PeriodicExportingMetricReader(
            exporter,
            export_interval_millis=export_interval_seconds * 1000,
        )
        _provider = MeterProvider(resource=resource, metric_readers=[reader])
    else:
        # No exporter: use a no-op provider that still records metrics
        _provider = MeterProvider(resource=resource)

    metrics.set_meter_provider(_provider)
    _meter = _provider.get_meter("jc-sre-databricks-pipeline")

    logger.info("Metrics provider initialized.")


def get_meter() -> metrics.Meter:
    """Return the configured meter, initializing if necessary."""
    if _meter is None:
        setup_metrics()
    assert _meter is not None
    return _meter


def shutdown_metrics() -> None:
    """Flush and shut down the metrics provider.

    Should be called at the end of the pipeline to ensure all metrics
    are exported before the process exits.
    """
    global _provider

    if _provider is None:
        return

    try:
        _provider.shutdown()
        logger.info("Metrics provider shut down cleanly.")
    except Exception:
        logger.exception("Error shutting down metrics provider.")
    finally:
        _provider = None


@contextmanager
def track_duration(histogram, attributes: Optional[dict] = None):
    """Context manager to record the duration of a block.

    Usage:
        with track_duration(pipeline_duration, {"stage": "ingest"}):
            do_work()
    """
    start = time.time()
    try:
        yield
    finally:
        duration = time.time() - start
        histogram.record(duration, attributes=attributes or {})