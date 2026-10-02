"""FastAPI application entry point.

Run with:
    uvicorn src.api_server.main:app --host 0.0.0.0 --port 8080
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api_server.config import APP_NAME, APP_VERSION
from src.api_server.routers import health, series, summary
from src.api_server.services.spark_manager import get_session, stop_session
from src.api_server.metrics import PrometheusMiddleware
from src.utils.logging import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown of shared resources.

    Creates the SparkSession on startup so the first request does not
    pay the initialization cost.
    """
    logger.info("Starting API server...")
    try:
        get_session()
        logger.info("SparkSession ready.")
    except Exception:
        logger.exception("Failed to initialize SparkSession at startup.")
        # Continue: the readiness probe will report the failure

    yield

    logger.info("Shutting down API server...")
    stop_session()


app = FastAPI(
    title="JC SRE Databricks API",
    description=(
        "REST API exposing aggregated Brazilian economic indicators "
        "and executive summaries from the data pipeline."
    ),
    version=APP_VERSION,
    lifespan=lifespan,
)


app.add_middleware(PrometheusMiddleware)

app.include_router(health.router)
app.include_router(series.router)
app.include_router(summary.router)


@app.get("/", include_in_schema=False)
def root() -> dict:
    """Root endpoint. Returns basic service information."""
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "docs": "/docs",
    }
