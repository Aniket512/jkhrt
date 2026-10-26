"""
Align wind forecasts with actuals and compute accuracy metrics.

Decision logic (day-ahead mode):
  For a delivery period on calendar day D, traders buy in the day-ahead market
  on D-1. We keep the latest forecast published at or before the gate time on D-1.
"""

from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Literal

from app.schemas import DashboardResponse, RangeInfo, SeriesPoint, SummaryMetrics


def _parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _period_cutoff(
    period: datetime,
    mode: Literal["day_ahead", "fixed_cutoff"],
    fixed_cutoff: datetime | None,
    gate_hour: int,
    gate_minute: int,
) -> datetime:
    """Return the latest publishTime that may be used for this delivery period."""
    if mode == "fixed_cutoff":
        assert fixed_cutoff is not None
        return fixed_cutoff

    # Day-ahead: previous UTC calendar day at the configured gate time.
    day = period.astimezone(timezone.utc).date() - timedelta(days=1)
    return datetime.combine(day, time(gate_hour, gate_minute), tzinfo=timezone.utc)


def build_dashboard(
    actual_rows: list[dict[str, Any]],
    forecast_rows: list[dict[str, Any]],
    start: date,
    end_exclusive: date,
    mode: Literal["day_ahead", "fixed_cutoff"],
    fixed_cutoff: datetime | None,
    gate_hour: int,
    gate_minute: int,
) -> DashboardResponse:
    start_dt = datetime.combine(start, time.min, tzinfo=timezone.utc)
    end_dt = datetime.combine(end_exclusive, time.min, tzinfo=timezone.utc)

    # Map delivery period -> actual MW (WIND only).
    actual_by_period: dict[datetime, float] = {}
    for row in actual_rows:
        fuel = str(row.get("fuelType", "WIND")).upper()
        if fuel not in {"WIND", "WIND ONSHORE", "WIND OFFSHORE"}:
            continue
        period = _parse_dt(row.get("startTime"))
        value = _number(row.get("generation", row.get("quantity")))
        if period is None or value is None or not (start_dt <= period < end_dt):
            continue
        actual_by_period[period] = value

    # Group forecasts by delivery period: list of (publishTime, MW).
    # WINDFOR is typically hourly; FUELHH is half-hourly. We map each hourly
    # forecast onto both :00 and :30 settlement periods in that hour so the
    # day-ahead desk can compare against every outturn point.
    forecasts_by_period: dict[datetime, list[tuple[datetime, float]]] = {}
    for row in forecast_rows:
        period = _parse_dt(row.get("startTime"))
        published = _parse_dt(row.get("publishTime"))
        value = _number(row.get("generation"))
        if period is None or published is None or value is None:
            continue
        if not (start_dt <= period < end_dt):
            continue
        forecasts_by_period.setdefault(period, []).append((published, value))
        if period.minute == 0:
            half = period + timedelta(minutes=30)
            if start_dt <= half < end_dt:
                forecasts_by_period.setdefault(half, []).append((published, value))

    points: list[SeriesPoint] = []
    errors: list[tuple[float, float]] = []

    for period in sorted(set(actual_by_period) | set(forecasts_by_period)):
        cutoff = _period_cutoff(period, mode, fixed_cutoff, gate_hour, gate_minute)
        available = [
            (published, value)
            for published, value in forecasts_by_period.get(period, [])
            if published <= cutoff
        ]
        chosen = max(available, key=lambda item: item[0]) if available else None
        actual = actual_by_period.get(period)
        forecast = chosen[1] if chosen else None
        error = (forecast - actual) if forecast is not None and actual is not None else None
        # shortfall: how many MW less wind we got vs the forecast we bought against
        shortfall = (forecast - actual) if error is not None and error > 0 else (
            0.0 if error is not None else None
        )

        if error is not None and actual is not None:
            errors.append((error, actual))

        points.append(
            SeriesPoint(
                start_time=period,
                actual_mw=actual,
                forecast_mw=forecast,
                forecast_publish_time=chosen[0] if chosen else None,
                decision_cutoff=cutoff,
                error_mw=error,
                shortfall_mw=shortfall,
            )
        )

    if errors:
        absolute_errors = [abs(error) for error, _ in errors]
        mae = sum(absolute_errors) / len(absolute_errors)
        rmse = (sum(error * error for error, _ in errors) / len(errors)) ** 0.5
        bias = sum(error for error, _ in errors) / len(errors)
        denominator = sum(abs(actual) for _, actual in errors)
        wape = (sum(absolute_errors) / denominator * 100) if denominator else None
        mean_actual = sum(actual for _, actual in errors) / len(errors)
        mean_forecast = sum(actual + error for error, actual in errors) / len(errors)
    else:
        mae = rmse = bias = wape = mean_actual = mean_forecast = None

    def _round(value: float | None) -> float | None:
        return round(value, 3) if value is not None else None

    gate_label = f"{gate_hour:02d}:{gate_minute:02d}Z" if mode == "day_ahead" else None

    return DashboardResponse(
        range=RangeInfo(
            start=start_dt,
            end_exclusive=end_dt,
            mode=mode,
            gate_time_utc=gate_label,
            decision_cutoff=fixed_cutoff if mode == "fixed_cutoff" else None,
        ),
        summary=SummaryMetrics(
            actual_periods=len(actual_by_period),
            forecast_periods_available=sum(1 for p in points if p.forecast_mw is not None),
            matched_periods=len(errors),
            mae_mw=_round(mae),
            rmse_mw=_round(rmse),
            bias_mw=_round(bias),
            wape_percent=_round(wape),
            mean_actual_mw=_round(mean_actual),
            mean_forecast_mw=_round(mean_forecast),
        ),
        points=points,
        notes=[
            "Day-ahead mode uses the latest forecast published at or before the gate time on the previous UTC day.",
            "A positive bias means the forecast was higher than actual wind generation (risk of under-procurement if relying on wind).",
            "Missing values stay null and are excluded from accuracy metrics.",
            "National WIND totals only — Elexon FUELHH + WINDFOR.",
            "WINDFOR is hourly; each hourly forecast is applied to both half-hour settlement periods in that hour.",
        ],
    )
