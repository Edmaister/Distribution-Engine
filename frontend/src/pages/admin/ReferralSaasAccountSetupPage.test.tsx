import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import type { ReactElement } from "react";
import { createMemoryRouter, Outlet, RouterProvider } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  getAdminOnboardingState,
  type AdminOnboardingStateResponse,
} from "../../api/endpoints/adminOnboarding";
import { ReferralSaasAccountSetupPage } from "./ReferralSaasAccountSetupPage";

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
      children: [{ index: true, element: ui }],
    },
  ]);

  return render(
    <QueryClientProvider client={client}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
}

function mockAccountSetupState(): AdminOnboardingStateResponse {
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
      ],
      summary: {
        ready_count: 1,
        in_progress_count: 0,
        blocked_count: 1,
        missing_evidence_count: 1,
        permission_limited_count: 0,
        go_live_disabled_count: 1,
        total_count: 2,
      },
      guardrails: ["NO_ACCOUNT_CREATION"],
      missing_evidence: [],
      source_warnings: [],
      redactions: ["INTERNAL_IDENTIFIER"],
    },
  };
}

function panelByHeading(heading: string) {
  const headingElement = screen.getByRole("heading", { name: heading });
  const panel = headingElement.closest(".panel");
  if (!panel) {
    throw new Error(`${heading} panel was not rendered`);
  }
  return within(panel as HTMLElement);
}

function lastMatch(elements: HTMLElement[]) {
  const element = elements[elements.length - 1];
  if (!element) {
    throw new Error("Expected at least one matching element");
  }
  return element;
}

describe("ReferralSaasAccountSetupPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedGetAdminOnboardingState.mockResolvedValue(mockAccountSetupState());
  });

  afterEach(() => {
    cleanup();
  });

  it("renders account setup readiness from external references", async () => {
    renderWorkspace(<ReferralSaasAccountSetupPage />);

    expect(await screen.findByRole("heading", { name: "Account setup workflow" })).toBeInTheDocument();
    await waitFor(() =>
      expect(mockedGetAdminOnboardingState).toHaveBeenCalledWith({
        external_tenant_ref: "demo-platform-operator",
        organisation_ref: "demo-organisation",
      }),
    );
    expect(screen.getByText("GO_LIVE_DISABLED")).toBeInTheDocument();
    expect(screen.getByText("ACCOUNT_PROFILE")).toBeInTheDocument();
    expect(screen.getByText("MEMBERSHIP")).toBeInTheDocument();
    expect(screen.getByText("NO_ACCOUNT_CREATION")).toBeInTheDocument();
    expect(screen.getByText("INTERNAL_IDENTIFIER")).toBeInTheDocument();
    expect(screen.queryByText(/tenant_code/i)).not.toBeInTheDocument();
  });

  it("explains the screen purpose, actions, and next step", async () => {
    renderWorkspace(<ReferralSaasAccountSetupPage />);

    expect(await screen.findByRole("heading", { name: "Guided setup path" })).toBeInTheDocument();
    expect(screen.getByText(/Readiness is one checkpoint inside setup/)).toBeInTheDocument();
    expect(screen.getByText(/Submit and review actions remain disabled/)).toBeInTheDocument();
    expect(screen.getByText(/Account creation remains future work/)).toBeInTheDocument();
  });

  it("shows a recommended account setup testing path", async () => {
    renderWorkspace(<ReferralSaasAccountSetupPage />);

    expect(await screen.findByRole("heading", { name: "Guided setup path" })).toBeInTheDocument();
    expect(screen.getByText("Do this next: complete setup actions")).toBeInTheDocument();
    expect(screen.getByText(/Use the Step 2 actions to fill the missing setup evidence/)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Step 1 action: check account scope" })).toBeInTheDocument();
    expect(screen.getByText("Step 2 action: complete setup evidence")).toBeInTheDocument();
    expect(screen.getByText("Step 3 action: move to campaign setup")).toBeInTheDocument();
    expect(screen.getAllByText("Company profile").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Users and roles").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Integration setup").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Readiness checkpoint").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Review handoff").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Campaign setup").length).toBeGreaterThan(0);
    expect(lastMatch(screen.getAllByRole("link", { name: /Campaign readiness/ }))).toHaveAttribute(
      "href",
      "/admin/referral-saas/campaigns",
    );
  });

  it("keeps scope typing local until the tester checks setup", async () => {
    renderWorkspace(<ReferralSaasAccountSetupPage />);

    await screen.findByRole("heading", { name: "Account setup workflow" });
    await waitFor(() => expect(mockedGetAdminOnboardingState).toHaveBeenCalledTimes(1));

    fireEvent.change(screen.getByLabelText("External tenant ref"), {
      target: { value: "org-fnb-referrals" },
    });
    fireEvent.change(screen.getByLabelText("Organisation ref"), {
      target: { value: "fnb-referral-org" },
    });

    expect(screen.getByText("Changes not checked")).toBeInTheDocument();
    expect(screen.getByText("Do this next: confirm the account scope")).toBeInTheDocument();
    expect(mockedGetAdminOnboardingState).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole("button", { name: "Check readiness" }));

    await waitFor(() =>
      expect(mockedGetAdminOnboardingState).toHaveBeenLastCalledWith({
        external_tenant_ref: "org-fnb-referrals",
        organisation_ref: "fnb-referral-org",
      }),
    );
    expect(await screen.findByText("Do this next: complete setup actions")).toBeInTheDocument();
    expect(JSON.stringify(mockedGetAdminOnboardingState.mock.calls)).not.toMatch(
      /account_ref|tenant_code|api_key|client_secret/i,
    );
  });

  it("keeps account creation and membership mutation as visible guardrails", async () => {
    renderWorkspace(<ReferralSaasAccountSetupPage />);

    await screen.findByText("ACCOUNT_PROFILE");
    const guardrailPanel = panelByHeading("Launch guardrails");

    expect(guardrailPanel.getByText("Account creation remains future work")).toBeInTheDocument();
    expect(guardrailPanel.getByText(/No account table, membership table/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /create account/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /invite/i })).not.toBeInTheDocument();
  });

  it("links to existing setup surfaces without forking source workflows", async () => {
    renderWorkspace(<ReferralSaasAccountSetupPage />);

    await screen.findByText("ACCOUNT_PROFILE");
    expect(lastMatch(screen.getAllByRole("link", { name: /Company onboarding/ }))).toHaveAttribute(
      "href",
      "/admin/onboarding/company",
    );
    expect(lastMatch(screen.getAllByRole("link", { name: /User and role setup/ }))).toHaveAttribute(
      "href",
      "/admin/onboarding/members-roles",
    );
    expect(lastMatch(screen.getAllByRole("link", { name: /Integration setup/ }))).toHaveAttribute(
      "href",
      "/admin/onboarding/webhook-api",
    );
    expect(lastMatch(screen.getAllByRole("link", { name: /Campaign readiness/ }))).toHaveAttribute(
      "href",
      "/admin/referral-saas/campaigns",
    );
  });
});
