import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import type { ReactElement } from "react";
import { createMemoryRouter, Outlet, RouterProvider } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  getAdminOnboardingState,
  recordAdminOnboardingReviewDecision,
  saveAdminOnboardingDraft,
  submitAdminOnboardingDraftForReview,
  validateAdminOnboardingDryRun,
  type AdminOnboardingDraftSaveResponse,
  type AdminOnboardingDryRunValidationResponse,
  type AdminOnboardingReviewDecisionResponse,
  type AdminOnboardingStateResponse,
  type AdminOnboardingSubmitForReviewResponse,
} from "../../api/endpoints/adminOnboarding";
import { createAdminOnboardingStateResponse } from "../../api/endpoints/adminOnboarding.testFixtures";
import { CompanyOnboardingPage } from "./CompanyOnboardingPage";

vi.mock("../../api/endpoints/adminOnboarding", () => ({
  getAdminOnboardingState: vi.fn(),
  recordAdminOnboardingReviewDecision: vi.fn(),
  saveAdminOnboardingDraft: vi.fn(),
  submitAdminOnboardingDraftForReview: vi.fn(),
  validateAdminOnboardingDryRun: vi.fn(),
}));

const mockedGetAdminOnboardingState = vi.mocked(getAdminOnboardingState);
const mockedRecordAdminOnboardingReviewDecision = vi.mocked(
  recordAdminOnboardingReviewDecision,
);
const mockedSaveAdminOnboardingDraft = vi.mocked(saveAdminOnboardingDraft);
const mockedSubmitAdminOnboardingDraftForReview = vi.mocked(
  submitAdminOnboardingDraftForReview,
);
const mockedValidateAdminOnboardingDryRun = vi.mocked(
  validateAdminOnboardingDryRun,
);

const draftSaveResponse: AdminOnboardingDraftSaveResponse = {
  status: "saved",
  draft_ref: "draft_acme_distribution",
  draft_status: "DRAFT_CREATED",
  draft_version: 1,
  idempotency_status: "NEW_REQUEST",
  validation_summary: {
    status: "WARNING",
    safe_error_count: 0,
    missing_evidence_count: 1,
    blocker_count: 0,
  },
  missing_evidence: [
    {
      section: "company",
      field: "industry",
      code: "MISSING_EVIDENCE",
      message: "Industry evidence is not complete.",
      severity: "warning",
    },
  ],
  blockers: [],
  next_actions: ["Review company draft evidence before go-live review."],
  guardrails: ["NO_LIVE_ACTIONS", "NO_MONEY_MOVEMENT"],
  redactions: ["TENANT_CODE_INTERNAL", "SECRETS_REDACTED"],
  no_live_action_confirmed: true,
};

const submitForReviewResponse: AdminOnboardingSubmitForReviewResponse = {
  status: "submitted_for_review",
  draft_ref: "draft_acme_distribution",
  draft_status: "READY_FOR_REVIEW",
  draft_version: 2,
  idempotency_status: "NEW_REQUEST",
  validation_summary: {
    status: "READY",
    safe_error_count: 0,
    missing_evidence_count: 0,
    blocker_count: 0,
  },
  readiness_summary: {
    overall_status: "READY_FOR_REVIEW",
    ready_count: 1,
    blocked_count: 0,
    missing_evidence_count: 0,
    go_live_disabled_count: 1,
    total_count: 1,
    go_live_enabled: false,
  },
  missing_evidence: [],
  blockers: [],
  next_actions: ["Review submitted draft evidence before any later approval."],
  guardrails: ["SUBMIT_FOR_REVIEW_ONLY", "NO_VALUE_TRANSFER"],
  redactions: ["internal_identifier"],
  audit_evidence_ref: null,
  audit_link_ref: null,
  audit_evidence_status: "NOT_RECORDED_IN_TASK_116",
  no_live_action_confirmed: true,
};

const reviewDecisionResponse: AdminOnboardingReviewDecisionResponse = {
  status: "review_decision_recorded",
  draft_ref: "draft_acme_distribution",
  previous_status: "READY_FOR_REVIEW",
  draft_status: "READY_FOR_REVIEW",
  draft_version: 3,
  review_outcome: "APPROVED_FOR_INTERNAL_REVIEW",
  reason_category: "OPERATOR_REVIEW",
  idempotency_status: "NEW_REQUEST",
  validation_summary: {
    status: "READY",
    safe_error_count: 0,
    missing_evidence_count: 0,
    blocker_count: 0,
  },
  readiness_summary: {
    overall_status: "READY_FOR_REVIEW",
    ready_count: 1,
    blocked_count: 0,
    missing_evidence_count: 0,
    go_live_disabled_count: 1,
    total_count: 1,
    go_live_enabled: false,
  },
  missing_evidence: [],
  blockers: [],
  next_actions: [],
  guardrails: [
    "REVIEW_DECISION_ONLY",
    "NO_APPROVAL_TO_LAUNCH",
    "NO_WEBHOOK_DISPATCH",
    "NO_VALUE_TRANSFER",
  ],
  redactions: ["internal_identifier"],
  audit_evidence_ref: "REVIEW_DECISION_AUDIT_EVIDENCE",
  audit_link_ref: "audit-link-uuid",
  audit_evidence_status: "RECORDED_REFERENCE",
  approval_to_launch: false,
  go_live_enabled: false,
  no_live_action_confirmed: true,
};

const dryRunValidationResponse: AdminOnboardingDryRunValidationResponse = {
  status: "ok",
  validation_result: {
    status: "MISSING_EVIDENCE",
    validated_scope: {
      external_tenant_ref: "acme-distribution",
      organisation_ref: "org-acme",
    },
    validated_sections: ["company"],
    checks: [],
  },
  readiness_preview: {
    contract_version: "onboarding.v1",
    overall_status: "GO_LIVE_DISABLED",
    categories: [
      {
        category: "company",
        display_label: "Company profile",
        status: "MISSING_EVIDENCE",
        safe_display_status: {
          status: "NEEDS_ATTENTION",
          label: "Needs evidence",
          action_required: true,
          go_live_enabled: false,
        },
        evidence_summary: "Company profile needs one more evidence check.",
        blockers: ["Missing industry evidence"],
        next_actions: ["Review company profile before go-live review."],
      },
    ],
    summary: {
      ready_count: 0,
      in_progress_count: 0,
      blocked_count: 0,
      missing_evidence_count: 1,
      permission_limited_count: 0,
      go_live_disabled_count: 1,
      total_count: 1,
    },
    guardrails: ["NO_LIVE_MUTATION"],
    missing_evidence: [],
    source_warnings: [],
    redactions: ["TENANT_CODE_INTERNAL"],
  },
  missing_evidence: [
    {
      section: "company",
      field: "industry",
      code: "MISSING_EVIDENCE",
      message: "Industry evidence is not complete.",
      severity: "warning",
    },
  ],
  blockers: [
    {
      section: "company",
      field: "industry",
      code: "READINESS_BLOCKED",
      message: "Company profile cannot move to review yet.",
      severity: "BLOCKER",
    },
  ],
  warnings: [
    {
      section: "readiness",
      field: null,
      code: "GO_LIVE_DISABLED",
      message: "Dry-run validation cannot enable go-live.",
      severity: "info",
    },
  ],
  safe_errors: [],
  next_actions: ["Review company profile before go-live review."],
  guardrails: ["DRY_RUN_ONLY", "NO_PERSISTENCE", "NO_LIVE_MUTATION"],
  redactions: ["TENANT_CODE_INTERNAL"],
  no_persistence_confirmed: true,
  no_live_action_confirmed: true,
};

function onboardingStateResponse(
  overrides: Partial<AdminOnboardingStateResponse["readiness"]> = {},
): AdminOnboardingStateResponse {
  return createAdminOnboardingStateResponse({
    overall_status: "GO_LIVE_DISABLED",
    categories: [
      {
        category: "ORGANISATION_PROFILE",
        display_label: "Organisation profile",
        status: "MISSING_EVIDENCE",
        safe_display_status: {
          status: "MISSING_EVIDENCE",
          label: "Missing evidence",
          action_required: true,
          go_live_enabled: false,
        },
        evidence_summary: "Organisation evidence is partially available.",
        blockers: ["Company onboarding remains shell-only."],
        next_actions: ["Confirm external references before go-live review."],
      },
    ],
    summary: {
      ready_count: 0,
      in_progress_count: 0,
      blocked_count: 0,
      missing_evidence_count: 1,
      permission_limited_count: 0,
      go_live_disabled_count: 1,
      total_count: 1,
    },
    ...overrides,
  });
}

function renderWorkspace(ui: ReactElement) {
  const router = createMemoryRouter([
    {
      path: "/",
      element: <Outlet context={{ refreshKey: 0 }} />,
      children: [{ index: true, element: ui }],
    },
  ]);

  return render(<RouterProvider router={router} />);
}

function readinessPanel() {
  const heading = screen.getByRole("heading", { name: "Setup readiness" });
  const panel = heading.closest(".panel");
  if (!panel) {
    throw new Error("Setup readiness panel was not rendered");
  }
  return within(panel as HTMLElement);
}

describe("CompanyOnboardingPage", () => {
  beforeEach(() => {
    mockedGetAdminOnboardingState.mockResolvedValue(onboardingStateResponse());
    mockedSaveAdminOnboardingDraft.mockResolvedValue(draftSaveResponse);
    mockedRecordAdminOnboardingReviewDecision.mockResolvedValue(
      reviewDecisionResponse,
    );
    mockedSubmitAdminOnboardingDraftForReview.mockResolvedValue(
      submitForReviewResponse,
    );
    mockedValidateAdminOnboardingDryRun.mockResolvedValue(
      dryRunValidationResponse,
    );
  });

  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("renders the company onboarding shell with external identifier guardrails", async () => {
    renderWorkspace(<CompanyOnboardingPage />);

    expect(
      screen.getByRole("heading", {
        name: "Company & organisation onboarding",
      }),
    ).toBeInTheDocument();
    expect(screen.getByText("Shell only")).toBeInTheDocument();
    expect(screen.getByLabelText(/Organisation name/)).toBeInTheDocument();
    expect(screen.getByLabelText(/external_tenant_ref/)).toBeInTheDocument();
    expect(screen.getByLabelText(/organisation_ref/)).toBeInTheDocument();
    expect(
      screen.getByText("Internal tenant identifier stays hidden"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("No records are created from this page."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Create account later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Preview validation" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Submit for review" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Accept internal review" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Mark review blocked" }),
    ).toBeDisabled();
    expect(
      await screen.findByText("Read-only platform state"),
    ).toBeInTheDocument();
    expect(screen.queryByText(/tenant_code/i)).not.toBeInTheDocument();
  });

  it("requests read-only company state with external references", async () => {
    renderWorkspace(<CompanyOnboardingPage />);

    await waitFor(() => {
      expect(mockedGetAdminOnboardingState).toHaveBeenCalledWith({
        external_tenant_ref: "demo-platform-operator",
        organisation_ref: "demo-organisation",
      });
    });
  });

  it("shows read-only partial evidence without enabling account creation", async () => {
    renderWorkspace(<CompanyOnboardingPage />);

    expect(
      await screen.findByText("Organisation evidence is partially available."),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Company onboarding remains shell-only."),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Confirm external references before go-live review."),
    ).toBeInTheDocument();
    expect(screen.getByText("demo-platform-operator")).toBeInTheDocument();
    expect(screen.getByText("demo-organisation")).toBeInTheDocument();
    expect(screen.getByText("Missing evidence")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Create account later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Submit for review" }),
    ).toBeDisabled();
  });

  it("updates local readiness state without enabling account creation", () => {
    renderWorkspace(<CompanyOnboardingPage />);

    fireEvent.change(screen.getByLabelText(/Organisation name/), {
      target: { value: "Acme Distribution Ltd" },
    });
    fireEvent.change(screen.getByLabelText(/external_tenant_ref/), {
      target: { value: "acme-distribution" },
    });
    fireEvent.change(screen.getByLabelText(/organisation_ref/), {
      target: { value: "org-acme" },
    });
    fireEvent.change(screen.getByLabelText(/Country/), {
      target: { value: "South Africa" },
    });
    fireEvent.change(screen.getByLabelText(/Industry/), {
      target: { value: "Insurance" },
    });
    fireEvent.change(screen.getByLabelText(/Admin contact/), {
      target: { value: "ops@example.test" },
    });
    fireEvent.change(screen.getByLabelText(/Intended role/), {
      target: { value: "Producer admin" },
    });

    expect(
      screen.getByText("Required shell fields are captured locally."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Create account later" }),
    ).toBeDisabled();
    expect(readinessPanel().getByText("Profile drafted")).toBeInTheDocument();
    expect(readinessPanel().getAllByText("Ready")).toHaveLength(3);
    expect(readinessPanel().getByText("Pending")).toBeInTheDocument();
    expect(screen.getByText("Backend account lifecycle")).toBeInTheDocument();
  });

  it("saves draft intent with external references and keeps live actions disabled", async () => {
    renderWorkspace(<CompanyOnboardingPage />);

    fireEvent.change(screen.getByLabelText(/Organisation name/), {
      target: { value: "Acme Distribution Ltd" },
    });
    fireEvent.change(screen.getByLabelText(/external_tenant_ref/), {
      target: { value: "acme-distribution" },
    });
    fireEvent.change(screen.getByLabelText(/organisation_ref/), {
      target: { value: "org-acme" },
    });
    fireEvent.change(screen.getByLabelText(/Country/), {
      target: { value: "South Africa" },
    });
    fireEvent.change(screen.getByLabelText(/Industry/), {
      target: { value: "Insurance" },
    });
    fireEvent.change(screen.getByLabelText(/Admin contact/), {
      target: { value: "ops@example.test" },
    });
    fireEvent.change(screen.getByLabelText(/Intended role/), {
      target: { value: "Producer admin" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Save draft" }));

    await waitFor(() => {
      expect(mockedSaveAdminOnboardingDraft).toHaveBeenCalledTimes(1);
    });
    const request = mockedSaveAdminOnboardingDraft.mock.calls[0][0];

    expect(request).toMatchObject({
      external_tenant_ref: "acme-distribution",
      organisation_ref: "org-acme",
      correlation_id: "company-onboarding-shell",
      sections: {
        company: {
          organisation_name: "Acme Distribution Ltd",
          external_tenant_ref: "acme-distribution",
          organisation_ref: "org-acme",
          country: "South Africa",
          organisation_type: "Producer / sponsor",
          industry: "Insurance",
          admin_contact: "ops@example.test",
          intended_role: "Producer admin",
        },
      },
    });
    expect(request.idempotency_key).toContain("company-onboarding-draft");
    expect(JSON.stringify(request).toLowerCase()).not.toContain("tenant_code");
    expect(JSON.stringify(request).toLowerCase()).not.toContain("api_key");
    expect(JSON.stringify(request).toLowerCase()).not.toContain(
      "client_secret",
    );

    expect(
      await screen.findByText("Draft saved for review."),
    ).toBeInTheDocument();
    expect(screen.getByText(/draft_acme_distribution/)).toBeInTheDocument();
    expect(
      screen.getByText("Review company draft evidence before go-live review."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Create account later" }),
    ).toBeDisabled();
    expect(screen.queryByText(/tenant_code/i)).not.toBeInTheDocument();
  });

  it("submits a saved company draft for review with external refs only", async () => {
    renderWorkspace(<CompanyOnboardingPage />);

    fillRequiredCompanyFields();
    fireEvent.click(screen.getByRole("button", { name: "Save draft" }));

    expect(
      await screen.findByText("Draft saved for review."),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Submit for review" }));

    await waitFor(() => {
      expect(mockedSubmitAdminOnboardingDraftForReview).toHaveBeenCalledTimes(
        1,
      );
    });
    const [draftRef, request] =
      mockedSubmitAdminOnboardingDraftForReview.mock.calls[0];
    const renderedRequest = JSON.stringify(request).toLowerCase();

    expect(draftRef).toBe("draft_acme_distribution");
    expect(request).toMatchObject({
      external_tenant_ref: "acme-distribution",
      organisation_ref: "org-acme",
      expected_version: 1,
      correlation_id: "company-onboarding-submit-review",
    });
    expect(request.idempotency_key).toContain(
      "company-onboarding-submit-review",
    );
    expect(renderedRequest).not.toContain("tenant_code");
    expect(renderedRequest).not.toContain("secret");
    expect(renderedRequest).not.toContain("api_key");
    expect(renderedRequest).not.toContain("client_secret");
    expect(renderedRequest).not.toContain("wallet");
    expect(renderedRequest).not.toContain("settlement");
    expect(renderedRequest).not.toContain("fulfilment");
    expect(renderedRequest).not.toContain("retry");
    expect(renderedRequest).not.toContain("money_movement");

    expect(
      await screen.findByText("Draft submitted for review."),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/READY_FOR_REVIEW/).length).toBeGreaterThan(0);
    expect(screen.getByText(/Validation: READY/)).toBeInTheDocument();
    expect(screen.getByText(/go-live: disabled/)).toBeInTheDocument();
    expect(
      screen.getByText(
        "Next actions: Review submitted draft evidence before any later approval.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Create account later" }),
    ).toBeDisabled();
    expect(screen.queryByText(/tenant_code/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/SECRET-API-KEY/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/SIGNING-SECRET/i)).not.toBeInTheDocument();
  });

  it("records an internal review decision only after submit-for-review", async () => {
    renderWorkspace(<CompanyOnboardingPage />);

    fillRequiredCompanyFields();
    fireEvent.click(screen.getByRole("button", { name: "Save draft" }));
    expect(
      await screen.findByText("Draft saved for review."),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Submit for review" }));
    expect(
      await screen.findByText("Draft submitted for review."),
    ).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Review reason"), {
      target: { value: "Evidence is complete enough for internal review." },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Accept internal review" }),
    );

    await waitFor(() => {
      expect(mockedRecordAdminOnboardingReviewDecision).toHaveBeenCalledTimes(
        1,
      );
    });
    const [draftRef, request] =
      mockedRecordAdminOnboardingReviewDecision.mock.calls[0];
    const renderedRequest = JSON.stringify(request).toLowerCase();

    expect(draftRef).toBe("draft_acme_distribution");
    expect(request).toMatchObject({
      external_tenant_ref: "acme-distribution",
      organisation_ref: "org-acme",
      expected_version: 2,
      review_outcome: "APPROVED_FOR_INTERNAL_REVIEW",
      reason_category: "OPERATOR_REVIEW",
      reason: "Evidence is complete enough for internal review.",
      correlation_id: "company-onboarding-review-decision",
    });
    expect(request.idempotency_key).toContain(
      "company-onboarding-review-decision",
    );
    expect(renderedRequest).not.toContain("tenant_code");
    expect(renderedRequest).not.toContain("secret");
    expect(renderedRequest).not.toContain("api_key");
    expect(renderedRequest).not.toContain("client_secret");
    expect(renderedRequest).not.toContain("wallet");
    expect(renderedRequest).not.toContain("settlement");
    expect(renderedRequest).not.toContain("fulfilment");
    expect(renderedRequest).not.toContain("retry");
    expect(renderedRequest).not.toContain("money_movement");
    expect(renderedRequest).not.toContain("approval_to_launch");
    expect(renderedRequest).not.toContain("go_live_enabled");

    expect(
      await screen.findByText("Review decision recorded."),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/APPROVED_FOR_INTERNAL_REVIEW/),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/audit evidence: RECORDED_REFERENCE/),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/go-live: disabled/).length).toBeGreaterThan(0);
    expect(
      screen.getByText("Audit reference: REVIEW_DECISION_AUDIT_EVIDENCE"),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Create account later" }),
    ).toBeDisabled();
    expect(screen.queryByText(/tenant_code/i)).not.toBeInTheDocument();
  });

  it("requires a bounded reason before recording a review decision", async () => {
    renderWorkspace(<CompanyOnboardingPage />);

    fillRequiredCompanyFields();
    fireEvent.click(screen.getByRole("button", { name: "Save draft" }));
    expect(
      await screen.findByText("Draft saved for review."),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Submit for review" }));
    expect(
      await screen.findByText("Draft submitted for review."),
    ).toBeInTheDocument();
    fireEvent.click(
      screen.getByRole("button", { name: "Accept internal review" }),
    );

    expect(
      await screen.findByText("Review decision fallback."),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "A bounded review reason is required before a review decision can be recorded. No approval or live action was taken.",
      ),
    ).toBeInTheDocument();
    expect(mockedRecordAdminOnboardingReviewDecision).not.toHaveBeenCalled();
  });

  it("records a blocked review decision without enabling launch actions", async () => {
    mockedRecordAdminOnboardingReviewDecision.mockResolvedValue({
      ...reviewDecisionResponse,
      draft_status: "BLOCKED",
      review_outcome: "BLOCKED",
      reason_category: "REVIEW_BLOCKER",
    });
    renderWorkspace(<CompanyOnboardingPage />);

    fillRequiredCompanyFields();
    fireEvent.click(screen.getByRole("button", { name: "Save draft" }));
    expect(
      await screen.findByText("Draft saved for review."),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Submit for review" }));
    expect(
      await screen.findByText("Draft submitted for review."),
    ).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Review reason"), {
      target: { value: "Policy evidence is missing." },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Mark review blocked" }),
    );

    await waitFor(() => {
      expect(mockedRecordAdminOnboardingReviewDecision).toHaveBeenCalledTimes(
        1,
      );
    });
    expect(
      mockedRecordAdminOnboardingReviewDecision.mock.calls[0][1],
    ).toMatchObject({
      review_outcome: "BLOCKED",
      reason_category: "REVIEW_BLOCKER",
      reason: "Policy evidence is missing.",
    });
    expect(
      await screen.findByText("Review decision recorded."),
    ).toBeInTheDocument();
    expect(screen.getByText(/BLOCKED/)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Create account later" }),
    ).toBeDisabled();
  });

  it("shows safe review-decision fallbacks", async () => {
    mockedRecordAdminOnboardingReviewDecision.mockRejectedValue({
      status: 409,
      message: "IDEMPOTENCY_CONFLICT",
    });
    renderWorkspace(<CompanyOnboardingPage />);

    fillRequiredCompanyFields();
    fireEvent.click(screen.getByRole("button", { name: "Save draft" }));
    expect(
      await screen.findByText("Draft saved for review."),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Submit for review" }));
    expect(
      await screen.findByText("Draft submitted for review."),
    ).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Review reason"), {
      target: { value: "Evidence is complete enough for internal review." },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Accept internal review" }),
    );

    expect(
      await screen.findByText(
        "The submitted draft changed or the review decision conflicts with an earlier request. No approval, go-live, or live action was taken.",
      ),
    ).toBeInTheDocument();
    expect(screen.queryByText(/tenant_code/i)).not.toBeInTheDocument();
  });

  it("shows validation blockers from submit-for-review safely", async () => {
    mockedSubmitAdminOnboardingDraftForReview.mockRejectedValue({
      status: 422,
      message: "VALIDATION_BLOCKED",
    });
    renderWorkspace(<CompanyOnboardingPage />);

    fillRequiredCompanyFields();
    fireEvent.click(screen.getByRole("button", { name: "Save draft" }));
    expect(
      await screen.findByText("Draft saved for review."),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Submit for review" }));

    expect(
      await screen.findByText("Submit for review fallback."),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "The saved draft has validation blockers and cannot be submitted for review yet. No approval or live action was taken.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Create account later" }),
    ).toBeDisabled();
  });

  it("shows stale or idempotency submit errors safely", async () => {
    mockedSubmitAdminOnboardingDraftForReview.mockRejectedValue({
      status: 409,
      message: "STALE_DRAFT",
    });
    renderWorkspace(<CompanyOnboardingPage />);

    fillRequiredCompanyFields();
    fireEvent.click(screen.getByRole("button", { name: "Save draft" }));
    expect(
      await screen.findByText("Draft saved for review."),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Submit for review" }));

    expect(
      await screen.findByText(
        "The saved draft changed or the submit request conflicts with a previous review request. No approval or live action was taken.",
      ),
    ).toBeInTheDocument();
    expect(screen.queryByText(/tenant_code/i)).not.toBeInTheDocument();
  });

  it("shows safe fallback when submit-for-review is unavailable", async () => {
    mockedSubmitAdminOnboardingDraftForReview.mockRejectedValue({
      status: 503,
      message: "service unavailable",
    });
    renderWorkspace(<CompanyOnboardingPage />);

    fillRequiredCompanyFields();
    fireEvent.click(screen.getByRole("button", { name: "Save draft" }));
    expect(
      await screen.findByText("Draft saved for review."),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Submit for review" }));

    expect(
      await screen.findByText(
        "Submit for review is unavailable, so the page is keeping the saved draft in local review-only state. No approval or live action was taken.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Create account later" }),
    ).toBeDisabled();
  });

  it("previews dry-run validation with external references without saving draft intent", async () => {
    renderWorkspace(<CompanyOnboardingPage />);

    fireEvent.change(screen.getByLabelText(/Organisation name/), {
      target: { value: "Acme Distribution Ltd" },
    });
    fireEvent.change(screen.getByLabelText(/external_tenant_ref/), {
      target: { value: "acme-distribution" },
    });
    fireEvent.change(screen.getByLabelText(/organisation_ref/), {
      target: { value: "org-acme" },
    });
    fireEvent.change(screen.getByLabelText(/Country/), {
      target: { value: "South Africa" },
    });
    fireEvent.change(screen.getByLabelText(/Industry/), {
      target: { value: "Insurance" },
    });
    fireEvent.change(screen.getByLabelText(/Admin contact/), {
      target: { value: "ops@example.test" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Preview validation" }));

    await waitFor(() => {
      expect(mockedValidateAdminOnboardingDryRun).toHaveBeenCalledTimes(1);
    });

    expect(mockedSaveAdminOnboardingDraft).not.toHaveBeenCalled();
    const request = mockedValidateAdminOnboardingDryRun.mock.calls[0][0];
    const renderedRequest = JSON.stringify(request).toLowerCase();

    expect(request).toMatchObject({
      external_tenant_ref: "acme-distribution",
      organisation_ref: "org-acme",
      validation_scope: ["company", "readiness"],
      correlation_id: "company-onboarding-validation-preview",
      sections: {
        company: {
          organisation_name: "Acme Distribution Ltd",
          external_tenant_ref: "acme-distribution",
          organisation_ref: "org-acme",
          country: "South Africa",
          organisation_type: "Producer / sponsor",
          industry: "Insurance",
          admin_contact: "ops@example.test",
          intended_role: "Company admin",
        },
      },
    });
    expect(renderedRequest).not.toContain("tenant_code");
    expect(renderedRequest).not.toContain("api_key");
    expect(renderedRequest).not.toContain("client_secret");

    expect(
      await screen.findByText("Dry-run validation preview."),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Status: MISSING_EVIDENCE; readiness: GO_LIVE_DISABLED/),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Company profile: Company profile needs one more evidence check.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Missing evidence: MISSING_EVIDENCE/),
    ).toBeInTheDocument();
    expect(screen.getByText(/Blockers: READINESS_BLOCKED/)).toBeInTheDocument();
    expect(screen.getByText(/Warnings: GO_LIVE_DISABLED/)).toBeInTheDocument();
    expect(
      screen.getByText(
        "Next actions: Review company profile before go-live review.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Create account later" }),
    ).toBeDisabled();
    expect(screen.queryByText(/tenant_code/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/SECRET-API-KEY/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/SECRET-CLIENT/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/SIGNING-SECRET/i)).not.toBeInTheDocument();
  });

  it("shows safe fallback when dry-run validation preview is unavailable", async () => {
    mockedValidateAdminOnboardingDryRun.mockRejectedValue({
      status: 503,
      message: "service unavailable",
    });
    renderWorkspace(<CompanyOnboardingPage />);

    fireEvent.change(screen.getByLabelText(/external_tenant_ref/), {
      target: { value: "acme-distribution" },
    });
    fireEvent.change(screen.getByLabelText(/organisation_ref/), {
      target: { value: "org-acme" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Preview validation" }));

    expect(
      await screen.findByText("Validation preview fallback."),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Dry-run validation is unavailable, so the page is keeping local shell feedback only. No draft was saved and no live action was taken.",
      ),
    ).toBeInTheDocument();
    expect(mockedSaveAdminOnboardingDraft).not.toHaveBeenCalled();
    expect(
      screen.getByRole("button", { name: "Create account later" }),
    ).toBeDisabled();
  });

  it("shows a safe fallback when draft save is unavailable", async () => {
    mockedSaveAdminOnboardingDraft.mockRejectedValue({
      status: 503,
      message: "service unavailable",
    });
    renderWorkspace(<CompanyOnboardingPage />);

    fireEvent.change(screen.getByLabelText(/external_tenant_ref/), {
      target: { value: "acme-distribution" },
    });
    fireEvent.change(screen.getByLabelText(/organisation_ref/), {
      target: { value: "org-acme" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save draft" }));

    expect(await screen.findByText("Draft save fallback.")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Draft save is unavailable, so the page is keeping local shell state only. No live action was taken.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Create account later" }),
    ).toBeDisabled();
  });

  it("shows a safe idempotency or duplicate draft fallback without live actions", async () => {
    mockedSaveAdminOnboardingDraft.mockRejectedValue({
      status: 409,
      message: "IDEMPOTENCY_CONFLICT",
    });
    renderWorkspace(<CompanyOnboardingPage />);

    fireEvent.change(screen.getByLabelText(/external_tenant_ref/), {
      target: { value: "acme-distribution" },
    });
    fireEvent.change(screen.getByLabelText(/organisation_ref/), {
      target: { value: "org-acme" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save draft" }));

    expect(await screen.findByText("Draft save fallback.")).toBeInTheDocument();
    expect(
      screen.getByText(
        "A matching draft already exists or the idempotency key needs review. No live action was taken.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Create account later" }),
    ).toBeDisabled();
  });

  it("links the company setup journey to future onboarding and monitoring surfaces", () => {
    renderWorkspace(<CompanyOnboardingPage />);

    expect(
      screen.getByRole("link", { name: /Producer \/ sponsor onboarding/ }),
    ).toHaveAttribute("href", "/admin/onboarding/producer-sponsor");
    expect(
      screen.getByRole("link", { name: /Distributor onboarding/ }),
    ).toHaveAttribute("href", "/admin/onboarding/distributor");
    expect(
      screen.getByRole("link", { name: /User & role setup/ }),
    ).toHaveAttribute("href", "/admin/onboarding/members-roles");
    expect(
      screen.getByRole("link", { name: /Campaign \/ opportunity setup/ }),
    ).toHaveAttribute("href", "/admin/onboarding/campaign-opportunity");
    expect(
      screen.getByRole("link", { name: /Webhook & API setup/ }),
    ).toHaveAttribute("href", "/admin/onboarding/webhook-api");
    expect(
      screen.getByRole("link", { name: /Operator monitoring/ }),
    ).toHaveAttribute("href", "/admin");
  });

  it("falls back to local shell state when read-only company state is unavailable", async () => {
    mockedGetAdminOnboardingState.mockRejectedValue(new Error("offline"));
    renderWorkspace(<CompanyOnboardingPage />);

    expect(
      await screen.findByText("Using local company setup fallback."),
    ).toBeInTheDocument();
    expect(screen.getAllByText("Company profile").length).toBeGreaterThan(0);
    expect(
      screen.getByRole("button", { name: "Create account later" }),
    ).toBeDisabled();
  });
});

function fillRequiredCompanyFields() {
  fireEvent.change(screen.getByLabelText(/Organisation name/), {
    target: { value: "Acme Distribution Ltd" },
  });
  fireEvent.change(screen.getByLabelText(/external_tenant_ref/), {
    target: { value: "acme-distribution" },
  });
  fireEvent.change(screen.getByLabelText(/organisation_ref/), {
    target: { value: "org-acme" },
  });
  fireEvent.change(screen.getByLabelText(/Country/), {
    target: { value: "South Africa" },
  });
  fireEvent.change(screen.getByLabelText(/Industry/), {
    target: { value: "Insurance" },
  });
  fireEvent.change(screen.getByLabelText(/Admin contact/), {
    target: { value: "ops@example.test" },
  });
}
