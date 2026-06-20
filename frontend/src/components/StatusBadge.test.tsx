import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { StatusBadge } from "./StatusBadge";

describe("StatusBadge", () => {
  it("renders the label and tone class", () => {
    render(<StatusBadge label="Ready" tone="success" />);

    const badge = screen.getByText("Ready");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass("badge", "success");
  });
});
