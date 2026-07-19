import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { Sidebar } from "./Sidebar";

vi.mock("../auth/useBackendSession", () => ({
  useBackendSession: () => ({
    status: "idle",
    workspaces: [],
    recommendedWorkspace: null,
  }),
  workspaceForPath: () => null,
}));

function renderSidebar(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Sidebar />
    </MemoryRouter>,
  );
}

describe("Sidebar", () => {
  it("ringfences Referral SaaS navigation inside the product workspace", () => {
    renderSidebar("/admin/referral-saas");

    expect(screen.getAllByText("Referral SaaS").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Management & Attribution")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Workspace Home/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas",
    );
    expect(screen.getByRole("link", { name: /Campaigns/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/campaigns",
    );
    expect(screen.getByText("While in a customer")).toBeInTheDocument();
    expect(screen.getByText("Global")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Customer profile/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/account-maintenance",
    );
    expect(screen.getByRole("link", { name: /Attribution Trace/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/attribution-trace",
    );

    expect(screen.queryByRole("link", { name: /Demo Home/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /Demand Marketplace/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /Funding Spine/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /Settlement Rail/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /My Wallet/ })).not.toBeInTheDocument();
  });

  it("keeps the broader platform navigation outside the Referral SaaS workspace", () => {
    renderSidebar("/admin/demo-home");

    expect(screen.getByText("Amplifi")).toBeInTheDocument();
    expect(screen.getByText("Distribution OS")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Demo Home/ })).toHaveAttribute("href", "/admin/demo-home");
    expect(screen.getByRole("link", { name: /Referral SaaS Setup/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/account-setup",
    );
  });
});
