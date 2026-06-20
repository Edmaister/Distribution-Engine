import { AlertTriangle, BadgeDollarSign, CalendarClock, CheckCircle2, Landmark, ReceiptText, Send, WalletCards } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import {
  getAdminSponsorBillingDashboard,
  getAdminNetworkWalletOverview,
  getAdminSponsorInvoices,
  getAdminSponsorStatement,
  getAdminSponsorVatReport,
  getAdminSponsorWallets,
  issueSponsorInvoice,
  recordSponsorInvoicePayment,
  runScheduledSponsorBillingGeneration,
} from "../../api/endpoints/sponsorBilling";
import { getAdminDistributorWallets } from "../../api/endpoints/distribution";
import { ActionGuardrail, GuardrailItem, GuardrailTone } from "../../components/ActionGuardrail";
import { DataTable } from "../../components/DataTable";
import { ErrorPanel } from "../../components/ErrorPanel";
import { FieldLabel } from "../../components/FieldLabel";
import { InfoTooltip } from "../../components/InfoTooltip";
import { JourneyStep, JourneyTracker } from "../../components/JourneyTracker";
import { KpiCard } from "../../components/KpiCard";
import { LoadingState } from "../../components/LoadingState";
import { PanelTitle } from "../../components/PanelTitle";
import { StatusBadge } from "../../components/StatusBadge";
import { SummaryGrid } from "../../components/SummaryGrid";
import { SummaryItem } from "../../components/SummaryItem";
import {
  asArray,
  formatDisplay,
  getNestedValue,
  getValue,
  statusTone,
  useRefreshContext,
} from "../pageUtils";

const ADMIN_BILLING_TENANT_KEY = "amplifi.adminBilling.tenant";

export function BillingSpinePage() {
  const { refreshKey } = useRefreshContext();
  const [tenantCode, setTenantCode] = useState(localStorage.getItem(ADMIN_BILLING_TENANT_KEY) || "FNB");
  const [submittedTenant, setSubmittedTenant] = useState(localStorage.getItem(ADMIN_BILLING_TENANT_KEY) || "FNB");
  const [dashboard, setDashboard] = useState<unknown>(null);
  const [invoices, setInvoices] = useState<Record<string, unknown>[]>([]);
  const [wallets, setWallets] = useState<Record<string, unknown>[]>([]);
  const [distributorWallets, setDistributorWallets] = useState<Record<string, unknown>[]>([]);
  const [walletOverview, setWalletOverview] = useState<unknown>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const [generationPeriodStart, setGenerationPeriodStart] = useState(defaultPeriodStart());
  const [generationPeriodEnd, setGenerationPeriodEnd] = useState(defaultPeriodEnd());
  const [generationDueDate, setGenerationDueDate] = useState(defaultDueDate());
  const [generationSponsor, setGenerationSponsor] = useState("");
  const [generationCurrency, setGenerationCurrency] = useState("ZAR");
  const [generationVatRate, setGenerationVatRate] = useState("0");
  const [generationDryRun, setGenerationDryRun] = useState(true);
  const [generationIssue, setGenerationIssue] = useState(false);
  const [generationLoading, setGenerationLoading] = useState(false);
  const [generationError, setGenerationError] = useState<unknown>(null);
  const [generationResult, setGenerationResult] = useState<Record<string, unknown> | null>(null);
  const [selectedInvoiceId, setSelectedInvoiceId] = useState("");
  const [paymentAmount, setPaymentAmount] = useState("");
  const [paymentReference, setPaymentReference] = useState("");
  const [invoiceActionLoading, setInvoiceActionLoading] = useState<"issue" | "payment" | null>(null);
  const [invoiceActionError, setInvoiceActionError] = useState<unknown>(null);
  const [invoiceActionResult, setInvoiceActionResult] = useState<Record<string, unknown> | null>(null);
  const [statementSponsor, setStatementSponsor] = useState("");
  const [statementPeriodStart, setStatementPeriodStart] = useState(defaultPeriodStart());
  const [statementPeriodEnd, setStatementPeriodEnd] = useState(defaultPeriodEnd());
  const [reportCurrency, setReportCurrency] = useState("ZAR");
  const [statementResult, setStatementResult] = useState<Record<string, unknown> | null>(null);
  const [statementError, setStatementError] = useState<unknown>(null);
  const [statementLoading, setStatementLoading] = useState(false);
  const [vatResult, setVatResult] = useState<Record<string, unknown> | null>(null);
  const [vatError, setVatError] = useState<unknown>(null);
  const [vatLoading, setVatLoading] = useState(false);
  const [localRefreshKey, setLocalRefreshKey] = useState(0);

  useEffect(() => {
    if (!submittedTenant) {
      return;
    }

    let alive = true;
    setLoading(true);
    setError(null);
    Promise.all([
      getAdminSponsorBillingDashboard(submittedTenant),
      getAdminSponsorInvoices(submittedTenant),
      getAdminSponsorWallets(submittedTenant),
      getAdminDistributorWallets(submittedTenant),
      getAdminNetworkWalletOverview(submittedTenant).catch(() => null),
    ])
      .then(([dashboardPayload, invoicePayload, walletPayload, distributorWalletPayload, walletOverviewPayload]) => {
        if (alive) {
          setDashboard(dashboardPayload);
          setInvoices(asArray(invoicePayload));
          setWallets(asArray(walletPayload));
          setDistributorWallets(asArray(distributorWalletPayload));
          setWalletOverview(walletOverviewPayload);
        }
      })
      .catch((requestError) => alive && setError(requestError))
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [submittedTenant, refreshKey, localRefreshKey]);

  const selectedInvoice = invoices.find((invoice) => getValue(invoice, ["invoice_id", "id"]) === selectedInvoiceId);
  const selectedInvoiceStatus = selectedInvoice ? getValue(selectedInvoice, ["status", "invoice_status"]) : "-";
  const selectedInvoiceOutstanding = selectedInvoice
    ? getValue(selectedInvoice, ["outstanding_amount", "total_amount", "amount"], "")
    : "";
  const selectedInvoiceOutstandingNumber = moneyNumber(selectedInvoiceOutstanding);
  const canIssueSelectedInvoice = selectedInvoiceStatus === "DRAFT";
  const canRecordPayment = ["ISSUED", "PARTIALLY_PAID"].includes(selectedInvoiceStatus) && selectedInvoiceOutstandingNumber > 0;
  const generationGuard = getBillingGenerationGuardrail({ generationDryRun, generationIssue, generationLoading });
  const invoiceGuard = getInvoiceActionGuardrail({
    selectedInvoice,
    selectedInvoiceStatus,
    selectedInvoiceOutstandingNumber,
    canIssueSelectedInvoice,
    canRecordPayment,
    invoiceActionLoading,
  });
  const reportGuard = getBillingReportGuardrail({ statementSponsor, statementLoading, vatLoading });
  const billingGuidance = getBillingGuidance({
    invoice: selectedInvoice,
    invoiceCount: invoices.length,
    outstandingAmount: selectedInvoiceOutstandingNumber,
  });
  const invoiceCount = Number(getNestedValue(dashboard, ["dashboard", "invoice_count"], invoices.length)) || invoices.length;
  const outstandingTotal = moneyNumber(getNestedValue(dashboard, ["dashboard", "totals", "outstanding_amount"], "0"));
  const paidTotal = moneyNumber(getNestedValue(dashboard, ["dashboard", "totals", "paid_amount"], "0"));
  const overdueInvoices = asArrayFromDashboard(dashboard, "overdue_invoices").length;
  const draftInvoices = invoices.filter((invoice) => getValue(invoice, ["status", "invoice_status"]) === "DRAFT").length;
  const payableInvoices = invoices.filter((invoice) => ["ISSUED", "PARTIALLY_PAID"].includes(getValue(invoice, ["status", "invoice_status"]))).length;
  const fundingNeedsAction = draftInvoices > 0 || payableInvoices > 0 || outstandingTotal > 0 || overdueInvoices > 0;
  const producerWalletTotal = overviewNumber(walletOverview, ["overview", "producer_wallets", "available_balance"], sumMoney(wallets, ["available_balance", "current_balance", "balance"]));
  const producerReservedTotal = overviewNumber(walletOverview, ["overview", "producer_wallets", "reserved_balance"], sumMoney(wallets, ["reserved_balance", "held_balance"]));
  const distributorAvailableTotal = overviewNumber(walletOverview, ["overview", "distributor_wallets", "available_balance"], sumMoney(distributorWallets, ["available_balance", "balance"]));
  const distributorHeldTotal = overviewNumber(walletOverview, ["overview", "distributor_wallets", "held_balance"], sumMoney(distributorWallets, ["held_balance", "reserved_balance"]));
  const distributorPaidOutTotal = overviewNumber(walletOverview, ["overview", "distributor_wallets", "paid_out_balance"], sumMoney(distributorWallets, ["paid_out_balance"]));
  const networkWalletCount = overviewNumber(walletOverview, ["overview", "network", "wallet_count"], wallets.length + distributorWallets.length);
  const networkDemandLiability = overviewNumber(walletOverview, ["overview", "network", "demand_liability"], distributorAvailableTotal + distributorHeldTotal);
  const networkNetAvailable = overviewNumber(walletOverview, ["overview", "network", "net_available_position"], producerWalletTotal - networkDemandLiability);
  const walletAttentionCount = overviewNumber(walletOverview, ["overview", "network", "attention_count"], 0);
  const walletPostureNeedsAction =
    walletAttentionCount > 0 ||
    wallets.some((wallet) => statusNeedsAttention(getValue(wallet, ["status", "wallet_status"]))) ||
    distributorWallets.some((wallet) => statusNeedsAttention(getValue(wallet, ["status", "wallet_status"])));

  useEffect(() => {
    if (!invoices.length) {
      setSelectedInvoiceId("");
      setPaymentAmount("");
      return;
    }

    const currentInvoice = invoices.find((invoice) => getValue(invoice, ["invoice_id", "id"]) === selectedInvoiceId);
    const nextInvoice = currentInvoice || invoices[0];
    const nextInvoiceId = getValue(nextInvoice, ["invoice_id", "id"], "");
    setSelectedInvoiceId(nextInvoiceId);
    setPaymentAmount(getValue(nextInvoice, ["outstanding_amount", "total_amount", "amount"], ""));
  }, [invoices, selectedInvoiceId]);

  function submitTenant(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cleanedTenant = tenantCode.trim().toUpperCase();
    localStorage.setItem(ADMIN_BILLING_TENANT_KEY, cleanedTenant);
    setTenantCode(cleanedTenant);
    setSubmittedTenant(cleanedTenant);
    setStatementResult(null);
    setVatResult(null);
    setStatementError(null);
    setVatError(null);
  }

  function submitGeneration(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!generationDryRun && !window.confirm("Generate sponsor invoices for this billing period?")) {
      return;
    }
    setGenerationLoading(true);
    setGenerationError(null);
    setGenerationResult(null);
    runScheduledSponsorBillingGeneration({
      tenant_code: submittedTenant,
      invoice_period_start: generationPeriodStart,
      invoice_period_end: generationPeriodEnd,
      due_date: generationDueDate || undefined,
      sponsor_code: generationSponsor.trim().toUpperCase() || undefined,
      currency: generationCurrency.trim().toUpperCase(),
      vat_rate: generationVatRate,
      dry_run: generationDryRun,
      issue: generationIssue,
      limit: 500,
      metadata: { source: "amplifi_control_centre" },
    })
      .then((payload) => setGenerationResult(payload))
      .catch((requestError) => setGenerationError(requestError))
      .finally(() => setGenerationLoading(false));
  }

  function submitIssueInvoice(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedInvoiceId) {
      return;
    }
    if (!window.confirm("Issue this draft invoice now?")) {
      return;
    }
    setInvoiceActionLoading("issue");
    setInvoiceActionError(null);
    setInvoiceActionResult(null);
    issueSponsorInvoice(selectedInvoiceId)
      .then((payload) => {
        setInvoiceActionResult(payload);
        setLocalRefreshKey((value) => value + 1);
      })
      .catch((requestError) => setInvoiceActionError(requestError))
      .finally(() => setInvoiceActionLoading(null));
  }

  function submitRecordPayment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedInvoiceId) {
      return;
    }
    if (!window.confirm("Record this sponsor payment against the selected invoice?")) {
      return;
    }
    setInvoiceActionLoading("payment");
    setInvoiceActionError(null);
    setInvoiceActionResult(null);
    recordSponsorInvoicePayment(selectedInvoiceId, {
      amount: paymentAmount,
      payment_reference: paymentReference.trim() || undefined,
      metadata: { source: "amplifi_control_centre" },
    })
      .then((payload) => {
        setInvoiceActionResult(payload);
        setPaymentReference("");
        setLocalRefreshKey((value) => value + 1);
      })
      .catch((requestError) => setInvoiceActionError(requestError))
      .finally(() => setInvoiceActionLoading(null));
  }

  function submitStatement(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!statementSponsor.trim()) {
      setStatementError({ message: "Sponsor code is required for a statement." });
      return;
    }
    setStatementLoading(true);
    setStatementError(null);
    setStatementResult(null);
    getAdminSponsorStatement(
      submittedTenant,
      statementSponsor.trim().toUpperCase(),
      statementPeriodStart,
      statementPeriodEnd,
      reportCurrency.trim().toUpperCase() || undefined,
    )
      .then((payload) => setStatementResult(payload))
      .catch((requestError) => setStatementError(requestError))
      .finally(() => setStatementLoading(false));
  }

  function submitVatReport(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setVatLoading(true);
    setVatError(null);
    setVatResult(null);
    getAdminSponsorVatReport(
      submittedTenant,
      statementPeriodStart,
      statementPeriodEnd,
      statementSponsor.trim().toUpperCase() || undefined,
      reportCurrency.trim().toUpperCase() || undefined,
    )
      .then((payload) => setVatResult(payload))
      .catch((requestError) => setVatError(requestError))
      .finally(() => setVatLoading(false));
  }

  if (loading) {
    return <LoadingState label="Loading sponsor finance" />;
  }

  if (error) {
    return <ErrorPanel error={error} />;
  }

  return (
    <>
      <section className="page-header">
        <div>
          <div className="page-kicker">Producer - Supply</div>
          <h1 className="page-title">Funding Spine</h1>
          <p className="page-copy">
            Control the producer-side finance rail for billing generation, sponsor invoices, funding wallets,
            payments, statements, and VAT reporting.
          </p>
        </div>
        <StatusBadge label={fundingNeedsAction ? "Finance action" : "Backend ready"} tone={fundingNeedsAction ? "warning" : "success"} />
      </section>

      <section className="funding-spine-grid">
        <div className="funding-spine-card primary">
          <div className="funding-spine-card-top">
            <div>
              <div className="funding-spine-kicker">Funding posture</div>
              <h2>{fundingNeedsAction ? "Producer finance needs action" : "Producer finance is observable"}</h2>
            </div>
            {fundingNeedsAction ? <AlertTriangle size={24} /> : <CheckCircle2 size={24} />}
          </div>
          <p>
            Funding Spine turns producer-funded demand into controlled billing and collection. Operators preview
            billing, generate invoices, issue payable invoices, record sponsor payments, and report balances.
          </p>
          <div className="funding-spine-metrics">
            <SummaryItem label="Invoices" value={invoiceCount} />
            <SummaryItem label="Outstanding" value={outstandingTotal} />
            <SummaryItem label="Paid" value={paidTotal} />
            <SummaryItem label="Wallets" value={networkWalletCount} />
          </div>
        </div>

        <div className="panel funding-action-map">
          <div className="panel-header">
            <div>
              <PanelTitle
                help="Shows where the finance operator should perform each funding and billing action."
                title="Operator action map"
              />
              <div className="panel-subtitle">Where to preview, generate, collect, and report.</div>
            </div>
          </div>
          <div className="panel-body admin-attention-list">
            <FundingActionMapRow
              label="Preview billing"
              copy="Run a dry-run billing generation before creating invoice records."
              targetId="billing-generation"
              value={generationDryRun ? "Dry run" : "Will generate"}
              tone={generationDryRun ? "info" : "warning"}
            />
            <FundingActionMapRow
              label="Generate invoices"
              copy="Create producer invoices once the preview is understood."
              targetId="billing-generation"
              value={draftInvoices ? `${draftInvoices} drafts` : "Generate"}
              tone={draftInvoices ? "warning" : "info"}
            />
            <FundingActionMapRow
              label="Issue and collect"
              copy="Issue draft invoices and record sponsor payments against payable invoices."
              targetId="billing-invoice-actions"
              value={payableInvoices ? `${payableInvoices} payable` : canIssueSelectedInvoice ? "Issue" : "Waiting"}
              tone={payableInvoices || canIssueSelectedInvoice ? "warning" : "neutral"}
            />
            <FundingActionMapRow
              label="Monitor exposure"
              copy="Review outstanding, overdue, wallet, and invoice status signals."
              targetId="billing-position"
              value={overdueInvoices ? `${overdueInvoices} overdue` : outstandingTotal > 0 ? "Watch" : "Clear"}
              tone={overdueInvoices || outstandingTotal > 0 ? "warning" : "success"}
            />
            <FundingActionMapRow
              label="Report finance"
              copy="Load sponsor statements and VAT reports without changing billing state."
              targetId="billing-reporting"
              value="Read only"
              tone="success"
            />
          </div>
        </div>
      </section>

      <section className="panel" id="billing-scope">
        <div className="panel-header">
          <div>
            <PanelTitle
              help="Sets the tenant context for all finance data and actions on this screen."
              title="Admin finance scope"
            />
            <div className="panel-subtitle">Required by the sponsor billing admin APIs.</div>
          </div>
        </div>
        <div className="panel-body">
          <form className="form-row" onSubmit={submitTenant}>
            <div className="field">
              <FieldLabel
                help="The tenant whose sponsor billing data should be loaded, for example FNB."
                htmlFor="billing-tenant"
                label="Tenant code"
              />
              <input
                className="input"
                id="billing-tenant"
                value={tenantCode}
                onChange={(event) => setTenantCode(event.target.value)}
              />
            </div>
            <button className="button" type="submit">
              Load finance
            </button>
          </form>
        </div>
      </section>

      <section className="grid-3">
        <KpiCard
          label="Invoices"
          value={formatDisplay(invoiceCount)}
          footnote="Billing dashboard count"
          icon={ReceiptText}
        />
        <KpiCard label="Network wallets" value={networkWalletCount} footnote="Producer and distributor wallet records" icon={Landmark} />
        <KpiCard
          label="Outstanding"
          value={formatDisplay(outstandingTotal)}
          footnote="Sponsor billing exposure"
          icon={BadgeDollarSign}
        />
      </section>

      <JourneyTracker
        title="Billing journey"
        subtitle="Step-by-step path from billing preview through collection and reporting."
        badge={billingGuidance.badge}
        tone={billingGuidance.tone}
        currentTitle={billingGuidance.title}
        currentCopy={billingGuidance.copy}
        steps={billingGuidance.steps}
      />

      <section className="panel" id="network-wallet-posture">
        <div className="panel-header">
          <div>
            <PanelTitle
              help="Combines producer funding wallets and distributor earning wallets so Amplifi can see funding capacity and earning liability in one place."
              title="Network wallet posture"
            />
            <div className="panel-subtitle">Producer funding, distributor earnings, held balances, and payout movement.</div>
          </div>
          <StatusBadge
            label={walletPostureNeedsAction ? "Review wallets" : "Observable"}
            tone={walletPostureNeedsAction ? "warning" : "success"}
          />
        </div>
        <div className="panel-body">
          <div className="summary-grid">
            <SummaryItem label="Producer wallets" value={wallets.length} />
            <SummaryItem label="Producer available" value={producerWalletTotal.toFixed(2)} />
            <SummaryItem label="Producer reserved" value={producerReservedTotal.toFixed(2)} />
            <SummaryItem label="Distributor wallets" value={distributorWallets.length} />
            <SummaryItem label="Distributor available" value={distributorAvailableTotal.toFixed(2)} />
            <SummaryItem label="Distributor held" value={distributorHeldTotal.toFixed(2)} />
            <SummaryItem label="Distributor paid out" value={distributorPaidOutTotal.toFixed(2)} />
            <SummaryItem label="Demand liability" value={networkDemandLiability.toFixed(2)} />
            <SummaryItem label="Net available" value={networkNetAvailable.toFixed(2)} />
          </div>
        </div>
      </section>

      <section className="panel" id="billing-generation">
        <div className="panel-header">
          <div>
            <PanelTitle
              help="Checks or creates sponsor invoices for a billing period based on eligible utilisation."
              title="Billing generation"
            />
            <div className="panel-subtitle">Dry run first, then generate invoices when the result looks right.</div>
          </div>
          <StatusBadge label={generationDryRun ? "Dry run" : "Will generate"} tone={generationDryRun ? "info" : "warning"} />
        </div>
        <div className="panel-body">
          <form className="billing-generation-form" onSubmit={submitGeneration}>
            <div className="field">
              <FieldLabel
                help="The first day included in the billing run."
                htmlFor="generation-period-start"
                label="Period start"
              />
              <input
                className="input"
                id="generation-period-start"
                type="date"
                value={generationPeriodStart}
                onChange={(event) => setGenerationPeriodStart(event.target.value)}
              />
            </div>
            <div className="field">
              <FieldLabel
                help="The last day included in the billing run."
                htmlFor="generation-period-end"
                label="Period end"
              />
              <input
                className="input"
                id="generation-period-end"
                type="date"
                value={generationPeriodEnd}
                onChange={(event) => setGenerationPeriodEnd(event.target.value)}
              />
            </div>
            <div className="field">
              <FieldLabel
                help="The payment due date that will be placed on generated invoices."
                htmlFor="generation-due-date"
                label="Due date"
              />
              <input
                className="input"
                id="generation-due-date"
                type="date"
                value={generationDueDate}
                onChange={(event) => setGenerationDueDate(event.target.value)}
              />
            </div>
            <div className="field">
              <FieldLabel
                help="Optional. Enter one sponsor to run billing for that sponsor only, or leave blank for all sponsors."
                htmlFor="generation-sponsor"
                label="Sponsor code"
              />
              <input
                className="input"
                id="generation-sponsor"
                placeholder="All sponsors"
                value={generationSponsor}
                onChange={(event) => setGenerationSponsor(event.target.value)}
              />
            </div>
            <div className="field">
              <label htmlFor="generation-currency">Currency</label>
              <input
                className="input"
                id="generation-currency"
                value={generationCurrency}
                onChange={(event) => setGenerationCurrency(event.target.value)}
              />
            </div>
            <div className="field">
              <label htmlFor="generation-vat-rate">VAT rate</label>
              <input
                className="input"
                id="generation-vat-rate"
                value={generationVatRate}
                onChange={(event) => setGenerationVatRate(event.target.value)}
              />
            </div>
            <label className="check-field">
              <input
                checked={generationDryRun}
                type="checkbox"
                onChange={(event) => setGenerationDryRun(event.target.checked)}
              />
              Dry run only
              <InfoTooltip text="When this is on, the backend previews the billing run without creating invoices." />
            </label>
            <label className="check-field">
              <input
                checked={generationIssue}
                type="checkbox"
                onChange={(event) => setGenerationIssue(event.target.checked)}
              />
              Issue invoices
              <InfoTooltip text="When enabled during a real run, invoices are issued immediately instead of staying as drafts." />
            </label>
            <button className="button" disabled={generationLoading} type="submit">
              <CalendarClock size={16} />
              {generationLoading ? "Running" : generationDryRun ? "Run preview" : "Generate"}
            </button>
          </form>

          {generationError ? <div className="action-result"><ErrorPanel error={generationError} /></div> : null}
          {generationResult ? <GenerationResult payload={generationResult} /> : null}
          <ActionGuardrail
            badge={generationGuard.badge}
            tone={generationGuard.tone}
            title={generationGuard.title}
            copy={generationGuard.copy}
            items={generationGuard.items}
          />
        </div>
      </section>

      <section className="grid-2" id="billing-position">
        <div className="panel">
          <div className="panel-header">
            <div>
              <PanelTitle
                help="Shows the overall billing totals for the selected tenant."
                title="Billing position"
              />
              <div className="panel-subtitle">Invoice, paid, outstanding, and overdue values.</div>
            </div>
          </div>
          <div className="panel-body">
            <div className="summary-grid">
              <SummaryItem label="Subtotal" value={getNestedValue(dashboard, ["dashboard", "totals", "subtotal_amount"], "0.00")} />
              <SummaryItem label="VAT" value={getNestedValue(dashboard, ["dashboard", "totals", "vat_amount"], "0.00")} />
              <SummaryItem label="Total" value={getNestedValue(dashboard, ["dashboard", "totals", "total_amount"], "0.00")} />
              <SummaryItem label="Paid" value={getNestedValue(dashboard, ["dashboard", "totals", "paid_amount"], "0.00")} />
              <SummaryItem label="Outstanding" value={getNestedValue(dashboard, ["dashboard", "totals", "outstanding_amount"], "0.00")} />
              <SummaryItem label="Overdue" value={getNestedValue(dashboard, ["dashboard", "totals", "overdue_outstanding_amount"], "0.00")} />
            </div>
          </div>
        </div>
        <div className="panel">
          <div className="panel-header">
            <div>
              <PanelTitle
                help="Shows operational invoice signals such as recent invoices and overdue exposure."
                title="Invoice control"
              />
              <div className="panel-subtitle">Status and ageing signals for finance operations.</div>
            </div>
          </div>
          <div className="panel-body route-list">
            {[
              {
                name: "Invoice count",
                value: getNestedValue(dashboard, ["dashboard", "invoice_count"], 0),
                badge: "Live",
              },
              {
                name: "Overdue count",
                value: getNestedValue(dashboard, ["dashboard", "overdue_count"], 0),
                badge: "Watch",
              },
              {
                name: "Recent invoices",
                value: asArrayFromDashboard(dashboard, "recent_invoices").length,
                badge: "Live",
              },
              {
                name: "Overdue invoices",
                value: asArrayFromDashboard(dashboard, "overdue_invoices").length,
                badge: "Watch",
              },
            ].map((item) => (
              <div className="route-item" key={item.name}>
                <div>
                  <div className="route-name">{item.name}</div>
                  <div className="route-path">{formatDisplay(item.value)}</div>
                </div>
                <StatusBadge label={item.badge} tone={item.badge === "Watch" ? "warning" : "success"} />
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="grid-2" id="billing-status">
        <div className="panel">
          <div className="panel-header">
            <div>
              <PanelTitle
                help="Groups invoices by lifecycle state, for example draft, issued, partially paid, or paid."
                title="Invoice status"
              />
              <div className="panel-subtitle">Count by invoice lifecycle status.</div>
            </div>
          </div>
          <div className="panel-body">
            <StatusRows rows={objectCountRows(getNestedValue(dashboard, ["dashboard", "status_counts"], {}))} />
          </div>
        </div>
        <div className="panel">
          <div className="panel-header">
            <div>
              <PanelTitle
                help="Shows how invoice volume is distributed across sponsors."
                title="Sponsor spread"
              />
              <div className="panel-subtitle">Invoice distribution by sponsor.</div>
            </div>
          </div>
          <div className="panel-body">
            <StatusRows rows={objectCountRows(getNestedValue(dashboard, ["dashboard", "sponsor_counts"], {}))} />
          </div>
        </div>
      </section>

      <section className="grid-2" id="billing-invoice-actions">
        <div className="panel">
          <div className="panel-header">
            <div>
              <PanelTitle
                help="Issue draft invoices or record payments against issued invoices."
                title="Invoice actions"
              />
              <div className="panel-subtitle">Issue draft invoices and record sponsor payments.</div>
            </div>
            <StatusBadge label={selectedInvoiceStatus} tone={statusTone(selectedInvoiceStatus)} />
          </div>
          <div className="panel-body">
            <form className="invoice-action-form" onSubmit={submitIssueInvoice}>
              <div className="field">
                <FieldLabel
                  help="Choose the invoice you want to issue or mark with a payment."
                  htmlFor="invoice-action-id"
                  label="Invoice"
                />
                <select
                  className="input"
                  id="invoice-action-id"
                  value={selectedInvoiceId}
                  onChange={(event) => setSelectedInvoiceId(event.target.value)}
                >
                  {invoices.length ? null : <option value="">No invoices returned</option>}
                  {invoices.map((invoice) => {
                    const invoiceId = getValue(invoice, ["invoice_id", "id"], "");
                    return (
                      <option key={invoiceId} value={invoiceId}>
                        {invoiceLabel(invoice)}
                      </option>
                    );
                  })}
                </select>
              </div>
              <button className="button" disabled={!canIssueSelectedInvoice || invoiceActionLoading !== null} type="submit">
                <Send size={16} />
                {invoiceActionLoading === "issue" ? "Issuing" : "Issue invoice"}
              </button>
            </form>
            <form className="invoice-action-form payment-action-form" onSubmit={submitRecordPayment}>
              <div className="field">
                <FieldLabel
                  help="The amount received from the sponsor for the selected invoice."
                  htmlFor="payment-amount"
                  label="Payment amount"
                />
                <input
                  className="input"
                  id="payment-amount"
                  value={paymentAmount}
                  onChange={(event) => setPaymentAmount(event.target.value)}
                />
              </div>
              <div className="field">
                <FieldLabel
                  help="Optional bank or internal reference for the recorded payment."
                  htmlFor="payment-reference"
                  label="Payment reference"
                />
                <input
                  className="input"
                  id="payment-reference"
                  placeholder="Bank reference"
                  value={paymentReference}
                  onChange={(event) => setPaymentReference(event.target.value)}
                />
              </div>
              <button className="button" disabled={!canRecordPayment || invoiceActionLoading !== null} type="submit">
                <WalletCards size={16} />
                {invoiceActionLoading === "payment" ? "Recording" : "Record payment"}
              </button>
            </form>
            {canRecordPayment ? null : (
              <div className="field-hint approval-hint">
                {invoiceActionHint(selectedInvoiceStatus, selectedInvoiceOutstandingNumber)}
              </div>
            )}
            <div className="field-hint">
              Current outstanding amount: {formatDisplay(selectedInvoiceOutstanding || "0.00")}
            </div>
            <ActionGuardrail
              badge={invoiceGuard.badge}
              tone={invoiceGuard.tone}
              title={invoiceGuard.title}
              copy={invoiceGuard.copy}
              items={invoiceGuard.items}
            />
            {invoiceActionError ? <div className="action-result"><ErrorPanel error={invoiceActionError} /></div> : null}
            {invoiceActionResult ? <InvoiceActionResult payload={invoiceActionResult} /> : null}
          </div>
        </div>
        <div className="panel">
          <div className="panel-header">
            <div>
              <PanelTitle
                help="Shows the current state of the invoice before an action is taken."
                title="Selected invoice"
              />
              <div className="panel-subtitle">Operational state before taking action.</div>
            </div>
          </div>
          <div className="panel-body">
            <div className="summary-grid">
              <SummaryItem label="Invoice" value={selectedInvoice ? getValue(selectedInvoice, ["invoice_number", "invoice_id"]) : "-"} />
              <SummaryItem label="Sponsor" value={selectedInvoice ? getValue(selectedInvoice, ["sponsor_code", "sponsor_name"]) : "-"} />
              <SummaryItem label="Status" value={selectedInvoiceStatus} />
              <SummaryItem label="Total" value={selectedInvoice ? getValue(selectedInvoice, ["total_amount", "amount"], "0.00") : "0.00"} />
              <SummaryItem label="Paid" value={selectedInvoice ? getValue(selectedInvoice, ["paid_amount"], "0.00") : "0.00"} />
              <SummaryItem label="Outstanding" value={selectedInvoiceOutstanding || "0.00"} />
            </div>
          </div>
        </div>
      </section>

      <section className="grid-2" id="billing-reporting">
        <div className="panel">
          <div className="panel-header">
            <div>
              <PanelTitle
                help="Builds a sponsor-facing statement for a period, including invoices and payments."
                title="Sponsor statement"
              />
              <div className="panel-subtitle">Invoice and payment position for one sponsor and period.</div>
            </div>
          </div>
          <div className="panel-body">
            <form className="report-form" onSubmit={submitStatement}>
              <div className="field">
                <FieldLabel
                  help="The sponsor whose statement should be loaded."
                  htmlFor="statement-sponsor"
                  label="Sponsor code"
                />
                <input
                  className="input"
                  id="statement-sponsor"
                  value={statementSponsor}
                  onChange={(event) => setStatementSponsor(event.target.value)}
                />
              </div>
              <div className="field">
                <label htmlFor="statement-start">Period start</label>
                <input
                  className="input"
                  id="statement-start"
                  type="date"
                  value={statementPeriodStart}
                  onChange={(event) => setStatementPeriodStart(event.target.value)}
                />
              </div>
              <div className="field">
                <label htmlFor="statement-end">Period end</label>
                <input
                  className="input"
                  id="statement-end"
                  type="date"
                  value={statementPeriodEnd}
                  onChange={(event) => setStatementPeriodEnd(event.target.value)}
                />
              </div>
              <div className="field">
                <label htmlFor="report-currency">Currency</label>
                <input
                  className="input"
                  id="report-currency"
                  value={reportCurrency}
                  onChange={(event) => setReportCurrency(event.target.value)}
                />
              </div>
              <button className="button" disabled={statementLoading} type="submit">
                {statementLoading ? "Loading" : "Load statement"}
              </button>
            </form>
            {statementError ? <div className="action-result"><ErrorPanel error={statementError} /></div> : null}
            {statementResult ? <StatementResult payload={statementResult} /> : null}
            <ActionGuardrail
              badge={reportGuard.badge}
              tone={reportGuard.tone}
              title={reportGuard.title}
              copy={reportGuard.copy}
              items={reportGuard.items}
            />
          </div>
        </div>

        <div className="panel">
          <div className="panel-header">
            <div>
              <PanelTitle
                help="Summarises invoice subtotal, VAT, and total amounts for finance reporting."
                title="VAT report"
              />
              <div className="panel-subtitle">VAT totals by invoice status and currency.</div>
            </div>
          </div>
          <div className="panel-body">
            <form className="report-form vat-report-form" onSubmit={submitVatReport}>
              <div className="field">
                <label htmlFor="vat-scope">Scope</label>
                <input className="input" id="vat-scope" readOnly value={statementSponsor || "All sponsors"} />
              </div>
              <div className="field">
                <label htmlFor="vat-period">Period</label>
                <input
                  className="input"
                  id="vat-period"
                  readOnly
                  value={`${statementPeriodStart} to ${statementPeriodEnd}`}
                />
              </div>
              <button className="button" disabled={vatLoading} type="submit">
                {vatLoading ? "Loading" : "Load VAT"}
              </button>
            </form>
            {vatError ? <div className="action-result"><ErrorPanel error={vatError} /></div> : null}
            {vatResult ? <VatReportResult payload={vatResult} /> : null}
          </div>
        </div>
      </section>

      <section className="panel" id="billing-invoices">
        <div className="panel-header">
          <div>
            <PanelTitle
              help="The latest sponsor invoice records returned by the admin billing API."
              title="Sponsor invoices"
            />
            <div className="panel-subtitle">Read-only invoice list from admin billing.</div>
          </div>
        </div>
        <DataTable
          emptyText="No sponsor invoices returned for this tenant."
          rows={invoices}
          columns={[
            { key: "invoice", header: "Invoice", render: (row) => <span className="mono">{getValue(row, ["invoice_id", "invoice_number", "id"])}</span> },
            { key: "sponsor", header: "Sponsor", render: (row) => getValue(row, ["sponsor_code", "sponsor_name"]) },
            { key: "period", header: "Period", render: (row) => getValue(row, ["period", "billing_period", "period_start"]) },
            { key: "amount", header: "Amount", render: (row) => getValue(row, ["total_amount", "amount", "invoice_total"]) },
            {
              key: "status",
              header: "Status",
              render: (row) => {
                const status = getValue(row, ["status", "invoice_status"]);
                return <StatusBadge label={status} tone={statusTone(status)} />;
              },
            },
          ]}
        />
      </section>

      <section className="panel" id="billing-wallets">
        <div className="panel-header">
          <div>
              <PanelTitle
                help="Sponsor funding wallets used to support marketplace settlement and distribution spend."
              title="Producer funding wallets"
            />
            <div className="panel-subtitle">Read-only marketplace funding wallets.</div>
          </div>
        </div>
        <DataTable
          emptyText="No sponsor wallets returned for this tenant."
          rows={wallets}
          columns={[
            { key: "wallet", header: "Wallet", render: (row) => <span className="mono">{getValue(row, ["wallet_id", "id"])}</span> },
            { key: "sponsor", header: "Sponsor", render: (row) => getValue(row, ["sponsor_code", "sponsor_name"]) },
            { key: "currency", header: "Currency", render: (row) => getValue(row, ["currency"]) },
            { key: "balance", header: "Balance", render: (row) => getValue(row, ["available_balance", "balance", "current_balance"]) },
            {
              key: "status",
              header: "Status",
              render: (row) => {
                const status = getValue(row, ["status", "wallet_status"]);
                return <StatusBadge label={status} tone={statusTone(status)} />;
              },
            },
          ]}
        />
      </section>

      <section className="panel" id="billing-distributor-wallets">
        <div className="panel-header">
          <div>
            <PanelTitle
              help="Distributor earning wallets show the demand-side value owed, held, paid out, or reversed."
              title="Distributor earning wallets"
            />
            <div className="panel-subtitle">Read-only distribution wallet balances.</div>
          </div>
        </div>
        <DataTable
          emptyText="No distributor wallets returned for this tenant."
          rows={distributorWallets}
          columns={[
            { key: "wallet", header: "Wallet", render: (row) => <span className="mono">{getValue(row, ["wallet_id", "id"])}</span> },
            { key: "distributor", header: "Distributor", render: (row) => getValue(row, ["distributor_code", "distributor_name"]) },
            { key: "currency", header: "Currency", render: (row) => getValue(row, ["currency"]) },
            { key: "available", header: "Available", render: (row) => getValue(row, ["available_balance", "balance"]) },
            { key: "held", header: "Held", render: (row) => getValue(row, ["held_balance", "reserved_balance"], "0.00") },
            { key: "paid", header: "Paid out", render: (row) => getValue(row, ["paid_out_balance"], "0.00") },
            {
              key: "status",
              header: "Status",
              render: (row) => {
                const status = getValue(row, ["status", "wallet_status"]);
                return <StatusBadge label={status} tone={statusTone(status)} />;
              },
            },
          ]}
        />
      </section>
    </>
  );
}

function InvoiceActionResult({ payload }: { payload: Record<string, unknown> }) {
  const invoice = getNestedValue(payload, ["invoice"], {}) as Record<string, unknown>;
  const payment = getNestedValue(payload, ["payment"], {}) as Record<string, unknown>;
  return (
    <SummaryGrid
      actionResult
      items={[
        ["Status", getValue(payload, ["status"])],
        ["Invoice", getValue(invoice, ["invoice_number", "invoice_id"])],
        ["Invoice status", getValue(invoice, ["status", "invoice_status"])],
        ["Paid", getValue(invoice, ["paid_amount"], "0.00")],
        ["Outstanding", getValue(invoice, ["outstanding_amount"], "0.00")],
        ["Payment", getValue(payment, ["payment_id"], "-")],
      ]}
    />
  );
}

function StatementResult({ payload }: { payload: Record<string, unknown> }) {
  const statement = getNestedValue(payload, ["statement"], {}) as Record<string, unknown>;
  return (
    <div className="action-result">
      <SummaryGrid
        items={[
          ["Invoices", getNestedValue(statement, ["invoice_count"], 0)],
          ["Payments", getNestedValue(statement, ["payment_count"], 0)],
          ["Total", getNestedValue(statement, ["totals", "total_amount"], "0.00")],
          ["Paid", getNestedValue(statement, ["totals", "paid_amount"], "0.00")],
          ["Outstanding", getNestedValue(statement, ["totals", "outstanding_amount"], "0.00")],
          ["Received", getNestedValue(statement, ["totals", "payments_received_amount"], "0.00")],
        ]}
      />
      <DataTable
        emptyText="No statement invoices returned for this sponsor."
        rows={asArray(getNestedValue(statement, ["invoices"], []))}
        columns={[
          { key: "invoice", header: "Invoice", render: (row) => getValue(row, ["invoice_number", "invoice_id"]) },
          { key: "date", header: "Date", render: (row) => getValue(row, ["issued_at", "invoice_date", "created_at"]) },
          { key: "total", header: "Total", render: (row) => getValue(row, ["total_amount"], "0.00") },
          { key: "outstanding", header: "Outstanding", render: (row) => getValue(row, ["outstanding_amount"], "0.00") },
          {
            key: "status",
            header: "Status",
            render: (row) => {
              const status = getValue(row, ["status"]);
              return <StatusBadge label={status} tone={statusTone(status)} />;
            },
          },
        ]}
      />
    </div>
  );
}

function VatReportResult({ payload }: { payload: Record<string, unknown> }) {
  const report = getNestedValue(payload, ["report"], {}) as Record<string, unknown>;
  return (
    <div className="action-result">
      <SummaryGrid
        items={[
          ["Invoices", getNestedValue(report, ["invoice_count"], 0)],
          ["Subtotal", getNestedValue(report, ["totals", "subtotal_amount"], "0.00")],
          ["VAT", getNestedValue(report, ["totals", "vat_amount"], "0.00")],
          ["Total", getNestedValue(report, ["totals", "total_amount"], "0.00")],
        ]}
      />
      <div className="status-list spacious">
        <div className="status-list-title">By status</div>
        {asArray(getNestedValue(report, ["by_status"], [])).length ? (
          asArray(getNestedValue(report, ["by_status"], [])).map((row) => (
            <div className="status-row" key={getValue(row, ["status"])}>
              <StatusBadge label={getValue(row, ["status"])} tone={statusTone(getValue(row, ["status"]))} />
              <span className="status-count">{getValue(row, ["invoice_count"], "0")}</span>
            </div>
          ))
        ) : (
          <div className="state-panel">No VAT status breakdown returned.</div>
        )}
      </div>
    </div>
  );
}

function GenerationResult({ payload }: { payload: Record<string, unknown> }) {
  const generation = getNestedValue(payload, ["generation"], {}) as Record<string, unknown>;
  const dryRun = getNestedValue(generation, ["dry_run"], getNestedValue(payload, ["dry_run"], true));
  return (
    <SummaryGrid
      actionResult
      items={[
        ["Mode", dryRun ? "Dry run" : "Generated"],
        ["Contracts", getNestedValue(generation, ["contract_count"], 0)],
        ["Invoices", getNestedValue(generation, ["generated_count"], 0)],
        ["Skipped", getNestedValue(generation, ["skipped_count"], 0)],
        ["Errors", getNestedValue(generation, ["error_count"], 0)],
        ["Status", getValue(payload, ["status"])],
      ]}
    />
  );
}

function FundingActionMapRow({
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
  tone: BadgeTone;
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

function StatusRows({ rows }: { rows: Array<{ label: string; count: string }> }) {
  if (!rows.length) {
    return <div className="state-panel">No records returned.</div>;
  }

  return (
    <div className="status-list">
      {rows.map((row) => (
        <div className="status-row" key={row.label}>
          <StatusBadge label={row.label} tone={statusTone(row.label)} />
          <span className="status-count">{row.count}</span>
        </div>
      ))}
    </div>
  );
}

function objectCountRows(value: unknown): Array<{ label: string; count: string }> {
  if (!value || typeof value !== "object") {
    return [];
  }

  return Object.entries(value as Record<string, unknown>).map(([label, count]) => ({
    label,
    count: formatDisplay(count),
  }));
}

function asArrayFromDashboard(value: unknown, key: string): Record<string, unknown>[] {
  const found = getNestedValue(value, ["dashboard", key], []);
  return Array.isArray(found) ? (found as Record<string, unknown>[]) : [];
}

function invoiceLabel(invoice: Record<string, unknown>): string {
  const invoiceNumber = getValue(invoice, ["invoice_number", "invoice_id"]);
  const sponsor = getValue(invoice, ["sponsor_code", "sponsor_name"]);
  const status = getValue(invoice, ["status", "invoice_status"]);
  const outstanding = getValue(invoice, ["outstanding_amount", "total_amount", "amount"], "0.00");
  return `${invoiceNumber} | ${sponsor} | ${status} | ${outstanding}`;
}

type BadgeTone = GuardrailTone;

type Guardrail = {
  badge: string;
  tone: BadgeTone;
  title: string;
  copy: string;
  items: GuardrailItem[];
};

function moneyNumber(value: unknown): number {
  const parsed = Number(String(value ?? "0").replace(/,/g, ""));
  return Number.isFinite(parsed) ? parsed : 0;
}

function sumMoney(rows: Record<string, unknown>[], keys: string[]): number {
  return rows.reduce((total, row) => total + moneyNumber(getValue(row, keys, "0")), 0);
}

function overviewNumber(value: unknown, path: string[], fallback: number): number {
  const found = getNestedValue(value, path, fallback);
  const parsed = moneyNumber(found);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function statusNeedsAttention(status: string): boolean {
  return ["SUSPENDED", "TERMINATED", "FAILED", "BLOCKED", "FROZEN"].includes(status.toUpperCase());
}

function invoiceActionHint(status: string, outstandingAmount: number): string {
  if (status === "DRAFT") {
    return "Issue the draft invoice before recording a sponsor payment.";
  }
  if (status === "PAID" || outstandingAmount <= 0) {
    return "This invoice has no outstanding amount to pay.";
  }
  if (status === "-") {
    return "Select an invoice before recording a payment.";
  }
  return "Payments can only be recorded against issued or partially paid invoices.";
}

function getBillingGenerationGuardrail({
  generationDryRun,
  generationIssue,
  generationLoading,
}: {
  generationDryRun: boolean;
  generationIssue: boolean;
  generationLoading: boolean;
}): Guardrail {
  if (generationLoading) {
    return {
      badge: "Running",
      tone: "info",
      title: "Billing run in progress",
      copy: "Wait for the backend response before starting another billing preview or generation run.",
      items: [
        { label: "Mode", value: generationDryRun ? "Dry run" : "Generate", tone: generationDryRun ? "info" : "warning" },
        { label: "Issue invoices", value: generationIssue ? "Yes" : "No", tone: generationIssue ? "warning" : "neutral" },
        { label: "System change", value: generationDryRun ? "None" : "Invoice records", tone: generationDryRun ? "success" : "warning" },
      ],
    };
  }

  return {
    badge: generationDryRun ? "Preview" : "Will generate",
    tone: generationDryRun ? "info" : "warning",
    title: generationDryRun ? "Preview billing safely" : "Generate sponsor invoices",
    copy: generationDryRun
      ? "This checks the billing run without creating invoices. Use it before a real generation run."
      : "This creates sponsor invoices. If issue invoices is enabled, generated invoices can become payable immediately.",
    items: [
      { label: "Mode", value: generationDryRun ? "Dry run" : "Generate", tone: generationDryRun ? "info" : "warning" },
      { label: "Issue invoices", value: generationIssue ? "Yes" : "No", tone: generationIssue ? "warning" : "neutral" },
      { label: "System change", value: generationDryRun ? "None" : "Invoice records", tone: generationDryRun ? "success" : "warning" },
    ],
  };
}

function getInvoiceActionGuardrail({
  selectedInvoice,
  selectedInvoiceStatus,
  selectedInvoiceOutstandingNumber,
  canIssueSelectedInvoice,
  canRecordPayment,
  invoiceActionLoading,
}: {
  selectedInvoice?: Record<string, unknown>;
  selectedInvoiceStatus: string;
  selectedInvoiceOutstandingNumber: number;
  canIssueSelectedInvoice: boolean;
  canRecordPayment: boolean;
  invoiceActionLoading: "issue" | "payment" | null;
}): Guardrail {
  if (!selectedInvoice) {
    return {
      badge: "Blocked",
      tone: "neutral",
      title: "Select an invoice",
      copy: "Invoice actions are disabled until an invoice is selected from the invoice action dropdown.",
      items: [
        { label: "Selected invoice", value: "Missing", tone: "warning" },
        { label: "Issue invoice", value: "Blocked", tone: "neutral" },
        { label: "Record payment", value: "Blocked", tone: "neutral" },
      ],
    };
  }

  if (invoiceActionLoading) {
    return {
      badge: "Running",
      tone: "info",
      title: invoiceActionLoading === "issue" ? "Issuing invoice" : "Recording payment",
      copy: "Wait for the backend response before taking another invoice action.",
      items: [
        { label: "Invoice status", value: selectedInvoiceStatus, tone: statusTone(selectedInvoiceStatus) as BadgeTone },
        { label: "Outstanding", value: String(selectedInvoiceOutstandingNumber), tone: selectedInvoiceOutstandingNumber > 0 ? "warning" : "success" },
        { label: "System change", value: invoiceActionLoading === "issue" ? "Invoice status" : "Payment ledger", tone: "warning" },
      ],
    };
  }

  return {
    badge: canIssueSelectedInvoice || canRecordPayment ? "Ready" : "Blocked",
    tone: canIssueSelectedInvoice || canRecordPayment ? "success" : "neutral",
    title: canIssueSelectedInvoice ? "Draft invoice can be issued" : canRecordPayment ? "Payment can be recorded" : "No invoice action available",
    copy: canIssueSelectedInvoice
      ? "Issuing this invoice moves it into a payable state."
      : canRecordPayment
        ? "Recording payment captures sponsor funds against the selected invoice."
        : invoiceActionHint(selectedInvoiceStatus, selectedInvoiceOutstandingNumber),
    items: [
      { label: "Invoice status", value: selectedInvoiceStatus, tone: statusTone(selectedInvoiceStatus) as BadgeTone },
      { label: "Issue invoice", value: canIssueSelectedInvoice ? "Available" : "Blocked", tone: canIssueSelectedInvoice ? "success" : "neutral" },
      { label: "Record payment", value: canRecordPayment ? "Available" : "Blocked", tone: canRecordPayment ? "success" : "neutral" },
    ],
  };
}

function getBillingReportGuardrail({
  statementSponsor,
  statementLoading,
  vatLoading,
}: {
  statementSponsor: string;
  statementLoading: boolean;
  vatLoading: boolean;
}): Guardrail {
  const loading = statementLoading || vatLoading;
  return {
    badge: loading ? "Loading" : "Read only",
    tone: loading ? "info" : "success",
    title: loading ? "Finance report is loading" : "Reports do not change billing state",
    copy: "Statements and VAT reports load finance views for review. They do not issue invoices or record payments.",
    items: [
      { label: "Statement sponsor", value: statementSponsor.trim() || "Required", tone: statementSponsor.trim() ? "success" : "warning" },
      { label: "VAT scope", value: statementSponsor.trim() || "All sponsors", tone: "info" },
      { label: "System change", value: "None", tone: "success" },
    ],
  };
}

function getBillingGuidance({
  invoice,
  invoiceCount,
  outstandingAmount,
}: {
  invoice: Record<string, unknown> | undefined;
  invoiceCount: number;
  outstandingAmount: number;
}): {
  badge: string;
  tone: BadgeTone;
  title: string;
  copy: string;
  steps: JourneyStep[];
} {
  if (!invoice) {
    return {
      badge: "No invoice",
      tone: "neutral",
      title: invoiceCount ? "Select an invoice" : "Run billing generation",
      copy: invoiceCount
        ? "Invoices are available. Select one to see whether it should be issued or paid."
        : "No invoices are loaded for this tenant yet. Run a dry-run billing preview, then generate invoices when the preview looks right.",
      steps: [
        journeyStep("Preview billing", "Check the billing run before creating invoices.", "current"),
        journeyStep("Generate invoice", "Create draft or issued invoices from eligible utilisation.", "waiting"),
        journeyStep("Issue invoice", "Send draft invoices into a payable state.", "waiting"),
        journeyStep("Record payment", "Capture sponsor funds against issued invoices.", "waiting"),
        journeyStep("Report", "Use statement and VAT views for finance follow-up.", "waiting"),
      ],
    };
  }

  const status = getValue(invoice, ["status", "invoice_status"], "DRAFT");

  if (status === "DRAFT") {
    return {
      badge: "Issue",
      tone: "info",
      title: "Issue the draft invoice",
      copy: "This invoice exists but has not been issued yet. Issue it before recording sponsor payments against it.",
      steps: [
        journeyStep("Preview billing", "Billing inputs were checked before this invoice was created.", "done"),
        journeyStep("Generate invoice", "The invoice exists in draft form.", "done"),
        journeyStep("Issue invoice", "Move this invoice into an issued, payable state.", "current"),
        journeyStep("Record payment", "Payment can only be recorded after issue.", "waiting"),
        journeyStep("Report", "Statements and VAT reports become useful after invoice activity.", "waiting"),
      ],
    };
  }

  if (status === "ISSUED" || status === "PARTIALLY_PAID") {
    return {
      badge: outstandingAmount > 0 ? "Collect" : "Review",
      tone: outstandingAmount > 0 ? "warning" : "neutral",
      title: outstandingAmount > 0 ? "Record the sponsor payment" : "Review the invoice balance",
      copy:
        outstandingAmount > 0
          ? "The invoice is payable. Record a payment up to the outstanding amount once sponsor funds are received."
          : "This invoice is issued but has no outstanding amount showing. Review the invoice before taking another payment action.",
      steps: [
        journeyStep("Preview billing", "Billing inputs were checked before this invoice was created.", "done"),
        journeyStep("Generate invoice", "The invoice has been generated.", "done"),
        journeyStep("Issue invoice", "The invoice is payable.", "done"),
        journeyStep(
          "Record payment",
          outstandingAmount > 0 ? "Capture sponsor funds up to the outstanding amount." : "Review why no outstanding amount remains.",
          outstandingAmount > 0 ? "current" : "review",
        ),
        journeyStep("Report", "Use statements and VAT once payments or balances need reporting.", "waiting"),
      ],
    };
  }

  if (status === "PAID") {
    return {
      badge: "Complete",
      tone: "success",
      title: "Invoice is paid",
      copy: "This invoice has completed the normal billing lifecycle. Use statements or VAT reporting for follow-up finance reporting.",
      steps: [
        journeyStep("Preview billing", "Billing inputs were checked before this invoice was created.", "done"),
        journeyStep("Generate invoice", "The invoice was generated.", "done"),
        journeyStep("Issue invoice", "The invoice was issued.", "done"),
        journeyStep("Record payment", "The invoice has no outstanding balance.", "done"),
        journeyStep("Report", "Load statements or VAT reports for finance reporting.", "current"),
      ],
    };
  }

  return {
    badge: status,
    tone: statusTone(status) as BadgeTone,
    title: "Review the selected invoice",
    copy: "This invoice is in a status that needs manual finance review before the next action is taken.",
    steps: [
      journeyStep("Preview billing", "Check whether this invoice came from the expected billing run.", "review"),
      journeyStep("Generate invoice", "Confirm invoice creation details.", "review"),
      journeyStep("Issue invoice", "Confirm whether this invoice is payable.", "review"),
      journeyStep("Record payment", "Confirm whether payment is allowed.", "review"),
      journeyStep("Report", "Use reports once the invoice state is understood.", "waiting"),
    ],
  };
}

function journeyStep(label: string, description: string, state: JourneyStep["state"]): JourneyStep {
  const workAreas: Record<string, string> = {
    "Preview billing": "Billing generation",
    "Generate invoice": "Billing generation",
    "Issue invoice": "Invoice actions",
    "Record payment": "Payment actions",
    Report: "Statement, VAT, and reporting panels",
  };
  const targets: Record<string, string> = {
    "Preview billing": "billing-generation",
    "Generate invoice": "billing-generation",
    "Issue invoice": "billing-invoice-actions",
    "Record payment": "billing-invoice-actions",
    Report: "billing-reporting",
  };

  return {
    label,
    description,
    state,
    workArea: workAreas[label],
    targetId: targets[label],
    help: description,
  };
}

function formatDate(value: Date): string {
  return value.toISOString().slice(0, 10);
}

function defaultPeriodStart(): string {
  const now = new Date();
  return formatDate(new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), 1)));
}

function defaultPeriodEnd(): string {
  const now = new Date();
  return formatDate(new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth() + 1, 0)));
}

function defaultDueDate(): string {
  const now = new Date();
  return formatDate(new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth() + 1, 7)));
}
