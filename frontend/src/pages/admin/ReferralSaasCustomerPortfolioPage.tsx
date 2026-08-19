import { AlertTriangle, ArrowLeft, ArrowRight, BriefcaseBusiness, Filter, Search, X } from "lucide-react";
import { Link, useOutletContext, useSearchParams } from "react-router-dom";

import type { ReferralSaasCustomerPortfolioResponse } from "../../api/endpoints/referralSaasAccounts";
import {
  useReferralSaasCustomerPortfolio,
  type ReferralSaasCustomerPortfolioFilters,
} from "../../api/referralSaasAccountQueries";
import { EmptyState } from "../../components/EmptyState";
import { LoadingState } from "../../components/LoadingState";
import { StatusBadge } from "../../components/StatusBadge";

type Customer = ReferralSaasCustomerPortfolioResponse["portfolio"]["customers"][number];

export function ReferralSaasCustomerPortfolioPage() {
  const outletContext = useOutletContext<{ refreshKey?: number } | undefined>();
  const [params, setParams] = useSearchParams();
  const limit = safeNumber(params.get("limit"), 25);
  const cursor = value(params, "cursor");
  const filters: ReferralSaasCustomerPortfolioFilters = {
    search: value(params, "search"),
    jurisdiction: value(params, "jurisdiction"),
    accountStatus: value(params, "accountStatus"),
    attention: value(params, "attention"),
    sort: value(params, "sort") || "ATTENTION",
    limit,
    cursor,
  };
  const query = useReferralSaasCustomerPortfolio(filters, outletContext?.refreshKey ?? 0);
  const portfolio = query.data?.portfolio;
  const offset = safeNumber(cursor, 0);
  const hasFilters = [...params.keys()].some((key) => !["limit", "sort"].includes(key));

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

  return <div className="operations-workspace customer-portfolio-page">
    <section className="page-header operations-hero">
      <div>
        <div className="page-kicker">Amplifi Internal · Customer Operations</div>
        <h1 className="page-title">Customer portfolio</h1>
        <p className="page-copy">Find a customer within your permitted jurisdictions, understand what needs attention, and open the correct customer workspace.</p>
      </div>
      <Link className="button secondary" to="/admin/referral-saas"><ArrowLeft size={16} /> Operations home</Link>
    </section>

    <section className="panel operations-filter-panel" aria-label="Customer portfolio filters">
      <div className="panel-header">
        <div><h2 className="panel-title"><Filter size={16} /> Find customers</h2><div className="panel-subtitle">Search and filters remain in the URL so this view can be shared and restored.</div></div>
        {hasFilters ? <button className="button secondary" onClick={() => setParams({ sort: filters.sort || "ATTENTION", limit: String(limit) })} type="button"><X size={15} /> Clear filters</button> : null}
      </div>
      <div className="operations-filter-grid customer-portfolio-filters">
        <label className="operations-filter-search"><span>Customer</span><span className="input-with-icon"><Search size={15} /><input aria-label="Customer" onChange={(event) => setFilter("search", event.target.value)} placeholder="Name, reference, account code, or ID" value={filters.search || ""} /></span></label>
        <FilterSelect label="Jurisdiction" name="jurisdiction" value={filters.jurisdiction} onChange={setFilter} options={(query.data?.operatorScope.jurisdictions || []).map((item) => [item, item])} />
        <FilterSelect label="Account status" name="accountStatus" value={filters.accountStatus} onChange={setFilter} options={[["ACTIVE", "Active"], ["PENDING_ONBOARDING", "Pending onboarding"], ["SUSPENDED", "Suspended"]]} />
        <FilterSelect label="Operational attention" name="attention" value={filters.attention} onChange={setFilter} options={[["NEEDS_ATTENTION", "Needs attention"], ["NO_OPEN_WORK", "No open work"]]} />
        <FilterSelect label="Order" name="sort" value={filters.sort} onChange={setFilter} includeAll={false} options={[["ATTENTION", "Attention first"], ["NAME_ASC", "Customer name"], ["UPDATED_DESC", "Recently updated"]]} />
      </div>
    </section>

    {query.isLoading ? <LoadingState label="Loading customer portfolio" /> : null}
    {query.error ? <PortfolioError error={query.error} /> : null}
    {portfolio ? <section className="panel customer-portfolio-results">
      <div className="panel-header"><div><h2 className="panel-title"><BriefcaseBusiness size={16} /> Customers</h2><div className="panel-subtitle">Showing {portfolio.customers.length} customers from position {offset + 1}.</div></div><StatusBadge label={`${portfolio.summary.needingAttention} need attention`} tone={portfolio.summary.needingAttention ? "warning" : "success"} /></div>
      {portfolio.customers.length ? <div className="customer-portfolio-list" role="list">{portfolio.customers.map((customer) => <CustomerRow customer={customer} key={customer.accountRef} />)}</div> : <EmptyState label={hasFilters ? "No customers match these filters. Clear or change a filter to widen the portfolio." : "No customers are available in your permitted scope."} />}
      <div className="operations-pagination" aria-label="Portfolio pagination">
        <button className="button secondary" disabled={offset === 0} onClick={() => setCursor(String(Math.max(0, offset - limit)))} type="button"><ArrowLeft size={15} /> Previous</button>
        <span>Customers {portfolio.customers.length ? `${offset + 1}-${offset + portfolio.customers.length}` : "0"}</span>
        <button className="button secondary" disabled={!portfolio.nextCursor} onClick={() => setCursor(portfolio.nextCursor || undefined)} type="button">Next <ArrowRight size={15} /></button>
      </div>
    </section> : null}
  </div>;
}

function CustomerRow({ customer }: { customer: Customer }) {
  const statusTone = customer.accountStatus === "ACTIVE" ? "success" : customer.accountStatus === "SUSPENDED" ? "danger" : "warning";
  return <article className="customer-portfolio-row" role="listitem">
    <span className="operations-customer-monogram" aria-hidden="true">{customer.accountName.slice(0, 2).toUpperCase()}</span>
    <div className="customer-portfolio-identity"><strong>{customer.accountName}</strong><span>{customer.accountCode}</span><small>{customer.customerReference || "No customer reference"}{customer.organisationReference ? ` · ${customer.organisationReference}` : ""}</small></div>
    <div className="customer-portfolio-context"><span><small>Jurisdiction</small><strong>{customer.jurisdiction}</strong></span><span><small>Account status</small><StatusBadge label={formatCode(customer.accountStatus)} tone={statusTone} /></span></div>
    <div className="customer-portfolio-attention"><small>Operational attention</small>{customer.attention.needsAttention ? <><StatusBadge label={`${customer.attention.openCaseCount} open`} tone={customer.attention.criticalCaseCount ? "danger" : "warning"} /><span>{customer.attention.reasons[0]}</span></> : <><StatusBadge label="No open work" tone="success" /><span>No operational action is currently recorded.</span></>}</div>
    <Link className="button secondary customer-portfolio-open" to={customer.destination}>Open customer <ArrowRight size={15} /></Link>
  </article>;
}

function FilterSelect({ label, name, value: selected, onChange, options, includeAll = true }: { label: string; name: string; value?: string; onChange: (name: string, value: string) => void; options: string[][]; includeAll?: boolean }) {
  return <label><span>{label}</span><select aria-label={label} onChange={(event) => onChange(name, event.target.value)} value={selected || ""}>{includeAll ? <option value="">All</option> : null}{options.map(([option, text]) => <option key={option} value={option}>{text}</option>)}</select></label>;
}

function PortfolioError({ error }: { error: unknown }) {
  const message = error instanceof Error ? error.message : "The customer portfolio could not be loaded.";
  return <section className="operations-error" role="alert"><AlertTriangle size={19} /><div><strong>Customer portfolio unavailable</strong><p>{message}</p></div></section>;
}

function value(params: URLSearchParams, key: string) { return params.get(key)?.trim() || undefined; }
function safeNumber(raw: string | null | undefined, fallback: number) { const parsed = Number(raw); return Number.isInteger(parsed) && parsed >= 0 ? parsed : fallback; }
function formatCode(raw: string) { return raw.replace(/_/g, " ").toLowerCase(); }
