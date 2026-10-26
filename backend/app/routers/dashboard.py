"""Dashboard API: wind forecast vs actuals for day-ahead procurement."""

import asyncio
from datetime import date, datetime, timedelta, timezone
from typing import Literal

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.config import settings
from app.schemas import DashboardResponse, HealthResponse
from app.services import build_dashboard, fetch_actuals, fetch_forecasts

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/dashboard", response_model=DashboardResponse)
async def dashboard(
    start_date: date = Query(
        default=date(2026, 1, 1),
        description="Delivery start date (inclusive, UTC settlement date).",
    ),
    end_date: date = Query(
        default=date(2026, 2, 1),
        description="Delivery end date (exclusive).",
    ),
    mode: Literal["day_ahead", "fixed_cutoff"] = Query(
        default="day_ahead",
        description="day_ahead = per-period cutoff on D-1 at gate time; fixed_cutoff = one global cutoff.",
    ),
    decision_cutoff: datetime | None = Query(
        default=None,
        description="Required when mode=fixed_cutoff. ISO-8601 timestamp.",
    ),
    gate_hour_utc: int = Query(
        default=None,
        ge=0,
        le=23,
        description="Day-ahead gate hour (UTC). Defaults to settings.",
    ),
    gate_minute_utc: int = Query(
        default=None,
        ge=0,
        le=59,
        description="Day-ahead gate minute (UTC). Defaults to settings.",
    ),
) -> DashboardResponse:
    if end_date <= start_date:
        raise HTTPException(status_code=400, detail="end_date must be after start_date")
    if (end_date - start_date).days > 62:
        raise HTTPException(status_code=400, detail="Date range cannot exceed 62 days")

    gate_hour = gate_hour_utc if gate_hour_utc is not None else settings.default_gate_hour_utc
    gate_minute = (
        gate_minute_utc if gate_minute_utc is not None else settings.default_gate_minute_utc
    )

    fixed: datetime | None = None
    if mode == "fixed_cutoff":
        if decision_cutoff is None:
            raise HTTPException(
                status_code=400,
                detail="decision_cutoff is required when mode=fixed_cutoff",
            )
        fixed = decision_cutoff
        if fixed.tzinfo is None:
            fixed = fixed.replace(tzinfo=timezone.utc)
        else:
            fixed = fixed.astimezone(timezone.utc)

    # Pull forecast vintages from 2 days before the first delivery through end_date.
    # This covers D-1 day-ahead publishes for every period in the requested window.
    publish_from = datetime.combine(
        start_date - timedelta(days=2),
        datetime.min.time(),
        tzinfo=timezone.utc,
    )
    publish_to = datetime.combine(end_date, datetime.min.time(), tzinfo=timezone.utc)

    try:
        actual_rows, forecast_rows = await asyncio.gather(
            fetch_actuals(start_date, end_date),
            fetch_forecasts(publish_from, publish_to),
        )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Elexon request failed: {exc}",
        ) from exc

    try:
        return build_dashboard(
            actual_rows=actual_rows,
            forecast_rows=forecast_rows,
            start=start_date,
            end_exclusive=end_date,
            mode=mode,
            fixed_cutoff=fixed,
            gate_hour=gate_hour,
            gate_minute=gate_minute,
        )
    except (ValueError, TypeError, KeyError) as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Could not process Elexon response: {exc}",
        ) from exc
