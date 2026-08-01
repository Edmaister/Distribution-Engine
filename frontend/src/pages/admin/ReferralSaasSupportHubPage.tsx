import {
  AlertTriangle,
  CheckCircle2,
  FileWarning,
  GitBranch,
  Link as LinkIcon,
  RefreshCw,
  Search,
  ShieldCheck,
  Split,
  Target,
  type LucideIcon,
} from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";

import { useReferralSaasOperatorSupportQueue } from "../../api/referralSaasAccountQueries";
import type { ReferralSaasOperatorSupportQueueItem } from "../../api/endpoints/referralSaasAccounts";
import { DataTable } from "../../components/DataTable";
import { ErrorPanel } from "../../components/ErrorPanel";
import { KpiCard } from "../../components/KpiCard";
import { LoadingState } from "../../components/LoadingState";
import { StatusBadge } from "../../components/StatusBadge";
import { formatDisplay, statusTone, useRefreshContext } from "../pageUtils";

type SupportCase = {
  title: string;
  category: string;
  lookup: string;
  route: string;
  routeLabel: string;
  description: string;
  icon: LucideIcon;
};

type QueueFilters = {
  status: string;
  priority: string;
  category: string;
  accountRef: string;
  sourceSurface: string;
};

const statusOptions = [
  { label: "All open work", value: "" },
  { label: "Open", value: "OPEN" },
  { label: "Investigating", value: "INVESTIGATING" },
  { label: "Waiting", value: "WAITING" },
  { label: "Resolved", value: "RESOLVED" },
  { label: "Closed", value: "CLOSED" },
];

const priorityOptions = [
  { label: "All priorities", value: "" },
  { label: "Critical", value: "CRITICAL" },
  { label: "High", value: "HIGH" },
  { label: "Medium", value: "MEDIUM" },
  { label: "Low", value: "LOW" },
];

const categoryOptions = [
  { label: "All case types", value: "" },
  { label: "Access scope", value: "ACCESS_SCOPE" },
  { label: "Validation recovery", value: "VALIDATION_RECOVERY" },
  { label: "Progress diagnostic", value: "PROGRESS_DIAGNOSTIC" },
  { label: "Attribution review", value: "ATTRIBUTION_REVIEW" },
  { label: "Campaign readiness", value: "READINESS_BLOCKER" },
  { label: "Reporting freshness", value: "REPORTING_FRESHNESS" },
  { label: "Integration setup", value: "INTEGRATION_HEALTH" },
  { label: "Manual review", value: "MANUAL_REVIEW_REQUIRED" },
];

const sourceSurfaceOptions = [
  { label: "All source pages", value: "" },
  { label: "People and Access", value: "people_access" },
  { label: "Customer settings", value: "customer_settings" },
  { label: "Integrations", value: "integrations" },
  { label: "Campaigns", value: "campaigns" },
  { label: "Links and Codes", value: "links_codes" },
  { label: "Reports", value: "reports" },
  { label: "Support", value: "support" },
];

const supportCases: SupportCase[] = [
  {
    title: "Code or link not recognized",
    category: "VALIDATION_RECOVERY",
    lookup: "Referral code, campaign code, route link, or composite code",
    route: "/admin/referral-saas/operator-links",
    routeLabel: "Inspect link/code",
    description: "Start from canonical link/code inspection before opening trace or progress views.",
    icon: LinkIcon,
  },
  {
    title: "Validation failed or customer cannot continue",
    category: "VALIDATION_RECOVERY",
    lookup: "Referral code, alias, terms context, or referral track",
    route: "/admin/referral-saas/link-codes",
    routeLabel: "Review link/code workflow",
    description: "Use product validation recovery and retry posture without creating duplicate support actions.",
    icon: AlertTriangle,
  },
  {
    title: "Progress stuck or delayed",
    category: "PROGRESS_DIAGNOSTIC",
    lookup: "Referral track ID",
    route: "/admin/referral-saas/progress-status",
    routeLabel: "Inspect progress/status",
    description: "Review safe progress, product status, missing evidence, redactions, and next diagnostics.",
    icon: CheckCircle2,
  },
  {
    title: "Attribution missing or partial",
    category: "ATTRIBUTION_REVIEW",
    lookup: "Referral track ID",
    route: "/admin/referral-saas/attribution-trace",
    routeLabel: "Inspect attribution trace",
    description: "Connect outcome, attribution, participant, event, and audit evidence through the trace surface.",
    icon: Split,
  },
  {
    title: "Campaign not ready",
    category: "READINESS_BLOCKER",
    lookup: "Campaign code",
    route: "/admin/referral-saas/campaigns",
    routeLabel: "Review campaign readiness",
    description: "Review setup blockers and warnings without exposing activation controls.",
    icon: Target,
  },
  {
    title: "Report count mismatch",
    category: "REPORTING_FRESHNESS",
    lookup: "Report type, campaign, and date window",
    route: "/admin/referral-saas/reports",
    routeLabel: "Review Referral SaaS reports",
    description: "Use tenant-safe reports, freshness, warnings, redactions, and inline previews.",
    icon: FileWarning,
  },
];

const guardrails = [
  "Read-only cross-customer queue",
  "Open cases inside the selected customer profile",
  "No assignment, repair, retry, or replay",
  "No invite, credential, auth, export, billing, or money actions",
  "No raw evidence, provider payloads, UCNs, tokens, or internal tenant identifiers",
];

export function ReferralSaasSupportHubPage() {
  const { refreshKey } = useRefreshContext();
  const [localRefreshKey, setLocalRefreshKey] = useState(0);
  const [filters, setFilters] = useState<QueueFilters>({
    status: "",
    priority: "",
    category: "",
    accountRef: "",
    sourceSurface: "",
  });

  const queueQuery = useReferralSaasOperatorSupportQueue(
    {
      status: filters.status,
      priority: filters.priority,
      category: filters.category,
      accountRef: filters.accountRef,
      sourceSurface: filters.sourceSurface,
      limit: 50,
    },
    refreshKey + localRefreshKey,
  );
  const queueItems = queueQuery.data?.supportQueue.supportCases || [];
  const openItems = queueItems.filter((item) => !["RESOLVED", "CLOSED"].includes(item.status));
  const investigatingCount = queueItems.filter((item) => item.status === "INVESTIGATING").length;
  const waitingCount = queueItems.filter((item) => item.status === "WAITING").length;
  const criticalCount = queueItems.filter((item) => item.priority === "CRITICAL").length;

  return (
    <>
      <section className="page-header">
        <div>
          <div className="page-kicker">Referral SaaS - Operator Support</div>
          <h1 className="page-title">Support queue</h1>
          <p className="page-copy">
            Triage support cases across Referral SaaS customers, then open the selected
            customer Support page to work the case. This queue is read-only.
          </p>
        </div>
        <StatusBadge label="Read-only queue" tone="info" />
      </section>

      <section className="grid-4">
        <KpiCard label="Open work" value={openItems.length} footnote="Unresolved cases" icon={Search} />
        <KpiCard label="Investigating" value={investigatingCount} footnote="Operator is reviewing" icon={ShieldCheck} />
        <KpiCard label="Waiting" value={waitingCount} footnote="Blocked on evidence" icon={AlertTriangle} />
        <KpiCard label="Critical" value={criticalCount} footnote="Highest priority" icon={GitBranch} />
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2 className="panel-title">Queue filters</h2>
            <div className="panel-subtitle">
              Narrow the queue without exposing tenant codes or raw support evidence.
            </div>
          </div>
          <button
            className="button secondary"
            onClick={() => setLocalRefreshKey((current) => current + 1)}
            type="button"
          >
            <RefreshCw size={15} />
            Refresh queue
          </button>
        </div>
        <div className="panel-body account-setup-scope-form">
          <SelectField
            label="Status"
            onChange={(status) => setFilters((current) => ({ ...current, status }))}
            options={statusOptions}
            value={filters.status}
          />
          <SelectField
            label="Priority"
            onChange={(priority) => setFilters((current) => ({ ...current, priority }))}
            options={priorityOptions}
            value={filters.priority}
          />
          <SelectField
            label="Case type"
            onChange={(category) => setFilters((current) => ({ ...current, category }))}
            options={categoryOptions}
            value={filters.category}
          />
          <SelectField
            label="Source page"
            onChange={(sourceSurface) => setFilters((current) => ({ ...current, sourceSurface }))}
            options={sourceSurfaceOptions}
            value={filters.sourceSurface}
          />
          <label className="field">
            <span>Account reference</span>
            <input
              aria-label="Account reference"
              className="input"
              onChange={(event) => setFilters((current) => ({ ...current, accountRef: event.target.value }))}
              placeholder="Optional account code or account id"
              value={filters.accountRef}
            />
          </label>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2 className="panel-title">Cases needing attention</h2>
            <div className="panel-subtitle">
              Open a case inside the selected customer profile for notes or status changes.
            </div>
          </div>
          <StatusBadge label={`${queueItems.length} returned`} tone={queueItems.length ? "info" : "success"} />
        </div>
        <div className="panel-body route-list">
          {queueQuery.error ? <ErrorPanel error={queueQuery.error} /> : null}
          {queueQuery.isLoading ? (
            <LoadingState label="Loading support queue" />
          ) : (
            <DataTable
              rows={queueItems}
              emptyText="No support cases match these filters."
              columns={[
                {
                  key: "case",
                  header: "Case",
                  render: (row) => (
                    <div>
                      <strong>{row.title || "Support case"}</strong>
                      <div className="table-subtext">{row.customerLabel || "Customer label unavailable"}</div>
                      <div className="table-subtext">{row.caseRef}</div>
                    </div>
                  ),
                },
                {
                  key: "type",
                  header: "Type",
                  render: (row) => formatDisplay(row.category || "Support"),
                },
                {
                  key: "priority",
                  header: "Priority",
                  render: (row) => (
                    <StatusBadge label={formatDisplay(row.priority || "Medium")} tone={statusTone(row.priority)} />
                  ),
                },
                {
                  key: "status",
                  header: "Status",
                  render: (row) => (
                    <StatusBadge label={formatDisplay(row.status || "Open")} tone={statusTone(row.status)} />
                  ),
                },
                {
                  key: "activity",
                  header: "Latest activity",
                  render: (row) => (
                    <div>
                      <strong>{row.latestActivity || "Case updated"}</strong>
                      <div className="table-subtext">
                        {row.evidenceLinkCount} evidence link{row.evidenceLinkCount === 1 ? "" : "s"} -{" "}
                        {row.noteCount} note{row.noteCount === 1 ? "" : "s"}
                      </div>
                    </div>
                  ),
                },
                {
                  key: "action",
                  header: "Next action",
                  render: (row) => <OpenCaseLink item={row} />,
                },
              ]}
            />
          )}
          <div className="wizard-status-card">
            <div>
              <strong>What this queue will not do</strong>
              <p>
                It does not assign cases, change status, add notes, repair referrals, replay events,
                deliver invites, create credentials, activate campaigns, export files, bill, or move money.
              </p>
            </div>
            <StatusBadge label="No mutations" tone="success" />
          </div>
        </div>
      </section>

      <section className="grid-2">
        <div className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Diagnostic shortcuts</h2>
              <div className="panel-subtitle">Use these when there is not yet a persisted support case.</div>
            </div>
          </div>
          <div className="panel-body route-list">
            {supportCases.map((item) => {
              const Icon = item.icon;
              return (
                <Link className="route-item route-link" key={item.title} to={item.route}>
                  <div>
                    <div className="route-name">{item.title}</div>
                    <div className="route-path">{item.description}</div>
                    <div className="route-path">Lookup: {item.lookup}</div>
                  </div>
                  <div className="support-hub-action">
                    <StatusBadge label={item.category} tone="info" />
                    <span className="support-hub-route">
                      <Icon size={15} />
                      {item.routeLabel}
                    </span>
                  </div>
                </Link>
              );
            })}
          </div>
        </div>

        <div className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Guardrails</h2>
              <div className="panel-subtitle">The queue does not authorize support mutations.</div>
            </div>
            <ShieldCheck size={18} />
          </div>
          <div className="panel-body route-list">
            {guardrails.map((guardrail) => (
              <div className="route-item" key={guardrail}>
                <div>
                  <div className="route-name">{guardrail}</div>
                  <div className="route-path">Deferred unless a later task adds role, audit, idempotency, and tests.</div>
                </div>
                <StatusBadge label="Guarded" tone="warning" />
              </div>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}

function SelectField({
  label,
  onChange,
  options,
  value,
}: {
  label: string;
  onChange: (value: string) => void;
  options: Array<{ label: string; value: string }>;
  value: string;
}) {
  return (
    <label className="field">
      <span>{label}</span>
      <select
        aria-label={label}
        className="input"
        onChange={(event) => onChange(event.target.value)}
        value={value}
      >
        {options.map((option) => (
          <option key={option.value || option.label} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function OpenCaseLink({ item }: { item: ReferralSaasOperatorSupportQueueItem }) {
  const supportRoute = `/admin/referral-saas/account-maintenance/${encodeURIComponent(
    item.accountRef,
  )}/support`;
  return (
    <div>
      <Link className="button secondary" to={supportRoute}>
        Open customer support case
      </Link>
      <div className="table-subtext">{item.nextAction || "Open selected customer support"}</div>
    </div>
  );
}
