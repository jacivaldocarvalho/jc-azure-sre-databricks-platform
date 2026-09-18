"""Client for the Brazilian Central Bank SGS API.

The SGS (Sistema Gerenciador de Séries Temporais) is the official source
for Brazilian economic time series. This client fetches daily and monthly
series and normalizes them into a consistent format.

API documentation:
    https://dadosabertos.bcb.gov.br/dataset?res_format=JSON

Limitations:
    Requests spanning more than 10 years are automatically split into
    chunks to comply with the API's 10-year window limit (as of March 2025).
"""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterator
from urllib.parse import urlencode

import requests

from src.utils.logging import get_logger

logger = get_logger(__name__)

SGS_BASE_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs"


@dataclass(frozen=True)
class SeriesConfig:
    """Configuration for a single SGS series."""

    code: int
    name: str
    frequency: str  # "daily" or "monthly"
    unit: str


# Curated series used by the pipeline
SERIES = {
    "selic": SeriesConfig(code=11, name="Selic", frequency="daily", unit="% per day"),
    "cdi": SeriesConfig(code=12, name="CDI", frequency="daily", unit="% per day"),
    "ipca": SeriesConfig(code=433, name="IPCA", frequency="monthly", unit="% per month"),
}


def _date_chunks(
    start: date, end: date, max_years: int = 10
) -> Iterator[tuple[date, date]]:
    """Split a date range into chunks of at most max_years.

    The SGS API rejects requests spanning more than 10 years.
    """
    current = start
    while current < end:
        chunk_end = min(
            date(current.year + max_years, current.month, current.day) - timedelta(days=1),
            end,
        )
        yield current, chunk_end
        current = chunk_end + timedelta(days=1)


def _format_date(d: date) -> str:
    """Format a date as dd/MM/yyyy, as required by the SGS API."""
    return d.strftime("%d/%m/%Y")


def fetch_series(
    series_key: str,
    start: date,
    end: date,
    timeout: int = 30,
) -> list[dict]:
    """Fetch a series from the SGS API.

    Args:
        series_key: Key in the SERIES dict (e.g., "selic", "cdi").
        start: Start date (inclusive).
        end: End date (inclusive).
        timeout: HTTP request timeout in seconds.

    Returns:
        List of dicts with keys: data (date string), valor (value string).

    Raises:
        ValueError: If series_key is unknown.
        requests.HTTPError: If the API returns an error.
    """
    if series_key not in SERIES:
        raise ValueError(
            f"Unknown series '{series_key}'. Available: {list(SERIES.keys())}"
        )

    config = SERIES[series_key]
    all_data: list[dict] = []

    for chunk_start, chunk_end in _date_chunks(start, end):
        params = {
            "formato": "json",
            "dataInicial": _format_date(chunk_start),
            "dataFinal": _format_date(chunk_end),
        }
        url = f"{SGS_BASE_URL}.{config.code}/dados?{urlencode(params)}"

        logger.info(
            "Fetching series '%s' (code=%d) from %s to %s",
            series_key,
            config.code,
            chunk_start.isoformat(),
            chunk_end.isoformat(),
        )

        response = requests.get(url, timeout=timeout)
        response.raise_for_status()

        data = response.json()
        all_data.extend(data)

    logger.info("Fetched %d observations for series '%s'", len(all_data), series_key)
    return all_data
