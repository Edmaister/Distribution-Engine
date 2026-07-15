import {
  AlertCircle,
  Building2,
  CheckCircle2,
  KeyRound,
  Link as LinkIcon,
  Lock,
  Route,
  ShieldCheck,
  Users,
} from "lucide-react";
import { Link } from "react-router-dom";
import { useState, type FormEvent } from "react";

import { useReferralSaasAccountMaintenanceState } from "../../api/referralSaasAccountQueries";
import { DataTable } from "../../components/DataTable";
import { ErrorPanel } from "../../components/ErrorPanel";
import { KpiCard } from "../../components/KpiCard";
import { LoadingState } from "../../components/LoadingState";
import { StatusBadge } from "../../components/StatusBadge";
import {
  asArray,
  formatDisplay,
  getNestedValue,
  getValue,
  statusTone,
  useRefreshContext,
} from "../pageUtils";

const defaultExternalTenantRef = "demo-platform-operator";
const defaultOrganisationRef = "demo-organisation";

const maintenanceAreas = [
  {
    code: "ACCOUNT_PROFILE",
    title: "Account profile",
    source: "Company setup evidence",
    action: "Review or correct company evidence in Account Setup.",
    route: "/admin/referral-saas/account-setup",
    icon: Building2,
  },
  {
    code: "EXTERNAL_REFERENCES",
    title: "External references",
    source: "Checked account scope",
    action: "Check references again before trusting this maintenance view.",
    route: "/admin/referral-saas/account-setup",
    icon: LinkIcon,
  },
  {
    code: "MEMBERSHIP",
    title: "Users and roles",
    source: "Role setup evidence",
    action: "Correct role intent in Account Setup; invitations remain unavailable.",
    route: "/admin/referral-saas/account-setup",
    icon: Users,
  },
  {
    code: "WEBHOOK_API",
    title: "Integration posture",
    source: "Webhook and API setup evidence",
    action: "Correct integration setup evidence; credentials are not rotated here.",
    route: "/admin/referral-saas/account-setup",
    icon: KeyRound,
  },
  {
    code: "CAMPAIGN_READINESS",
    title: "Campaign handoff",
    source: "Campaign readiness surface",
    action: "Continue to campaign readiness only after setup blockers are understood.",
    route: "/admin/referral-saas/campaigns",
    icon: Route,
  },
  {
    code: "REPORTING_BASELINE",
    title: "Reporting posture",
    source: "Referral SaaS reports",
    action: "Review tenant-safe report posture and export preview guardrails.",
    route: "/admin/referral-saas/reports",
    icon: CheckCircle2,
  },
  {
    code: "AUDIT_SUPPORT",
    title: "Audit and support posture",
    source: "Read-only support surfaces",
    action: "Use support hub for link, progress, and attribution evidence.",
    route: "/admin/referral-saas/support",
    icon: ShieldCheck,
  },
];

const blockedCommands = [
  "Create, activate, suspend, or disable account",
  "Update durable account profile",
  "Invite, remove, or change user roles",
  "Register, rotate, suspend, or disable external references",
  "Rotate credentials or enable webhook delivery",
  "Enable go-live or activate campaign",
  "Retry, replay, or repair events",
  "Reward, funding, fulfilment, settlement, payout, invoice, wallet, or money movement",
];

export function ReferralSaasAccountMaintenancePage() {
  const { refreshKey } = useRefreshContext();
  const [draftExternalTenantRef, setDraftExternalTenantRef] = useState(defaultExternalTenantRef);
  const [draftOrganisationRef, setDraftOrganisationRef] = useState(defaultOrganisationRef);
  const [appliedExternalTenantRef, setAppliedExternalTenantRef] = useState(defaultExternalTenantRef);
  const [appliedOrganisationRef, setAppliedOrganisationRef] = useState(defaultOrganisationRef);
  const scopeChanged =
    draftExternalTenantRef.trim() !== appliedExternalTenantRef ||
    draftOrganisationRef.trim() !== appliedOrganisationRef;
  const canCheckScope = Boolean(draftExternalTenantRef.trim() && draftOrganisationRef.trim() && scopeChanged);
  const { data, error, isLoading } = useReferralSaasAccountMaintenanceState(
    appliedExternalTenantRef,
    appliedOrganisationRef,
    refreshKey,
  );

  const readiness = data?.readiness;
  const summary = readiness?.summary;
  const categories = asArray(readiness?.categories || []);
  const guardrails = asArray(
    (data?.onboarding_state.guardrails || []).map((guardrail) => ({
      name: guardrail,
    })),
  );
  const redactions = asArray(
    (data?.onboarding_state.redactions || []).map((redaction) => ({
      name: redaction,
    })),
  );
  const readyCount = toCount(summary?.ready_count);
  const blockedCount = toCount(summary?.blocked_count);
  const missingEvidenceCount = toCount(summary?.missing_evidence_count);
  const goLiveDisabledCount = toCount(summary?.go_live_disabled_count);
  const overallStatus = formatDisplay(readiness?.overall_status || "read_only_evidence");
  const nextAction = getMaintenanceNextAction(scopeChanged, blockedCount, missingEvidenceCount);
  const areaRows = maintenanceAreas.map((area) => resolveMaintenanceArea(area, categories));

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
          <div className="page-kicker">Referral SaaS - Account Maintenance</div>
          <h1 className="page-title">Account maintenance evidence</h1>
          <p className="page-copy">
            Review account health, setup drift, and safe maintenance evidence.
            Changes still go through Account Setup until durable account and
            membership commands exist.
          </p>
        </div>
        <StatusBadge label="Read-only evidence" tone="info" />
      </section>

      {isLoading ? <LoadingState label="Loading account maintenance evidence" /> : null}
      {error ? <ErrorPanel error={error} /> : null}
      {!isLoading && !error ? (
        <>
          <section className="panel journey-panel" aria-labelledby="maintenance-action-heading">
            <div className="panel-header">
              <div>
                <h2 className="panel-title" id="maintenance-action-heading">
                  What to do on this screen
                </h2>
                <div className="panel-subtitle">
                  Maintenance is a health and evidence view. Fixes route back to setup or related read-only product surfaces.
                </div>
              </div>
              <StatusBadge label={nextAction.badge} tone={nextAction.tone} />
            </div>
            <div className="panel-body">
              <div className="journey-summary">
                <div>
                  <div className="route-name">{nextAction.title}</div>
                  <div className="route-path">{nextAction.copy}</div>
                </div>
                <StatusBadge label={nextAction.step} tone={nextAction.tone} />
              </div>

              <div className="account-setup-action-grid">
                <form className="account-setup-scope-form" onSubmit={submitScope}>
                  <div>
                    <h3 className="panel-title">Step 1: load account evidence</h3>
                    <p className="journey-step-copy">
                      Choose the external references to inspect. Typing stays local until you run the check.
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
                    Check maintenance evidence
                  </button>
                  <StatusBadge label={scopeChanged ? "Changes not checked" : "Loaded"} tone={scopeChanged ? "warning" : "success"} />
                </form>

                <div className="route-list">
                  <div className="route-item">
                    <div>
                      <div className="route-name">Step 2: review health and drift</div>
                      <div className="route-path">
                        Use the maintenance areas below to see what is ready, blocked, or missing evidence.
                      </div>
                    </div>
                    <AlertCircle size={18} />
                  </div>
                  <div className="route-item">
                    <div>
                      <div className="route-name">Current scope</div>
                      <div className="route-path">
                        {appliedExternalTenantRef} / {appliedOrganisationRef}
                      </div>
                    </div>
                    <StatusBadge label="External refs" tone="info" />
                  </div>
                </div>

                <div className="route-list">
                  <div className="route-item">
                    <div>
                      <div className="route-name">Step 3: fix in the right workflow</div>
                      <div className="route-path">
                        Use Account Setup for evidence corrections, Campaigns for readiness, Reports for reporting posture, or Support for diagnostics.
                      </div>
                    </div>
                    <ShieldCheck size={18} />
                  </div>
                  <Link className="route-item route-link" to="/admin/referral-saas/account-setup">
                    <div>
                      <div className="route-name">Open Account Setup</div>
                      <div className="route-path">Correct setup evidence using guarded draft actions.</div>
                    </div>
                    <StatusBadge label="Fix setup" tone="warning" />
                  </Link>
                </div>
              </div>
            </div>
          </section>

          <section className="grid-4">
            <KpiCard label="Ready areas" value={formatDisplay(readyCount)} footnote="Evidence usable for testing" icon={CheckCircle2} />
            <KpiCard label="Blocked areas" value={formatDisplay(blockedCount)} footnote="Route back to setup" icon={ShieldCheck} />
            <KpiCard label="Evidence gaps" value={formatDisplay(missingEvidenceCount)} footnote="Missing setup proof" icon={Building2} />
            <KpiCard label="Maintenance commands" value="0" footnote={`${goLiveDisabledCount} go-live blocker shown`} icon={Lock} />
          </section>

          <section className="grid-2">
            <div className="panel">
              <div className="panel-header">
                <div>
                  <h2 className="panel-title">Maintenance areas</h2>
                  <div className="panel-subtitle">
                    Read-only account health grouped by the product areas operators expect to maintain.
                  </div>
                </div>
                <StatusBadge label={overallStatus} tone={statusTone(overallStatus)} />
              </div>
              <div className="panel-body route-list">
                {areaRows.map((area) => {
                  const Icon = area.icon;
                  return (
                    <Link className="route-item route-link" key={area.code} to={area.route}>
                      <div>
                        <div className="route-name">{area.title}</div>
                        <div className="route-path">{area.evidence}</div>
                        <div className="table-subtext">{area.action}</div>
                      </div>
                      <span className="support-hub-route">
                        <Icon size={15} />
                        {area.status}
                      </span>
                    </Link>
                  );
                })}
              </div>
            </div>

            <div className="panel">
              <div className="panel-header">
                <div>
                  <h2 className="panel-title">Unavailable maintenance commands</h2>
                  <div className="panel-subtitle">
                    These are intentionally absent until real account, membership, lifecycle, and audit primitives exist.
                  </div>
                </div>
                <StatusBadge label="Blocked by design" tone="warning" />
              </div>
              <div className="panel-body route-list">
                {blockedCommands.map((command) => (
                  <div className="route-item" key={command}>
                    <div>
                      <div className="route-name">{command}</div>
                      <div className="route-path">No action is available from this read-only maintenance shell.</div>
                    </div>
                    <StatusBadge label="Unavailable" tone="neutral" />
                  </div>
                ))}
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
                  <div className="panel-subtitle">Fields hidden from the Referral SaaS maintenance surface.</div>
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

function resolveMaintenanceArea(
  area: (typeof maintenanceAreas)[number],
  categories: Record<string, unknown>[],
) {
  const matchingCategory = categories.find((category) => categoryMatches(category, area.code));
  const status = formatDisplay(
    getNestedValue(matchingCategory, ["safe_display_status", "label"], getNestedValue(matchingCategory, ["status"], "Check")),
  );
  return {
    ...area,
    evidence: formatDisplay(getNestedValue(matchingCategory, ["evidence_summary"], area.source)),
    status,
  };
}

function categoryMatches(category: Record<string, unknown>, code: string) {
  const categoryCode = getValue(category, ["category"], "").toUpperCase();
  if (categoryCode === code) {
    return true;
  }
  if (code === "EXTERNAL_REFERENCES") {
    return categoryCode === "TENANT_LINK";
  }
  if (code === "WEBHOOK_API") {
    return categoryCode.includes("WEBHOOK") || categoryCode.includes("API");
  }
  if (code === "AUDIT_SUPPORT") {
    return categoryCode.includes("AUDIT") || categoryCode.includes("SUPPORT");
  }
  return false;
}

function getMaintenanceNextAction(scopeChanged: boolean, blockedCount: number, missingEvidenceCount: number) {
  if (scopeChanged) {
    return {
      badge: "Check changes",
      copy: "You changed the account references. Check maintenance evidence before trusting the health view.",
      step: "Step 1",
      title: "Do this next: reload account evidence",
      tone: "warning" as const,
    };
  }
  if (blockedCount > 0 || missingEvidenceCount > 0) {
    return {
      badge: "Fix in setup",
      copy: "Maintenance found blocked or missing setup evidence. Open Account Setup for the matching area and correct the draft evidence there.",
      step: "Step 3",
      title: "Do this next: route the fix to Account Setup",
      tone: "warning" as const,
    };
  }
  return {
    badge: "Review complete",
    copy: "No blocker count is visible in maintenance evidence. Continue to campaign readiness, reports, or support diagnostics as needed.",
    step: "Step 3",
    title: "Do this next: continue with product testing",
    tone: "success" as const,
  };
}

function toCount(value: unknown) {
  const count = Number(value);
  return Number.isFinite(count) ? count : 0;
}
