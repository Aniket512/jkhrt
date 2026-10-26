interface MetricCardProps {
  label: string;
  value: string;
  hint?: string;
}

/** Compact metric tile used for MAE / RMSE / bias / WAPE. */
export function MetricCard({ label, value, hint }: MetricCardProps) {
  return (
    <div className="metric">
      <span className="label">{label}</span>
      <div className="value">{value}</div>
      {hint ? <div className="hint">{hint}</div> : null}
    </div>
  );
}
