"""Metrics collection and export for the pipeline.

Provides a Prometheus-compatible API surface backed by OpenTelemetry.
Metrics are exported to Azure Monitor (Application Insights) via OTLP.

The Application Insights connection string is resolved in this order:
    1. The APPLICATIONINSIGHTS_CONNECTION_STRING environment variable
    2. The Azure Key Vault secret named "applicationinsights-connection-string"

The Key Vault access uses a credential that depends on the environment:
    - Local development: AzureCliCredential (uses the `az login` session)
    - Azure: DefaultAzureCredential (supports Managed Identity)

The credential is selected via the AZURE_USE_CLI environment variable:
    - AZURE_USE_CLI=true  → forces AzureCliCredential (local development)
    - unset or false      → uses DefaultAzureCredential (Azure deployment)

If neither source provides a connection string, metrics are recorded
but not exported. This allows running the pipeline in environments
without observability configured.
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


def _get_credential():
    """Return the appropriate Azure credential for the current environment.

    Local development uses AzureCliCredential explicitly to avoid
    interference from environment variables that DefaultAzureCredential
    would pick up first (e.g., AZURE_CLIENT_ID from another project).

    Azure deployments use DefaultAzureCredential, which supports
    Managed Identity transparently.

    The behavior is controlled by the AZURE_USE_CLI environment variable.
    """
    if os.getenv("AZURE_USE_CLI", "false").lower() == "true":
        from azure.identity import AzureCliCredential

        logger.debug("Using AzureCliCredential (AZURE_USE_CLI=true).")
        return AzureCliCredential()

    from azure.identity import DefaultAzureCredential

    logger.debug("Using DefaultAzureCredential.")
    return DefaultAzureCredential()


def _get_connection_string_from_env() -> Optional[str]:
    """Try to read the connection string from environment variables."""
    return os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")


def _get_connection_string_from_keyvault() -> Optional[str]:
    """Try to read the connection string from Azure Key Vault.

    Returns None if Key Vault is not configured or the secret is missing.
    """
    keyvault_uri = os.getenv("AZURE_KEY_VAULT_URI")
    if not keyvault_uri:
        logger.debug("AZURE_KEY_VAULT_URI not set, skipping Key Vault lookup.")
        return None

    try:
        from azure.keyvault.secrets import SecretClient

        credential = _get_credential()
        client = SecretClient(vault_url=keyvault_uri, credential=credential)

        secret = client.get_secret("applicationinsights-connection-string")
        logger.info("Loaded connection string from Key Vault.")
        return secret.value

    except Exception:
        logger.exception(
            "Failed to retrieve secret from Key Vault at %s.", keyvault_uri
        )
        return None


def _resolve_connection_string() -> Optional[str]:
    """Resolve the Application Insights connection string from all sources."""
    conn_str = _get_connection_string_from_env()
    if conn_str:
        logger.info("Using connection string from environment variable.")
        return conn_str

    conn_str = _get_connection_string_from_keyvault()
    if conn_str:
        return conn_str

    logger.warning(
        "APPLICATIONINSIGHTS_CONNECTION_STRING not set and Key Vault "
        "is not configured. Metrics will be recorded but not exported."
    )
    return None


def _create_exporter():
    """Create the Azure Monitor exporter if a connection string is available.

    Returns None if no connection string is resolvable, in which case
    metrics are collected but not exported.
    """
    connection_string = _resolve_connection_string()
    if not connection_string:
        return None

    try:
        from azure.monitor.opentelemetry.exporter import AzureMonitorMetricExporter

        exporter = AzureMonitorMetricExporter(connection_string=connection_string)
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