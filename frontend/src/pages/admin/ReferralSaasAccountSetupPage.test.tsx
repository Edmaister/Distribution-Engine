import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactElement } from "react";
import { createMemoryRouter, Outlet, RouterProvider } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  getAdminOnboardingDrafts,
  getAdminOnboardingState,
  recordAdminOnboardingReviewDecision,
  saveAdminOnboardingDraft,
  submitAdminOnboardingDraftForReview,
  validateAdminOnboardingDryRun,
  type AdminOnboardingStateResponse,
} from "../../api/endpoints/adminOnboarding";
import {
  createReferralSaasAccountFromDraft,
  resolveReferralSaasAccount,
} from "../../api/endpoints/referralSaasAccounts";
import { ReferralSaasAccountSetupPage } from "./ReferralSaasAccountSetupPage";

vi.mock("../../api/endpoints/adminOnboarding", () => ({
  getAdminOnboardingDrafts: vi.fn(),
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

const mockedGetAdminOnboardingDrafts = vi.mocked(getAdminOnboardingDrafts);
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

function mockDraftSelectorResponse() {
  return {
    status: "ok",
    count: 1,
    guardrails: ["READ_ONLY_DRAFT_SELECTOR", "NO_LIVE_ACTION"],
    redactions: ["internal_identifier"],
    items: [
      {
        draft_ref: "draft_saved_company_profile",
        draft_version: 4,
        draft_status: "DRAFT_CREATED",
        external_tenant_ref: "demo-platform-operator",
        organisation_ref: "demo-organisation",
        readiness_status: "GO_LIVE_DISABLED",
        validation_status: "VALID",
        missing_evidence_count: 1,
        blocker_count: 0,
        updated_at: "2026-07-19T06:00:00Z",
        redactions: ["internal_identifier"],
        draft_sections: {
          company: {
            organisation_name: "Saved Referral Company",
            external_tenant_ref: "demo-platform-operator",
            organisation_ref: "demo-organisation",
            country: "South Africa",
            organisation_type: "Enterprise customer",
            industry: "Automotive",
            admin_contact: "saved-admin@example.test",
            intended_role: "Implementation lead",
          },
        },
      },
    ],
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
    guardrails: ["DURABLE_ACCOUNT_FOUNDATION_ONLY", "BOUNDED_INTERNAL_TENANT_SEED", "NO_MONEY_MOVEMENT"],
    redactions: ["internal_tenant_identifier"],
    noAdjacentLiveActionConfirmed: true,
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

const testCustomerReference = "demo-platform-operator";
const testOrganisationReference = "demo-organisation";

async function confirmAccountScope() {
  const customerReference = screen.getByPlaceholderText("Example: fnb-sa-referrals");
  const organisationReference = screen.getByPlaceholderText("Example: fnb-retail-bank");
  if (!(customerReference as HTMLInputElement).value) {
    fireEvent.change(customerReference, { target: { value: testCustomerReference } });
  }
  if (!(organisationReference as HTMLInputElement).value) {
    fireEvent.change(organisationReference, { target: { value: testOrganisationReference } });
  }
  const findAccountButton = screen.getByRole("button", { name: "Find account" });
  await waitFor(() => expect(findAccountButton).toBeEnabled());
  fireEvent.click(findAccountButton);
  await screen.findByText("Checked");
}

async function validateSetup() {
  fireEvent.click(screen.getByRole("button", { name: "Setup checkpoint" }));
  fireEvent.click(screen.getByRole("button", { name: "Refresh setup checkpoint" }));
  await screen.findByText("Checkpoint refreshed");
}

function fillRequiredCompanyProfile() {
  fireEvent.change(screen.getByLabelText("Organisation name"), {
    target: { value: "FNB Referral Programme" },
  });
  fireEvent.change(screen.getByLabelText("Admin contact"), {
    target: { value: "referrals-admin@example.test" },
  });
}

describe("ReferralSaasAccountSetupPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedGetAdminOnboardingDrafts.mockResolvedValue({
      status: "ok",
      items: [],
      count: 0,
      guardrails: ["READ_ONLY_DRAFT_SELECTOR"],
      redactions: ["internal_identifier"],
    });
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

    expect(await screen.findByRole("heading", { name: "Account setup wizard" })).toBeInTheDocument();
    await waitForWizard();
    expect(screen.getByPlaceholderText("Example: fnb-sa-referrals")).toHaveValue("");
    expect(screen.getByPlaceholderText("Example: fnb-retail-bank")).toHaveValue("");
    expect(screen.getByRole("button", { name: "Find account" })).toBeDisabled();
    expect(mockedGetAdminOnboardingState).not.toHaveBeenCalled();
    expect(mockedResolveReferralSaasAccount).not.toHaveBeenCalled();
    await confirmAccountScope();
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
    expect(screen.getByText("Safe mode: no go-live / money / credentials")).toBeInTheDocument();
    expect(screen.getByText("Account status")).toBeInTheDocument();
    expect(screen.getByText("FNB Referral SaaS - ACTIVE - tenant link ACTIVE")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Integration intent" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "People & roles" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Record role intent" })).not.toBeInTheDocument();
    expect(screen.queryByText(/tenant_code/i)).not.toBeInTheDocument();
  });

  it("explains the screen purpose, actions, and next step", async () => {
    renderWorkspace(<ReferralSaasAccountSetupPage />);

    expect(await screen.findByRole("heading", { name: "Account setup wizard" })).toBeInTheDocument();
    await waitForWizard();
    expect(screen.getByRole("button", { name: "Identify customer" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Company profile" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Integration intent" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Setup checkpoint" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Review & create" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Handoff" })).not.toBeInTheDocument();
    expect(screen.getByText(/Set up a customer account foundation before campaign and attribution testing/)).toBeInTheDocument();
    expect(screen.getByText(/Technical integration setup is handled after the account foundation is ready/)).toBeInTheDocument();
  });

  it("locks future wizard steps until previous steps are complete", async () => {
    mockedGetAdminOnboardingState.mockResolvedValue(mockAccountSetupStateWithMissingCompanyProfile());

    renderWorkspace(<ReferralSaasAccountSetupPage />);

    await screen.findByRole("heading", { name: "Account setup wizard" });
    await waitForWizard();

    expect(screen.getByRole("button", { name: "Company profile" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Setup checkpoint" })).toBeDisabled();
    expect(screen.getByText("Not checked")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Setup checkpoint" }));

    expect(screen.getByRole("heading", { name: "Find or start the account" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Company profile" })).not.toHaveClass("done");
    expect(screen.getByRole("button", { name: "Identify customer" })).not.toHaveClass("done");

    await confirmAccountScope();
    expect(screen.getByRole("button", { name: "Company profile" })).toBeEnabled();

    fireEvent.click(screen.getByRole("button", { name: "Continue" }));

    expect(screen.getByRole("heading", { name: "Capture company setup evidence" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Identify customer" })).toHaveClass("done");
    expect(screen.getByRole("button", { name: "Continue" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Setup checkpoint" })).toBeDisabled();
  });

  it("shows a recommended account setup testing path", async () => {
    renderWorkspace(<ReferralSaasAccountSetupPage />);

    expect(await screen.findByRole("heading", { name: "Account setup wizard" })).toBeInTheDocument();
    await waitForWizard();
    expect(screen.getByRole("heading", { name: "Find or start the account" })).toBeInTheDocument();
    await confirmAccountScope();
    fireEvent.click(screen.getByRole("button", { name: "Company profile" }));
    expect(screen.getByText(/Capture the company evidence inside this wizard/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Save company profile" })).toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: "Operating jurisdiction" })).toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: /Customer type/ })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Agency / implementation partner" })).toBeInTheDocument();
    expect(screen.queryByRole("option", { name: "Referral Management SaaS" })).not.toBeInTheDocument();
    expect(screen.queryByRole("option", { name: "RMCAaaS Enterprise" })).not.toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: "Industry" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Automotive" })).toBeInTheDocument();
    expect(screen.queryByRole("option", { name: "Referral management and campaign attribution" })).not.toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: /Contact responsibility/ })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Implementation lead" })).toBeInTheDocument();
    expect(screen.queryByRole("option", { name: "Referral SaaS account admin" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Product package and billing plan are configured separately/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Users, access roles, and permissions are managed later in Account Maintenance/ })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /Company profile/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "People & roles" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Record role intent" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Integration intent" })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Setup checkpoint" }));
    expect(screen.getByRole("button", { name: "Refresh setup checkpoint" })).toBeInTheDocument();
    expect(screen.getByText("Account foundation already exists")).toBeInTheDocument();
    expect(lastMatch(screen.getAllByRole("link", { name: /Account Maintenance readiness/ }))).toHaveAttribute(
      "href",
      "/admin/referral-saas/account-maintenance",
    );
    fireEvent.click(screen.getByRole("button", { name: "Refresh setup checkpoint" }));
    await screen.findByText("Checkpoint refreshed");
    fireEvent.click(screen.getByRole("button", { name: "Review & create" }));
    expect(screen.getByRole("button", { name: "Save and finish later" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Handoff" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /Configure technical integration/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /Start campaign setup/ })).not.toBeInTheDocument();
  });

  it("keeps Company Profile setup inside the wizard and saves profile evidence", async () => {
    renderWorkspace(<ReferralSaasAccountSetupPage />);

    await screen.findByRole("heading", { name: "Account setup wizard" });
    await waitForWizard();
    await confirmAccountScope();
    fireEvent.click(screen.getByRole("button", { name: "Company profile" }));

    fireEvent.change(screen.getByLabelText("Organisation name"), {
      target: { value: "FNB Referral Programme" },
    });
    fireEvent.change(screen.getByRole("combobox", { name: "Operating jurisdiction" }), {
      target: { value: "South Africa" },
    });
    fireEvent.change(screen.getByRole("combobox", { name: "Industry" }), {
      target: { value: "Automotive" },
    });
    fireEvent.change(screen.getByLabelText("Admin contact"), {
      target: { value: "referrals-admin@example.test" },
    });
    fireEvent.change(screen.getByRole("combobox", { name: /Contact responsibility/ }), {
      target: { value: "Campaign manager" },
    });

    expect(screen.queryByRole("link", { name: /Company profile/ })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Save company profile" }));

    await waitFor(() => expect(mockedSaveAdminOnboardingDraft).toHaveBeenCalledTimes(1));
    const draftRequest = mockedSaveAdminOnboardingDraft.mock.calls[0][0];
    expect(draftRequest).toMatchObject({
      external_tenant_ref: "demo-platform-operator",
      organisation_ref: "demo-organisation",
      correlation_id: "referral-saas-account-setup-draft",
      sections: {
        company: {
          organisation_name: "FNB Referral Programme",
          external_tenant_ref: "demo-platform-operator",
          organisation_ref: "demo-organisation",
          country: "South Africa",
          organisation_type: "Direct customer",
          industry: "Automotive",
          admin_contact: "referrals-admin@example.test",
          intended_role: "Campaign manager",
        },
      },
    });
    expect(JSON.stringify(draftRequest).toLowerCase()).not.toMatch(/tenant_code|api_key|client_secret|wallet|settlement|money/);
    expect(await screen.findByText(/Company profile saved/)).toBeInTheDocument();
    expect(screen.queryByText("Setup draft saved.")).not.toBeInTheDocument();
    expect(screen.getAllByText("Draft saved").length).toBeGreaterThan(0);
  });

  it("loads saved company profile draft evidence and blocks continuing after unsaved edits", async () => {
    mockedGetAdminOnboardingState.mockResolvedValue(mockAccountSetupStateWithMissingCompanyProfile());
    mockedGetAdminOnboardingDrafts.mockResolvedValue(mockDraftSelectorResponse());

    renderWorkspace(<ReferralSaasAccountSetupPage />);

    await screen.findByRole("heading", { name: "Account setup wizard" });
    await waitForWizard();
    await confirmAccountScope();
    fireEvent.click(screen.getByRole("button", { name: "Company profile" }));

    expect(await screen.findByDisplayValue("Saved Referral Company")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Automotive")).toBeInTheDocument();
    expect(screen.getByDisplayValue("saved-admin@example.test")).toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: /Contact responsibility/ })).toHaveValue("Implementation lead");
    expect(screen.getByText(/Company profile saved/)).toBeInTheDocument();
    expect(screen.getByText(/Saved profile evidence - version 4 - updated 2026-07-19T06:00:00Z/)).toBeInTheDocument();
    expect(screen.queryByText(/draft_saved_company_profile/)).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Continue" })).toBeEnabled();

    fireEvent.change(screen.getByLabelText("Organisation name"), {
      target: { value: "Saved Referral Company Updated" },
    });

    expect(screen.getByText(/You changed the company profile after the last saved draft/)).toBeInTheDocument();
    expect(screen.getAllByText("Unsaved changes").length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "Continue" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Save company changes" })).toBeEnabled();
  });

  it("shows actionable recovery when company profile save hits an existing draft conflict", async () => {
    mockedSaveAdminOnboardingDraft.mockRejectedValueOnce({
      status: 409,
      message: "Conflict",
    });

    renderWorkspace(<ReferralSaasAccountSetupPage />);

    await screen.findByRole("heading", { name: "Account setup wizard" });
    await waitForWizard();
    await confirmAccountScope();

    fireEvent.click(screen.getByRole("button", { name: "Company profile" }));
    fillRequiredCompanyProfile();
    fireEvent.click(screen.getByRole("button", { name: "Save company profile" }));

    expect(await screen.findByText("Existing setup draft found.")).toBeInTheDocument();
    expect(screen.getByText(/A saved setup already exists for this customer/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Refresh setup status" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Use different customer identifiers" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Change customer references" })).not.toBeInTheDocument();
    expect(screen.queryByText("Setup action fallback.")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Refresh setup status" }));
    await waitFor(() => expect(mockedGetAdminOnboardingState).toHaveBeenCalledTimes(2));
    expect(screen.queryByText("Existing setup draft found.")).not.toBeInTheDocument();
  });

  it("keeps scope typing local until the tester checks setup", async () => {
    renderWorkspace(<ReferralSaasAccountSetupPage />);

    await screen.findByRole("heading", { name: "Account setup wizard" });
    await waitForWizard();
    expect(mockedGetAdminOnboardingState).not.toHaveBeenCalled();
    expect(mockedResolveReferralSaasAccount).not.toHaveBeenCalled();

    fireEvent.change(screen.getByPlaceholderText("Example: fnb-sa-referrals"), {
      target: { value: "org-fnb-referrals" },
    });
    fireEvent.change(screen.getByPlaceholderText("Example: fnb-retail-bank"), {
      target: { value: "fnb-referral-org" },
    });

    expect(screen.getByText("Changes not checked")).toBeInTheDocument();
    expect(mockedGetAdminOnboardingState).not.toHaveBeenCalled();

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
    expect(await screen.findByText("Checked")).toBeInTheDocument();
    expect(JSON.stringify(mockedGetAdminOnboardingState.mock.calls)).not.toMatch(
      /account_ref|tenant_code|api_key|client_secret/i,
    );
    await validateSetup();
    fireEvent.click(screen.getByRole("button", { name: "Review & create" }));
    expect(screen.getByRole("button", { name: "Save and finish later" })).toBeEnabled();
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
    expect(await screen.findByText("No account exists for these customer identifiers yet. Start the company setup draft to create one.")).toBeInTheDocument();
    expect(screen.getByText("Start setup")).toBeInTheDocument();
    await validateSetup();
    fireEvent.click(screen.getByRole("button", { name: "Review & create" }));
    expect(screen.getByRole("button", { name: "Save and finish later" })).toBeEnabled();
    expect(screen.queryByText(/tenant_code/i)).not.toBeInTheDocument();
  });

  it("connects the single create action to existing onboarding draft APIs safely", async () => {
    mockedResolveReferralSaasAccount.mockRejectedValue({
      status: 404,
      message: "External reference was not found.",
    });

    renderWorkspace(<ReferralSaasAccountSetupPage />);

    await screen.findByRole("heading", { name: "Account setup wizard" });
    await waitForWizard();
    await confirmAccountScope();
    fireEvent.click(screen.getByRole("button", { name: "Company profile" }));
    fillRequiredCompanyProfile();

    fireEvent.click(screen.getByRole("button", { name: "Setup checkpoint" }));
    fireEvent.click(screen.getByRole("button", { name: "Refresh setup checkpoint" }));
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
    expect(await screen.findByText("Checkpoint refreshed")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Review & create" }));
    expect(screen.queryByRole("button", { name: "Submit for review" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Accept internal review" })).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Review reason")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Create account foundation" }));

    await waitFor(() => expect(mockedSaveAdminOnboardingDraft).toHaveBeenCalledTimes(1));
    const draftRequest = mockedSaveAdminOnboardingDraft.mock.calls[0][0];
    expect(draftRequest).toMatchObject({
      external_tenant_ref: "demo-platform-operator",
      organisation_ref: "demo-organisation",
      correlation_id: "referral-saas-account-setup-draft",
    });
    expect(draftRequest.idempotency_key).toContain("referral-saas-account-setup-draft");
    expect(JSON.stringify(draftRequest).toLowerCase()).not.toMatch(/tenant_code|api_key|client_secret|wallet|settlement|money/);
    expect(screen.queryByText("Setup draft saved.")).not.toBeInTheDocument();

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
    expect(screen.queryByText("Setup draft submitted for review.")).not.toBeInTheDocument();

    await waitFor(() => expect(mockedRecordAdminOnboardingReviewDecision).toHaveBeenCalledTimes(1));
    const [reviewDraftRef, reviewRequest] = mockedRecordAdminOnboardingReviewDecision.mock.calls[0];
    expect(reviewDraftRef).toBe("draft_referral_saas_setup");
    expect(reviewRequest).toMatchObject({
      external_tenant_ref: "demo-platform-operator",
      organisation_ref: "demo-organisation",
      expected_version: 2,
      review_outcome: "APPROVED_FOR_INTERNAL_REVIEW",
      reason_category: "OPERATOR_REVIEW",
      reason: "Account setup reviewed through the guided Referral SaaS account setup flow.",
      correlation_id: "referral-saas-account-setup-review-decision",
    });
    expect(reviewRequest.idempotency_key).toContain("referral-saas-account-setup-review");
    expect(JSON.stringify(reviewRequest).toLowerCase()).not.toMatch(/tenant_code|api_key|client_secret|wallet|settlement|money/);
    expect(await screen.findByText("Safe setup review completed.")).toBeInTheDocument();
    expect(screen.queryByText("Internal review decision recorded.")).not.toBeInTheDocument();
    expect(screen.queryByText(/go-live: disabled/)).not.toBeInTheDocument();
    await waitFor(() => expect(mockedCreateReferralSaasAccountFromDraft).toHaveBeenCalledTimes(1));
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
    expect(await screen.findByText(/No account exists for these customer identifiers yet/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Company profile" }));
    fillRequiredCompanyProfile();
    await validateSetup();
    fireEvent.click(screen.getByRole("button", { name: "Review & create" }));
    const createButton = screen.getByRole("button", { name: "Create account foundation" });
    await waitFor(() => expect(createButton).toBeEnabled());
    fireEvent.click(createButton);

    await waitFor(() => expect(mockedCreateReferralSaasAccountFromDraft).toHaveBeenCalledTimes(1));
    expect(mockedCreateReferralSaasAccountFromDraft).toHaveBeenCalledWith({
      draftRef: "draft_referral_saas_setup",
      internalTenantCode: "RS_DEMO_PLATFORM_OPERATOR_DEMO__1EVY6SE",
      idempotencyKey: "referral-saas-account-setup-create:draft_referral_saas_setup",
    });
    expect(JSON.stringify(mockedCreateReferralSaasAccountFromDraft.mock.calls).toLowerCase()).not.toMatch(
      /client_secret|wallet|settlement|money_movement|go_live_enabled/,
    );
    expect(await screen.findByText("Account foundation created.")).toBeInTheDocument();
    expect(screen.getByText(/Account Setup is complete/)).toBeInTheDocument();
    expect(lastMatch(screen.getAllByRole("link", { name: /Open customer profile/ }))).toHaveAttribute(
      "href",
      "/admin/referral-saas/account-maintenance/acc_created",
    );
    expect(lastMatch(screen.getAllByRole("link", { name: /Manage access/ }))).toHaveAttribute(
      "href",
      "/admin/referral-saas/account-maintenance",
    );
    expect(lastMatch(screen.getAllByRole("link", { name: /Configure technical integration/ }))).toHaveAttribute(
      "href",
      "/admin/onboarding/webhook-api",
    );
    expect(lastMatch(screen.getAllByRole("link", { name: /Start campaign setup/ }))).toHaveAttribute(
      "href",
      "/admin/referral-saas/campaigns",
    );
  });

  it("explains internal setup scope conflicts without claiming the customer already exists", async () => {
    mockedResolveReferralSaasAccount.mockRejectedValue({
      status: 404,
      message: "External reference was not found.",
    });
    mockedCreateReferralSaasAccountFromDraft.mockRejectedValueOnce({
      status: 409,
      detail: { code: "DUPLICATE_INTERNAL_TENANT_SCOPE" },
    });

    renderWorkspace(<ReferralSaasAccountSetupPage />);

    await screen.findByRole("heading", { name: "Account setup wizard" });
    await waitForWizard();
    await confirmAccountScope();
    fireEvent.click(screen.getByRole("button", { name: "Company profile" }));
    fillRequiredCompanyProfile();
    await validateSetup();
    fireEvent.click(screen.getByRole("button", { name: "Review & create" }));
    fireEvent.click(screen.getByRole("button", { name: "Create account foundation" }));

    expect(await screen.findByText("Setup workspace already used.")).toBeInTheDocument();
    expect(screen.getByText(/setup workspace for this customer is already attached/)).toBeInTheDocument();
    expect(screen.queryByText("Account foundation already exists.")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Refresh setup status" })).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Use different customer identifiers" })).not.toHaveLength(0);
  });

  it("keeps user access writes out of Account Setup", async () => {
    renderWorkspace(<ReferralSaasAccountSetupPage />);

    await screen.findByRole("heading", { name: "Account setup wizard" });
    await waitForWizard();
    await confirmAccountScope();
    expect(screen.queryByRole("button", { name: "People & roles" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Record role intent" })).not.toBeInTheDocument();
    expect(screen.queryByLabelText("User subject")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Permission set")).not.toBeInTheDocument();
  });

  it("keeps account creation guardrails and routes access work to maintenance", async () => {
    renderWorkspace(<ReferralSaasAccountSetupPage />);

    await screen.findByRole("heading", { name: "Account setup wizard" });
    await waitForWizard();
    await confirmAccountScope();
    expect(screen.getByText("Safe mode: no go-live / money / credentials")).toBeInTheDocument();
    await validateSetup();
    fireEvent.click(screen.getByRole("button", { name: "Review & create" }));
    expect(screen.getByRole("button", { name: "Create account foundation" })).toBeInTheDocument();
    expect(screen.getByText(/does not create users, send invites, create campaigns, enable go-live, create credentials, bill, settle, or move money/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Submit for review" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Accept internal review" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "People & roles" })).not.toBeInTheDocument();
  });

  it("links to existing setup surfaces without forking source workflows", async () => {
    mockedResolveReferralSaasAccount.mockRejectedValue({
      status: 404,
      message: "External reference was not found.",
    });

    renderWorkspace(<ReferralSaasAccountSetupPage />);

    await screen.findByRole("heading", { name: "Account setup wizard" });
    await waitForWizard();
    await confirmAccountScope();
    fireEvent.click(screen.getByRole("button", { name: "Company profile" }));
    fillRequiredCompanyProfile();
    expect(screen.getByRole("button", { name: "Save company profile" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /Company profile/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Integration intent" })).not.toBeInTheDocument();
    await validateSetup();
    fireEvent.click(screen.getByRole("button", { name: "Review & create" }));
    fireEvent.click(screen.getByRole("button", { name: "Create account foundation" }));
    expect(await screen.findByText("Account foundation created.")).toBeInTheDocument();
    expect(lastMatch(screen.getAllByRole("link", { name: /Configure technical integration/ }))).toHaveAttribute(
      "href",
      "/admin/onboarding/webhook-api",
    );
    expect(lastMatch(screen.getAllByRole("link", { name: /Start campaign setup/ }))).toHaveAttribute(
      "href",
      "/admin/referral-saas/campaigns",
    );
  });
});
