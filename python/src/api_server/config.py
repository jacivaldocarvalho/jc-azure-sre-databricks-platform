"""Configuration for the API server.

Reads environment variables with sensible defaults for local development.
"""

import os

# Base path for the Delta warehouse. In local development, it is
# relative to the project root. In Kubernetes, it can be mounted as a
# volume or point to an ABFSS path.
DELTA_WAREHOUSE_PATH = os.getenv(
    "DELTA_WAREHOUSE_PATH",
    "./spark-warehouse",
)

# API server configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8080"))
API_LOG_LEVEL = os.getenv("API_LOG_LEVEL", "info")

# Application metadata
APP_NAME = "jc-sre-databricks-api"
APP_VERSION = "0.1.0"

# Paths to Delta tables
RAW_TABLE = f"{DELTA_WAREHOUSE_PATH}/raw"
PROCESSED_MONTHLY_AGGREGATES = (
    f"{DELTA_WAREHOUSE_PATH}/processed/monthly_aggregates"
)
PROCESSED_VARIATIONS = f"{DELTA_WAREHOUSE_PATH}/processed/variations"
PROCESSED_SUMMARIES = f"{DELTA_WAREHOUSE_PATH}/processed/summaries"
