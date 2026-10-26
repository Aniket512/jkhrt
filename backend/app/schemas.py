"""Pydantic response models for the public API."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class RangeInfo(BaseModel):
    start: datetime
    end_exclusive: datetime
    mode: Literal["day_ahead", "fixed_cutoff"]
    gate_time_utc: str | None = None
    decision_cutoff: datetime | None = None


class SummaryMetrics(BaseModel):
    actual_periods: int
    forecast_periods_available: int
    matched_periods: int
    mae_mw: float | None = None
    rmse_mw: float | None = None
    bias_mw: float | None = None
    wape_percent: float | None = None
    mean_actual_mw: float | None = None
    mean_forecast_mw: float | None = None


class SeriesPoint(BaseModel):
    start_time: datetime
    actual_mw: float | None = None
    forecast_mw: float | None = None
    forecast_publish_time: datetime | None = None
    decision_cutoff: datetime | None = None
    error_mw: float | None = None
    # Positive error = shortfall risk if relying on wind (actual < forecast).
    shortfall_mw: float | None = None


class DashboardResponse(BaseModel):
    range: RangeInfo
    summary: SummaryMetrics
    points: list[SeriesPoint]
    notes: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
