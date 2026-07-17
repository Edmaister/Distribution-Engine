import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import type { ReactElement } from "react";
import { createMemoryRouter, Outlet, RouterProvider } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  getAdminOnboardingState,
  recordAdminOnboardingReviewDecision,
  saveAdminOnboardingDraft,
  submitAdminOnboardingDraftForReview,
  validateAdminOnboardingDryRun,
  type AdminOnboardingStateResponse,
} from "../../api/endpoints/adminOnboarding";
import { createReferralSaasAccountFromDraft, resolveReferralSaasAccount } from "../../api/endpoints/referralSaasAccounts";
import { ReferralSaasAccountSetupPage } from "./ReferralSaasAccountSetupPage";

vi.mock("../../api/endpoints/adminOnboarding", () => ({
  getAdminOnboardingState: vi.fn(),
  recordAdminOnboardingReviewDecision: vi.fn(),
  saveAdminOnboardingDraft: vi.fn(),
  submitAdminOnboardingDraftForReview: vi.fn(),
  validateAdminOnboardingDryRun: vi.fn(),
}));
vi.mock("../../api/endpoints/referralSaasAccounts", () => ({
  createReferralSaasAccountFromDraft: vi.fn(),
  resolveReferralSaasAccount: vi.fn(),
}));

const mockedGetAdminOnboardingState = vi.mocked(getAdminOnboardingState);
const mockedRecordAdminOnboardingReviewDecision = vi.mocked(recordAdminOnboardingReviewDecision);
const mockedSaveAdminOnboardingDraft = vi.mocked(saveAdminOnboardingDraft);
const mockedSubmitAdminOnboardingDraftForReview = vi.mocked(submitAdminOnboardingDraftForReview);
const mockedValidateAdminOnboardingDryRun = vi.mocked(validateAdminOnboardingDryRun);
const mockedCreateReferralSaasAccountFromDraft = vi.mocked(createReferralSaasAccountFromDraft);
const mockedResolveReferralSaasAccount = vi.mocked(resolveReferralSaasAccount);

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

function mockValidationResponse() {
  return {
    status: "ok",
    validation_result: { status: "VALID" },
    readiness_preview: mockAccountSetupState().readiness,
    missing_evidence: [],
    blockers: [],
    warnings: [],
    safe_errors: [],
    next_actions: ["Save setup draft."],
    guardrails: ["NO_PERSISTENCE", "NO_LIVE_MUTATION"],
    redactions: ["INTERNAL_IDENTIFIER"],
    no_persistence_confirmed: true,
    no_live_action_confirmed: true,
  };
}

function mockDraftSaveResponse() {
  return {
    status: "ok",
    draft_ref: "draft_referral_saas_setup",
    draft_status: "DRAFT_CREATED",
    draft_version: 1,
    idempotency_status: "NEW_REQUEST",
    validation_summary: {
      status: "VALID",
      safe_error_count: 0,
      missing_evidence_count: 0,
      blocker_count: 0,
    },
    next_actions: ["Submit setup draft for review."],
    guardrails: ["NO_LIVE_ACTION"],
    redactions: ["INTERNAL_IDENTIFIER"],
    no_live_action_confirmed: true,
  };
}

function mockSubmitResponse() {
  return {
    status: "ok",
    draft_ref: "draft_referral_saas_setup",
    draft_status: "READY_FOR_REVIEW",
    draft_version: 2,
    idempotency_status: "NEW_REQUEST",
    validation_summary: {
      status: "VALID",
      safe_error_count: 0,
      missing_evidence_count: 0,
      blocker_count: 0,
    },
    readiness_summary: {
      overall_status: "GO_LIVE_DISABLED",
      ready_count: 3,
      blocked_count: 0,
      missing_evidence_count: 0,
      go_live_disabled_count: 1,
      total_count: 4,
      go_live_enabled: false,
    },
    next_actions: ["Record internal review decision."],
    guardrails: ["NO_LIVE_ACTION"],
    redactions: ["INTERNAL_IDENTIFIER"],
    no_live_action_confirmed: true,
  };
}

function mockReviewResponse() {
  return {
    status: "ok",
    draft_ref: "draft_referral_saas_setup",
    previous_status: "READY_FOR_REVIEW",
    draft_status: "READY_FOR_REVIEW",
    draft_version: 3,
    review_outcome: "APPROVED_FOR_INTERNAL_REVIEW",
    reason_category: "OPERATOR_REVIEW",
    idempotency_status: "NEW_REQUEST",
    guardrails: ["NO_LIVE_ACTION"],
    redactions: ["INTERNAL_IDENTIFIER"],
    audit_evidence_status: "RECORDED_REFERENCE",
    approval_to_launch: false,
    go_live_enabled: false,
    no_live_action_confirmed: true,
  };
}

function mockAccountResolutionResponse() {
  return {
    status: "ok",
    context: "setup" as const,
    account: {
      accountId: "acc_fnb",
      accountCode: "FNB_REFERRAL_SAAS",
      accountName: "FNB Referral SaaS",
      accountType: "REFERRAL_SAAS_CUSTOMER",
      accountStatus: "ACTIVE",
      onboardingStatus: "READY_FOR_SETUP",
      externalRefId: "ext_fnb",
      refType: "external_tenant_ref",
      externalRef: "demo-platform-operator",
      referenceStatus: "ACTIVE",
      accountTenantId: "acct_tenant_fnb",
      relationshipType: "PRIMARY",
      tenantLinkStatus: "ACTIVE",
      isPrimary: true,
      source: "external_reference",
    },
    guardrail: "Read-only Referral SaaS account resolver.",
  };
}

function mockAccountCreateResponse() {
  return {
    status: "created",
    account: {
      accountId: "acc_created",
      accountCode: "ACCT_CREATED",
      accountName: "demo-organisation Referral SaaS setup",
      accountStatus: "PENDING_ONBOARDING",
      onboardingStatus: "READY_FOR_REVIEW",
      tenantLinkStatus: "PENDING_SETUP",
    },
    guardrails: ["DURABLE_ACCOUNT_FOUNDATION_ONLY", "NO_TENANT_CREATION", "NO_MONEY_MOVEMENT"],
    redactions: ["internal_tenant_identifier"],
    noAdjacentLiveActionConfirmed: true,
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
    mockedValidateAdminOnboardingDryRun.mockResolvedValue(mockValidationResponse());
    mockedSaveAdminOnboardingDraft.mockResolvedValue(mockDraftSaveResponse());
    mockedSubmitAdminOnboardingDraftForReview.mockResolvedValue(mockSubmitResponse());
    mockedRecordAdminOnboardingReviewDecision.mockResolvedValue(mockReviewResponse());
    mockedCreateReferralSaasAccountFromDraft.mockResolvedValue(mockAccountCreateResponse());
    mockedResolveReferralSaasAccount.mockResolvedValue(mockAccountResolutionResponse());
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
    expect(mockedResolveReferralSaasAccount).toHaveBeenCalledWith({
      refType: "external_tenant_ref",
      externalRef: "demo-platform-operator",
      context: "setup",
    });
    expect(screen.getByText("GO_LIVE_DISABLED")).toBeInTheDocument();
    expect(screen.getByText("Durable account resolution")).toBeInTheDocument();
    expect(screen.getByText("FNB Referral SaaS - ACTIVE - tenant link ACTIVE")).toBeInTheDocument();
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
    expect(screen.getByText(/Save, submit, and review the setup draft/)).toBeInTheDocument();
    expect(screen.getByText(/Account creation is gated/)).toBeInTheDocument();
  });

  it("shows a recommended account setup testing path", async () => {
    renderWorkspace(<ReferralSaasAccountSetupPage />);

    expect(await screen.findByRole("heading", { name: "Guided setup path" })).toBeInTheDocument();
    expect(screen.getByText("Do this next: complete setup actions")).toBeInTheDocument();
    expect(screen.getByText(/Use the Step 2 actions to fill the missing setup evidence/)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Step 1 action: check account setup" })).toBeInTheDocument();
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

    fireEvent.click(screen.getByRole("button", { name: "Check setup" }));

    await waitFor(() =>
      expect(mockedGetAdminOnboardingState).toHaveBeenLastCalledWith({
        external_tenant_ref: "org-fnb-referrals",
        organisation_ref: "fnb-referral-org",
      }),
    );
    await waitFor(() =>
      expect(mockedResolveReferralSaasAccount).toHaveBeenLastCalledWith({
        refType: "external_tenant_ref",
        externalRef: "org-fnb-referrals",
        context: "setup",
      }),
    );
    expect(await screen.findByText("Do this next: complete setup actions")).toBeInTheDocument();
    expect(JSON.stringify(mockedGetAdminOnboardingState.mock.calls)).not.toMatch(
      /account_ref|tenant_code|api_key|client_secret/i,
    );
    expect(screen.getByRole("button", { name: "Save setup draft" })).toBeEnabled();
  });

  it("keeps first-time setup usable when no durable account exists yet", async () => {
    mockedResolveReferralSaasAccount.mockRejectedValue({
      status: 404,
      message: "External reference was not found.",
    });

    renderWorkspace(<ReferralSaasAccountSetupPage />);

    expect(await screen.findByRole("heading", { name: "Account setup workflow" })).toBeInTheDocument();
    expect(await screen.findByText("No durable account was found for this reference yet. Continue the Account Setup draft path.")).toBeInTheDocument();
    expect(screen.getByText("Setup draft")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Save setup draft" })).toBeEnabled();
    expect(screen.queryByText(/tenant_code/i)).not.toBeInTheDocument();
  });

  it("connects setup workflow actions to existing onboarding draft APIs safely", async () => {
    renderWorkspace(<ReferralSaasAccountSetupPage />);

    await screen.findByRole("heading", { name: "Setup draft actions" });

    fireEvent.click(screen.getByRole("button", { name: "Validate setup" }));
    await waitFor(() => expect(mockedValidateAdminOnboardingDryRun).toHaveBeenCalledTimes(1));
    const validationRequest = mockedValidateAdminOnboardingDryRun.mock.calls[0][0];
    expect(validationRequest).toMatchObject({
      external_tenant_ref: "demo-platform-operator",
      organisation_ref: "demo-organisation",
      validation_scope: ["company", "member_role", "webhook_api"],
      correlation_id: "referral-saas-account-setup-validate",
    });
    expect(validationRequest.idempotency_key).toContain("referral-saas-account-setup-validate");
    expect(Object.keys(validationRequest.sections || {})).toEqual(["company", "member_role", "webhook_api"]);
    expect(JSON.stringify(validationRequest).toLowerCase()).not.toMatch(/tenant_code|api_key|client_secret|wallet|settlement|money/);
    expect(await screen.findByText("Validation completed without saving.")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Save setup draft" }));
    await waitFor(() => expect(mockedSaveAdminOnboardingDraft).toHaveBeenCalledTimes(1));
    const draftRequest = mockedSaveAdminOnboardingDraft.mock.calls[0][0];
    expect(draftRequest).toMatchObject({
      external_tenant_ref: "demo-platform-operator",
      organisation_ref: "demo-organisation",
      correlation_id: "referral-saas-account-setup-draft",
    });
    expect(draftRequest.idempotency_key).toContain("referral-saas-account-setup-draft");
    expect(JSON.stringify(draftRequest).toLowerCase()).not.toMatch(/tenant_code|api_key|client_secret|wallet|settlement|money/);
    expect(await screen.findByText("Setup draft saved.")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Submit for review" }));
    await waitFor(() => expect(mockedSubmitAdminOnboardingDraftForReview).toHaveBeenCalledTimes(1));
    const [draftRef, submitRequest] = mockedSubmitAdminOnboardingDraftForReview.mock.calls[0];
    expect(draftRef).toBe("draft_referral_saas_setup");
    expect(submitRequest).toMatchObject({
      external_tenant_ref: "demo-platform-operator",
      organisation_ref: "demo-organisation",
      expected_version: 1,
      correlation_id: "referral-saas-account-setup-submit-review",
    });
    expect(submitRequest.idempotency_key).toContain("referral-saas-account-setup-submit");
    expect(JSON.stringify(submitRequest).toLowerCase()).not.toMatch(/tenant_code|api_key|client_secret|wallet|settlement|money/);
    expect(await screen.findByText("Setup draft submitted for review.")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Review reason"), {
      target: { value: "Setup evidence is complete enough for internal review." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Accept internal review" }));
    await waitFor(() => expect(mockedRecordAdminOnboardingReviewDecision).toHaveBeenCalledTimes(1));
    const [reviewDraftRef, reviewRequest] = mockedRecordAdminOnboardingReviewDecision.mock.calls[0];
    expect(reviewDraftRef).toBe("draft_referral_saas_setup");
    expect(reviewRequest).toMatchObject({
      external_tenant_ref: "demo-platform-operator",
      organisation_ref: "demo-organisation",
      expected_version: 2,
      review_outcome: "APPROVED_FOR_INTERNAL_REVIEW",
      reason_category: "OPERATOR_REVIEW",
      reason: "Setup evidence is complete enough for internal review.",
      correlation_id: "referral-saas-account-setup-review-decision",
    });
    expect(reviewRequest.idempotency_key).toContain("referral-saas-account-setup-review");
    expect(JSON.stringify(reviewRequest).toLowerCase()).not.toMatch(/tenant_code|api_key|client_secret|wallet|settlement|money/);
    expect(await screen.findByText("Internal review decision recorded.")).toBeInTheDocument();
    expect(screen.getByText(/go-live: disabled/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Create account foundation" })).toBeDisabled();
  });

  it("creates the account foundation only after accepted internal review when no durable account exists", async () => {
    mockedResolveReferralSaasAccount.mockRejectedValue({
      status: 404,
      message: "External reference was not found.",
    });

    renderWorkspace(<ReferralSaasAccountSetupPage />);

    await screen.findByRole("heading", { name: "Setup draft actions" });
    expect(await screen.findByText(/No durable account was found/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Create account foundation" })).toBeDisabled();

    fireEvent.click(screen.getByRole("button", { name: "Save setup draft" }));
    await screen.findByText("Setup draft saved.");

    fireEvent.click(screen.getByRole("button", { name: "Submit for review" }));
    await screen.findByText("Setup draft submitted for review.");

    fireEvent.change(screen.getByLabelText("Review reason"), {
      target: { value: "Setup evidence is ready for account foundation creation." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Accept internal review" }));
    await screen.findByText("Internal review decision recorded.");

    const createButton = screen.getByRole("button", { name: "Create account foundation" });
    await waitFor(() => expect(createButton).toBeEnabled());
    fireEvent.click(createButton);

    await waitFor(() => expect(mockedCreateReferralSaasAccountFromDraft).toHaveBeenCalledTimes(1));
    expect(mockedCreateReferralSaasAccountFromDraft).toHaveBeenCalledWith({
      draftRef: "draft_referral_saas_setup",
      internalTenantCode: "FNB",
      idempotencyKey: "referral-saas-account-setup-create:draft_referral_saas_setup",
    });
    expect(JSON.stringify(mockedCreateReferralSaasAccountFromDraft.mock.calls).toLowerCase()).not.toMatch(
      /client_secret|wallet|settlement|money_movement|go_live_enabled/,
    );
    expect(await screen.findByText("Account foundation created.")).toBeInTheDocument();
    expect(screen.getByText(/PENDING_ONBOARDING/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /invite/i })).not.toBeInTheDocument();
  });

  it("keeps account creation and membership mutation as visible guardrails", async () => {
    renderWorkspace(<ReferralSaasAccountSetupPage />);

    await screen.findByText("ACCOUNT_PROFILE");
    const guardrailPanel = panelByHeading("Launch guardrails");

    expect(guardrailPanel.getByText("Account creation is gated")).toBeInTheDocument();
    expect(guardrailPanel.getByText(/available only after setup draft save/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Create account foundation" })).toBeDisabled();
    expect(screen.queryByRole("button", { name: /invite/i })).not.toBeInTheDocument();
  });

  it("links to existing setup surfaces without forking source workflows", async () => {
    renderWorkspace(<ReferralSaasAccountSetupPage />);

    await screen.findByText("ACCOUNT_PROFILE");
    expect(lastMatch(screen.getAllByRole("link", { name: /Company profile/ }))).toHaveAttribute(
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
