import { AlertTriangle, ArrowRight, Plus, Search, ShieldCheck, X } from "lucide-react";
import { Link, useOutletContext, useSearchParams } from "react-router-dom";

import type { ReferralSaasCustomerPortfolioResponse } from "../../api/endpoints/referralSaasAccounts";
import {
  useReferralSaasCustomerPortfolio,
  type ReferralSaasCustomerPortfolioFilters,
} from "../../api/referralSaasAccountQueries";
import { EmptyState } from "../../components/EmptyState";
import { LoadingState } from "../../components/LoadingState";
import { StatusBadge } from "../../components/StatusBadge";
import { ReferralSaasAccountSetupPage } from "./ReferralSaasAccountSetupPage";

type Customer = ReferralSaasCustomerPortfolioResponse["portfolio"]["customers"][number];

export function ReferralSaasCustomerAccountsPage() {
  const outletContext = useOutletContext<{ refreshKey?: number } | undefined>();
  const [params, setParams] = useSearchParams();
  const mode = params.get("mode") === "create" ? "create" : "find";
  const filters: ReferralSaasCustomerPortfolioFilters = {
    search: value(params, "search"),
    jurisdiction: value(params, "jurisdiction"),
    accountStatus: value(params, "accountStatus"),
    sort: "NAME_ASC",
    limit: 50,
  };
  const query = useReferralSaasCustomerPortfolio(filters, outletContext?.refreshKey ?? 0);
  const customers = query.data?.portfolio.customers;
  const hasFilters = Boolean(filters.search || filters.jurisdiction || filters.accountStatus);

  function setFilter(name: string, selected: string) {
    const next = new URLSearchParams(params);
    if (selected) {
      next.set(name, selected);
    } else {
      next.delete(name);
    }
    setParams(next);
  }

  return <div className="operations-workspace customer-accounts-page">
    <section className="page-header operations-hero">
      <div>
        <div className="page-kicker">Amplifi Internal · Customer Account Control</div>
        <h1 className="page-title">Customer accounts</h1>
        <p className="page-copy">Find an existing customer before creating a new governed customer account.</p>
      </div>
      {mode === "find" ? <Link className="button primary" to="?mode=create"><Plus size={16} /> Create customer</Link> : null}
    </section>

    <nav className="customer-accounts-tabs" aria-label="Customer account actions">
      {mode === "find" ? <span aria-current="page"><Search size={16} /> Find customer</span> : <Link to="?mode=find"><Search size={16} /> Find customer</Link>}
      {mode === "create" ? <span aria-current="page"><Plus size={16} /> Create customer</span> : <Link to="?mode=create"><Plus size={16} /> Create customer</Link>}
    </nav>

    {mode === "create" ? <CustomerCreateWorkspace /> : <div className="customer-accounts-layout">
      <section className="customer-accounts-main">
        <div className="customer-accounts-heading">
          <div className="page-kicker">Find an existing customer</div>
          <h2>Search customer accounts</h2>
          <p>Use the customer name, customer number, or visible reference, then narrow the permitted results by jurisdiction.</p>
        </div>

        <section className="panel customer-account-search" aria-label="Search customer accounts">
          <label className="customer-account-search-input">
            <span className="sr-only">Customer name or number</span>
            <Search size={19} />
            <input aria-label="Customer name or number" onChange={(event) => setFilter("search", event.target.value)} placeholder="Customer name or number, e.g. Northstar or ACC-NSF-008" value={filters.search || ""} />
          </label>
          {hasFilters ? <button className="button secondary" onClick={() => setParams({})} type="button"><X size={15} /> Clear</button> : null}
        </section>

        <div className="customer-account-filters">
          <FilterSelect label="Jurisdiction" name="jurisdiction" value={filters.jurisdiction} onChange={setFilter} options={(query.data?.operatorScope.jurisdictions || []).map((item) => [item, item])} />
          <FilterSelect label="Account status" name="accountStatus" value={filters.accountStatus} onChange={setFilter} options={[["ACTIVE", "Active"], ["PENDING_ONBOARDING", "Pending onboarding"], ["SUSPENDED", "Suspended"]]} />
          <span>{customers?.length ?? 0} customer {customers?.length === 1 ? "profile" : "profiles"}</span>
        </div>

        {query.isLoading ? <LoadingState label="Loading customer accounts" /> : null}
        {query.error ? <DirectoryError error={query.error} /> : null}
        {customers ? <section className="panel customer-account-results" aria-label="Customer account results">
          {customers.length ? <div className="customer-account-table" role="table">
            <div className="customer-account-table-head" role="row"><span>Customer</span><span>Customer number</span><span>Jurisdiction</span><span>Status</span><span className="sr-only">Action</span></div>
            {customers.map((customer) => <CustomerAccountRow customer={customer} key={customer.accountRef} />)}
          </div> : <EmptyState label={hasFilters ? "No customer accounts match your search. Change or clear the filters before creating a new customer." : "No customer accounts are available in your permitted scope."} />}
        </section> : null}
      </section>

      <aside className="customer-account-boundary" aria-label="Search and access boundary">
        <ShieldCheck size={28} />
        <div className="page-kicker">Search &amp; access boundary</div>
        <h2>Results are permission-scoped</h2>
        <p>Name, customer-number, and reference matching only happens within the jurisdictions your role permits.</p>
        <dl>
          <div><dt>Permitted jurisdictions</dt><dd>{query.data?.operatorScope.jurisdictions.join(" · ") || "Loading"}</dd></div>
          <div><dt>Your capability</dt><dd>Customer Operations</dd></div>
        </dl>
        <strong>Customer not found?</strong>
        <p>Create only after checking for an existing account.</p>
        <Link className="button secondary" to="?mode=create"><Plus size={15} /> Create new customer</Link>
      </aside>
    </div>}
  </div>;
}

function CustomerCreateWorkspace() {
  return <div className="customer-create-workspace">
    <section className="customer-create-intro">
      <div className="page-kicker">Create a governed customer</div>
      <h2>Start with the customer identity</h2>
      <p>Check the visible customer references first. If no workspace exists, continue through company evidence, setup review, and customer workspace creation.</p>
    </section>
    <ReferralSaasAccountSetupPage embedded />
  </div>;
}

function CustomerAccountRow({ customer }: { customer: Customer }) {
  const statusTone = customer.accountStatus === "ACTIVE" ? "success" : customer.accountStatus === "SUSPENDED" ? "danger" : "warning";
  return <article className="customer-account-row" role="row">
    <div className="customer-account-name" role="cell"><span className="operations-customer-monogram" aria-hidden="true">{customer.accountName.slice(0, 2).toUpperCase()}</span><strong>{customer.accountName}</strong></div>
    <span role="cell">{customer.accountCode}</span>
    <span role="cell">{customer.jurisdiction}</span>
    <span role="cell"><StatusBadge label={formatCode(customer.accountStatus)} tone={statusTone} /></span>
    <Link className="customer-account-open" to={customer.destination}>Open profile <ArrowRight size={14} /></Link>
  </article>;
}

function FilterSelect({ label, name, value: selected, onChange, options }: { label: string; name: string; value?: string; onChange: (name: string, value: string) => void; options: string[][] }) {
  return <label><span className="sr-only">{label}</span><select aria-label={label} onChange={(event) => onChange(name, event.target.value)} value={selected || ""}><option value="">All</option>{options.map(([option, text]) => <option key={option} value={option}>{text}</option>)}</select></label>;
}

function DirectoryError({ error }: { error: unknown }) {
  const message = error instanceof Error ? error.message : "The customer account directory could not be loaded.";
  return <section className="operations-error" role="alert"><AlertTriangle size={19} /><div><strong>Customer accounts unavailable</strong><p>{message}</p></div></section>;
}

function value(params: URLSearchParams, key: string) { return params.get(key)?.trim() || undefined; }
function formatCode(raw: string) { return raw.replace(/_/g, " ").toLowerCase(); }
