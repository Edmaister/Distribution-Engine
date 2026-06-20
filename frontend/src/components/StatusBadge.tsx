import { CheckCircle2, CircleAlert, CircleDashed, Info, XCircle } from "lucide-react";

type Tone = "success" | "warning" | "danger" | "info" | "neutral";

type Props = {
  label: string;
  tone?: Tone;
};

const icons = {
  success: CheckCircle2,
  warning: CircleAlert,
  danger: XCircle,
  info: Info,
  neutral: CircleDashed,
};

export function StatusBadge({ label, tone = "neutral" }: Props) {
  const Icon = icons[tone];

  return (
    <span className={`badge ${tone}`}>
      <Icon size={13} />
      {label}
    </span>
  );
}
