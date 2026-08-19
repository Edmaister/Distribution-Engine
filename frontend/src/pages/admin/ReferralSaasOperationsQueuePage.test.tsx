import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, RouterProvider, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { useReferralSaasOperationsQueue } from "../../api/referralSaasAccountQueries";
import { ReferralSaasOperationsQueuePage } from "./ReferralSaasOperationsQueuePage";

vi.mock("../../api/referralSaasAccountQueries", () => ({ useReferralSaasOperationsQueue: vi.fn() }));
const mockQueue = vi.mocked(useReferralSaasOperationsQueue);

const response = {
  status: "ok" as const,
  operatorScope: { role: "AMPLIFI_ADMIN", jurisdictions: ["BW", "ZA"] },
  operations: {
    metrics: { awaitingYourAction: 3, customersNeedingAttention: 2, withinServiceTargetPercent: null, serviceTargetStatus: "UNAVAILABLE" as const, productionIncidents: 0 },
    workItems: [{
      workItemRef: "case-1", workItemType: "SUPPORT_CASE" as const, title: "Review referral evidence",
      customer: { accountRef: "account-1", accountCode: "ACC-100", label: "Northstar Financial" }, jurisdiction: "ZA",
      priority: "HIGH" as const, status: "OPEN", category: "REFERRAL_EVIDENCE", ownerRef: null, updatedAt: "2026-08-19T08:00:00Z",
      serviceTarget: { status: "UNAVAILABLE" as const, dueAt: null }, destination: "/admin/referral-saas/account-maintenance/account-1/support?case=case-1",
    }],
    nextCursor: "25", filters: { jurisdictions: ["ZA"], priority: null, customer: null, category: null, status: null, owner: null, workType: null, serviceTarget: null, sort: "PRIORITY", limit: 25 }, metricDefinitions: {}, guardrails: [], redactions: [],
  },
  noCrossJurisdictionAccessConfirmed: true, noSyntheticFrontendMetricsConfirmed: true,
};

function Location() { return <output data-testid="location">{useLocation().search}</output>; }
function renderQueue(initial = "/admin/referral-saas/operations/work-queue") {
  const router = createMemoryRouter([{ path: "/admin/referral-saas/operations/work-queue", element: <><ReferralSaasOperationsQueuePage /><Location /></> }], { initialEntries: [initial] });
  return render(<RouterProvider router={router} />);
}

describe("ReferralSaasOperationsQueuePage", () => {
  afterEach(() => cleanup());

  it("reads URL filters and opens only the persisted destination", () => {
    mockQueue.mockReturnValue({ data: response, isLoading: false, error: null } as unknown as ReturnType<typeof useReferralSaasOperationsQueue>);
    renderQueue("/admin/referral-saas/operations/work-queue?jurisdiction=ZA&priority=HIGH&status=OPEN&limit=25");
    expect(mockQueue).toHaveBeenCalledWith(expect.objectContaining({ jurisdiction: "ZA", priority: "HIGH", status: "OPEN", limit: 25 }), 0);
    expect(screen.getByRole("link", { name: /Review referral evidence/ })).toHaveAttribute("href", "/admin/referral-saas/account-maintenance/account-1/support?case=case-1");
  });

  it("writes filters and pagination to the URL", async () => {
    mockQueue.mockReturnValue({ data: response, isLoading: false, error: null } as unknown as ReturnType<typeof useReferralSaasOperationsQueue>);
    renderQueue();
    fireEvent.change(screen.getByLabelText("Priority"), { target: { value: "CRITICAL" } });
    await waitFor(() => expect(screen.getByTestId("location")).toHaveTextContent("priority=CRITICAL"));
    fireEvent.click(screen.getByRole("button", { name: /Next/ }));
    await waitFor(() => expect(screen.getByTestId("location")).toHaveTextContent("cursor=25"));
  });

  it("explains an empty filtered queue", () => {
    mockQueue.mockReturnValue({ data: { ...response, operations: { ...response.operations, workItems: [], nextCursor: null } }, isLoading: false, error: null } as unknown as ReturnType<typeof useReferralSaasOperationsQueue>);
    renderQueue("/admin/referral-saas/operations/work-queue?owner=UNASSIGNED");
    expect(screen.getByText(/No work matches these filters/)).toBeInTheDocument();
  });
});
