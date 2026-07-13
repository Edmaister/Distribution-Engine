import { cleanup, render, screen, within } from "@testing-library/react";
import { createMemoryRouter, Outlet, RouterProvider } from "react-router-dom";
import { afterEach, describe, expect, it } from "vitest";

import { ReferralSaasSupportHubPage } from "./ReferralSaasSupportHubPage";

function renderWorkspace() {
  const router = createMemoryRouter([
    {
      path: "/",
      element: <Outlet context={{ refreshKey: 0 }} />,
      children: [{ index: true, element: <ReferralSaasSupportHubPage /> }],
    },
  ]);

  return render(<RouterProvider router={router} />);
}

function panelByHeading(heading: string) {
  const headingElement = screen.getByRole("heading", { name: heading });
  const panel = headingElement.closest(".panel");
  if (!panel) {
    throw new Error(`${heading} panel was not rendered`);
  }
  return within(panel as HTMLElement);
}

describe("ReferralSaasSupportHubPage", () => {
  afterEach(() => {
    cleanup();
  });

  it("renders the read-only support workflow hub", () => {
    renderWorkspace();

    expect(screen.getByRole("heading", { name: "Support workflow hub" })).toBeInTheDocument();
    expect(screen.getAllByText("Read-only").length).toBeGreaterThan(0);
    expect(screen.getByText("Support cases")).toBeInTheDocument();
    expect(screen.getByText("Mutation actions")).toBeInTheDocument();
    expect(screen.getByText("Money actions")).toBeInTheDocument();
  });

  it("routes support case types to existing Referral SaaS diagnostic surfaces", () => {
    renderWorkspace();

    expect(screen.getByRole("link", { name: /Code or link not recognized/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/operator-links",
    );
    expect(screen.getByRole("link", { name: /Validation failed or customer cannot continue/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/link-codes",
    );
    expect(screen.getByRole("link", { name: /Progress stuck or delayed/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/progress-status",
    );
    expect(screen.getByRole("link", { name: /Attribution missing or partial/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/attribution-trace",
    );
    expect(screen.getByRole("link", { name: /Campaign not ready/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/campaigns",
    );
    expect(screen.getByRole("link", { name: /Report count mismatch/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/reports",
    );
  });

  it("shows the expected read-only evidence order", () => {
    renderWorkspace();

    const evidenceOrder = panelByHeading("Read-only evidence order");
    expect(evidenceOrder.getByText("1. Link/code inspection")).toBeInTheDocument();
    expect(evidenceOrder.getByText("2. Progress/status")).toBeInTheDocument();
    expect(evidenceOrder.getByText("3. Attribution trace")).toBeInTheDocument();
    expect(evidenceOrder.getByText("4. Campaign and reports")).toBeInTheDocument();
  });

  it("keeps support-case, repair, replay, and money actions absent", () => {
    renderWorkspace();

    expect(screen.queryByRole("button", { name: /support case/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /repair/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /retry/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /replay/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /reward/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /settle/i })).not.toBeInTheDocument();

    const guardrails = panelByHeading("Guardrails");
    expect(guardrails.getByText("No support-case writes")).toBeInTheDocument();
    expect(guardrails.getByText("No repair, retry, or replay")).toBeInTheDocument();
    expect(
      guardrails.getByText("No reward, funding, fulfilment, settlement, wallet, invoice, or payout controls"),
    ).toBeInTheDocument();
  });
});
