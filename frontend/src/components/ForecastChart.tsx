import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { SeriesPoint } from "../types";

interface ForecastChartProps {
  points: SeriesPoint[];
}

function formatTick(iso: string): string {
  const d = new Date(iso);
  return `${d.getUTCDate()}/${d.getUTCMonth() + 1} ${String(d.getUTCHours()).padStart(2, "0")}:00`;
}

/** Half-hourly actual vs day-ahead forecast wind generation (MW). */
export function ForecastChart({ points }: ForecastChartProps) {
  // Downsample slightly for readability when showing a full month (~1488 points).
  const step = points.length > 400 ? 2 : 1;
  const data = points
    .filter((_, index) => index % step === 0)
    .map((p) => ({
      t: p.start_time,
      actual: p.actual_mw,
      forecast: p.forecast_mw,
    }));

  return (
    <div className="chart-wrap">
      <h2 className="chart-title">National wind: forecast vs actual</h2>
      <div className="legend">
        <span>
          <i className="actual" /> Actual (FUELHH)
        </span>
        <span>
          <i className="forecast" /> Day-ahead forecast (WINDFOR)
        </span>
      </div>
      <ResponsiveContainer width="100%" height={340}>
        <LineChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
          <CartesianGrid stroke="rgba(180,210,220,0.12)" strokeDasharray="3 3" />
          <XAxis
            dataKey="t"
            tickFormatter={formatTick}
            minTickGap={48}
            stroke="#9bb0bc"
            tick={{ fill: "#9bb0bc", fontSize: 11 }}
          />
          <YAxis
            stroke="#9bb0bc"
            tick={{ fill: "#9bb0bc", fontSize: 11 }}
            width={56}
            tickFormatter={(v: number) => `${Math.round(v / 1000)}k`}
            label={{
              value: "MW",
              angle: -90,
              position: "insideLeft",
              fill: "#9bb0bc",
            }}
          />
          <Tooltip
            contentStyle={{
              background: "#0e2a40",
              border: "1px solid rgba(180,210,220,0.2)",
              borderRadius: 10,
            }}
            labelFormatter={(label) => new Date(String(label)).toISOString()}
            // Recharts passes the Line `name` ("Actual" / "Forecast"), not the dataKey.
            formatter={(value, name) => [
              `${Math.round(Number(value ?? 0)).toLocaleString()} MW`,
              String(name),
            ]}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="actual"
            name="Actual"
            stroke="#7eb8ff"
            dot={false}
            strokeWidth={2}
            connectNulls={false}
            isAnimationActive
            animationDuration={700}
          />
          <Line
            type="monotone"
            dataKey="forecast"
            name="Forecast"
            stroke="#2ec4b6"
            dot={false}
            strokeWidth={2}
            connectNulls={false}
            isAnimationActive
            animationDuration={900}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
