import { Building2, ChartNoAxesCombined, ReceiptText, Target, WalletCards, type LucideIcon } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import {
  closeProducerSupplyOpportunity,
  createProducerSupplyLaunch,
  getAdminSponsorWallets,
  getSponsorExperience,
  getSponsorPortalContractLedger,
  getSponsorPortalStatement,
  getSponsorPortalWalletLedger,
  publishProducerSupplyOpportunity,
  reopenProducerSupplyOpportunity,
  updateProducerSupplyOpportunity,
} from "../../api/endpoints/sponsorBilling";
import { DataTable } from "../../components/DataTable";
import { EmptyState } from "../../components/EmptyState";
import { ErrorPanel } from "../../components/ErrorPanel";
import { FieldLabel } from "../../components/FieldLabel";
import { ActionGuardrail, GuardrailItem, GuardrailTone } from "../../components/ActionGuardrail";
import { InsuranceJourneyProofPanel } from "../../components/InsuranceJourneyProofPanel";
import { JourneyStep, JourneyTracker } from "../../components/JourneyTracker";
import { KpiCard } from "../../components/KpiCard";
import { LoadingState } from "../../components/LoadingState";
import { PanelTitle } from "../../components/PanelTitle";
import { StatusBadge } from "../../components/StatusBadge";
import { SummaryGrid } from "../../components/SummaryGrid";
import { SummaryItem } from "../../components/SummaryItem";
import { normalizeSessionRole, useBackendSession } from "../../auth/useBackendSession";
import {
  asArray,
  currencyFrom,
  formatCurrency,
  formatDisplay,
  formatPercent,
  getNestedValue,
  getValue,
  moneyValue,
  statusTone,
  useRefreshContext,
} from "../pageUtils";
import { SponsorWorkspaceView } from "./components/SponsorWorkspaceView";

const TENANT_KEY = "amplifi.sponsorPortal.tenant";
const SPONSOR_KEY = "amplifi.sponsorPortal.sponsor";
const today = new Date().toISOString().slice(0, 10);
const monthStart = today.slice(0, 8) + "01";

type SponsorPageMode = "workspace" | "operations";

export function SponsorOperationsPage() {
  return <SponsorPortalPage mode="operations" />;
}

export function SponsorPortalPage({ mode = "workspace" }: { mode?: SponsorPageMode }) {
  const { refreshKey } = useRefreshContext();
  const backend = useBackendSession(refreshKey, "producer-workspace");
  const [tenantCode, setTenantCode] = useState(localStorage.getItem(TENANT_KEY) || "FNB");
  const [sponsorCode, setSponsorCode] = useState(localStorage.getItem(SPONSOR_KEY) || "");
  const [submitted, setSubmitted] = useState({
    tenantCode: localStorage.getItem(TENANT_KEY) || "FNB",
    sponsorCode: localStorage.getItem(SPONSOR_KEY) || "",
  });
  const [dashboard, setDashboard] = useState<unknown>(null);
  const [wallet, setWallet] = useState<unknown>(null);
  const [sponsorOptions, setSponsorOptions] = useState<Record<string, unknown>[]>([]);
  const [sponsorOptionsLoading, setSponsorOptionsLoading] = useState(false);
  const [sponsorOptionsError, setSponsorOptionsError] = useState<string | null>(null);
  const [invoices, setInvoices] = useState<Record<string, unknown>[]>([]);
  const [contracts, setContracts] = useState<Record<string, unknown>[]>([]);
  const [receipts, setReceipts] = useState<Record<string, unknown>[]>([]);
  const [forecast, setForecast] = useState<unknown>(null);
  const [opportunities, setOpportunities] = useState<Record<string, unknown>[]>([]);
  const [performanceOverview, setPerformanceOverview] = useState<unknown>(null);
  const [opportunityPerformance, setOpportunityPerformance] = useState<Record<string, unknown>[]>([]);
  const [supplyConversionSummary, setSupplyConversionSummary] = useState<unknown>(null);
  const [supplyConversions, setSupplyConversions] = useState<Record<string, unknown>[]>([]);
  const [walletLedger, setWalletLedger] = useState<Record<string, unknown>[]>([]);
  const [insuranceProof, setInsuranceProof] = useState<unknown>(null);
  const [outcomeMoneyReview, setOutcomeMoneyReview] = useState<unknown>(null);
  const [channelReadiness, setChannelReadiness] = useState<unknown>(null);
  const [channelRecommendations, setChannelRecommendations] = useState<unknown>(null);
  const [statement, setStatement] = useState<unknown>(null);
  const [contractLedger, setContractLedger] = useState<Record<string, unknown>[]>([]);
  const [selectedContractId, setSelectedContractId] = useState("");
  const [statementPeriodStart, setStatementPeriodStart] = useState(monthStart);
  const [statementPeriodEnd, setStatementPeriodEnd] = useState(today);
  const [portalCurrency, setPortalCurrency] = useState("ZAR");
  const [statementLoading, setStatementLoading] = useState(false);
  const [statementError, setStatementError] = useState<unknown>(null);
  const [statementResult, setStatementResult] = useState<unknown>(null);
  const [supplyForm, setSupplyForm] = useState({
    campaignName: "Activate funeral cover",
    campaignCode: "",
    segment: "INSURANCE",
    opportunityTitle: "Activate funeral cover",
    productCode: "INSURANCE",
    productName: "Funeral plan",
    description: "Acquire customers who accept a quote, receive a policy, and pay the first premium.",
    targetSegments: "INSURANCE, MASS_MARKET",
    targetRegions: "ZA",
    targetChannels: "WHATSAPP, FIELD, DIGITAL",
    distributorTypes: "BROKER, AFFILIATE, RETAILER",
    estimatedRewardAmount: "100.00",
    estimatedCommissionAmount: "25.00",
    totalBudget: "10000.00",
    maxAllocations: "100",
    publishNow: false,
  });
  const [supplyLoading, setSupplyLoading] = useState(false);
  const [supplyError, setSupplyError] = useState<unknown>(null);
  const [supplyResult, setSupplyResult] = useState<Record<string, unknown> | null>(null);
  const [opportunityActionLoading, setOpportunityActionLoading] = useState<string | null>(null);
  const [opportunityActionError, setOpportunityActionError] = useState<unknown>(null);
  const [opportunityActionResult, setOpportunityActionResult] = useState<Record<string, unknown> | null>(null);
  const [selectedDraftId, setSelectedDraftId] = useState("");
  const [draftEditForm, setDraftEditForm] = useState({
    title: "",
    description: "",
    totalBudget: "",
    maxAllocations: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const sponsorGuidance = getSponsorGuidance({
    hasSponsor: Boolean(submitted.tenantCode && submitted.sponsorCode),
    dashboard,
    wallet,
    invoices,
    contracts,
    receipts,
    forecast,
    opportunities,
  });
  const statementGuard = getStatementGuardrail({
    statementPeriodStart,
    statementPeriodEnd,
    portalCurrency,
    statementLoading,
  });
  const channelItems = asArray(getNestedValue(channelReadiness, ["items"], []));
  const channelReadyCount = Number(getNestedValue(channelReadiness, ["summary", "ready_count"], 0)) || 0;
  const channelCount = Number(getNestedValue(channelReadiness, ["summary", "count"], channelItems.length)) || channelItems.length;
  const channelStatus = formatDisplay(getNestedValue(channelReadiness, ["status"], channelItems.length ? "ATTENTION" : "UNKNOWN"));
  const supportedChannels = formatDisplay(getNestedValue(channelReadiness, ["summary", "supported_channels"], []));
  const topChannel = getNestedValue(channelRecommendations, ["top_channel"], {});
  const topChannelCode = formatDisplay(getNestedValue(topChannel, ["channel_code"], "-"));
  const topChannelScore = formatDisplay(getNestedValue(topChannel, ["recommendation_score"], "-"));
  const topChannelAction = formatDisplay(getNestedValue(topChannel, ["recommended_action"], "No channel recommendation returned."));
  const producerSessionLocked =
    backend.status === "confirmed" &&
    normalizeSessionRole(backend.session?.role) === "producer" &&
    Boolean(backend.session?.producer_code);
  const walletCurrency = currencyFrom(wallet, portalCurrency);
  const availableWalletDisplay = formatCurrency(
    getWalletValue(wallet, ["available_balance", "balance", "current_balance"]),
    walletCurrency,
  );
  const outstandingExposureDisplay = formatCurrency(
    getNestedValue(dashboard, ["dashboard", "totals", "outstanding_amount"], "0.00"),
    walletCurrency,
  );

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cleanedTenant = tenantCode.trim().toUpperCase();
    const cleanedSponsor = sponsorCode.trim().toUpperCase();
    localStorage.setItem(TENANT_KEY, cleanedTenant);
    localStorage.setItem(SPONSOR_KEY, cleanedSponsor);
    setTenantCode(cleanedTenant);
    setSponsorCode(cleanedSponsor);
    setSubmitted({ tenantCode: cleanedTenant, sponsorCode: cleanedSponsor });
  }

  useEffect(() => {
    if (!producerSessionLocked || !backend.session?.producer_code) {
      return;
    }

    const scopedTenant = String(backend.session.tenant_code || backend.session.tenant || "FNB").toUpperCase();
    const scopedProducer = String(backend.session.producer_code).toUpperCase();

    localStorage.setItem(TENANT_KEY, scopedTenant);
    localStorage.setItem(SPONSOR_KEY, scopedProducer);
    setTenantCode(scopedTenant);
    setSponsorCode(scopedProducer);
    setSubmitted({ tenantCode: scopedTenant, sponsorCode: scopedProducer });
  }, [
    producerSessionLocked,
    backend.session?.tenant_code,
    backend.session?.tenant,
    backend.session?.producer_code,
  ]);

  useEffect(() => {
    const cleanedTenant = tenantCode.trim().toUpperCase();
    if (!cleanedTenant) {
      setSponsorOptions([]);
      setSponsorOptionsError(null);
      return;
    }

    let alive = true;
    setSponsorOptionsLoading(true);
    setSponsorOptionsError(null);
    getAdminSponsorWallets(cleanedTenant, 100)
      .then((walletPayload) => {
        if (alive) {
          setSponsorOptions(asArray(walletPayload));
        }
      })
      .catch((requestError) => {
        if (alive) {
          setSponsorOptions([]);
          setSponsorOptionsError(requestError?.message || "Could not load sponsors for this tenant.");
        }
      })
      .finally(() => alive && setSponsorOptionsLoading(false));
    return () => {
      alive = false;
    };
  }, [tenantCode, refreshKey]);

  useEffect(() => {
    if (!submitted.tenantCode || !submitted.sponsorCode) {
      return;
    }

    let alive = true;
    setLoading(true);
    setError(null);
    Promise.all([
      getSponsorExperience(submitted.tenantCode, submitted.sponsorCode, portalCurrency),
      getSponsorPortalWalletLedger(submitted.tenantCode, submitted.sponsorCode).catch(() => []),
    ])
      .then(([
        experiencePayload,
        walletLedgerPayload,
      ]) => {
        if (alive) {
          const sections = getNestedValue(experiencePayload, ["sections"], {}) as Record<string, unknown>;
          setDashboard({
            status: "ok",
            dashboard: getNestedValue(sections.billing, ["data"], {}),
          });
          setWallet(getNestedValue(sections.wallet, ["data"], null));
          setInvoices(asArray(getNestedValue(sections.invoices, ["data"], [])));
          setContracts(asArray(getNestedValue(sections.contracts, ["data"], [])));
          setReceipts(asArray(getNestedValue(sections.receipts, ["data"], [])));
          setForecast(getNestedValue(sections.forecast, ["data"], null));
          setOpportunities(asArray(getNestedValue(sections.opportunities, ["data"], [])));
          setPerformanceOverview(getNestedValue(sections.performanceOverview, ["data"], null));
          setOpportunityPerformance(asArray(getNestedValue(sections.opportunityPerformance, ["data"], [])));
          const supplyConversionPayload = getNestedValue(sections.conversions, ["data"], null);
          setSupplyConversionSummary(supplyConversionPayload);
          setSupplyConversions(asArray(getNestedValue(supplyConversionPayload, ["items"], [])));
          setOutcomeMoneyReview(getNestedValue(sections.outcomeMoney, ["data"], null));
          setInsuranceProof(getNestedValue(sections.proof, ["data"], null));
          const channelPayload = getNestedValue(sections.channels, ["data"], null);
          setChannelReadiness(getNestedValue(channelPayload, ["readiness"], null));
          setChannelRecommendations(getNestedValue(channelPayload, ["recommendations"], null));
          setWalletLedger(asArray(walletLedgerPayload));
        }
      })
      .catch((requestError) => alive && setError(requestError))
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [submitted, refreshKey, portalCurrency]);

  useEffect(() => {
    if (!contracts.length) {
      setSelectedContractId("");
      return;
    }

    const current = contracts.find((contract) => getValue(contract, ["contract_id", "id"]) === selectedContractId);
    setSelectedContractId(getValue(current || contracts[0], ["contract_id", "id"], ""));
  }, [contracts, selectedContractId]);

  useEffect(() => {
    if (!submitted.tenantCode || !submitted.sponsorCode || !selectedContractId) {
      setContractLedger([]);
      return;
    }

    let alive = true;
    getSponsorPortalContractLedger(submitted.tenantCode, submitted.sponsorCode, selectedContractId)
      .then((payload) => {
        if (alive) {
          setContractLedger(asArray(payload));
        }
      })
      .catch(() => {
        if (alive) {
          setContractLedger([]);
        }
      });
    return () => {
      alive = false;
    };
  }, [submitted, selectedContractId, refreshKey]);

  function loadStatement(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!submitted.tenantCode || !submitted.sponsorCode) {
      return;
    }

    setStatementLoading(true);
    setStatementError(null);
    setStatementResult(null);
    getSponsorPortalStatement(
      submitted.tenantCode,
      submitted.sponsorCode,
      statementPeriodStart,
      statementPeriodEnd,
      portalCurrency,
    )
      .then((payload) => {
        setStatement(payload);
        setStatementResult(payload);
      })
      .catch((requestError) => setStatementError(requestError))
      .finally(() => setStatementLoading(false));
  }

  function submitSupplyLaunch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!submitted.tenantCode || !submitted.sponsorCode || supplyLoading) {
      return;
    }

    const campaignName = supplyForm.campaignName.trim();
    const opportunityTitle = supplyForm.opportunityTitle.trim();
    const segment = supplyForm.segment.trim().toUpperCase();
    if (!campaignName || !opportunityTitle || !segment) {
      setSupplyError({ message: "Campaign name, opportunity title, and segment are required." });
      return;
    }

    const generatedCode = buildProducerCode(campaignName);
    const campaignCode = (supplyForm.campaignCode.trim() || generatedCode).toUpperCase();
    const opportunityCode = `${campaignCode}-OPP`;
    setSupplyLoading(true);
    setSupplyError(null);
    setSupplyResult(null);

    createProducerSupplyLaunch(submitted.tenantCode, submitted.sponsorCode, {
      campaign_name: campaignName,
      campaign_code: campaignCode,
      opportunity_code: opportunityCode,
      segment,
      opportunity_title: opportunityTitle,
      description: supplyForm.description.trim() || undefined,
      funding_contract_id: selectedContractId || undefined,
      product_code: supplyForm.productCode.trim() || undefined,
      product_name: supplyForm.productName.trim() || undefined,
      target_segments: csvList(supplyForm.targetSegments),
      target_regions: csvList(supplyForm.targetRegions),
      target_channels: csvList(supplyForm.targetChannels),
      distributor_types: csvList(supplyForm.distributorTypes),
      estimated_reward_amount: supplyForm.estimatedRewardAmount || undefined,
      estimated_commission_amount: supplyForm.estimatedCommissionAmount || undefined,
      total_budget: supplyForm.totalBudget || undefined,
      max_allocations: numberOrUndefined(supplyForm.maxAllocations),
      publish_now: supplyForm.publishNow,
      metadata: {
        source: "producer_workspace",
      },
    })
      .then((payload) => {
        setSupplyResult(payload);
        const opportunity = getNestedValue(payload, ["opportunity"], null);
        if (opportunity && typeof opportunity === "object") {
          setOpportunities((current) => upsertOpportunity(current, opportunity as Record<string, unknown>));
        }
        setSupplyForm((current) => ({
          ...current,
          campaignCode: "",
          opportunityTitle: current.opportunityTitle,
        }));
      })
      .catch((requestError) => setSupplyError(requestError))
      .finally(() => setSupplyLoading(false));
  }

  function selectDraftOpportunity(opportunity: Record<string, unknown>) {
    setSelectedDraftId(getValue(opportunity, ["opportunity_id", "id"], ""));
    setDraftEditForm({
      title: getValue(opportunity, ["title", "opportunity_title"], ""),
      description: getValue(opportunity, ["description"], ""),
      totalBudget: getValue(opportunity, ["total_budget"], ""),
      maxAllocations: getValue(opportunity, ["max_allocations"], ""),
    });
    setOpportunityActionError(null);
    setOpportunityActionResult(null);
  }

  function saveDraftOpportunity(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!submitted.tenantCode || !submitted.sponsorCode || !selectedDraftId || opportunityActionLoading) {
      return;
    }

    setOpportunityActionLoading(`edit:${selectedDraftId}`);
    setOpportunityActionError(null);
    setOpportunityActionResult(null);
    updateProducerSupplyOpportunity(submitted.tenantCode, submitted.sponsorCode, selectedDraftId, {
      title: draftEditForm.title.trim() || undefined,
      description: draftEditForm.description.trim() || undefined,
      total_budget: draftEditForm.totalBudget || undefined,
      max_allocations: numberOrUndefined(draftEditForm.maxAllocations),
      metadata: { source: "producer_workspace" },
    })
      .then((payload) => {
        setOpportunityActionResult(payload);
        setOpportunities((current) => upsertOpportunity(current, payload));
      })
      .catch((requestError) => setOpportunityActionError(requestError))
      .finally(() => setOpportunityActionLoading(null));
  }

  function runOpportunityLifecycle(action: "publish" | "close" | "reopen", opportunity: Record<string, unknown>) {
    if (!submitted.tenantCode || !submitted.sponsorCode || opportunityActionLoading) {
      return;
    }

    const opportunityId = getValue(opportunity, ["opportunity_id", "id"], "");
    if (!opportunityId) {
      return;
    }

    const actionMap = {
      publish: publishProducerSupplyOpportunity,
      close: closeProducerSupplyOpportunity,
      reopen: reopenProducerSupplyOpportunity,
    };
    setOpportunityActionLoading(`${action}:${opportunityId}`);
    setOpportunityActionError(null);
    setOpportunityActionResult(null);
    actionMap[action](submitted.tenantCode, submitted.sponsorCode, opportunityId)
      .then((payload) => {
        setOpportunityActionResult(payload);
        setOpportunities((current) => upsertOpportunity(current, payload));
        if (selectedDraftId === opportunityId && action !== "publish") {
          setSelectedDraftId("");
        }
      })
      .catch((requestError) => setOpportunityActionError(requestError))
      .finally(() => setOpportunityActionLoading(null));
  }

  if (mode === "workspace") {
    const activeCampaigns = getNestedValue(performanceOverview, ["opportunities", "published_count"], opportunities.length || "-");
    const acquiredCustomers = getNestedValue(
      performanceOverview,
      ["conversions", "completed_count"],
      getNestedValue(supplyConversionSummary, ["completed_count"], supplyConversions.length),
    );
    const walletBalance = getWalletValue(wallet, ["available_balance", "balance", "current_balance"]);
    const rewardLiability = getNestedValue(dashboard, ["dashboard", "totals", "outstanding_amount"], "0.00");
    const producerName = getWalletValue(wallet, ["sponsor_name", "producer_name", "sponsor_code"]);
    const campaignRows = opportunities.slice(0, 6);

    return (
      <SponsorWorkspaceView
        activeCampaigns={activeCampaigns}
        acquiredCustomers={acquiredCustomers}
        campaignRows={campaignRows}
        channelCount={channelCount}
        channelReadyCount={channelReadyCount}
        channelStatus={channelStatus}
        contracts={contracts}
        error={error}
        forecast={forecast}
        loading={loading}
        opportunityPerformance={opportunityPerformance}
        producerName={producerName}
        producerSessionLocked={producerSessionLocked}
        receipts={receipts}
        rewardLiability={rewardLiability}
        sponsorCode={sponsorCode}
        sponsorOptions={sponsorOptions}
        sponsorOptionsLoading={sponsorOptionsLoading}
        submitted={submitted}
        tenantCode={tenantCode}
        walletBalance={walletBalance}
        onSponsorCodeChange={setSponsorCode}
        onSubmit={submit}
        onTenantCodeChange={setTenantCode}
      />
    );
  }

  return (
    <>
      <section className="page-header">
        <div>
          <div className="page-kicker">Producer - Supply</div>
          <h1 className="page-title">Organisation Workspace</h1>
          <p className="page-copy">
            Where a producer runs distribution strategy: campaigns, partners, funding, fulfilment, and performance.
            Current live data is pulled from the funding, billing, wallet, contract, receipt, statement, and forecast spine.
          </p>
        </div>
        <StatusBadge label="Supply publishing mapped" tone="success" />
      </section>

      <section className="producer-outcome-grid">
        <ProducerOutcomeCard
          icon={Target}
          kicker="Outcome first"
          title="Acquire customers"
          copy="Define the acquisition result: open an account, switch salary, buy a product, sign a contract, or register."
          badge="Representable now"
          tone="info"
        />
        <ProducerOutcomeCard
          icon={Building2}
          kicker="Supply to demand"
          title="Publish offers"
          copy="Package campaign intent, rewards, eligibility, and target audiences so distributors can choose what to promote."
          badge="Producer API"
          tone="success"
        />
        <ProducerOutcomeCard
          icon={WalletCards}
          kicker="Financial rail"
          title="Fund rewards"
          copy="Use wallets, contracts, invoices, statements, receipts, and forecasts to control reward exposure."
          badge="Live now"
          tone="success"
        />
        <ProducerOutcomeCard
          icon={ChartNoAxesCombined}
          kicker="Performance"
          title="Measure ROI"
          copy="Track acquisition performance, campaign spend, funding runway, billing exposure, and distributor quality."
          badge="Partial"
          tone="info"
        />
      </section>

      <section className="grid-3 producer-kpi-grid">
          <KpiCard
          label="Active campaigns"
          value={formatDisplay(getNestedValue(performanceOverview, ["opportunities", "published_count"], opportunities.length || "-"))}
          footnote={opportunities.length ? "Published producer opportunities from backend reporting" : "Create a supply launch to publish demand"}
          icon={Target}
        />
        <KpiCard
          label="Accepted routes"
          value={formatDisplay(getNestedValue(performanceOverview, ["routes", "accepted_count"], "-"))}
          footnote="Distributor demand accepted for this producer"
          icon={ChartNoAxesCombined}
        />
        <KpiCard
          label="Customer conversions"
          value={supplyConversions.length}
          footnote="Linked customer journeys from accepted distributor routes"
          icon={Target}
        />
        <KpiCard
          label="Producer wallet balance"
          value={availableWalletDisplay}
          footnote="Available reward funding"
          icon={WalletCards}
        />
        <KpiCard
          label="Reward liability"
          value={outstandingExposureDisplay}
          footnote="Pending billing and reward exposure"
          icon={ReceiptText}
        />
      </section>

      <section className="grid-2 producer-workspace-grid">
        <div className="panel">
          <div className="panel-header">
            <div>
              <PanelTitle
                help="Uses the existing campaign API and distribution opportunity API to create producer demand without adding a parallel backend flow."
                title="Campaigns"
              />
              <div className="panel-subtitle">Producer opportunities, marketplace status, and draft controls.</div>
            </div>
            <span className="muted mono">distribution / products / offers</span>
          </div>
          <DataTable
            emptyText="No producer opportunities returned yet."
            rows={opportunities}
            columns={[
              {
                key: "campaign",
                header: "Campaign",
                render: (row) => (
                  <div>
                    <strong>{getValue(row, ["title", "opportunity_title", "opportunity_code"])}</strong>
                    <div className="table-subtext">{getValue(row, ["campaign_code", "product_name", "description"], "Producer supply")}</div>
                  </div>
                ),
              },
              {
                key: "status",
                header: "Status",
                render: (row) => {
                  const status = getValue(row, ["opportunity_status", "status"], "Planned");
                  return <StatusBadge label={status} tone={statusTone(status)} />;
                },
              },
              {
                key: "readiness",
                header: "Readiness",
                render: (row) => {
                  const performance = findOpportunityPerformance(opportunityPerformance, row);
                  return <OpportunityReadiness opportunity={row} performance={performance} />;
                },
              },
              { key: "budget", header: "Budget", render: (row) => moneyValue(row, ["total_budget", "remaining_budget"], "0.00") },
              { key: "remaining", header: "Remaining", render: (row) => getValue(row, ["remaining_allocations", "max_allocations"], "-") },
              {
                key: "actions",
                header: "Actions",
                render: (row) => (
                  <OpportunityActions
                    loadingKey={opportunityActionLoading}
                    opportunity={row}
                    onClose={runOpportunityLifecycle}
                    onEdit={selectDraftOpportunity}
                    onPublish={runOpportunityLifecycle}
                    onReopen={runOpportunityLifecycle}
                  />
                ),
              },
              {
                key: "performance",
                header: "Performance",
                render: (row) => {
                  const performance = findOpportunityPerformance(opportunityPerformance, row);
                  return (
                    <div>
                      <strong>{formatDisplay(getValue(performance, ["accepted_count"], "0"))} accepted</strong>
                      <div className="table-subtext">
                        {formatDisplay(getValue(performance, ["conversion_count"], "0"))} journeys /{" "}
                        {formatDisplay(getValue(performance, ["completed_conversion_count"], "0"))} complete /{" "}
                        {formatPercent(getValue(performance, ["conversion_completion_rate"], "0.0000"))} rate
                      </div>
                      <div className="table-subtext">
                        {formatDisplay(getValue(performance, ["routed_count"], "0"))} routed / score{" "}
                        {formatDisplay(getValue(performance, ["average_route_score"], "0"))}
                      </div>
                    </div>
                  );
                },
              },
            ]}
          />
          {opportunityActionError ? <ErrorPanel error={opportunityActionError} /> : null}
          {opportunityActionResult ? <OpportunityActionResult payload={opportunityActionResult} /> : null}
        </div>

        <div className="producer-side-stack">
          <div className="panel">
            <div className="panel-header">
              <div>
                <PanelTitle help="Funding exposure across contracts, wallet, invoices, and pending settlement." title="Funding & exposure" />
                <div className="panel-subtitle">How much distribution funding is available and at risk.</div>
              </div>
            </div>
            <div className="panel-body status-list spacious">
              <ExposureRow label="Committed contracts" value={contracts.length ? `${contracts.length} contracts` : "-"} />
              <ExposureRow label="Funds available" value={availableWalletDisplay} tone="success" />
              <ExposureRow label="Outstanding exposure" value={outstandingExposureDisplay} />
              <ExposureRow label="Accepted demand" value={getNestedValue(performanceOverview, ["routes", "accepted_count"], "-")} tone="success" />
              <ExposureRow label="Forecast runway" value={getNestedValue(forecast, ["forecast", "wallet", "days_remaining"], "-")} />
            </div>
          </div>

          <div className="panel">
            <div className="panel-header">
              <div>
                <PanelTitle help="Shows whether partner and channel data can be represented from the current backend." title="Channel readiness" />
                <div className="panel-subtitle">What the producer can safely rely on today.</div>
              </div>
            </div>
            <div className="panel-body status-list spacious">
              <ExposureRow label="Funding wallet" value={availableWalletDisplay} tone="success" />
              <ExposureRow label="Contracts" value={contracts.length ? `${contracts.length} loaded` : "Needs setup"} tone={contracts.length ? "success" : "warning"} />
              <ExposureRow label="Campaign publishing" value={opportunities.length ? `${opportunities.length} opportunities` : "Producer API"} tone="success" />
              <ExposureRow label="Performance reporting" value={opportunityPerformance.length ? `${opportunityPerformance.length} rows` : "No activity yet"} tone={opportunityPerformance.length ? "success" : "warning"} />
              <ExposureRow label="Customer conversions" value={supplyConversions.length ? `${supplyConversions.length} linked` : "Awaiting referrals"} tone={supplyConversions.length ? "success" : "warning"} />
              <ExposureRow label="Channel adapters" value={channelCount ? `${channelReadyCount}/${channelCount} ready` : "Unavailable"} tone={channelStatus === "READY" ? "success" : "warning"} />
              <ExposureRow label="Supported channels" value={supportedChannels || "WhatsApp, SMS, USSD"} tone={channelItems.length ? "success" : "warning"} />
              <ExposureRow label="Recommended channel" value={topChannelCode} tone={topChannelCode !== "-" ? "success" : "warning"} />
              <ExposureRow label="Recommendation score" value={topChannelScore} tone={topChannelScore !== "-" ? "success" : "warning"} />
              <ExposureRow label="Next channel action" value={topChannelAction} tone={topChannelCode !== "-" ? "success" : "warning"} />
            </div>
          </div>
        </div>
      </section>

      <section className="panel" id="producer-customer-conversions">
        <div className="panel-header">
          <div>
            <PanelTitle
              help="Shows customer journeys linked from accepted distributor routes back to this producer's opportunities."
              title="Customer conversions"
            />
            <div className="panel-subtitle">Producer supply performance by opportunity, distributor, and next customer milestone.</div>
          </div>
          <StatusBadge
            label={`${formatDisplay(getNestedValue(supplyConversionSummary, ["completed_count"], 0))}/${formatDisplay(getNestedValue(supplyConversionSummary, ["count"], supplyConversions.length))} complete | ${formatPercent(getNestedValue(supplyConversionSummary, ["completion_rate"], "0.0000"))}`}
            tone={supplyConversions.length ? "success" : "neutral"}
          />
        </div>
        <DataTable
          emptyText="No linked customer conversions returned yet."
          rows={supplyConversions}
          columns={[
            {
              key: "opportunity",
              header: "Opportunity",
              render: (row) => (
                <div>
                  <strong>{getValue(row, ["opportunity_title", "opportunity_code"], "Producer supply")}</strong>
                  <div className="table-subtext">{getValue(row, ["campaign_code", "product", "sub_product"], "-")}</div>
                </div>
              ),
            },
            {
              key: "distributor",
              header: "Distributor",
              render: (row) => (
                <div>
                  <strong>{getValue(row, ["distributor_name", "distributor_code"], "-")}</strong>
                  <div className="table-subtext">{getValue(row, ["distributor_type", "distributor_code"], "-")}</div>
                </div>
              ),
            },
            {
              key: "journey",
              header: "Customer journey",
              render: (row) => (
                <div>
                  <strong>{getValue(row, ["display_status", "status"], "-")}</strong>
                  <div className="table-subtext mono">{getValue(row, ["referral_track_id"], "-")}</div>
                </div>
              ),
            },
            {
              key: "progress",
              header: "Progress",
              render: (row) => `${formatDisplay(getValue(row, ["progress_percent"], "0"))}%`,
            },
            {
              key: "next",
              header: "Next step",
              render: (row) => producerConversionNextStep(row),
            },
            {
              key: "state",
              header: "State",
              render: (row) => {
                const complete = Boolean(row.is_complete);
                const label = complete ? "Complete" : getValue(row, ["progress_band", "status"], "In progress");
                return <StatusBadge label={label} tone={complete ? "success" : statusTone(label)} />;
              },
            },
          ]}
        />
      </section>

      <section className="panel" id="sponsor-identity">
        <div className="panel-header">
          <div>
            <PanelTitle
              help="Sets the tenant and producer funding context for billing, wallet, contract, statement, and forecast requests."
              title="Producer identity"
            />
            <div className="panel-subtitle">Used for producer-scoped funding, billing, and performance requests.</div>
          </div>
        </div>
        <div className="panel-body">
          <form className="form-row sponsor-picker-row" onSubmit={submit}>
            <div className="field">
              <FieldLabel help="The tenant whose producer workspace should be loaded." htmlFor="sponsor-tenant" label="Tenant code" />
              <input
                className="input"
                disabled={producerSessionLocked}
                id="sponsor-tenant"
                value={tenantCode}
                onChange={(event) => setTenantCode(event.target.value)}
              />
              {producerSessionLocked ? <div className="field-hint">Backend-confirmed tenant scope.</div> : null}
            </div>
            <div className="field">
              <FieldLabel help="A convenience picker loaded from producer funding wallets for the selected tenant." htmlFor="sponsor-picker" label="Producer picker" />
              <select
                className="input"
                disabled={producerSessionLocked || sponsorOptionsLoading || !sponsorOptions.length}
                id="sponsor-picker"
                value={sponsorCode}
                onChange={(event) => setSponsorCode(event.target.value)}
              >
                <option value="">
                  {sponsorOptionsLoading
                    ? "Loading producers..."
                    : sponsorOptions.length
                      ? "Select a producer"
                      : "No producers found"}
                </option>
                {sponsorOptions.map((option) => {
                  const code = getValue(option, ["sponsor_code"]);
                  const name = getValue(option, ["sponsor_name"]);
                  const available = getValue(option, ["available_balance"], "0.00");
                  return (
                    <option key={code} value={code}>
                      {name} - {code} - available {available}
                    </option>
                  );
                })}
              </select>
              {sponsorOptionsError ? <div className="field-hint danger-text">{sponsorOptionsError}</div> : null}
            </div>
            <div className="field">
              <FieldLabel help="The producer funding code used by the portal APIs." htmlFor="sponsor-code" label="Producer code" />
              <input
                className="input"
                disabled={producerSessionLocked}
                id="sponsor-code"
                value={sponsorCode}
                onChange={(event) => setSponsorCode(event.target.value)}
              />
              <div className="field-hint">
                {producerSessionLocked ? "Backend-confirmed producer scope." : "Select from the list or enter a code manually."}
              </div>
            </div>
            <button className="button" disabled={producerSessionLocked} type="submit">
              {producerSessionLocked ? "Loaded from session" : "Load producer"}
            </button>
          </form>
        </div>
      </section>

      {!submitted.tenantCode || !submitted.sponsorCode ? (
        <EmptyState label="Enter a tenant code and producer code to load the producer workspace." />
      ) : loading ? (
        <LoadingState label="Loading producer workspace" />
      ) : error ? (
        <ErrorPanel error={error} />
      ) : (
        <>
          <section className="grid-3">
            <KpiCard
              label="Invoices"
              value={formatDisplay(getNestedValue(dashboard, ["dashboard", "invoice_count"], invoices.length))}
              footnote="Producer invoice records"
              icon={ReceiptText}
            />
            <KpiCard label="Contracts" value={contracts.length} footnote="Funding contract records" icon={Building2} />
            <KpiCard
              label="Outstanding"
              value={outstandingExposureDisplay}
              footnote="Producer billing exposure"
              icon={ChartNoAxesCombined}
            />
          </section>

          <JourneyTracker
            badge={sponsorGuidance.badge}
            currentCopy={sponsorGuidance.copy}
            currentTitle={sponsorGuidance.title}
            steps={sponsorGuidance.steps}
            subtitle="Step-by-step path from producer context through funding, billing, contract cover, and acquisition readiness."
            title="Producer supply journey"
            tone={sponsorGuidance.tone}
          />

          <InsuranceJourneyProofPanel proof={insuranceProof} role="producer" />

          <OutcomeMoneyReviewPanel
            review={outcomeMoneyReview}
            title="Producer outcome money"
          />

          {selectedDraftId ? (
            <section className="panel" id="producer-draft-edit">
              <div className="panel-header">
                <div>
                  <PanelTitle
                    help="Draft opportunities can be refined by the producer before they are published into the demand marketplace."
                    title="Edit draft"
                  />
                  <div className="panel-subtitle">Adjust the distributor-facing offer before publishing.</div>
                </div>
                <StatusBadge label="Draft selected" tone="warning" />
              </div>
              <div className="panel-body">
                <form className="supply-launch-form" onSubmit={saveDraftOpportunity}>
                  <div className="form-row">
                    <div className="field">
                      <FieldLabel help="Distributor-facing opportunity title." htmlFor="draft-title" label="Opportunity title" />
                      <input
                        className="input"
                        id="draft-title"
                        value={draftEditForm.title}
                        onChange={(event) => setDraftEditForm({ ...draftEditForm, title: event.target.value })}
                      />
                    </div>
                    <div className="field">
                      <FieldLabel help="Total budget available to this opportunity." htmlFor="draft-budget" label="Budget" />
                      <input
                        className="input"
                        id="draft-budget"
                        value={draftEditForm.totalBudget}
                        onChange={(event) => setDraftEditForm({ ...draftEditForm, totalBudget: event.target.value })}
                      />
                    </div>
                    <div className="field">
                      <FieldLabel help="Maximum accepted allocations for this opportunity." htmlFor="draft-allocations" label="Max allocations" />
                      <input
                        className="input"
                        id="draft-allocations"
                        value={draftEditForm.maxAllocations}
                        onChange={(event) => setDraftEditForm({ ...draftEditForm, maxAllocations: event.target.value })}
                      />
                    </div>
                  </div>
                  <div className="field">
                    <FieldLabel help="Short description shown to distributors." htmlFor="draft-description" label="Description" />
                    <textarea
                      className="input"
                      id="draft-description"
                      rows={3}
                      value={draftEditForm.description}
                      onChange={(event) => setDraftEditForm({ ...draftEditForm, description: event.target.value })}
                    />
                  </div>
                  <div className="action-button-row">
                    <button className="button" disabled={opportunityActionLoading === `edit:${selectedDraftId}`} type="submit">
                      {opportunityActionLoading === `edit:${selectedDraftId}` ? "Saving" : "Save draft"}
                    </button>
                    <button className="button secondary" type="button" onClick={() => setSelectedDraftId("")}>
                      Cancel
                    </button>
                  </div>
                </form>
              </div>
            </section>
          ) : null}

          <section className="panel" id="producer-supply-launch">
            <div className="panel-header">
              <div>
                <PanelTitle
                  help="Creates a campaign through the campaign API, packages it as a distribution opportunity, and can publish it into the demand marketplace."
                  title="Supply launch"
                />
                <div className="panel-subtitle">
                  Create campaign/outcome, fund it with the selected contract, and publish producer demand.
                </div>
              </div>
              <StatusBadge label={supplyForm.publishNow ? "Create + publish" : "Create draft"} tone="info" />
            </div>
            <div className="panel-body">
              <form className="supply-launch-form" onSubmit={submitSupplyLaunch}>
                <div className="form-row">
                  <div className="field">
                    <FieldLabel help="The human-readable campaign/outcome name." htmlFor="supply-campaign-name" label="Campaign name" />
                    <input
                      className="input"
                      id="supply-campaign-name"
                      value={supplyForm.campaignName}
                      onChange={(event) => setSupplyForm({ ...supplyForm, campaignName: event.target.value })}
                    />
                  </div>
                  <div className="field">
                    <FieldLabel help="Optional campaign code. If left blank, the workspace generates one from the campaign name." htmlFor="supply-campaign-code" label="Campaign code" />
                    <input
                      className="input"
                      id="supply-campaign-code"
                      value={supplyForm.campaignCode}
                      onChange={(event) => setSupplyForm({ ...supplyForm, campaignCode: event.target.value })}
                    />
                  </div>
                  <div className="field">
                    <FieldLabel help="Campaign segment passed to the existing campaign API." htmlFor="supply-segment" label="Segment" />
                    <input
                      className="input"
                      id="supply-segment"
                      value={supplyForm.segment}
                      onChange={(event) => setSupplyForm({ ...supplyForm, segment: event.target.value })}
                    />
                  </div>
                </div>
                <div className="form-row">
                  <div className="field">
                    <FieldLabel help="The marketplace opportunity title distributors will see." htmlFor="supply-opportunity-title" label="Opportunity title" />
                    <input
                      className="input"
                      id="supply-opportunity-title"
                      value={supplyForm.opportunityTitle}
                      onChange={(event) => setSupplyForm({ ...supplyForm, opportunityTitle: event.target.value })}
                    />
                  </div>
                  <div className="field">
                    <FieldLabel help="Product code attached to the opportunity." htmlFor="supply-product-code" label="Product code" />
                    <input
                      className="input"
                      id="supply-product-code"
                      value={supplyForm.productCode}
                      onChange={(event) => setSupplyForm({ ...supplyForm, productCode: event.target.value })}
                    />
                  </div>
                  <div className="field">
                    <FieldLabel help="Product name shown in opportunity and reporting surfaces." htmlFor="supply-product-name" label="Product name" />
                    <input
                      className="input"
                      id="supply-product-name"
                      value={supplyForm.productName}
                      onChange={(event) => setSupplyForm({ ...supplyForm, productName: event.target.value })}
                    />
                  </div>
                </div>
                <div className="field">
                  <FieldLabel help="Short business description of the acquisition outcome." htmlFor="supply-description" label="Description" />
                  <textarea
                    className="input"
                    id="supply-description"
                    rows={3}
                    value={supplyForm.description}
                    onChange={(event) => setSupplyForm({ ...supplyForm, description: event.target.value })}
                  />
                </div>
                <div className="form-row">
                  <div className="field">
                    <FieldLabel help="Comma-separated target segments." htmlFor="supply-target-segments" label="Target segments" />
                    <input
                      className="input"
                      id="supply-target-segments"
                      value={supplyForm.targetSegments}
                      onChange={(event) => setSupplyForm({ ...supplyForm, targetSegments: event.target.value })}
                    />
                  </div>
                  <div className="field">
                    <FieldLabel help="Comma-separated target regions." htmlFor="supply-target-regions" label="Target regions" />
                    <input
                      className="input"
                      id="supply-target-regions"
                      value={supplyForm.targetRegions}
                      onChange={(event) => setSupplyForm({ ...supplyForm, targetRegions: event.target.value })}
                    />
                  </div>
                  <div className="field">
                    <FieldLabel help="Comma-separated channels supported for this opportunity." htmlFor="supply-target-channels" label="Channels" />
                    <input
                      className="input"
                      id="supply-target-channels"
                      value={supplyForm.targetChannels}
                      onChange={(event) => setSupplyForm({ ...supplyForm, targetChannels: event.target.value })}
                    />
                  </div>
                </div>
                <div className="form-row">
                  <div className="field">
                    <FieldLabel help="Comma-separated distributor types eligible for this opportunity." htmlFor="supply-distributor-types" label="Distributor types" />
                    <input
                      className="input"
                      id="supply-distributor-types"
                      value={supplyForm.distributorTypes}
                      onChange={(event) => setSupplyForm({ ...supplyForm, distributorTypes: event.target.value })}
                    />
                  </div>
                  <div className="field">
                    <FieldLabel help="Reward amount available to the customer or journey, where applicable." htmlFor="supply-reward" label="Reward" />
                    <input
                      className="input"
                      id="supply-reward"
                      value={supplyForm.estimatedRewardAmount}
                      onChange={(event) => setSupplyForm({ ...supplyForm, estimatedRewardAmount: event.target.value })}
                    />
                  </div>
                  <div className="field">
                    <FieldLabel help="Distributor commission estimate for this opportunity." htmlFor="supply-commission" label="Commission" />
                    <input
                      className="input"
                      id="supply-commission"
                      value={supplyForm.estimatedCommissionAmount}
                      onChange={(event) => setSupplyForm({ ...supplyForm, estimatedCommissionAmount: event.target.value })}
                    />
                  </div>
                </div>
                <div className="form-row">
                  <div className="field">
                    <FieldLabel help="Total budget attached to the opportunity." htmlFor="supply-budget" label="Budget" />
                    <input
                      className="input"
                      id="supply-budget"
                      value={supplyForm.totalBudget}
                      onChange={(event) => setSupplyForm({ ...supplyForm, totalBudget: event.target.value })}
                    />
                  </div>
                  <div className="field">
                    <FieldLabel help="Maximum accepted allocations for the opportunity." htmlFor="supply-allocations" label="Max allocations" />
                    <input
                      className="input"
                      id="supply-allocations"
                      value={supplyForm.maxAllocations}
                      onChange={(event) => setSupplyForm({ ...supplyForm, maxAllocations: event.target.value })}
                    />
                  </div>
                  <div className="field">
                    <FieldLabel help="Funding contract used as the financial cover for this launch." htmlFor="supply-contract" label="Funding contract" />
                    <select
                      className="input"
                      id="supply-contract"
                      value={selectedContractId}
                      onChange={(event) => setSelectedContractId(event.target.value)}
                    >
                      {contracts.length ? null : <option value="">No contracts returned</option>}
                      {contracts.map((contract) => {
                        const contractId = getValue(contract, ["contract_id", "id"], "");
                        return (
                          <option key={contractId} value={contractId}>
                            {contractLabel(contract)}
                          </option>
                        );
                      })}
                    </select>
                  </div>
                </div>
                <label className="toggle-row">
                  <input
                    checked={supplyForm.publishNow}
                    type="checkbox"
                    onChange={(event) => setSupplyForm({ ...supplyForm, publishNow: event.target.checked })}
                  />
                  <span>Publish to the demand marketplace after creating the opportunity.</span>
                </label>
                <div className="action-button-row">
                  <button className="button" disabled={supplyLoading} type="submit">
                    {supplyLoading ? "Launching" : supplyForm.publishNow ? "Create and publish" : "Create draft"}
                  </button>
                  <span className="muted">Uses the producer supply API backed by campaign and opportunity services.</span>
                </div>
              </form>
              {supplyError ? <ErrorPanel error={supplyError} /> : null}
              {supplyResult ? <SupplyLaunchResult payload={supplyResult} /> : null}
            </div>
          </section>

          <section className="grid-2">
            <div className="panel" id="sponsor-statement">
              <div className="panel-header">
                <div>
                  <PanelTitle
                    help="Shows a producer billing statement for a selected period and currency."
                    title="Statement"
                  />
                  <div className="panel-subtitle">Period-based invoice and payment position.</div>
                </div>
              </div>
              <div className="panel-body">
                <form className="portal-statement-form" onSubmit={loadStatement}>
                  <div className="field">
                    <FieldLabel help="The first date included in the statement." htmlFor="portal-statement-start" label="Start" />
                    <input
                      className="input"
                      id="portal-statement-start"
                      type="date"
                      value={statementPeriodStart}
                      onChange={(event) => setStatementPeriodStart(event.target.value)}
                    />
                  </div>
                  <div className="field">
                    <FieldLabel help="The last date included in the statement." htmlFor="portal-statement-end" label="End" />
                    <input
                      className="input"
                      id="portal-statement-end"
                      type="date"
                      value={statementPeriodEnd}
                      onChange={(event) => setStatementPeriodEnd(event.target.value)}
                    />
                  </div>
                  <div className="field">
                    <FieldLabel help="The currency used for the statement and forecast." htmlFor="portal-currency" label="Currency" />
                    <input
                      className="input"
                      id="portal-currency"
                      value={portalCurrency}
                      onChange={(event) => setPortalCurrency(event.target.value.toUpperCase())}
                    />
                  </div>
                  <button className="button" disabled={statementLoading} type="submit">
                    {statementLoading ? "Loading" : "Load statement"}
                  </button>
                </form>
                {statementError ? <div className="action-result"><ErrorPanel error={statementError} /></div> : null}
                {statementResult ? <StatementSummary payload={statementResult} /> : null}
                <ActionGuardrail
                  badge={statementGuard.badge}
                  tone={statementGuard.tone}
                  title={statementGuard.title}
                  copy={statementGuard.copy}
                  items={statementGuard.items}
                />
              </div>
            </div>

            <div className="panel" id="sponsor-performance">
              <div className="panel-header">
                <div>
                  <PanelTitle
                    help="Forecasts how long producer wallet and contract funding may last at the current burn rate."
                    title="Funding forecast"
                  />
                  <div className="panel-subtitle">Wallet and contract funding risk posture.</div>
                </div>
                <StatusBadge
                  label={String(getNestedValue(forecast, ["forecast", "wallet", "forecast_status"], "-"))}
                  tone={statusTone(String(getNestedValue(forecast, ["forecast", "wallet", "forecast_status"], "-")))}
                />
              </div>
              <div className="panel-body">
                <div className="summary-grid">
                  <SummaryItem label="Wallet days" value={getNestedValue(forecast, ["forecast", "wallet", "days_remaining"], "-")} />
                  <SummaryItem label="Wallet burn" value={getNestedValue(forecast, ["forecast", "wallet", "average_burn_rate_per_day"], "0.00")} />
                  <SummaryItem label="Wallet buffer" value={getNestedValue(forecast, ["forecast", "wallet", "target_buffer"], "0.00")} />
                  <SummaryItem label="Contract days" value={getNestedValue(forecast, ["forecast", "contracts", "days_remaining"], "-")} />
                  <SummaryItem label="Contract burn" value={getNestedValue(forecast, ["forecast", "contracts", "average_burn_rate_per_day"], "0.00")} />
                  <SummaryItem label="Currency" value={portalCurrency} />
                </div>
              </div>
            </div>
          </section>

          <section className="grid-2">
            <div className="panel" id="sponsor-billing">
              <div className="panel-header">
                <div>
                  <PanelTitle help="Invoice, paid, outstanding, and overdue values returned by the billing dashboard." title="Billing position" />
                  <div className="panel-subtitle">Invoice, paid, outstanding, and overdue values.</div>
                </div>
              </div>
              <div className="panel-body">
                <div className="summary-grid">
                  <SummaryItem label="Total" value={formatCurrency(getNestedValue(dashboard, ["dashboard", "totals", "total_amount"], "0.00"), walletCurrency)} />
                  <SummaryItem label="Paid" value={formatCurrency(getNestedValue(dashboard, ["dashboard", "totals", "paid_amount"], "0.00"), walletCurrency)} />
                  <SummaryItem label="Outstanding" value={outstandingExposureDisplay} />
                  <SummaryItem label="Overdue" value={formatCurrency(getNestedValue(dashboard, ["dashboard", "totals", "overdue_outstanding_amount"], "0.00"), walletCurrency)} />
                  <SummaryItem label="Invoice count" value={getNestedValue(dashboard, ["dashboard", "invoice_count"], invoices.length)} />
                  <SummaryItem label="Overdue count" value={getNestedValue(dashboard, ["dashboard", "overdue_count"], 0)} />
                </div>
              </div>
            </div>
            <div className="panel" id="sponsor-funding">
              <div className="panel-header">
                <div>
                  <PanelTitle help="Producer funding wallet used to support marketplace spend." title="Wallet position" />
                  <div className="panel-subtitle">Producer funding wallet and available balance.</div>
                </div>
              </div>
              <div className="panel-body">
                <div className="summary-grid">
                  <SummaryItem label="Currency" value={getWalletValue(wallet, ["currency"])} />
                  <SummaryItem label="Available" value={availableWalletDisplay} />
                  <SummaryItem label="Held" value={formatCurrency(getWalletValue(wallet, ["held_balance", "hold_balance", "reserved_balance"]), walletCurrency)} />
                  <SummaryItem label="Status" value={getWalletValue(wallet, ["status", "wallet_status"])} />
                  <SummaryItem label="Wallet" value={getWalletValue(wallet, ["wallet_id", "id"])} />
                  <SummaryItem label="Producer" value={getWalletValue(wallet, ["sponsor_code", "sponsor_name"])} />
                </div>
              </div>
            </div>
          </section>

          <section className="panel" id="sponsor-wallet-ledger">
            <div className="panel-header">
              <div>
                <PanelTitle
                  help="Ledger entries explain how the producer funding wallet balance moved over time."
                  title="Wallet ledger"
                />
                <div className="panel-subtitle">Recent producer wallet movement from the sponsor wallet ledger.</div>
              </div>
              <StatusBadge label={`${walletLedger.length} movements`} tone={walletLedger.length ? "success" : "neutral"} />
            </div>
            <DataTable
              emptyText="No producer wallet ledger entries returned."
              rows={walletLedger}
              columns={[
                { key: "type", header: "Type", render: (row) => getValue(row, ["transaction_type", "movement_type"]) },
                { key: "amount", header: "Amount", render: (row) => getValue(row, ["amount", "movement_amount"]) },
                { key: "before", header: "Before", render: (row) => getValue(row, ["balance_before"], "-") },
                { key: "after", header: "After", render: (row) => getValue(row, ["balance_after"], "-") },
                { key: "reference", header: "Reference", render: (row) => <span className="mono">{getValue(row, ["correlation_id", "reference", "ledger_id"], "-")}</span> },
                { key: "created", header: "Created", render: (row) => <span className="mono">{getValue(row, ["created_at"], "-")}</span> },
              ]}
            />
          </section>

          <section className="panel" id="sponsor-invoices">
            <div className="panel-header">
              <div>
                <PanelTitle help="Producer-scoped invoice list from the billing API." title="Invoices" />
                <div className="panel-subtitle">Producer-scoped invoice list.</div>
              </div>
            </div>
            <DataTable
              emptyText="No producer invoices returned."
              rows={invoices}
              columns={[
                { key: "invoice", header: "Invoice", render: (row) => <span className="mono">{getValue(row, ["invoice_id", "invoice_number", "id"])}</span> },
                { key: "period", header: "Period", render: (row) => getValue(row, ["period", "billing_period", "period_start"]) },
                { key: "amount", header: "Amount", render: (row) => moneyValue(row, ["total_amount", "amount", "invoice_total"], "0.00") },
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

          <section className="panel" id="sponsor-receipts">
            <div className="panel-header">
              <div>
                <PanelTitle help="Payment receipts recorded against this producer." title="Payment receipts" />
                <div className="panel-subtitle">Producer-scoped payment receipt list.</div>
              </div>
            </div>
            <DataTable
              emptyText="No producer payment receipts returned."
              rows={receipts}
              columns={[
                { key: "receipt", header: "Receipt", render: (row) => <span className="mono">{getValue(row, ["receipt_id", "payment_reference", "id"])}</span> },
                { key: "reference", header: "Reference", render: (row) => getValue(row, ["payment_reference", "external_reference"], "-") },
                { key: "amount", header: "Amount", render: (row) => moneyValue(row, ["payment_amount", "amount", "total_amount"], "0.00") },
                { key: "unapplied", header: "Unapplied", render: (row) => getValue(row, ["unapplied_amount"], "0.00") },
                {
                  key: "status",
                  header: "Status",
                  render: (row) => {
                    const status = getValue(row, ["status", "receipt_status"]);
                    return <StatusBadge label={status} tone={statusTone(status)} />;
                  },
                },
              ]}
            />
          </section>

          <section className="panel" id="sponsor-contracts">
            <div className="panel-header">
              <div>
                <PanelTitle help="Producer-scoped funding contracts used to fund marketplace activity." title="Contracts" />
                <div className="panel-subtitle">Producer-scoped funding contracts.</div>
              </div>
            </div>
            <DataTable
              emptyText="No producer contracts returned."
              rows={contracts}
              columns={[
                { key: "contract", header: "Contract", render: (row) => <span className="mono">{getValue(row, ["contract_id", "id"])}</span> },
                { key: "currency", header: "Currency", render: (row) => getValue(row, ["currency"]) },
                { key: "limit", header: "Limit", render: (row) => getValue(row, ["contract_limit", "limit_amount", "amount"]) },
                {
                  key: "status",
                  header: "Status",
                  render: (row) => {
                    const status = getValue(row, ["status", "contract_status"]);
                    return <StatusBadge label={status} tone={statusTone(status)} />;
                  },
                },
              ]}
            />
          </section>

          <section className="panel" id="sponsor-contract-ledger">
            <div className="panel-header">
              <div>
                <PanelTitle help="Ledger entries explain how a selected funding contract balance has moved." title="Contract ledger" />
                <div className="panel-subtitle">Recent movement history for the selected producer contract.</div>
              </div>
            </div>
            <div className="panel-body">
              <div className="action-select-row">
                <div className="field">
                  <FieldLabel help="The contract whose ledger movements should be shown." htmlFor="portal-contract-ledger" label="Contract" />
                  <select
                    className="input"
                    id="portal-contract-ledger"
                    value={selectedContractId}
                    onChange={(event) => setSelectedContractId(event.target.value)}
                  >
                    {contracts.length ? null : <option value="">No contracts returned</option>}
                    {contracts.map((contract) => {
                      const contractId = getValue(contract, ["contract_id", "id"], "");
                      return (
                        <option key={contractId} value={contractId}>
                          {contractLabel(contract)}
                        </option>
                      );
                    })}
                  </select>
                </div>
              </div>
            </div>
            <DataTable
              emptyText="No contract ledger entries returned."
              rows={contractLedger}
              columns={[
                { key: "type", header: "Type", render: (row) => getValue(row, ["transaction_type", "entry_type", "movement_type"]) },
                { key: "amount", header: "Amount", render: (row) => getValue(row, ["amount", "movement_amount"]) },
                { key: "balance", header: "Balance", render: (row) => moneyValue(row, ["balance_after", "available_balance_after", "remaining_balance"], "0.00") },
                { key: "reference", header: "Reference", render: (row) => <span className="mono">{getValue(row, ["reference", "correlation_id", "ledger_id"], "-")}</span> },
                { key: "created", header: "Created", render: (row) => <span className="mono">{getValue(row, ["created_at"], "-")}</span> },
              ]}
            />
          </section>
        </>
      )}
    </>
  );
}

function OutcomeMoneyReviewPanel({ review, title }: { review: unknown; title: string }) {
  const summary = getNestedValue(review, ["summary"], {});
  const attentionItems = asArray(getNestedValue(review, ["attention_items"], []));
  const guardrails = asArray(getNestedValue(review, ["guardrails"], []));
  const completed = getNestedValue(summary, ["completed_outcome_count"], 0);
  const attention = Number(getNestedValue(summary, ["attention_count"], 0)) || 0;
  const adminReview = Number(getNestedValue(summary, ["admin_review_count"], 0)) || 0;

  return (
    <section className="panel" id="producer-outcome-money">
      <div className="panel-header">
        <div>
          <PanelTitle
            help="Role-scoped outcome-to-money review. Producer users see reward and invoice evidence without Admin repair controls."
            title={title}
          />
          <div className="panel-subtitle">Completed outcomes traced into producer-owned money evidence.</div>
        </div>
        <StatusBadge label={attention ? `${attention} need review` : "Ready"} tone={attention ? "warning" : "success"} />
      </div>
      <div className="panel-body">
        <div className="summary-grid">
          <SummaryItem label="Completed" value={completed} />
          <SummaryItem label="Ready" value={getNestedValue(summary, ["ready_count"], 0)} />
          <SummaryItem label="Producer review" value={attention} />
          <SummaryItem label="Admin follow-up" value={adminReview} />
        </div>
        <div className="route-list">
          {attentionItems.length ? attentionItems.slice(0, 5).map((item) => (
            <div className="route-item" key={formatDisplay(getNestedValue(item, ["referral_track_id"]))}>
              <div>
                <div className="route-name">{formatDisplay(getNestedValue(item, ["opportunity_title"], "Completed outcome"))}</div>
                <div className="route-path">{formatDisplay(getNestedValue(item, ["referral_track_id"]))}</div>
                <div className="route-path">{formatDisplay(getNestedValue(item, ["missing_owned_steps"], []))}</div>
              </div>
              <StatusBadge label={formatDisplay(getNestedValue(item, ["review_status"], "ATTENTION"))} tone="warning" />
            </div>
          )) : <div className="empty-state">No producer-owned money gaps returned.</div>}
        </div>
        {guardrails.length ? (
          <div className="route-list">
            {guardrails.map((item) => (
              <div className="route-item" key={formatDisplay(item)}>
                <div className="route-name">{formatDisplay(item)}</div>
              </div>
            ))}
          </div>
        ) : null}
      </div>
    </section>
  );
}

function ProducerOutcomeCard({
  icon: Icon,
  kicker,
  title,
  copy,
  badge,
  tone,
}: {
  icon: LucideIcon;
  kicker: string;
  title: string;
  copy: string;
  badge: string;
  tone: "success" | "warning" | "danger" | "info" | "neutral";
}) {
  return (
    <div className="producer-outcome-card">
      <div className="producer-outcome-icon">
        <Icon size={20} />
      </div>
      <div>
        <div className="producer-outcome-kicker">{kicker}</div>
        <h2>{title}</h2>
        <p>{copy}</p>
      </div>
      <StatusBadge label={badge} tone={tone} />
    </div>
  );
}

function ExposureRow({
  label,
  value,
  tone,
}: {
  label: string;
  value: unknown;
  tone?: "success" | "warning" | "danger" | "info" | "neutral";
}) {
  return (
    <div className="status-row">
      <span className="status-name">{label}</span>
      <span className={tone === "success" ? "status-count up" : "status-count"}>{formatDisplay(value)}</span>
    </div>
  );
}

function StatementSummary({ payload }: { payload: unknown }) {
  const statement = getNestedValue(payload, ["statement"], {}) as Record<string, unknown>;
  const statementCurrency = currencyFrom(statement);
  return (
    <div className="action-result">
      <SummaryGrid
        items={[
          ["Invoices", getNestedValue(statement, ["invoice_count"], 0)],
          ["Payments", getNestedValue(statement, ["payment_count"], 0)],
          ["Total", formatCurrency(getNestedValue(statement, ["totals", "total_amount"], "0.00"), statementCurrency)],
          ["Paid", formatCurrency(getNestedValue(statement, ["totals", "paid_amount"], "0.00"), statementCurrency)],
          ["Outstanding", formatCurrency(getNestedValue(statement, ["totals", "outstanding_amount"], "0.00"), statementCurrency)],
          ["Received", formatCurrency(getNestedValue(statement, ["totals", "payments_received_amount"], "0.00"), statementCurrency)],
        ]}
      />
    </div>
  );
}

function SupplyLaunchResult({ payload }: { payload: Record<string, unknown> }) {
  const campaignPayload =
    (getNestedValue(payload, ["campaign"], null) as Record<string, unknown> | null) ||
    (getNestedValue(payload, ["campaignPayload"], {}) as Record<string, unknown>);
  const opportunityPayload =
    (getNestedValue(payload, ["opportunity"], null) as Record<string, unknown> | null) ||
    (getNestedValue(payload, ["opportunityPayload"], {}) as Record<string, unknown>);
  const mode = getValue(payload, ["mode"], getValue(opportunityPayload, ["opportunity_status", "status"], "draft"));

  return (
    <div className="action-result">
      <SummaryGrid
        items={[
          ["Campaign", getValue(campaignPayload, ["campaignCode", "campaign_code"], getValue(payload, ["resolvedCampaignCode"], "-"))],
          ["Opportunity", getValue(opportunityPayload, ["opportunity_id", "id"], "-")],
          ["Status", getValue(opportunityPayload, ["opportunity_status", "status"], "-")],
          ["Mode", mode],
        ]}
      />
    </div>
  );
}

function OpportunityActionResult({ payload }: { payload: Record<string, unknown> }) {
  return (
    <div className="action-result">
      <SummaryGrid
        items={[
          ["Opportunity", getValue(payload, ["opportunity_code", "opportunity_id"], "-")],
          ["Status", getValue(payload, ["opportunity_status", "status"], "-")],
          ["Budget", getValue(payload, ["total_budget"], "-")],
          ["Remaining", getValue(payload, ["remaining_allocations"], "-")],
        ]}
      />
    </div>
  );
}

function OpportunityActions({
  opportunity,
  loadingKey,
  onEdit,
  onPublish,
  onClose,
  onReopen,
}: {
  opportunity: Record<string, unknown>;
  loadingKey: string | null;
  onEdit: (opportunity: Record<string, unknown>) => void;
  onPublish: (action: "publish", opportunity: Record<string, unknown>) => void;
  onClose: (action: "close", opportunity: Record<string, unknown>) => void;
  onReopen: (action: "reopen", opportunity: Record<string, unknown>) => void;
}) {
  const opportunityId = getValue(opportunity, ["opportunity_id", "id"], "");
  const status = getValue(opportunity, ["opportunity_status", "status"], "").toUpperCase();
  const isBusy = Boolean(loadingKey && loadingKey.endsWith(`:${opportunityId}`));

  return (
    <div className="action-button-row">
      {status === "DRAFT" ? (
        <>
          <button className="button secondary" disabled={isBusy} type="button" onClick={() => onEdit(opportunity)}>
            Edit
          </button>
          <button className="button" disabled={isBusy} type="button" onClick={() => onPublish("publish", opportunity)}>
            {loadingKey === `publish:${opportunityId}` ? "Publishing" : "Publish"}
          </button>
        </>
      ) : null}
      {status === "PUBLISHED" ? (
        <button className="button secondary" disabled={isBusy} type="button" onClick={() => onClose("close", opportunity)}>
          {loadingKey === `close:${opportunityId}` ? "Closing" : "Close"}
        </button>
      ) : null}
      {status === "CLOSED" ? (
        <button className="button secondary" disabled={isBusy} type="button" onClick={() => onReopen("reopen", opportunity)}>
          {loadingKey === `reopen:${opportunityId}` ? "Reopening" : "Reopen"}
        </button>
      ) : null}
      {["DRAFT", "PUBLISHED", "CLOSED"].includes(status) ? null : <span className="muted">No action</span>}
    </div>
  );
}

function contractLabel(contract: Record<string, unknown>): string {
  return `${getValue(contract, ["contract_id", "id"])} | ${getValue(contract, ["currency"], "-")} | ${getValue(
    contract,
    ["status", "contract_status"],
    "-",
  )}`;
}

function getWalletValue(wallet: unknown, keys: string[]): unknown {
  const nestedWallet = getNestedValue(wallet, ["wallet"], {});
  if (nestedWallet && typeof nestedWallet === "object") {
    for (const key of keys) {
      const value = (nestedWallet as Record<string, unknown>)[key];
      if (value !== undefined && value !== null && value !== "") {
        return value;
      }
    }
  }

  const direct = wallet && typeof wallet === "object" ? (wallet as Record<string, unknown>) : {};
  for (const key of keys) {
    if (direct[key] !== undefined && direct[key] !== null && direct[key] !== "") {
      return direct[key];
    }
  }

  return "-";
}

function csvList(value: string): string[] | undefined {
  const items = value
    .split(",")
    .map((item) => item.trim().toUpperCase())
    .filter(Boolean);
  return items.length ? items : undefined;
}

function numberOrUndefined(value: string): number | undefined {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : undefined;
}

function upsertOpportunity(
  opportunities: Record<string, unknown>[],
  opportunity: Record<string, unknown>,
): Record<string, unknown>[] {
  const opportunityId = getValue(opportunity, ["opportunity_id", "id"], "");
  if (!opportunityId) {
    return opportunities;
  }

  const exists = opportunities.some((current) => getValue(current, ["opportunity_id", "id"], "") === opportunityId);
  if (!exists) {
    return [opportunity, ...opportunities];
  }

  return opportunities.map((current) =>
    getValue(current, ["opportunity_id", "id"], "") === opportunityId ? opportunity : current,
  );
}

function findOpportunityPerformance(
  performanceRows: Record<string, unknown>[],
  opportunity: Record<string, unknown>,
): Record<string, unknown> {
  const opportunityId = getValue(opportunity, ["opportunity_id", "id"], "");
  const opportunityCode = getValue(opportunity, ["opportunity_code"], "");
  return (
    performanceRows.find((row) => {
      return (
        getValue(row, ["opportunity_id", "id"], "") === opportunityId ||
        getValue(row, ["opportunity_code"], "") === opportunityCode
      );
    }) || {}
  );
}

function OpportunityReadiness({
  opportunity,
  performance,
}: {
  opportunity: Record<string, unknown>;
  performance: Record<string, unknown>;
}) {
  const readiness = getOpportunityReadiness(opportunity, performance);
  return (
    <div>
      <StatusBadge label={readiness.label} tone={readiness.tone} />
      <div className="table-subtext">{readiness.nextStep}</div>
    </div>
  );
}

function getOpportunityReadiness(
  opportunity: Record<string, unknown>,
  performance: Record<string, unknown>,
): { label: string; tone: BadgeTone; nextStep: string } {
  const status = getValue(opportunity, ["opportunity_status", "status"], "").toUpperCase();
  const routedCount = numberValue(getValue(performance, ["routed_count"], "0"));
  const acceptedCount = numberValue(getValue(performance, ["accepted_count"], "0"));
  const conversionCount = numberValue(getValue(performance, ["conversion_count"], "0"));
  const completedCount = numberValue(getValue(performance, ["completed_conversion_count"], "0"));

  if (status === "DRAFT") {
    return {
      label: "Draft",
      tone: "warning",
      nextStep: "Review and publish to demand",
    };
  }

  if (status === "CLOSED") {
    return {
      label: completedCount > 0 ? "Closed with outcomes" : "Closed",
      tone: completedCount > 0 ? "success" : "neutral",
      nextStep: completedCount > 0 ? "Review ROI and settlement" : "Reopen if demand should resume",
    };
  }

  if (completedCount > 0) {
    return {
      label: "Outcomes complete",
      tone: "success",
      nextStep: "Review ROI, funding, and settlement",
    };
  }

  if (conversionCount > 0) {
    return {
      label: "Converting",
      tone: "info",
      nextStep: "Monitor customer milestones",
    };
  }

  if (acceptedCount > 0) {
    return {
      label: "Accepted demand",
      tone: "success",
      nextStep: "Wait for linked customer journeys",
    };
  }

  if (routedCount > 0) {
    return {
      label: "Routed",
      tone: "info",
      nextStep: "Wait for distributor acceptance",
    };
  }

  if (status === "PUBLISHED") {
    return {
      label: "Live",
      tone: "info",
      nextStep: "Await route matching",
    };
  }

  return {
    label: status || "Unknown",
    tone: "neutral",
    nextStep: "Review opportunity setup",
  };
}

function producerConversionNextStep(row: Record<string, unknown>): string {
  const explicit = getValue(row, ["next_milestone"], "");
  if (explicit) {
    return explicit;
  }

  if (Boolean(row.is_complete)) {
    return "Review reward and settlement";
  }

  const status = getValue(row, ["status", "display_status"], "").toUpperCase();
  if (status.includes("VALIDATED") || status.includes("UCN")) {
    return "Open account";
  }
  if (status.includes("OPEN")) {
    return "Activate account";
  }
  if (status.includes("ACTIVATED") || status.includes("FUNDED")) {
    return "Complete funded outcome";
  }

  return "Monitor customer progress";
}

function buildProducerCode(value: string): string {
  const slug = value
    .toUpperCase()
    .replace(/[^A-Z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 40);
  return `${slug || "CAMPAIGN"}-${Date.now().toString().slice(-6)}`;
}

type BadgeTone = GuardrailTone;

type Guardrail = {
  badge: string;
  tone: BadgeTone;
  title: string;
  copy: string;
  items: GuardrailItem[];
};

function getStatementGuardrail({
  statementPeriodStart,
  statementPeriodEnd,
  portalCurrency,
  statementLoading,
}: {
  statementPeriodStart: string;
  statementPeriodEnd: string;
  portalCurrency: string;
  statementLoading: boolean;
}): Guardrail {
  const hasDates = Boolean(statementPeriodStart && statementPeriodEnd);
  const validRange = hasDates && statementPeriodStart <= statementPeriodEnd;
  if (statementLoading) {
    return {
      badge: "Loading",
      tone: "info",
      title: "Statement is loading",
      copy: "Wait for the statement response before changing the period or currency.",
      items: [
        { label: "Period", value: `${statementPeriodStart || "-"} to ${statementPeriodEnd || "-"}`, tone: validRange ? "success" : "warning" },
        { label: "Currency", value: portalCurrency || "Required", tone: portalCurrency ? "success" : "warning" },
        { label: "System change", value: "None", tone: "success" },
      ],
    };
  }

  return {
    badge: validRange && portalCurrency ? "Read only" : "Check inputs",
    tone: validRange && portalCurrency ? "success" : "warning",
    title: validRange && portalCurrency ? "Statement load is safe" : "Confirm statement inputs",
    copy: "Loading a statement reviews producer invoices and payments for the selected period. It does not issue invoices or record payments.",
    items: [
      { label: "Period", value: `${statementPeriodStart || "-"} to ${statementPeriodEnd || "-"}`, tone: validRange ? "success" : "warning" },
      { label: "Currency", value: portalCurrency || "Required", tone: portalCurrency ? "success" : "warning" },
      { label: "System change", value: "None", tone: "success" },
    ],
  };
}

function getSponsorGuidance({
  hasSponsor,
  dashboard,
  wallet,
  invoices,
  contracts,
  receipts,
  forecast,
  opportunities,
}: {
  hasSponsor: boolean;
  dashboard: unknown;
  wallet: unknown;
  invoices: Record<string, unknown>[];
  contracts: Record<string, unknown>[];
  receipts: Record<string, unknown>[];
  forecast: unknown;
  opportunities: Record<string, unknown>[];
}): {
  badge: string;
  tone: BadgeTone;
  title: string;
  copy: string;
  steps: JourneyStep[];
} {
  const walletStatus = String(getWalletValue(wallet, ["status", "wallet_status"]));
  const availableBalance = numberValue(getWalletValue(wallet, ["available_balance", "balance", "current_balance"]));
  const outstandingAmount = numberValue(getNestedValue(dashboard, ["dashboard", "totals", "outstanding_amount"], "0"));
  const overdueAmount = numberValue(getNestedValue(dashboard, ["dashboard", "totals", "overdue_outstanding_amount"], "0"));
  const forecastStatus = String(getNestedValue(forecast, ["forecast", "wallet", "forecast_status"], "-"));
  const hasFunding = walletStatus === "ACTIVE" && availableBalance > 0;
  const hasInvoiceExposure = outstandingAmount > 0 || overdueAmount > 0;
  const hasForecastWarning = ["LOW", "WARNING", "CRITICAL", "AT_RISK"].includes(forecastStatus.toUpperCase());

  if (!hasSponsor) {
    return {
      badge: "Load",
      tone: "info",
      title: "Load producer",
      copy: "Enter the tenant and producer code to see funding, billing, and performance information.",
      steps: sponsorSteps("current", "waiting", "waiting", "waiting", "waiting"),
    };
  }

  if (!hasFunding) {
    return {
      badge: "Funding",
      tone: walletStatus === "-" ? "neutral" : "warning",
      title: "Confirm producer funding",
      copy: "The producer workspace is loaded, but funding needs attention before downstream distribution activity can scale safely.",
      steps: sponsorSteps("done", "current", "waiting", contracts.length ? "done" : "waiting", "waiting"),
    };
  }

  if (hasInvoiceExposure) {
    return {
      badge: overdueAmount > 0 ? "Overdue" : "Billing",
      tone: overdueAmount > 0 ? "warning" : "info",
      title: overdueAmount > 0 ? "Review overdue billing" : "Review outstanding invoices",
      copy: "There is producer billing exposure to review. Use invoices, receipts, and statements to understand what remains payable.",
      steps: sponsorSteps("done", "done", "current", contracts.length ? "done" : "waiting", "waiting"),
    };
  }

  if (!contracts.length) {
    return {
      badge: "Contracts",
      tone: "info",
      title: "Review funding contracts",
      copy: "Funding is visible, but no producer contracts were returned. Confirm the contract setup before relying on long-running reward spend.",
      steps: sponsorSteps("done", "done", invoices.length ? "done" : "waiting", "current", "waiting"),
    };
  }

  if (hasForecastWarning) {
    return {
      badge: "Forecast",
      tone: "warning",
      title: "Review funding forecast",
      copy: "The forecast is signalling funding risk. Check burn rate, wallet buffer, and contract cover before new demand is expanded.",
      steps: sponsorSteps("done", "done", invoices.length ? "done" : "done", "current", "current"),
    };
  }

  if (!opportunities.length) {
    return {
      badge: "Supply",
      tone: "info",
      title: "Create producer supply",
      copy: "Funding and contracts are visible. Create a supply launch or publish an existing draft so distributors can see demand.",
      steps: sponsorSteps("done", "done", invoices.length ? "done" : "waiting", "done", "current"),
    };
  }

  return {
    badge: "Stable",
    tone: "success",
    title: "Producer position is healthy",
    copy: receipts.length
      ? "Funding, contracts, receipts, and billing are visible. Keep monitoring statements and forecast movement."
      : "Funding and contracts are visible. Monitor invoices, receipts, statements, and forecast movement as activity grows.",
    steps: sponsorSteps("done", "done", invoices.length ? "done" : "waiting", "done", "current"),
  };
}

function sponsorSteps(
  identity: JourneyStep["state"],
  funding: JourneyStep["state"],
  billing: JourneyStep["state"],
  contracts: JourneyStep["state"],
  performance: JourneyStep["state"],
): JourneyStep[] {
  return [
    {
      label: "Load producer",
      description: "Choose the tenant and producer funding context for the workspace.",
      workArea: "Producer identity",
      targetId: "sponsor-identity",
      state: identity,
    },
    {
      label: "Confirm funding",
      description: "Check wallet status, available balance, and funding buffer.",
      workArea: "Wallet position and funding forecast",
      targetId: "sponsor-funding",
      state: funding,
    },
    {
      label: "Review billing",
      description: "Review invoices, receipts, outstanding values, and statements.",
      workArea: "Billing position, invoices, receipts, and statement",
      targetId: "sponsor-billing",
      state: billing,
    },
    {
      label: "Check contracts",
      description: "Confirm producer funding contracts and contract ledger movement.",
      workArea: "Contracts and contract ledger",
      targetId: "sponsor-contracts",
      state: contracts,
    },
    {
      label: "Monitor performance",
      description: "Use forecast and billing movement to watch producer health over time.",
      workArea: "Funding forecast and portal KPIs",
      targetId: "sponsor-performance",
      state: performance,
    },
  ];
}

function numberValue(value: unknown): number {
  const parsed = Number(String(value ?? "0").replace(/[^0-9.-]/g, ""));
  return Number.isFinite(parsed) ? parsed : 0;
}
