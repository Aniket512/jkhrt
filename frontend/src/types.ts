/** Shapes returned by GET /api/dashboard */

export type DecisionMode = "day_ahead" | "fixed_cutoff";

export interface SummaryMetrics {
  actual_periods: number;
  forecast_periods_available: number;
  matched_periods: number;
  mae_mw: number | null;
  rmse_mw: number | null;
  bias_mw: number | null;
  wape_percent: number | null;
  mean_actual_mw: number | null;
  mean_forecast_mw: number | null;
}

export interface SeriesPoint {
  start_time: string;
  actual_mw: number | null;
  forecast_mw: number | null;
  forecast_publish_time: string | null;
  decision_cutoff: string | null;
  error_mw: number | null;
  shortfall_mw: number | null;
}

export interface DashboardResponse {
  range: {
    start: string;
    end_exclusive: string;
    mode: DecisionMode;
    gate_time_utc: string | null;
    decision_cutoff: string | null;
  };
  summary: SummaryMetrics;
  points: SeriesPoint[];
  notes: string[];
}
