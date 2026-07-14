import { ArrowRight, Building2, CheckCircle2, ClipboardCheck, KeyRound, ShieldCheck, Users } from "lucide-react";
import { Link } from "react-router-dom";
import { useState } from "react";

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

const setupPath = [
  {
    title: "1. Confirm the account references",
    copy: "Use the external tenant and organisation references to load the account setup view you want to test.",
  },
  {
    title: "2. Fix blocked setup evidence",
    copy: "Use the checklist to find missing account profile, tenant-link, membership, campaign, or reporting evidence.",
  },
  {
    title: "3. Continue only when setup is usable",
    copy: "Move to campaign readiness after account evidence is ready enough for referral testing.",
  },
];

export function ReferralSaasAccountSetupPage() {
  const { refreshKey } = useRefreshContext();
  const [externalTenantRef, setExternalTenantRef] = useState(defaultExternalTenantRef);
  const [organisationRef, setOrganisationRef] = useState(defaultOrganisationRef);
  const { data, error, isLoading } = useReferralSaasAccountSetupState(
    externalTenantRef,
    organisationRef,
    refreshKey,
  );

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
  const readyCount = formatDisplay(getNestedValue(summary, ["ready_count"], 0));
  const blockedCount = formatDisplay(getNestedValue(summary, ["blocked_count"], 0));
  const missingEvidenceCount = formatDisplay(getNestedValue(summary, ["missing_evidence_count"], 0));
  const goLiveDisabledCount = formatDisplay(getNestedValue(summary, ["go_live_disabled_count"], 0));
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

  return (
    <>
      <section className="page-header">
        <div>
          <div className="page-kicker">Referral SaaS - Account Setup</div>
          <h1 className="page-title">Check account setup</h1>
          <p className="page-copy">
            Start here before testing campaigns, links, attribution, or reports.
            This page tells you whether the account setup evidence is ready,
            blocked, or missing.
          </p>
        </div>
        <StatusBadge label={overallStatus} tone={statusTone(overallStatus)} />
      </section>

      <section className="grid-3">
        <div className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">What this screen is for</h2>
              <div className="panel-subtitle">It checks if this SaaS account is ready for referral testing.</div>
            </div>
            <StatusBadge label="Setup" tone="info" />
          </div>
          <div className="panel-body">
            <p className="page-copy">
              Use it to verify account profile, tenant link, membership, campaign
              readiness, and reporting baseline evidence before moving deeper
              into the product.
            </p>
          </div>
        </div>
        <div className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">What you can do here</h2>
              <div className="panel-subtitle">Change the safe account references and review readiness.</div>
            </div>
            <ClipboardCheck size={18} />
          </div>
          <div className="panel-body">
            <p className="page-copy">
              You can load a different external tenant or organisation reference,
              see what is ready or blocked, and choose the next setup surface to
              complete missing evidence.
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
              First confirm the references below. Then review the setup checklist.
              If anything is blocked or missing, use <strong>Next setup actions</strong>
              before moving to campaign readiness.
            </p>
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2 className="panel-title">Account scope</h2>
            <div className="panel-subtitle">
              External references are used for this product surface; internal tenant identifiers stay hidden.
            </div>
          </div>
        </div>
        <div className="panel-body referral-account-controls">
          <label className="field">
            <span>External tenant ref</span>
            <input
              className="input"
              onChange={(event) => setExternalTenantRef(event.target.value)}
              value={externalTenantRef}
            />
          </label>
          <label className="field">
            <span>Organisation ref</span>
            <input
              className="input"
              onChange={(event) => setOrganisationRef(event.target.value)}
              value={organisationRef}
            />
          </label>
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
                <h2 className="panel-title">Recommended setup path</h2>
                <div className="panel-subtitle">
                  Follow this order while testing account setup locally.
                </div>
              </div>
              <StatusBadge label="Start here" tone="success" />
            </div>
            <div className="panel-body route-list">
              {setupPath.map((step) => (
                <div className="route-item" key={step.title}>
                  <div>
                    <div className="route-name">{step.title}</div>
                    <div className="route-path">{step.copy}</div>
                  </div>
                  <StatusBadge label="Guided" tone="info" />
                </div>
              ))}
              <SetupLink
                to="/admin/referral-saas/campaigns"
                title="Next product screen: Campaign readiness"
                copy="Use this after the account setup evidence is ready enough for campaign testing."
              />
            </div>
          </section>

          <section className="grid-2">
            <div className="panel">
              <div className="panel-header">
                <div>
                  <h2 className="panel-title">Setup checklist</h2>
                  <div className="panel-subtitle">
                    Productized account setup gates mapped to existing onboarding evidence.
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
                  <h2 className="panel-title">Next setup actions</h2>
                  <div className="panel-subtitle">Existing surfaces that complete the first SaaS setup path.</div>
                </div>
              </div>
              <div className="panel-body route-list">
                <SetupLink to="/admin/onboarding/company" title="Company onboarding" copy="Save draft company evidence with external references." />
                <SetupLink to="/admin/onboarding/members-roles" title="User & role setup" copy="Draft member and role-family intent before membership APIs exist." />
                <SetupLink to="/admin/onboarding/campaign-opportunity" title="Campaign setup" copy="Continue only after account setup evidence is ready." />
                <SetupLink to="/admin/referral-saas/reports" title="Referral SaaS reports" copy="Confirm report baseline and redaction posture." />
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
