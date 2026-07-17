import {
  Building2,
  CheckCircle2,
  CircleDashed,
  KeyRound,
  Link as LinkIcon,
  ShieldCheck,
  Users,
} from "lucide-react";
import { useEffect, useId, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  getAdminOnboardingState,
  recordAdminOnboardingReviewDecision,
  saveAdminOnboardingDraft,
  submitAdminOnboardingDraftForReview,
  validateAdminOnboardingDryRun,
  type AdminOnboardingDraftSaveResponse,
  type AdminOnboardingDryRunValidationResponse,
  type AdminOnboardingReviewDecisionResponse,
  type AdminOnboardingReviewOutcome,
  type AdminOnboardingStateResponse,
  type AdminOnboardingSubmitForReviewResponse,
} from "../../api/endpoints/adminOnboarding";
import { StatusBadge } from "../../components/StatusBadge";
import { SummaryItem } from "../../components/SummaryItem";

type FormState = {
  organisationName: string;
  externalTenantRef: string;
  organisationRef: string;
  country: string;
  organisationType: string;
  industry: string;
  adminContact: string;
  intendedRole: string;
};

type ReadinessStep = {
  label: string;
  copy: string;
  ready: boolean;
};

const initialState: FormState = {
  organisationName: "",
  externalTenantRef: "",
  organisationRef: "",
  country: "",
  organisationType: "Producer / sponsor",
  industry: "",
  adminContact: "",
  intendedRole: "Company admin",
};

const futureJourneyLinks = [
  {
    label: "Producer / sponsor onboarding",
    path: "/admin/onboarding/producer-sponsor",
    copy: "Continue with sponsor profile, funding-readiness placeholders, and campaign ownership context.",
  },
  {
    label: "Distributor onboarding",
    path: "/admin/onboarding/distributor",
    copy: "Invite distributors or partner admins into the demand side once the company shell is complete.",
  },
  {
    label: "User & role setup",
    path: "/admin/onboarding/members-roles",
    copy: "Draft invite, membership, and role-family intent without creating users or roles.",
  },
  {
    label: "Campaign / opportunity setup",
    path: "/admin/onboarding/campaign-opportunity",
    copy: "Draft campaign, opportunity, readiness, and go-live intent without launching anything.",
  },
  {
    label: "Webhook & API setup",
    path: "/admin/onboarding/webhook-api",
    copy: "Draft credential, callback, event catalog, and payload preview intent without creating secrets.",
  },
  {
    label: "Operator monitoring",
    path: "/admin",
    copy: "Return to read-only platform diagnostics while account lifecycle APIs remain future work.",
  },
];

const readOnlyScope = {
  external_tenant_ref: "demo-platform-operator",
  organisation_ref: "demo-organisation",
};

type LoadState = "loading" | "success" | "fallback";
type DraftSaveState = "idle" | "saving" | "saved" | "error";
type ValidationPreviewState = "idle" | "loading" | "success" | "error";
type SubmitForReviewState = "idle" | "submitting" | "submitted" | "error";
type ReviewDecisionState = "idle" | "recording" | "recorded" | "error";

export function CompanyOnboardingPage() {
  const [form, setForm] = useState<FormState>(initialState);
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [readOnlyState, setReadOnlyState] =
    useState<AdminOnboardingStateResponse | null>(null);
  const [draftSaveState, setDraftSaveState] = useState<DraftSaveState>("idle");
  const [draftSaveResponse, setDraftSaveResponse] =
    useState<AdminOnboardingDraftSaveResponse | null>(null);
  const [draftSaveError, setDraftSaveError] = useState<string | null>(null);
  const [validationPreviewState, setValidationPreviewState] =
    useState<ValidationPreviewState>("idle");
  const [validationPreview, setValidationPreview] =
    useState<AdminOnboardingDryRunValidationResponse | null>(null);
  const [validationPreviewError, setValidationPreviewError] = useState<
    string | null
  >(null);
  const [submitForReviewState, setSubmitForReviewState] =
    useState<SubmitForReviewState>("idle");
  const [submitForReviewResponse, setSubmitForReviewResponse] =
    useState<AdminOnboardingSubmitForReviewResponse | null>(null);
  const [submitForReviewError, setSubmitForReviewError] = useState<
    string | null
  >(null);
  const [reviewReason, setReviewReason] = useState("");
  const [reviewDecisionState, setReviewDecisionState] =
    useState<ReviewDecisionState>("idle");
  const [reviewDecisionResponse, setReviewDecisionResponse] =
    useState<AdminOnboardingReviewDecisionResponse | null>(null);
  const [reviewDecisionError, setReviewDecisionError] = useState<string | null>(
    null,
  );
  const requiredComplete = Boolean(
    form.organisationName.trim() &&
    form.externalTenantRef.trim() &&
    form.organisationRef.trim() &&
    form.country.trim() &&
    form.adminContact.trim(),
  );

  const readinessSteps = useMemo<ReadinessStep[]>(
    () => [
      {
        label: "Company profile",
        copy: "Organisation name, country, type, and industry are captured locally for the onboarding shell.",
        ready: Boolean(
          form.organisationName.trim() &&
          form.country.trim() &&
          form.industry.trim(),
        ),
      },
      {
        label: "External identifiers",
        copy: "`external_tenant_ref` and `organisation_ref` stay outside the internal tenant partition.",
        ready: Boolean(
          form.externalTenantRef.trim() && form.organisationRef.trim(),
        ),
      },
      {
        label: "Admin contact",
        copy: "Primary admin contact and intended role are ready for a future membership invite flow.",
        ready: Boolean(form.adminContact.trim() && form.intendedRole.trim()),
      },
      {
        label: "Backend account lifecycle",
        copy: "Blocked until additive account, membership, and external-reference APIs are implemented.",
        ready: false,
      },
    ],
    [form],
  );

  const readyCount = readinessSteps.filter((step) => step.ready).length;
  const organisationCategory = readOnlyState?.readiness.categories.find(
    (category) => category.category.toUpperCase().includes("ORGANISATION"),
  );
  const draftSaveReady = Boolean(
    form.externalTenantRef.trim() && form.organisationRef.trim(),
  );
  const draftIdempotencyKey = useMemo(
    () =>
      [
        "company-onboarding-draft",
        form.externalTenantRef.trim() || "missing-external-ref",
        form.organisationRef.trim() || "missing-organisation-ref",
        form.organisationName.trim() || "unnamed-organisation",
        form.adminContact.trim() || "missing-admin-contact",
      ].join(":"),
    [form],
  );
  const submitForReviewReady = Boolean(draftSaveResponse?.draft_ref);
  const reviewDecisionReady = Boolean(
    submitForReviewResponse?.draft_ref &&
    submitForReviewResponse.draft_status === "READY_FOR_REVIEW",
  );
  const submitForReviewIdempotencyKey = useMemo(
    () =>
      [
        "company-onboarding-submit-review",
        draftSaveResponse?.draft_ref || "missing-draft-ref",
        form.externalTenantRef.trim() || "missing-external-ref",
        form.organisationRef.trim() || "missing-organisation-ref",
      ].join(":"),
    [
      draftSaveResponse?.draft_ref,
      form.externalTenantRef,
      form.organisationRef,
    ],
  );
  const reviewDecisionIdempotencyKey = useMemo(
    () =>
      [
        "company-onboarding-review-decision",
        submitForReviewResponse?.draft_ref || "missing-draft-ref",
        submitForReviewResponse?.draft_version ?? "missing-version",
        form.externalTenantRef.trim() || "missing-external-ref",
        form.organisationRef.trim() || "missing-organisation-ref",
      ].join(":"),
    [
      submitForReviewResponse?.draft_ref,
      submitForReviewResponse?.draft_version,
      form.externalTenantRef,
      form.organisationRef,
    ],
  );

  function updateField(field: keyof FormState, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function handleSaveDraft() {
    if (!draftSaveReady || draftSaveState === "saving") {
      return;
    }

    setDraftSaveState("saving");
    setDraftSaveError(null);
    setDraftSaveResponse(null);

    try {
      const response = await saveAdminOnboardingDraft({
        external_tenant_ref: form.externalTenantRef,
        organisation_ref: form.organisationRef,
        idempotency_key: draftIdempotencyKey,
        correlation_id: "company-onboarding-shell",
        sections: {
          company: {
            organisation_name: form.organisationName,
            external_tenant_ref: form.externalTenantRef,
            organisation_ref: form.organisationRef,
            country: form.country,
            organisation_type: form.organisationType,
            industry: form.industry,
            admin_contact: form.adminContact,
            intended_role: form.intendedRole,
          },
        },
      });
      setDraftSaveResponse(response);
      setDraftSaveState("saved");
      setSubmitForReviewState("idle");
      setSubmitForReviewResponse(null);
      setSubmitForReviewError(null);
      setReviewDecisionState("idle");
      setReviewDecisionResponse(null);
      setReviewDecisionError(null);
    } catch (error) {
      const status =
        typeof error === "object" && error && "status" in error
          ? Number((error as { status?: number }).status)
          : null;
      setDraftSaveError(
        status === 409
          ? "A matching draft already exists or the idempotency key needs review. No live action was taken."
          : "Draft save is unavailable, so the page is keeping local shell state only. No live action was taken.",
      );
      setDraftSaveState("error");
    }
  }

  async function handleSubmitForReview() {
    if (
      !draftSaveResponse?.draft_ref ||
      submitForReviewState === "submitting"
    ) {
      return;
    }

    setSubmitForReviewState("submitting");
    setSubmitForReviewResponse(null);
    setSubmitForReviewError(null);

    try {
      const response = await submitAdminOnboardingDraftForReview(
        draftSaveResponse.draft_ref,
        {
          external_tenant_ref: form.externalTenantRef,
          organisation_ref: form.organisationRef,
          expected_version: draftSaveResponse.draft_version ?? 1,
          idempotency_key: submitForReviewIdempotencyKey,
          correlation_id: "company-onboarding-submit-review",
        },
      );
      setSubmitForReviewResponse(response);
      setSubmitForReviewState("submitted");
      setReviewDecisionState("idle");
      setReviewDecisionResponse(null);
      setReviewDecisionError(null);
    } catch (error) {
      const status =
        typeof error === "object" && error && "status" in error
          ? Number((error as { status?: number }).status)
          : null;
      setSubmitForReviewError(safeSubmitForReviewError(status));
      setSubmitForReviewState("error");
    }
  }

  async function handleReviewDecision(outcome: AdminOnboardingReviewOutcome) {
    if (
      !submitForReviewResponse?.draft_ref ||
      !reviewDecisionReady ||
      reviewDecisionState === "recording"
    ) {
      return;
    }

    const reason = reviewReason.trim();
    if (!reason) {
      setReviewDecisionError(
        "A bounded review reason is required before a review decision can be recorded. No approval or live action was taken.",
      );
      setReviewDecisionState("error");
      return;
    }

    setReviewDecisionState("recording");
    setReviewDecisionResponse(null);
    setReviewDecisionError(null);

    try {
      const response = await recordAdminOnboardingReviewDecision(
        submitForReviewResponse.draft_ref,
        {
          external_tenant_ref: form.externalTenantRef,
          organisation_ref: form.organisationRef,
          expected_version: submitForReviewResponse.draft_version ?? 1,
          idempotency_key: `${reviewDecisionIdempotencyKey}:${outcome}`,
          review_outcome: outcome,
          reason_category:
            outcome === "BLOCKED" ? "REVIEW_BLOCKER" : "OPERATOR_REVIEW",
          reason,
          correlation_id: "company-onboarding-review-decision",
        },
      );
      setReviewDecisionResponse(response);
      setReviewDecisionState("recorded");
    } catch (error) {
      const status =
        typeof error === "object" && error && "status" in error
          ? Number((error as { status?: number }).status)
          : null;
      setReviewDecisionError(safeReviewDecisionError(status));
      setReviewDecisionState("error");
    }
  }

  async function handlePreviewValidation() {
    if (!draftSaveReady || validationPreviewState === "loading") {
      return;
    }

    setValidationPreviewState("loading");
    setValidationPreview(null);
    setValidationPreviewError(null);

    try {
      const response = await validateAdminOnboardingDryRun({
        external_tenant_ref: form.externalTenantRef,
        organisation_ref: form.organisationRef,
        validation_scope: ["company", "readiness"],
        correlation_id: "company-onboarding-validation-preview",
        sections: {
          company: companySectionPayload(form),
        },
      });
      setValidationPreview(response);
      setValidationPreviewState("success");
    } catch {
      setValidationPreviewError(
        "Dry-run validation is unavailable, so the page is keeping local shell feedback only. No draft was saved and no live action was taken.",
      );
      setValidationPreviewState("error");
    }
  }

  useEffect(() => {
    let cancelled = false;

    getAdminOnboardingState(readOnlyScope)
      .then((response) => {
        if (cancelled) {
          return;
        }
        setReadOnlyState(response);
        setLoadState("success");
      })
      .catch(() => {
        if (cancelled) {
          return;
        }
        setReadOnlyState(null);
        setLoadState("fallback");
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <>
      <section className="page-header">
        <div>
          <div className="page-kicker">Referral SaaS Account Setup - Step 1</div>
          <h1 className="page-title">Step 1: Company profile</h1>
          <p className="page-copy">
            Capture the company evidence that Account Setup needs before
            review, durable account creation, users, integrations, and campaign
            testing can continue.
          </p>
        </div>
        <StatusBadge label="Step 1" tone="info" />
      </section>

      <section className="banner info" role="note">
        <Building2 size={18} />
        <div>
          <strong>This is one step inside Referral SaaS Account Setup.</strong>
          <div className="table-subtext">
            Save the company draft here, then return to Account Setup to run
            readiness, review handoff, and the gated account creation path.
          </div>
        </div>
        <Link
          className="button secondary"
          to="/admin/referral-saas/account-setup"
        >
          Back to Account Setup
        </Link>
      </section>

      <section className="grid-3">
        <SummaryItem label="Readiness" value={`${readyCount}/4`} />
        <SummaryItem
          label="Read-only state"
          value={loadState === "success" ? "Available" : "Fallback"}
        />
        <SummaryItem label="Internal tenant identifier" value="Hidden" />
      </section>

      <section className="panel" aria-labelledby="read-only-state-heading">
        <div className="panel-header">
          <div>
            <h2 className="panel-title" id="read-only-state-heading">
              Saved setup evidence
            </h2>
            <div className="panel-subtitle">
              Reference context from the existing onboarding projection. Use
              the Step 1 form below for action.
            </div>
          </div>
          <StatusBadge
            label={
              loadState === "loading"
                ? "Loading"
                : loadState === "success"
                  ? "Read-only"
                  : "Demo fallback"
            }
            tone={loadState === "success" ? "success" : "info"}
          />
        </div>
        <div className="panel-body">
          {loadState === "loading" ? (
            <div className="banner info" role="status">
              <CircleDashed size={18} />
              <div>
                <strong>Loading read-only company readiness.</strong>
                <div className="table-subtext">
                  Checking saved setup evidence without creating account
                  records.
                </div>
              </div>
            </div>
          ) : loadState === "fallback" ? (
            <div className="banner warning" role="status">
              <ShieldCheck size={18} />
              <div>
                <strong>Using local company setup fallback.</strong>
                <div className="table-subtext">
                  The read-only onboarding state endpoint is unavailable, so
                  this page keeps local Step 1 state only.
                </div>
              </div>
            </div>
          ) : (
            <>
              <div className="grid-3">
                <SummaryItem
                  label="Overall readiness"
                  value={
                    readOnlyState?.readiness.overall_status ?? "Unavailable"
                  }
                />
                <SummaryItem
                  label="External tenant ref"
                  value={readOnlyScope.external_tenant_ref}
                />
                <SummaryItem
                  label="Organisation ref"
                  value={readOnlyScope.organisation_ref}
                />
              </div>
              <div className="route-list">
                <div className="route-item">
                  <div>
                    <div className="route-name">
                      {organisationCategory?.display_label ??
                        "Organisation profile"}
                    </div>
                    <div className="route-path">
                      {organisationCategory?.evidence_summary ??
                        "Read-only organisation evidence is not available yet."}
                    </div>
                    {organisationCategory?.blockers[0] ? (
                      <div className="table-subtext">
                        {organisationCategory.blockers[0]}
                      </div>
                    ) : null}
                    {organisationCategory?.next_actions[0] ? (
                      <div className="table-subtext">
                        {organisationCategory.next_actions[0]}
                      </div>
                    ) : null}
                  </div>
                  <StatusBadge
                    label={
                      organisationCategory?.safe_display_status?.label ??
                      organisationCategory?.status ??
                      "Missing evidence"
                    }
                    tone={
                      organisationCategory?.status === "READY"
                        ? "success"
                        : "info"
                    }
                  />
                </div>
              </div>
            </>
          )}
        </div>
      </section>

      <section className="banner warning" role="note">
        <ShieldCheck size={18} />
        <div>
          <strong>This page saves onboarding evidence, not the final account.</strong>
          <div className="table-subtext">
            Save draft can persist company setup intent. It does not create the
            durable account, tenant, membership, billing, credential, webhook,
            campaign, go-live, or money records.
          </div>
        </div>
      </section>

      <section className="grid-2">
        <form className="panel" aria-label="Company onboarding shell">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Step 1: company profile</h2>
              <div className="panel-subtitle">
                Enter the visible customer/account references used by the
                Referral SaaS setup workflow.
              </div>
            </div>
            <Building2 size={18} />
          </div>
          <div className="panel-body">
            <div className="grid-2">
              <TextField
                label="Organisation name"
                value={form.organisationName}
                onChange={(value) => updateField("organisationName", value)}
                placeholder="Acme Distribution Ltd"
                required
              />
              <TextField
                label="external_tenant_ref"
                value={form.externalTenantRef}
                onChange={(value) => updateField("externalTenantRef", value)}
                placeholder="acme-distribution"
                required
              />
              <TextField
                label="organisation_ref"
                value={form.organisationRef}
                onChange={(value) => updateField("organisationRef", value)}
                placeholder="org-acme"
                required
              />
              <TextField
                label="Country"
                value={form.country}
                onChange={(value) => updateField("country", value)}
                placeholder="South Africa"
                required
              />
              <SelectField
                label="Organisation type"
                value={form.organisationType}
                onChange={(value) => updateField("organisationType", value)}
                options={[
                  "Producer / sponsor",
                  "Distributor",
                  "Partner",
                  "Mixed account",
                  "Platform operator",
                ]}
              />
              <TextField
                label="Industry"
                value={form.industry}
                onChange={(value) => updateField("industry", value)}
                placeholder="Banking, insurance, retail"
              />
              <TextField
                label="Admin contact"
                value={form.adminContact}
                onChange={(value) => updateField("adminContact", value)}
                placeholder="ops@example.test"
                required
              />
              <SelectField
                label="Intended role"
                value={form.intendedRole}
                onChange={(value) => updateField("intendedRole", value)}
                options={[
                  "Company admin",
                  "Producer admin",
                  "Distributor admin",
                  "Partner admin",
                  "Platform operator",
                ]}
              />
            </div>
            <div className="action-button-row">
              <button
                className="button secondary"
                disabled={
                  !draftSaveReady || validationPreviewState === "loading"
                }
                onClick={handlePreviewValidation}
                type="button"
              >
                {validationPreviewState === "loading"
                  ? "Previewing validation"
                  : "Preview readiness"}
              </button>
              <button
                className="button secondary"
                disabled={!draftSaveReady || draftSaveState === "saving"}
                onClick={handleSaveDraft}
                type="button"
              >
                {draftSaveState === "saving"
                  ? "Saving draft"
                  : "Save company draft"}
              </button>
              <button
                className="button secondary"
                disabled={
                  !submitForReviewReady || submitForReviewState === "submitting"
                }
                onClick={handleSubmitForReview}
                type="button"
              >
                {submitForReviewState === "submitting"
                  ? "Submitting for review"
                  : "Submit profile for review"}
              </button>
              <button
                className="button"
                disabled
                title="Durable account creation is completed from Account Setup after review."
                type="button"
              >
                Create account in Account Setup
              </button>
              <span className={requiredComplete ? "muted" : "danger-text"}>
                {requiredComplete
                  ? "Company profile is complete enough to save."
                  : "Complete required company fields to save the profile draft."}
              </span>
            </div>
            <div className="table-subtext">
              Preview readiness answers three questions before you save: can
              this continue, why is it blocked, and what should happen next. It
              does not save, submit, create records, launch, or move money.
            </div>
            {validationPreviewState === "loading" ? (
              <div className="banner info" role="status">
                <CircleDashed size={18} />
                <div>
                  <strong>Previewing validation.</strong>
                  <div className="table-subtext">
                    The shell is checking company readiness without saving or
                    launching anything.
                  </div>
                </div>
              </div>
            ) : null}
            {validationPreviewState === "success" && validationPreview ? (
              <ValidationPreviewPanel preview={validationPreview} />
            ) : null}
            {validationPreviewState === "error" && validationPreviewError ? (
              <div className="banner warning" role="status">
                <ShieldCheck size={18} />
                <div>
                  <strong>Validation preview fallback.</strong>
                  <div className="table-subtext">{validationPreviewError}</div>
                </div>
              </div>
            ) : null}
            <div className="table-subtext">
              Draft save stores onboarding intent only. It does not create
              accounts, invite users, create credentials, publish campaigns,
              deliver webhooks, activate go-live, or move money.
            </div>
            {draftSaveState === "saved" && draftSaveResponse ? (
              <div className="banner success" role="status">
                <CheckCircle2 size={18} />
                <div>
                  <strong>Draft saved for review.</strong>
                  <div className="table-subtext">
                    {draftSaveResponse.draft_ref} -{" "}
                    {draftSaveResponse.draft_status} -{" "}
                    {draftSaveResponse.idempotency_status}
                  </div>
                  {draftSaveResponse.validation_summary ? (
                    <div className="table-subtext">
                      Validation: {draftSaveResponse.validation_summary.status};
                      blockers:{" "}
                      {draftSaveResponse.validation_summary.blocker_count};
                      missing evidence:{" "}
                      {
                        draftSaveResponse.validation_summary
                          .missing_evidence_count
                      }
                    </div>
                  ) : null}
                  {draftSaveResponse.next_actions?.[0] ? (
                    <div className="table-subtext">
                      {draftSaveResponse.next_actions[0]}
                    </div>
                  ) : null}
                </div>
              </div>
            ) : null}
            <div className="table-subtext">
              Submit for review only marks the saved draft for human review. It
              does not approve, activate, create accounts, invite users, create
              credentials, publish campaigns, deliver webhooks, activate
              go-live, or move money.
            </div>
            {submitForReviewState === "submitted" && submitForReviewResponse ? (
              <SubmitForReviewPanel response={submitForReviewResponse} />
            ) : null}
            <div className="table-subtext">
              Review decisions are internal review classifications only. They do
              not approve launch, activate go-live, create accounts, invite
              users, publish campaigns, deliver webhooks, or move money.
            </div>
            <div className="field">
              <label htmlFor="company-review-reason">Review reason</label>
              <textarea
                className="input"
                disabled={!reviewDecisionReady}
                id="company-review-reason"
                onChange={(event) => setReviewReason(event.target.value)}
                placeholder="Bounded internal review reason"
                rows={3}
                value={reviewReason}
              />
            </div>
            <div className="action-button-row">
              <button
                className="button secondary"
                disabled={
                  !reviewDecisionReady || reviewDecisionState === "recording"
                }
                onClick={() =>
                  handleReviewDecision("APPROVED_FOR_INTERNAL_REVIEW")
                }
                type="button"
              >
                {reviewDecisionState === "recording"
                  ? "Recording review"
                  : "Accept internal review"}
              </button>
              <button
                className="button secondary"
                disabled={
                  !reviewDecisionReady || reviewDecisionState === "recording"
                }
                onClick={() => handleReviewDecision("BLOCKED")}
                type="button"
              >
                Mark review blocked
              </button>
            </div>
            {reviewDecisionState === "recorded" && reviewDecisionResponse ? (
              <ReviewDecisionPanel response={reviewDecisionResponse} />
            ) : null}
            {reviewDecisionState === "error" && reviewDecisionError ? (
              <div className="banner warning" role="status">
                <ShieldCheck size={18} />
                <div>
                  <strong>Review decision fallback.</strong>
                  <div className="table-subtext">{reviewDecisionError}</div>
                </div>
              </div>
            ) : null}
            {submitForReviewState === "error" && submitForReviewError ? (
              <div className="banner warning" role="status">
                <ShieldCheck size={18} />
                <div>
                  <strong>Submit for review fallback.</strong>
                  <div className="table-subtext">{submitForReviewError}</div>
                </div>
              </div>
            ) : null}
            {draftSaveState === "error" && draftSaveError ? (
              <div className="banner warning" role="status">
                <ShieldCheck size={18} />
                <div>
                  <strong>Draft save fallback.</strong>
                  <div className="table-subtext">{draftSaveError}</div>
                </div>
              </div>
            ) : null}
          </div>
        </form>

        <section className="panel" aria-labelledby="readiness-heading">
          <div className="panel-header">
            <div>
              <h2 className="panel-title" id="readiness-heading">
                Step 1 readiness
              </h2>
              <div className="panel-subtitle">
                Plain-language checks for this company profile step.
              </div>
            </div>
            <StatusBadge
              label={requiredComplete ? "Profile drafted" : "Draft"}
              tone={requiredComplete ? "info" : "neutral"}
            />
          </div>
          <div className="panel-body route-list">
            {readinessSteps.map((step) => (
              <div className="route-item" key={step.label}>
                <div>
                  <div className="route-name">{step.label}</div>
                  <div className="route-path">{step.copy}</div>
                </div>
                <StatusBadge
                  label={step.ready ? "Ready" : "Pending"}
                  tone={step.ready ? "success" : "warning"}
                />
              </div>
            ))}
          </div>
        </section>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2 className="panel-title">Identifier boundary</h2>
            <div className="panel-subtitle">
              This shell follows the TASK-048 tenant identifier decision.
            </div>
          </div>
          <KeyRound size={18} />
        </div>
        <div className="panel-body capability-grid">
          <BoundaryCard
            icon={LinkIcon}
            title="External first"
            copy="Use external_tenant_ref and organisation_ref in onboarding and future public/SaaS-facing flows."
          />
          <BoundaryCard
            icon={ShieldCheck}
            title="Internal tenant identifier stays hidden"
            copy="Use external references as the visible product identifiers in this company setup journey."
          />
          <BoundaryCard
            icon={Users}
            title="Membership comes later"
            copy="User invites, seats, role assignment, and tenant-link enforcement are TASK-073 and backend follow-up work."
          />
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2 className="panel-title">Next setup steps</h2>
            <div className="panel-subtitle">
              Continue in the Account Setup workflow after the company draft is
              saved and reviewed.
            </div>
          </div>
          <CircleDashed size={18} />
        </div>
        <div className="panel-body route-list">
          {futureJourneyLinks.map((item) => (
            <Link className="route-item" key={item.label} to={item.path}>
              <div>
                <div className="route-name">{item.label}</div>
                <div className="route-path">{item.copy}</div>
              </div>
              <CheckCircle2 size={18} />
            </Link>
          ))}
        </div>
      </section>
    </>
  );
}

function companySectionPayload(form: FormState): Record<string, unknown> {
  return {
    organisation_name: form.organisationName,
    external_tenant_ref: form.externalTenantRef,
    organisation_ref: form.organisationRef,
    country: form.country,
    organisation_type: form.organisationType,
    industry: form.industry,
    admin_contact: form.adminContact,
    intended_role: form.intendedRole,
  };
}

function safeSubmitForReviewError(status: number | null): string {
  if (status === 409) {
    return "The saved draft changed or the submit request conflicts with a previous review request. No approval or live action was taken.";
  }
  if (status === 422) {
    return "The saved draft has validation blockers and cannot be submitted for review yet. No approval or live action was taken.";
  }
  return "Submit for review is unavailable, so the page is keeping the saved draft in local review-only state. No approval or live action was taken.";
}

function safeReviewDecisionError(status: number | null): string {
  if (status === 409) {
    return "The submitted draft changed or the review decision conflicts with an earlier request. No approval, go-live, or live action was taken.";
  }
  if (status === 422) {
    return "The submitted draft cannot receive that review decision yet. No approval, go-live, or live action was taken.";
  }
  return "Review decision recording is unavailable, so the page is keeping local review-only state. No approval, go-live, or live action was taken.";
}

function ReviewDecisionPanel({
  response,
}: {
  response: AdminOnboardingReviewDecisionResponse;
}) {
  const validationStatus = response.validation_summary?.status ?? "Unavailable";
  const guardrails = response.guardrails?.slice(0, 5) ?? [];

  return (
    <div className="banner success" role="status">
      <CheckCircle2 size={18} />
      <div>
        <strong>Review decision recorded.</strong>
        <div className="table-subtext">
          {response.draft_ref} - {response.review_outcome} -{" "}
          {response.draft_status}; no live action:{" "}
          {response.no_live_action_confirmed ? "confirmed" : "unavailable"}.
        </div>
        <div className="table-subtext">
          Validation: {validationStatus}; audit evidence:{" "}
          {response.audit_evidence_status ?? "unavailable"}; go-live:{" "}
          {response.go_live_enabled ? "enabled." : "disabled."}
        </div>
        {response.audit_evidence_ref ? (
          <div className="table-subtext">
            Audit reference: {response.audit_evidence_ref}
          </div>
        ) : null}
        {guardrails.length > 0 ? (
          <div className="table-subtext">
            Guardrails: {guardrails.join(", ")}
          </div>
        ) : null}
      </div>
    </div>
  );
}

function SubmitForReviewPanel({
  response,
}: {
  response: AdminOnboardingSubmitForReviewResponse;
}) {
  const validationStatus = response.validation_summary?.status ?? "Unavailable";
  const blockers = response.blockers?.slice(0, 3) ?? [];
  const nextActions = response.next_actions?.slice(0, 3) ?? [];
  const guardrails = response.guardrails?.slice(0, 4) ?? [];

  return (
    <div className="banner success" role="status">
      <CheckCircle2 size={18} />
      <div>
        <strong>Draft submitted for review.</strong>
        <div className="table-subtext">
          {response.draft_ref} - {response.draft_status} -{" "}
          {response.idempotency_status}; no live action:{" "}
          {response.no_live_action_confirmed ? "confirmed" : "unavailable"}.
        </div>
        <div className="table-subtext">
          Validation: {validationStatus}; blockers:{" "}
          {response.validation_summary?.blocker_count ?? 0}; missing evidence:{" "}
          {response.validation_summary?.missing_evidence_count ?? 0}.
        </div>
        {response.readiness_summary ? (
          <div className="table-subtext">
            Readiness: {response.readiness_summary.overall_status}; go-live:{" "}
            {response.readiness_summary.go_live_enabled
              ? "enabled."
              : "disabled."}
          </div>
        ) : null}
        <ValidationItemList label="Review blockers" items={blockers} />
        {nextActions.length > 0 ? (
          <div className="table-subtext">
            Next actions: {nextActions.join("; ")}
          </div>
        ) : null}
        {guardrails.length > 0 ? (
          <div className="table-subtext">
            Guardrails: {guardrails.join(", ")}
          </div>
        ) : null}
      </div>
    </div>
  );
}

function ValidationPreviewPanel({
  preview,
}: {
  preview: AdminOnboardingDryRunValidationResponse;
}) {
  const validationStatus =
    typeof preview.validation_result.status === "string"
      ? preview.validation_result.status
      : preview.status;
  const firstReadinessCategory = preview.readiness_preview.categories[0];
  const missingEvidence = preview.missing_evidence.slice(0, 3);
  const blockers = preview.blockers.slice(0, 3);
  const warnings = preview.warnings.slice(0, 2);
  const safeErrors = preview.safe_errors.slice(0, 2);
  const nextActions = preview.next_actions.slice(0, 3);
  const canContinue =
    blockers.length === 0 &&
    missingEvidence.length === 0 &&
    safeErrors.length === 0 &&
    !String(validationStatus).toUpperCase().includes("MISSING");

  return (
    <div className="banner info" role="status">
      <ShieldCheck size={18} />
      <div>
        <strong>
          Readiness preview: {canContinue ? "ready to save" : "needs attention"}.
        </strong>
        <div className="table-subtext">
          Can I continue?{" "}
          {canContinue
            ? "Yes, save the company draft next."
            : "Not yet. Review the items below first."}
        </div>
        <div className="table-subtext">
          Result: {validationStatus}; setup posture:{" "}
          {preview.readiness_preview.overall_status}; no save:{" "}
          {preview.no_persistence_confirmed ? "confirmed" : "unavailable"}; no
          launch action:{" "}
          {preview.no_live_action_confirmed ? "confirmed" : "unavailable"}.
        </div>
        {firstReadinessCategory ? (
          <div className="table-subtext">
            Why? {firstReadinessCategory.display_label}:{" "}
            {firstReadinessCategory.evidence_summary}
          </div>
        ) : null}
        <ValidationItemList label="Missing evidence" items={missingEvidence} />
        <ValidationItemList label="Blockers" items={blockers} />
        <ValidationItemList label="Warnings" items={warnings} />
        <ValidationItemList label="Safe errors" items={safeErrors} />
        {nextActions.length > 0 ? (
          <div className="table-subtext">
            Next action: {nextActions.join("; ")}
          </div>
        ) : null}
        {preview.guardrails.length > 0 ? (
          <div className="table-subtext">
            Guardrails: {preview.guardrails.slice(0, 4).join(", ")}
          </div>
        ) : null}
      </div>
    </div>
  );
}

function ValidationItemList({
  label,
  items,
}: {
  label: string;
  items: Array<{
    code: string;
    message: string;
    section?: string | null;
    severity: string;
  }>;
}) {
  if (items.length === 0) {
    return null;
  }

  return (
    <div className="table-subtext">
      {label}:{" "}
      {items.map((item) => `${item.code} - ${item.message}`).join("; ")}
    </div>
  );
}

function TextField({
  label,
  value,
  onChange,
  placeholder,
  required = false,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  required?: boolean;
}) {
  const id = useId();

  return (
    <div className="field">
      <label htmlFor={id}>
        {label}
        {required ? " *" : ""}
      </label>
      <input
        className="input"
        id={id}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        required={required}
        type="text"
        value={value}
      />
    </div>
  );
}

function SelectField({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: string[];
}) {
  const id = useId();

  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <select
        className="input"
        id={id}
        onChange={(event) => onChange(event.target.value)}
        value={value}
      >
        {options.map((option) => (
          <option key={option}>{option}</option>
        ))}
      </select>
    </div>
  );
}

function BoundaryCard({
  icon: Icon,
  title,
  copy,
}: {
  icon: typeof Building2;
  title: string;
  copy: string;
}) {
  return (
    <article className="capability-card">
      <div className="capability-icon">
        <Icon size={18} />
      </div>
      <div>
        <div className="capability-title">{title}</div>
        <div className="capability-copy">{copy}</div>
      </div>
      <StatusBadge label="Guardrail" tone="info" />
    </article>
  );
}
