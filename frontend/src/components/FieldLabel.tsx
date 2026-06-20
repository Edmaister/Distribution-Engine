import { InfoTooltip } from "./InfoTooltip";

type Props = {
  help: string;
  htmlFor: string;
  label: string;
};

export function FieldLabel({ htmlFor, label, help }: Props) {
  return (
    <label className="label-with-help" htmlFor={htmlFor}>
      {label}
      <InfoTooltip text={help} />
    </label>
  );
}
