import { StatusBadge } from "./StatusBadge";

export type GuardrailTone = "success" | "warning" | "danger" | "info" | "neutral";

export type GuardrailItem = {
  label: string;
  value: string;
  tone?: GuardrailTone;
};

type Props = {
  badge: string;
  tone: GuardrailTone;
  title: string;
  copy: string;
  items: GuardrailItem[];
  label?: string;
};

export function ActionGuardrail({ badge, tone, title, copy, items, label = "Decision guide" }: Props) {
  return (
    <div className="action-guardrail">
      <div className="action-guardrail-header">
        <div>
          <div className="guidance-kicker">{label}</div>
          <div className="action-guardrail-title">{title}</div>
          <p className="guidance-copy">{copy}</p>
        </div>
        <StatusBadge label={badge} tone={tone} />
      </div>
      <div className="action-guardrail-list">
        {items.map((item) => (
          <div className="action-guardrail-item" key={item.label}>
            <span>{item.label}</span>
            <StatusBadge label={item.value} tone={item.tone || "neutral"} />
          </div>
        ))}
      </div>
    </div>
  );
}
