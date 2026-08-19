import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { Sidebar } from "./Sidebar";

vi.mock("../auth/useBackendSession", () => ({
  useBackendSession: () => ({
    status: "idle",
    workspaces: [],
    recommendedWorkspace: null,
  }),
  workspaceForPath: () => null,
}));

afterEach(cleanup);

function renderSidebar(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Sidebar />
    </MemoryRouter>,
  );
}

describe("Sidebar", () => {
  it("presents the Amplifi Global shell outside selected-customer context", () => {
    renderSidebar("/admin/referral-saas");

    expect(screen.getAllByText("Referral SaaS").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Management & Attribution")).toBeInTheDocument();
    expect(screen.getByLabelText("Amplifi Global workspace")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Operations/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas",
    );
    expect(screen.getByRole("link", { name: /Customer accounts/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/account-setup",
    );
    expect(screen.getByRole("link", { name: /Customer portfolio/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/operations/customer-portfolio",
    );
    expect(screen.getByRole("link", { name: /Find or create customer/ })).toHaveAttribute(
      "href", "/admin/referral-saas/operations/customer-portfolio",
    );
    expect(screen.queryByRole("link", { name: /^Campaigns/ })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Programme governance/ })).toHaveAttribute(
      "href", "/admin/referral-saas/operations/customer-portfolio?destination=programmes",
    );
    expect(screen.getByRole("link", { name: /Commercial governance/ })).toHaveAttribute(
      "href", "/admin/referral-saas/operations/customer-portfolio?destination=commercial",
    );
    expect(screen.queryByRole("link", { name: /Global approvals/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /Global exceptions/ })).not.toBeInTheDocument();

    expect(screen.queryByRole("link", { name: /Demo Home/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /Demand Marketplace/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /Funding Spine/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /Settlement Rail/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /My Wallet/ })).not.toBeInTheDocument();
  });

  it("shows customer-scoped navigation only after an account is selected", () => {
    renderSidebar("/admin/referral-saas/account-maintenance/account-123/people");

    expect(screen.getByLabelText("Selected customer workspace")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Campaigns/ })).toHaveAttribute(
      "href", "/admin/referral-saas/campaigns",
    );
    expect(screen.getByRole("link", { name: /Amplifi Global/ })).toHaveAttribute(
      "href", "/admin/referral-saas",
    );
    expect(screen.queryByRole("link", { name: /Customer accounts/ })).not.toBeInTheDocument();
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
