import { CircleDashed } from "lucide-react";

export function EmptyState({ label }: { label: string }) {
  return (
    <div className="state-panel">
      <CircleDashed size={18} />
      {label}
    </div>
  );
}
