import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, Outlet, RouterProvider } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { listReferralSaasOperatorSupportQueue } from "../../api/endpoints/referralSaasAccounts";
import { ReferralSaasSupportHubPage } from "./ReferralSaasSupportHubPage";

vi.mock("../../api/endpoints/referralSaasAccounts", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../api/endpoints/referralSaasAccounts")>()),
  listReferralSaasOperatorSupportQueue: vi.fn(),
}));

const mockedListOperatorQueue = vi.mocked(listReferralSaasOperatorSupportQueue);

function queueResponse() {
  return {
    status: "ok",
    operatorScope: {
      surface: "operator_support_queue",
      role: "REFERRAL_SAAS_READER",
    },
    supportQueue: {
      supportCases: [
        {
          caseRef: "CASE-001",
          accountRef: "acct-1",
          customerLabel: "Acme Retail",
          externalTenantRef: "acme-tenant",
          organisationRef: "acme-org",
          category: "ACCESS_SCOPE",
          priority: "HIGH",
          status: "OPEN",
          title: "Owner responsibility missing",
          sourceSurface: "people_access",
          assigneeRef: null,
          createdAt: "2026-08-01T08:00:00Z",
          updatedAt: "2026-08-01T09:00:00Z",
          evidenceLinkCount: 2,
          noteCount: 1,
          latestActivity: "Status OPEN",
          redactions: ["internal_tenant_identifier"],
          nextAction: "Open customer support case",
        },
      ],
      filters: {},
      nextCursor: null,
      guardrails: ["READ_ONLY_QUEUE"],
      redactions: ["internal_tenant_identifier"],
    },
    guardrail: "Operator support queue is a read-only aggregate.",
    guardrails: ["READ_ONLY_QUEUE", "NO_REPAIR_REPLAY_RETRY"],
    redactions: ["internal_tenant_identifier"],
    no_assignment_from_queue_confirmed: true,
    no_case_lifecycle_mutation_confirmed: true,
    no_repair_replay_retry_confirmed: true,
    no_referral_or_campaign_mutation_confirmed: true,
    no_progress_or_attribution_mutation_confirmed: true,
    no_report_or_export_mutation_confirmed: true,
    no_invite_delivery_confirmed: true,
    no_credential_or_auth_claim_change_confirmed: true,
    no_tenant_code_exposure_confirmed: true,
    no_billing_or_money_movement_confirmed: true,
  };
}

function renderWorkspace() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  const router = createMemoryRouter([
    {
      path: "/",
      element: <Outlet context={{ refreshKey: 0 }} />,
      children: [{ index: true, element: <ReferralSaasSupportHubPage /> }],
    },
  ]);

  return render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
}

describe("ReferralSaasSupportHubPage", () => {
  beforeEach(() => {
    mockedListOperatorQueue.mockResolvedValue(queueResponse());
  });

  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("loads the read-only operator support queue", async () => {
    renderWorkspace();

    expect(screen.getByRole("heading", { name: "Support queue" })).toBeInTheDocument();
    expect(await screen.findByText("Owner responsibility missing")).toBeInTheDocument();
    expect(screen.getByText("Acme Retail")).toBeInTheDocument();
    expect(screen.getByText("CASE-001")).toBeInTheDocument();
    expect(screen.getByText("2 evidence links - 1 note")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Open customer support case" })).toHaveAttribute(
      "href",
      "/admin/referral-saas/account-maintenance/acct-1/support",
    );

    expect(mockedListOperatorQueue).toHaveBeenCalledWith({
      status: "",
      priority: "",
      category: "",
      accountRef: "",
      sourceSurface: "",
      assigneeRef: "",
      limit: 50,
    });
  });

  it("sends bounded queue filters to the read-only API", async () => {
    renderWorkspace();

    await screen.findByText("Owner responsibility missing");

    fireEvent.change(screen.getByLabelText("Status"), { target: { value: "WAITING" } });
    fireEvent.change(screen.getByLabelText("Priority"), { target: { value: "HIGH" } });
    fireEvent.change(screen.getByLabelText("Case type"), { target: { value: "ACCESS_SCOPE" } });
    fireEvent.change(screen.getByLabelText("Source page"), { target: { value: "people_access" } });
    fireEvent.change(screen.getByLabelText("Account reference"), { target: { value: " acct-1 " } });

    await waitFor(() =>
      expect(mockedListOperatorQueue).toHaveBeenLastCalledWith({
        status: "WAITING",
        priority: "HIGH",
        category: "ACCESS_SCOPE",
        accountRef: "acct-1",
        sourceSurface: "people_access",
        assigneeRef: "",
        limit: 50,
      }),
    );
  });

  it("keeps assignment, repair, replay, provider, credential, and money actions absent", async () => {
    renderWorkspace();

    await screen.findByText("Owner responsibility missing");

    expect(screen.queryByRole("button", { name: /assign/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /repair/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /retry/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /replay/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /credential/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /settle|pay|bill/i })).not.toBeInTheDocument();
    expect(screen.getByText("What this queue will not do")).toBeInTheDocument();
    expect(screen.getByText("No assignment, repair, retry, or replay")).toBeInTheDocument();
  });
});
