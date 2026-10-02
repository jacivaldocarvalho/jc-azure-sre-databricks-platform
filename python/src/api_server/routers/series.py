"""Endpoints for querying economic series."""

from fastapi import APIRouter, HTTPException, Query

from src.api_server.models.schemas import (
    HistoryPoint,
    HistoryResponse,
    LatestValueResponse,
    SeriesInfo,
    SeriesListResponse,
)
from src.api_server.services.delta_reader import (
    get_all_series_names,
    get_history_for_series,
    get_latest_for_series,
)

router = APIRouter(prefix="/series", tags=["series"])


# Static metadata about the series. In a larger system this would
# come from a catalog or a configuration file.
SERIES_METADATA = {
    "selic": SeriesInfo(
        name="selic",
        description="Taxa Selic diária",
        frequency="daily",
        unit="% per day",
    ),
    "cdi": SeriesInfo(
        name="cdi",
        description="Taxa CDI diária",
        frequency="daily",
        unit="% per day",
    ),
    "ipca": SeriesInfo(
        name="ipca",
        description="Índice IPCA mensal",
        frequency="monthly",
        unit="% per month",
    ),
}


@router.get("", response_model=SeriesListResponse)
def list_series() -> SeriesListResponse:
    """List all available series."""
    names = get_all_series_names()
    series = [SERIES_METADATA[name] for name in names if name in SERIES_METADATA]
    return SeriesListResponse(series=series)


@router.get("/{name}/latest", response_model=LatestValueResponse)
def latest_value(name: str) -> LatestValueResponse:
    """Return the latest available month for a series."""
    if name not in SERIES_METADATA:
        raise HTTPException(status_code=404, detail=f"Unknown series: {name}")

    row = get_latest_for_series(name)
    if row is None:
        raise HTTPException(
            status_code=404, detail=f"No data available for series: {name}"
        )

    return LatestValueResponse(
        series=row["series"],
        year_month=row["year_month"],
        mean_value=row["mean_value"],
        min_value=row["min_value"],
        max_value=row["max_value"],
        observation_count=row["observation_count"],
    )


@router.get("/{name}/history", response_model=HistoryResponse)
def history(
    name: str,
    limit: int = Query(24, ge=1, le=120, description="Number of months to return"),
) -> HistoryResponse:
    """Return the historical monthly aggregates for a series."""
    if name not in SERIES_METADATA:
        raise HTTPException(status_code=404, detail=f"Unknown series: {name}")

    rows = get_history_for_series(name, limit=limit)

    points = [
        HistoryPoint(
            year_month=row["year_month"],
            mean_value=row["mean_value"],
            min_value=row["min_value"],
            max_value=row["max_value"],
            stddev_value=row.get("stddev_value"),
            observation_count=row["observation_count"],
        )
        for row in rows
    ]

    return HistoryResponse(series=name, points=points, total_points=len(points))
