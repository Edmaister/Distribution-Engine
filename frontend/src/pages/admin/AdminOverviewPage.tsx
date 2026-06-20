import {
  Activity,
  AlertTriangle,
  Bot,
  Building2,
  CheckCircle2,
  DatabaseZap,
  GitBranch,
  KeyRound,
  Landmark,
  Route,
  Send,
  ShieldCheck,
  Trophy,
  Users,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";
import { getAdminCommandCentreExperience } from "../../api/endpoints/adminExperience";
import {
  createOutcomeCommissionEvidence,
  createOutcomeInvoiceEvidence,
  createOutcomeRewardEvidence,
  createOutcomeSettlementEvidence,
  createOutcomeWalletEvidence,
  resolveOutcomeSettlementExceptions,
} from "../../api/endpoints/finance";
import {
  getAdminPartnerWebhookAlerts,
  getPartnerClients,
  getPartnerWebhookDeliveries,
  getPartnerWebhookSummary,
  notifyPartnerWebhookAlerts,
  processPartnerWebhookDeliveries,
} from "../../api/endpoints/partnerSeam";
import { getVerticalReadiness } from "../../api/endpoints/verticals";
import { queryKeys } from "../../api/queryKeys";
import { EmptyState } from "../../components/EmptyState";
import { ErrorPanel } from "../../components/ErrorPanel";
import { KpiCard } from "../../components/KpiCard";
import { LoadingState } from "../../components/LoadingState";
import { StatusBadge } from "../../components/StatusBadge";
import { SummaryItem } from "../../components/SummaryItem";
import {
  asArray,
  countFrom,
  formatDisplay,
  getNestedValue,
  objectEntries,
  statusTone,
  useRefreshContext,
} from "../pageUtils";

type OverviewState = {
  health: unknown;
  readiness: unknown;
  audit: unknown;
  events: unknown;
  finance: unknown;
  verticals: unknown;
  partnerSeam: unknown;
  partnerDeliveries: unknown;
  partnerDeliverySummary: unknown;
  partnerAlerts: unknown;
};

type Capability = {
  name: string;
  copy: string;
  path: string;
  badge: string;
  tone: "success" | "warning" | "danger" | "info" | "neutral";
  icon: typeof Activity;
};

type RoleGateway = {
  role: string;
  side: string;
  headline: string;
  copy: string;
  path: string;
  action: string;
  tone: "success" | "warning" | "danger" | "info" | "neutral";
  icon: typeof Activity;
  outcomes: string[];
  links: Array<{ label: string; path: string }>;
};

type AdminRail = {
  title: string;
  copy: string;
  path: string;
  icon: typeof Activity;
  badge: string;
};

const DEFAULT_TENANT_CODE = "FNB";

const roleGateways: RoleGateway[] = [
  {
    role: "Distributor",
    side: "Demand",
    headline: "I want to distribute and earn.",
    copy: "For individuals, influencers, communities, retailers, and advocates that create demand and get paid for qualified activation.",
    path: "/distributor",
    action: "Open Earnings Hub",
    tone: "success",
    icon: Users,
    outcomes: ["Find opportunities", "Convert customers", "Track earnings", "Build trust and rank"],
    links: [
      { label: "Customer Journey", path: "/consumer" },
      { label: "Marketplace Ops", path: "/admin/distribution" },
    ],
  },
  {
    role: "Producer",
    side: "Supply",
    headline: "I want customers and distribution.",
    copy: "For banks, retailers, telcos, insurers, and brands that publish offers, fund rewards, and buy acquisition outcomes.",
    path: "/sponsor",
    action: "Open Producer Workspace",
    tone: "success",
    icon: Building2,
    outcomes: ["Publish offers", "Fund rewards", "Manage contracts", "Measure acquisition ROI"],
    links: [
      { label: "Funding Spine", path: "/admin/billing" },
      { label: "Treasury Rail", path: "/admin/multi-currency" },
    ],
  },
  {
    role: "Amplifi Admin",
    side: "Platform",
    headline: "I operate the network.",
    copy: "For the platform team governing tenants, events, trust, settlement, reconciliation, readiness, and financial rails.",
    path: "/admin",
    action: "Open Command Centre",
    tone: "info",
    icon: ShieldCheck,
    outcomes: ["Monitor network health", "Govern trust", "Replay events", "Control settlement risk"],
    links: [
      { label: "Event Fabric", path: "/admin/events" },
      { label: "Settlement Rail", path: "/admin/settlements" },
    ],
  },
];

const capabilities: Capability[] = [
  {
    name: "Demand Marketplace",
    copy: "Where demand routes are matched to distributors through opportunities, routing, eligibility, wallets, and governance.",
    path: "/admin/distribution",
    badge: "Demand ops",
    tone: "success",
    icon: Route,
  },
  {
    name: "Customer Journey",
    copy: "The demand conversion path: discover, join, establish, activate, then become an advocate.",
    path: "/consumer",
    badge: "Convert",
    tone: "success",
    icon: Trophy,
  },
  {
    name: "Funding Spine",
    copy: "Producer billing, invoices, contracts, receipts, statements, and reward funding controls.",
    path: "/admin/billing",
    badge: "Supply rail",
    tone: "success",
    icon: Landmark,
  },
  {
    name: "Settlement Rail",
    copy: "Producer funding, distributor earnings, provider exposure, approval, reconciliation, and payout controls.",
    path: "/admin/settlements",
    badge: "Rail",
    tone: "success",
    icon: Landmark,
  },
  {
    name: "AI Distribution Copilot",
    copy: "The future optimisation layer for forecasts, funding recommendations, and next-best distribution actions.",
    path: "/admin",
    badge: "Layer 07",
    tone: "info",
    icon: Bot,
  },
  {
    name: "Platform Operations",
    copy: "Event fabric, funding spine, treasury rail, runtime health, audit, and operational controls.",
    path: "/admin/events",
    badge: "Ops",
    tone: "info",
    icon: GitBranch,
  },
];

const adminRails: AdminRail[] = [
  {
    title: "Event Fabric",
    copy: "Monitor source events, exception states, and replay checks.",
    path: "/admin/events",
    icon: GitBranch,
    badge: "Operate",
  },
  {
    title: "Settlement Rail",
    copy: "Control batches, approvals, provider exposure, and execution.",
    path: "/admin/settlements",
    icon: Landmark,
    badge: "Settle",
  },
  {
    title: "Trust & Audit",
    copy: "Review sensitive action history and operator accountability.",
    path: "/admin/audit",
    icon: ShieldCheck,
    badge: "Govern",
  },
  {
    title: "Runtime Health",
    copy: "Check database, schema groups, messaging, and dependency readiness.",
    path: "/admin/health",
    icon: Activity,
    badge: "Assure",
  },
];

async function loadAdminOverviewData(): Promise<OverviewState> {
  const [
    adminExperience,
    verticals,
    partnerSeam,
    partnerDeliveries,
    partnerDeliverySummary,
    partnerAlerts,
  ] = await Promise.all([
    getAdminCommandCentreExperience(DEFAULT_TENANT_CODE, 25),
    getVerticalReadiness(),
    getPartnerClients(),
    getPartnerWebhookDeliveries(),
    getPartnerWebhookSummary(),
    getAdminPartnerWebhookAlerts(),
  ]);

  const runtime = adminExperience.sections.runtime?.data ?? {};

  return {
    health: runtime,
    readiness: runtime,
    audit: adminExperience.sections.audit?.data ?? {},
    events: adminExperience.sections.events?.data ?? {},
    finance: adminExperience.sections.finance?.data ?? {},
    verticals,
    partnerSeam,
    partnerDeliveries,
    partnerDeliverySummary,
    partnerAlerts,
  };
}

export function AdminOverviewPage() {
  const { refreshKey } = useRefreshContext();
  const {
    data,
    error,
    isLoading: loading,
    refetch,
  } = useQuery({
    queryKey: [...queryKeys.adminExperience(DEFAULT_TENANT_CODE, 25), "overview", refreshKey],
    queryFn: loadAdminOverviewData,
  });
  const [actionPageError, setActionPageError] = useState<unknown>(null);
  const [repairingReferralId, setRepairingReferralId] = useState<string | null>(null);
  const [repairMessage, setRepairMessage] = useState<string | null>(null);
  const [processingWebhooks, setProcessingWebhooks] = useState(false);
  const [notifyingPartnerAlerts, setNotifyingPartnerAlerts] = useState(false);
  const [partnerWebhookMessage, setPartnerWebhookMessage] = useState<string | null>(null);

  if (loading) {
    return <LoadingState label="Loading control centre" />;
  }

  if (error || actionPageError) {
    return <ErrorPanel error={error || actionPageError} />;
  }

  const auditTotal = countFrom(data?.audit, ["total", "total_count", "audit_count"]);
  const eventTotal = countFrom(data?.events, ["total", "total_count", "event_count"]);
  const schemaGroups = objectEntries(getNestedValue(data?.readiness, ["components", "schema", "groups"], {}));
  const missingSchemaGroups = schemaGroups.filter(([, group]) => formatDisplay(group.ok) !== "Yes").length;
  const dbReady = formatDisplay(getNestedValue(data?.health, ["components", "db", "ok"], false)) === "Yes";
  const schemaReady = formatDisplay(getNestedValue(data?.health, ["components", "schema", "ok"], false)) === "Yes";
  const runtimeReady = dbReady && schemaReady;
  const outcomeMoney = getNestedValue(data?.finance, ["outcome_money"], {});
  const outcomeSummary = getNestedValue(outcomeMoney, ["summary"], {});
  const outcomeJourney = asArray(getNestedValue(outcomeMoney, ["journey"], []));
  const outcomeItems = asArray(getNestedValue(outcomeMoney, ["items"], []));
  const attentionOutcomes = outcomeItems.filter((item) => formatDisplay(item.money_status) === "ATTENTION").slice(0, 5);
  const outcomeAttentionBreakdown = asArray(getNestedValue(outcomeSummary, ["attention_breakdown"], []));
  const completedMoneyOutcomes = countFrom(outcomeSummary, ["completed_outcome_count"]);
  const readyMoneyOutcomes = countFrom(outcomeSummary, ["ready_count"]);
  const attentionMoneyOutcomes = countFrom(outcomeSummary, ["attention_count"]);
  const exceptionMoneyOutcomes = countFrom(outcomeSummary, ["exception_count"]);
  const moneyCompletionRate = formatPercent(getNestedValue(outcomeSummary, ["money_completion_rate"], 0));
  const verticalReadiness = getNestedValue(data?.verticals, ["readiness"], {});
  const verticalItems = asArray(getNestedValue(verticalReadiness, ["items"], []));
  const insuranceProof = getNestedValue(data?.verticals, ["proof", "insurance"], {});
  const insuranceProofSteps = asArray(getNestedValue(insuranceProof, ["steps"], []));
  const insuranceProofReady = formatDisplay(getNestedValue(insuranceProof, ["ready"], false)) === "Yes";
  const configuredVerticals = countFrom(verticalReadiness, ["configured_count"]);
  const verticalCount = countFrom(verticalReadiness, ["vertical_count"]);
  const agnosticReady = formatDisplay(getNestedValue(verticalReadiness, ["agnostic_ready"], false)) === "Yes";
  const partnerSeamAvailable = formatDisplay(getNestedValue(data?.partnerSeam, ["available"], true)) !== "No";
  const partnerClientCount = countFrom(data?.partnerSeam, ["count"]);
  const partnerClients = asArray(getNestedValue(data?.partnerSeam, ["items"], []));
  const partnerDeliveriesAvailable = formatDisplay(getNestedValue(data?.partnerDeliveries, ["available"], true)) !== "No";
  const partnerSummaryAvailable = formatDisplay(getNestedValue(data?.partnerDeliverySummary, ["available"], true)) !== "No";
  const partnerAlertsAvailable = formatDisplay(getNestedValue(data?.partnerAlerts, ["available"], true)) !== "No";
  const partnerSummary = getNestedValue(data?.partnerDeliverySummary, ["summary"], {});
  const partnerDeliveries = asArray(getNestedValue(data?.partnerDeliveries, ["items"], []));
  const partnerAlerts = asArray(getNestedValue(data?.partnerAlerts, ["items"], []));
  const partnerFailedDeliveries = partnerDeliveries.filter((item) => formatDisplay(getNestedValue(item, ["delivery_status"])) === "FAILED");
  const partnerDeliveryStatus = formatDisplay(getNestedValue(partnerSummary, ["status"], "HEALTHY"));
  const partnerSentCount = countFrom(partnerSummary, ["sent_count"]);
  const partnerPendingCount = countFrom(partnerSummary, ["pending_count"]);
  const partnerFailedCount = countFrom(partnerSummary, ["failed_count"]);
  const partnerSeamMessage = formatDisplay(
    getNestedValue(data?.partnerSeam, ["message"], "Client credentials and webhook delivery queue are available."),
  );
  const partnerDeliveryMessage = formatDisplay(
    getNestedValue(data?.partnerDeliveries, ["message"], "Webhook delivery worker can process due delivery records."),
  );
  const attentionItems = [
    {
      label: "Runtime readiness",
      value: runtimeReady ? "Healthy" : "Review",
      tone: runtimeReady ? "success" : "warning",
      path: "/admin/health",
      copy: runtimeReady ? "Core platform dependencies are responding." : "Open runtime health to inspect dependency status.",
    },
    {
      label: "Schema groups",
      value: missingSchemaGroups === 0 ? "Ready" : `${missingSchemaGroups} missing`,
      tone: missingSchemaGroups === 0 ? "success" : "warning",
      path: "/admin/health",
      copy: "Confirms the database groups needed by demand, supply, treasury, audit, and settlements.",
    },
    {
      label: "Event fabric",
      value: `${eventTotal} events`,
      tone: eventTotal > 0 ? "info" : "neutral",
      path: "/admin/events",
      copy: "Watch Hogan and enterprise events that drive activation and switching signals.",
    },
    {
      label: "Outcome money",
      value:
        completedMoneyOutcomes === 0
          ? "No outcomes"
          : `${readyMoneyOutcomes}/${completedMoneyOutcomes} ready`,
      tone:
        exceptionMoneyOutcomes > 0 || attentionMoneyOutcomes > 0
          ? "warning"
          : completedMoneyOutcomes > 0
            ? "success"
            : "neutral",
      path: "/admin/billing",
      copy: "Shows completed outcomes moving through rewards, commission, wallets, invoices, and settlement.",
    },
    {
      label: "Vertical readiness",
      value: verticalCount === 0 ? "No verticals" : `${configuredVerticals}/${verticalCount} configured`,
      tone: agnosticReady ? "success" : "warning",
      path: "/admin",
      copy: agnosticReady
        ? `${configuredVerticals} vertical journeys are configured as platform definitions.`
        : "Second-vertical proof still needs configuration coverage.",
    },
    {
      label: "Trust trail",
      value: `${auditTotal} records`,
      tone: auditTotal > 0 ? "info" : "neutral",
      path: "/admin/audit",
      copy: "Review sensitive operator actions across the platform rails.",
    },
  ] as const;

  async function resolveOutcomeException(referralTrackId: string) {
    setRepairingReferralId(referralTrackId);
    setRepairMessage(null);
    try {
      const result = await resolveOutcomeSettlementExceptions(referralTrackId, "admin-operator", DEFAULT_TENANT_CODE);
      const resolvedCount = countFrom(getNestedValue(result, ["repair"], {}), ["resolved_count"]);
      await refetch();
      setRepairMessage(
        resolvedCount > 0
          ? `${resolvedCount} settlement exception resolved.`
          : "No open settlement exceptions were found for that outcome.",
      );
    } catch (requestError) {
      setActionPageError(requestError);
    } finally {
      setRepairingReferralId(null);
    }
  }

  async function processWebhookQueue() {
    setProcessingWebhooks(true);
    setPartnerWebhookMessage(null);
    try {
      const result = await processPartnerWebhookDeliveries(25);
      setPartnerWebhookMessage(
        `Processed ${formatDisplay(result.processed_count)} deliveries: ${formatDisplay(result.sent_count)} sent, ${formatDisplay(result.pending_count)} pending, ${formatDisplay(result.failed_count)} failed.`,
      );
      const [clients, deliveries, deliverySummary, alerts] = await Promise.all([
        getPartnerClients(),
        getPartnerWebhookDeliveries(),
        getPartnerWebhookSummary(),
        getAdminPartnerWebhookAlerts(),
      ]);
      await refetch();
      void clients;
      void deliveries;
      void deliverySummary;
      void alerts;
    } catch (requestError) {
      setPartnerWebhookMessage(requestError && typeof requestError === "object" && "message" in requestError ? String(requestError.message) : "Webhook delivery processing failed.");
    } finally {
      setProcessingWebhooks(false);
    }
  }

  async function notifyWebhookAlerts() {
    setNotifyingPartnerAlerts(true);
    setPartnerWebhookMessage(null);
    try {
      const result = await notifyPartnerWebhookAlerts(25);
      setPartnerWebhookMessage(
        `${formatDisplay(result.notified_count)} partner alert notifications recorded.`,
      );
      const [deliveries, deliverySummary, alerts] = await Promise.all([
        getPartnerWebhookDeliveries(),
        getPartnerWebhookSummary(),
        getAdminPartnerWebhookAlerts(),
      ]);
      await refetch();
      void deliveries;
      void deliverySummary;
      void alerts;
    } catch (requestError) {
      setPartnerWebhookMessage(requestError && typeof requestError === "object" && "message" in requestError ? String(requestError.message) : "Partner alert notification failed.");
    } finally {
      setNotifyingPartnerAlerts(false);
    }
  }

  async function createRewardEvidence(referralTrackId: string) {
    setRepairingReferralId(referralTrackId);
    setRepairMessage(null);
    try {
      const result = await createOutcomeRewardEvidence(referralTrackId, "admin-operator", DEFAULT_TENANT_CODE);
      const rewardCount = countFrom(getNestedValue(result, ["repair"], {}), ["reward_count"]);
      await refetch();
      setRepairMessage(
        rewardCount > 0
          ? `${rewardCount} reward evidence item created.`
          : "No missing reward evidence was found for that outcome.",
      );
    } catch (requestError) {
      setActionPageError(requestError);
    } finally {
      setRepairingReferralId(null);
    }
  }

  async function createCommissionEvidence(referralTrackId: string) {
    setRepairingReferralId(referralTrackId);
    setRepairMessage(null);
    try {
      const result = await createOutcomeCommissionEvidence(referralTrackId, "admin-operator", DEFAULT_TENANT_CODE);
      const commissionCount = countFrom(getNestedValue(result, ["repair"], {}), ["commission_count"]);
      await refetch();
      setRepairMessage(
        commissionCount > 0
          ? `${commissionCount} commission evidence item created.`
          : "No missing commission evidence was found for that outcome.",
      );
    } catch (requestError) {
      setActionPageError(requestError);
    } finally {
      setRepairingReferralId(null);
    }
  }

  async function createWalletEvidence(referralTrackId: string) {
    setRepairingReferralId(referralTrackId);
    setRepairMessage(null);
    try {
      const result = await createOutcomeWalletEvidence(referralTrackId, "admin-operator", DEFAULT_TENANT_CODE);
      const walletMovementCount = countFrom(getNestedValue(result, ["repair"], {}), ["wallet_movement_count"]);
      await refetch();
      setRepairMessage(
        walletMovementCount > 0
          ? `${walletMovementCount} distributor wallet movement created.`
          : "No missing distributor wallet movement was found for that outcome.",
      );
    } catch (requestError) {
      setActionPageError(requestError);
    } finally {
      setRepairingReferralId(null);
    }
  }

  async function createInvoiceEvidence(referralTrackId: string) {
    setRepairingReferralId(referralTrackId);
    setRepairMessage(null);
    try {
      const result = await createOutcomeInvoiceEvidence(referralTrackId, "admin-operator", DEFAULT_TENANT_CODE);
      const lineCount = countFrom(getNestedValue(result, ["repair"], {}), ["line_count"]);
      await refetch();
      setRepairMessage(
        lineCount > 0
          ? `${lineCount} producer invoice line created.`
          : "No missing producer invoice evidence was found for that outcome.",
      );
    } catch (requestError) {
      setActionPageError(requestError);
    } finally {
      setRepairingReferralId(null);
    }
  }

  async function createSettlementEvidence(referralTrackId: string) {
    setRepairingReferralId(referralTrackId);
    setRepairMessage(null);
    try {
      const result = await createOutcomeSettlementEvidence(referralTrackId, "admin-operator", DEFAULT_TENANT_CODE);
      const settlementCount = countFrom(getNestedValue(result, ["repair"], {}), ["settlement_count"]);
      await refetch();
      setRepairMessage(
        settlementCount > 0
          ? `${settlementCount} settlement evidence item created.`
          : "No missing settlement evidence was found for that outcome.",
      );
    } catch (requestError) {
      setActionPageError(requestError);
    } finally {
      setRepairingReferralId(null);
    }
  }

  return (
    <>
      <section className="page-header os-command-hero">
        <div>
          <div className="page-kicker">Amplifi Admin</div>
          <h1 className="page-title">Command Centre</h1>
          <p className="page-copy">
            Operate the distribution network across demand, supply, events, settlement, trust, and runtime readiness.
            The admin workspace should show what is healthy, what needs attention, and where the operator acts next.
          </p>
        </div>
        <StatusBadge label={runtimeReady ? "Network online" : "Needs review"} tone={runtimeReady ? "success" : "warning"} />
      </section>

      <section className="admin-command-grid">
        <div className="admin-command-card primary">
          <div className="admin-command-card-top">
            <div>
              <div className="admin-command-kicker">Operator posture</div>
              <h2>{runtimeReady ? "Network is ready to operate" : "Operator review needed"}</h2>
            </div>
            {runtimeReady ? <CheckCircle2 size={24} /> : <AlertTriangle size={24} />}
          </div>
          <p>
            Runtime, schema, event intake, and audit signals are pulled from the live backend so the operator starts
            from the actual platform state.
          </p>
          <div className="admin-command-metrics">
            <SummaryItem label="Events" value={eventTotal} />
            <SummaryItem label="Audit" value={auditTotal} />
            <SummaryItem label="Schema gaps" value={missingSchemaGroups} />
            <SummaryItem label="Money ready" value={`${readyMoneyOutcomes}/${completedMoneyOutcomes}`} />
          </div>
        </div>

        <div className="panel admin-attention-panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Needs attention</h2>
              <div className="panel-subtitle">Fast triage for the platform operator.</div>
            </div>
          </div>
          <div className="panel-body admin-attention-list">
            {attentionItems.map((item) => (
              <Link className="admin-attention-row" key={item.label} to={item.path}>
                <div>
                  <div className="admin-attention-label">{item.label}</div>
                  <div className="table-subtext">{item.copy}</div>
                </div>
                <StatusBadge label={item.value} tone={item.tone} />
              </Link>
            ))}
          </div>
        </div>
      </section>

      <section className="grid-2">
        <div className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Outcome-to-money map</h2>
              <div className="panel-subtitle">Completed customer outcomes traced into the financial rails.</div>
            </div>
            <StatusBadge
              label={attentionMoneyOutcomes > 0 ? `${attentionMoneyOutcomes} need review` : "Aligned"}
              tone={attentionMoneyOutcomes > 0 ? "warning" : "success"}
            />
          </div>
          <div className="panel-body">
            <div className="summary-grid">
              <SummaryItem label="Completed" value={completedMoneyOutcomes} />
              <SummaryItem label="Ready" value={readyMoneyOutcomes} />
              <SummaryItem label="Exceptions" value={exceptionMoneyOutcomes} />
              <SummaryItem label="Completion" value={moneyCompletionRate} />
            </div>
            <div className="status-list spacious">
              <div className="status-list-title">Repair focus</div>
              {outcomeAttentionBreakdown.length === 0 ? (
                <div className="status-row">
                  <span className="status-name">No money rail breaks</span>
                  <StatusBadge label="Clear" tone="success" />
                </div>
              ) : (
                outcomeAttentionBreakdown.map((item) => {
                  const label = formatDisplay(item.label);
                  const owner = formatDisplay(item.owner);
                  const count = countFrom(item, ["count"]);
                  return (
                    <Link className="status-row" key={`${label}-${owner}`} to={getOwnerPath(owner)}>
                      <span className="status-name">
                        {label}
                        <span className="table-subtext"> {owner}</span>
                      </span>
                      <StatusBadge label={`${count} missing`} tone="warning" />
                    </Link>
                  );
                })
              )}
            </div>
            <div className="status-list spacious">
              <div className="status-list-title">Money journey</div>
              {outcomeJourney.map((step) => {
                const name = formatDisplay(step.step);
                const readyCount = countFrom(step, ["ready_count"]);
                const missingCount = countFrom(step, ["missing_count"]);
                const isExceptionStep = name.toLowerCase().includes("exception");
                const tone = isExceptionStep
                  ? readyCount > 0
                    ? "warning"
                    : "success"
                  : missingCount > 0
                    ? "warning"
                    : "success";
                return (
                  <div className="status-row" key={name}>
                    <span className="status-name">{name}</span>
                    <StatusBadge
                      label={isExceptionStep ? `${readyCount} open` : `${readyCount} ready`}
                      tone={tone}
                    />
                  </div>
                );
              })}
            </div>
            <div className="status-list spacious">
              <div className="status-list-title">Attention outcomes</div>
              {repairMessage ? (
                <div className="status-row">
                  <span className="status-name">{repairMessage}</span>
                  <StatusBadge label="Updated" tone="success" />
                </div>
              ) : null}
              {attentionOutcomes.length === 0 ? (
                <div className="status-row">
                  <span className="status-name">No outcome repair actions</span>
                  <StatusBadge label="Clear" tone="success" />
                </div>
              ) : (
                attentionOutcomes.map((item) => {
                  const referralTrackId = formatDisplay(item.referral_track_id);
                  const missingSteps = asStringArray(getNestedValue(item, ["missing_steps"], []));
                  const repairActions = asArray(getNestedValue(item, ["repair_actions"], []));
                  const canCreateReward = repairActions.some(
                    (action) =>
                      formatDisplay(action.type) === "CREATE_REWARD_EVIDENCE" &&
                      formatDisplay(action.available) === "Yes",
                  );
                  const canCreateCommission = repairActions.some(
                    (action) =>
                      formatDisplay(action.type) === "CREATE_COMMISSION_EVIDENCE" &&
                      formatDisplay(action.available) === "Yes",
                  );
                  const canCreateWallet = repairActions.some(
                    (action) =>
                      formatDisplay(action.type) === "CREATE_WALLET_EVIDENCE" &&
                      formatDisplay(action.available) === "Yes",
                  );
                  const canResolveException = repairActions.some(
                    (action) =>
                      formatDisplay(action.type) === "RESOLVE_SETTLEMENT_EXCEPTIONS" &&
                      formatDisplay(action.available) === "Yes",
                  );
                  const canCreateInvoice = repairActions.some(
                    (action) =>
                      formatDisplay(action.type) === "CREATE_INVOICE_EVIDENCE" &&
                      formatDisplay(action.available) === "Yes",
                  );
                  const canCreateSettlement = repairActions.some(
                    (action) =>
                      formatDisplay(action.type) === "CREATE_SETTLEMENT_EVIDENCE" &&
                      formatDisplay(action.available) === "Yes",
                  );
                  const isRepairing = repairingReferralId === referralTrackId;
                  return (
                    <div className="status-row" key={referralTrackId}>
                      <span className="status-name">
                        {formatOutcomeLabel(item)}
                        <span className="table-subtext"> {missingSteps.join(", ") || "Open exception"}</span>
                      </span>
                      {canCreateReward ? (
                        <button
                          className="button secondary"
                          disabled={isRepairing}
                          onClick={() => createRewardEvidence(referralTrackId)}
                          type="button"
                        >
                          {isRepairing ? "Creating" : "Create reward"}
                        </button>
                      ) : canCreateCommission ? (
                        <button
                          className="button secondary"
                          disabled={isRepairing}
                          onClick={() => createCommissionEvidence(referralTrackId)}
                          type="button"
                        >
                          {isRepairing ? "Creating" : "Create commission"}
                        </button>
                      ) : canCreateWallet ? (
                        <button
                          className="button secondary"
                          disabled={isRepairing}
                          onClick={() => createWalletEvidence(referralTrackId)}
                          type="button"
                        >
                          {isRepairing ? "Creating" : "Create wallet"}
                        </button>
                      ) : canCreateInvoice ? (
                        <button
                          className="button secondary"
                          disabled={isRepairing}
                          onClick={() => createInvoiceEvidence(referralTrackId)}
                          type="button"
                        >
                          {isRepairing ? "Creating" : "Create invoice"}
                        </button>
                      ) : canCreateSettlement ? (
                        <button
                          className="button secondary"
                          disabled={isRepairing}
                          onClick={() => createSettlementEvidence(referralTrackId)}
                          type="button"
                        >
                          {isRepairing ? "Creating" : "Create settlement"}
                        </button>
                      ) : canResolveException ? (
                        <button
                          className="button secondary"
                          disabled={isRepairing}
                          onClick={() => resolveOutcomeException(referralTrackId)}
                          type="button"
                        >
                          {isRepairing ? "Resolving" : "Resolve exception"}
                        </button>
                      ) : (
                        <StatusBadge label="Guided" tone="warning" />
                      )}
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
        <div className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Financial rail ownership</h2>
              <div className="panel-subtitle">How the shared rail supports each target-state user.</div>
            </div>
            <Landmark size={18} />
          </div>
          <div className="panel-body route-list">
            {[
              ["Producer - Supply", "Funds customer outcomes and receives invoice evidence.", "/admin/billing"],
              ["Distributor - Demand", "Earns commission and sees wallet movement after qualified conversion.", "/distributor"],
              ["Amplifi Admin", "Monitors reward, invoice, wallet, settlement, and exception alignment.", "/admin/settlements"],
            ].map(([name, copy, path]) => (
              <Link className="route-item" key={name} to={path}>
                <div>
                  <div className="route-name">{name}</div>
                  <div className="route-path">{copy}</div>
                </div>
                <StatusBadge label="Mapped" tone="info" />
              </Link>
            ))}
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2 className="panel-title">Partner seam</h2>
            <div className="panel-subtitle">Self-service integration boundary for producers, distributors, and enterprise partners.</div>
          </div>
          <StatusBadge
            label={
              partnerSeamAvailable && partnerDeliveriesAvailable && partnerSummaryAvailable
                ? `${partnerClientCount} clients / ${partnerDeliveryStatus}`
                : "Needs setup"
            }
            tone={
              partnerFailedCount
                ? "warning"
                : partnerPendingCount
                  ? "info"
                  : partnerSeamAvailable && partnerDeliveriesAvailable && partnerSummaryAvailable
                    ? "success"
                    : "warning"
            }
          />
        </div>
        <div className="panel-body route-list">
          <div className="route-item">
            <div>
              <div className="route-name">Client credentials</div>
              <div className="route-path">Tenant-scoped partners exchange client credentials for bearer access.</div>
            </div>
            <KeyRound size={18} />
          </div>
          <div className="route-item">
            <div>
              <div className="route-name">Outbound webhooks</div>
              <div className="route-path">
                {partnerSentCount} sent, {partnerPendingCount} pending, {partnerFailedCount} failed in the last 24 hours.
              </div>
            </div>
            <Send size={18} />
          </div>
          <div className="route-item">
            <div>
              <div className="route-name">Alert notifications</div>
              <div className="route-path">
                {partnerAlertsAvailable
                  ? `${partnerAlerts.length} open alert groups. ${latestPartnerNotificationCopy(partnerAlerts)}`
                  : "Alert notification evidence is not available."}
              </div>
            </div>
            <button
              className="button secondary"
              disabled={notifyingPartnerAlerts || !partnerAlertsAvailable || !partnerAlerts.length}
              onClick={notifyWebhookAlerts}
              type="button"
            >
              {notifyingPartnerAlerts ? "Notifying" : "Notify alerts"}
            </button>
          </div>
          <div className="route-item">
            <div>
              <div className="route-name">Delivery worker</div>
              <div className="route-path">
                {partnerDeliveriesAvailable && partnerSummaryAvailable ? "Process due webhook deliveries and update retry or failure state." : partnerDeliveryMessage}
              </div>
              {partnerWebhookMessage ? <div className="route-path">{partnerWebhookMessage}</div> : null}
            </div>
            <button className="button secondary" disabled={processingWebhooks || !partnerDeliveriesAvailable || !partnerSummaryAvailable} onClick={processWebhookQueue} type="button">
              {processingWebhooks ? "Processing" : "Process due"}
            </button>
          </div>
          {partnerClients.slice(0, 3).map((client) => (
            <div className="route-item" key={formatDisplay(getNestedValue(client, ["client_id"]))}>
              <div>
                <div className="route-name">{formatDisplay(getNestedValue(client, ["client_name"]))}</div>
                <div className="route-path">
                  {formatDisplay(getNestedValue(client, ["tenant_code"]))} - {formatDisplay(getNestedValue(client, ["client_id"]))}
                </div>
              </div>
              <StatusBadge label={formatDisplay(getNestedValue(client, ["status"]))} tone="info" />
            </div>
          ))}
          {partnerFailedDeliveries.slice(0, 3).map((delivery) => (
            <div className="route-item" key={formatDisplay(getNestedValue(delivery, ["delivery_id"]))}>
              <div>
                <div className="route-name">{formatDisplay(getNestedValue(delivery, ["event_type"]))}</div>
                <div className="route-path">
                  {formatDisplay(getNestedValue(delivery, ["tenant_code"]))} - attempt {formatDisplay(getNestedValue(delivery, ["attempt_count"]))}
                </div>
                <div className="route-path">{formatDisplay(getNestedValue(delivery, ["last_error"], "Review delivery failure."))}</div>
              </div>
              <StatusBadge label="Failed" tone="warning" />
            </div>
          ))}
          {(!partnerSeamAvailable || !partnerDeliveriesAvailable) && (
            <div className="route-item">
              <div>
                <div className="route-name">Readiness attention</div>
                <div className="route-path">{partnerSeamAvailable ? partnerDeliveryMessage : partnerSeamMessage}</div>
              </div>
              <StatusBadge label="Review" tone="warning" />
            </div>
          )}
          {partnerSeamAvailable && partnerDeliveriesAvailable && partnerClients.length === 0 && partnerFailedDeliveries.length === 0 ? (
            <EmptyState label="No partner clients or failed deliveries returned." />
          ) : null}
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2 className="panel-title">Vertical readiness</h2>
            <div className="panel-subtitle">Configuration-led journey coverage beyond a banking-only platform.</div>
          </div>
          <StatusBadge label={agnosticReady ? "Agnostic proof" : "Banking-led"} tone={agnosticReady ? "success" : "warning"} />
        </div>
        <div className="panel-body route-list">
          {verticalItems.length === 0 ? (
            <EmptyState label="No configured vertical readiness records returned." />
          ) : (
          verticalItems.map((item) => {
            const name = formatDisplay(getNestedValue(item, ["name"]));
            const code = formatDisplay(getNestedValue(item, ["vertical_code"]));
            const source = formatDisplay(getNestedValue(item, ["configuration_source"], "configuration"));
            const journeyCode = formatDisplay(getNestedValue(item, ["journey_code"]));
            const journeySteps = asStringArray(getNestedValue(item, ["journey_steps"], []));
            const completionEvents = asStringArray(getNestedValue(item, ["completion_events"], []));
            const missingComponents = asStringArray(getNestedValue(item, ["missing_components"], []));
            const rewardPolicy = formatDisplay(getNestedValue(item, ["reward_policy"]));
            const leaderboardCode = formatDisplay(getNestedValue(item, ["leaderboard_code"]));
            const identifierReady = formatDisplay(getNestedValue(item, ["identifier_validation_configured"], false));
            const fulfilmentProvider = formatDisplay(getNestedValue(item, ["fulfilment_route", "provider_key"]));
            const fulfilmentReady = formatDisplay(getNestedValue(item, ["fulfilment_route_configured"], false));
            const regulatoryReady = formatDisplay(getNestedValue(item, ["regulatory_overlay_configured"], false));
            const regulatoryPolicy = formatDisplay(getNestedValue(item, ["regulatory_policy_code"]));
            const commercialStatus = formatDisplay(getNestedValue(item, ["commercial_status"]));
            const configured = formatDisplay(getNestedValue(item, ["status"])) === "CONFIGURED";
            return (
              <div className="route-item" key={code}>
                <div>
                  <div className="route-name">
                    {name} / {journeyCode}
                  </div>
                  <div className="route-path">
                    {journeySteps.length} steps · {completionEvents.join(", ") || "No completion event configured"}
                  </div>
                  <div className="route-path">
                    Reward {rewardPolicy} · Leaderboard {leaderboardCode}
                  </div>
                  <div className="route-path">Fulfilment {fulfilmentReady === "Yes" ? fulfilmentProvider : "missing"}</div>
                  <div className="route-path">Regulatory overlay {regulatoryReady === "Yes" ? regulatoryPolicy : "missing"}</div>
                  <div className="route-path">Identifier validation {identifierReady === "Yes" ? "configured" : "missing"}</div>
                  <div className="route-path">
                    {missingComponents.length ? `Missing ${missingComponents.join(", ")}` : `Loaded from ${source}`}
                  </div>
                </div>
                <StatusBadge
                  label={configured ? commercialStatus : "Incomplete"}
                  tone={configured ? "success" : "warning"}
                />
              </div>
            );
          })
          )}
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2 className="panel-title">Insurance journey proof</h2>
            <div className="panel-subtitle">{formatDisplay(getNestedValue(insuranceProof, ["proof_summary"], "Run the canonical Insurance journey seed to prove the surfaces."))}</div>
          </div>
          <StatusBadge label={insuranceProofReady ? "Surface proof" : "Needs evidence"} tone={insuranceProofReady ? "success" : "warning"} />
        </div>
        <div className="panel-body route-list">
          {insuranceProofSteps.length === 0 ? (
            <EmptyState label="No Insurance proof steps returned." />
          ) : (
          insuranceProofSteps.map((step) => {
            const surface = formatDisplay(getNestedValue(step, ["surface"]));
            const label = formatDisplay(getNestedValue(step, ["label"]));
            const evidence = formatDisplay(getNestedValue(step, ["evidence"]));
            const action = formatDisplay(getNestedValue(step, ["action"]));
            const ready = formatDisplay(getNestedValue(step, ["ready"], false)) === "Yes";
            return (
              <div className="route-item" key={`${surface}-${label}`}>
                <div>
                  <div className="route-name">{surface}</div>
                  <div className="route-path">{label}</div>
                  <div className="route-path">{evidence}</div>
                  <div className="route-path">{action}</div>
                </div>
                <StatusBadge label={ready ? "Ready" : "Missing"} tone={ready ? "success" : "warning"} />
              </div>
            );
          })
          )}
        </div>
      </section>

      <section className="admin-rail-grid">
        {adminRails.map((rail) => {
          const Icon = rail.icon;
          return (
          <Link className="admin-rail-card" key={rail.title} to={rail.path}>
            <div className="capability-icon">
              <Icon size={18} />
            </div>
            <div>
              <div className="capability-title">{rail.title}</div>
              <div className="capability-copy">{rail.copy}</div>
            </div>
            <StatusBadge label={rail.badge} tone="info" />
          </Link>
          );
        })}
      </section>

      <section className="role-gateway-grid">
        {roleGateways.map((gateway) => {
          const Icon = gateway.icon;
          return (
            <article className={`role-gateway-card ${gateway.side.toLowerCase()}`} key={gateway.role}>
              <div className="role-gateway-top">
                <div className="role-gateway-icon">
                  <Icon size={22} />
                </div>
                <StatusBadge label={gateway.side} tone={gateway.tone} />
              </div>
              <div>
                <div className="role-gateway-role">{gateway.role}</div>
                <h2>{gateway.headline}</h2>
                <p>{gateway.copy}</p>
              </div>
              <div className="role-outcome-list">
                {gateway.outcomes.map((outcome) => (
                  <span key={outcome}>{outcome}</span>
                ))}
              </div>
              <div className="role-gateway-actions">
                <Link className="button" to={gateway.path}>
                  {gateway.action}
                </Link>
                {gateway.links.map((link) => (
                  <Link className="button secondary" key={link.path} to={link.path}>
                    {link.label}
                  </Link>
                ))}
              </div>
            </article>
          );
        })}
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2 className="panel-title">Shared platform capabilities</h2>
            <div className="panel-subtitle">Capabilities that sit underneath the three main user experiences.</div>
          </div>
          <StatusBadge label="Mapped" tone="success" />
        </div>
        <div className="panel-body capability-grid">
          {capabilities.map((capability) => {
            const Icon = capability.icon;
            return (
              <Link className="capability-card" key={capability.name} to={capability.path}>
                <div className="capability-icon">
                  <Icon size={18} />
                </div>
                <div>
                  <div className="capability-title">{capability.name}</div>
                  <div className="capability-copy">{capability.copy}</div>
                  <div className="capability-path">{getUserRole(capability.name)}</div>
                </div>
                <StatusBadge label={capability.badge} tone={capability.tone} />
              </Link>
            );
          })}
        </div>
      </section>

      <section className="grid-3">
        <KpiCard label="Runtime health" value="Online" footnote="Operating layer is reachable" icon={Activity} />
        <KpiCard
          label="Trust signals"
          value={countFrom(data?.audit, ["total", "total_count", "audit_count"])}
          footnote="Sensitive action visibility"
          icon={ShieldCheck}
        />
        <KpiCard
          label="Network events"
          value={countFrom(data?.events, ["total", "total_count", "event_count"])}
          footnote="Enterprise event fabric"
          icon={GitBranch}
        />
      </section>

      <section className="grid-2">
        <div className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Readiness summary</h2>
              <div className="panel-subtitle">Schema groups and dependency status from the backend.</div>
            </div>
            <DatabaseZap size={18} />
          </div>
          <div className="panel-body">
            <div className="summary-grid">
              <SummaryItem label="Database" value={getNestedValue(data?.health, ["components", "db", "msg"])} />
              <SummaryItem label="Schema" value={getNestedValue(data?.health, ["components", "schema", "msg"])} />
              <SummaryItem label="Messaging" value={getNestedValue(data?.health, ["components", "kafka", "msg"])} />
            </div>
            <div className="status-list spacious">
              <div className="status-list-title">Schema groups</div>
              {objectEntries(getNestedValue(data?.readiness, ["components", "schema", "groups"], {})).map(
                ([name, group]) => {
                  const ok = formatDisplay(group.ok);
                  return (
                    <div className="status-row" key={name}>
                      <span className="status-name">{formatGroupName(name)}</span>
                      <StatusBadge label={ok === "Yes" ? "OK" : "Missing"} tone={statusTone(ok)} />
                    </div>
                  );
                },
              )}
            </div>
          </div>
        </div>
        <div className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Target-state coverage</h2>
              <div className="panel-subtitle">How the current UI lines up to the platform roadmap.</div>
            </div>
          </div>
          <div className="panel-body route-list">
            {[
              ["Distributor - Demand", "Earnings hub, customer journey, marketplace demand routes, wallet movement", "Primary"],
              ["Producer - Supply", "Producer workspace, funding spine, treasury rail, offers, budgets, contracts", "Primary"],
              ["Amplifi Admin", "Command centre, event fabric, settlement rail, trust, audit, runtime health", "Primary"],
              ["Marketplace bridge", "Matches producer supply to distributor demand", "Shared"],
              ["Financial rail", "Funds rewards, reconciles exposure, settles earnings", "Shared"],
              ["Copilot layer", "Future optimisation across demand, supply, and admin operations", "Future"],
            ].map(([name, path, badge]) => (
              <div className="route-item" key={name}>
                <div>
                  <div className="route-name">{name}</div>
                  <div className="route-path">{path}</div>
                </div>
                <StatusBadge label={badge} tone="success" />
              </div>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}

function formatGroupName(value: string): string {
  return value.replace(/_/g, " ");
}

function formatPercent(value: unknown): string {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) {
    return "0%";
  }
  return `${Math.round(parsed * 100)}%`;
}

function asStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.map((item) => formatDisplay(item)).filter((item) => item !== "-");
}

function formatOutcomeLabel(item: Record<string, unknown>): string {
  const opportunity = formatDisplay(item.opportunity_code);
  const distributor = formatDisplay(item.distributor_code);
  if (opportunity !== "-" && distributor !== "-") {
    return `${opportunity} / ${distributor}`;
  }
  return formatDisplay(item.referral_track_id);
}

function latestPartnerNotificationCopy(alerts: Array<Record<string, unknown>>): string {
  const latest = alerts
    .map((alert) => ({
      status: formatDisplay(getNestedValue(alert, ["last_notification_status"], "")),
      notifiedAt: formatDisplay(getNestedValue(alert, ["last_notified_at"], "")),
    }))
    .find((alert) => alert.notifiedAt && alert.notifiedAt !== "-");

  if (!latest) {
    return "No notification evidence recorded yet.";
  }

  return `Last notification ${latest.status} at ${latest.notifiedAt}.`;
}

function getOwnerPath(owner: string): string {
  if (owner.includes("Producer")) return "/admin/billing";
  if (owner.includes("Distributor")) return "/admin/distribution";
  return "/admin/settlements";
}

function getUserRole(name: string): string {
  if (name.includes("Distributor")) return "Demand-side user";
  if (name.includes("Producer")) return "Supply-side user";
  if (name.includes("Admin")) return "Platform operator";
  if (name.includes("Marketplace")) return "Demand and supply bridge";
  if (name.includes("Customer")) return "Demand conversion journey";
  if (name.includes("Funding")) return "Shared financial rail";
  if (name.includes("Copilot")) return "Future optimisation layer";
  return "Platform capability";
}
