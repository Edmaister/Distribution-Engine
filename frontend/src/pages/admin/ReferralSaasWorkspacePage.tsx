import { AlertTriangle, ArrowRight, Building2, CheckCircle2, Clock3, Search, ShieldAlert } from "lucide-react";
import { Link, useOutletContext } from "react-router-dom";

import type { ReferralSaasOperationsOverviewResponse } from "../../api/endpoints/referralSaasAccounts";
import { useReferralSaasOperationsOverview } from "../../api/referralSaasAccountQueries";
import { EmptyState } from "../../components/EmptyState";
import { LoadingState } from "../../components/LoadingState";
import { StatusBadge } from "../../components/StatusBadge";

type WorkItem = ReferralSaasOperationsOverviewResponse["operations"]["workItems"][number];

const priorityTone = {
  CRITICAL: "danger",
  HIGH: "danger",
  MEDIUM: "warning",
  LOW: "info",
} as const;

export function ReferralSaasWorkspacePage() {
  const outletContext = useOutletContext<{ refreshKey?: number } | undefined>();
  const refreshKey = outletContext?.refreshKey ?? 0;
  const overview = useReferralSaasOperationsOverview(8, refreshKey);
  const operations = overview.data?.operations;
  const visibleCustomers = uniqueVisibleCustomers(operations?.workItems || []);

  return (
    <div className="operations-workspace">
      <section className="page-header operations-hero">
        <div>
          <div className="page-kicker">Amplifi Internal · Customer Operations</div>
          <h1 className="page-title">Operations workspace</h1>
          <p className="page-copy">
            Prioritise governed work across the customers and jurisdictions you are permitted to support.
          </p>
        </div>
        <Link className="button primary operations-primary-action" to="/admin/referral-saas/account-maintenance">
          <Search size={16} /> Find or create customer
        </Link>
      </section>

      <Link className="operations-customer-search" to="/admin/referral-saas/account-maintenance">
        <Search aria-hidden="true" size={21} />
        <span><strong>Find a customer</strong><small>Search by customer name, reference, or account code.</small></span>
        <span className="operations-search-link">Open directory <ArrowRight size={15} /></span>
      </Link>

      {overview.isLoading ? <LoadingState label="Loading operations workspace" /> : null}
      {overview.error ? <OperationsError error={overview.error} /> : null}

      {operations ? (
        <>
          <section className="operations-kpi-strip" aria-label="Operations summary">
            <OperationsMetric label="Awaiting your action" value={operations.metrics.awaitingYourAction} note="Open operational cases" icon={Clock3} />
            <OperationsMetric label="Customers needing attention" value={operations.metrics.customersNeedingAttention} note="Across permitted jurisdictions" icon={Building2} />
            <OperationsMetric
              label="Within service target"
              value={operations.metrics.withinServiceTargetPercent === null ? "Not configured" : `${operations.metrics.withinServiceTargetPercent}%`}
              note={operations.metrics.serviceTargetStatus === "UNAVAILABLE" ? "No governed SLA source yet" : "Current measured performance"}
              icon={CheckCircle2}
            />
            <OperationsMetric
              label="Production incidents"
              value={operations.metrics.productionIncidents}
              note={operations.metrics.productionIncidents ? "Critical cases require attention" : "No critical cases in scope"}
              icon={ShieldAlert}
            />
          </section>

          <section className="operations-main-grid">
            <div className="panel operations-queue-panel">
              <div className="panel-header">
                <div>
                  <h2 className="panel-title">Your work queue</h2>
                  <div className="panel-subtitle">Ordered by operational priority using persisted support evidence.</div>
                </div>
                <StatusBadge label={`${operations.workItems.length} shown`} tone={operations.workItems.length ? "info" : "success"} />
              </div>
              <div className="operations-queue-list">
                {operations.workItems.length
                  ? operations.workItems.map((item) => <WorkQueueRow item={item} key={item.workItemRef} />)
                  : <EmptyState label="No operational work needs attention in your permitted scope." />}
              </div>
            </div>

            <aside className="panel operations-portfolio-panel">
              <div className="panel-header">
                <div>
                  <div className="page-kicker">Customer portfolio</div>
                  <h2 className="panel-title">Operational attention</h2>
                  <div className="panel-subtitle">Customers represented in this queue page.</div>
                </div>
              </div>
              <div className="operations-portfolio-list">
                {visibleCustomers.length ? visibleCustomers.map((customer) => (
                  <Link aria-label={`Open ${customer.label} ${customer.accountCode}`} key={customer.accountRef} to={`/admin/referral-saas/account-maintenance/${customer.accountRef}`}>
                    <span className="operations-customer-monogram">{customer.label.slice(0, 2).toUpperCase()}</span>
                    <span><strong>{customer.label}</strong><small>{customer.accountCode}</small></span>
                    <ArrowRight size={15} />
                  </Link>
                )) : <p className="operations-empty-copy">No customers currently need operational attention.</p>}
              </div>
              <Link className="operations-inline-link" to="/admin/referral-saas/account-maintenance">
                Open customer directory <ArrowRight size={14} />
              </Link>
            </aside>
          </section>
        </>
      ) : null}
    </div>
  );
}

function OperationsMetric({ label, value, note, icon: Icon }: { label: string; value: string | number; note: string; icon: typeof Clock3 }) {
  return <div className="operations-metric"><div className="operations-metric-label"><Icon size={15} />{label}</div><strong className={typeof value === "string" ? "operations-metric-text" : undefined}>{value}</strong><span>{note}</span></div>;
}

function WorkQueueRow({ item }: { item: WorkItem }) {
  return (
    <Link className="operations-work-row" to={item.destination}>
      <span className={`operations-priority-marker ${item.priority.toLowerCase()}`} aria-hidden="true" />
      <span className="operations-work-copy"><strong>{item.title}</strong><small>{formatCode(item.category)} · {formatCode(item.status)}</small></span>
      <span className="operations-work-customer"><strong>{item.customer.label}</strong><small>{item.jurisdiction}</small></span>
      <StatusBadge label={item.priority} tone={priorityTone[item.priority]} />
      <span className="operations-open-action">Open <ArrowRight size={14} /></span>
    </Link>
  );
}

function OperationsError({ error }: { error: unknown }) {
  const message = error instanceof Error ? error.message : "The workspace could not be loaded.";
  return <section className="operations-error" role="alert"><AlertTriangle size={19} /><div><strong>Operations evidence is unavailable</strong><p>{message}</p></div></section>;
}

function formatCode(value: string) {
  return value.replace(/_/g, " ");
}

function uniqueVisibleCustomers(items: WorkItem[]) {
  const customers = new Map<string, WorkItem["customer"]>();
  for (const item of items) customers.set(item.customer.accountRef, item.customer);
  return [...customers.values()].slice(0, 4);
}
