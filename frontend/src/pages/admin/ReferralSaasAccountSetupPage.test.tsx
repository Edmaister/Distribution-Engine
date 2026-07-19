import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
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
import {
  createReferralSaasAccountFromDraft,
  getReferralSaasAccountMembershipPosture,
  recordReferralSaasMembershipInvitationIntent,
  resolveReferralSaasAccount,
} from "../../api/endpoints/referralSaasAccounts";
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
  getReferralSaasAccountMembershipPosture: vi.fn(),
  recordReferralSaasMembershipInvitationIntent: vi.fn(),
  resolveReferralSaasAccount: vi.fn(),
}));

const mockedGetAdminOnboardingState = vi.mocked(getAdminOnboardingState);
const mockedRecordAdminOnboardingReviewDecision = vi.mocked(recordAdminOnboardingReviewDecision);
const mockedSaveAdminOnboardingDraft = vi.mocked(saveAdminOnboardingDraft);
const mockedSubmitAdminOnboardingDraftForReview = vi.mocked(submitAdminOnboardingDraftForReview);
const mockedValidateAdminOnboardingDryRun = vi.mocked(validateAdminOnboardingDryRun);
const mockedCreateReferralSaasAccountFromDraft = vi.mocked(createReferralSaasAccountFromDraft);
const mockedGetReferralSaasAccountMembershipPosture = vi.mocked(getReferralSaasAccountMembershipPosture);
const mockedRecordReferralSaasMembershipInvitationIntent = vi.mocked(recordReferralSaasMembershipInvitationIntent);
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

function mockAccountSetupStateWithMissingCompanyProfile(): AdminOnboardingStateResponse {
  const state = mockAccountSetupState();
  const accountProfile = state.readiness.categories.find((category) => category.category === "ACCOUNT_PROFILE");
  if (accountProfile) {
    accountProfile.status = "MISSING_EVIDENCE";
    accountProfile.safe_display_status = {
      status: "MISSING_EVIDENCE",
      label: "Missing evidence",
      action_required: true,
      go_live_enabled: false,
    };
    accountProfile.evidence_summary = "Company profile evidence is missing.";
  }
  return state;
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

function mockMembershipPostureResponse() {
  return {
    status: "ok",
    context: "setup" as const,
    account: mockAccountResolutionResponse().account,
    membershipPosture: {
      accountId: "acc_fnb",
      totalMemberships: 0,
      invitedCount: 0,
      activeCount: 0,
      suspendedCount: 0,
      disabledCount: 0,
      archivedCount: 0,
      roleFamilies: [],
      currentActor: {
        status: "NO_MEMBERSHIP_EVIDENCE",
        roleFamily: null,
        permissionSet: null,
        canOperateSetup: false,
        evidence: "No active account membership matched the current actor.",
      },
      guardrails: ["READ_ONLY_MEMBERSHIP_POSTURE", "NO_MEMBERSHIP_WRITE", "NO_INVITE_DELIVERY"],
      redactions: ["internal_tenant_identifier", "user_identifier", "client_identifier"],
      noMembershipWriteConfirmed: true,
      noInviteDeliveryConfirmed: true,
    },
    guardrail: "Read-only Referral SaaS account membership posture.",
    no_membership_write_confirmed: true,
    no_invite_delivery_confirmed: true,
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

function mockMembershipInvitationResponse() {
  return {
    status: "ok",
    context: "setup" as const,
    account: mockAccountResolutionResponse().account,
    invitation: {
      commandStatus: "INVITATION_INTENT_RECORDED",
      membership: {
        membershipRef: "mbr_setup_owner",
        status: "INVITED",
        roleFamily: "DISTRIBUTION_ADMIN",
        permissionSet: "REFERRAL_SAAS_ACCOUNT_ADMIN",
        canOperateSetup: false,
      },
      delivery: {
        status: "DELIVERY_NOT_CONFIGURED",
        nextAction: "Configure approved invitation delivery provider",
      },
      idempotency: {
        status: "RECORDED",
      },
      auditEventId: "audit_membership_invite",
      guardrails: ["NO_RAW_EMAIL_STORAGE", "NO_EMAIL_DELIVERY_WITHOUT_PROVIDER"],
      redactions: ["internal_tenant_identifier", "email_hash"],
      noInviteDeliveryConfirmed: true,
      noAuthClaimChangeConfirmed: true,
      noSeatAssignmentConfirmed: true,
      noMoneyMovementConfirmed: true,
    },
    guardrails: ["NO_RAW_EMAIL_STORAGE", "NO_EMAIL_DELIVERY_WITHOUT_PROVIDER"],
    redactions: ["internal_tenant_identifier", "email_hash"],
    no_invite_delivery_confirmed: true,
    no_auth_claim_change_confirmed: true,
    no_seat_assignment_confirmed: true,
    no_money_movement_confirmed: true,
  };
}

function lastMatch(elements: HTMLElement[]) {
  const element = elements[elements.length - 1];
  if (!element) {
    throw new Error("Expected at least one matching element");
  }
  return element;
}

async function waitForWizard() {
  await screen.findByRole("button", { name: "Identify customer" });
}

async function confirmAccountScope() {
  fireEvent.click(screen.getByRole("button", { name: "Find account" }));
  await screen.findByText("Checked");
}

async function recordRoleIntent() {
  fireEvent.click(screen.getByRole("button", { name: "People & roles" }));
  fireEvent.click(screen.getByRole("button", { name: "Record role intent" }));
  await screen.findByText("Role intent recorded.");
}

async function validateSetup() {
  fireEvent.click(screen.getByRole("button", { name: "Readiness check" }));
  fireEvent.click(screen.getByRole("button", { name: "Validate setup" }));
  await screen.findByText("Validation completed without saving.");
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
    mockedGetReferralSaasAccountMembershipPosture.mockResolvedValue(mockMembershipPostureResponse());
    mockedRecordReferralSaasMembershipInvitationIntent.mockResolvedValue(mockMembershipInvitationResponse());
    mockedResolveReferralSaasAccount.mockResolvedValue(mockAccountResolutionResponse());
  });

  afterEach(() => {
    cleanup();
  });

  it("renders account setup readiness from external references", async () => {
    renderWorkspace(<ReferralSaasAccountSetupPage />);

    expect(await screen.findByRole("heading", { name: "Account setup wizard" })).toBeInTheDocument();
    await waitForWizard();
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
    await waitFor(() =>
      expect(mockedGetReferralSaasAccountMembershipPosture).toHaveBeenCalledWith({
        refType: "external_tenant_ref",
        externalRef: "demo-platform-operator",
        context: "setup",
      }),
    );
    expect(screen.getByText("GO_LIVE_DISABLED")).toBeInTheDocument();
    expect(screen.getByText("Safe mode: no go-live / money / credentials")).toBeInTheDocument();
    expect(screen.getByText("Account status")).toBeInTheDocument();
    expect(screen.getByText("FNB Referral SaaS - ACTIVE - tenant link ACTIVE")).toBeInTheDocument();
    await confirmAccountScope();
    fireEvent.click(screen.getByRole("button", { name: "People & roles" }));
    expect(screen.getByText("User access status")).toBeInTheDocument();
    expect(screen.getByText("No membership")).toBeInTheDocument();
    expect(screen.getByText(/Capture who should administer this account/)).toBeInTheDocument();
    expect(screen.queryByText(/tenant_code/i)).not.toBeInTheDocument();
  });

  it("explains the screen purpose, actions, and next step", async () => {
    renderWorkspace(<ReferralSaasAccountSetupPage />);

    expect(await screen.findByRole("heading", { name: "Account setup wizard" })).toBeInTheDocument();
    await waitForWizard();
    expect(screen.getByRole("button", { name: "Identify customer" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Company profile" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "People & roles" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Integration intent" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Readiness check" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Review & create" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Handoff" })).toBeInTheDocument();
    expect(screen.getByText(/Set up a customer account foundation before campaign and attribution testing/)).toBeInTheDocument();
  });

  it("locks future wizard steps until previous steps are complete", async () => {
    mockedGetAdminOnboardingState.mockResolvedValue(mockAccountSetupStateWithMissingCompanyProfile());

    renderWorkspace(<ReferralSaasAccountSetupPage />);

    await screen.findByRole("heading", { name: "Account setup wizard" });
    await waitForWizard();

    expect(screen.getByRole("button", { name: "Company profile" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "People & roles" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Integration intent" })).toBeDisabled();
    expect(screen.getByText("Not checked")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "People & roles" }));

    expect(screen.getByRole("heading", { name: "Find or start the account" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Company profile" })).not.toHaveClass("done");
    expect(screen.getByRole("button", { name: "Identify customer" })).not.toHaveClass("done");

    await confirmAccountScope();
    expect(screen.getByRole("button", { name: "Company profile" })).toBeEnabled();

    fireEvent.click(screen.getByRole("button", { name: "Continue" }));

    expect(screen.getByRole("heading", { name: "Capture company setup evidence" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Identify customer" })).toHaveClass("done");
    expect(screen.getByRole("button", { name: "Continue" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "People & roles" })).toBeDisabled();
  });

  it("shows a recommended account setup testing path", async () => {
    renderWorkspace(<ReferralSaasAccountSetupPage />);

    expect(await screen.findByRole("heading", { name: "Account setup wizard" })).toBeInTheDocument();
    await waitForWizard();
    expect(screen.getByRole("heading", { name: "Find or start the account" })).toBeInTheDocument();
    await confirmAccountScope();
    fireEvent.click(screen.getByRole("button", { name: "Company profile" }));
    expect(screen.getByText(/Use the existing company onboarding surface/)).toBeInTheDocument();
    expect(lastMatch(screen.getAllByRole("link", { name: /Company profile/ }))).toHaveAttribute(
      "href",
      "/admin/onboarding/company",
    );
    await recordRoleIntent();
    expect(screen.getByRole("button", { name: "Record role intent" })).toBeInTheDocument();
    fireEvent.click(screen.getByText("Integration intent"));
    expect(screen.getByRole("link", { name: /Integration setup/ })).toHaveAttribute(
      "href",
      "/admin/onboarding/webhook-api",
    );
    fireEvent.click(screen.getByRole("button", { name: "Readiness check" }));
    expect(screen.getByRole("button", { name: "Validate setup" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Validate setup" }));
    await screen.findByText("Validation completed without saving.");
    fireEvent.click(screen.getByRole("button", { name: "Review & create" }));
    expect(screen.getByRole("button", { name: "Save setup draft" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Handoff" }));
    expect(lastMatch(screen.getAllByRole("link", { name: /Campaign readiness/ }))).toHaveAttribute(
      "href",
      "/admin/referral-saas/campaigns",
    );
  });

  it("keeps scope typing local until the tester checks setup", async () => {
    renderWorkspace(<ReferralSaasAccountSetupPage />);

    await screen.findByRole("heading", { name: "Account setup wizard" });
    await waitForWizard();
    await waitFor(() => expect(mockedGetAdminOnboardingState).toHaveBeenCalledTimes(1));

    fireEvent.change(screen.getByLabelText("External tenant ref"), {
      target: { value: "org-fnb-referrals" },
    });
    fireEvent.change(screen.getByLabelText("Organisation ref"), {
      target: { value: "fnb-referral-org" },
    });

    expect(screen.getByText("Changes not checked")).toBeInTheDocument();
    expect(mockedGetAdminOnboardingState).toHaveBeenCalledTimes(1);
    expect(mockedGetReferralSaasAccountMembershipPosture).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole("button", { name: "Find account" }));

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
    await waitFor(() =>
      expect(mockedGetReferralSaasAccountMembershipPosture).toHaveBeenLastCalledWith({
        refType: "external_tenant_ref",
        externalRef: "org-fnb-referrals",
        context: "setup",
      }),
    );
    expect(await screen.findByText("Checked")).toBeInTheDocument();
    expect(JSON.stringify(mockedGetAdminOnboardingState.mock.calls)).not.toMatch(
      /account_ref|tenant_code|api_key|client_secret/i,
    );
    await recordRoleIntent();
    await validateSetup();
    fireEvent.click(screen.getByRole("button", { name: "Review & create" }));
    expect(screen.getByRole("button", { name: "Save setup draft" })).toBeEnabled();
  });

  it("keeps first-time setup usable when no durable account exists yet", async () => {
    mockedResolveReferralSaasAccount.mockRejectedValue({
      status: 404,
      message: "External reference was not found.",
    });

    renderWorkspace(<ReferralSaasAccountSetupPage />);

    expect(await screen.findByRole("heading", { name: "Account setup wizard" })).toBeInTheDocument();
    await waitForWizard();
    await confirmAccountScope();
    expect(await screen.findByText("No account exists for these references yet. Start the company setup draft to create one.")).toBeInTheDocument();
    expect(screen.getByText("Start setup")).toBeInTheDocument();
    await validateSetup();
    fireEvent.click(screen.getByRole("button", { name: "Review & create" }));
    expect(screen.getByRole("button", { name: "Save setup draft" })).toBeEnabled();
    expect(screen.queryByText(/tenant_code/i)).not.toBeInTheDocument();
  });

  it("connects setup workflow actions to existing onboarding draft APIs safely", async () => {
    renderWorkspace(<ReferralSaasAccountSetupPage />);

    await screen.findByRole("heading", { name: "Account setup wizard" });
    await waitForWizard();
    await confirmAccountScope();

    await recordRoleIntent();
    fireEvent.click(screen.getByRole("button", { name: "Readiness check" }));
    fireEvent.click(screen.getByRole("button", { name: "Validate setup" }));
    await waitFor(() => expect(mockedValidateAdminOnboardingDryRun).toHaveBeenCalledTimes(1));
    const validationRequest = mockedValidateAdminOnboardingDryRun.mock.calls[0][0];
    expect(validationRequest).toMatchObject({
      external_tenant_ref: "demo-platform-operator",
      organisation_ref: "demo-organisation",
      validation_scope: [
        "company",
        "producer_sponsor",
        "distributor",
        "member_role",
        "campaign_opportunity",
        "webhook_api",
      ],
      correlation_id: "referral-saas-account-setup-validate",
    });
    expect(validationRequest.idempotency_key).toContain("referral-saas-account-setup-validate");
    expect(Object.keys(validationRequest.sections || {})).toEqual([
      "company",
      "producer_sponsor",
      "distributor",
      "member_role",
      "campaign_opportunity",
      "webhook_api",
    ]);
    expect(JSON.stringify(validationRequest).toLowerCase()).not.toMatch(/tenant_code|api_key|client_secret|wallet|settlement|money/);
    expect(await screen.findByText("Validation completed without saving.")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Review & create" }));
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

    await screen.findByRole("heading", { name: "Account setup wizard" });
    await waitForWizard();
    await confirmAccountScope();
    expect(await screen.findByText(/No account exists for these references yet/)).toBeInTheDocument();
    await validateSetup();
    fireEvent.click(screen.getByRole("button", { name: "Review & create" }));
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
    fireEvent.click(screen.getByRole("button", { name: "People & roles" }));
    expect(screen.getByRole("button", { name: "Record role intent" })).toBeInTheDocument();
  });

  it("records users and roles invitation intent from Step 2 after durable account resolution", async () => {
    renderWorkspace(<ReferralSaasAccountSetupPage />);

    await screen.findByRole("heading", { name: "Account setup wizard" });
    await waitForWizard();
    await confirmAccountScope();
    await waitFor(() => expect(mockedResolveReferralSaasAccount).toHaveBeenCalledTimes(1));
    fireEvent.click(screen.getByText("People & roles"));

    fireEvent.change(screen.getByLabelText("User subject"), {
      target: { value: "fnb-setup-owner-subject" },
    });
    fireEvent.change(screen.getByLabelText("Display name"), {
      target: { value: "FNB setup owner" },
    });
    fireEvent.change(screen.getByLabelText("Email hash"), {
      target: { value: "hash_fnb_setup_owner" },
    });
    fireEvent.change(screen.getByLabelText("Role family"), {
      target: { value: "DISTRIBUTION_ADMIN" },
    });
    fireEvent.change(screen.getByLabelText("Permission set"), {
      target: { value: "REFERRAL_SAAS_ACCOUNT_ADMIN" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Record role intent" }));

    await waitFor(() => expect(mockedRecordReferralSaasMembershipInvitationIntent).toHaveBeenCalledTimes(1));
    expect(mockedRecordReferralSaasMembershipInvitationIntent).toHaveBeenCalledWith({
      accountRef: "acc_fnb",
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: "demo-platform-operator",
        context: "setup",
      },
      actor: {
        actorType: "USER",
        subject: "fnb-setup-owner-subject",
        emailHash: "hash_fnb_setup_owner",
        displayName: "FNB setup owner",
      },
      membership: {
        roleFamily: "DISTRIBUTION_ADMIN",
        permissionSet: "REFERRAL_SAAS_ACCOUNT_ADMIN",
        tenantScope: "PRIMARY_ACCOUNT_TENANT",
      },
      reasonCode: "ACCOUNT_SETUP_USER_ROLE",
      correlationId: "referral-saas-account-setup-membership-invitation",
      idempotencyKey: "referral-saas-account-setup-membership-invitation:acc_fnb:fnb-setup-owner-subject:DISTRIBUTION_ADMIN",
    });
    expect(JSON.stringify(mockedRecordReferralSaasMembershipInvitationIntent.mock.calls).toLowerCase()).not.toMatch(
      /tenant_code|client_secret|wallet|settlement|money_movement|send_invite|activate/,
    );
    expect(await screen.findByText("Role intent recorded.")).toBeInTheDocument();
    expect(screen.getByText(/DELIVERY_NOT_CONFIGURED/)).toBeInTheDocument();
    expect(screen.getByText(/No active access, seat, auth claim, campaign, go-live, or money action was taken/)).toBeInTheDocument();
  });

  it("keeps account creation and bounded membership intent as visible guardrails", async () => {
    renderWorkspace(<ReferralSaasAccountSetupPage />);

    await screen.findByRole("heading", { name: "Account setup wizard" });
    await waitForWizard();
    await confirmAccountScope();
    expect(screen.getByText("Safe mode: no go-live / money / credentials")).toBeInTheDocument();
    await recordRoleIntent();
    await validateSetup();
    fireEvent.click(screen.getByRole("button", { name: "Review & create" }));
    expect(screen.getByRole("button", { name: "Create account foundation" })).toBeInTheDocument();
    expect(screen.getByText(/No users, campaigns, go-live, or money/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Create account foundation" })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "People & roles" }));
    expect(screen.getByText(/it does not send email or activate login/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Record role intent" })).toBeEnabled();
  });

  it("links to existing setup surfaces without forking source workflows", async () => {
    renderWorkspace(<ReferralSaasAccountSetupPage />);

    await screen.findByRole("heading", { name: "Account setup wizard" });
    await waitForWizard();
    await confirmAccountScope();
    fireEvent.click(screen.getByRole("button", { name: "Company profile" }));
    expect(lastMatch(screen.getAllByRole("link", { name: /Company profile/ }))).toHaveAttribute(
      "href",
      "/admin/onboarding/company",
    );
    await recordRoleIntent();
    fireEvent.click(screen.getByRole("button", { name: "Integration intent" }));
    expect(lastMatch(screen.getAllByRole("link", { name: /Integration setup/ }))).toHaveAttribute(
      "href",
      "/admin/onboarding/webhook-api",
    );
    await validateSetup();
    fireEvent.click(screen.getByRole("button", { name: "Review & create" }));
    fireEvent.click(screen.getByRole("button", { name: "Handoff" }));
    expect(lastMatch(screen.getAllByRole("link", { name: /Campaign readiness/ }))).toHaveAttribute(
      "href",
      "/admin/referral-saas/campaigns",
    );
  });
});
