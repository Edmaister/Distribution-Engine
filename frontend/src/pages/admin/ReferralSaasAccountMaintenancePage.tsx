import {
  AlertCircle,
  BarChart3,
  Building2,
  CheckCircle2,
  KeyRound,
  Link as LinkIcon,
  Lock,
  Route,
  Search,
  ShieldCheck,
  Users,
} from "lucide-react";
import { Link } from "react-router-dom";
import { useState, type FormEvent } from "react";

import {
  useReferralSaasAccountDraftSelector,
  useReferralSaasAccountMaintenanceState,
  useReferralSaasAccountRegistry,
} from "../../api/referralSaasAccountQueries";
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
    title: "Client profile",
    source: "Company setup evidence",
    action: "Review customer profile evidence and profile readiness.",
    route: "/admin/referral-saas/account-setup",
    icon: Building2,
  },
  {
    code: "EXTERNAL_REFERENCES",
    title: "Customer identifiers",
    source: "Checked account scope",
    action: "Confirm the selected client references used by product workflows.",
    route: "/admin/referral-saas/account-setup",
    icon: LinkIcon,
  },
  {
    code: "MEMBERSHIP",
    title: "Users and access",
    source: "Role setup evidence",
    action: "Review user access posture; write actions remain future work.",
    route: "/admin/referral-saas/account-maintenance",
    icon: Users,
  },
  {
    code: "WEBHOOK_API",
    title: "Technical setup posture",
    source: "Webhook and API setup evidence",
    action: "Review API and webhook setup evidence; credentials are not rotated here.",
    route: "/admin/onboarding/webhook-api",
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

const clientActivityAreas = [
  {
    title: "Client profile",
    copy: "Maintain customer profile evidence and visible client identifiers.",
    route: "/admin/referral-saas/account-setup",
    icon: Building2,
    status: "Profile",
  },
  {
    title: "Users and access",
    copy: "Review access posture for the selected client; invitation delivery is not enabled yet.",
    route: "/admin/referral-saas/account-maintenance",
    icon: Users,
    status: "Access",
  },
  {
    title: "Technical setup",
    copy: "Capture API and webhook setup intent after the client foundation exists.",
    route: "/admin/onboarding/webhook-api",
    icon: KeyRound,
    status: "Technical",
  },
  {
    title: "Campaigns",
    copy: "Open campaign readiness and setup surfaces for this client.",
    route: "/admin/referral-saas/campaigns",
    icon: Route,
    status: "Campaigns",
  },
  {
    title: "Links and codes",
    copy: "Issue, validate, inspect, and recover referral links and codes.",
    route: "/admin/referral-saas/link-codes",
    icon: LinkIcon,
    status: "Links",
  },
  {
    title: "Attribution trace",
    copy: "Investigate campaign, link, referral, progress, and outcome evidence.",
    route: "/admin/referral-saas/attribution-trace",
    icon: Search,
    status: "Trace",
  },
  {
    title: "Reports",
    copy: "View tenant-safe reporting, export previews, and freshness posture.",
    route: "/admin/referral-saas/reports",
    icon: BarChart3,
    status: "Reports",
  },
  {
    title: "Support hub",
    copy: "Triage validation, link/code, progress, and attribution evidence.",
    route: "/admin/referral-saas/support",
    icon: ShieldCheck,
    status: "Support",
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
  const {
    data: draftSelector,
    error: draftSelectorError,
    isLoading: isDraftSelectorLoading,
  } = useReferralSaasAccountDraftSelector(appliedExternalTenantRef, appliedOrganisationRef, refreshKey);
  const {
    data: accountRegistry,
    error: accountRegistryError,
    isLoading: isAccountRegistryLoading,
  } = useReferralSaasAccountRegistry(50, refreshKey);

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
  const draftItems = draftSelector?.items || [];
  const accountItems = accountRegistry?.accounts || [];
  const selectedAccount = findSelectedAccount(accountItems, appliedExternalTenantRef, appliedOrganisationRef);
  const selectedClientName = selectedAccount?.accountName || appliedOrganisationRef || appliedExternalTenantRef;

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

  function selectAccount(account: NonNullable<typeof accountRegistry>["accounts"][number]) {
    const externalTenantRef =
      account.primaryExternalTenantRef ||
      findAccountExternalRef(account.externalReferences, "external_tenant_ref");
    const organisationRef = findAccountExternalRef(account.externalReferences, "organisation_ref");
    if (!externalTenantRef || !organisationRef) {
      return;
    }
    setDraftExternalTenantRef(externalTenantRef);
    setDraftOrganisationRef(organisationRef);
    setAppliedExternalTenantRef(externalTenantRef);
    setAppliedOrganisationRef(organisationRef);
  }

  return (
    <>
      <section className="page-header">
        <div>
          <div className="page-kicker">Referral SaaS - Account Maintenance</div>
          <h1 className="page-title">Client workspace</h1>
          <p className="page-copy">
            Select a client, review the client profile and readiness posture,
            then open the activities and dashboards for that client.
          </p>
        </div>
        <StatusBadge label="Client-scoped" tone="info" />
      </section>

      {isLoading ? <LoadingState label="Loading client workspace" /> : null}
      {error ? <ErrorPanel error={error} /> : null}
      {!isLoading && !error ? (
        <>
          <section className="panel journey-panel" aria-labelledby="maintenance-action-heading">
            <div className="panel-header">
              <div>
                <h2 className="panel-title" id="maintenance-action-heading">
                  Start with a client
                </h2>
                <div className="panel-subtitle">
                  Create the client in Account Setup first. Then select it here before working on profile, campaigns, attribution, reports, or support.
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

              <div className="route-list">
                <div className="route-item">
                  <div>
                    <div className="route-name">Step 1: select the client</div>
                    <div className="route-path">
                      Start from the real client foundation list. Drafts below are only for setup evidence that has not become a client yet.
                    </div>
                  </div>
                  <StatusBadge label={`${accountItems.length} clients`} tone={accountItems.length ? "info" : "neutral"} />
                </div>
                {isAccountRegistryLoading ? <LoadingState label="Loading account list" /> : null}
                {accountRegistryError ? <ErrorPanel error={accountRegistryError} /> : null}
                {!isAccountRegistryLoading && !accountRegistryError && accountItems.length === 0 ? (
                  <div className="empty-state">
                    No clients are available yet. Use Account Setup to create the first client foundation.
                  </div>
                ) : null}
                {!isAccountRegistryLoading && !accountRegistryError
                  ? accountItems.map((account) => {
                      const externalTenantRef =
                        account.primaryExternalTenantRef ||
                        findAccountExternalRef(account.externalReferences, "external_tenant_ref");
                      const organisationRef = findAccountExternalRef(account.externalReferences, "organisation_ref");
                      const canSelectAccount = Boolean(externalTenantRef && organisationRef);
                      return (
                        <button
                          className="route-item route-link"
                          disabled={!canSelectAccount}
                          key={account.accountId}
                          onClick={() => selectAccount(account)}
                          type="button"
                        >
                          <div>
                            <div className="route-name">{account.accountName}</div>
                            <div className="route-path">
                              {externalTenantRef || "Missing customer reference"} / {organisationRef || "Missing organisation reference"}
                            </div>
                            <div className="table-subtext">
                              {account.accountCode} - {formatDisplay(account.accountStatus)} - onboarding {formatDisplay(account.onboardingStatus)}
                            </div>
                          </div>
                          <StatusBadge label={isSelectedAccount(account, appliedExternalTenantRef, appliedOrganisationRef) ? "Selected" : canSelectAccount ? "Select" : "Incomplete refs"} tone={isSelectedAccount(account, appliedExternalTenantRef, appliedOrganisationRef) ? "success" : canSelectAccount ? "info" : "warning"} />
                        </button>
                      );
                    })
                  : null}
              </div>

              <div className="grid-3">
                <div className="route-item">
                  <div>
                    <div className="route-name">Selected client</div>
                    <div className="route-path">{selectedClientName}</div>
                    <div className="table-subtext">
                      {appliedExternalTenantRef} / {appliedOrganisationRef}
                    </div>
                  </div>
                  <StatusBadge label={selectedAccount ? "Durable client" : "Manual lookup"} tone={selectedAccount ? "success" : "warning"} />
                </div>
                <div className="route-item">
                  <div>
                    <div className="route-name">Client status</div>
                    <div className="route-path">
                      {selectedAccount
                        ? `${formatDisplay(selectedAccount.accountStatus)} - onboarding ${formatDisplay(selectedAccount.onboardingStatus)}`
                        : "No durable client selected from the registry yet."}
                    </div>
                  </div>
                  <StatusBadge label={overallStatus} tone={statusTone(overallStatus)} />
                </div>
                <Link className="route-item route-link" to="/admin/referral-saas/account-setup">
                  <div>
                    <div className="route-name">Create new client</div>
                    <div className="route-path">Start a new client foundation before profile, campaign, or reporting work.</div>
                  </div>
                  <StatusBadge label="Account Setup" tone="info" />
                </Link>
              </div>

              <div className="account-setup-action-grid">
                <form className="account-setup-scope-form" onSubmit={submitScope}>
                  <div>
                    <h3 className="panel-title">Manual lookup</h3>
                    <p className="journey-step-copy">
                      Use only when a client is not listed yet or you need to inspect saved setup evidence by customer identifiers.
                    </p>
                  </div>
                  <label className="field">
                    <span>Customer reference</span>
                    <input
                      className="input"
                      onChange={(event) => setDraftExternalTenantRef(event.target.value)}
                      value={draftExternalTenantRef}
                    />
                  </label>
                  <label className="field">
                    <span>Organisation reference</span>
                    <input
                      className="input"
                      onChange={(event) => setDraftOrganisationRef(event.target.value)}
                      value={draftOrganisationRef}
                    />
                  </label>
                  <button className="button" disabled={!canCheckScope} type="submit">
                    Check client evidence
                  </button>
                  <StatusBadge label={scopeChanged ? "Changes not checked" : "Loaded"} tone={scopeChanged ? "warning" : "success"} />
                </form>

                <div className="route-list">
                  <div className="route-item">
                    <div>
                      <div className="route-name">Step 2: review client health</div>
                      <div className="route-path">
                        Use the workspace summary to see what is ready, blocked, or missing evidence for the selected client.
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
                      <div className="route-name">Step 3: open the right client activity</div>
                      <div className="route-path">
                        Use the activity cards below for profile, users, technical setup, campaigns, links, attribution, reports, or support.
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
            <KpiCard label="Ready areas" value={formatDisplay(readyCount)} footnote="Usable for client testing" icon={CheckCircle2} />
            <KpiCard label="Blocked areas" value={formatDisplay(blockedCount)} footnote="Needs client setup work" icon={ShieldCheck} />
            <KpiCard label="Evidence gaps" value={formatDisplay(missingEvidenceCount)} footnote="Missing client proof" icon={Building2} />
            <KpiCard label="Live actions" value="0" footnote={`${goLiveDisabledCount} go-live blocker shown`} icon={Lock} />
          </section>

          <section className="panel">
            <div className="panel-header">
              <div>
                <h2 className="panel-title">Client workspace summary</h2>
                <div className="panel-subtitle">
                  This is the selected client posture. It tells you whether to complete profile/setup work or continue into product activities.
                </div>
              </div>
              <StatusBadge label={overallStatus} tone={statusTone(overallStatus)} />
            </div>
            <div className="panel-body route-list">
              <div className={`wizard-summary-strip ${blockedCount || missingEvidenceCount ? "warning" : "success"}`}>
                <StatusBadge label={blockedCount || missingEvidenceCount ? "Needs attention" : "Ready"} tone={blockedCount || missingEvidenceCount ? "warning" : "success"} />
                <div>
                  <strong>{formatAreaCount(blockedCount, "blocked area")}, {formatAreaCount(missingEvidenceCount, "evidence gap")}</strong>
                  <span>
                    {formatDisplay(readyCount)} areas ready. Profile, access, technical setup, campaign readiness, reporting, guardrails, and redactions are reviewed here.
                  </span>
                </div>
              </div>
              <DataTable
                rows={categories}
                emptyText="No readiness categories returned."
                columns={[
                  {
                    key: "category",
                    header: "Area",
                    render: (row) => (
                      <span className="mono">
                        {formatDisplay(getValue(row, ["display_label"], getValue(row, ["category"], "Readiness area")))}
                      </span>
                    ),
                  },
                  {
                    key: "status",
                    header: "Status",
                    render: (row) => {
                      const label = formatDisplay(
                        getNestedValue(row, ["safe_display_status", "label"], getNestedValue(row, ["status"], "Check")),
                      );
                      return <StatusBadge label={label} tone={statusTone(label)} />;
                    },
                  },
                  {
                    key: "evidence",
                    header: "Evidence",
                    render: (row) => <span className="table-subtext">{formatDisplay(getValue(row, ["evidence_summary"], "No evidence summary returned."))}</span>,
                  },
                ]}
              />
            </div>
          </section>

          <section className="panel">
            <div className="panel-header">
              <div>
                <h2 className="panel-title">Client activities and dashboards</h2>
                <div className="panel-subtitle">
                  Open these after selecting the client. Each surface remains bounded to Referral SaaS referral management and campaign attribution work.
                </div>
              </div>
              <StatusBadge label="Referral SaaS only" tone="success" />
            </div>
            <div className="panel-body grid-4">
              {clientActivityAreas.map((area) => {
                const Icon = area.icon;
                return (
                  <Link className="route-item route-link" key={area.title} to={area.route}>
                    <div>
                      <div className="route-name">{area.title}</div>
                      <div className="route-path">{area.copy}</div>
                    </div>
                    <span className="support-hub-route">
                      <Icon size={15} />
                      {area.status}
                    </span>
                  </Link>
                );
              })}
            </div>
          </section>

          <section className="panel">
            <div className="panel-header">
              <div>
                  <h2 className="panel-title">Setup draft fallback</h2>
                <div className="panel-subtitle">
                  Use this only when the customer has saved setup evidence but no durable account foundation is available in the account list.
                </div>
              </div>
              <StatusBadge label={`${draftItems.length} drafts`} tone={draftItems.length ? "info" : "neutral"} />
            </div>
            <div className="panel-body route-list">
              {isDraftSelectorLoading ? <LoadingState label="Loading setup drafts" /> : null}
              {draftSelectorError ? <ErrorPanel error={draftSelectorError} /> : null}
              {!isDraftSelectorLoading && !draftSelectorError && draftItems.length === 0 ? (
                <div className="empty-state">
                  No saved setup drafts found for this external scope. Use Account Setup to save setup intent first.
                </div>
              ) : null}
              {!isDraftSelectorLoading && !draftSelectorError
                ? draftItems.map((draft) => (
                    <button
                      className="route-item route-link"
                      key={draft.draft_ref}
                      onClick={() => {
                        setDraftExternalTenantRef(draft.external_tenant_ref);
                        setDraftOrganisationRef(draft.organisation_ref);
                        setAppliedExternalTenantRef(draft.external_tenant_ref);
                        setAppliedOrganisationRef(draft.organisation_ref);
                      }}
                      type="button"
                    >
                      <div>
                        <div className="route-name">{draft.organisation_ref || draft.draft_ref}</div>
                        <div className="route-path">
                          {draft.external_tenant_ref} - {draft.draft_status || "Draft evidence"}
                        </div>
                        <div className="table-subtext">
                          {draft.draft_ref} - readiness {formatDisplay(draft.readiness_status || "unknown")} - blockers {formatDisplay(draft.blocker_count || 0)}
                        </div>
                      </div>
                      <StatusBadge label="Load evidence" tone="info" />
                    </button>
                  ))
                : null}
            </div>
          </section>

          <section className="grid-2">
            <div className="panel">
              <div className="panel-header">
                <div>
                  <h2 className="panel-title">Client readiness details</h2>
                  <div className="panel-subtitle">
                    Read-only health grouped by the product areas operators expect to maintain.
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
      copy: "You changed the client identifiers. Check client evidence before trusting the workspace view.",
      step: "Step 1",
      title: "Do this next: check the client again",
      tone: "warning" as const,
    };
  }
  if (blockedCount > 0 || missingEvidenceCount > 0) {
    return {
      badge: "Needs attention",
      copy: "Review the selected client summary, then open the matching activity card for profile, access, technical setup, campaign readiness, reports, or support.",
      step: "Workspace",
      title: "Do this next: open the client workspace",
      tone: "warning" as const,
    };
  }
  return {
    badge: "Review complete",
    copy: "No blocker count is visible for this client. Continue to campaign readiness, links/codes, attribution, reports, or support diagnostics as needed.",
    step: "Activities",
    title: "Do this next: continue with client activities",
    tone: "success" as const,
  };
}

function toCount(value: unknown) {
  const count = Number(value);
  return Number.isFinite(count) ? count : 0;
}

function formatAreaCount(count: number, singularLabel: string) {
  return `${formatDisplay(count)} ${count === 1 ? singularLabel : `${singularLabel}s`}`;
}

function findAccountExternalRef(
  references: { refType: string; externalRef: string }[] = [],
  refType: string,
) {
  return references.find((reference) => reference.refType === refType)?.externalRef || "";
}

function findSelectedAccount(
  accounts: NonNullable<ReturnType<typeof useReferralSaasAccountRegistry>["data"]>["accounts"] = [],
  externalTenantRef: string,
  organisationRef: string,
) {
  return accounts.find((account) => isSelectedAccount(account, externalTenantRef, organisationRef));
}

function isSelectedAccount(
  account: NonNullable<ReturnType<typeof useReferralSaasAccountRegistry>["data"]>["accounts"][number],
  externalTenantRef: string,
  organisationRef: string,
) {
  const accountExternalTenantRef =
    account.primaryExternalTenantRef ||
    findAccountExternalRef(account.externalReferences, "external_tenant_ref");
  const accountOrganisationRef = findAccountExternalRef(account.externalReferences, "organisation_ref");
  return accountExternalTenantRef === externalTenantRef && accountOrganisationRef === organisationRef;
}
