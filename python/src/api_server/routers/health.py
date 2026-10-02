"""Health, readiness, and metrics endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from src.api_server.config import APP_VERSION
from src.api_server.models.schemas import HealthResponse, ReadyResponse
from src.api_server.services.delta_reader import is_delta_accessible

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Liveness probe. Returns 200 as long as the process is running."""
    return HealthResponse(
        status="healthy",
        version=APP_VERSION,
        timestamp=datetime.now(timezone.utc),
    )


@router.get("/ready", response_model=ReadyResponse)
def ready() -> ReadyResponse:
    """Readiness probe. Returns 200 when the Delta Lake is accessible."""
    delta_ok = is_delta_accessible()
    return ReadyResponse(
        status="ready" if delta_ok else "not_ready",
        delta_accessible=delta_ok,
    )


@router.get("/metrics", response_class=PlainTextResponse)
def metrics() -> PlainTextResponse:
    """Prometheus metrics endpoint."""
    return PlainTextResponse(
        content=generate_latest().decode("utf-8"),
        media_type=CONTENT_TYPE_LATEST,
    )
