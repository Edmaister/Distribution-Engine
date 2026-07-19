import { CheckCircle2, ShieldCheck, Users } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
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
  recordReferralSaasMembershipInvitationIntent,
  type ReferralSaasAccountMembershipPosture,
  type ReferralSaasAccountCreateFromDraftResponse,
  type ReferralSaasAccountSummary,
  type ReferralSaasMembershipInvitationResponse,
} from "../../api/endpoints/referralSaasAccounts";
import {
  useReferralSaasAccountMembershipPosture,
  useReferralSaasAccountResolver,
  useReferralSaasAccountSetupState,
} from "../../api/referralSaasAccountQueries";
import { DataTable } from "../../components/DataTable";
import { ErrorPanel } from "../../components/ErrorPanel";
import { InfoTooltip } from "../../components/InfoTooltip";
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
type CompanyProfileForm = {
  organisationName: string;
  country: string;
  organisationType: string;
  industry: string;
  adminContact: string;
  intendedRole: string;
};

const companyCountryOptions = ["South Africa", "United Kingdom", "United States", "European Union", "Other"];
const companyIndustryOptions = [
  "Banking",
  "Insurance",
  "Retail",
  "Telecommunications",
  "Financial services",
  "Referral management and campaign attribution",
  "Other",
];

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

export function ReferralSaasAccountSetupPage() {
  const navigate = useNavigate();
  const { refreshKey } = useRefreshContext();
  const [activeWizardStep, setActiveWizardStep] = useState(1);
  const [scopeCheckConfirmed, setScopeCheckConfirmed] = useState(false);
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
  const [companyProfile, setCompanyProfile] = useState<CompanyProfileForm>({
    organisationName: `${defaultOrganisationRef} Referral SaaS setup`,
    country: "South Africa",
    organisationType: "Referral SaaS customer",
    industry: "Referral management and campaign attribution",
    adminContact: "setup-owner@example.test",
    intendedRole: "Referral SaaS account admin",
  });
  const [memberSubject, setMemberSubject] = useState("setup-owner");
  const [memberDisplayName, setMemberDisplayName] = useState("Referral SaaS setup owner");
  const [memberEmailHash, setMemberEmailHash] = useState("");
  const [memberRoleFamily, setMemberRoleFamily] = useState("DISTRIBUTION_ADMIN");
  const [memberPermissionSet, setMemberPermissionSet] = useState("REFERRAL_SAAS_ACCOUNT_ADMIN");
  const [membershipInviteState, setMembershipInviteState] = useState<SetupActionState>("idle");
  const [membershipInviteResponse, setMembershipInviteResponse] = useState<ReferralSaasMembershipInvitationResponse | null>(null);
  const [membershipInviteError, setMembershipInviteError] = useState<string | null>(null);
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
  const canCheckScope = Boolean(draftExternalTenantRef.trim() && draftOrganisationRef.trim());

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
  const setupSections = useMemo(
    () => buildReferralSaasSetupSections(appliedExternalTenantRef, appliedOrganisationRef, companyProfile),
    [appliedExternalTenantRef, appliedOrganisationRef, companyProfile],
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
  const membershipInvitationIdempotencyKey = useMemo(
    () => [
      "referral-saas-account-setup-membership-invitation",
      durableAccount?.accountId || durableAccount?.accountCode || "missing-account",
      memberSubject.trim() || "missing-subject",
      memberRoleFamily,
    ].join(":"),
    [durableAccount?.accountCode, durableAccount?.accountId, memberRoleFamily, memberSubject],
  );
  const canSubmitForReview = Boolean(actionScopeReady && draftResponse?.draft_ref && draftState === "success");
  const canSaveCompanyProfile = Boolean(
    actionScopeReady &&
      companyProfile.organisationName.trim() &&
      companyProfile.country.trim() &&
      companyProfile.organisationType.trim() &&
      companyProfile.industry.trim() &&
      companyProfile.adminContact.trim() &&
      companyProfile.intendedRole.trim() &&
      draftState !== "loading",
  );
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
  const canRecordMembershipInvitation = Boolean(
    actionScopeReady &&
      durableAccount &&
      (durableAccount.accountId || durableAccount.accountCode) &&
      memberSubject.trim() &&
      memberRoleFamily &&
      memberPermissionSet &&
      membershipInviteState !== "loading",
  );
  const wizardSteps = [
    { id: 1, label: "Identify customer" },
    { id: 2, label: "Company profile" },
    { id: 3, label: "People & roles" },
    { id: 4, label: "Integration intent" },
    { id: 5, label: "Readiness check" },
    { id: 6, label: "Review & create" },
    { id: 7, label: "Handoff" },
  ];
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
  const failingReadinessRows = resolvedRows.filter((row) =>
    ["Blocked", "Missing evidence", "Needs evidence", "Needs attention", "Pending"].includes(row.status),
  );
  const accountProfileRow = resolvedRows.find((row) => row.code === "ACCOUNT_PROFILE");
  const membershipRow = resolvedRows.find((row) => row.code === "MEMBERSHIP");
  const hasMembershipEvidence = Boolean(
    membershipInviteResponse ||
      (membershipPosture &&
        (membershipPosture.activeCount > 0 ||
          membershipPosture.invitedCount > 0 ||
          membershipPosture.totalMemberships > 0)),
  );
  const wizardStepCompletion = {
    1: actionScopeReady && scopeCheckConfirmed && !scopeChanged,
    2: isReadyStatus(accountProfileRow?.status) || Boolean(draftResponse?.draft_ref),
    3: hasMembershipEvidence,
    4: true,
    5: validationState === "success" || !needsSetupWork,
    6: Boolean(durableAccount || createResponse),
    7: false,
  } as const;
  const wizardStepPassable = {
    ...wizardStepCompletion,
    3: wizardStepCompletion[3] || !durableAccount,
  } as const;

  function submitScope(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextExternalTenantRef = draftExternalTenantRef.trim();
    const nextOrganisationRef = draftOrganisationRef.trim();
    if (!nextExternalTenantRef || !nextOrganisationRef) {
      return;
    }
    setAppliedExternalTenantRef(nextExternalTenantRef);
    setAppliedOrganisationRef(nextOrganisationRef);
    setCompanyProfile((current) => ({
      ...current,
      organisationName: current.organisationName.trim() || `${nextOrganisationRef} Referral SaaS setup`,
    }));
    setScopeCheckConfirmed(true);
    resetSetupActionState();
  }

  function updateCompanyProfile(field: keyof CompanyProfileForm, value: string) {
    setCompanyProfile((current) => ({ ...current, [field]: value }));
  }

  function goToWizardStep(step: number) {
    const requestedStep = Math.min(Math.max(step, 1), wizardSteps.length);
    if (!canOpenWizardStep(requestedStep)) {
      return;
    }
    setActiveWizardStep(requestedStep);
  }

  function continueWizard() {
    if (activeWizardStep === wizardSteps.length) {
      navigate("/admin/referral-saas/campaigns");
      return;
    }
    if (canOpenWizardStep(activeWizardStep + 1)) {
      goToWizardStep(activeWizardStep + 1);
    }
  }

  function canOpenWizardStep(step: number) {
    if (step <= activeWizardStep) {
      return true;
    }
    return wizardSteps
      .filter((wizardStep) => wizardStep.id < step)
      .every((wizardStep) => wizardStepPassable[wizardStep.id as keyof typeof wizardStepPassable]);
  }

  function getWizardRailState(step: number) {
    if (step === activeWizardStep) {
      return "current";
    }
    if (!canOpenWizardStep(step)) {
      return "locked";
    }
    if (wizardStepCompletion[step as keyof typeof wizardStepCompletion]) {
      return "done";
    }
    return "available";
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
    setMembershipInviteState("idle");
    setMembershipInviteResponse(null);
    setMembershipInviteError(null);
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

  async function handleRecordMembershipInvitationIntent() {
    if (!canRecordMembershipInvitation || !durableAccount) {
      return;
    }
    const accountRef = durableAccount.accountId || durableAccount.accountCode;
    if (!accountRef) {
      return;
    }

    setMembershipInviteState("loading");
    setMembershipInviteResponse(null);
    setMembershipInviteError(null);
    try {
      const response = await recordReferralSaasMembershipInvitationIntent({
        accountRef,
        accountScope: {
          refType: "external_tenant_ref",
          externalRef: appliedExternalTenantRef,
          context: "setup",
        },
        actor: {
          actorType: "USER",
          subject: memberSubject,
          emailHash: memberEmailHash,
          displayName: memberDisplayName,
        },
        membership: {
          roleFamily: memberRoleFamily,
          permissionSet: memberPermissionSet,
          tenantScope: "PRIMARY_ACCOUNT_TENANT",
        },
        reasonCode: "ACCOUNT_SETUP_USER_ROLE",
        correlationId: "referral-saas-account-setup-membership-invitation",
        idempotencyKey: membershipInvitationIdempotencyKey,
      });
      setMembershipInviteResponse(response);
      setMembershipInviteState("success");
      setAccountRefreshKey((current) => current + 1);
    } catch (error) {
      setMembershipInviteError(safeMembershipInvitationError(error));
      setMembershipInviteState("error");
    }
  }

  return (
    <>
      <section className="page-header">
        <div>
          <div className="page-kicker">Referral SaaS - Account Setup</div>
          <h1 className="page-title">Account setup wizard</h1>
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
          <section className="account-wizard" aria-labelledby="account-setup-wizard-heading">
            <aside className="account-wizard-rail" aria-label="Account setup progress">
              <div className="rail-title">Progress</div>
              {wizardSteps.map((step) => {
                const state = getWizardRailState(step.id);
                const locked = state === "locked";
                return (
                  <button
                    className={`rail-step ${state}`}
                    disabled={locked}
                    key={step.id}
                    onClick={() => goToWizardStep(step.id)}
                    type="button"
                  >
                    <span aria-hidden="true" className="rail-dot">{state === "done" ? "OK" : locked ? "Lock" : step.id}</span>
                    <span>{step.label}</span>
                  </button>
                );
              })}
            </aside>

            <div className="account-wizard-main">
              <div className="account-wizard-topbar">
                <div>
                  <div className="page-kicker">Step {activeWizardStep} of {wizardSteps.length}</div>
                  <h2 className="panel-title" id="account-setup-wizard-heading">Guided account setup</h2>
                  <div className="panel-subtitle">Set up a customer account foundation before campaign and attribution testing.</div>
                </div>
                <StatusBadge label="Safe mode: no go-live / money / credentials" tone="warning" />
              </div>

              <div className="account-wizard-step">
                {activeWizardStep === 1 ? (
                  <>
                    <div>
                      <div className="page-kicker">Identify customer</div>
                      <h3 className="account-wizard-title">Find or start the account</h3>
                      <p className="page-copy">Enter the customer references. We will tell you if a Referral SaaS account already exists.</p>
                    </div>
                    <form className="wizard-card" onSubmit={submitScope}>
                      <div className="form-grid">
                        <label className="field">
                          <span>External tenant ref</span>
                          <input className="input" onChange={(event) => setDraftExternalTenantRef(event.target.value)} value={draftExternalTenantRef} />
                        </label>
                        <label className="field">
                          <span>Organisation ref</span>
                          <input className="input" onChange={(event) => setDraftOrganisationRef(event.target.value)} value={draftOrganisationRef} />
                        </label>
                      </div>
                      <div className="action-button-row">
                        <button className="button" disabled={!canCheckScope} type="submit">Find account</button>
                        <StatusBadge
                          label={scopeChanged ? "Changes not checked" : scopeCheckConfirmed ? "Checked" : "Not checked"}
                          tone={scopeChanged || !scopeCheckConfirmed ? "warning" : "success"}
                        />
                      </div>
                      <div className="wizard-status-card">
                        <div>
                          <strong>Account status</strong>
                          <p>{durableAccountStatus.copy}</p>
                          {durableAccount ? <span>{formatAccountSummary(durableAccount)}</span> : null}
                        </div>
                        <StatusBadge label={durableAccountStatus.label} tone={durableAccountStatus.tone} />
                      </div>
                    </form>
                  </>
                ) : null}

                {activeWizardStep === 2 ? (
                  <>
                    <div>
                      <div className="page-kicker">Company profile</div>
                      <h3 className="account-wizard-title">Capture company setup evidence</h3>
                      <p className="page-copy">Capture the company evidence inside this wizard. Saving here creates a setup draft only; it does not leave Account Setup or create the final account.</p>
                    </div>
                    <div className="wizard-card">
                      <div className="wizard-status-card">
                        <div>
                          <strong>Account scope</strong>
                          <p>These references were confirmed in Step 1 and are used for the saved company profile evidence.</p>
                          <span>{appliedExternalTenantRef} / {appliedOrganisationRef}</span>
                        </div>
                        <StatusBadge label="Confirmed" tone="success" />
                      </div>
                      <div className="form-grid">
                        <label className="field">
                          <span>Organisation name</span>
                          <input className="input" onChange={(event) => updateCompanyProfile("organisationName", event.target.value)} value={companyProfile.organisationName} />
                        </label>
                        <label className="field">
                          <span>Country</span>
                          <select className="input" onChange={(event) => updateCompanyProfile("country", event.target.value)} value={companyProfile.country}>
                            {companyCountryOptions.map((country) => (
                              <option key={country} value={country}>{country}</option>
                            ))}
                          </select>
                        </label>
                        <div className="field">
                          <label htmlFor="referral-saas-company-organisation-type">
                            Organisation type{" "}
                            <InfoTooltip text="Choose the customer's commercial relationship to this Referral SaaS account. This controls setup evidence only; it does not activate billing, funding, or money movement." />
                          </label>
                          <select
                            className="input"
                            id="referral-saas-company-organisation-type"
                            onChange={(event) => updateCompanyProfile("organisationType", event.target.value)}
                            value={companyProfile.organisationType}
                          >
                            <option value="Referral SaaS customer">Referral SaaS customer</option>
                            <option value="Producer / sponsor">Producer / sponsor</option>
                            <option value="Partner">Partner</option>
                            <option value="Enterprise customer">Enterprise customer</option>
                          </select>
                        </div>
                        <label className="field">
                          <span>Industry</span>
                          <select className="input" onChange={(event) => updateCompanyProfile("industry", event.target.value)} value={companyProfile.industry}>
                            {companyIndustryOptions.map((industry) => (
                              <option key={industry} value={industry}>{industry}</option>
                            ))}
                          </select>
                        </label>
                        <label className="field">
                          <span>Admin contact</span>
                          <input className="input" onChange={(event) => updateCompanyProfile("adminContact", event.target.value)} value={companyProfile.adminContact} />
                        </label>
                        <div className="field">
                          <label htmlFor="referral-saas-company-intended-role">
                            Intended role{" "}
                            <InfoTooltip text="Select the setup role the primary contact is expected to hold later. This records onboarding intent only; it does not invite a user or grant access." />
                          </label>
                          <select
                            className="input"
                            id="referral-saas-company-intended-role"
                            onChange={(event) => updateCompanyProfile("intendedRole", event.target.value)}
                            value={companyProfile.intendedRole}
                          >
                            <option value="Referral SaaS account admin">Referral SaaS account admin</option>
                            <option value="Campaign manager">Campaign manager</option>
                            <option value="Support lead">Support lead</option>
                            <option value="Reporting analyst">Reporting analyst</option>
                          </select>
                        </div>
                      </div>
                      <div className="action-button-row">
                        <button className="button" disabled={!canSaveCompanyProfile} onClick={handleSaveSetupDraft} type="button">
                          {draftState === "loading" ? "Saving company profile" : "Save company profile"}
                        </button>
                        <StatusBadge label={draftResponse ? "Profile saved" : "Draft only"} tone={draftResponse ? "success" : "warning"} />
                      </div>
                      <div className="wizard-status-card">
                        <div>
                          <strong>Company setup status</strong>
                          <p>{resolvedRows.find((row) => row.code === "ACCOUNT_PROFILE")?.evidence || "Company evidence has not been returned yet."}</p>
                        </div>
                        <StatusBadge label={resolvedRows.find((row) => row.code === "ACCOUNT_PROFILE")?.status || "Pending"} tone={statusTone(resolvedRows.find((row) => row.code === "ACCOUNT_PROFILE")?.status || "Pending")} />
                      </div>
                      <SetupActionResult
                        createError={null}
                        createResponse={null}
                        draftResponse={draftResponse}
                        draftError={draftError}
                        reviewError={null}
                        reviewResponse={null}
                        submitError={null}
                        submitResponse={null}
                        validationError={null}
                        validationResponse={null}
                      />
                    </div>
                  </>
                ) : null}

                {activeWizardStep === 3 ? (
                  <>
                    <div>
                      <div className="page-kicker">People & roles</div>
                      <h3 className="account-wizard-title">Record role invitation intent</h3>
                      <p className="page-copy">Capture who should administer this account. This records intent only; it does not send email or activate login.</p>
                    </div>
                    <div className="wizard-card route-list">
                      <div className="wizard-status-card">
                        <div>
                          <strong>User access status</strong>
                          <p>{membershipPostureStatus.copy}</p>
                          {membershipPosture ? <span>{membershipPosture.activeCount} active, {membershipPosture.invitedCount} invited, {membershipPosture.totalMemberships} total memberships.</span> : null}
                        </div>
                        <StatusBadge label={membershipPostureStatus.label} tone={membershipPostureStatus.tone} />
                      </div>
                      <div className="form-grid">
                        <label className="field">
                          <span>User subject</span>
                          <input className="input" onChange={(event) => setMemberSubject(event.target.value)} placeholder="future identity subject" value={memberSubject} />
                        </label>
                        <label className="field">
                          <span>Display name</span>
                          <input className="input" onChange={(event) => setMemberDisplayName(event.target.value)} placeholder="Setup owner name" value={memberDisplayName} />
                        </label>
                        <label className="field">
                          <span>Email hash</span>
                          <input className="input" onChange={(event) => setMemberEmailHash(event.target.value)} placeholder="Optional privacy-safe hash" value={memberEmailHash} />
                        </label>
                        <label className="field">
                          <span>Role family</span>
                          <select className="input" onChange={(event) => setMemberRoleFamily(event.target.value)} value={memberRoleFamily}>
                            <option value="DISTRIBUTION_ADMIN">Distribution admin</option>
                            <option value="PLATFORM_ADMIN">Platform admin</option>
                            <option value="SYSTEM_ADMIN">System admin</option>
                            <option value="PARTNER">Partner</option>
                            <option value="SUPPORT">Support</option>
                          </select>
                        </label>
                        <label className="field">
                          <span>Permission set</span>
                          <select className="input" onChange={(event) => setMemberPermissionSet(event.target.value)} value={memberPermissionSet}>
                            <option value="REFERRAL_SAAS_ACCOUNT_ADMIN">Referral SaaS account admin</option>
                            <option value="REFERRAL_SAAS_CAMPAIGN_MANAGER">Referral SaaS campaign manager</option>
                            <option value="REFERRAL_SAAS_ANALYST">Referral SaaS analyst</option>
                            <option value="REFERRAL_SAAS_SUPPORT">Referral SaaS support</option>
                          </select>
                        </label>
                      </div>
                      <button className="button" disabled={!canRecordMembershipInvitation} onClick={handleRecordMembershipInvitationIntent} type="button">
                        {membershipInviteState === "loading" ? "Recording role intent" : "Record role intent"}
                      </button>
                      <MembershipInvitationResult error={membershipInviteError} response={membershipInviteResponse} />
                    </div>
                  </>
                ) : null}

                {activeWizardStep === 4 ? (
                  <>
                    <div>
                      <div className="page-kicker">Integration intent</div>
                      <h3 className="account-wizard-title">Document API and webhook intent</h3>
                      <p className="page-copy">Capture setup intent without creating credentials, sending webhooks, or exposing secrets.</p>
                    </div>
                    <div className="wizard-card route-list">
                      <SetupLink to="/admin/onboarding/webhook-api" title="Integration setup" copy="Open advanced webhook/API setup intent. No credentials are created from Account Setup." />
                      <div className="chip-row">
                        <StatusBadge label="No credentials" tone="warning" />
                        <StatusBadge label="No webhook delivery" tone="warning" />
                        <StatusBadge label="Intent only" tone="info" />
                      </div>
                    </div>
                  </>
                ) : null}

                {activeWizardStep === 5 ? (
                  <>
                    <div>
                      <div className="page-kicker">Readiness check</div>
                      <h3 className="account-wizard-title">Check what is blocking setup</h3>
                      <p className="page-copy">Validate once, show the failing gates, and keep full evidence in the details drawer.</p>
                    </div>
                    <div className="wizard-card route-list">
                      <div className={`wizard-summary-strip ${needsSetupWork ? "warning" : "success"}`}>
                        <StatusBadge label={needsSetupWork ? "Needs work" : "Ready"} tone={needsSetupWork ? "warning" : "success"} />
                        <div>
                          <strong>{blockedCount} blocked gates, {missingEvidenceCount} evidence gaps</strong>
                          <span>{readyCount} setup gates ready. {goLiveDisabledCount} go-live blocker shown.</span>
                        </div>
                      </div>
                      <div className="route-list">
                        {failingReadinessRows.length ? (
                          failingReadinessRows.map((row) => (
                            <div className="route-item" key={row.code}>
                              <div>
                                <div className="route-name">{row.label}</div>
                                <div className="route-path">{row.evidence}</div>
                              </div>
                              <StatusBadge label={row.status} tone={statusTone(row.status)} />
                            </div>
                          ))
                        ) : (
                          <div className="empty-state">No failing setup gates returned.</div>
                        )}
                      </div>
                      <button className="button" disabled={!actionScopeReady || validationState === "loading"} onClick={handleValidateSetupDraft} type="button">
                        {validationState === "loading" ? "Validating setup" : "Validate setup"}
                      </button>
                      <SetupActionResult
                        createError={null}
                        createResponse={null}
                        draftResponse={null}
                        draftError={null}
                        reviewError={null}
                        reviewResponse={null}
                        submitError={null}
                        submitResponse={null}
                        validationError={validationError}
                        validationResponse={validationResponse}
                      />
                      <details className="wizard-details">
                        <summary>Full evidence and system boundaries</summary>
                        <div className="grid-2">
                          <DataTable
                            rows={resolvedRows}
                            emptyText="No setup checklist rows returned."
                            columns={[
                              { key: "gate", header: "Gate", render: (row) => <span className="mono">{row.code}</span> },
                              { key: "status", header: "Status", render: (row) => <StatusBadge label={row.status} tone={statusTone(row.status)} /> },
                              { key: "evidence", header: "Evidence", render: (row) => <span className="table-subtext">{row.evidence}</span> },
                            ]}
                          />
                          <DataTable
                            rows={guardrails}
                            emptyText="No guardrails returned."
                            columns={[{ key: "guardrail", header: "Guardrail", render: (row) => <span className="mono">{getValue(row, ["name"])}</span> }]}
                          />
                        </div>
                        <DataTable
                          rows={redactions}
                          emptyText="No redactions returned."
                          columns={[{ key: "redaction", header: "Redaction", render: (row) => <span className="mono">{getValue(row, ["name"])}</span> }]}
                        />
                      </details>
                    </div>
                  </>
                ) : null}

                {activeWizardStep === 6 ? (
                  <>
                    <div>
                      <div className="page-kicker">Review & create</div>
                      <h3 className="account-wizard-title">Save, review, then create foundation</h3>
                      <p className="page-copy">The same gated spine as before, shown as an ordered timeline instead of equal competing actions.</p>
                    </div>
                    <div className="wizard-card">
                      <ol className="wizard-timeline">
                        <li className={draftResponse ? "done" : "current"}>
                          <span>1</span>
                          <div>
                            <strong>Save setup draft</strong>
                            <p>Persist setup intent for this external scope.</p>
                            <button className="button secondary" disabled={!actionScopeReady || draftState === "loading"} onClick={handleSaveSetupDraft} type="button">
                              {draftState === "loading" ? "Saving draft" : "Save setup draft"}
                            </button>
                          </div>
                        </li>
                        <li className={submitResponse ? "done" : canSubmitForReview ? "current" : "locked"}>
                          <span>2</span>
                          <div>
                            <strong>Submit for review</strong>
                            <p>Move the draft into a human review gate.</p>
                            <button className="button secondary" disabled={!canSubmitForReview || submitState === "loading"} onClick={handleSubmitSetupDraft} type="button">
                              {submitState === "loading" ? "Submitting review" : "Submit for review"}
                            </button>
                          </div>
                        </li>
                        <li className={reviewResponse ? "done" : canRecordReview ? "current" : "locked"}>
                          <span>3</span>
                          <div>
                            <strong>Internal review decision</strong>
                            <p>Reason required. Accept unlocks create; Block stops the path.</p>
                            <label className="field" htmlFor="referral-saas-review-reason">
                              <span>Review reason</span>
                              <textarea className="input" disabled={!canRecordReview} id="referral-saas-review-reason" onChange={(event) => setReviewReason(event.target.value)} placeholder="Bounded internal review reason" rows={3} value={reviewReason} />
                            </label>
                            <div className="action-button-row">
                              <button className="button" disabled={!canRecordReview || reviewState === "loading"} onClick={() => handleReviewDecision("APPROVED_FOR_INTERNAL_REVIEW")} type="button">Accept internal review</button>
                              <button className="button secondary" disabled={!canRecordReview || reviewState === "loading"} onClick={() => handleReviewDecision("BLOCKED")} type="button">Mark review blocked</button>
                            </div>
                          </div>
                        </li>
                        <li className={createResponse || durableAccount ? "done" : canCreateAccount ? "current" : "locked"}>
                          <span>4</span>
                          <div>
                            <strong>Create account foundation</strong>
                            <p>Creates the durable account foundation only. No users, campaigns, go-live, or money.</p>
                            <button className="button" disabled={!canCreateAccount || createState === "loading"} onClick={handleCreateAccountFoundation} type="button">
                              {createState === "loading" ? "Creating account" : "Create account foundation"}
                            </button>
                          </div>
                        </li>
                      </ol>
                      <SetupActionResult
                        createError={createError}
                        createResponse={createResponse}
                        draftResponse={draftResponse}
                        draftError={draftError}
                        reviewError={reviewError}
                        reviewResponse={reviewResponse}
                        submitError={submitError}
                        submitResponse={submitResponse}
                        validationError={null}
                        validationResponse={null}
                      />
                    </div>
                  </>
                ) : null}

                {activeWizardStep === 7 ? (
                  <>
                    <div>
                      <div className="page-kicker">Handoff</div>
                      <h3 className="account-wizard-title">Account ready for campaign setup</h3>
                      <p className="page-copy">Confirm account posture, then leave Account Setup for campaign readiness.</p>
                    </div>
                    <div className="wizard-card route-list">
                      <div className="wizard-status-card">
                        <div>
                          <strong>{durableAccount ? formatAccountSummary(durableAccount) : "Account not created yet"}</strong>
                          <p>{membershipPostureStatus.copy}</p>
                          {membershipPosture ? <span>{membershipPosture.activeCount} active, {membershipPosture.invitedCount} invited, {membershipPosture.totalMemberships} total memberships.</span> : null}
                        </div>
                        <StatusBadge label={durableAccount ? "Account found" : "Setup incomplete"} tone={durableAccount ? "success" : "warning"} />
                      </div>
                      <SetupLink to="/admin/referral-saas/campaigns" title="Campaign readiness" copy="Go to campaign setup only after account evidence is clear enough for referral testing." />
                    </div>
                  </>
                ) : null}
              </div>

              <div className="account-wizard-footer">
                <button className="button secondary" disabled={activeWizardStep === 1} onClick={() => goToWizardStep(activeWizardStep - 1)} type="button">Back</button>
                <button className="button" disabled={activeWizardStep < wizardSteps.length && !canOpenWizardStep(activeWizardStep + 1)} onClick={continueWizard} type="button">
                  {activeWizardStep === wizardSteps.length ? "Go to Campaigns" : "Continue"}
                </button>
              </div>
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

function isReadyStatus(status: string | undefined) {
  return status === "Ready" || status === "READY";
}

function toCount(value: unknown) {
  const count = Number(value);
  return Number.isFinite(count) ? count : 0;
}

function getDurableAccountStatus(hasAccount: boolean, isLoading: boolean, error: unknown) {
  if (isLoading) {
    return {
      copy: "Looking for an existing Referral SaaS account for these customer references.",
      label: "Checking",
      tone: "info" as const,
    };
  }
  if (hasAccount) {
    return {
      copy: "Account found. Continue with users, roles, and readiness from this account context.",
      label: "Account found",
      tone: "success" as const,
    };
  }

  const status = typeof error === "object" && error && "status" in error ? Number((error as { status?: number }).status) : null;
  if (status === 404) {
    return {
      copy: "No account exists for these references yet. Start the company setup draft to create one.",
      label: "Start setup",
      tone: "warning" as const,
    };
  }
  if (error) {
    return {
      copy: "The account lookup could not safely confirm this customer. Check the references before continuing.",
      label: "Lookup blocked",
      tone: "warning" as const,
    };
  }
  return {
    copy: "Run Step 1 before moving to setup actions.",
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
      copy: "User access can be checked after an account is found or created.",
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

function buildReferralSaasSetupSections(
  externalTenantRef: string,
  organisationRef: string,
  companyProfile: CompanyProfileForm,
) {
  const producerRef = `${organisationRef}-producer`;
  const sponsorRef = `${organisationRef}-sponsor`;
  const distributorRef = `${organisationRef}-distributor`;
  const campaignCode = `${organisationRef}-setup-campaign`;
  const opportunityRef = `${organisationRef}-setup-opportunity`;
  const adminContact = companyProfile.adminContact.trim();

  return {
    company: {
      organisation_name: companyProfile.organisationName.trim(),
      external_tenant_ref: externalTenantRef,
      organisation_ref: organisationRef,
      country: companyProfile.country.trim(),
      organisation_type: companyProfile.organisationType.trim(),
      industry: companyProfile.industry.trim(),
      admin_contact: adminContact,
      intended_role: companyProfile.intendedRole.trim(),
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

function safeMembershipInvitationError(error: unknown) {
  const status = typeof error === "object" && error && "status" in error ? Number((error as { status?: number }).status) : null;
  if (status === 409) {
    return "Membership invitation intent was not recorded because the account, idempotency key, or existing membership evidence conflicts. No email, access, seat, campaign, go-live, or money action was taken.";
  }
  if (status === 422) {
    return "Membership invitation intent needs a valid subject, role family, permission set, account scope, correlation ID, and idempotency key. No delivery or activation was attempted.";
  }
  if (status === 403) {
    return "Your current session is not allowed to record membership invitation intent for this account. No membership, delivery, access, or money action was taken.";
  }
  return "Membership invitation intent is unavailable. No email delivery, active access, seat assignment, auth claim, campaign, go-live, or money action was taken.";
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

function MembershipInvitationResult({
  error,
  response,
}: {
  error: string | null;
  response: ReferralSaasMembershipInvitationResponse | null;
}) {
  if (response) {
    return (
      <div className="banner success" role="status">
        <CheckCircle2 size={18} />
        <div>
          <strong>Role intent recorded.</strong>
          <div className="table-subtext">
            {response.invitation.commandStatus} - {response.invitation.membership.status} -{" "}
            {response.invitation.membership.roleFamily}; delivery: {response.invitation.delivery.status}.
          </div>
          <div className="table-subtext">
            Next: {response.invitation.delivery.nextAction}. No active access, seat, auth claim, campaign, go-live, or money action was taken.
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="banner warning" role="status">
        <ShieldCheck size={18} />
        <div>
          <strong>Role intent fallback.</strong>
          <div className="table-subtext">{error}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="banner info">
      <ShieldCheck size={18} />
      <div>
        <strong>What this records</strong>
        <div className="table-subtext">
          A bounded invited membership record for setup evidence. It is not an email invitation, login activation, seat assignment, or campaign launch.
        </div>
      </div>
    </div>
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
