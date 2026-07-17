import { ArrowRight, Building2, CheckCircle2, ClipboardCheck, KeyRound, ShieldCheck, Users } from "lucide-react";
import { Link } from "react-router-dom";
import { useMemo, useState, type FormEvent } from "react";

import {
  recordAdminOnboardingReviewDecision,
  saveAdminOnboardingDraft,
  submitAdminOnboardingDraftForReview,
  validateAdminOnboardingDryRun,
  type AdminOnboardingDraftSaveResponse,
  type AdminOnboardingDryRunValidationResponse,
  type AdminOnboardingReviewDecisionResponse,
  type AdminOnboardingReviewOutcome,
  type AdminOnboardingSubmitForReviewResponse,
} from "../../api/endpoints/adminOnboarding";
import {
  createReferralSaasAccountFromDraft,
  type ReferralSaasAccountMembershipPosture,
  type ReferralSaasAccountCreateFromDraftResponse,
  type ReferralSaasAccountSummary,
} from "../../api/endpoints/referralSaasAccounts";
import {
  useReferralSaasAccountMembershipPosture,
  useReferralSaasAccountResolver,
  useReferralSaasAccountSetupState,
} from "../../api/referralSaasAccountQueries";
import { DataTable } from "../../components/DataTable";
import { ErrorPanel } from "../../components/ErrorPanel";
import { KpiCard } from "../../components/KpiCard";
import { LoadingState } from "../../components/LoadingState";
import { StatusBadge } from "../../components/StatusBadge";
import {
  asArray,
  asRecord,
  formatDisplay,
  getNestedValue,
  getValue,
  statusTone,
  useRefreshContext,
} from "../pageUtils";

const defaultExternalTenantRef = "demo-platform-operator";
const defaultOrganisationRef = "demo-organisation";
const trustedInternalTenantScopeKey = "amplifi.referralSaas.accountSetup.trustedTenantScope";
const defaultTrustedInternalTenantScope = "FNB";
type SetupActionState = "idle" | "loading" | "success" | "error";

const accountChecklist = [
  {
    code: "ACCOUNT_PROFILE",
    label: "Account profile",
    source: "Company onboarding draft",
    next: "Capture organisation profile and primary setup contact.",
  },
  {
    code: "TENANT_LINK",
    label: "Tenant link",
    source: "Existing onboarding readiness projection",
    next: "Resolve external references to an internal tenant before campaign work.",
  },
  {
    code: "MEMBERSHIP",
    label: "Membership and roles",
    source: "User & role setup shell",
    next: "Configure owner, campaign manager, analyst, support, and integration roles.",
  },
  {
    code: "CAMPAIGN_READINESS",
    label: "Campaign readiness",
    source: "Campaign setup workflow",
    next: "Move to campaign setup only after account evidence is ready.",
  },
  {
    code: "REPORTING_BASELINE",
    label: "Reporting baseline",
    source: "Referral SaaS reports",
    next: "Use tenant-safe reports; persisted exports remain future work.",
  },
];

const setupWorkflowLinks = [
  {
    code: "ACCOUNT_PROFILE",
    copy: "Capture the company profile draft used by this Account Setup workflow.",
    label: "Company profile",
    path: "/admin/onboarding/company",
  },
  {
    code: "MEMBERSHIP",
    copy: "Confirm owner, campaign manager, support, analyst, and integration role intent.",
    label: "Users and roles",
    path: "/admin/onboarding/members-roles",
  },
  {
    code: "WEBHOOK_API",
    copy: "Document API and webhook setup intent without creating credentials or sending webhooks.",
    label: "Integration setup",
    path: "/admin/onboarding/webhook-api",
  },
  {
    code: "READINESS",
    copy: "Run the integrated readiness checkpoint before review handoff or campaign testing.",
    label: "Readiness checkpoint",
    path: "/admin/referral-saas/account-setup",
  },
  {
    code: "REVIEW_HANDOFF",
    copy: "Save, submit, and review the setup draft before the gated account creation path.",
    label: "Review handoff",
  },
  {
    code: "CAMPAIGN_READINESS",
    copy: "Continue only when setup evidence is clear enough for referral testing.",
    label: "Campaign setup",
    path: "/admin/referral-saas/campaigns",
  },
];

export function ReferralSaasAccountSetupPage() {
  const { refreshKey } = useRefreshContext();
  const [draftExternalTenantRef, setDraftExternalTenantRef] = useState(defaultExternalTenantRef);
  const [draftOrganisationRef, setDraftOrganisationRef] = useState(defaultOrganisationRef);
  const [appliedExternalTenantRef, setAppliedExternalTenantRef] = useState(defaultExternalTenantRef);
  const [appliedOrganisationRef, setAppliedOrganisationRef] = useState(defaultOrganisationRef);
  const [validationState, setValidationState] = useState<SetupActionState>("idle");
  const [validationResponse, setValidationResponse] = useState<AdminOnboardingDryRunValidationResponse | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [draftState, setDraftState] = useState<SetupActionState>("idle");
  const [draftResponse, setDraftResponse] = useState<AdminOnboardingDraftSaveResponse | null>(null);
  const [draftError, setDraftError] = useState<string | null>(null);
  const [submitState, setSubmitState] = useState<SetupActionState>("idle");
  const [submitResponse, setSubmitResponse] = useState<AdminOnboardingSubmitForReviewResponse | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [reviewReason, setReviewReason] = useState("");
  const [reviewState, setReviewState] = useState<SetupActionState>("idle");
  const [reviewResponse, setReviewResponse] = useState<AdminOnboardingReviewDecisionResponse | null>(null);
  const [reviewError, setReviewError] = useState<string | null>(null);
  const [createState, setCreateState] = useState<SetupActionState>("idle");
  const [createResponse, setCreateResponse] = useState<ReferralSaasAccountCreateFromDraftResponse | null>(null);
  const [createError, setCreateError] = useState<string | null>(null);
  const [accountRefreshKey, setAccountRefreshKey] = useState(0);
  const { data, error, isLoading } = useReferralSaasAccountSetupState(
    appliedExternalTenantRef,
    appliedOrganisationRef,
    refreshKey,
  );
  const {
    data: accountResolution,
    error: accountResolutionError,
    isLoading: accountResolutionLoading,
  } = useReferralSaasAccountResolver(appliedExternalTenantRef, refreshKey + accountRefreshKey);
  const scopeChanged =
    draftExternalTenantRef.trim() !== appliedExternalTenantRef ||
    draftOrganisationRef.trim() !== appliedOrganisationRef;
  const {
    data: membershipPostureResponse,
    error: membershipPostureError,
    isLoading: membershipPostureLoading,
  } = useReferralSaasAccountMembershipPosture(
    appliedExternalTenantRef,
    Boolean(accountResolution?.account && !scopeChanged),
    refreshKey + accountRefreshKey,
  );
  const canCheckScope = Boolean(draftExternalTenantRef.trim() && draftOrganisationRef.trim() && scopeChanged);

  const readiness = asRecord(data?.readiness);
  const summary = asRecord(getNestedValue(readiness, ["summary"], {}));
  const categories = asArray(getNestedValue(readiness, ["categories"], []));
  const guardrails = asArray(
    (getNestedValue(data?.onboarding_state, ["guardrails"], []) as unknown[]).map((guardrail) => ({
      name: guardrail,
    })),
  );
  const redactions = asArray(
    (getNestedValue(data?.onboarding_state, ["redactions"], []) as unknown[]).map((redaction) => ({
      name: redaction,
    })),
  );
  const overallStatus = formatDisplay(getNestedValue(readiness, ["overall_status"], "pending"));
  const readyCountValue = toCount(getNestedValue(summary, ["ready_count"], 0));
  const blockedCountValue = toCount(getNestedValue(summary, ["blocked_count"], 0));
  const missingEvidenceCountValue = toCount(getNestedValue(summary, ["missing_evidence_count"], 0));
  const goLiveDisabledCountValue = toCount(getNestedValue(summary, ["go_live_disabled_count"], 0));
  const readyCount = formatDisplay(readyCountValue);
  const blockedCount = formatDisplay(blockedCountValue);
  const missingEvidenceCount = formatDisplay(missingEvidenceCountValue);
  const goLiveDisabledCount = formatDisplay(goLiveDisabledCountValue);
  const needsSetupWork = blockedCountValue > 0 || missingEvidenceCountValue > 0;
  const durableAccount = accountResolution?.account;
  const membershipPosture = membershipPostureResponse?.membershipPosture;
  const membershipPostureStatus = getMembershipPostureStatus(
    membershipPosture,
    membershipPostureLoading,
    membershipPostureError,
    Boolean(durableAccount),
  );
  const durableAccountStatus = getDurableAccountStatus(
    Boolean(durableAccount),
    accountResolutionLoading,
    accountResolutionError,
  );
  const nextStep = getAccountSetupNextStep(scopeChanged, needsSetupWork);
  const setupSections = useMemo(
    () => buildReferralSaasSetupSections(appliedExternalTenantRef, appliedOrganisationRef),
    [appliedExternalTenantRef, appliedOrganisationRef],
  );
  const actionScopeReady = Boolean(appliedExternalTenantRef && appliedOrganisationRef && !scopeChanged);
  const draftIdempotencyKey = useMemo(
    () => ["referral-saas-account-setup-draft", appliedExternalTenantRef, appliedOrganisationRef].join(":"),
    [appliedExternalTenantRef, appliedOrganisationRef],
  );
  const validateIdempotencyKey = useMemo(
    () => ["referral-saas-account-setup-validate", appliedExternalTenantRef, appliedOrganisationRef].join(":"),
    [appliedExternalTenantRef, appliedOrganisationRef],
  );
  const submitIdempotencyKey = useMemo(
    () => ["referral-saas-account-setup-submit", draftResponse?.draft_ref || "missing-draft"].join(":"),
    [draftResponse?.draft_ref],
  );
  const reviewIdempotencyKey = useMemo(
    () => [
      "referral-saas-account-setup-review",
      submitResponse?.draft_ref || "missing-draft",
      submitResponse?.draft_version ?? "missing-version",
    ].join(":"),
    [submitResponse?.draft_ref, submitResponse?.draft_version],
  );
  const createAccountIdempotencyKey = useMemo(
    () => ["referral-saas-account-setup-create", reviewResponse?.draft_ref || "missing-draft"].join(":"),
    [reviewResponse?.draft_ref],
  );
  const canSubmitForReview = Boolean(actionScopeReady && draftResponse?.draft_ref && draftState === "success");
  const canRecordReview = Boolean(
    actionScopeReady &&
      submitResponse?.draft_ref &&
      submitResponse.draft_status === "READY_FOR_REVIEW" &&
      submitState === "success",
  );
  const canCreateAccount = Boolean(
    actionScopeReady &&
      reviewResponse?.draft_ref &&
      reviewResponse.review_outcome === "APPROVED_FOR_INTERNAL_REVIEW" &&
      reviewState === "success" &&
      !durableAccount,
  );
  const workflowSteps = setupWorkflowLinks.map((step) =>
    resolveWorkflowStep(step, categories, scopeChanged, needsSetupWork),
  );
  const resolvedRows = accountChecklist.map((item) => {
    const matchingCategory = categories.find((category) => categoryMatches(category, item));
    const status = formatDisplay(
      getNestedValue(matchingCategory, ["safe_display_status", "label"], getNestedValue(matchingCategory, ["status"], "Pending")),
    );

    return {
      ...item,
      status,
      evidence: formatDisplay(getNestedValue(matchingCategory, ["evidence_summary"], item.next)),
      blocker: formatDisplay(getNestedValue(matchingCategory, ["blockers", "0"], "-")),
    };
  });

  function submitScope(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextExternalTenantRef = draftExternalTenantRef.trim();
    const nextOrganisationRef = draftOrganisationRef.trim();
    if (!nextExternalTenantRef || !nextOrganisationRef) {
      return;
    }
    setAppliedExternalTenantRef(nextExternalTenantRef);
    setAppliedOrganisationRef(nextOrganisationRef);
    resetSetupActionState();
  }

  function resetSetupActionState() {
    setValidationState("idle");
    setValidationResponse(null);
    setValidationError(null);
    setDraftState("idle");
    setDraftResponse(null);
    setDraftError(null);
    setSubmitState("idle");
    setSubmitResponse(null);
    setSubmitError(null);
    setReviewState("idle");
    setReviewResponse(null);
    setReviewError(null);
    setCreateState("idle");
    setCreateResponse(null);
    setCreateError(null);
  }

  async function handleValidateSetupDraft() {
    if (!actionScopeReady || validationState === "loading") {
      return;
    }
    setValidationState("loading");
    setValidationResponse(null);
    setValidationError(null);
    try {
      const response = await validateAdminOnboardingDryRun({
        external_tenant_ref: appliedExternalTenantRef,
        organisation_ref: appliedOrganisationRef,
        validation_scope: [
          "company",
          "producer_sponsor",
          "distributor",
          "member_role",
          "campaign_opportunity",
          "webhook_api",
        ],
        idempotency_key: validateIdempotencyKey,
        correlation_id: "referral-saas-account-setup-validate",
        sections: setupSections,
      });
      setValidationResponse(response);
      setValidationState("success");
    } catch {
      setValidationError("Validation is unavailable. No draft was saved and no live action was taken.");
      setValidationState("error");
    }
  }

  async function handleSaveSetupDraft() {
    if (!actionScopeReady || draftState === "loading") {
      return;
    }
    setDraftState("loading");
    setDraftResponse(null);
    setDraftError(null);
    setSubmitState("idle");
    setSubmitResponse(null);
    setSubmitError(null);
    setReviewState("idle");
    setReviewResponse(null);
    setReviewError(null);
    setCreateState("idle");
    setCreateResponse(null);
    setCreateError(null);
    try {
      const response = await saveAdminOnboardingDraft({
        external_tenant_ref: appliedExternalTenantRef,
        organisation_ref: appliedOrganisationRef,
        idempotency_key: draftIdempotencyKey,
        correlation_id: "referral-saas-account-setup-draft",
        sections: setupSections,
      });
      setDraftResponse(response);
      setDraftState("success");
    } catch (error) {
      setDraftError(safeActionError(error, "Draft save is unavailable. No account was created and no live action was taken."));
      setDraftState("error");
    }
  }

  async function handleSubmitSetupDraft() {
    if (!canSubmitForReview || !draftResponse?.draft_ref || submitState === "loading") {
      return;
    }
    setSubmitState("loading");
    setSubmitResponse(null);
    setSubmitError(null);
    setReviewState("idle");
    setReviewResponse(null);
    setReviewError(null);
    setCreateState("idle");
    setCreateResponse(null);
    setCreateError(null);
    try {
      const response = await submitAdminOnboardingDraftForReview(draftResponse.draft_ref, {
        external_tenant_ref: appliedExternalTenantRef,
        organisation_ref: appliedOrganisationRef,
        expected_version: draftResponse.draft_version ?? 1,
        idempotency_key: submitIdempotencyKey,
        correlation_id: "referral-saas-account-setup-submit-review",
      });
      setSubmitResponse(response);
      setSubmitState("success");
    } catch (error) {
      setSubmitError(safeActionError(error, "Submit for review is unavailable. No approval or live action was taken."));
      setSubmitState("error");
    }
  }

  async function handleReviewDecision(outcome: AdminOnboardingReviewOutcome) {
    if (!canRecordReview || !submitResponse?.draft_ref || reviewState === "loading") {
      return;
    }
    const reason = reviewReason.trim();
    if (!reason) {
      setReviewError("A bounded review reason is required. No approval, go-live, or live action was taken.");
      setReviewState("error");
      return;
    }
    setReviewState("loading");
    setReviewResponse(null);
    setReviewError(null);
    try {
      const response = await recordAdminOnboardingReviewDecision(submitResponse.draft_ref, {
        external_tenant_ref: appliedExternalTenantRef,
        organisation_ref: appliedOrganisationRef,
        expected_version: submitResponse.draft_version ?? 1,
        idempotency_key: `${reviewIdempotencyKey}:${outcome}`,
        review_outcome: outcome,
        reason_category: outcome === "BLOCKED" ? "REVIEW_BLOCKER" : "OPERATOR_REVIEW",
        reason,
        correlation_id: "referral-saas-account-setup-review-decision",
      });
      setReviewResponse(response);
      setReviewState("success");
      setCreateState("idle");
      setCreateResponse(null);
      setCreateError(null);
    } catch (error) {
      setReviewError(safeActionError(error, "Review decision is unavailable. No approval, go-live, or live action was taken."));
      setReviewState("error");
    }
  }

  async function handleCreateAccountFoundation() {
    if (!canCreateAccount || !reviewResponse?.draft_ref || createState === "loading") {
      return;
    }
    setCreateState("loading");
    setCreateResponse(null);
    setCreateError(null);
    try {
      const response = await createReferralSaasAccountFromDraft({
        draftRef: reviewResponse.draft_ref,
        internalTenantCode: getTrustedInternalTenantScope(),
        idempotencyKey: createAccountIdempotencyKey,
      });
      setCreateResponse(response);
      setCreateState("success");
      setAccountRefreshKey((current) => current + 1);
    } catch (error) {
      setCreateError(safeAccountCreateError(error));
      setCreateState("error");
    }
  }

  return (
    <>
      <section className="page-header">
        <div>
          <div className="page-kicker">Referral SaaS - Account Setup</div>
          <h1 className="page-title">Account setup workflow</h1>
          <p className="page-copy">
            Work through company setup, roles, integration intent, readiness,
            and review handoff before testing campaigns, links, attribution, or
            reports.
          </p>
        </div>
        <StatusBadge label={overallStatus} tone={statusTone(overallStatus)} />
      </section>

      {isLoading ? <LoadingState label="Loading Referral SaaS account setup" /> : null}
      {error ? <ErrorPanel error={error} /> : null}
      {!isLoading && !error ? (
        <>
          <section className="panel journey-panel" aria-labelledby="account-setup-workflow-heading">
            <div className="panel-header">
              <div>
                <h2 className="panel-title" id="account-setup-workflow-heading">
                  Guided setup path
                </h2>
                <div className="panel-subtitle">
                  Follow the steps in order. Readiness is one checkpoint inside setup, not the whole workflow.
                </div>
              </div>
              <StatusBadge label={nextStep.badge} tone={nextStep.tone} />
            </div>
            <div className="panel-body">
              <div className="journey-summary">
                <div>
                  <div className="route-name">{nextStep.title}</div>
                  <div className="route-path">{nextStep.copy}</div>
                </div>
                <StatusBadge label={nextStep.actionLabel} tone={nextStep.tone} />
              </div>

              <ol className="journey-steps account-setup-journey">
                {workflowSteps.map((step, index) => (
                  <li className={`journey-step ${step.state}`} key={step.label}>
                    <div className="journey-step-index">
                      <span>{index + 1}</span>
                      <StatusBadge label={step.badge} tone={step.tone} />
                    </div>
                    <div>
                      <div className="journey-step-title">{step.label}</div>
                      <p className="journey-step-copy">{step.copy}</p>
                    </div>
                    <div className="journey-step-area">
                      <span>{step.actionLabel}</span>
                      {step.path ? <Link to={step.path}>{step.actionText}</Link> : <strong>{step.actionText}</strong>}
                    </div>
                  </li>
                ))}
              </ol>

              <div className="account-setup-action-grid">
                <form className="account-setup-scope-form" onSubmit={submitScope}>
                  <div>
                    <h3 className="panel-title">Step 1 action: check account setup</h3>
                    <p className="journey-step-copy">
                      Confirm the account references, load readiness evidence, and resolve any durable account already created for setup.
                    </p>
                  </div>
                  <label className="field">
                    <span>External tenant ref</span>
                    <input
                      className="input"
                      onChange={(event) => setDraftExternalTenantRef(event.target.value)}
                      value={draftExternalTenantRef}
                    />
                  </label>
                  <label className="field">
                    <span>Organisation ref</span>
                    <input
                      className="input"
                      onChange={(event) => setDraftOrganisationRef(event.target.value)}
                      value={draftOrganisationRef}
                    />
                  </label>
                  <button className="button" disabled={!canCheckScope} type="submit">
                    Check setup
                  </button>
                  <StatusBadge label={scopeChanged ? "Changes not checked" : "Loaded"} tone={scopeChanged ? "warning" : "success"} />
                  <div className="route-item">
                    <div>
                      <div className="route-name">Durable account resolution</div>
                      <div className="route-path">{durableAccountStatus.copy}</div>
                      {durableAccount ? (
                        <div className="table-subtext">
                          {durableAccount.accountName || durableAccount.accountCode || "Account"} -{" "}
                          {durableAccount.accountStatus || "status unavailable"} - tenant link{" "}
                          {durableAccount.tenantLinkStatus || "unavailable"}
                        </div>
                      ) : null}
                    </div>
                    <StatusBadge label={durableAccountStatus.label} tone={durableAccountStatus.tone} />
                  </div>
                  <div className="route-item">
                    <div>
                      <div className="route-name">Membership access check</div>
                      <div className="route-path">{membershipPostureStatus.copy}</div>
                      {membershipPosture ? (
                        <div className="table-subtext">
                          {membershipPosture.activeCount} active, {membershipPosture.invitedCount} invited,{" "}
                          {membershipPosture.totalMemberships} total memberships. Invitations stay outside Account Setup.
                        </div>
                      ) : null}
                    </div>
                    <StatusBadge label={membershipPostureStatus.label} tone={membershipPostureStatus.tone} />
                  </div>
                </form>
                <div className="route-list">
                  <div className="route-item">
                    <div>
                      <div className="route-name">Step 2 action: complete setup evidence</div>
                      <div className="route-path">
                        Use company, role, and integration setup only when the readiness check shows missing evidence.
                      </div>
                    </div>
                    <ClipboardCheck size={18} />
                  </div>
                  <SetupLink to="/admin/onboarding/company" title="Company profile" copy="Open Step 1 and save the company setup draft." />
                  <SetupLink to="/admin/onboarding/members-roles" title="User and role setup" copy="Confirm owner, campaign manager, support, analyst, and integration roles." />
                  <SetupLink to="/admin/onboarding/webhook-api" title="Integration setup" copy="Document API and webhook setup intent without creating credentials." />
                </div>
                <div className="route-list">
                  <div className="route-item">
                    <div>
                      <div className="route-name">Step 3 action: move to campaign setup</div>
                      <div className="route-path">
                        Continue only after account setup evidence is checked and blockers are understood.
                      </div>
                    </div>
                    <ArrowRight size={18} />
                  </div>
                  <SetupLink
                    to="/admin/referral-saas/campaigns"
                    title="Campaign readiness"
                    copy="Check campaign setup evidence, blockers, warnings, and launch posture."
                  />
                </div>
              </div>
            </div>
          </section>

          <section className="panel" aria-labelledby="setup-draft-actions-heading">
            <div className="panel-header">
              <div>
                <h2 className="panel-title" id="setup-draft-actions-heading">
                  Setup draft actions
                </h2>
                <div className="panel-subtitle">
                  Save setup intent, validate evidence, submit for review, and record internal review without account creation.
                </div>
              </div>
              <StatusBadge label={actionScopeReady ? "Checked scope" : "Check scope first"} tone={actionScopeReady ? "success" : "warning"} />
            </div>
            <div className="panel-body route-list">
              <div className="action-button-row">
                <button className="button secondary" disabled={!actionScopeReady || validationState === "loading"} onClick={handleValidateSetupDraft} type="button">
                  {validationState === "loading" ? "Validating setup" : "Validate setup"}
                </button>
                <button className="button" disabled={!actionScopeReady || draftState === "loading"} onClick={handleSaveSetupDraft} type="button">
                  {draftState === "loading" ? "Saving draft" : "Save setup draft"}
                </button>
                <button className="button secondary" disabled={!canSubmitForReview || submitState === "loading"} onClick={handleSubmitSetupDraft} type="button">
                  {submitState === "loading" ? "Submitting review" : "Submit for review"}
                </button>
              </div>
              <div className="field">
                <label htmlFor="referral-saas-review-reason">Review reason</label>
                <textarea
                  className="input"
                  disabled={!canRecordReview}
                  id="referral-saas-review-reason"
                  onChange={(event) => setReviewReason(event.target.value)}
                  placeholder="Bounded internal review reason"
                  rows={3}
                  value={reviewReason}
                />
              </div>
              <div className="action-button-row">
                <button
                  className="button secondary"
                  disabled={!canRecordReview || reviewState === "loading"}
                  onClick={() => handleReviewDecision("APPROVED_FOR_INTERNAL_REVIEW")}
                  type="button"
                >
                  Accept internal review
                </button>
                <button
                  className="button secondary"
                  disabled={!canRecordReview || reviewState === "loading"}
                  onClick={() => handleReviewDecision("BLOCKED")}
                  type="button"
                >
                  Mark review blocked
                </button>
              </div>
              <div className="table-subtext">
                These actions use existing guarded onboarding APIs. They do not invite users, create credentials, deliver webhooks, activate campaigns, enable go-live, or move money.
              </div>
              <SetupActionResult
                createError={createError}
                createResponse={createResponse}
                draftResponse={draftResponse}
                draftError={draftError}
                reviewError={reviewError}
                reviewResponse={reviewResponse}
                submitError={submitError}
                submitResponse={submitResponse}
                validationError={validationError}
                validationResponse={validationResponse}
              />
              <div className="route-item">
                <div>
                  <div className="route-name">Final setup action: create account foundation</div>
                  <div className="route-path">
                    Available only after internal review is accepted. It creates the durable account foundation and external reference, not users, campaigns, activation, go-live, or money movement.
                  </div>
                  {durableAccount ? (
                    <div className="table-subtext">
                      Account already resolves as {formatAccountSummary(durableAccount)}. Continue from the resolved account context.
                    </div>
                  ) : null}
                </div>
                <button
                  className="button"
                  disabled={!canCreateAccount || createState === "loading"}
                  onClick={handleCreateAccountFoundation}
                  type="button"
                >
                  {createState === "loading" ? "Creating account" : "Create account foundation"}
                </button>
              </div>
            </div>
          </section>

          <section className="grid-4">
            <KpiCard label="Ready setup gates" value={readyCount} footnote="Can support testing" icon={CheckCircle2} />
            <KpiCard label="Blocked setup gates" value={blockedCount} footnote="Fix before moving on" icon={ShieldCheck} />
            <KpiCard label="Evidence gaps" value={missingEvidenceCount} footnote="Missing setup proof" icon={Building2} />
            <KpiCard label="Launch actions here" value="0" footnote={`${goLiveDisabledCount} go-live blocker shown`} icon={KeyRound} />
          </section>

          <section className="grid-2">
            <div className="panel">
              <div className="panel-header">
                <div>
                  <h2 className="panel-title">Setup checklist</h2>
                  <div className="panel-subtitle">
                    Productized setup-readiness gates mapped to existing onboarding evidence.
                  </div>
                </div>
              </div>
              <DataTable
                rows={resolvedRows}
                emptyText="No setup checklist rows returned."
                columns={[
                  {
                    key: "gate",
                    header: "Gate",
                    render: (row) => (
                      <>
                        <span className="mono">{row.code}</span>
                        <div className="table-subtext">{row.label}</div>
                      </>
                    ),
                  },
                  {
                    key: "status",
                    header: "Status",
                    render: (row) => <StatusBadge label={row.status} tone={statusTone(row.status)} />,
                  },
                  {
                    key: "evidence",
                    header: "Evidence",
                    render: (row) => <span className="table-subtext">{row.evidence}</span>,
                  },
                ]}
              />
            </div>

            <div className="panel">
              <div className="panel-header">
                <div>
                  <h2 className="panel-title">Launch guardrails</h2>
                  <div className="panel-subtitle">
                    This surface is a setup/readiness wrapper, not an account lifecycle API.
                  </div>
                </div>
                <StatusBadge label="No live action" tone="warning" />
              </div>
              <div className="panel-body route-list">
                <div className="route-item">
                  <div>
                    <div className="route-name">Durable account resolver is read-only</div>
                    <div className="route-path">
                      Step 1 resolves existing account context when available, but it does not create accounts, tenants, users, memberships, or invitations.
                    </div>
                  </div>
                  <StatusBadge label={durableAccount ? "Resolved" : "Setup mode"} tone={durableAccount ? "success" : "info"} />
                </div>
                <div className="route-item">
                  <div>
                    <div className="route-name">Account creation is gated</div>
                    <div className="route-path">
                      Account foundation creation is available only after setup draft save, submit, and internal review. It does not create tenants, users, memberships, invitations, campaigns, go-live, or money movement.
                    </div>
                  </div>
                  <StatusBadge label={canCreateAccount ? "Ready" : durableAccount ? "Resolved" : "Gated"} tone={canCreateAccount || durableAccount ? "success" : "warning"} />
                </div>
                <div className="route-item">
                  <div>
                    <div className="route-name">Internal tenant identifier hidden</div>
                    <div className="route-path">
                      Operators work from external references. Membership posture is read-only here, and internal tenant identifiers stay redacted.
                    </div>
                  </div>
                  <StatusBadge label="Redacted" tone="success" />
                </div>
                <div className="route-item">
                  <div>
                    <div className="route-name">Membership writes are outside setup</div>
                    <div className="route-path">
                      This page can show active or missing membership evidence, but it cannot invite users, assign seats, or change auth claims.
                    </div>
                  </div>
                  <StatusBadge
                    label={membershipPosture?.noInviteDeliveryConfirmed ? "Read-only" : "Guarded"}
                    tone={membershipPosture?.noInviteDeliveryConfirmed ? "success" : "warning"}
                  />
                </div>
              </div>
            </div>
          </section>

          <section className="grid-2">
            <div className="panel">
              <div className="panel-header">
                <div>
                  <h2 className="panel-title">Current readiness evidence</h2>
                  <div className="panel-subtitle">Safe categories returned by the onboarding projection.</div>
                </div>
                <StatusBadge label={`${categories.length} categories`} tone={categories.length ? "info" : "neutral"} />
              </div>
              <div className="panel-body route-list">
                {categories.length ? (
                  categories.map((category) => {
                    const label = getValue(category, ["display_label", "category"]);
                    const status = formatDisplay(
                      getNestedValue(category, ["safe_display_status", "label"], getNestedValue(category, ["status"])),
                    );
                    return (
                      <div className="route-item" key={getValue(category, ["category"])}>
                        <div>
                          <div className="route-name">{label}</div>
                          <div className="route-path">{getValue(category, ["evidence_summary"])}</div>
                          <div className="table-subtext">{getValue(category, ["next_actions", "0"], "Review setup evidence.")}</div>
                        </div>
                        <StatusBadge label={status} tone={statusTone(status)} />
                      </div>
                    );
                  })
                ) : (
                  <div className="empty-state">No account readiness categories returned.</div>
                )}
              </div>
            </div>

            <div className="panel">
              <div className="panel-header">
                <div>
                  <h2 className="panel-title">How to read the evidence</h2>
                  <div className="panel-subtitle">Use the checklist and categories to decide whether to complete setup actions or continue.</div>
                </div>
              </div>
              <div className="panel-body route-list">
                <div className="route-item">
                  <div>
                    <div className="route-name">Blocked or missing evidence</div>
                    <div className="route-path">Return to Step 2 and complete the setup action that matches the blocker.</div>
                  </div>
                  <StatusBadge label="Fix" tone="warning" />
                </div>
                <div className="route-item">
                  <div>
                    <div className="route-name">Ready enough for testing</div>
                    <div className="route-path">Continue to Step 3 and check campaign setup readiness before testing links and codes.</div>
                  </div>
                  <StatusBadge label="Continue" tone="success" />
                </div>
              </div>
            </div>
          </section>

          <section className="grid-2">
            <div className="panel">
              <div className="panel-header">
                <div>
                  <h2 className="panel-title">Guardrails</h2>
                  <div className="panel-subtitle">Boundaries returned by the current onboarding projection.</div>
                </div>
              </div>
              <DataTable
                rows={guardrails}
                emptyText="No guardrails returned."
                columns={[
                  {
                    key: "guardrail",
                    header: "Guardrail",
                    render: (row) => <span className="mono">{getValue(row, ["name"])}</span>,
                  },
                ]}
              />
            </div>

            <div className="panel">
              <div className="panel-header">
                <div>
                  <h2 className="panel-title">Redactions</h2>
                  <div className="panel-subtitle">Fields hidden from the Referral SaaS setup surface.</div>
                </div>
              </div>
              <DataTable
                rows={redactions}
                emptyText="No redactions returned."
                columns={[
                  {
                    key: "redaction",
                    header: "Redaction",
                    render: (row) => <span className="mono">{getValue(row, ["name"])}</span>,
                  },
                ]}
              />
            </div>
          </section>
        </>
      ) : null}
    </>
  );
}

function categoryMatches(category: Record<string, unknown>, item: { code: string; label: string }) {
  const haystack = [
    getValue(category, ["category"], ""),
    getValue(category, ["display_label"], ""),
    getValue(category, ["evidence_summary"], ""),
  ]
    .join(" ")
    .toLowerCase();
  return item.code
    .toLowerCase()
    .split("_")
    .some((part) => haystack.includes(part)) || haystack.includes(item.label.toLowerCase());
}

function toCount(value: unknown) {
  const count = Number(value);
  return Number.isFinite(count) ? count : 0;
}

function getDurableAccountStatus(hasAccount: boolean, isLoading: boolean, error: unknown) {
  if (isLoading) {
    return {
      copy: "Checking whether the external tenant reference maps to a durable Referral SaaS account.",
      label: "Checking",
      tone: "info" as const,
    };
  }
  if (hasAccount) {
    return {
      copy: "This setup scope resolves to an existing durable account. Continue setup from this account context.",
      label: "Resolved",
      tone: "success" as const,
    };
  }

  const status = typeof error === "object" && error && "status" in error ? Number((error as { status?: number }).status) : null;
  if (status === 404) {
    return {
      copy: "No durable account was found for this reference yet. Continue the Account Setup draft path.",
      label: "Setup draft",
      tone: "warning" as const,
    };
  }
  if (error) {
    return {
      copy: "The account resolver could not safely resolve this reference. Check the reference or resolver guardrails before continuing.",
      label: "Resolver blocked",
      tone: "warning" as const,
    };
  }
  return {
    copy: "No durable account check has returned yet. Run Step 1 before moving to setup actions.",
    label: "Unchecked",
    tone: "neutral" as const,
  };
}

function getMembershipPostureStatus(
  posture: ReferralSaasAccountMembershipPosture | undefined,
  isLoading: boolean,
  error: unknown,
  hasAccount: boolean,
) {
  if (!hasAccount) {
    return {
      copy: "Membership access is checked after Step 1 resolves a durable account.",
      label: "Wait for account",
      tone: "neutral" as const,
    };
  }
  if (isLoading) {
    return {
      copy: "Checking read-only membership posture for this account.",
      label: "Checking",
      tone: "info" as const,
    };
  }
  if (error) {
    return {
      copy: "Membership posture is unavailable. Keep setup actions bounded until access evidence can be checked.",
      label: "Unavailable",
      tone: "warning" as const,
    };
  }

  const actorStatus = posture?.currentActor?.status || "NO_MEMBERSHIP_EVIDENCE";
  if (actorStatus === "MEMBERSHIP_CONFIRMED") {
    return {
      copy: "The current actor has active account membership evidence. Continue setup actions in order.",
      label: "Membership active",
      tone: "success" as const,
    };
  }
  if (actorStatus === "INVITED_NOT_ACTIVE") {
    return {
      copy: "The current actor has invited membership evidence, but it is not active. Complete access activation outside this Account Setup page.",
      label: "Invited only",
      tone: "warning" as const,
    };
  }
  if (actorStatus === "MEMBERSHIP_NOT_USABLE") {
    return {
      copy: "The current actor membership evidence is suspended or disabled. Resolve account access outside this Account Setup page.",
      label: "Blocked access",
      tone: "warning" as const,
    };
  }

  return {
    copy: "No active account membership evidence matched the current actor yet. This page remains a read-only setup wrapper for access posture.",
    label: "No membership",
    tone: "warning" as const,
  };
}

function getAccountSetupNextStep(scopeChanged: boolean, needsSetupWork: boolean) {
  if (scopeChanged) {
    return {
      actionLabel: "Step 1",
      badge: "Check changes",
      copy: "You changed the account references. Click Check readiness before using the setup or campaign actions.",
      title: "Do this next: confirm the account scope",
      tone: "warning" as const,
    };
  }
  if (needsSetupWork) {
    return {
      actionLabel: "Step 2",
      badge: "Fix blockers",
      copy: "The account setup readiness check is loaded, but it is not ready yet. Use the Step 2 actions to fill the missing setup evidence.",
      title: "Do this next: complete setup actions",
      tone: "warning" as const,
    };
  }
  return {
    actionLabel: "Step 3",
    badge: "Ready",
    copy: "The account setup readiness check has no blocker count. Continue to campaign setup readiness before testing links and attribution.",
    title: "Do this next: continue to campaign setup",
    tone: "success" as const,
  };
}

function resolveWorkflowStep(
  step: (typeof setupWorkflowLinks)[number],
  categories: Record<string, unknown>[],
  scopeChanged: boolean,
  needsSetupWork: boolean,
) {
  const category = categories.find((item) => getValue(item, ["category"], "") === step.code);
  const status = formatDisplay(
    getNestedValue(category, ["safe_display_status", "label"], getNestedValue(category, ["status"], "")),
  );
  const ready = status === "READY" || status === "Ready";
  const blocked = [
    "BLOCKED",
    "MISSING_EVIDENCE",
    "NEEDS_EVIDENCE",
    "NEEDS_ATTENTION",
    "Blocked",
    "Missing evidence",
    "Needs evidence",
  ].includes(status);

  if (step.code === "READINESS") {
    return {
      ...step,
      actionLabel: "Current checkpoint",
      actionText: scopeChanged ? "Check readiness" : "Readiness loaded",
      badge: scopeChanged ? "Check" : needsSetupWork ? "Active" : "Ready",
      state: scopeChanged ? "blocked" : needsSetupWork ? "current" : "done",
      tone: scopeChanged ? ("warning" as const) : needsSetupWork ? ("info" as const) : ("success" as const),
    };
  }

  if (step.code === "REVIEW_HANDOFF") {
    return {
      ...step,
      actionLabel: "Review action",
      actionText: "Complete draft review",
      badge: needsSetupWork || scopeChanged ? "Wait" : "Review",
      state: "review",
      tone: "warning" as const,
    };
  }

  if (step.code === "CAMPAIGN_READINESS") {
    return {
      ...step,
      actionLabel: "Next product step",
      actionText: "Open campaign readiness",
      badge: needsSetupWork || scopeChanged ? "Wait" : "Next",
      state: needsSetupWork || scopeChanged ? "blocked" : "current",
      tone: needsSetupWork || scopeChanged ? ("neutral" as const) : ("success" as const),
    };
  }

  return {
    ...step,
    actionLabel: "Setup action",
    actionText: `Open ${step.label.toLowerCase()}`,
    badge: ready ? "Ready" : blocked ? "Fix" : "Check",
    state: ready ? "done" : blocked ? "blocked" : "current",
    tone: ready ? ("success" as const) : blocked ? ("warning" as const) : ("info" as const),
  };
}

function buildReferralSaasSetupSections(externalTenantRef: string, organisationRef: string) {
  const producerRef = `${organisationRef}-producer`;
  const sponsorRef = `${organisationRef}-sponsor`;
  const distributorRef = `${organisationRef}-distributor`;
  const campaignCode = `${organisationRef}-setup-campaign`;
  const opportunityRef = `${organisationRef}-setup-opportunity`;
  const adminContact = "setup-owner@example.test";

  return {
    company: {
      organisation_name: `${organisationRef} Referral SaaS setup`,
      external_tenant_ref: externalTenantRef,
      organisation_ref: organisationRef,
      country: "South Africa",
      organisation_type: "Referral SaaS customer",
      industry: "Referral management and campaign attribution",
      admin_contact: adminContact,
      intended_role: "Referral SaaS admin",
    },
    producer_sponsor: {
      producer_sponsor_name: `${organisationRef} sponsor setup`,
      external_tenant_ref: externalTenantRef,
      producer_ref: producerRef,
      sponsor_ref: sponsorRef,
      organisation_ref: organisationRef,
      industry: "Referral management and campaign attribution",
      funding_model_intention: "No value transfer during account setup",
      admin_contact: adminContact,
      campaign_opportunity_role: "Referral SaaS sponsor owner",
    },
    distributor: {
      distributor_name: `${organisationRef} referral distribution setup`,
      external_tenant_ref: externalTenantRef,
      distributor_ref: distributorRef,
      organisation_ref: organisationRef,
      channel_type: "Referral SaaS direct",
      market_country: "South Africa",
      admin_contact: adminContact,
      distribution_model: "Referral management and campaign attribution",
      campaign_opportunity_participation: "Referral testing after account setup",
    },
    member_role: {
      organisation_ref: organisationRef,
      external_tenant_ref: externalTenantRef,
      user_email: adminContact,
      display_name: "Referral SaaS setup owner",
      role_family: "Account setup admin",
      participant_type: "Platform operator",
      access_scope: "Referral SaaS account setup",
      invite_status: "Draft intent only",
    },
    campaign_opportunity: {
      organisation_ref: organisationRef,
      producer_ref: producerRef,
      sponsor_ref: sponsorRef,
      campaign_code: campaignCode,
      opportunity_ref: opportunityRef,
      campaign_name: `${organisationRef} setup readiness campaign`,
      market_country: "South Africa",
      distribution_model: "Referral SaaS direct",
      eligible_distributor_type: "Referral partner",
      intended_outcome_event: "REFERRED_CUSTOMER_VERIFIED",
      reward_commission_policy_intention: "No reward or commission activation during account setup",
      funding_model_intention: "No value transfer during account setup",
      go_live_target_status: "GO_LIVE_DISABLED",
      link_code_intent: "Issue referral links or codes after account setup readiness",
    },
    webhook_api: {
      organisation_ref: organisationRef,
      external_tenant_ref: externalTenantRef,
      integration_owner_contact: "integration-owner@example.test",
      api_environment_intention: "Sandbox integration intent",
      callback_url_placeholder: "https://example.invalid/referral-saas/webhook-placeholder",
      selected_webhook_event_categories: ["referral", "campaign_attribution", "progress"],
      intended_authentication_method: "Partner credential setup intent only",
      ip_allowlist_notes: "To be confirmed before credential lifecycle work",
      payload_format_version: "referral-saas.v1",
      go_live_readiness_status: "GO_LIVE_DISABLED",
    },
  };
}

function safeActionError(error: unknown, fallback: string) {
  const status = typeof error === "object" && error && "status" in error ? Number((error as { status?: number }).status) : null;
  if (status === 409) {
    return "The request conflicts with a previous setup action or stale draft. No approval or live action was taken.";
  }
  if (status === 422) {
    return "The setup evidence has blockers or unsafe input. No account was created and no live action was taken.";
  }
  return fallback;
}

function safeAccountCreateError(error: unknown) {
  const status = typeof error === "object" && error && "status" in error ? Number((error as { status?: number }).status) : null;
  if (status === 409) {
    return "The account could not be created because this setup scope already has conflicting or previously created account evidence. Re-check account setup to continue from the resolved account context.";
  }
  if (status === 422) {
    return "The reviewed setup draft is missing required account creation evidence. No account, tenant, user, campaign, go-live, or money action was taken.";
  }
  if (status === 403) {
    return "Your current session is not allowed to create the account foundation. No adjacent setup action was taken.";
  }
  return "Account foundation creation is unavailable. No tenant, user, campaign, go-live, or money action was taken.";
}

function getTrustedInternalTenantScope() {
  if (typeof window === "undefined") {
    return defaultTrustedInternalTenantScope;
  }

  return localStorage.getItem(trustedInternalTenantScopeKey) || defaultTrustedInternalTenantScope;
}

function formatAccountSummary(account: ReferralSaasAccountSummary) {
  return [
    account.accountName || account.accountCode || "Referral SaaS account",
    account.accountStatus || "status unavailable",
    account.tenantLinkStatus ? `tenant link ${account.tenantLinkStatus}` : "",
  ]
    .filter(Boolean)
    .join(" - ");
}

function SetupActionResult({
  createError,
  createResponse,
  draftError,
  draftResponse,
  reviewError,
  reviewResponse,
  submitError,
  submitResponse,
  validationError,
  validationResponse,
}: {
  createError: string | null;
  createResponse: ReferralSaasAccountCreateFromDraftResponse | null;
  draftError: string | null;
  draftResponse: AdminOnboardingDraftSaveResponse | null;
  reviewError: string | null;
  reviewResponse: AdminOnboardingReviewDecisionResponse | null;
  submitError: string | null;
  submitResponse: AdminOnboardingSubmitForReviewResponse | null;
  validationError: string | null;
  validationResponse: AdminOnboardingDryRunValidationResponse | null;
}) {
  return (
    <>
      {validationResponse ? (
        <div className="banner info" role="status">
          <ShieldCheck size={18} />
          <div>
            <strong>Validation completed without saving.</strong>
            <div className="table-subtext">
              Readiness: {validationResponse.readiness_preview.overall_status}; no persistence:{" "}
              {validationResponse.no_persistence_confirmed ? "confirmed" : "unavailable"}; no live action:{" "}
              {validationResponse.no_live_action_confirmed ? "confirmed" : "unavailable"}.
            </div>
          </div>
        </div>
      ) : null}
      {draftResponse ? (
        <div className="banner success" role="status">
          <CheckCircle2 size={18} />
          <div>
            <strong>Setup draft saved.</strong>
            <div className="table-subtext">
              {draftResponse.draft_ref} - {draftResponse.draft_status} - {draftResponse.idempotency_status}; no live action:{" "}
              {draftResponse.no_live_action_confirmed ? "confirmed" : "unavailable"}.
            </div>
          </div>
        </div>
      ) : null}
      {submitResponse ? (
        <div className="banner success" role="status">
          <CheckCircle2 size={18} />
          <div>
            <strong>Setup draft submitted for review.</strong>
            <div className="table-subtext">
              {submitResponse.draft_ref} - {submitResponse.draft_status} - {submitResponse.idempotency_status}; no live action:{" "}
              {submitResponse.no_live_action_confirmed ? "confirmed" : "unavailable"}.
            </div>
          </div>
        </div>
      ) : null}
      {reviewResponse ? (
        <div className="banner success" role="status">
          <CheckCircle2 size={18} />
          <div>
            <strong>Internal review decision recorded.</strong>
            <div className="table-subtext">
              {reviewResponse.draft_ref} - {reviewResponse.review_outcome} - {reviewResponse.draft_status}; go-live:{" "}
              {reviewResponse.go_live_enabled ? "enabled" : "disabled"}.
            </div>
          </div>
        </div>
      ) : null}
      {createResponse ? (
        <div className="banner success" role="status">
          <CheckCircle2 size={18} />
          <div>
            <strong>Account foundation created.</strong>
            <div className="table-subtext">
              {formatAccountSummary(createResponse.account)}; adjacent live action:{" "}
              {createResponse.noAdjacentLiveActionConfirmed ? "blocked" : "unavailable"}.
            </div>
          </div>
        </div>
      ) : null}
      {[validationError, draftError, submitError, reviewError, createError].filter(Boolean).map((message) => (
        <div className="banner warning" key={message} role="status">
          <ShieldCheck size={18} />
          <div>
            <strong>Setup action fallback.</strong>
            <div className="table-subtext">{message}</div>
          </div>
        </div>
      ))}
    </>
  );
}

function SetupLink({ to, title, copy }: { to: string; title: string; copy: string }) {
  return (
    <Link className="route-item" to={to}>
      <div>
        <div className="route-name">{title}</div>
        <div className="route-path">{copy}</div>
      </div>
      <Users size={18} />
    </Link>
  );
}
