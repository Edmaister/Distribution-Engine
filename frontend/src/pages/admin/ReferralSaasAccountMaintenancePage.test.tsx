import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactElement } from "react";
import { createMemoryRouter, Outlet, RouterProvider } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  getAdminOnboardingState,
  type AdminOnboardingStateResponse,
} from "../../api/endpoints/adminOnboarding";
import { ReferralSaasAccountMaintenancePage } from "./ReferralSaasAccountMaintenancePage";

vi.mock("../../api/endpoints/adminOnboarding", () => ({
  getAdminOnboardingState: vi.fn(),
}));

const mockedGetAdminOnboardingState = vi.mocked(getAdminOnboardingState);

function renderWorkspace(ui: ReactElement) {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  const router = createMemoryRouter([
    {
      path: "/",
      element: <Outlet context={{ refreshKey: 0 }} />,
      children: [
        { index: true, element: ui },
        { path: "admin/referral-saas/account-setup", element: <div>Account Setup Target</div> },
        { path: "admin/referral-saas/campaigns", element: <div>Campaign Target</div> },
        { path: "admin/referral-saas/reports", element: <div>Reports Target</div> },
        { path: "admin/referral-saas/support", element: <div>Support Target</div> },
      ],
    },
  ]);

  return render(
    <QueryClientProvider client={client}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
}

function mockMaintenanceState(): AdminOnboardingStateResponse {
  return {
    status: "ok",
    guardrail: "Read-only onboarding state projection.",
    onboarding_state: {
      contract_version: "onboarding.v1",
      scope: {
        external_tenant_ref: "demo-platform-operator",
        organisation_ref: "demo-organisation",
        resolved_tenant: { status: "AVAILABLE" },
      },
      sections: {},
      readiness: {},
      missing_evidence: [],
      guardrails: ["NO_ACCOUNT_CREATION", "NO_LIVE_ACTIONS", "NO_VALUE_TRANSFER"],
      redactions: ["INTERNAL_IDENTIFIER", "SECRETS_REDACTED"],
      source_warnings: [],
    },
    readiness: {
      contract_version: "onboarding.v1",
      overall_status: "GO_LIVE_DISABLED",
      categories: [
        {
          category: "ACCOUNT_PROFILE",
          display_label: "Account profile",
          status: "READY",
          safe_display_status: {
            status: "READY",
            label: "Ready",
            action_required: false,
            go_live_enabled: false,
          },
          evidence_summary: "Organisation profile and primary contact are captured.",
          blockers: [],
          next_actions: ["Review tenant link before campaign setup."],
        },
        {
          category: "MEMBERSHIP",
          display_label: "Membership and roles",
          status: "MISSING_EVIDENCE",
          safe_display_status: {
            status: "NEEDS_ATTENTION",
            label: "Needs evidence",
            action_required: true,
            go_live_enabled: false,
          },
          evidence_summary: "Owner and campaign manager role-family intent is incomplete.",
          blockers: ["Invite evidence is not complete."],
          next_actions: ["Draft owner and campaign manager access."],
        },
        {
          category: "WEBHOOK_API",
          display_label: "Webhook and API setup",
          status: "MISSING_EVIDENCE",
          safe_display_status: {
            status: "NEEDS_ATTENTION",
            label: "Needs evidence",
            action_required: true,
            go_live_enabled: false,
          },
          evidence_summary: "Integration owner and callback intent are incomplete.",
          blockers: [],
          next_actions: ["Capture API and webhook setup intent."],
        },
      ],
      summary: {
        ready_count: 1,
        in_progress_count: 0,
        blocked_count: 1,
        missing_evidence_count: 2,
        permission_limited_count: 0,
        go_live_disabled_count: 1,
        total_count: 3,
      },
      guardrails: ["NO_ACCOUNT_CREATION"],
      missing_evidence: [],
      source_warnings: [],
      redactions: ["INTERNAL_IDENTIFIER"],
    },
  };
}

describe("ReferralSaasAccountMaintenancePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedGetAdminOnboardingState.mockResolvedValue(mockMaintenanceState());
  });

  afterEach(() => {
    cleanup();
  });

  it("renders read-only account maintenance evidence from external references", async () => {
    renderWorkspace(<ReferralSaasAccountMaintenancePage />);

    expect(await screen.findByRole("heading", { name: "Account maintenance evidence" })).toBeInTheDocument();
    await waitFor(() =>
      expect(mockedGetAdminOnboardingState).toHaveBeenCalledWith({
        external_tenant_ref: "demo-platform-operator",
        organisation_ref: "demo-organisation",
      }),
    );

    expect(screen.getByText("Read-only evidence")).toBeInTheDocument();
    expect(screen.getByText("Do this next: route the fix to Account Setup")).toBeInTheDocument();
    expect(screen.getByText("Account profile")).toBeInTheDocument();
    expect(screen.getByText("Users and roles")).toBeInTheDocument();
    expect(screen.getByText("Integration posture")).toBeInTheDocument();
    expect(screen.queryByText(/tenant_code/i)).not.toBeInTheDocument();
  });

  it("keeps scope typing local until the tester checks maintenance evidence", async () => {
    renderWorkspace(<ReferralSaasAccountMaintenancePage />);

    await screen.findByRole("heading", { name: "Account maintenance evidence" });
    await waitFor(() => expect(mockedGetAdminOnboardingState).toHaveBeenCalledTimes(1));

    fireEvent.change(screen.getByLabelText("External tenant ref"), {
      target: { value: "fnb-referral-account" },
    });
    fireEvent.change(screen.getByLabelText("Organisation ref"), {
      target: { value: "fnb-demo-org" },
    });

    expect(screen.getByText("Changes not checked")).toBeInTheDocument();
    expect(screen.getByText("Do this next: reload account evidence")).toBeInTheDocument();
    expect(mockedGetAdminOnboardingState).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole("button", { name: "Check maintenance evidence" }));

    await waitFor(() =>
      expect(mockedGetAdminOnboardingState).toHaveBeenLastCalledWith({
        external_tenant_ref: "fnb-referral-account",
        organisation_ref: "fnb-demo-org",
      }),
    );
    expect(JSON.stringify(mockedGetAdminOnboardingState.mock.calls)).not.toMatch(
      /account_ref|tenant_code|api_key|client_secret/i,
    );
  });

  it("routes fixes to existing product surfaces without adding maintenance commands", async () => {
    renderWorkspace(<ReferralSaasAccountMaintenancePage />);

    await screen.findByRole("heading", { name: "Maintenance areas" });

    expect(screen.getAllByRole("link", { name: /Account profile/ })[0]).toHaveAttribute(
      "href",
      "/admin/referral-saas/account-setup",
    );
    expect(screen.getByRole("link", { name: /Campaign handoff/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/campaigns",
    );
    expect(screen.getByRole("link", { name: /Reporting posture/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/reports",
    );
    expect(screen.getByRole("link", { name: /Audit and support posture/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/support",
    );

    expect(screen.queryByRole("button", { name: /create account/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /invite/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /rotate/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /go-live/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /money/i })).not.toBeInTheDocument();
  });

  it("shows blocked future commands as unavailable read-only evidence", async () => {
    renderWorkspace(<ReferralSaasAccountMaintenancePage />);

    expect(await screen.findByRole("heading", { name: "Unavailable maintenance commands" })).toBeInTheDocument();
    expect(screen.getByText("Create, activate, suspend, or disable account")).toBeInTheDocument();
    expect(screen.getByText("Invite, remove, or change user roles")).toBeInTheDocument();
    expect(screen.getByText("Rotate credentials or enable webhook delivery")).toBeInTheDocument();
    expect(
      screen.getByText("Reward, funding, fulfilment, settlement, payout, invoice, wallet, or money movement"),
    ).toBeInTheDocument();
    expect(screen.getAllByText("Unavailable").length).toBeGreaterThan(0);
  });
});
