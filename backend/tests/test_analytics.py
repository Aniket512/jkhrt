"""Unit tests for day-ahead forecast selection and metrics."""

from datetime import datetime, timezone

from app.services.analytics import build_dashboard


def test_day_ahead_picks_latest_forecast_before_gate():
    actual_rows = [
        {
            "fuelType": "WIND",
            "startTime": "2026-01-02T00:00:00Z",
            "generation": 1000,
        }
    ]
    forecast_rows = [
        # Too late: published after D-1 11:00Z gate
        {
            "startTime": "2026-01-02T00:00:00Z",
            "publishTime": "2026-01-01T12:00:00Z",
            "generation": 1500,
        },
        # Eligible and newer of the early vintages
        {
            "startTime": "2026-01-02T00:00:00Z",
            "publishTime": "2026-01-01T10:00:00Z",
            "generation": 1100,
        },
        {
            "startTime": "2026-01-02T00:00:00Z",
            "publishTime": "2026-01-01T08:00:00Z",
            "generation": 900,
        },
    ]

    result = build_dashboard(
        actual_rows=actual_rows,
        forecast_rows=forecast_rows,
        start=datetime(2026, 1, 2, tzinfo=timezone.utc).date(),
        end_exclusive=datetime(2026, 1, 3, tzinfo=timezone.utc).date(),
        mode="day_ahead",
        fixed_cutoff=None,
        gate_hour=11,
        gate_minute=0,
    )

    assert result.summary.matched_periods == 1
    assert result.points[0].forecast_mw == 1100
    assert result.points[0].error_mw == 100
    assert result.summary.mae_mw == 100


def test_hourly_forecast_fills_half_hour_period():
    """Hourly WINDFOR at :00 should also cover the :30 settlement period."""
    actual_rows = [
        {
            "fuelType": "WIND",
            "startTime": "2026-01-02T00:30:00Z",
            "generation": 1000,
        }
    ]
    forecast_rows = [
        {
            "startTime": "2026-01-02T00:00:00Z",
            "publishTime": "2026-01-01T10:00:00Z",
            "generation": 1200,
        }
    ]

    result = build_dashboard(
        actual_rows=actual_rows,
        forecast_rows=forecast_rows,
        start=datetime(2026, 1, 2, tzinfo=timezone.utc).date(),
        end_exclusive=datetime(2026, 1, 3, tzinfo=timezone.utc).date(),
        mode="day_ahead",
        fixed_cutoff=None,
        gate_hour=11,
        gate_minute=0,
    )

    assert result.summary.matched_periods == 1
    assert result.points[0].forecast_mw == 1200
