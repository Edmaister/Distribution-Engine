import { SummaryItem } from "./SummaryItem";

type SummaryGridItem = {
  label: string;
  value: unknown;
};
type SummaryGridEntry = SummaryGridItem | [string, unknown];

type Props = {
  actionResult?: boolean;
  className?: string;
  items: SummaryGridEntry[];
};

export function SummaryGrid({ actionResult = false, className = "", items }: Props) {
  const classes = ["summary-grid", actionResult ? "action-result" : "", className].filter(Boolean).join(" ");

  return (
    <div className={classes}>
      {items.map((item) => (
        <SummaryItem key={Array.isArray(item) ? item[0] : item.label} label={Array.isArray(item) ? item[0] : item.label} value={Array.isArray(item) ? item[1] : item.value} />
      ))}
    </div>
  );
}
