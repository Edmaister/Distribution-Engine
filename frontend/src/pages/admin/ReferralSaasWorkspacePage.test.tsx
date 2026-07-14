import { cleanup, render, screen } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { afterEach, describe, expect, it } from "vitest";

import { ReferralSaasWorkspacePage } from "./ReferralSaasWorkspacePage";

function renderWorkspace() {
  const router = createMemoryRouter([
    {
      path: "/admin/referral-saas",
      element: <ReferralSaasWorkspacePage />,
    },
  ], {
    initialEntries: ["/admin/referral-saas"],
  });

  return render(<RouterProvider router={router} />);
}

describe("ReferralSaasWorkspacePage", () => {
  afterEach(() => {
    cleanup();
  });

  it("renders the focused Referral SaaS workspace", () => {
    renderWorkspace();

    expect(screen.getByRole("heading", { name: "Focused workspace" })).toBeInTheDocument();
    expect(screen.getByText("Referral Management and Campaign Attribution SaaS")).toBeInTheDocument();
    expect(screen.getByText("Ringfenced")).toBeInTheDocument();
    expect(screen.getByText("DLaaS controls")).toBeInTheDocument();
    expect(screen.getByText("Money actions")).toBeInTheDocument();
  });

  it("links only to Referral SaaS product surfaces", () => {
    renderWorkspace();

    const expectedLinks = [
      ["/admin/referral-saas/account-setup", /Account setup/],
      ["/admin/referral-saas/campaigns", /Campaign readiness/],
      ["/admin/referral-saas/link-codes", /Links and codes/],
      ["/admin/referral-saas/reports", /Reports/],
      ["/admin/referral-saas/support", /Support hub/],
      ["/admin/referral-saas/operator-links", /Link inspection/],
      ["/admin/referral-saas/attribution-trace", /Attribution trace/],
      ["/admin/referral-saas/progress-status", /Progress status/],
    ] as const;

    for (const [href, name] of expectedLinks) {
      expect(screen.getByRole("link", { name })).toHaveAttribute("href", href);
    }

    expect(screen.queryByRole("link", { name: /Distribution/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /Settlement/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /Wallet/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /Billing/i })).not.toBeInTheDocument();
  });

  it("states the product boundary guardrails", () => {
    renderWorkspace();

    expect(
      screen.getByText("Focused on referral management and campaign attribution only"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("No distributor marketplace, wallet, settlement, funding, billing, or treasury controls"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("No repair, replay, retry, reward, payout, invoice, or money movement actions"),
    ).toBeInTheDocument();
  });
});
