import { CheckCircle2, ShieldCheck, Users } from "lucide-react";
import { Link } from "react-router-dom";
import { useEffect, useMemo, useState, type FormEvent } from "react";

import {
  recordAdminOnboardingReviewDecision,
  saveAdminOnboardingDraft,
  submitAdminOnboardingDraftForReview,
  validateAdminOnboardingDryRun,
  type AdminOnboardingDraftSaveResponse,
  type AdminOnboardingReviewDecisionResponse,
  type AdminOnboardingSubmitForReviewResponse,
} from "../../api/endpoints/adminOnboarding";
import {
  createReferralSaasAccountFromDraft,
  type ReferralSaasAccountCreateFromDraftResponse,
  type ReferralSaasAccountSummary,
} from "../../api/endpoints/referralSaasAccounts";
import {
  useReferralSaasAccountDraftSelector,
  useReferralSaasAccountResolver,
  useReferralSaasAccountSetupState,
} from "../../api/referralSaasAccountQueries";
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

const defaultExternalTenantRef = "";
const defaultOrganisationRef = "";
const draftConflictRecoveryMessage =
  "A saved setup already exists for this customer. Refresh the setup status to continue from the latest evidence, or use a different customer before saving another draft. No account was created and no live action was taken.";
const accountAlreadyExistsMessage =
  "This customer already has a workspace, or the selected internal workspace scope is already attached to a customer. Open the customer profile if this is the same customer, or use different customer identifiers.";
const internalScopeAlreadyUsedMessage =
  "The internal workspace scope for this customer is already attached to another customer workspace. Use different customer identifiers, then create the workspace again.";
const guidedReviewReason = "Account setup reviewed through the guided Referral SaaS account setup flow.";
type SetupActionState = "idle" | "loading" | "success" | "error";
type CompanyProfileForm = {
  organisationName: string;
  country: string;
  organisationType: string;
  industry: string;
  adminContact: string;
  intendedRole: string;
};

const companyJurisdictionOptions = [
  "South Africa",
  "United Kingdom",
  "United States",
  "European Union",
  "Canada",
  "Australia",
  "United Arab Emirates",
  "Singapore",
  "India",
  "Brazil",
  "Other",
];
const companyIndustryOptions = [
  "Banking and financial services",
  "Insurance",
  "Retail and ecommerce",
  "Telecommunications",
  "Automotive",
  "Travel and hospitality",
  "Healthcare",
  "Education",
  "Real estate",
  "Energy and utilities",
  "Technology and SaaS",
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
    label: "Workspace scope",
    source: "Existing onboarding readiness projection",
    next: "Assign the hidden internal workspace scope before campaign work.",
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
    next: "Use customer-safe reports; persisted exports remain future work.",
  },
];

export function ReferralSaasAccountSetupPage() {
  const { refreshKey } = useRefreshContext();
  const [activeWizardStep, setActiveWizardStep] = useState(1);
  const [scopeCheckConfirmed, setScopeCheckConfirmed] = useState(false);
  const [draftExternalTenantRef, setDraftExternalTenantRef] = useState(defaultExternalTenantRef);
  const [draftOrganisationRef, setDraftOrganisationRef] = useState(defaultOrganisationRef);
  const [appliedExternalTenantRef, setAppliedExternalTenantRef] = useState(defaultExternalTenantRef);
  const [appliedOrganisationRef, setAppliedOrganisationRef] = useState(defaultOrganisationRef);
  const [validationState, setValidationState] = useState<SetupActionState>("idle");
  const [validationError, setValidationError] = useState<string | null>(null);
  const [draftState, setDraftState] = useState<SetupActionState>("idle");
  const [draftResponse, setDraftResponse] = useState<AdminOnboardingDraftSaveResponse | null>(null);
  const [draftError, setDraftError] = useState<string | null>(null);
  const [submitResponse, setSubmitResponse] = useState<AdminOnboardingSubmitForReviewResponse | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [reviewResponse, setReviewResponse] = useState<AdminOnboardingReviewDecisionResponse | null>(null);
  const [reviewError, setReviewError] = useState<string | null>(null);
  const [createState, setCreateState] = useState<SetupActionState>("idle");
  const [createResponse, setCreateResponse] = useState<ReferralSaasAccountCreateFromDraftResponse | null>(null);
  const [createError, setCreateError] = useState<string | null>(null);
  const [companyProfile, setCompanyProfile] = useState<CompanyProfileForm>({
    organisationName: "",
    country: "South Africa",
    organisationType: "Direct customer",
    industry: "Banking and financial services",
    adminContact: "",
    intendedRole: "Account owner",
  });
  const [savedCompanyProfile, setSavedCompanyProfile] = useState<CompanyProfileForm | null>(null);
  const [loadedCompanyDraftRef, setLoadedCompanyDraftRef] = useState<string | null>(null);
  const [loadedCompanyDraftVersion, setLoadedCompanyDraftVersion] = useState<number | null>(null);
  const [loadedCompanyDraftUpdatedAt, setLoadedCompanyDraftUpdatedAt] = useState<string | null>(null);
  const [setupRefreshKey, setSetupRefreshKey] = useState(0);
  const [accountRefreshKey, setAccountRefreshKey] = useState(0);
  const { data, error, isLoading } = useReferralSaasAccountSetupState(
    appliedExternalTenantRef,
    appliedOrganisationRef,
    refreshKey + setupRefreshKey,
  );
  const {
    data: draftSelector,
    error: draftSelectorError,
    isLoading: draftSelectorLoading,
  } = useReferralSaasAccountDraftSelector(
    appliedExternalTenantRef,
    appliedOrganisationRef,
    refreshKey + setupRefreshKey,
  );
  const {
    data: accountResolution,
    error: accountResolutionError,
    isLoading: accountResolutionLoading,
  } = useReferralSaasAccountResolver(appliedExternalTenantRef, refreshKey + accountRefreshKey);
  const scopeChanged =
    draftExternalTenantRef.trim() !== appliedExternalTenantRef ||
    draftOrganisationRef.trim() !== appliedOrganisationRef;
  const canCheckScope = Boolean(draftExternalTenantRef.trim() && draftOrganisationRef.trim());

  const readiness = asRecord(data?.readiness);
  const categories = asArray(getNestedValue(readiness, ["categories"], []));
  const overallStatus = formatDisplay(getNestedValue(readiness, ["overall_status"], "pending"));
  const durableAccount = accountResolution?.account;
  const durableAccountStatus = getDurableAccountStatus(
    Boolean(durableAccount),
    accountResolutionLoading,
    accountResolutionError,
  );
  const setupSections = useMemo(
    () => buildReferralSaasSetupSections(appliedExternalTenantRef, appliedOrganisationRef, companyProfile),
    [appliedExternalTenantRef, appliedOrganisationRef, companyProfile],
  );
  const latestCompanyDraft = useMemo(
    () =>
      (draftSelector?.items || []).find((draft) =>
        Boolean(companyProfileFromDraftSection(draft.draft_sections?.company)),
      ),
    [draftSelector],
  );
  const latestSavedCompanyProfile = useMemo(
    () => companyProfileFromDraftSection(latestCompanyDraft?.draft_sections?.company),
    [latestCompanyDraft],
  );
  const actionScopeReady = Boolean(appliedExternalTenantRef && appliedOrganisationRef && !scopeChanged);
  const companyProfileHasSavedDraft = Boolean(savedCompanyProfile && loadedCompanyDraftRef);
  const companyProfileHasUnsavedChanges = Boolean(
    savedCompanyProfile && !companyProfilesEqual(companyProfile, savedCompanyProfile),
  );
  const companyProfileComplete = Boolean(
    companyProfile.organisationName.trim() &&
      companyProfile.country.trim() &&
      companyProfile.organisationType.trim() &&
      companyProfile.industry.trim() &&
      companyProfile.adminContact.trim() &&
      companyProfile.intendedRole.trim(),
  );
  const draftIdempotencyKey = useMemo(
    () => ["referral-saas-account-setup-draft", appliedExternalTenantRef, appliedOrganisationRef].join(":"),
    [appliedExternalTenantRef, appliedOrganisationRef],
  );
  const validateIdempotencyKey = useMemo(
    () => ["referral-saas-account-setup-validate", appliedExternalTenantRef, appliedOrganisationRef].join(":"),
    [appliedExternalTenantRef, appliedOrganisationRef],
  );
  const canSaveCompanyProfile = Boolean(
    actionScopeReady &&
      companyProfileComplete &&
      draftState !== "loading" &&
      (!companyProfileHasSavedDraft || companyProfileHasUnsavedChanges || draftState !== "success"),
  );
  const canCreateAccount = Boolean(
    actionScopeReady &&
      companyProfileComplete &&
      !durableAccount &&
      createState !== "loading",
  );
  const wizardSteps = [
    { id: 1, label: "Identify customer" },
    { id: 2, label: "Company profile" },
    { id: 3, label: "Setup checkpoint" },
    { id: 4, label: "Review & create" },
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
  const accountProfileRow = resolvedRows.find((row) => row.code === "ACCOUNT_PROFILE");
  const accountProfileReady =
    isReadyStatus(accountProfileRow?.status) ||
    Boolean(companyProfileHasSavedDraft && !companyProfileHasUnsavedChanges);
  const accountSetupCheckpoint = getAccountSetupCheckpoint({
    accountProfileReady,
    actionScopeReady,
    companyProfileHasUnsavedChanges,
    companyProfileHasSavedDraft,
    durableAccount: Boolean(durableAccount),
    validationState,
  });
  const wizardStepCompletion = {
    1: actionScopeReady && scopeCheckConfirmed && !scopeChanged,
    2: accountProfileReady,
    3: accountProfileReady && !companyProfileHasUnsavedChanges,
    4: Boolean(durableAccount || createResponse),
  } as const;
  const wizardStepPassable = {
    ...wizardStepCompletion,
  } as const;

  useEffect(() => {
    if (!latestCompanyDraft || !latestSavedCompanyProfile || scopeChanged) {
      return;
    }
    if (
      loadedCompanyDraftRef === latestCompanyDraft.draft_ref &&
      savedCompanyProfile &&
      !companyProfilesEqual(companyProfile, savedCompanyProfile)
    ) {
      return;
    }
    setCompanyProfile(latestSavedCompanyProfile);
    setSavedCompanyProfile(latestSavedCompanyProfile);
    setLoadedCompanyDraftRef(latestCompanyDraft.draft_ref);
    setLoadedCompanyDraftVersion(latestCompanyDraft.draft_version ?? null);
    setLoadedCompanyDraftUpdatedAt(latestCompanyDraft.updated_at || null);
    setDraftResponse({
      status: "ok",
      draft_ref: latestCompanyDraft.draft_ref,
      draft_status: latestCompanyDraft.draft_status || "DRAFT_LOADED",
      draft_version: latestCompanyDraft.draft_version,
      idempotency_status: "LOADED_SAVED_DRAFT",
      guardrails: ["READ_ONLY_DRAFT_SELECTOR", "NO_LIVE_ACTION"],
      redactions: latestCompanyDraft.redactions || ["internal_identifier"],
      no_live_action_confirmed: true,
    });
    setDraftState("success");
    setDraftError(null);
  }, [
    companyProfile,
    latestCompanyDraft,
    latestSavedCompanyProfile,
    loadedCompanyDraftRef,
    savedCompanyProfile,
    scopeChanged,
  ]);

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
    setSavedCompanyProfile(null);
    setLoadedCompanyDraftRef(null);
    setLoadedCompanyDraftVersion(null);
    setLoadedCompanyDraftUpdatedAt(null);
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
    if (canOpenWizardStep(activeWizardStep + 1)) {
      goToWizardStep(activeWizardStep + 1);
    }
  }

  function handleRefreshSetupStatus() {
    resetSetupActionState();
    setSetupRefreshKey((current) => current + 1);
    setAccountRefreshKey((current) => current + 1);
  }

  function handleChangeCustomerReferences() {
    resetSetupActionState();
    setScopeCheckConfirmed(false);
    setActiveWizardStep(1);
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
    setValidationError(null);
    setDraftState("idle");
    setDraftResponse(null);
    setDraftError(null);
    setSubmitResponse(null);
    setSubmitError(null);
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
    setValidationError(null);
    try {
      await validateAdminOnboardingDryRun({
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
    setSubmitResponse(null);
    setSubmitError(null);
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
      setSavedCompanyProfile(companyProfile);
      setLoadedCompanyDraftRef(response.draft_ref);
      setLoadedCompanyDraftVersion(response.draft_version ?? null);
      setLoadedCompanyDraftUpdatedAt(null);
    } catch (error) {
      setDraftError(safeActionError(error, "Draft save is unavailable. No account was created and no live action was taken."));
      setDraftState("error");
    }
  }

  async function handleCreateAccountFoundation() {
    if (!canCreateAccount) {
      return;
    }
    setDraftError(null);
    setSubmitError(null);
    setReviewError(null);
    setCreateState("loading");
    setCreateResponse(null);
    setCreateError(null);
    try {
      const savedDraft = draftResponse?.draft_ref && draftState === "success" && !companyProfileHasUnsavedChanges
        ? draftResponse
        : await saveAdminOnboardingDraft({
            external_tenant_ref: appliedExternalTenantRef,
            organisation_ref: appliedOrganisationRef,
            idempotency_key: draftIdempotencyKey,
            correlation_id: "referral-saas-account-setup-draft",
            sections: setupSections,
          });
      setDraftResponse(savedDraft);
      setDraftState("success");
      setSavedCompanyProfile(companyProfile);
      setLoadedCompanyDraftRef(savedDraft.draft_ref);
      setLoadedCompanyDraftVersion(savedDraft.draft_version ?? null);
      setLoadedCompanyDraftUpdatedAt(null);

      const submittedDraft = await submitAdminOnboardingDraftForReview(savedDraft.draft_ref, {
        external_tenant_ref: appliedExternalTenantRef,
        organisation_ref: appliedOrganisationRef,
        expected_version: savedDraft.draft_version ?? 1,
        idempotency_key: ["referral-saas-account-setup-submit", savedDraft.draft_ref].join(":"),
        correlation_id: "referral-saas-account-setup-submit-review",
      });
      setSubmitResponse(submittedDraft);

      const reviewedDraft = await recordAdminOnboardingReviewDecision(submittedDraft.draft_ref, {
        external_tenant_ref: appliedExternalTenantRef,
        organisation_ref: appliedOrganisationRef,
        expected_version: submittedDraft.draft_version ?? 1,
        idempotency_key: [
          "referral-saas-account-setup-review",
          submittedDraft.draft_ref,
          submittedDraft.draft_version ?? "missing-version",
          "APPROVED_FOR_INTERNAL_REVIEW",
        ].join(":"),
        review_outcome: "APPROVED_FOR_INTERNAL_REVIEW",
        reason_category: "OPERATOR_REVIEW",
        reason: guidedReviewReason,
        correlation_id: "referral-saas-account-setup-review-decision",
      });
      setReviewResponse(reviewedDraft);

      const response = await createReferralSaasAccountFromDraft({
        draftRef: reviewedDraft.draft_ref,
        internalTenantCode: deriveInternalSetupTenantScope(appliedExternalTenantRef, appliedOrganisationRef),
        idempotencyKey: ["referral-saas-account-setup-create", reviewedDraft.draft_ref].join(":"),
      });
      setCreateResponse(response);
      setCreateState("success");
      setAccountRefreshKey((current) => current + 1);
    } catch (error) {
      setCreateError(safeAccountCreateError(error));
      setCreateState("error");
    }
  }

  const readinessEvidenceLabel = resolvedRows.find((row) => row.code === "ACCOUNT_PROFILE")?.status || "Pending";
  const readinessEvidenceCopy =
    resolvedRows.find((row) => row.code === "ACCOUNT_PROFILE")?.evidence ||
    "Company readiness evidence has not been returned yet.";
  const companyProfileStatusCopy = companyProfileHasUnsavedChanges
    ? "You changed the company profile after the last saved draft. Save these changes before continuing."
    : companyProfileHasSavedDraft
      ? "Company profile saved. Continue to Setup checkpoint."
      : draftSelectorLoading
        ? "Checking for a saved company profile draft for this customer."
        : "Save the company profile draft before moving to Setup checkpoint.";
  const companyProfileStatusBadge = companyProfileHasUnsavedChanges
    ? "Unsaved changes"
    : companyProfileHasSavedDraft
      ? "Draft saved"
      : draftSelectorLoading
        ? "Checking drafts"
        : "Not saved";
  const companyProfileStatusTone = companyProfileHasUnsavedChanges
    ? ("warning" as const)
    : companyProfileHasSavedDraft
      ? ("success" as const)
      : draftSelectorLoading
        ? ("info" as const)
        : ("warning" as const);
  const savedCompanyDraftSummary = loadedCompanyDraftRef
    ? [
        "Saved profile evidence",
        loadedCompanyDraftVersion ? `version ${loadedCompanyDraftVersion}` : null,
        loadedCompanyDraftUpdatedAt ? `updated ${loadedCompanyDraftUpdatedAt}` : null,
      ]
        .filter(Boolean)
        .join(" - ")
    : null;

  return (
    <>
      <section className="page-header">
        <div>
          <div className="page-kicker">Referral SaaS - Account Setup</div>
          <h1 className="page-title">Account setup wizard</h1>
          <p className="page-copy">
            Work through customer identification, company profile, setup
            checkpoint, and customer workspace creation before testing
            campaigns, links, attribution, or reports. Technical integration
            setup is handled after the customer workspace is ready.
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
                  <div className="panel-subtitle">Create the customer workspace before campaign and attribution testing.</div>
                </div>
                <StatusBadge label="Safe mode: no go-live / money / credentials" tone="warning" />
              </div>

              <div className="account-wizard-step">
                {activeWizardStep === 1 ? (
                  <>
                    <div>
                      <div className="page-kicker">Identify customer</div>
                      <h3 className="account-wizard-title">Find or start the customer workspace</h3>
                      <p className="page-copy">Enter the customer identifiers. We will tell you if a Referral SaaS customer workspace already exists.</p>
                    </div>
                    <form className="wizard-card" onSubmit={submitScope}>
                      <div className="wizard-status-card">
                        <div>
                          <strong>Customer identifiers</strong>
                          <p>Use the customer's visible identifiers for setup. Internal workspace identifiers stay hidden.</p>
                        </div>
                        <StatusBadge label="External only" tone="info" />
                      </div>
                      <div className="form-grid">
                        <div className="field">
                          <label htmlFor="referral-saas-customer-reference">
                            Customer reference{" "}
                            <InfoTooltip text="Enter the stable customer-facing reference for this workspace, such as a customer slug or external account reference. We use it to find an existing Referral SaaS customer, save setup evidence, and keep later customer work scoped without exposing internal platform identifiers." />
                          </label>
                          <input
                            className="input"
                            id="referral-saas-customer-reference"
                            onChange={(event) => setDraftExternalTenantRef(event.target.value)}
                            placeholder="Example: fnb-sa-referrals"
                            value={draftExternalTenantRef}
                          />
                        </div>
                        <div className="field">
                          <label htmlFor="referral-saas-organisation-reference">
                            Organisation reference{" "}
                            <InfoTooltip text="Enter the customer organisation reference that pairs with the customer reference. We use it in setup drafts, readiness checks, and customer profile routing so the workspace can be selected again consistently." />
                          </label>
                          <input
                            className="input"
                            id="referral-saas-organisation-reference"
                            onChange={(event) => setDraftOrganisationRef(event.target.value)}
                            placeholder="Example: fnb-retail-bank"
                            value={draftOrganisationRef}
                          />
                        </div>
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
                          <strong>Customer workspace status</strong>
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
                          <strong>Customer workspace scope</strong>
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
                          <span>Operating jurisdiction</span>
                          <select className="input" onChange={(event) => updateCompanyProfile("country", event.target.value)} value={companyProfile.country}>
                            {companyJurisdictionOptions.map((jurisdiction) => (
                              <option key={jurisdiction} value={jurisdiction}>{jurisdiction}</option>
                            ))}
                          </select>
                        </label>
                        <div className="field">
                          <label htmlFor="referral-saas-company-organisation-type">
                            Customer type{" "}
                            <InfoTooltip text="Describes the customer's relationship to this account setup. Product package and billing plan are configured separately." />
                          </label>
                          <select
                            className="input"
                            id="referral-saas-company-organisation-type"
                            onChange={(event) => updateCompanyProfile("organisationType", event.target.value)}
                            value={companyProfile.organisationType}
                          >
                            <option value="Direct customer">Direct customer</option>
                            <option value="Enterprise customer">Enterprise customer</option>
                            <option value="Agency / implementation partner">Agency / implementation partner</option>
                            <option value="Producer / sponsor">Producer / sponsor</option>
                            <option value="Partner operator">Partner operator</option>
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
                            Contact responsibility{" "}
                            <InfoTooltip text="Describes why this contact is involved in setup. Users, access roles, and permissions are managed later in Account Maintenance." />
                          </label>
                          <select
                            className="input"
                            id="referral-saas-company-intended-role"
                            onChange={(event) => updateCompanyProfile("intendedRole", event.target.value)}
                            value={companyProfile.intendedRole}
                          >
                            <option value="Account owner">Account owner</option>
                            <option value="Implementation lead">Implementation lead</option>
                            <option value="Campaign manager">Campaign manager</option>
                            <option value="Technical integration lead">Technical integration lead</option>
                            <option value="Reporting lead">Reporting lead</option>
                            <option value="Support lead">Support lead</option>
                          </select>
                        </div>
                      </div>
                      <div className="action-button-row">
                        <button className="button" disabled={!canSaveCompanyProfile} onClick={handleSaveSetupDraft} type="button">
                          {draftState === "loading"
                            ? "Saving company profile"
                            : companyProfileHasUnsavedChanges
                              ? "Save company changes"
                              : "Save company profile"}
                        </button>
                        <StatusBadge label={companyProfileStatusBadge} tone={companyProfileStatusTone} />
                      </div>
                      <div className="wizard-status-card">
                        <div>
                          <strong>Company profile status</strong>
                          <p>{companyProfileStatusCopy}</p>
                          {savedCompanyDraftSummary ? <span>{savedCompanyDraftSummary}</span> : null}
                          <span>Backend readiness: {readinessEvidenceLabel} - {readinessEvidenceCopy}</span>
                        </div>
                        <StatusBadge label={companyProfileStatusBadge} tone={companyProfileStatusTone} />
                      </div>
                      {draftSelectorError ? <ErrorPanel error={draftSelectorError} /> : null}
                      <SetupActionResult
                        createError={null}
                        createResponse={null}
                        draftResponse={null}
                        draftError={draftError}
                        onChangeCustomerReferences={handleChangeCustomerReferences}
                        onRefreshSetupStatus={handleRefreshSetupStatus}
                        reviewError={null}
                        reviewResponse={null}
                        submitError={null}
                        submitResponse={null}
                        validationError={null}
                      />
                    </div>
                  </>
                ) : null}

                {activeWizardStep === 3 ? (
                  <>
                    <div>
                      <div className="page-kicker">Setup checkpoint</div>
                      <h3 className="account-wizard-title">Confirm customer setup can continue</h3>
                      <p className="page-copy">
                        This checkpoint only confirms the Account Setup path.
                        Full readiness evidence now lives in Account Maintenance.
                      </p>
                    </div>
                    <div className="wizard-card route-list">
                      <div className={`wizard-summary-strip ${accountSetupCheckpoint.tone === "success" ? "success" : "warning"}`}>
                        <StatusBadge label={accountSetupCheckpoint.badge} tone={accountSetupCheckpoint.tone} />
                        <div>
                          <strong>{accountSetupCheckpoint.title}</strong>
                          <span>{accountSetupCheckpoint.copy}</span>
                        </div>
                      </div>
                      <div className="route-list">
                        <div className="route-item">
                          <div>
                            <div className="route-name">Customer identifiers confirmed</div>
                            <div className="route-path">Step 1 checked the visible customer and organisation identifiers.</div>
                          </div>
                          <StatusBadge label={actionScopeReady && scopeCheckConfirmed ? "Confirmed" : "Check first"} tone={actionScopeReady && scopeCheckConfirmed ? "success" : "warning"} />
                        </div>
                        <div className="route-item">
                          <div>
                            <div className="route-name">Company profile saved</div>
                            <div className="route-path">Step 2 saved the company evidence used by review and customer workspace creation.</div>
                          </div>
                          <StatusBadge label={accountProfileReady ? "Saved" : "Save first"} tone={accountProfileReady ? "success" : "warning"} />
                        </div>
                        <SetupLink to="/admin/referral-saas/account-maintenance" title="Account Maintenance readiness" copy="Review users, access posture, technical setup, campaign readiness, reporting baseline, guardrails, and redactions there." />
                      </div>
                      <button className="button secondary" disabled={!actionScopeReady || validationState === "loading"} onClick={handleValidateSetupDraft} type="button">
                        {validationState === "loading" ? "Refreshing checkpoint" : "Refresh setup checkpoint"}
                      </button>
                      {validationState === "success" ? (
                        <div className="wizard-status-card">
                          <div>
                            <strong>Checkpoint refreshed</strong>
                            <p>Continue to Review & create. Maintenance readiness remains separate from this setup checkpoint.</p>
                          </div>
                          <StatusBadge label="Continue" tone="success" />
                        </div>
                      ) : null}
                      <SetupActionResult
                        createError={null}
                        createResponse={null}
                        draftResponse={null}
                        draftError={null}
                        onChangeCustomerReferences={handleChangeCustomerReferences}
                        onRefreshSetupStatus={handleRefreshSetupStatus}
                        reviewError={null}
                        reviewResponse={null}
                        submitError={null}
                        submitResponse={null}
                        validationError={validationError}
                      />
                    </div>
                  </>
                ) : null}

                {activeWizardStep === 4 ? (
                  <>
                    <div>
                      <div className="page-kicker">Review & create</div>
                      <h3 className="account-wizard-title">Review and create customer workspace</h3>
                      <p className="page-copy">Confirm the customer setup evidence, then create the customer workspace. We handle the required safe review steps in the background.</p>
                    </div>
                    <div className="wizard-card">
                      <div className="wizard-status-card">
                        <div>
                          <strong>Ready to create the customer workspace</strong>
                          <p>
                            This creates the durable customer workspace and hidden internal scope only. It does not create users, send invites,
                            create campaigns, enable go-live, create credentials, bill, settle, or move money.
                          </p>
                        </div>
                        <StatusBadge label="Safe mode" tone="warning" />
                      </div>
                      <div className="summary-grid">
                        <div className="summary-item">
                          <div className="summary-label">Customer</div>
                          <div className="summary-value">{appliedExternalTenantRef}</div>
                          <div className="table-subtext">{appliedOrganisationRef}</div>
                        </div>
                        <div className="summary-item">
                          <div className="summary-label">Company profile</div>
                          <div className="summary-value">{companyProfileStatusBadge}</div>
                          <div className="table-subtext">{companyProfileStatusCopy}</div>
                        </div>
                        <div className="summary-item">
                          <div className="summary-label">Setup checkpoint</div>
                          <div className="summary-value">{accountSetupCheckpoint.title}</div>
                          <div className="table-subtext">{accountSetupCheckpoint.copy}</div>
                        </div>
                        <div className="summary-item">
                          <div className="summary-label">Customer workspace</div>
                          <div className="summary-value">{durableAccount ? "Already exists" : createResponse ? "Created" : "Not created"}</div>
                          <div className="table-subtext">{durableAccount ? formatAccountSummary(durableAccount) : "Create only after customer evidence is correct."}</div>
                        </div>
                      </div>
                      <div className="action-button-row">
                        <button className="button" disabled={!canCreateAccount} onClick={handleCreateAccountFoundation} type="button">
                          {createState === "loading" ? "Creating customer workspace" : "Create customer workspace"}
                        </button>
                        <button className="button secondary" disabled={!actionScopeReady || draftState === "loading"} onClick={handleSaveSetupDraft} type="button">
                          {draftState === "loading" ? "Saving draft" : "Save and finish later"}
                        </button>
                        <button className="button secondary" onClick={handleChangeCustomerReferences} type="button">
                          Use different customer identifiers
                        </button>
                      </div>
                      <details className="wizard-details">
                        <summary>What happens behind the button</summary>
                        <ol className="wizard-timeline compact">
                          <li className={draftResponse ? "done" : "locked"}>
                            <span>1</span>
                            <div>
                              <strong>Save setup draft</strong>
                              <p>Persist customer setup evidence for this customer workspace scope.</p>
                            </div>
                          </li>
                          <li className={submitResponse ? "done" : "locked"}>
                            <span>2</span>
                            <div>
                              <strong>Submit for internal review</strong>
                              <p>Move the setup draft through the existing governed review gate.</p>
                            </div>
                          </li>
                          <li className={reviewResponse ? "done" : "locked"}>
                            <span>3</span>
                            <div>
                              <strong>Record review approval</strong>
                              <p>Record a bounded internal setup decision without enabling launch or money actions.</p>
                            </div>
                          </li>
                          <li className={createResponse || durableAccount ? "done" : "locked"}>
                            <span>4</span>
                            <div>
                              <strong>Create customer workspace</strong>
                              <p>Create the customer workspace, hidden internal workspace scope, and customer-reference mapping only.</p>
                            </div>
                          </li>
                        </ol>
                      </details>
                      {durableAccount ? (
                        <div className="banner success" role="status">
                          <CheckCircle2 size={18} />
                          <div>
                            <strong>Customer workspace already exists.</strong>
                            <div className="table-subtext">{formatAccountSummary(durableAccount)}</div>
                          </div>
                        </div>
                      ) : null}
                      <SetupActionResult
                        createError={createError}
                        createResponse={createResponse}
                        draftResponse={draftResponse}
                        draftError={draftError}
                        mode="guided"
                        onChangeCustomerReferences={handleChangeCustomerReferences}
                        onRefreshSetupStatus={handleRefreshSetupStatus}
                        reviewError={reviewError}
                        reviewResponse={reviewResponse}
                        submitError={submitError}
                        submitResponse={submitResponse}
                        validationError={null}
                      />
                    </div>
                  </>
                ) : null}

              </div>

              <div className="account-wizard-footer">
                <button className="button secondary" disabled={activeWizardStep === 1} onClick={() => goToWizardStep(activeWizardStep - 1)} type="button">Back</button>
                {activeWizardStep < wizardSteps.length ? (
                  <button className="button" disabled={!canOpenWizardStep(activeWizardStep + 1)} onClick={continueWizard} type="button">
                    Continue
                  </button>
                ) : null}
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

function getDurableAccountStatus(hasAccount: boolean, isLoading: boolean, error: unknown) {
  if (isLoading) {
    return {
      copy: "Looking for an existing Referral SaaS account for these customer identifiers.",
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
      copy: "No account exists for these customer identifiers yet. Start the company setup draft to create one.",
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

function getAccountSetupCheckpoint({
  accountProfileReady,
  actionScopeReady,
  companyProfileHasSavedDraft,
  companyProfileHasUnsavedChanges,
  durableAccount,
  validationState,
}: {
  accountProfileReady: boolean;
  actionScopeReady: boolean;
  companyProfileHasSavedDraft: boolean;
  companyProfileHasUnsavedChanges: boolean;
  durableAccount: boolean;
  validationState: SetupActionState;
}) {
  if (!actionScopeReady) {
    return {
      badge: "Check customer",
      copy: "Confirm the customer identifiers before continuing.",
      title: "Customer identifiers still need to be checked",
      tone: "warning" as const,
    };
  }
  if (companyProfileHasUnsavedChanges) {
    return {
      badge: "Save changes",
      copy: "Save the changed company profile before moving to review.",
      title: "Company profile has unsaved changes",
      tone: "warning" as const,
    };
  }
  if (!companyProfileHasSavedDraft && !accountProfileReady) {
    return {
      badge: "Save profile",
      copy: "Save the company profile evidence before moving to review.",
      title: "Company profile evidence is not saved yet",
      tone: "warning" as const,
    };
  }
  if (durableAccount) {
    return {
      badge: "Workspace found",
      copy: "A customer workspace already exists for this customer. Open the customer profile to continue maintenance and customer-scoped work.",
      title: "Customer workspace already exists",
      tone: "success" as const,
    };
  }
  if (validationState === "success") {
    return {
      badge: "Checked",
      copy: "The setup checkpoint was refreshed. Continue to review and create when ready.",
      title: "Account Setup can continue",
      tone: "success" as const,
    };
  }
  return {
    badge: "Ready to review",
    copy: "Customer identifiers and company profile are ready for the guarded review/create path.",
    title: "Account Setup can continue",
    tone: "success" as const,
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
      industry: companyProfile.industry.trim(),
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

function companyProfileFromDraftSection(section: Record<string, unknown> | undefined): CompanyProfileForm | null {
  if (!section) {
    return null;
  }
  const organisationName = asText(section.organisation_name);
  const country = asText(section.country);
  const organisationType = asText(section.organisation_type);
  const industry = asText(section.industry);
  const adminContact = asText(section.admin_contact);
  const intendedRole = asText(section.intended_role);
  if (!organisationName || !country || !organisationType || !industry || !adminContact || !intendedRole) {
    return null;
  }
  return {
    organisationName,
    country,
    organisationType,
    industry,
    adminContact,
    intendedRole,
  };
}

function companyProfilesEqual(left: CompanyProfileForm, right: CompanyProfileForm) {
  return (
    left.organisationName.trim() === right.organisationName.trim() &&
    left.country.trim() === right.country.trim() &&
    left.organisationType.trim() === right.organisationType.trim() &&
    left.industry.trim() === right.industry.trim() &&
    left.adminContact.trim() === right.adminContact.trim() &&
    left.intendedRole.trim() === right.intendedRole.trim()
  );
}

function asText(value: unknown) {
  return typeof value === "string" ? value.trim() : "";
}

function safeActionError(error: unknown, fallback: string) {
  const status = typeof error === "object" && error && "status" in error ? Number((error as { status?: number }).status) : null;
  if (status === 409) {
    return draftConflictRecoveryMessage;
  }
  if (status === 422) {
    return "The setup evidence has blockers or unsafe input. No account was created and no live action was taken.";
  }
  return fallback;
}

function safeAccountCreateError(error: unknown) {
  const status = typeof error === "object" && error && "status" in error ? Number((error as { status?: number }).status) : null;
  const code =
    typeof error === "object" && error && "detail" in error
      ? asText((error as { detail?: { code?: unknown } }).detail?.code)
      : "";
  if (status === 409) {
    if (code === "DUPLICATE_INTERNAL_TENANT_SCOPE") {
      return internalScopeAlreadyUsedMessage;
    }
    return accountAlreadyExistsMessage;
  }
  if (status === 422) {
    return "The reviewed setup draft is missing required customer workspace evidence. No workspace, user, campaign, go-live, or money action was taken.";
  }
  if (status === 403) {
    return "Your current session is not allowed to create the customer workspace. No adjacent setup action was taken.";
  }
  return "Customer workspace creation is unavailable. No user, campaign, go-live, or money action was taken.";
}

function deriveInternalSetupTenantScope(externalTenantRef: string, organisationRef: string) {
  const source = `${externalTenantRef}:${organisationRef}`;
  const cleaned = source
    .toUpperCase()
    .replace(/[^A-Z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
  const prefix = (cleaned || "CUSTOMER_SETUP").slice(0, 28);
  let hash = 0;
  for (let index = 0; index < source.length; index += 1) {
    hash = (hash * 31 + source.charCodeAt(index)) >>> 0;
  }
  return `RS_${prefix}_${hash.toString(36).toUpperCase()}`.slice(0, 48);
}

function formatAccountSummary(account: ReferralSaasAccountSummary) {
  return [
    account.accountName || account.accountCode || "Referral SaaS account",
    account.accountStatus || "status unavailable",
    account.tenantLinkStatus ? `workspace scope ${account.tenantLinkStatus}` : "",
  ]
    .filter(Boolean)
    .join(" - ");
}

function customerProfileRoute(account: ReferralSaasAccountSummary | undefined) {
  return account?.accountId
    ? `/admin/referral-saas/account-maintenance/${encodeURIComponent(account.accountId)}`
    : "/admin/referral-saas/account-maintenance";
}

function SetupActionResult({
  createError,
  createResponse,
  draftError,
  draftResponse,
  mode = "technical",
  onChangeCustomerReferences,
  onRefreshSetupStatus,
  reviewError,
  reviewResponse,
  submitError,
  submitResponse,
  validationError,
}: {
  createError: string | null;
  createResponse: ReferralSaasAccountCreateFromDraftResponse | null;
  draftError: string | null;
  draftResponse: AdminOnboardingDraftSaveResponse | null;
  mode?: "guided" | "technical";
  onChangeCustomerReferences: () => void;
  onRefreshSetupStatus: () => void;
  reviewError: string | null;
  reviewResponse: AdminOnboardingReviewDecisionResponse | null;
  submitError: string | null;
  submitResponse: AdminOnboardingSubmitForReviewResponse | null;
  validationError: string | null;
}) {
  const showTechnicalSteps = mode === "technical";
  const createdCustomerProfileRoute = customerProfileRoute(createResponse?.account);

  return (
    <>
      {draftResponse && showTechnicalSteps ? (
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
      {submitResponse && showTechnicalSteps ? (
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
      {reviewResponse && showTechnicalSteps ? (
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
      {mode === "guided" && draftResponse && !createResponse && !createError ? (
        <div className="banner success" role="status">
          <CheckCircle2 size={18} />
          <div>
            <strong>Customer setup evidence saved.</strong>
            <div className="table-subtext">
              You can finish later, or continue now to create the customer workspace.
            </div>
          </div>
        </div>
      ) : null}
      {mode === "guided" && createResponse ? (
        <div className="banner success" role="status">
          <CheckCircle2 size={18} />
          <div>
            <strong>Safe setup review completed.</strong>
            <div className="table-subtext">
              The required setup checks passed without enabling go-live, credentials, billing, settlement, or money movement.
            </div>
          </div>
        </div>
      ) : null}
      {createResponse ? (
        <>
          <div className="banner success" role="status">
            <CheckCircle2 size={18} />
            <div>
              <strong>Customer workspace created.</strong>
              <div className="table-subtext">
                {mode === "guided"
                  ? "Account Setup is complete. Open the customer profile to continue in the selected customer context."
                  : `${formatAccountSummary(createResponse.account)}; adjacent live action: ${
                      createResponse.noAdjacentLiveActionConfirmed ? "blocked" : "unavailable"
                    }.`}
              </div>
            </div>
          </div>
          {mode === "guided" ? (
            <div className="wizard-card route-list" aria-label="Account setup next best actions">
              <div className="wizard-status-card">
                <div>
                  <strong>Next best actions</strong>
                  <p>Choose where to continue now that the customer workspace exists.</p>
                </div>
                <StatusBadge label="Setup complete" tone="success" />
              </div>
              <SetupLink
                to={createdCustomerProfileRoute}
                title="Open customer profile"
                copy="Use this customer home for account health, customer-scoped actions, reports, support, attribution, and progress."
              />
              <SetupLink
                to="/admin/referral-saas/account-maintenance"
                title="Manage access"
                copy="Add or review users, roles, and account access from Account Maintenance."
              />
              <SetupLink
                to="/admin/referral-saas/campaigns"
                title="Start campaign setup"
                copy="Create or review Referral SaaS campaigns after the customer foundation exists."
              />
              <SetupLink
                to="/admin/onboarding/webhook-api"
                title="Configure technical integration"
                copy="Set up API and webhook intent outside Account Setup when the customer is ready."
              />
            </div>
          ) : null}
        </>
      ) : null}
      {[validationError, draftError, submitError, reviewError, createError].filter(Boolean).map((message) => (
        <div className="banner warning" key={message} role="status">
          <ShieldCheck size={18} />
          <div>
            <strong>
              {message === draftConflictRecoveryMessage
                ? "Existing setup draft found."
                : message === internalScopeAlreadyUsedMessage
                  ? "Setup workspace already used."
                : message === accountAlreadyExistsMessage
                  ? "Customer workspace already exists."
                  : "Setup action fallback."}
            </strong>
            <div className="table-subtext">{message}</div>
            {message === draftConflictRecoveryMessage ||
            message === accountAlreadyExistsMessage ||
            message === internalScopeAlreadyUsedMessage ? (
              <div className="action-button-row">
                <button className="button secondary" onClick={onRefreshSetupStatus} type="button">
                  Refresh setup status
                </button>
                {message === accountAlreadyExistsMessage ? (
                  <Link className="button secondary" to="/admin/referral-saas/account-maintenance">
                    Open customer profile
                  </Link>
                ) : null}
                <button className="button secondary" onClick={onChangeCustomerReferences} type="button">
                  Use different customer identifiers
                </button>
              </div>
            ) : null}
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
