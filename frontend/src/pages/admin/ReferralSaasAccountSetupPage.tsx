import { ArrowRight, Building2, CheckCircle2, ClipboardCheck, KeyRound, ShieldCheck, Users } from "lucide-react";
import { Link } from "react-router-dom";
import { useState, type FormEvent } from "react";

import { useReferralSaasAccountSetupState } from "../../api/referralSaasAccountQueries";
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
    copy: "Capture company profile, organisation reference, and primary setup contact evidence.",
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
    copy: "Submit and review actions remain disabled until the product wrapper is implemented.",
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
  const { data, error, isLoading } = useReferralSaasAccountSetupState(
    appliedExternalTenantRef,
    appliedOrganisationRef,
    refreshKey,
  );
  const scopeChanged =
    draftExternalTenantRef.trim() !== appliedExternalTenantRef ||
    draftOrganisationRef.trim() !== appliedOrganisationRef;
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
  const nextStep = getAccountSetupNextStep(scopeChanged, needsSetupWork);
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
                    <h3 className="panel-title">Step 1 action: check account scope</h3>
                    <p className="journey-step-copy">
                      Confirm which setup evidence to load. Typing stays local until you run the check.
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
                    Check readiness
                  </button>
                  <StatusBadge label={scopeChanged ? "Changes not checked" : "Loaded"} tone={scopeChanged ? "warning" : "success"} />
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
                  <SetupLink to="/admin/onboarding/company" title="Company onboarding" copy="Capture company evidence and external references." />
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
                    <div className="route-name">Account creation remains future work</div>
                    <div className="route-path">
                      No account table, membership table, tenant-link write, invitation, or activation is created here.
                    </div>
                  </div>
                  <StatusBadge label="Bounded" tone="info" />
                </div>
                <div className="route-item">
                  <div>
                    <div className="route-name">Internal tenant identifier hidden</div>
                    <div className="route-path">
                      Operators work from external references until trusted account membership is implemented.
                    </div>
                  </div>
                  <StatusBadge label="Redacted" tone="success" />
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
      actionLabel: "Future action",
      actionText: "Requires draft save wrapper",
      badge: "Future",
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
