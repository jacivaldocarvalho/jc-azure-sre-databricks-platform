# syntax=docker/dockerfile:1
#
# Multi-stage Dockerfile for the API server.
#
# Stage 1 (builder): installs Python dependencies into a virtual environment.
# Stage 2 (runtime): copies only the venv and the source code.

# =============================================================================
# Stage 1: builder
# =============================================================================
FROM python:3.12-slim AS builder

# Install system dependencies required to build Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r /tmp/requirements.txt

# =============================================================================
# Stage 2: runtime
# =============================================================================
FROM python:3.12-slim AS runtime

# Install Java (required by PySpark) and curl (for health checks).
# The base image is python:3.12-slim, which currently ships Debian 13 (Trixie).
# Debian 13 replaced openjdk-17 with openjdk-21. PySpark 3.5.x supports
# Java 8, 11, 17, and 21, so openjdk-21 is fully compatible.
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-21-jre-headless \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV JAVA_HOME="/usr/lib/jvm/java-21-openjdk-amd64"

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash app
USER app
WORKDIR /home/app

# Copy the application source
COPY --chown=app:app src/ /home/app/src/

# The Delta warehouse is mounted as a volume at runtime
ENV DELTA_WAREHOUSE_PATH=/data/spark-warehouse

# Expose the API port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the API server
CMD ["uvicorn", "src.api_server.main:app", "--host", "0.0.0.0", "--port", "8080"]
