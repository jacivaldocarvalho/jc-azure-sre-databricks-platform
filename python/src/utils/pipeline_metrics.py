"""Definition of the metrics exposed by the pipeline.

Provides a PipelineMetrics dataclass that holds all instruments.
The instruments are created lazily via the initialize() function,
which requires the OpenTelemetry meter provider to be configured
first (see src.utils.metrics.setup_metrics).
"""

from dataclasses import dataclass
from typing import Optional

from opentelemetry.metrics import Counter, Histogram, UpDownCounter

from src.utils.logging import get_logger
from src.utils.metrics import get_meter

logger = get_logger(__name__)


@dataclass
class PipelineMetrics:
    """Container for all metric instruments used by the pipeline."""

    runs_total: Counter
    rows_processed_total: Counter
    rows_rejected_total: Counter
    api_requests_total: Counter
    duration_seconds: Histogram
    api_request_duration_seconds: Histogram
    last_success_timestamp: UpDownCounter


_instance: Optional[PipelineMetrics] = None


def initialize() -> PipelineMetrics:
    """Create (or return) the pipeline metrics instruments.

    Must be called after metrics.setup_metrics() to ensure the meter
    provider is configured.
    """
    global _instance

    if _instance is not None:
        return _instance

    meter = get_meter()

    _instance = PipelineMetrics(
        runs_total=meter.create_counter(
            name="pipeline_runs_total",
            description="Total number of pipeline runs",
            unit="1",
        ),
        rows_processed_total=meter.create_counter(
            name="pipeline_rows_processed_total",
            description="Total number of rows processed",
            unit="1",
        ),
        rows_rejected_total=meter.create_counter(
            name="pipeline_rows_rejected_total",
            description="Total number of rows rejected during validation",
            unit="1",
        ),
        api_requests_total=meter.create_counter(
            name="pipeline_api_requests_total",
            description="Total number of API requests made to the BCB SGS API",
            unit="1",
        ),
        duration_seconds=meter.create_histogram(
            name="pipeline_duration_seconds",
            description="Duration of pipeline stages in seconds",
            unit="s",
        ),
        api_request_duration_seconds=meter.create_histogram(
            name="pipeline_api_request_duration_seconds",
            description="Duration of BCB API requests in seconds",
            unit="s",
        ),
        last_success_timestamp=meter.create_up_down_counter(
            name="pipeline_last_success_timestamp",
            description="Unix timestamp of the last successful pipeline run",
            unit="s",
        ),
    )

    logger.info("Pipeline metrics instruments created.")
    return _instance