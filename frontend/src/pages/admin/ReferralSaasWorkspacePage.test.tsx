import { cleanup, render, screen } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { useReferralSaasOperationsOverview } from "../../api/referralSaasAccountQueries";
import { ReferralSaasWorkspacePage } from "./ReferralSaasWorkspacePage";

vi.mock("../../api/referralSaasAccountQueries", () => ({ useReferralSaasOperationsOverview: vi.fn() }));
const mockOverview = vi.mocked(useReferralSaasOperationsOverview);

function renderWorkspace() {
  const router = createMemoryRouter([{ path: "/admin/referral-saas", element: <ReferralSaasWorkspacePage /> }], { initialEntries: ["/admin/referral-saas"] });
  return render(<RouterProvider router={router} />);
}

const response = {
  status: "ok" as const,
  operatorScope: { role: "AMPLIFI_ADMIN", jurisdictions: ["ZA"] },
  operations: {
    metrics: { awaitingYourAction: 2, customersNeedingAttention: 1, withinServiceTargetPercent: null, serviceTargetStatus: "UNAVAILABLE" as const, productionIncidents: 0 },
    workItems: [{
      workItemRef: "case-1", workItemType: "SUPPORT_CASE" as const, title: "Referral evidence exception",
      customer: { accountRef: "account-1", accountCode: "ACC-100", label: "Northstar Financial" }, jurisdiction: "ZA",
      priority: "HIGH" as const, status: "OPEN", category: "REFERRAL_EVIDENCE", ownerRef: null, updatedAt: "2026-08-19T08:00:00Z",
      serviceTarget: { status: "UNAVAILABLE" as const, dueAt: null }, destination: "/admin/referral-saas/account-maintenance/account-1/support?case=case-1",
    }],
    nextCursor: null, filters: { jurisdictions: ["ZA"], priority: null, customer: null, category: null, status: null, owner: null, workType: null, serviceTarget: null, sort: "PRIORITY", limit: 8 }, metricDefinitions: {}, guardrails: [], redactions: [],
  },
  noCrossJurisdictionAccessConfirmed: true, noSyntheticFrontendMetricsConfirmed: true,
};

describe("ReferralSaasWorkspacePage", () => {
  afterEach(() => cleanup());

  it("renders authoritative operations metrics without a synthetic SLA", () => {
    mockOverview.mockReturnValue({ data: response, isLoading: false, error: null } as unknown as ReturnType<typeof useReferralSaasOperationsOverview>);
    renderWorkspace();
    expect(screen.getByRole("heading", { name: "Operations workspace" })).toBeInTheDocument();
    expect(screen.getByText("Awaiting your action")).toBeInTheDocument();
    expect(screen.getByText("Not configured")).toBeInTheDocument();
    expect(screen.getByText("No governed SLA source yet")).toBeInTheDocument();
    expect(screen.queryByText("96%")).not.toBeInTheDocument();
  });

  it("opens persisted queue destinations and visible customers", () => {
    mockOverview.mockReturnValue({ data: response, isLoading: false, error: null } as unknown as ReturnType<typeof useReferralSaasOperationsOverview>);
    renderWorkspace();
    expect(screen.getByRole("link", { name: /Referral evidence exception/ })).toHaveAttribute("href", "/admin/referral-saas/account-maintenance/account-1/support?case=case-1");
    expect(screen.getByRole("link", { name: /Northstar Financial ACC-100/ })).toHaveAttribute("href", "/admin/referral-saas/account-maintenance/account-1");
  });

  it("uses a clear customer-directory action", () => {
    mockOverview.mockReturnValue({ data: response, isLoading: false, error: null } as unknown as ReturnType<typeof useReferralSaasOperationsOverview>);
    renderWorkspace();
    expect(screen.getAllByRole("link", { name: /Find or create customer|Find a customer/ })[0]).toHaveAttribute("href", "/admin/referral-saas/account-maintenance");
  });

  it("links the summary to the complete operational queue", () => {
    mockOverview.mockReturnValue({ data: response, isLoading: false, error: null } as unknown as ReturnType<typeof useReferralSaasOperationsOverview>);
    renderWorkspace();
    expect(screen.getByRole("link", { name: /View all work/ })).toHaveAttribute("href", "/admin/referral-saas/operations/work-queue");
  });

  it("shows a plain-language degraded state", () => {
    mockOverview.mockReturnValue({ data: undefined, isLoading: false, error: new Error("Evidence store unavailable") } as unknown as ReturnType<typeof useReferralSaasOperationsOverview>);
    renderWorkspace();
    expect(screen.getByRole("alert")).toHaveTextContent("Operations evidence is unavailable");
    expect(screen.getByRole("alert")).toHaveTextContent("Evidence store unavailable");
  });
});
