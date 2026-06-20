import { CheckCircle2, Eye, ShieldCheck, UserCog } from "lucide-react";
import { useAdminAudit } from "../../api/operationalQueries";
import { DataTable } from "../../components/DataTable";
import { ErrorPanel } from "../../components/ErrorPanel";
import { KpiCard } from "../../components/KpiCard";
import { LoadingState } from "../../components/LoadingState";
import { StatusBadge } from "../../components/StatusBadge";
import { SummaryItem } from "../../components/SummaryItem";
import { countFrom, getValue, useRefreshContext } from "../pageUtils";

export function AdminAuditPage() {
  const { refreshKey } = useRefreshContext();
  const { data, error, isLoading } = useAdminAudit(24, 25, refreshKey);

  if (isLoading) {
    return <LoadingState label="Loading audit log" />;
  }

  if (error) {
    return <ErrorPanel error={error} />;
  }

  const rows = data?.rows || [];
  const auditTotal = countFrom(data?.summary, [
    "total",
    "total_count",
    "audit_count",
  ]);
  const domains = uniqueCount(rows, ["action_domain", "domain"]);
  const actors = uniqueCount(rows, ["actor_id", "actor", "api_key_label"]);
  const actions = uniqueCount(rows, ["action_type", "action"]);
  const recentActivity = rows.length > 0;

  return (
    <>
      <section className="page-header">
        <div>
          <div className="page-kicker">Amplifi Admin - Trust & Audit</div>
          <h1 className="page-title">Trust & Audit</h1>
          <p className="page-copy">
            Review sensitive operator actions across finance, distribution,
            settlement, event, and platform workflows so control decisions
            remain visible and accountable.
          </p>
        </div>
        <StatusBadge
          label={recentActivity ? "Audit active" : "No recent records"}
          tone={recentActivity ? "success" : "neutral"}
        />
      </section>

      <section className="trust-audit-grid">
        <div className="trust-audit-card primary">
          <div className="trust-audit-card-top">
            <div>
              <div className="trust-audit-kicker">Trust posture</div>
              <h2>
                {recentActivity
                  ? "Sensitive actions are visible"
                  : "No recent sensitive actions"}
              </h2>
            </div>
            <CheckCircle2 size={24} />
          </div>
          <p>
            Audit records show who performed a controlled action, which domain
            it affected, and when it was recorded. This gives Amplifi Admin an
            accountability trail across the operating system.
          </p>
          <div className="trust-audit-metrics">
            <SummaryItem label="24h total" value={auditTotal} />
            <SummaryItem label="Returned rows" value={rows.length} />
            <SummaryItem label="Domains" value={domains} />
            <SummaryItem label="Actors" value={actors} />
          </div>
        </div>

        <div className="panel trust-action-map">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Operator action map</h2>
              <div className="panel-subtitle">
                Where to inspect trust and accountability signals.
              </div>
            </div>
          </div>
          <div className="panel-body admin-attention-list">
            <AuditActionMapRow
              label="Review recent activity"
              copy="Inspect the latest sensitive actions returned by the audit API."
              targetId="audit-recent-activity"
              value={`${rows.length} rows`}
              tone={rows.length ? "info" : "neutral"}
            />
            <AuditActionMapRow
              label="Check actor coverage"
              copy="Confirm which operators or API keys have performed controlled actions."
              targetId="audit-recent-activity"
              value={`${actors} actors`}
              tone={actors ? "info" : "neutral"}
            />
            <AuditActionMapRow
              label="Check domain coverage"
              copy="See whether finance, distribution, settlement, or system domains are represented."
              targetId="audit-domain-summary"
              value={`${domains} domains`}
              tone={domains ? "success" : "neutral"}
            />
            <AuditActionMapRow
              label="Trace action types"
              copy="Use action names to explain what changed before investigating backend outcomes."
              targetId="audit-domain-summary"
              value={`${actions} actions`}
              tone={actions ? "info" : "neutral"}
            />
          </div>
        </div>
      </section>

      <section className="grid-3">
        <KpiCard
          label="Audit records"
          value={rows.length}
          footnote="Latest returned rows"
          icon={ShieldCheck}
        />
        <KpiCard
          label="24h total"
          value={auditTotal}
          footnote="Summary endpoint"
          icon={UserCog}
        />
        <KpiCard
          label="Scope"
          value="Admin"
          footnote="Platform sensitive actions"
          icon={ShieldCheck}
        />
      </section>

      <section className="grid-2" id="audit-domain-summary">
        <div className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Coverage summary</h2>
              <div className="panel-subtitle">
                A quick read of domains, actors, and action variety.
              </div>
            </div>
            <Eye size={18} />
          </div>
          <div className="panel-body">
            <div className="summary-grid">
              <SummaryItem label="Domains" value={domains} />
              <SummaryItem label="Actors" value={actors} />
              <SummaryItem label="Action types" value={actions} />
            </div>
          </div>
        </div>

        <div className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Audit interpretation</h2>
              <div className="panel-subtitle">
                How to use this page during operations.
              </div>
            </div>
          </div>
          <div className="panel-body route-list">
            <div className="route-item">
              <div>
                <div className="route-name">Who acted?</div>
                <div className="route-path">
                  Use the actor column to identify the operator or API key.
                </div>
              </div>
              <StatusBadge label="Actor" tone="info" />
            </div>
            <div className="route-item">
              <div>
                <div className="route-name">What changed?</div>
                <div className="route-path">
                  Use domain and action type to explain the controlled
                  operation.
                </div>
              </div>
              <StatusBadge label="Action" tone="info" />
            </div>
          </div>
        </div>
      </section>

      <section className="panel" id="audit-recent-activity">
        <div className="panel-header">
          <div>
            <h2 className="panel-title">Recent activity</h2>
            <div className="panel-subtitle">
              Last 25 admin audit records returned by the API.
            </div>
          </div>
        </div>
        <DataTable
          rows={rows}
          emptyText="No admin audit records returned."
          columns={[
            {
              key: "time",
              header: "Time",
              render: (row) => (
                <span className="mono">
                  {getValue(row, ["created_at", "occurred_at", "timestamp"])}
                </span>
              ),
            },
            {
              key: "domain",
              header: "Domain",
              render: (row) => getValue(row, ["action_domain", "domain"]),
            },
            {
              key: "type",
              header: "Action",
              render: (row) => getValue(row, ["action_type", "action"]),
            },
            {
              key: "actor",
              header: "Actor",
              render: (row) =>
                getValue(row, ["actor_id", "actor", "api_key_label"]),
            },
            {
              key: "status",
              header: "Status",
              render: (row) => (
                <StatusBadge
                  label={getValue(row, ["status"], "recorded")}
                  tone="info"
                />
              ),
            },
          ]}
        />
      </section>
    </>
  );
}

function AuditActionMapRow({
  label,
  copy,
  targetId,
  value,
  tone,
}: {
  label: string;
  copy: string;
  targetId: string;
  value: string;
  tone: "success" | "warning" | "danger" | "info" | "neutral";
}) {
  return (
    <a className="admin-attention-row" href={`#${targetId}`}>
      <div>
        <div className="admin-attention-label">{label}</div>
        <div className="table-subtext">{copy}</div>
      </div>
      <StatusBadge label={value} tone={tone} />
    </a>
  );
}

function uniqueCount(rows: Record<string, unknown>[], keys: string[]): number {
  const values = new Set<string>();
  rows.forEach((row) => {
    const value = getValue(row, keys, "");
    if (value) {
      values.add(value);
    }
  });
  return values.size;
}
