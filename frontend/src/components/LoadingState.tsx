import { Loader2 } from "lucide-react";

export function LoadingState({ label = "Loading data" }: { label?: string }) {
  return (
    <div className="state-panel">
      <Loader2 size={18} />
      {label}
    </div>
  );
}
