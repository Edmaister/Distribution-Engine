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

    expect(screen.getByRole("heading", { name: "Start testing Referral SaaS" })).toBeInTheDocument();
    expect(screen.getByText("Referral Management and Campaign Attribution SaaS")).toBeInTheDocument();
    expect(screen.getByText("Ringfenced")).toBeInTheDocument();
    expect(screen.getByText("Core areas to test")).toBeInTheDocument();
    expect(screen.getByText("DLaaS items shown")).toBeInTheDocument();
    expect(screen.getByText("Money actions available")).toBeInTheDocument();
  });

  it("explains the screen purpose, available actions, and first call to action", () => {
    renderWorkspace();

    expect(screen.getByRole("heading", { name: "What this screen is for" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "What you can do here" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "What to do first" })).toBeInTheDocument();
    expect(screen.getByText(/If setup is blocked, fix that first/)).toBeInTheDocument();
  });

  it("shows a recommended local testing path", () => {
    renderWorkspace();

    expect(screen.getByRole("heading", { name: "Recommended test path" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /1. Check account setup/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/account-setup",
    );
    expect(screen.getByRole("link", { name: /2. Check campaign readiness/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/campaigns",
    );
    expect(screen.getByRole("link", { name: /3. Test links and codes/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/link-codes",
    );
    expect(screen.getByRole("link", { name: /4. Prove attribution and reporting/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/support",
    );
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
