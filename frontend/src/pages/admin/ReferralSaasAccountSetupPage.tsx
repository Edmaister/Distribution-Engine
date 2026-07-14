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
          <div className="page-kicker">Referral SaaS - Account Setup Workflow</div>
          <h1 className="page-title">Account setup readiness</h1>
          <p className="page-copy">
            Use this checkpoint inside Account Setup before testing campaigns,
            links, attribution, or reports. It confirms whether setup evidence
            is ready, blocked, or missing.
          </p>
        </div>
        <StatusBadge label={overallStatus} tone={statusTone(overallStatus)} />
      </section>

      <section className="grid-3">
        <div className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Where this fits</h2>
              <div className="panel-subtitle">This is the readiness checkpoint inside Account Setup.</div>
            </div>
            <StatusBadge label="Setup" tone="info" />
          </div>
          <div className="panel-body">
            <p className="page-copy">
              Account Setup is the wider workflow. This screen checks whether
              company profile, tenant link, membership, campaign-readiness, and
              reporting-baseline evidence are ready before moving deeper into
              the product.
            </p>
          </div>
        </div>
        <div className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">What you can do here</h2>
              <div className="panel-subtitle">Review readiness and jump to setup actions.</div>
            </div>
            <ClipboardCheck size={18} />
          </div>
          <div className="panel-body">
            <p className="page-copy">
              You can load safe account references, see what is ready or
              blocked, and open the setup action that captures missing evidence.
              This page does not create accounts or invite users.
            </p>
          </div>
        </div>
        <div className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">What to do next</h2>
              <div className="panel-subtitle">Fix account blockers before campaign testing.</div>
            </div>
            <ArrowRight size={18} />
          </div>
          <div className="panel-body">
            <p className="page-copy">
              First confirm the account scope below. Then resolve any setup
              blockers. Move to campaign readiness only when this checkpoint is
              clear enough for referral testing.
            </p>
          </div>
        </div>
      </section>

      {isLoading ? <LoadingState label="Loading Referral SaaS account setup" /> : null}
      {error ? <ErrorPanel error={error} /> : null}
      {!isLoading && !error ? (
        <>
          <section className="grid-4">
            <KpiCard label="Ready setup gates" value={readyCount} footnote="Can support testing" icon={CheckCircle2} />
            <KpiCard label="Blocked setup gates" value={blockedCount} footnote="Fix before moving on" icon={ShieldCheck} />
            <KpiCard label="Evidence gaps" value={missingEvidenceCount} footnote="Missing setup proof" icon={Building2} />
            <KpiCard label="Launch actions here" value="0" footnote={`${goLiveDisabledCount} go-live blocker shown`} icon={KeyRound} />
          </section>

          <section className="panel">
            <div className="panel-header">
              <div>
                <h2 className="panel-title">Account setup workflow</h2>
                <div className="panel-subtitle">
                  Use this readiness checkpoint as part of setup. Each step contains its own action.
                </div>
              </div>
              <StatusBadge label={nextStep.badge} tone={nextStep.tone} />
            </div>
            <div className="panel-body route-list">
              <div className="route-item">
                <div>
                  <div className="route-name">{nextStep.title}</div>
                  <div className="route-path">{nextStep.copy}</div>
                </div>
                <StatusBadge label={nextStep.actionLabel} tone={nextStep.tone} />
              </div>
            </div>
            <div className="panel-body grid-3">
              <div className="panel">
                <div className="panel-header">
                  <div>
                    <h3 className="panel-title">Step 1: Confirm account scope</h3>
                    <div className="panel-subtitle">
                      Load the account setup evidence you want to review.
                    </div>
                  </div>
                  <StatusBadge label={scopeChanged ? "Changes not checked" : "Loaded"} tone={scopeChanged ? "warning" : "success"} />
                </div>
                <form className="panel-body route-list" onSubmit={submitScope}>
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
                </form>
              </div>

              <div className="panel">
                <div className="panel-header">
                  <div>
                    <h3 className="panel-title">Step 2: Complete setup actions</h3>
                    <div className="panel-subtitle">
                      {needsSetupWork
                        ? "This is your next step because setup still has blocked or missing evidence."
                        : "Skip this for now because this readiness check has no blocker count."}
                    </div>
                  </div>
                  <StatusBadge label={needsSetupWork ? "Do next" : "No blockers"} tone={needsSetupWork ? "warning" : "success"} />
                </div>
                <div className="panel-body route-list">
                  <SetupLink to="/admin/onboarding/company" title="Company onboarding" copy="Capture company evidence and external references." />
                  <SetupLink to="/admin/onboarding/members-roles" title="User and role setup" copy="Confirm owner, campaign manager, support, analyst, and integration roles." />
                  <SetupLink to="/admin/referral-saas/reports" title="Report baseline" copy="Confirm reporting baseline and redaction posture." />
                </div>
              </div>

              <div className="panel">
                <div className="panel-header">
                  <div>
                    <h3 className="panel-title">Step 3: Continue to campaign setup</h3>
                    <div className="panel-subtitle">
                      {needsSetupWork || scopeChanged
                        ? "Wait until account scope is checked and setup blockers are clear."
                        : "This is your next step because account setup is ready enough for campaign testing."}
                    </div>
                  </div>
                  <StatusBadge label={needsSetupWork || scopeChanged ? "Wait" : "Do next"} tone={needsSetupWork || scopeChanged ? "neutral" : "success"} />
                </div>
                <div className="panel-body route-list">
                  <SetupLink
                    to="/admin/referral-saas/campaigns"
                    title="Campaign readiness"
                    copy="Check campaign setup evidence, blockers, warnings, and launch posture."
                  />
                </div>
              </div>
            </div>
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
