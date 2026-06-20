type Props = {
  label: string;
  value: unknown;
};

export function SummaryItem({ label, value }: Props) {
  return (
    <div className="summary-item">
      <div className="summary-label">{label}</div>
      <div className="summary-value">{formatSummaryValue(value)}</div>
    </div>
  );
}

function formatSummaryValue(value: unknown): string {
  if (value === undefined || value === null || value === "") {
    return "-";
  }

  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }

  return String(value);
}
