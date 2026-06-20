import { InfoTooltip } from "./InfoTooltip";

type Props = {
  help: string;
  title: string;
};

export function PanelTitle({ title, help }: Props) {
  return (
    <h2 className="panel-title with-help">
      {title}
      <InfoTooltip text={help} />
    </h2>
  );
}
