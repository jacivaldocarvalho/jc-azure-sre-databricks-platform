"""Prometheus metrics middleware for the FastAPI application.

Records request count, latency, and in-progress requests with labels
for method, path, and status code.

Path normalization: dynamic path segments (e.g., /series/selic) are
replaced with a placeholder (/series/{name}) to avoid cardinality
explosion in Prometheus.
"""

import re
import time
from typing import Callable

from fastapi import Request, Response
from prometheus_client import Counter, Gauge, Histogram
from starlette.middleware.base import BaseHTTPMiddleware

# Metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being processed",
    ["method", "path"],
)

# Path normalization patterns
_DYNAMIC_PATH_PATTERNS = [
    # /series/{name}/latest, /series/{name}/history
    (re.compile(r"^/series/[^/]+/"), "/series/{name}/"),
    # /series/{name}
    (re.compile(r"^/series/[^/]+$"), "/series/{name}"),
]


def normalize_path(path: str) -> str:
    """Replace dynamic path segments with placeholders."""
    for pattern, replacement in _DYNAMIC_PATH_PATTERNS:
        if pattern.match(path):
            return replacement
    return path


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware that records metrics for every HTTP request."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        method = request.method
        raw_path = request.url.path

        # Do not track the /metrics endpoint itself (avoids self-instrumentation)
        if raw_path == "/metrics":
            return await call_next(request)

        path = normalize_path(raw_path)

        http_requests_in_progress.labels(method=method, path=path).inc()
        start = time.time()

        try:
            response = await call_next(request)
            status = str(response.status_code)
            return response
        except Exception:
            status = "500"
            raise
        finally:
            duration = time.time() - start
            http_request_duration_seconds.labels(
                method=method, path=path
            ).observe(duration)
            http_requests_total.labels(
                method=method, path=path, status=status
            ).inc()
            http_requests_in_progress.labels(method=method, path=path).dec()
