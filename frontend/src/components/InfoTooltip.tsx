import { CircleHelp } from "lucide-react";
import { useId } from "react";

type Props = {
  text: string;
};

export function InfoTooltip({ text }: Props) {
  const tooltipId = useId();

  return (
    <span className="tooltip-wrap">
      <button aria-describedby={tooltipId} aria-label={text} className="tooltip-trigger" type="button">
        <CircleHelp size={14} />
      </button>
      <span className="tooltip-bubble" id={tooltipId} role="tooltip">
        {text}
      </span>
    </span>
  );
}
