import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { InfoTooltip } from "./InfoTooltip";

describe("InfoTooltip", () => {
  it("connects the help trigger to the tooltip content", () => {
    render(<InfoTooltip text="Shows context for this field." />);

    const trigger = screen.getByRole("button", { name: "Shows context for this field." });
    const tooltip = screen.getByRole("tooltip");

    expect(trigger).toHaveAttribute("aria-describedby", tooltip.id);
    expect(tooltip).toHaveTextContent("Shows context for this field.");
  });
});
