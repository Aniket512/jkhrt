import type { DashboardResponse, DecisionMode } from "./types";

/** Base URL for the API. Empty string uses Vite proxy in local dev. */
const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "";

export interface DashboardQuery {
  startDate: string;
  endDate: string;
  mode: DecisionMode;
  gateHourUtc: number;
  decisionCutoff?: string;
}

export async function fetchDashboard(query: DashboardQuery): Promise<DashboardResponse> {
  const params = new URLSearchParams({
    start_date: query.startDate,
    end_date: query.endDate,
    mode: query.mode,
    gate_hour_utc: String(query.gateHourUtc),
  });

  if (query.mode === "fixed_cutoff" && query.decisionCutoff) {
    params.set("decision_cutoff", query.decisionCutoff);
  }

  const response = await fetch(`${API_BASE}/api/dashboard?${params.toString()}`);
  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      // keep default message
    }
    throw new Error(detail);
  }
  return response.json() as Promise<DashboardResponse>;
}
