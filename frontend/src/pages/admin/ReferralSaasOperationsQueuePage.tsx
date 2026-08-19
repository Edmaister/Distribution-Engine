import { AlertTriangle, ArrowLeft, ArrowRight, Filter, ListChecks, Search, X } from "lucide-react";
import { Link, useOutletContext, useSearchParams } from "react-router-dom";

import type { ReferralSaasOperationsOverviewResponse } from "../../api/endpoints/referralSaasAccounts";
import {
  useReferralSaasOperationsQueue,
  type ReferralSaasOperationsQueueFilters,
} from "../../api/referralSaasAccountQueries";
import { EmptyState } from "../../components/EmptyState";
import { LoadingState } from "../../components/LoadingState";
import { StatusBadge } from "../../components/StatusBadge";

type WorkItem = ReferralSaasOperationsOverviewResponse["operations"]["workItems"][number];

const priorityTone = { CRITICAL: "danger", HIGH: "danger", MEDIUM: "warning", LOW: "info" } as const;

export function ReferralSaasOperationsQueuePage() {
  const outletContext = useOutletContext<{ refreshKey?: number } | undefined>();
  const [params, setParams] = useSearchParams();
  const limit = safeNumber(params.get("limit"), 25);
  const cursor = params.get("cursor") || undefined;
  const filters: ReferralSaasOperationsQueueFilters = {
    priority: value(params, "priority"),
    jurisdiction: value(params, "jurisdiction"),
    customer: value(params, "customer"),
    category: value(params, "category"),
    status: value(params, "status"),
    owner: value(params, "owner"),
    workType: value(params, "workType"),
    serviceTarget: value(params, "serviceTarget"),
    sort: value(params, "sort") || "PRIORITY",
    limit,
    cursor,
  };
  const queue = useReferralSaasOperationsQueue(filters, outletContext?.refreshKey ?? 0);
  const operations = queue.data?.operations;

  function setFilter(name: string, selected: string) {
    const next = new URLSearchParams(params);
    if (selected) {
      next.set(name, selected);
    } else {
      next.delete(name);
    }
    next.delete("cursor");
    setParams(next);
  }

  function setCursor(nextCursor?: string) {
    const next = new URLSearchParams(params);
    if (nextCursor) {
      next.set("cursor", nextCursor);
    } else {
      next.delete("cursor");
    }
    setParams(next);
  }

  const offset = safeNumber(cursor, 0);
  const hasFilters = [...params.keys()].some((key) => key !== "limit" && key !== "sort");

  return (
    <div className="operations-workspace operations-queue-page">
      <section className="page-header operations-hero">
        <div>
          <div className="page-kicker">Amplifi Internal · Operations</div>
          <h1 className="page-title">Work queue</h1>
          <p className="page-copy">Find and prioritise persisted operational work across the customers and jurisdictions you may support.</p>
        </div>
        <Link className="button secondary" to="/admin/referral-saas"><ArrowLeft size={16} /> Operations home</Link>
      </section>

      <section className="panel operations-filter-panel" aria-label="Work queue filters">
        <div className="panel-header">
          <div><h2 className="panel-title"><Filter size={16} /> Filter work</h2><div className="panel-subtitle">The URL keeps this view shareable and restores it when you return.</div></div>
          {hasFilters ? <button className="button secondary" type="button" onClick={() => setParams({ sort: filters.sort || "PRIORITY", limit: String(limit) })}><X size={15} /> Clear filters</button> : null}
        </div>
        <div className="operations-filter-grid">
          <label className="operations-filter-search"><span>Customer</span><span className="input-with-icon"><Search size={15} /><input aria-label="Customer" onChange={(event) => setFilter("customer", event.target.value)} placeholder="Name, account code, or ID" value={filters.customer || ""} /></span></label>
          <FilterSelect label="Jurisdiction" name="jurisdiction" value={filters.jurisdiction} onChange={setFilter} options={(queue.data?.operatorScope.jurisdictions || []).map((item) => [item, item])} />
          <FilterSelect label="Priority" name="priority" value={filters.priority} onChange={setFilter} options={[["CRITICAL", "Critical"], ["HIGH", "High"], ["MEDIUM", "Medium"], ["LOW", "Low"]]} />
          <FilterSelect label="Status" name="status" value={filters.status} onChange={setFilter} options={[["OPEN", "Open"], ["INVESTIGATING", "Investigating"], ["WAITING", "Waiting"]]} />
          <label><span>Category</span><input aria-label="Category" onChange={(event) => setFilter("category", event.target.value)} placeholder="For example: attribution review" value={filters.category || ""} /></label>
          <label><span>Owner</span><input aria-label="Owner" onChange={(event) => setFilter("owner", event.target.value)} placeholder="Owner reference or UNASSIGNED" value={filters.owner || ""} /></label>
          <FilterSelect label="Work type" name="workType" value={filters.workType} onChange={setFilter} options={[["SUPPORT_CASE", "Support case"]]} />
          <FilterSelect label="Service target" name="serviceTarget" value={filters.serviceTarget} onChange={setFilter} options={[["UNAVAILABLE", "Not configured"], ["AVAILABLE", "Configured"]]} />
          <FilterSelect label="Order" name="sort" value={filters.sort} onChange={setFilter} includeAll={false} options={[["PRIORITY", "Priority"], ["UPDATED_DESC", "Newest updated"], ["UPDATED_ASC", "Oldest updated"]]} />
          <FilterSelect label="Rows" name="limit" value={String(limit)} onChange={setFilter} includeAll={false} options={[["10", "10"], ["25", "25"], ["50", "50"]]} />
        </div>
      </section>

      {queue.isLoading ? <LoadingState label="Loading work queue" /> : null}
      {queue.error ? <OperationsError error={queue.error} /> : null}
      {operations ? (
        <section className="panel operations-queue-panel">
          <div className="panel-header"><div><h2 className="panel-title"><ListChecks size={16} /> Operational work</h2><div className="panel-subtitle">Showing {operations.workItems.length} persisted items from position {offset + 1}.</div></div><StatusBadge label={`${operations.metrics.awaitingYourAction} in scope`} tone={operations.metrics.awaitingYourAction ? "info" : "success"} /></div>
          {operations.workItems.length ? <div className="operations-queue-table" role="list">{operations.workItems.map((item) => <QueueItem item={item} key={item.workItemRef} />)}</div> : <EmptyState label={hasFilters ? "No work matches these filters. Clear or change a filter to widen the queue." : "No operational work needs attention in your permitted scope."} />}
          <div className="operations-pagination" aria-label="Queue pagination">
            <button className="button secondary" disabled={offset === 0} onClick={() => setCursor(String(Math.max(0, offset - limit)))} type="button"><ArrowLeft size={15} /> Previous</button>
            <span>Items {operations.workItems.length ? `${offset + 1}-${offset + operations.workItems.length}` : "0"}</span>
            <button className="button secondary" disabled={!operations.nextCursor} onClick={() => setCursor(operations.nextCursor || undefined)} type="button">Next <ArrowRight size={15} /></button>
          </div>
        </section>
      ) : null}
    </div>
  );
}

function FilterSelect({ label, name, value: selected, onChange, options, includeAll = true }: { label: string; name: string; value?: string; onChange: (name: string, value: string) => void; options: string[][]; includeAll?: boolean }) {
  return <label><span>{label}</span><select aria-label={label} onChange={(event) => onChange(name, event.target.value)} value={selected || ""}>{includeAll ? <option value="">All</option> : null}{options.map(([value, text]) => <option key={value} value={value}>{text}</option>)}</select></label>;
}

function QueueItem({ item }: { item: WorkItem }) {
  return <Link className="operations-queue-item" to={item.destination}>
    <span className={`operations-priority-marker ${item.priority.toLowerCase()}`} aria-hidden="true" />
    <span className="operations-work-copy"><strong>{item.title}</strong><small>{formatCode(item.category)} · {formatCode(item.status)}</small></span>
    <span className="operations-work-customer"><strong>{item.customer.label}</strong><small>{item.customer.accountCode} · {item.jurisdiction}</small></span>
    <span className="operations-owner"><small>Owner</small><strong>{item.ownerRef || "Unassigned"}</strong></span>
    <StatusBadge label={item.priority} tone={priorityTone[item.priority]} />
    <span className="operations-open-action">Open <ArrowRight size={14} /></span>
  </Link>;
}

function OperationsError({ error }: { error: unknown }) {
  const message = error instanceof Error ? error.message : "The work queue could not be loaded.";
  return <section className="operations-error" role="alert"><AlertTriangle size={19} /><div><strong>Work queue unavailable</strong><p>{message}</p></div></section>;
}

function value(params: URLSearchParams, key: string) { return params.get(key)?.trim() || undefined; }
function safeNumber(value: string | null | undefined, fallback: number) { const parsed = Number(value); return Number.isInteger(parsed) && parsed >= 0 ? parsed : fallback; }
function formatCode(value: string) { return value.replace(/_/g, " ").toLowerCase(); }
