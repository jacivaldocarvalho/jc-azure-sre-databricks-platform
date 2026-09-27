"""Centralized Azure credential resolution.

Provides a single function to obtain an Azure credential, following
the same logic as metrics.py: Azure CLI in local development,
DefaultAzureCredential in Azure.
"""

import os

from src.utils.logging import get_logger

logger = get_logger(__name__)


def get_azure_credential():
    """Return the appropriate Azure credential for the current environment.

    Uses AzureCliCredential when AZURE_USE_CLI=true (local development),
    otherwise uses DefaultAzureCredential (Azure deployment).
    """
    if os.getenv("AZURE_USE_CLI", "false").lower() == "true":
        from azure.identity import AzureCliCredential

        logger.debug("Using AzureCliCredential (AZURE_USE_CLI=true).")
        return AzureCliCredential()

    from azure.identity import DefaultAzureCredential

    logger.debug("Using DefaultAzureCredential.")
    return DefaultAzureCredential()
