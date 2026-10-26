import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";
import { fetchDashboard } from "./api";
import { ForecastChart } from "./components/ForecastChart";
import { MetricCard } from "./components/MetricCard";
import type { DashboardResponse, DecisionMode } from "./types";

function formatMw(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `${Math.round(value).toLocaleString()} MW`;
}

function formatPct(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `${value.toFixed(1)}%`;
}

export default function App() {
  const [startDate, setStartDate] = useState("2026-01-01");
  const [endDate, setEndDate] = useState("2026-02-01");
  const [mode, setMode] = useState<DecisionMode>("day_ahead");
  const [gateHourUtc, setGateHourUtc] = useState(11);
  const [decisionCutoff, setDecisionCutoff] = useState("2026-01-01T11:00:00Z");
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchDashboard({
        startDate,
        endDate,
        mode,
        gateHourUtc,
        decisionCutoff,
      });
      setData(result);
    } catch (err) {
      setData(null);
      setError(err instanceof Error ? err.message : "Failed to load dashboard");
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate, mode, gateHourUtc, decisionCutoff]);

  // Initial load for the January 2026 pilot window.
  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    void load();
  }

  const summary = data?.summary;

  return (
    <div className="app">
      <header className="hero">
        <h1 className="brand">
          Wind<span>Desk</span>
        </h1>
        <p className="tagline">
          Day-ahead view of UK national wind generation: the forecast available when you buy,
          measured against what actually ran — so procurement can price forecast error, not guess it.
        </p>
      </header>

      <form className="panel controls" onSubmit={onSubmit}>
        <div className="field">
          <label htmlFor="start">Delivery from</label>
          <input
            id="start"
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
        </div>
        <div className="field">
          <label htmlFor="end">Delivery to (exclusive)</label>
          <input
            id="end"
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />
        </div>
        <div className="field">
          <label htmlFor="mode">Decision mode</label>
          <select
            id="mode"
            value={mode}
            onChange={(e) => setMode(e.target.value as DecisionMode)}
          >
            <option value="day_ahead">Day-ahead (D−1 gate)</option>
            <option value="fixed_cutoff">Fixed cutoff</option>
          </select>
        </div>
        {mode === "day_ahead" ? (
          <div className="field">
            <label htmlFor="gate">Gate hour (UTC)</label>
            <input
              id="gate"
              type="number"
              min={0}
              max={23}
              value={gateHourUtc}
              onChange={(e) => setGateHourUtc(Number(e.target.value))}
            />
          </div>
        ) : (
          <div className="field">
            <label htmlFor="cutoff">Decision cutoff (UTC)</label>
            <input
              id="cutoff"
              type="datetime-local"
              value={decisionCutoff.slice(0, 16)}
              onChange={(e) => setDecisionCutoff(`${e.target.value}:00Z`)}
            />
          </div>
        )}
        <div className="actions">
          <button className="btn btn-primary" type="submit" disabled={loading}>
            {loading ? "Loading…" : "Refresh analysis"}
          </button>
          <button
            className="btn btn-ghost"
            type="button"
            onClick={() => {
              setStartDate("2026-01-01");
              setEndDate("2026-02-01");
              setMode("day_ahead");
              setGateHourUtc(11);
            }}
          >
            Reset Jan 2026
          </button>
        </div>
      </form>

      {error ? <p className="status error">{error}</p> : null}
      {loading && !data ? <p className="status">Fetching Elexon actuals and forecasts…</p> : null}

      {summary ? (
        <>
          <section className="metrics" aria-label="Accuracy metrics">
            <MetricCard
              label="MAE"
              value={formatMw(summary.mae_mw)}
              hint="Mean absolute error"
            />
            <MetricCard
              label="RMSE"
              value={formatMw(summary.rmse_mw)}
              hint="Penalises large misses"
            />
            <MetricCard
              label="Bias"
              value={formatMw(summary.bias_mw)}
              hint="Forecast − actual (avg)"
            />
            <MetricCard
              label="WAPE"
              value={formatPct(summary.wape_percent)}
              hint="Error vs total wind"
            />
            <MetricCard
              label="Matched periods"
              value={String(summary.matched_periods)}
              hint={`${summary.actual_periods} actual / ${summary.forecast_periods_available} forecast`}
            />
          </section>

          <section className="panel">
            <ForecastChart points={data?.points ?? []} />
            {data?.notes?.length ? (
              <div className="notes">
                <strong>How to read this</strong>
                <ul>
                  {data.notes.map((note) => (
                    <li key={note}>{note}</li>
                  ))}
                </ul>
              </div>
            ) : null}
          </section>
        </>
      ) : null}
    </div>
  );
}
