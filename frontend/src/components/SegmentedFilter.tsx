type Option = {
  label: string;
  value: string;
};

type Props = {
  ariaLabel: string;
  className?: string;
  chipClassName?: string;
  onChange: (value: string) => void;
  options: Option[];
  value: string;
};

export function SegmentedFilter({
  ariaLabel,
  className = "segmented-filter-row",
  chipClassName = "segmented-filter-chip",
  onChange,
  options,
  value,
}: Props) {
  return (
    <div className={className} aria-label={ariaLabel}>
      {options.map((option) => (
        <button
          className={value === option.value ? `${chipClassName} active` : chipClassName}
          key={option.value}
          type="button"
          onClick={() => onChange(option.value)}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
