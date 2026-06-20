import { LucideIcon } from "lucide-react";

type Props = {
  label: string;
  value: string | number;
  footnote?: string;
  icon: LucideIcon;
};

export function KpiCard({ label, value, footnote, icon: Icon }: Props) {
  return (
    <section className="kpi-card">
      <div className="kpi-topline">
        <Icon size={15} />
        {label}
      </div>
      <div className="kpi-value">{value}</div>
      {footnote ? <div className="kpi-footnote">{footnote}</div> : null}
    </section>
  );
}
