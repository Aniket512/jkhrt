"""
Elexon BMRS client for national wind actuals and forecasts.

Docs:
- FUELHH stream: filter by settlementDateFrom / settlementDateTo (+ fuelType)
- WINDFOR stream: filter by publishDateTimeFrom / publishDateTimeTo
  (without publish filters the API returns only the latest vintage)
"""

from datetime import date, datetime, timedelta, timezone
from typing import Any

import httpx

from app.config import settings


def _iso(dt: datetime) -> str:
    """Format a datetime as UTC ISO-8601 with a Z suffix."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _as_rows(payload: Any, dataset: str) -> list[dict[str, Any]]:
    """Normalise stream/list or {data: [...]} envelopes into a list of dict rows."""
    if isinstance(payload, dict):
        payload = payload.get("data", [])
    if not isinstance(payload, list):
        raise ValueError(f"Unexpected {dataset} response shape: expected list or data array")
    return [row for row in payload if isinstance(row, dict)]


async def fetch_actuals(start: date, end_exclusive: date) -> list[dict[str, Any]]:
    """
    Fetch half-hourly WIND outturn for settlement dates in [start, end_exclusive).

    settlementDateTo is inclusive on the Elexon API, so we pass end_exclusive - 1 day.
    """
    if end_exclusive <= start:
        return []

    settlement_to = end_exclusive - timedelta(days=1)
    url = f"{settings.elexon_base_url}/datasets/FUELHH/stream"
    params = {
        "settlementDateFrom": start.isoformat(),
        "settlementDateTo": settlement_to.isoformat(),
        "fuelType": "WIND",
    }

    async with httpx.AsyncClient(timeout=settings.elexon_timeout_seconds) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return _as_rows(response.json(), "FUELHH")


async def fetch_forecasts(publish_from: datetime, publish_to: datetime) -> list[dict[str, Any]]:
    """
    Fetch WINDFOR rows whose publishTime lies in [publish_from, publish_to].

    Day-ahead analysis needs many vintages, so we always send publish filters.
    Large ranges are chunked to keep responses manageable.
    """
    if publish_to <= publish_from:
        return []

    url = f"{settings.elexon_base_url}/datasets/WINDFOR/stream"
    chunk = timedelta(days=7)
    rows: list[dict[str, Any]] = []

    async with httpx.AsyncClient(timeout=settings.elexon_timeout_seconds) as client:
        cursor = publish_from
        while cursor < publish_to:
            chunk_end = min(cursor + chunk, publish_to)
            params = {
                "publishDateTimeFrom": _iso(cursor),
                "publishDateTimeTo": _iso(chunk_end),
            }
            response = await client.get(url, params=params)
            response.raise_for_status()
            rows.extend(_as_rows(response.json(), "WINDFOR"))
            cursor = chunk_end

    return rows
