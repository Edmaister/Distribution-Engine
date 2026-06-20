import { GitPullRequestArrow, Send, ShieldCheck, Undo2, Users, XCircle } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import {
  acceptAdminRoute,
  activateAdminDistributor,
  applyAdminDistributorGovernanceAction,
  closeAdminOpportunity,
  completeAdminComplianceReview,
  createAdminComplianceReview,
  createAdminDispute,
  creditAdminDistributorWallet,
  declineAdminRoute,
  getAdminDistributionAttributionExceptions,
  getAdminComplianceReviews,
  getAdminDisputes,
  getAdminDistributorWalletLedger,
  getAdminDistributorWallets,
  getAdminDistributionDistributorReport,
  getAdminDistributionGovernanceReport,
  getAdminDistributionOpportunityReport,
  getAdminDistributionOverview,
  getAdminDistributors,
  getAdminGovernanceAudit,
  getAdminOpportunities,
  getAdminRoutes,
  holdAdminDistributorWallet,
  payoutAdminDistributorWallet,
  publishAdminOpportunity,
  releaseHoldAdminDistributorWallet,
  resolveAdminDispute,
  reopenAdminOpportunity,
  reverseAdminDistributorWallet,
  suspendAdminDistributor,
  terminateAdminDistributor,
} from "../../api/endpoints/distribution";
import { DataTable } from "../../components/DataTable";
import { ErrorPanel } from "../../components/ErrorPanel";
import { FieldLabel } from "../../components/FieldLabel";
import { ActionGuardrail, GuardrailItem, GuardrailTone } from "../../components/ActionGuardrail";
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
import { DistributionMarketplaceView } from "./distribution/DistributionMarketplaceView";
import type { MarketplaceCard } from "./distribution/DistributionMarketplaceView";

const ADMIN_DISTRIBUTION_TENANT_KEY = "amplifi.adminDistribution.tenant";

type DistributionPageMode = "marketplace" | "operations";

export function DistributionOperationsPage() {
  return <DistributionCommandCentrePage mode="operations" />;
}

export function DistributionCommandCentrePage({ mode = "marketplace" }: { mode?: DistributionPageMode }) {
  const { refreshKey } = useRefreshContext();
  const [tenantCode, setTenantCode] = useState(localStorage.getItem(ADMIN_DISTRIBUTION_TENANT_KEY) || "FNB");
  const [submittedTenant, setSubmittedTenant] = useState(
    localStorage.getItem(ADMIN_DISTRIBUTION_TENANT_KEY) || "FNB",
  );
  const [distributors, setDistributors] = useState<Record<string, unknown>[]>([]);
  const [opportunities, setOpportunities] = useState<Record<string, unknown>[]>([]);
  const [routes, setRoutes] = useState<Record<string, unknown>[]>([]);
  const [wallets, setWallets] = useState<Record<string, unknown>[]>([]);
  const [walletLedger, setWalletLedger] = useState<Record<string, unknown>[]>([]);
  const [complianceReviews, setComplianceReviews] = useState<Record<string, unknown>[]>([]);
  const [disputes, setDisputes] = useState<Record<string, unknown>[]>([]);
  const [governanceAudit, setGovernanceAudit] = useState<Record<string, unknown>[]>([]);
  const [overview, setOverview] = useState<unknown>(null);
  const [attributionExceptions, setAttributionExceptions] = useState<unknown>(null);
  const [opportunityReport, setOpportunityReport] = useState<unknown>(null);
  const [distributorReport, setDistributorReport] = useState<unknown>(null);
  const [governanceReport, setGovernanceReport] = useState<unknown>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const [selectedDistributorId, setSelectedDistributorId] = useState("");
  const [selectedWalletId, setSelectedWalletId] = useState("");
  const [selectedOpportunityId, setSelectedOpportunityId] = useState("");
  const [selectedRouteId, setSelectedRouteId] = useState("");
  const [walletAmount, setWalletAmount] = useState("1.00");
  const [walletCorrelationId, setWalletCorrelationId] = useState("");
  const [selectedReviewId, setSelectedReviewId] = useState("");
  const [reviewType, setReviewType] = useState("KYC");
  const [reviewer, setReviewer] = useState("ops");
  const [reviewNotes, setReviewNotes] = useState("");
  const [reviewResult, setReviewResult] = useState("PASSED");
  const [selectedDisputeId, setSelectedDisputeId] = useState("");
  const [disputeRaisedBy, setDisputeRaisedBy] = useState("ops");
  const [disputeReasonCode, setDisputeReasonCode] = useState("ROUTE_QUERY");
  const [disputeDescription, setDisputeDescription] = useState("");
  const [disputeResolutionStatus, setDisputeResolutionStatus] = useState("RESOLVED");
  const [governanceActionType, setGovernanceActionType] = useState("SUSPEND");
  const [governanceReasonCode, setGovernanceReasonCode] = useState("COMPLIANCE_REVIEW");
  const [governanceActor, setGovernanceActor] = useState("ops");
  const [governanceNotes, setGovernanceNotes] = useState("");
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [actionError, setActionError] = useState<unknown>(null);
  const [actionResult, setActionResult] = useState<Record<string, unknown> | null>(null);
  const [localRefreshKey, setLocalRefreshKey] = useState(0);
  const [marketplaceSearch, setMarketplaceSearch] = useState("");
  const [marketplaceFilter, setMarketplaceFilter] = useState("ALL");
  const [marketplaceSort, setMarketplaceSort] = useState("HIGHEST_PAYING");

  useEffect(() => {
    if (!submittedTenant) {
      return;
    }

    let alive = true;
    setLoading(true);
    setError(null);
    Promise.all([
      getAdminDistributors(submittedTenant),
      getAdminOpportunities(submittedTenant),
      getAdminRoutes(submittedTenant),
      getAdminDistributorWallets(submittedTenant),
      getAdminComplianceReviews(submittedTenant),
      getAdminDisputes(submittedTenant),
      getAdminGovernanceAudit(submittedTenant),
      getAdminDistributionOverview(submittedTenant),
      getAdminDistributionOpportunityReport(submittedTenant),
      getAdminDistributionDistributorReport(submittedTenant),
      getAdminDistributionGovernanceReport(submittedTenant),
      getAdminDistributionAttributionExceptions(submittedTenant),
    ])
      .then(
        ([
          distributorPayload,
          opportunityPayload,
          routePayload,
          walletPayload,
          compliancePayload,
          disputePayload,
          governanceAuditPayload,
          overviewPayload,
          opportunityReportPayload,
          distributorReportPayload,
          governanceReportPayload,
          attributionExceptionPayload,
        ]) => {
          if (alive) {
            setDistributors(asArray(distributorPayload));
            setOpportunities(asArray(opportunityPayload));
            setRoutes(asArray(routePayload));
            setWallets(asArray(walletPayload));
            setComplianceReviews(asArray(compliancePayload));
            setDisputes(asArray(disputePayload));
            setGovernanceAudit(asArray(governanceAuditPayload));
            setOverview(overviewPayload);
            setOpportunityReport(opportunityReportPayload);
            setDistributorReport(distributorReportPayload);
            setGovernanceReport(governanceReportPayload);
            setAttributionExceptions(attributionExceptionPayload);
          }
        },
      )
      .catch((requestError) => alive && setError(requestError))
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [submittedTenant, refreshKey, localRefreshKey]);

  useEffect(() => {
    if (!selectedWalletId) {
      setWalletLedger([]);
      return;
    }

    let alive = true;
    getAdminDistributorWalletLedger(selectedWalletId)
      .then((payload) => {
        if (alive) {
          setWalletLedger(asArray(payload));
        }
      })
      .catch(() => {
        if (alive) {
          setWalletLedger([]);
        }
      });
    return () => {
      alive = false;
    };
  }, [selectedWalletId, localRefreshKey, refreshKey]);

  useEffect(() => {
    if (!distributors.length) {
      setSelectedDistributorId("");
      return;
    }

    const current = distributors.find(
      (distributor) => getValue(distributor, ["distributor_id", "id"]) === selectedDistributorId,
    );
    setSelectedDistributorId(getValue(current || distributors[0], ["distributor_id", "id"], ""));
  }, [distributors, selectedDistributorId]);

  useEffect(() => {
    if (!wallets.length) {
      setSelectedWalletId("");
      return;
    }

    const current = wallets.find((wallet) => getValue(wallet, ["wallet_id", "id"]) === selectedWalletId);
    setSelectedWalletId(getValue(current || wallets[0], ["wallet_id", "id"], ""));
  }, [wallets, selectedWalletId]);

  useEffect(() => {
    if (!opportunities.length) {
      setSelectedOpportunityId("");
      return;
    }

    const current = opportunities.find((opportunity) => getValue(opportunity, ["opportunity_id", "id"]) === selectedOpportunityId);
    setSelectedOpportunityId(getValue(current || opportunities[0], ["opportunity_id", "id"], ""));
  }, [opportunities, selectedOpportunityId]);

  useEffect(() => {
    if (!routes.length) {
      setSelectedRouteId("");
      return;
    }

    const current = routes.find((route) => getValue(route, ["route_id", "id"]) === selectedRouteId);
    setSelectedRouteId(getValue(current || routes[0], ["route_id", "id"], ""));
  }, [routes, selectedRouteId]);

  useEffect(() => {
    const openReviews = complianceReviews.filter((review) => getValue(review, ["review_status", "status"]) === "OPEN");
    if (!openReviews.length) {
      setSelectedReviewId("");
      return;
    }

    const current = openReviews.find((review) => getValue(review, ["review_id", "id"]) === selectedReviewId);
    setSelectedReviewId(getValue(current || openReviews[0], ["review_id", "id"], ""));
  }, [complianceReviews, selectedReviewId]);

  useEffect(() => {
    const openDisputes = disputes.filter((dispute) => getValue(dispute, ["dispute_status", "status"]) === "OPEN");
    if (!openDisputes.length) {
      setSelectedDisputeId("");
      return;
    }

    const current = openDisputes.find((dispute) => getValue(dispute, ["dispute_id", "id"]) === selectedDisputeId);
    setSelectedDisputeId(getValue(current || openDisputes[0], ["dispute_id", "id"], ""));
  }, [disputes, selectedDisputeId]);

  const selectedOpportunity = opportunities.find(
    (opportunity) => getValue(opportunity, ["opportunity_id", "id"]) === selectedOpportunityId,
  );
  const selectedDistributor = distributors.find(
    (distributor) => getValue(distributor, ["distributor_id", "id"]) === selectedDistributorId,
  );
  const selectedDistributorStatus = selectedDistributor ? getValue(selectedDistributor, ["status", "lifecycle_status"]) : "-";
  const selectedWallet = wallets.find((wallet) => getValue(wallet, ["wallet_id", "id"]) === selectedWalletId);
  const selectedOpportunityStatus = selectedOpportunity
    ? getValue(selectedOpportunity, ["opportunity_status", "status"])
    : "-";
  const selectedRoute = routes.find((route) => getValue(route, ["route_id", "id"]) === selectedRouteId);
  const selectedRouteStatus = selectedRoute ? getValue(selectedRoute, ["route_status", "status"]) : "-";
  const openReviews = complianceReviews.filter((review) => getValue(review, ["review_status", "status"]) === "OPEN");
  const openDisputes = disputes.filter((dispute) => getValue(dispute, ["dispute_status", "status"]) === "OPEN");
  const selectedWalletStatus = selectedWallet ? getValue(selectedWallet, ["status"]) : "-";
  const selectedWalletAvailable = moneyNumber(selectedWallet ? getValue(selectedWallet, ["available_balance"], "0") : "0");
  const selectedWalletHeld = moneyNumber(selectedWallet ? getValue(selectedWallet, ["held_balance"], "0") : "0");
  const activeDistributorCount = distributors.filter(
    (distributor) => getValue(distributor, ["status", "lifecycle_status"]) === "ACTIVE",
  ).length;
  const publishedOpportunityCount = opportunities.filter(
    (opportunity) => getValue(opportunity, ["opportunity_status", "status"]) === "PUBLISHED",
  ).length;
  const draftOpportunityCount = opportunities.filter(
    (opportunity) => getValue(opportunity, ["opportunity_status", "status"]) === "DRAFT",
  ).length;
  const routedOfferCount = routes.filter((route) => getValue(route, ["route_status", "status"]) === "ROUTED").length;
  const walletExposureAmount = wallets.reduce(
    (total, wallet) => total + moneyNumber(getValue(wallet, ["available_balance"], "0")),
    0,
  );
  const walletMovementAmount = moneyNumber(walletAmount);
  const canCreditWallet = selectedWalletStatus === "ACTIVE" && walletMovementAmount > 0;
  const canHoldWallet = canCreditWallet && selectedWalletAvailable >= walletMovementAmount;
  const canReleaseWalletHold = canCreditWallet && selectedWalletHeld >= walletMovementAmount;
  const canPayoutWallet = canCreditWallet && selectedWalletHeld >= walletMovementAmount;
  const canReverseWallet = canCreditWallet && selectedWalletAvailable >= walletMovementAmount;
  const canOpenComplianceReview = Boolean(selectedDistributorId) && selectedDistributorStatus !== "TERMINATED";
  const canCompleteComplianceReview = Boolean(selectedReviewId);
  const canCreateDispute = Boolean(selectedRouteId) && selectedRouteStatus !== "-";
  const canResolveDispute = Boolean(selectedDisputeId);
  const canApplyGovernanceAction = isGovernanceActionAllowed(selectedDistributorStatus, governanceActionType);
  const attributionExceptionRows = asArray(getNestedValue(attributionExceptions, ["items"], []));
  const attributionGuard = getAttributionGuardrail({
    unlinkedCount: Number(getNestedValue(overview, ["conversions", "unlinked_count"], attributionExceptionRows.length)),
    attributionRate: formatDisplay(getNestedValue(overview, ["conversions", "attribution_rate"], "0.0000")),
    completedExceptionCount: Number(getNestedValue(attributionExceptions, ["completed_count"], 0)),
  });
  const distributorGuard = simpleActionGuardrail({
    hasSelection: Boolean(selectedDistributor),
    ready: selectedDistributorStatus !== "-" && selectedDistributorStatus !== "TERMINATED",
    status: selectedDistributorStatus,
    title: "Distributor lifecycle controls",
    missingTitle: "Select a distributor",
    copy: "These actions change whether a distributor can participate in marketplace routing.",
    backendChange: "Distributor status",
    availableAction: selectedDistributorStatus === "ACTIVE" ? "Suspend or terminate" : selectedDistributorStatus === "SUSPENDED" ? "Activate or terminate" : selectedDistributorStatus === "TERMINATED" ? "None" : "Activate",
    actionLoading,
  });
  const walletGuard = getWalletGuardrail({
    selectedWallet,
    selectedWalletStatus,
    walletMovementAmount,
    selectedWalletAvailable,
    selectedWalletHeld,
    actionLoading,
  });
  const opportunityGuard = simpleActionGuardrail({
    hasSelection: Boolean(selectedOpportunity),
    ready: ["DRAFT", "PUBLISHED", "CLOSED"].includes(selectedOpportunityStatus),
    status: selectedOpportunityStatus,
    title: "Opportunity lifecycle controls",
    missingTitle: "Select an opportunity",
    copy: "These actions decide whether sponsor-funded demand can be routed through the marketplace.",
    backendChange: "Opportunity status",
    availableAction: selectedOpportunityStatus === "DRAFT" ? "Publish" : selectedOpportunityStatus === "PUBLISHED" ? "Close" : selectedOpportunityStatus === "CLOSED" ? "Reopen" : "None",
    actionLoading,
  });
  const routeGuard = simpleActionGuardrail({
    hasSelection: Boolean(selectedRoute),
    ready: selectedRouteStatus === "ROUTED",
    status: selectedRouteStatus,
    title: "Route decision controls",
    missingTitle: "Select a route",
    copy: "Accepting or declining records the outcome for a matched opportunity-distributor route.",
    backendChange: "Route status",
    availableAction: selectedRouteStatus === "ROUTED" ? "Accept or decline" : "None",
    actionLoading,
  });
  const complianceGuard = simpleActionGuardrail({
    hasSelection: Boolean(selectedDistributor),
    ready: canOpenComplianceReview || canCompleteComplianceReview,
    status: selectedDistributorStatus,
    title: "Compliance review controls",
    missingTitle: "Select a distributor",
    copy: "Create a review when a distributor needs checking, then complete open reviews with an outcome.",
    backendChange: "Compliance review",
    availableAction: canCompleteComplianceReview ? "Complete review" : canOpenComplianceReview ? "Open review" : "None",
    actionLoading,
  });
  const disputeGuard = simpleActionGuardrail({
    hasSelection: Boolean(selectedRoute),
    ready: canCreateDispute || canResolveDispute,
    status: selectedRouteStatus,
    title: "Route dispute controls",
    missingTitle: "Select a route",
    copy: "Dispute actions preserve an audit trail when a route outcome needs investigation.",
    backendChange: "Dispute record",
    availableAction: canResolveDispute ? "Resolve dispute" : canCreateDispute ? "Create dispute" : "None",
    actionLoading,
  });
  const governanceGuard = simpleActionGuardrail({
    hasSelection: Boolean(selectedDistributor),
    ready: canApplyGovernanceAction,
    status: selectedDistributorStatus,
    title: "Distributor governance controls",
    missingTitle: "Select a distributor",
    copy: governanceActionHint(selectedDistributorStatus, governanceActionType),
    backendChange: "Governance audit",
    availableAction: canApplyGovernanceAction ? governanceActionType : "Blocked",
    actionLoading,
  });
  const distributionGuidance = getDistributionGuidance({
    opportunities,
    routes,
    openReviewCount: openReviews.length,
    openDisputeCount: openDisputes.length,
    selectedOpportunityStatus,
    selectedRouteStatus,
    selectedDistributorStatus,
  });
  const marketplaceCategories = getMarketplaceCategories(opportunities);
  const marketplaceCards = getMarketplaceCards({
    opportunities,
    routes,
    search: marketplaceSearch,
    filter: marketplaceFilter,
    sort: marketplaceSort,
  });
  const featuredCampaign = marketplaceCards.find((card) => card.id === selectedOpportunityId) || marketplaceCards[0];
  const marketplaceActiveCount = marketplaceCards.reduce((total, card) => total + card.activeCount, 0);

  function submitTenant(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cleanedTenant = tenantCode.trim().toUpperCase();
    localStorage.setItem(ADMIN_DISTRIBUTION_TENANT_KEY, cleanedTenant);
    setTenantCode(cleanedTenant);
    setSubmittedTenant(cleanedTenant);
    setActionError(null);
    setActionResult(null);
  }

  function runAction(label: string, action: () => Promise<Record<string, unknown>>) {
    setActionLoading(label);
    setActionError(null);
    setActionResult(null);
    action()
      .then((payload) => {
        setActionResult({ action: label, result: payload });
        setLocalRefreshKey((value) => value + 1);
      })
      .catch((requestError) => setActionError(requestError))
      .finally(() => setActionLoading(null));
  }

  function submitActivateDistributor(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selectedDistributorId) {
      if (!window.confirm("Activate this distributor? They can receive routed opportunities once active.")) {
        return;
      }
      runAction("Activate distributor", () => activateAdminDistributor(selectedDistributorId));
    }
  }

  function submitSuspendDistributor(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selectedDistributorId) {
      if (!window.confirm("Suspend this distributor? They should not receive new routed opportunities while suspended.")) {
        return;
      }
      runAction("Suspend distributor", () => suspendAdminDistributor(selectedDistributorId));
    }
  }

  function submitTerminateDistributor(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selectedDistributorId) {
      if (!window.confirm("Terminate this distributor?")) {
        return;
      }
      runAction("Terminate distributor", () => terminateAdminDistributor(selectedDistributorId));
    }
  }

  function walletRequest() {
    return {
      amount: walletAmount,
      correlation_id: walletCorrelationId.trim() || undefined,
      metadata: { source: "amplifi_control_centre" },
    };
  }

  function submitWalletCredit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selectedWalletId && window.confirm("Credit this distributor wallet?")) {
      runAction("Credit wallet", () => creditAdminDistributorWallet(selectedWalletId, walletRequest()));
    }
  }

  function submitWalletHold(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selectedWalletId && window.confirm("Place a hold on available distributor wallet funds?")) {
      runAction("Hold wallet funds", () => holdAdminDistributorWallet(selectedWalletId, walletRequest()));
    }
  }

  function submitWalletReleaseHold(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selectedWalletId && window.confirm("Release held distributor wallet funds back to available balance?")) {
      runAction("Release wallet hold", () => releaseHoldAdminDistributorWallet(selectedWalletId, walletRequest()));
    }
  }

  function submitWalletPayout(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selectedWalletId && window.confirm("Pay out held distributor wallet funds?")) {
      runAction("Payout wallet", () => payoutAdminDistributorWallet(selectedWalletId, walletRequest()));
    }
  }

  function submitWalletReverse(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selectedWalletId && window.confirm("Reverse available distributor wallet earnings?")) {
      runAction("Reverse wallet earning", () => reverseAdminDistributorWallet(selectedWalletId, walletRequest()));
    }
  }

  function submitPublish(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selectedOpportunityId) {
      if (!window.confirm("Publish this opportunity so it can be routed?")) {
        return;
      }
      runAction("Publish opportunity", () => publishAdminOpportunity(selectedOpportunityId));
    }
  }

  function submitClose(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selectedOpportunityId) {
      if (!window.confirm("Close this opportunity? It will no longer be available for new routing.")) {
        return;
      }
      runAction("Close opportunity", () => closeAdminOpportunity(selectedOpportunityId));
    }
  }

  function submitReopen(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selectedOpportunityId) {
      if (!window.confirm("Reopen this opportunity?")) {
        return;
      }
      runAction("Reopen opportunity", () => reopenAdminOpportunity(selectedOpportunityId));
    }
  }

  function submitAcceptRoute(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selectedRouteId) {
      if (!window.confirm("Accept this offer route?")) {
        return;
      }
      runAction("Accept route", () => acceptAdminRoute(selectedRouteId));
    }
  }

  function submitDeclineRoute(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selectedRouteId) {
      if (!window.confirm("Decline this offer route?")) {
        return;
      }
      runAction("Decline route", () => declineAdminRoute(selectedRouteId));
    }
  }

  function submitCreateComplianceReview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedDistributorId) {
      return;
    }
    if (!window.confirm("Open a compliance review for this distributor?")) {
      return;
    }
    runAction("Open compliance review", () =>
      createAdminComplianceReview({
        distributor_id: selectedDistributorId,
        review_type: reviewType,
        reviewer: reviewer.trim() || undefined,
        notes: reviewNotes.trim() || undefined,
        metadata: { source: "amplifi_control_centre" },
      }),
    );
  }

  function submitCompleteComplianceReview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedReviewId) {
      return;
    }
    if (!window.confirm("Complete this compliance review?")) {
      return;
    }
    runAction("Complete compliance review", () =>
      completeAdminComplianceReview(selectedReviewId, {
        review_result: reviewResult,
        reviewer: reviewer.trim() || undefined,
        notes: reviewNotes.trim() || undefined,
        metadata: { source: "amplifi_control_centre" },
      }),
    );
  }

  function submitCreateDispute(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedRouteId) {
      return;
    }
    if (!window.confirm("Create a dispute against this route?")) {
      return;
    }
    runAction("Create route dispute", () =>
      createAdminDispute({
        route_id: selectedRouteId,
        raised_by: disputeRaisedBy.trim() || "ops",
        reason_code: disputeReasonCode.trim() || "ROUTE_QUERY",
        description: disputeDescription.trim() || undefined,
        metadata: { source: "amplifi_control_centre" },
      }),
    );
  }

  function submitResolveDispute(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedDisputeId) {
      return;
    }
    if (!window.confirm("Resolve this dispute?")) {
      return;
    }
    runAction("Resolve dispute", () =>
      resolveAdminDispute(selectedDisputeId, {
        dispute_status: disputeResolutionStatus,
        resolved_by: disputeRaisedBy.trim() || "ops",
        resolution_notes: disputeDescription.trim() || undefined,
        metadata: { source: "amplifi_control_centre" },
      }),
    );
  }

  function submitGovernanceAction(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedDistributorId) {
      return;
    }
    if (!window.confirm("Apply this governance action to the selected distributor?")) {
      return;
    }
    runAction("Apply governance action", () =>
      applyAdminDistributorGovernanceAction(selectedDistributorId, {
        action_type: governanceActionType,
        reason_code: governanceReasonCode.trim() || undefined,
        actor: governanceActor.trim() || undefined,
        notes: governanceNotes.trim() || undefined,
        metadata: { source: "amplifi_control_centre" },
      }),
    );
  }

  if (loading) {
    return <LoadingState label="Loading distribution command centre" />;
  }

  if (error) {
    return <ErrorPanel error={error} />;
  }

  return (
    <>
      {mode === "marketplace" ? (
        <DistributionMarketplaceView
          activeDistributorCount={activeDistributorCount}
          distributorsCount={distributors.length}
          featuredCampaign={featuredCampaign}
          marketplaceActiveCount={marketplaceActiveCount}
          marketplaceCards={marketplaceCards}
          marketplaceCategories={marketplaceCategories}
          marketplaceFilter={marketplaceFilter}
          marketplaceSearch={marketplaceSearch}
          marketplaceSort={marketplaceSort}
          opportunitiesCount={opportunities.length}
          publishedOpportunityCount={publishedOpportunityCount}
          routedOfferCount={routedOfferCount}
          submittedTenant={submittedTenant}
          tenantCode={tenantCode}
          onCampaignSelect={setSelectedOpportunityId}
          onMarketplaceFilterChange={setMarketplaceFilter}
          onMarketplaceSearchChange={setMarketplaceSearch}
          onMarketplaceSortChange={setMarketplaceSort}
          onSubmitTenant={submitTenant}
          onTenantCodeChange={setTenantCode}
        />
      ) : (
        <>
          <section className="page-header">
            <div>
              <div className="page-kicker">Marketplace operations</div>
              <h1 className="page-title">Demand Operations</h1>
              <p className="page-copy">
                Operational controls for distributor eligibility, demand publishing, route decisions, wallet movement,
                governance queues, and marketplace reporting.
              </p>
            </div>
            <StatusBadge label={openReviews.length || openDisputes.length ? "Governance watch" : "Operations"} tone={openReviews.length || openDisputes.length ? "warning" : "success"} />
          </section>

          <section className="panel" id="distribution-scope">
            <div className="panel-header">
              <div>
                <PanelTitle
                  help="Sets the tenant context for marketplace reporting and distribution actions."
                  title="Operations scope"
                />
                <div className="panel-subtitle">Required by marketplace admin and reporting APIs.</div>
              </div>
            </div>
            <div className="panel-body">
              <form className="form-row" onSubmit={submitTenant}>
                <div className="field">
                  <FieldLabel
                    help="The tenant whose distribution marketplace should be loaded, for example FNB."
                    htmlFor="distribution-tenant"
                    label="Tenant code"
                  />
                  <input
                    className="input"
                    id="distribution-tenant"
                    value={tenantCode}
                    onChange={(event) => setTenantCode(event.target.value)}
                  />
                </div>
                <button className="button" type="submit">
                  Load operations
                </button>
              </form>
            </div>
          </section>
        </>
      )}

      {mode === "operations" ? (
        <>

      <section className="marketplace-command-grid">
        <div className="marketplace-command-card primary">
          <div className="marketplace-command-card-top">
            <div>
              <div className="marketplace-command-kicker">Operations layer</div>
              <h2>Route producer demand to trusted distributors.</h2>
              <p>
                Admin controls remain available for eligibility, publishing, routing, wallet movement, and governance.
              </p>
            </div>
            <StatusBadge label={openReviews.length || openDisputes.length ? "Governance watch" : "Stable"} tone={openReviews.length || openDisputes.length ? "warning" : "success"} />
          </div>
          <div className="marketplace-command-metrics">
            <SummaryItem label="Routed offers" value={routedOfferCount} />
            <SummaryItem label="Draft demand" value={draftOpportunityCount} />
            <SummaryItem label="Wallet exposure" value={walletExposureAmount.toFixed(2)} />
            <SummaryItem label="Open queues" value={openReviews.length + openDisputes.length} />
          </div>
        </div>

        <div className="marketplace-command-card">
          <div className="panel-header compact">
            <div>
              <PanelTitle
                help="Shows the operating sequence for marketplace admins and where each action is performed on this page."
                title="Operator action map"
              />
              <div className="panel-subtitle">Move top to bottom before scaling demand.</div>
            </div>
          </div>
          <div className="marketplace-action-map">
            <MarketplaceActionMapRow label="Confirm distributor eligibility" value="Activate, suspend, or terminate distributor participation." target="Distributor lifecycle" tone={activeDistributorCount ? "success" : "warning"} />
            <MarketplaceActionMapRow label="Publish producer demand" value="Move opportunities from draft into the marketplace." target="Opportunity actions" tone={draftOpportunityCount ? "warning" : "success"} />
            <MarketplaceActionMapRow label="Work routed offers" value="Accept or decline matched opportunity-distributor routes." target="Route actions" tone={routedOfferCount ? "info" : "success"} />
            <MarketplaceActionMapRow label="Clear governance queues" value="Resolve compliance reviews, disputes, and governance audit work." target="Governance queue" tone={openReviews.length || openDisputes.length ? "warning" : "success"} />
          </div>
        </div>
      </section>

      <JourneyTracker
        badge={distributionGuidance.badge}
        currentCopy={distributionGuidance.copy}
        currentTitle={distributionGuidance.title}
        steps={distributionGuidance.steps}
        subtitle="Step-by-step path from marketplace readiness through routing and governance."
        title="Distribution journey"
        tone={distributionGuidance.tone}
      />

      <section className="panel" id="distribution-distributor-lifecycle">
        <div className="panel-header">
          <div>
            <PanelTitle
              help="Controls whether a distributor can participate in the marketplace."
              title="Distributor lifecycle"
            />
            <div className="panel-subtitle">Activate, suspend, or terminate distributor participation.</div>
          </div>
          <StatusBadge label={selectedDistributorStatus} tone={statusTone(selectedDistributorStatus)} />
        </div>
        <div className="panel-body">
          <div className="action-select-row">
            <div className="field">
              <FieldLabel
                help="Choose the distributor whose marketplace status you want to change."
                htmlFor="distribution-distributor-action"
                label="Distributor"
              />
              <select
                className="input"
                id="distribution-distributor-action"
                value={selectedDistributorId}
                onChange={(event) => setSelectedDistributorId(event.target.value)}
              >
                {distributors.length ? null : <option value="">No distributors returned</option>}
                {distributors.map((distributor) => {
                  const distributorId = getValue(distributor, ["distributor_id", "id"], "");
                  return (
                    <option key={distributorId} value={distributorId}>
                      {distributorLabel(distributor)}
                    </option>
                  );
                })}
              </select>
            </div>
          </div>
          <div className="action-button-row">
            <form onSubmit={submitActivateDistributor}>
              <button
                className="button"
                disabled={selectedDistributorStatus === "ACTIVE" || selectedDistributorStatus === "TERMINATED" || actionLoading !== null}
                type="submit"
              >
                <Send size={16} />
                Activate
              </button>
            </form>
            <form onSubmit={submitSuspendDistributor}>
              <button
                className="button secondary"
                disabled={selectedDistributorStatus !== "ACTIVE" || actionLoading !== null}
                type="submit"
              >
                <XCircle size={16} />
                Suspend
              </button>
            </form>
            <form onSubmit={submitTerminateDistributor}>
              <button
                className="button secondary"
                disabled={selectedDistributorStatus === "TERMINATED" || selectedDistributorStatus === "-" || actionLoading !== null}
                type="submit"
              >
                <XCircle size={16} />
                Terminate
              </button>
            </form>
          </div>
          <SelectedDistributorSummary distributor={selectedDistributor} />
          <ActionGuardrail
            badge={distributorGuard.badge}
            tone={distributorGuard.tone}
            title={distributorGuard.title}
            copy={distributorGuard.copy}
            items={distributorGuard.items}
          />
        </div>
      </section>

      <section className="grid-2">
        <div className="panel" id="distribution-wallet-operations">
          <div className="panel-header">
            <div>
              <PanelTitle
                help="Moves money through a distributor wallet: credit earnings, hold funds, release holds, pay out, or reverse earnings."
                title="Distributor wallet operations"
              />
              <div className="panel-subtitle">Controlled balance movements for selected distributor wallets.</div>
            </div>
            <StatusBadge label={selectedWallet ? getValue(selectedWallet, ["status"]) : "-"} tone={statusTone(selectedWallet ? getValue(selectedWallet, ["status"]) : "-")} />
          </div>
          <div className="panel-body">
            <div className="wallet-action-form">
              <div className="field">
                <FieldLabel
                  help="Choose the distributor wallet that should receive the movement."
                  htmlFor="distribution-wallet-action"
                  label="Wallet"
                />
                <select
                  className="input"
                  id="distribution-wallet-action"
                  value={selectedWalletId}
                  onChange={(event) => setSelectedWalletId(event.target.value)}
                >
                  {wallets.length ? null : <option value="">No wallets returned</option>}
                  {wallets.map((wallet) => {
                    const walletId = getValue(wallet, ["wallet_id", "id"], "");
                    return (
                      <option key={walletId} value={walletId}>
                        {walletLabel(wallet)}
                      </option>
                    );
                  })}
                </select>
              </div>
              <div className="field">
                <FieldLabel
                  help="The positive amount to move through the selected wallet."
                  htmlFor="wallet-action-amount"
                  label="Amount"
                />
                <input
                  className="input"
                  id="wallet-action-amount"
                  value={walletAmount}
                  onChange={(event) => setWalletAmount(event.target.value)}
                />
              </div>
              <div className="field">
                <FieldLabel
                  help="Optional reference used to tie this movement back to another business event."
                  htmlFor="wallet-action-correlation"
                  label="Correlation"
                />
                <input
                  className="input"
                  id="wallet-action-correlation"
                  placeholder="Optional reference"
                  value={walletCorrelationId}
                  onChange={(event) => setWalletCorrelationId(event.target.value)}
                />
              </div>
            </div>
            <div className="action-button-row">
              <form onSubmit={submitWalletCredit}>
                <button className="button" disabled={!canCreditWallet || actionLoading !== null} type="submit">Credit</button>
              </form>
              <form onSubmit={submitWalletHold}>
                <button className="button secondary" disabled={!canHoldWallet || actionLoading !== null} type="submit">Hold</button>
              </form>
              <form onSubmit={submitWalletReleaseHold}>
                <button className="button secondary" disabled={!canReleaseWalletHold || actionLoading !== null} type="submit">Release hold</button>
              </form>
              <form onSubmit={submitWalletPayout}>
                <button className="button secondary" disabled={!canPayoutWallet || actionLoading !== null} type="submit">Payout</button>
              </form>
              <form onSubmit={submitWalletReverse}>
                <button className="button secondary" disabled={!canReverseWallet || actionLoading !== null} type="submit">Reverse</button>
              </form>
            </div>
            <div className="field-hint approval-hint">
              {walletActionHint(selectedWalletStatus, walletMovementAmount, selectedWalletAvailable, selectedWalletHeld)}
            </div>
            <SelectedWalletSummary wallet={selectedWallet} />
            <ActionGuardrail
              badge={walletGuard.badge}
              tone={walletGuard.tone}
              title={walletGuard.title}
              copy={walletGuard.copy}
              items={walletGuard.items}
            />
          </div>
        </div>
        <div className="panel" id="distribution-wallet-ledger">
          <div className="panel-header">
            <div>
              <PanelTitle
                help="Shows the latest balance movements recorded for the selected wallet."
                title="Wallet ledger"
              />
              <div className="panel-subtitle">Recent wallet movement history.</div>
            </div>
          </div>
          <DataTable
            emptyText="No wallet ledger entries returned."
            rows={walletLedger}
            columns={[
              { key: "type", header: "Type", render: (row) => getValue(row, ["transaction_type"]) },
              { key: "amount", header: "Amount", render: (row) => getValue(row, ["amount"]) },
              { key: "before", header: "Before", render: (row) => getValue(row, ["balance_before"]) },
              { key: "after", header: "After", render: (row) => getValue(row, ["balance_after"]) },
              { key: "created", header: "Created", render: (row) => <span className="mono">{getValue(row, ["created_at"])}</span> },
            ]}
          />
        </div>
      </section>

      <section className="grid-2">
        <div className="panel" id="distribution-marketplace-overview">
          <div className="panel-header">
            <div>
              <PanelTitle
                help="A top-level view of supply, demand, routing, commission, wallet, and governance signals."
                title="Marketplace overview"
              />
              <div className="panel-subtitle">Supply, demand, routing, wallet, and governance position.</div>
            </div>
            <GitPullRequestArrow size={18} />
          </div>
          <div className="panel-body">
            <SummaryGrid
              items={[
                ["Active distributors", getNestedValue(overview, ["distributors", "active_count"])],
                ["Published opportunities", getNestedValue(overview, ["opportunities", "published_count"])],
                ["Accepted routes", getNestedValue(overview, ["routes", "accepted_count"])],
                ["Linked journeys", getNestedValue(overview, ["conversions", "linked_count"])],
                ["Completed outcomes", getNestedValue(overview, ["conversions", "completed_count"])],
                ["Completion rate", getNestedValue(overview, ["conversions", "completion_rate"])],
                ["Total journeys", getNestedValue(overview, ["conversions", "total_referral_count"])],
                ["Unlinked journeys", getNestedValue(overview, ["conversions", "unlinked_count"])],
                ["Attribution rate", getNestedValue(overview, ["conversions", "attribution_rate"])],
                ["Commission value", getNestedValue(overview, ["commissions", "total_commission_amount"])],
                ["Wallet balance", getNestedValue(overview, ["wallets", "current_balance"])],
                ["Open disputes", getNestedValue(overview, ["governance", "open_dispute_count"])],
              ]}
            />
          </div>
        </div>
        <div className="panel" id="distribution-governance-signal">
          <div className="panel-header">
            <div>
              <PanelTitle
                help="Shows whether compliance reviews, disputes, or governance actions need attention."
                title="Governance signal"
              />
              <div className="panel-subtitle">Compliance, dispute, and governance summary.</div>
            </div>
          </div>
          <div className="panel-body">
            <StatusList
              title="Compliance reviews"
              rows={asArrayFromKey(governanceReport, "compliance_reviews")}
              labelKeys={["status", "action_type"]}
            />
            <StatusList
              title="Disputes"
              rows={asArrayFromKey(governanceReport, "disputes")}
              labelKeys={["status", "action_type"]}
            />
            <StatusList
              title="Governance actions"
              rows={asArrayFromKey(governanceReport, "governance_actions")}
              labelKeys={["action_type", "status"]}
            />
          </div>
        </div>
      </section>

      <section className="grid-2">
        <div className="panel" id="distribution-attribution-exceptions">
          <div className="panel-header">
            <div>
              <PanelTitle
                help="Customer journeys that are not linked to an accepted marketplace route cannot be trusted for route ROI or settlement attribution."
                title="Attribution exceptions"
              />
              <div className="panel-subtitle">Customer journeys that need route attribution before reporting is trusted.</div>
            </div>
            <StatusBadge
              label={`${formatDisplay(getNestedValue(attributionExceptions, ["count"], attributionExceptionRows.length))} open`}
              tone={attributionExceptionRows.length ? "warning" : "success"}
            />
          </div>
          <div className="panel-body">
            <ActionGuardrail
              badge={attributionGuard.badge}
              tone={attributionGuard.tone}
              title={attributionGuard.title}
              copy={attributionGuard.copy}
              items={attributionGuard.items}
              label="Attribution readiness"
            />
            <DataTable
              emptyText="No attribution exceptions returned."
              rows={attributionExceptionRows}
              columns={[
                {
                  key: "referral",
                  header: "Journey",
                  render: (row) => <span className="mono">{getValue(row, ["referral_track_id"])}</span>,
                },
                { key: "distributor", header: "Distributor", render: (row) => getValue(row, ["distributor_code"], "Unknown") },
                { key: "product", header: "Product", render: (row) => productLabel(row) },
                { key: "status", header: "Status", render: (row) => <StatusBadge label={getValue(row, ["display_status", "status"])} tone={statusTone(getValue(row, ["status"]))} /> },
                { key: "progress", header: "Progress", render: (row) => formatDisplay(getValue(row, ["progress_percent"], "0")) },
                { key: "next", header: "Next step", render: (row) => getValue(row, ["next_milestone"], "Link to accepted route") },
              ]}
            />
          </div>
        </div>
        <div className="panel" id="distribution-attribution-next-step">
          <div className="panel-header">
            <div>
              <PanelTitle
                help="Shows the operational path for cleaning attribution before settlement or ROI review."
                title="Exception handling"
              />
              <div className="panel-subtitle">What must happen before these journeys support network reporting.</div>
            </div>
          </div>
          <div className="panel-body">
            <SummaryGrid
              items={[
                ["Exception count", getNestedValue(attributionExceptions, ["count"], attributionExceptionRows.length)],
                ["Completed but unlinked", getNestedValue(attributionExceptions, ["completed_count"], 0)],
                ["Network attribution", getNestedValue(overview, ["conversions", "attribution_rate"])],
                ["Trusted linked journeys", getNestedValue(overview, ["conversions", "linked_count"])],
              ]}
            />
            <StatusList
              title="Operating path"
              rows={[
                { status: "Find accepted route", count: "Match distributor, product, and timing." },
                { status: "Link journey", count: "Use the distributor journey-link flow once the route is confirmed." },
                { status: "Rerun reporting", count: "Refresh the Command Centre before ROI or settlement review." },
              ]}
              labelKeys={["status"]}
            />
          </div>
        </div>
      </section>

      <section className="grid-2">
        <div className="panel" id="distribution-opportunity-actions">
          <div className="panel-header">
            <div>
              <PanelTitle
                help="Controls whether sponsor-funded opportunities are available for routing."
                title="Opportunity actions"
              />
              <div className="panel-subtitle">Publish, close, or reopen an opportunity by lifecycle status.</div>
            </div>
            <StatusBadge label={selectedOpportunityStatus} tone={statusTone(selectedOpportunityStatus)} />
          </div>
          <div className="panel-body">
            <div className="action-select-row">
              <div className="field">
                <FieldLabel
                  help="Choose the opportunity whose lifecycle state you want to change."
                  htmlFor="distribution-opportunity-action"
                  label="Opportunity"
                />
                <select
                  className="input"
                  id="distribution-opportunity-action"
                  value={selectedOpportunityId}
                  onChange={(event) => setSelectedOpportunityId(event.target.value)}
                >
                  {opportunities.length ? null : <option value="">No opportunities returned</option>}
                  {opportunities.map((opportunity) => {
                    const opportunityId = getValue(opportunity, ["opportunity_id", "id"], "");
                    return (
                      <option key={opportunityId} value={opportunityId}>
                        {opportunityLabel(opportunity)}
                      </option>
                    );
                  })}
                </select>
              </div>
            </div>
            <div className="action-button-row">
              <form onSubmit={submitPublish}>
                <button
                  className="button"
                  disabled={selectedOpportunityStatus !== "DRAFT" || actionLoading !== null}
                  type="submit"
                >
                  <Send size={16} />
                  Publish
                </button>
              </form>
              <form onSubmit={submitClose}>
                <button
                  className="button secondary"
                  disabled={selectedOpportunityStatus !== "PUBLISHED" || actionLoading !== null}
                  type="submit"
                >
                  <XCircle size={16} />
                  Close
                </button>
              </form>
              <form onSubmit={submitReopen}>
                <button
                  className="button secondary"
                  disabled={selectedOpportunityStatus !== "CLOSED" || actionLoading !== null}
                  type="submit"
                >
                  <Undo2 size={16} />
                  Reopen
                </button>
              </form>
            </div>
            <SelectedOpportunitySummary opportunity={selectedOpportunity} />
            <ActionGuardrail
              badge={opportunityGuard.badge}
              tone={opportunityGuard.tone}
              title={opportunityGuard.title}
              copy={opportunityGuard.copy}
              items={opportunityGuard.items}
            />
          </div>
        </div>

        <div className="panel" id="distribution-route-actions">
          <div className="panel-header">
            <div>
              <PanelTitle
                help="Controls a matched offer route between an opportunity and a distributor."
                title="Route actions"
              />
              <div className="panel-subtitle">Accept or decline offer routes that are still routed.</div>
            </div>
            <StatusBadge label={selectedRouteStatus} tone={statusTone(selectedRouteStatus)} />
          </div>
          <div className="panel-body">
            <div className="action-select-row">
              <div className="field">
                <FieldLabel
                  help="Choose the matched route to accept or decline. Only routed items can be actioned."
                  htmlFor="distribution-route-action"
                  label="Route"
                />
                <select
                  className="input"
                  id="distribution-route-action"
                  value={selectedRouteId}
                  onChange={(event) => setSelectedRouteId(event.target.value)}
                >
                  {routes.length ? null : <option value="">No routes returned</option>}
                  {routes.map((route) => {
                    const routeId = getValue(route, ["route_id", "id"], "");
                    return (
                      <option key={routeId} value={routeId}>
                        {routeLabel(route)}
                      </option>
                    );
                  })}
                </select>
              </div>
            </div>
            <div className="action-button-row">
              <form onSubmit={submitAcceptRoute}>
                <button
                  className="button"
                  disabled={selectedRouteStatus !== "ROUTED" || actionLoading !== null}
                  type="submit"
                >
                  <Send size={16} />
                  Accept
                </button>
              </form>
              <form onSubmit={submitDeclineRoute}>
                <button
                  className="button secondary"
                  disabled={selectedRouteStatus !== "ROUTED" || actionLoading !== null}
                  type="submit"
                >
                  <XCircle size={16} />
                  Decline
                </button>
              </form>
            </div>
            <SelectedRouteSummary route={selectedRoute} />
            <ActionGuardrail
              badge={routeGuard.badge}
              tone={routeGuard.tone}
              title={routeGuard.title}
              copy={routeGuard.copy}
              items={routeGuard.items}
            />
          </div>
        </div>
      </section>

      <section className="grid-3">
        <KpiCard label="Compliance reviews" value={complianceReviews.length} footnote="Latest review records" icon={ShieldCheck} />
        <KpiCard label="Open disputes" value={openDisputes.length} footnote="Routes needing attention" icon={GitPullRequestArrow} />
        <KpiCard label="Governance audit" value={governanceAudit.length} footnote="Recent control actions" icon={Users} />
      </section>

      <section className="grid-2">
        <div className="panel" id="distribution-compliance-reviews">
          <div className="panel-header">
            <div>
              <PanelTitle
                help="Opens or completes compliance checks for a distributor before they continue operating in the marketplace."
                title="Compliance reviews"
              />
              <div className="panel-subtitle">Create a review, then complete it when the outcome is known.</div>
            </div>
          </div>
          <div className="panel-body">
            <form className="governance-form" onSubmit={submitCreateComplianceReview}>
              <div className="field">
                <FieldLabel
                  help="The distributor who needs a compliance review."
                  htmlFor="compliance-review-distributor"
                  label="Distributor"
                />
                <select
                  className="input"
                  id="compliance-review-distributor"
                  value={selectedDistributorId}
                  onChange={(event) => setSelectedDistributorId(event.target.value)}
                >
                  {distributors.length ? null : <option value="">No distributors returned</option>}
                  {distributors.map((distributor) => {
                    const distributorId = getValue(distributor, ["distributor_id", "id"], "");
                    return (
                      <option key={distributorId} value={distributorId}>
                        {distributorLabel(distributor)}
                      </option>
                    );
                  })}
                </select>
              </div>
              <div className="field">
                <FieldLabel
                  help="The type of review being performed, such as KYC, contract, risk, or limits."
                  htmlFor="compliance-review-type"
                  label="Review type"
                />
                <input
                  className="input"
                  id="compliance-review-type"
                  value={reviewType}
                  onChange={(event) => setReviewType(event.target.value)}
                />
              </div>
              <div className="field">
                <FieldLabel
                  help="The person or team responsible for the review."
                  htmlFor="compliance-reviewer"
                  label="Reviewer"
                />
                <input
                  className="input"
                  id="compliance-reviewer"
                  value={reviewer}
                  onChange={(event) => setReviewer(event.target.value)}
                />
              </div>
              <button className="button" disabled={!canOpenComplianceReview || actionLoading !== null} type="submit">
                Open review
              </button>
            </form>

            <form className="governance-form action-result" onSubmit={submitCompleteComplianceReview}>
              <div className="field">
                <FieldLabel
                  help="Only open reviews can be completed from this control."
                  htmlFor="compliance-review-complete"
                  label="Open review"
                />
                <select
                  className="input"
                  id="compliance-review-complete"
                  value={selectedReviewId}
                  onChange={(event) => setSelectedReviewId(event.target.value)}
                >
                  {openReviews.length ? null : <option value="">No open reviews returned</option>}
                  {openReviews.map((review) => {
                    const reviewId = getValue(review, ["review_id", "id"], "");
                    return (
                      <option key={reviewId} value={reviewId}>
                        {reviewLabel(review)}
                      </option>
                    );
                  })}
                </select>
              </div>
              <div className="field">
                <FieldLabel
                  help="The final outcome recorded against the review."
                  htmlFor="compliance-review-result"
                  label="Result"
                />
                <select
                  className="input"
                  id="compliance-review-result"
                  value={reviewResult}
                  onChange={(event) => setReviewResult(event.target.value)}
                >
                  <option value="PASSED">PASSED</option>
                  <option value="FAILED">FAILED</option>
                  <option value="CONDITIONALLY_APPROVED">CONDITIONALLY_APPROVED</option>
                </select>
              </div>
              <div className="field">
                <FieldLabel
                  help="Optional note stored with the review action."
                  htmlFor="compliance-review-notes"
                  label="Notes"
                />
                <input
                  className="input"
                  id="compliance-review-notes"
                  value={reviewNotes}
                  onChange={(event) => setReviewNotes(event.target.value)}
                />
              </div>
              <button className="button secondary" disabled={!canCompleteComplianceReview || actionLoading !== null} type="submit">
                Complete review
              </button>
            </form>
            <ActionGuardrail
              badge={complianceGuard.badge}
              tone={complianceGuard.tone}
              title={complianceGuard.title}
              copy={complianceGuard.copy}
              items={complianceGuard.items}
            />
          </div>
        </div>

        <div className="panel" id="distribution-route-disputes">
          <div className="panel-header">
            <div>
              <PanelTitle
                help="Creates and resolves disputes against offer routes when routing, acceptance, or commission outcomes are contested."
                title="Route disputes"
              />
              <div className="panel-subtitle">Track route problems without losing the audit trail.</div>
            </div>
          </div>
          <div className="panel-body">
            <form className="governance-form" onSubmit={submitCreateDispute}>
              <div className="field">
                <FieldLabel
                  help="The offer route that is being disputed."
                  htmlFor="route-dispute-route"
                  label="Route"
                />
                <select
                  className="input"
                  id="route-dispute-route"
                  value={selectedRouteId}
                  onChange={(event) => setSelectedRouteId(event.target.value)}
                >
                  {routes.length ? null : <option value="">No routes returned</option>}
                  {routes.map((route) => {
                    const routeId = getValue(route, ["route_id", "id"], "");
                    return (
                      <option key={routeId} value={routeId}>
                        {routeLabel(route)}
                      </option>
                    );
                  })}
                </select>
              </div>
              <div className="field">
                <FieldLabel
                  help="The user, team, or process that raised the dispute."
                  htmlFor="route-dispute-raised-by"
                  label="Raised by"
                />
                <input
                  className="input"
                  id="route-dispute-raised-by"
                  value={disputeRaisedBy}
                  onChange={(event) => setDisputeRaisedBy(event.target.value)}
                />
              </div>
              <div className="field">
                <FieldLabel
                  help="A short reason code that makes dispute reporting consistent."
                  htmlFor="route-dispute-reason"
                  label="Reason code"
                />
                <input
                  className="input"
                  id="route-dispute-reason"
                  value={disputeReasonCode}
                  onChange={(event) => setDisputeReasonCode(event.target.value)}
                />
              </div>
              <button className="button" disabled={!canCreateDispute || actionLoading !== null} type="submit">
                Create dispute
              </button>
            </form>

            <form className="governance-form action-result" onSubmit={submitResolveDispute}>
              <div className="field">
                <FieldLabel
                  help="Only open disputes can be resolved or rejected here."
                  htmlFor="route-dispute-open"
                  label="Open dispute"
                />
                <select
                  className="input"
                  id="route-dispute-open"
                  value={selectedDisputeId}
                  onChange={(event) => setSelectedDisputeId(event.target.value)}
                >
                  {openDisputes.length ? null : <option value="">No open disputes returned</option>}
                  {openDisputes.map((dispute) => {
                    const disputeId = getValue(dispute, ["dispute_id", "id"], "");
                    return (
                      <option key={disputeId} value={disputeId}>
                        {disputeLabel(dispute)}
                      </option>
                    );
                  })}
                </select>
              </div>
              <div className="field">
                <FieldLabel
                  help="Choose whether the dispute was resolved or rejected."
                  htmlFor="route-dispute-resolution"
                  label="Outcome"
                />
                <select
                  className="input"
                  id="route-dispute-resolution"
                  value={disputeResolutionStatus}
                  onChange={(event) => setDisputeResolutionStatus(event.target.value)}
                >
                  <option value="RESOLVED">RESOLVED</option>
                  <option value="REJECTED">REJECTED</option>
                </select>
              </div>
              <div className="field">
                <FieldLabel
                  help="Optional note captured when creating or resolving the dispute."
                  htmlFor="route-dispute-notes"
                  label="Notes"
                />
                <input
                  className="input"
                  id="route-dispute-notes"
                  value={disputeDescription}
                  onChange={(event) => setDisputeDescription(event.target.value)}
                />
              </div>
              <button className="button secondary" disabled={!canResolveDispute || actionLoading !== null} type="submit">
                Resolve dispute
              </button>
            </form>
            <ActionGuardrail
              badge={disputeGuard.badge}
              tone={disputeGuard.tone}
              title={disputeGuard.title}
              copy={disputeGuard.copy}
              items={disputeGuard.items}
            />
          </div>
        </div>
      </section>

      <section className="panel" id="distribution-governance-action">
        <div className="panel-header">
          <div>
            <PanelTitle
              help="Applies controlled governance decisions to a distributor, with an audit record for every action."
              title="Distributor governance action"
            />
            <div className="panel-subtitle">Suspend, reinstate, terminate, or update limits through the governance path.</div>
          </div>
          <StatusBadge label={selectedDistributorStatus} tone={statusTone(selectedDistributorStatus)} />
        </div>
        <div className="panel-body">
          <form className="governance-action-form" onSubmit={submitGovernanceAction}>
            <div className="field">
              <FieldLabel
                help="The distributor receiving the governance action."
                htmlFor="governance-action-distributor"
                label="Distributor"
              />
              <select
                className="input"
                id="governance-action-distributor"
                value={selectedDistributorId}
                onChange={(event) => setSelectedDistributorId(event.target.value)}
              >
                {distributors.length ? null : <option value="">No distributors returned</option>}
                {distributors.map((distributor) => {
                  const distributorId = getValue(distributor, ["distributor_id", "id"], "");
                  return (
                    <option key={distributorId} value={distributorId}>
                      {distributorLabel(distributor)}
                    </option>
                  );
                })}
              </select>
            </div>
            <div className="field">
              <FieldLabel
                help="The controlled governance action to apply."
                htmlFor="governance-action-type"
                label="Action"
              />
              <select
                className="input"
                id="governance-action-type"
                value={governanceActionType}
                onChange={(event) => setGovernanceActionType(event.target.value)}
              >
                <option value="SUSPEND">SUSPEND</option>
                <option value="REINSTATE">REINSTATE</option>
                <option value="TERMINATE">TERMINATE</option>
                <option value="UPDATE_LIMITS">UPDATE_LIMITS</option>
              </select>
            </div>
            <div className="field">
              <FieldLabel
                help="A consistent reason code for the audit record."
                htmlFor="governance-action-reason"
                label="Reason"
              />
              <input
                className="input"
                id="governance-action-reason"
                value={governanceReasonCode}
                onChange={(event) => setGovernanceReasonCode(event.target.value)}
              />
            </div>
            <div className="field">
              <FieldLabel
                help="The person or team applying the governance action."
                htmlFor="governance-action-actor"
                label="Actor"
              />
              <input
                className="input"
                id="governance-action-actor"
                value={governanceActor}
                onChange={(event) => setGovernanceActor(event.target.value)}
              />
            </div>
            <div className="field">
              <FieldLabel
                help="Optional note stored with the governance audit record."
                htmlFor="governance-action-notes"
                label="Notes"
              />
              <input
                className="input"
                id="governance-action-notes"
                value={governanceNotes}
                onChange={(event) => setGovernanceNotes(event.target.value)}
              />
            </div>
            <button className="button" disabled={!canApplyGovernanceAction || actionLoading !== null} type="submit">
              Apply action
            </button>
          </form>
          <div className="field-hint approval-hint">
            {governanceActionHint(selectedDistributorStatus, governanceActionType)}
          </div>
          <ActionGuardrail
            badge={governanceGuard.badge}
            tone={governanceGuard.tone}
            title={governanceGuard.title}
            copy={governanceGuard.copy}
            items={governanceGuard.items}
          />
        </div>
      </section>

      {actionError ? <ErrorPanel error={actionError} /> : null}
      {actionResult ? <DistributionActionResult payload={actionResult} /> : null}

      <section className="grid-2">
        <div className="panel">
          <div className="panel-header">
            <div>
              <PanelTitle
                help="Review history by distributor, including open and completed outcomes."
                title="Compliance review records"
              />
              <div className="panel-subtitle">Latest compliance reviews returned by the API.</div>
            </div>
          </div>
          <DataTable
            emptyText="No compliance reviews returned."
            rows={complianceReviews}
            columns={[
              { key: "review", header: "Review", render: (row) => <span className="mono">{getValue(row, ["review_id"])}</span> },
              { key: "distributor", header: "Distributor", render: (row) => getValue(row, ["distributor_code", "distributor_id"]) },
              { key: "type", header: "Type", render: (row) => getValue(row, ["review_type"]) },
              {
                key: "status",
                header: "Status",
                render: (row) => {
                  const status = getValue(row, ["review_status"]);
                  return <StatusBadge label={status} tone={statusTone(status)} />;
                },
              },
              { key: "result", header: "Result", render: (row) => getValue(row, ["review_result"], "-") },
            ]}
          />
        </div>

        <div className="panel">
          <div className="panel-header">
            <div>
              <PanelTitle
                help="Dispute history for routes, including open, resolved, and rejected outcomes."
                title="Dispute records"
              />
              <div className="panel-subtitle">Latest marketplace disputes returned by the API.</div>
            </div>
          </div>
          <DataTable
            emptyText="No disputes returned."
            rows={disputes}
            columns={[
              { key: "dispute", header: "Dispute", render: (row) => <span className="mono">{getValue(row, ["dispute_id"])}</span> },
              { key: "route", header: "Route", render: (row) => <span className="mono">{getValue(row, ["route_id"], "-")}</span> },
              { key: "reason", header: "Reason", render: (row) => getValue(row, ["reason_code"]) },
              { key: "raised", header: "Raised by", render: (row) => getValue(row, ["raised_by"]) },
              {
                key: "status",
                header: "Status",
                render: (row) => {
                  const status = getValue(row, ["dispute_status"]);
                  return <StatusBadge label={status} tone={statusTone(status)} />;
                },
              },
            ]}
          />
        </div>
      </section>

      <section className="panel" id="distribution-governance-audit">
        <div className="panel-header">
          <div>
            <PanelTitle
              help="Immutable governance action trail for distributor, review, and dispute decisions."
              title="Governance audit"
            />
            <div className="panel-subtitle">Latest governance audit entries for this tenant.</div>
          </div>
        </div>
        <DataTable
          emptyText="No governance audit entries returned."
          rows={governanceAudit}
          columns={[
            { key: "action", header: "Action", render: (row) => getValue(row, ["action_type"]) },
            { key: "distributor", header: "Distributor", render: (row) => <span className="mono">{getValue(row, ["distributor_id"], "-")}</span> },
            { key: "reason", header: "Reason", render: (row) => getValue(row, ["reason_code"], "-") },
            { key: "actor", header: "Actor", render: (row) => getValue(row, ["actor"], "-") },
            { key: "created", header: "Created", render: (row) => <span className="mono">{getValue(row, ["created_at"])}</span> },
          ]}
        />
      </section>

      <section className="panel" id="distribution-opportunity-report">
        <div className="panel-header">
          <div>
            <PanelTitle
              help="Performance view for opportunities, including budget, routing outcomes, linked customer journeys, and completed outcomes."
              title="Opportunity report"
            />
            <div className="panel-subtitle">Performance summary for producer-funded opportunities, routed demand, and customer outcomes.</div>
          </div>
        </div>
        <DataTable
          rows={asArray(opportunityReport)}
          columns={[
            {
              key: "opportunity",
              header: "Opportunity",
              render: (row) => (
                <div>
                  <div>{getValue(row, ["title", "opportunity_name", "name"])}</div>
                  <div className="table-subtext mono">{getValue(row, ["opportunity_code", "opportunity_id"])}</div>
                </div>
              ),
            },
            { key: "sponsor", header: "Sponsor", render: (row) => getValue(row, ["sponsor_code", "sponsor_name"]) },
            { key: "campaign", header: "Campaign", render: (row) => <span className="mono">{getValue(row, ["campaign_code"])}</span> },
            { key: "budget", header: "Budget", render: (row) => getValue(row, ["total_budget", "budget"]) },
            { key: "remaining", header: "Remaining", render: (row) => getValue(row, ["remaining_budget"]) },
            { key: "accepted", header: "Accepted", render: (row) => getValue(row, ["accepted_count"], "0") },
            { key: "journeys", header: "Journeys", render: (row) => getValue(row, ["conversion_count"], "0") },
            { key: "completed", header: "Completed", render: (row) => getValue(row, ["completed_conversion_count"], "0") },
            { key: "completion", header: "Completion", render: (row) => getValue(row, ["conversion_completion_rate"], "0.0000") },
            {
              key: "status",
              header: "Status",
              render: (row) => {
                const status = getValue(row, ["opportunity_status", "status"]);
                return <StatusBadge label={status} tone={statusTone(status)} />;
              },
            },
          ]}
        />
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <PanelTitle
              help="Distributor wallets hold earned, held, paid out, and reversed balances."
              title="Distributor wallets"
            />
            <div className="panel-subtitle">Wallet balances by distributor and currency.</div>
          </div>
        </div>
        <DataTable
          emptyText="No distributor wallets returned."
          rows={wallets}
          columns={[
            { key: "wallet", header: "Wallet", render: (row) => <span className="mono">{getValue(row, ["wallet_id"])}</span> },
            { key: "distributor", header: "Distributor", render: (row) => getValue(row, ["distributor_code", "distributor_id"]) },
            { key: "currency", header: "Currency", render: (row) => getValue(row, ["currency"]) },
            { key: "current", header: "Current", render: (row) => getValue(row, ["current_balance"], "0.00") },
            { key: "available", header: "Available", render: (row) => getValue(row, ["available_balance"], "0.00") },
            { key: "held", header: "Held", render: (row) => getValue(row, ["held_balance"], "0.00") },
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
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <PanelTitle
              help="Performance view for distributors, including offer decisions, linked customer journeys, completed outcomes, and earnings."
              title="Distributor report"
            />
            <div className="panel-subtitle">Distributor performance across routed offers, customer journeys, and earnings.</div>
          </div>
        </div>
        <DataTable
          rows={asArray(distributorReport)}
          columns={[
            {
              key: "distributor",
              header: "Distributor",
              render: (row) => (
                <div>
                  <div>{getValue(row, ["distributor_name", "display_name", "name"])}</div>
                  <div className="table-subtext mono">{getValue(row, ["distributor_code", "distributor_id"])}</div>
                </div>
              ),
            },
            { key: "type", header: "Type", render: (row) => getValue(row, ["distributor_type", "type"]) },
            { key: "routed", header: "Routed", render: (row) => getValue(row, ["routed_count"]) },
            { key: "accepted", header: "Accepted", render: (row) => getValue(row, ["accepted_count"]) },
            { key: "declined", header: "Declined", render: (row) => getValue(row, ["declined_count"]) },
            { key: "journeys", header: "Journeys", render: (row) => getValue(row, ["conversion_count"], "0") },
            { key: "completed", header: "Completed", render: (row) => getValue(row, ["completed_conversion_count"], "0") },
            { key: "completion", header: "Completion", render: (row) => getValue(row, ["conversion_completion_rate"], "0.0000") },
            { key: "commission", header: "Commission", render: (row) => getValue(row, ["total_commission_amount", "commission_amount"]) },
            {
              key: "status",
              header: "Status",
              render: (row) => {
                const status = getValue(row, ["status", "lifecycle_status"]);
                return <StatusBadge label={status} tone={statusTone(status)} />;
              },
            },
          ]}
        />
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <PanelTitle
              help="Supply-side participants who can receive and act on routed offers."
              title="Distributors"
            />
            <div className="panel-subtitle">Supply-side participants available to the marketplace.</div>
          </div>
        </div>
        <DataTable
          rows={distributors}
          columns={[
            { key: "code", header: "Distributor", render: (row) => <span className="mono">{getValue(row, ["distributor_code", "code", "distributor_id", "id"])}</span> },
            { key: "name", header: "Name", render: (row) => getValue(row, ["display_name", "name", "legal_name"]) },
            { key: "type", header: "Type", render: (row) => getValue(row, ["distributor_type", "type"]) },
            { key: "region", header: "Region", render: (row) => getValue(row, ["region", "country", "province"]) },
            {
              key: "status",
              header: "Status",
              render: (row) => {
                const status = getValue(row, ["status", "lifecycle_status"]);
                return <StatusBadge label={status} tone={statusTone(status)} />;
              },
            },
          ]}
        />
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <PanelTitle
              help="Sponsor-funded demand that can be published and routed to distributors."
              title="Opportunities"
            />
            <div className="panel-subtitle">Sponsor-funded demand available for routing.</div>
          </div>
        </div>
        <DataTable
          rows={opportunities}
          columns={[
            { key: "opportunity", header: "Opportunity", render: (row) => <span className="mono">{getValue(row, ["opportunity_id", "id"])}</span> },
            { key: "name", header: "Name", render: (row) => getValue(row, ["name", "opportunity_name", "title"]) },
            { key: "sponsor", header: "Sponsor", render: (row) => getValue(row, ["sponsor_code", "sponsor_name"]) },
            { key: "reward", header: "Reward", render: (row) => getValue(row, ["reward_amount", "commission_amount", "reward"]) },
            {
              key: "status",
              header: "Status",
              render: (row) => {
                const status = getValue(row, ["status", "opportunity_status"]);
                return <StatusBadge label={status} tone={statusTone(status)} />;
              },
            },
          ]}
        />
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <PanelTitle
              help="Matches between opportunities and distributors, including route status and score."
              title="Offer routes"
            />
            <div className="panel-subtitle">Matched routes between opportunities and distributors.</div>
          </div>
        </div>
        <DataTable
          rows={routes}
          columns={[
            { key: "route", header: "Route", render: (row) => <span className="mono">{getValue(row, ["route_id", "id"])}</span> },
            { key: "opportunity", header: "Opportunity", render: (row) => getValue(row, ["opportunity_id", "opportunity_name"]) },
            { key: "distributor", header: "Distributor", render: (row) => getValue(row, ["distributor_code", "distributor_id"]) },
            { key: "score", header: "Score", render: (row) => getValue(row, ["match_score", "score"]) },
            {
              key: "status",
              header: "Status",
              render: (row) => {
                const status = getValue(row, ["status", "route_status"]);
                return <StatusBadge label={status} tone={statusTone(status)} />;
              },
            },
          ]}
        />
      </section>
        </>
      ) : null}
    </>
  );
}

function SelectedOpportunitySummary({ opportunity }: { opportunity?: Record<string, unknown> }) {
  if (!opportunity) {
    return <div className="state-panel">No opportunity selected.</div>;
  }

  return (
    <SummaryGrid
      actionResult
      items={[
        ["Sponsor", getValue(opportunity, ["sponsor_code", "sponsor_name"])],
        ["Budget", getValue(opportunity, ["total_budget"], "0.00")],
        ["Remaining", getValue(opportunity, ["remaining_budget"], "0.00")],
      ]}
    />
  );
}

function SelectedDistributorSummary({ distributor }: { distributor?: Record<string, unknown> }) {
  if (!distributor) {
    return <div className="state-panel">No distributor selected.</div>;
  }

  return (
    <SummaryGrid
      actionResult
      items={[
        ["Code", getValue(distributor, ["distributor_code", "code"])],
        ["Type", getValue(distributor, ["distributor_type", "type"])],
        ["Regions", formatListValue(distributor, "regions")],
      ]}
    />
  );
}

function SelectedWalletSummary({ wallet }: { wallet?: Record<string, unknown> }) {
  if (!wallet) {
    return <div className="state-panel">No wallet selected.</div>;
  }

  return (
    <SummaryGrid
      actionResult
      items={[
        ["Current", getValue(wallet, ["current_balance"], "0.00")],
        ["Available", getValue(wallet, ["available_balance"], "0.00")],
        ["Held", getValue(wallet, ["held_balance"], "0.00")],
        ["Paid out", getValue(wallet, ["paid_out_balance"], "0.00")],
        ["Reversed", getValue(wallet, ["reversed_balance"], "0.00")],
        ["Currency", getValue(wallet, ["currency"])],
      ]}
    />
  );
}

function SelectedRouteSummary({ route }: { route?: Record<string, unknown> }) {
  if (!route) {
    return <div className="state-panel">No route selected.</div>;
  }

  return (
    <SummaryGrid
      actionResult
      items={[
        ["Opportunity", getValue(route, ["opportunity_id"])],
        ["Distributor", getValue(route, ["distributor_code", "distributor_id"])],
        ["Score", getValue(route, ["route_score", "match_score", "score"], "0")],
      ]}
    />
  );
}

function DistributionActionResult({ payload }: { payload: Record<string, unknown> }) {
  const result = (payload.result && typeof payload.result === "object" ? payload.result : {}) as Record<string, unknown>;
  const distributor = (result.distributor && typeof result.distributor === "object"
    ? result.distributor
    : {}) as Record<string, unknown>;
  const audit = (result.audit && typeof result.audit === "object" ? result.audit : {}) as Record<string, unknown>;
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <h2 className="panel-title">Action result</h2>
          <div className="panel-subtitle">{getValue(payload, ["action"], "Distribution action")} completed.</div>
        </div>
        <StatusBadge label="Updated" tone="success" />
      </div>
      <div className="panel-body">
        <div className="summary-grid">
          <SummaryItem label="Opportunity" value={getValue(result, ["opportunity_code", "opportunity_id"], "-")} />
          <SummaryItem label="Route" value={getValue(result, ["route_id"], "-")} />
          <SummaryItem
            label="Distributor"
            value={getValue(result, ["distributor_code", "distributor_id"], getValue(distributor, ["distributor_code", "distributor_id"], "-"))}
          />
          <SummaryItem label="Review" value={getValue(result, ["review_id"], "-")} />
          <SummaryItem label="Dispute" value={getValue(result, ["dispute_id"], "-")} />
          <SummaryItem label="Audit" value={getValue(audit, ["action_type", "audit_id"], "-")} />
          <SummaryItem
            label="Status"
            value={getValue(
              result,
              ["opportunity_status", "route_status", "review_status", "dispute_status", "status"],
              getValue(distributor, ["status"], "-"),
            )}
          />
        </div>
      </div>
    </section>
  );
}

function MarketplaceActionMapRow({
  label,
  value,
  target,
  tone,
}: {
  label: string;
  value: string;
  target: string;
  tone: "success" | "warning" | "danger" | "info" | "neutral";
}) {
  return (
    <div className="admin-attention-row">
      <div>
        <div className="admin-attention-title">{label}</div>
        <div className="admin-attention-copy">{value}</div>
      </div>
      <StatusBadge label={target} tone={tone} />
    </div>
  );
}

function StatusList({
  title,
  rows,
  labelKeys,
}: {
  title: string;
  rows: Record<string, unknown>[];
  labelKeys: string[];
}) {
  if (!rows.length) {
    return null;
  }

  return (
    <div className="status-list">
      <div className="status-list-title">{title}</div>
      {rows.map((row, index) => {
        const label = getValue(row, labelKeys);
        const count = getValue(row, ["count", "total_count", "event_count"], "0");
        return (
          <div className="status-row" key={`${title}-${index}`}>
            <StatusBadge label={label} tone={statusTone(label)} />
            <span className="status-count">{count}</span>
          </div>
        );
      })}
    </div>
  );
}

function asArrayFromKey(value: unknown, key: string): Record<string, unknown>[] {
  if (!value || typeof value !== "object") {
    return [];
  }

  const found = (value as Record<string, unknown>)[key];
  return Array.isArray(found) ? (found as Record<string, unknown>[]) : [];
}

function getMarketplaceCategories(opportunities: Record<string, unknown>[]): string[] {
  const categories = new Set<string>(["ALL"]);
  opportunities.forEach((opportunity) => categories.add(marketplaceCategory(opportunity)));
  return Array.from(categories).slice(0, 7);
}

function getMarketplaceCards({
  opportunities,
  routes,
  search,
  filter,
  sort,
}: {
  opportunities: Record<string, unknown>[];
  routes: Record<string, unknown>[];
  search: string;
  filter: string;
  sort: string;
}): MarketplaceCard[] {
  const query = search.trim().toLowerCase();
  const cards = opportunities.map((opportunity, index) => toMarketplaceCard(opportunity, routes, index));
  const filtered = cards.filter((card) => {
    const matchesCategory = filter === "ALL" || card.category === filter;
    const matchesSearch = !query || `${card.title} ${card.company} ${card.category} ${card.status}`.toLowerCase().includes(query);
    return matchesCategory && matchesSearch;
  });

  return filtered.sort((left, right) => {
    if (sort === "TRENDING") {
      return right.activeCount - left.activeCount;
    }
    if (sort === "NEW") {
      return right.id.localeCompare(left.id);
    }
    return right.rewardAmount - left.rewardAmount;
  });
}

function toMarketplaceCard(
  opportunity: Record<string, unknown>,
  routes: Record<string, unknown>[],
  index: number,
): MarketplaceCard {
  const id = getValue(opportunity, ["opportunity_id", "id", "opportunity_code"], `OP-${index + 1}`);
  const linkedRoutes = routes.filter((route) => getValue(route, ["opportunity_id", "opportunity_code"]) === id);
  const acceptedRoutes = linkedRoutes.filter((route) => getValue(route, ["route_status", "status"]) === "ACCEPTED").length;
  const category = marketplaceCategory(opportunity);
  const rewardAmount = moneyNumber(getValue(opportunity, ["estimated_reward_amount", "estimated_commission_amount", "reward_amount", "commission_amount", "reward"], String((index + 1) * 75)));
  const conversionScore = numberOrFallback(getValue(opportunity, ["conversion_rate", "conversionRate", "expected_conversion_rate"], ""), [24, 38, 52, 11, 17, 9][index % 6]);
  const activeCount = numberOrFallback(getValue(opportunity, ["active_count", "audience_count", "estimated_audience", "route_count"], ""), [8200, 19000, 31000, 4100, 2600, 1300][index % 6]);

  return {
    id,
    title: getValue(opportunity, ["title", "opportunity_name", "campaign_name", "opportunity_code"], `Campaign ${index + 1}`),
    company: getValue(opportunity, ["sponsor_code", "sponsor_name", "company_name", "producer_code"], "Company demand"),
    category,
    status: getValue(opportunity, ["opportunity_status", "status"], "PUBLISHED"),
    reward: formatCurrencyReward(rewardAmount),
    rewardAmount,
    conversionRate: `${conversionScore}%`,
    conversionScore,
    activeLabel: formatCompactNumber(activeCount),
    activeCount,
    trustRequirement: `Trust ${getValue(opportunity, ["min_trust_score", "trust_score_min"], String(60 + (index % 5) * 5))}+`,
    routeCount: linkedRoutes.length,
    joinedCount: acceptedRoutes,
    tone: ["violet", "amber", "green", "violet", "rose", "blue"][index % 6] as MarketplaceCard["tone"],
  };
}

function marketplaceCategory(opportunity: Record<string, unknown>): string {
  const raw = getValue(opportunity, ["category", "vertical", "product", "product_category", "industry"], "");
  const title = getValue(opportunity, ["title", "opportunity_name", "campaign_name"], "").toLowerCase();
  const combined = `${raw} ${title}`.toLowerCase();
  if (combined.includes("insur") || combined.includes("funeral")) {
    return "Insurance";
  }
  if (combined.includes("telco") || combined.includes("sim") || combined.includes("data")) {
    return "Telco";
  }
  if (combined.includes("retail") || combined.includes("loyal")) {
    return "Retail";
  }
  if (combined.includes("health") || combined.includes("medical")) {
    return "Healthcare";
  }
  if (combined.includes("bank") || combined.includes("salary") || combined.includes("sme")) {
    return "Banking";
  }
  return raw ? formatDisplay(raw) : "Campaign";
}

function numberOrFallback(value: unknown, fallback: number): number {
  const parsed = moneyNumber(value);
  return parsed > 0 ? parsed : fallback;
}

function formatCurrencyReward(value: number): string {
  if (!value) {
    return "-";
  }
  return `R${Math.round(value).toLocaleString("en-ZA")}`;
}

function formatCompactNumber(value: number): string {
  if (value >= 1000) {
    return `${Number((value / 1000).toFixed(value >= 10000 ? 0 : 1))}k`;
  }
  return String(value);
}

function opportunityLabel(opportunity: Record<string, unknown>): string {
  return `${getValue(opportunity, ["opportunity_code", "opportunity_id"])} | ${getValue(
    opportunity,
    ["opportunity_status", "status"],
  )}`;
}

function productLabel(row: Record<string, unknown>): string {
  const product = getValue(row, ["product"], "");
  const subProduct = getValue(row, ["sub_product"], "");
  if (product && subProduct) {
    return `${product} / ${subProduct}`;
  }
  return product || subProduct || "-";
}

function routeLabel(route: Record<string, unknown>): string {
  return `${getValue(route, ["route_id"])} | ${getValue(route, ["route_status", "status"])} | ${getValue(
    route,
    ["distributor_code", "distributor_id"],
  )}`;
}

function distributorLabel(distributor: Record<string, unknown>): string {
  return `${getValue(distributor, ["distributor_code", "distributor_id"])} | ${getValue(
    distributor,
    ["status", "lifecycle_status"],
  )}`;
}

function walletLabel(wallet: Record<string, unknown>): string {
  return `${getValue(wallet, ["distributor_code", "distributor_id"])} | ${getValue(wallet, ["currency"])} | ${getValue(
    wallet,
    ["available_balance"],
    "0.00",
  )} available`;
}

function reviewLabel(review: Record<string, unknown>): string {
  return `${getValue(review, ["distributor_code", "distributor_id"])} | ${getValue(review, ["review_type"])} | ${getValue(
    review,
    ["review_status"],
  )}`;
}

function disputeLabel(dispute: Record<string, unknown>): string {
  return `${getValue(dispute, ["reason_code"])} | ${getValue(dispute, ["dispute_status"])} | ${getValue(
    dispute,
    ["route_id"],
    "-",
  )}`;
}

type BadgeTone = GuardrailTone;

type Guardrail = {
  badge: string;
  tone: BadgeTone;
  title: string;
  copy: string;
  items: GuardrailItem[];
};

function simpleActionGuardrail({
  hasSelection,
  ready,
  status,
  title,
  missingTitle,
  copy,
  backendChange,
  availableAction,
  actionLoading,
}: {
  hasSelection: boolean;
  ready: boolean;
  status: string;
  title: string;
  missingTitle: string;
  copy: string;
  backendChange: string;
  availableAction: string;
  actionLoading: string | null;
}): Guardrail {
  if (!hasSelection) {
    return {
      badge: "Blocked",
      tone: "neutral",
      title: missingTitle,
      copy: "Choose a record before taking this action.",
      items: [
        { label: "Selected record", value: "Missing", tone: "warning" },
        { label: "Next action", value: "None", tone: "neutral" },
        { label: "System change", value: "None", tone: "success" },
      ],
    };
  }

  if (actionLoading) {
    return {
      badge: "Running",
      tone: "info",
      title: "Action in progress",
      copy: "Wait for the backend response before taking another marketplace action.",
      items: [
        { label: "Current action", value: actionLoading, tone: "info" },
        { label: "Status", value: status, tone: statusTone(status) as BadgeTone },
        { label: "System change", value: backendChange, tone: "warning" },
      ],
    };
  }

  return {
    badge: ready ? "Ready" : "Blocked",
    tone: ready ? "success" : "neutral",
    title,
    copy,
    items: [
      { label: "Status", value: status, tone: statusTone(status) as BadgeTone },
      { label: "Next action", value: availableAction, tone: ready ? "success" : "neutral" },
      { label: "System change", value: ready ? backendChange : "None", tone: ready ? "warning" : "success" },
    ],
  };
}

function getAttributionGuardrail({
  unlinkedCount,
  attributionRate,
  completedExceptionCount,
}: {
  unlinkedCount: number;
  attributionRate: string;
  completedExceptionCount: number;
}): Guardrail {
  if (unlinkedCount <= 0) {
    return {
      badge: "Ready",
      tone: "success",
      title: "Journey attribution is clean",
      copy: "Customer journeys are linked to active marketplace routes, so network reporting can rely on route attribution.",
      items: [
        { label: "Unlinked journeys", value: "0", tone: "success" },
        { label: "Attribution rate", value: attributionRate, tone: "success" },
        { label: "Next action", value: "Monitor", tone: "info" },
      ],
    };
  }

  return {
    badge: "Needs review",
    tone: completedExceptionCount > 0 ? "danger" : "warning",
    title: "Resolve unlinked customer journeys",
    copy: "Some customer journeys are not tied to an accepted route. Link them before treating ROI, commission, or settlement attribution as final.",
    items: [
      { label: "Unlinked journeys", value: String(unlinkedCount), tone: "warning" },
      {
        label: "Completed unlinked",
        value: String(completedExceptionCount),
        tone: completedExceptionCount > 0 ? "danger" : "success",
      },
      { label: "Next action", value: "Link route", tone: "info" },
    ],
  };
}

function getWalletGuardrail({
  selectedWallet,
  selectedWalletStatus,
  walletMovementAmount,
  selectedWalletAvailable,
  selectedWalletHeld,
  actionLoading,
}: {
  selectedWallet: Record<string, unknown> | undefined;
  selectedWalletStatus: string;
  walletMovementAmount: number;
  selectedWalletAvailable: number;
  selectedWalletHeld: number;
  actionLoading: string | null;
}): Guardrail {
  if (!selectedWallet) {
    return {
      badge: "Blocked",
      tone: "neutral",
      title: "Select a wallet",
      copy: "Wallet actions are disabled until a distributor wallet is selected.",
      items: [
        { label: "Selected wallet", value: "Missing", tone: "warning" },
        { label: "Amount", value: String(walletMovementAmount), tone: "neutral" },
        { label: "System change", value: "None", tone: "success" },
      ],
    };
  }

  if (actionLoading) {
    return {
      badge: "Running",
      tone: "info",
      title: "Wallet movement in progress",
      copy: "Wait for the wallet response before starting another money movement.",
      items: [
        { label: "Current action", value: actionLoading, tone: "info" },
        { label: "Amount", value: String(walletMovementAmount), tone: "warning" },
        { label: "System change", value: "Wallet ledger", tone: "warning" },
      ],
    };
  }

  const ready = selectedWalletStatus === "ACTIVE" && walletMovementAmount > 0;
  return {
    badge: ready ? "Ready" : "Blocked",
    tone: ready ? "success" : "neutral",
    title: "Wallet movement controls",
    copy: walletActionHint(selectedWalletStatus, walletMovementAmount, selectedWalletAvailable, selectedWalletHeld),
    items: [
      { label: "Wallet status", value: selectedWalletStatus, tone: statusTone(selectedWalletStatus) as BadgeTone },
      { label: "Available / held", value: `${selectedWalletAvailable} / ${selectedWalletHeld}`, tone: ready ? "success" : "warning" },
      { label: "System change", value: ready ? "Wallet ledger" : "None", tone: ready ? "warning" : "success" },
    ],
  };
}

function moneyNumber(value: unknown): number {
  const parsed = Number(String(value ?? "0").replace(/,/g, ""));
  return Number.isFinite(parsed) ? parsed : 0;
}

function walletActionHint(status: string, amount: number, available: number, held: number): string {
  if (status !== "ACTIVE") {
    return "Wallet movements are only available for active wallets.";
  }
  if (amount <= 0) {
    return "Enter a positive amount before moving wallet funds.";
  }
  if (available < amount && held < amount) {
    return "The selected amount is higher than both available and held wallet balances.";
  }
  if (held < amount) {
    return "Release and payout need enough held balance. Credit, hold, or reverse may still be available based on available balance.";
  }
  if (available < amount) {
    return "Hold and reverse need enough available balance. Release hold or payout may still be available based on held balance.";
  }
  return "Wallet controls are available according to available and held balance.";
}

function isGovernanceActionAllowed(distributorStatus: string, actionType: string): boolean {
  if (distributorStatus === "-" || distributorStatus === "TERMINATED") {
    return false;
  }
  if (actionType === "SUSPEND") {
    return distributorStatus === "ACTIVE";
  }
  if (actionType === "REINSTATE") {
    return distributorStatus === "SUSPENDED";
  }
  if (actionType === "TERMINATE") {
    return distributorStatus !== "TERMINATED";
  }
  return distributorStatus !== "TERMINATED";
}

function governanceActionHint(distributorStatus: string, actionType: string): string {
  if (distributorStatus === "TERMINATED") {
    return "Terminated distributors cannot receive further governance actions from this control.";
  }
  if (actionType === "SUSPEND" && distributorStatus !== "ACTIVE") {
    return "Suspend is only available for active distributors.";
  }
  if (actionType === "REINSTATE" && distributorStatus !== "SUSPENDED") {
    return "Reinstate is only available for suspended distributors.";
  }
  return "Governance action is available for the selected distributor state.";
}

function getDistributionGuidance({
  opportunities,
  routes,
  openReviewCount,
  openDisputeCount,
  selectedOpportunityStatus,
  selectedRouteStatus,
  selectedDistributorStatus,
}: {
  opportunities: Record<string, unknown>[];
  routes: Record<string, unknown>[];
  openReviewCount: number;
  openDisputeCount: number;
  selectedOpportunityStatus: string;
  selectedRouteStatus: string;
  selectedDistributorStatus: string;
}): {
  badge: string;
  tone: BadgeTone;
  title: string;
  copy: string;
  steps: JourneyStep[];
} {
  const draftCount = opportunities.filter((opportunity) => getValue(opportunity, ["opportunity_status", "status"]) === "DRAFT").length;
  const routedCount = routes.filter((route) => getValue(route, ["route_status", "status"]) === "ROUTED").length;
  const distributorState = distributionDistributorStepState(selectedDistributorStatus);

  if (openReviewCount > 0 || openDisputeCount > 0) {
    return {
      badge: "Governance",
      tone: "warning",
      title: "Clear open governance work",
      copy: "There are open compliance reviews or disputes. Resolve those before scaling routing and payout activity.",
      steps: [
        distributionStep("Distributor health", "Confirm distributors are active and eligible to receive routed demand.", distributorState),
        distributionStep("Publish opportunities", "Move sponsor-funded opportunities from draft into market.", draftCount ? "waiting" : "done"),
        distributionStep("Work routes", "Accept or decline routed offers so demand can become distributor activity.", routedCount ? "waiting" : "done"),
        distributionStep("Governance queue", "Resolve compliance reviews and disputes before scaling activity.", "current"),
      ],
    };
  }

  if (draftCount > 0 || selectedOpportunityStatus === "DRAFT") {
    return {
      badge: "Publish",
      tone: "info",
      title: "Publish ready opportunities",
      copy: "Draft opportunities need to be published before they can be routed and accepted by distributors.",
      steps: [
        distributionStep("Distributor health", "Confirm distributors are active and eligible to receive routed demand.", distributorState),
        distributionStep("Publish opportunities", "Move sponsor-funded opportunities from draft into market.", "current"),
        distributionStep("Work routes", "Accept or decline routed offers so demand can become distributor activity.", routedCount ? "waiting" : "waiting"),
        distributionStep("Governance queue", "Resolve compliance reviews and disputes before scaling activity.", "done"),
      ],
    };
  }

  if (routedCount > 0 || selectedRouteStatus === "ROUTED") {
    return {
      badge: "Routes",
      tone: "info",
      title: "Work routed offers",
      copy: "Routed offers are waiting for accept or decline decisions. Actioning those routes turns published demand into distributor activity.",
      steps: [
        distributionStep("Distributor health", "Confirm distributors are active and eligible to receive routed demand.", distributorState),
        distributionStep("Publish opportunities", "Move sponsor-funded opportunities from draft into market.", "done"),
        distributionStep("Work routes", "Accept or decline routed offers so demand can become distributor activity.", "current"),
        distributionStep("Governance queue", "Resolve compliance reviews and disputes before scaling activity.", "done"),
      ],
    };
  }

  return {
    badge: "Stable",
    tone: "success",
    title: "Marketplace is operational",
    copy: "No immediate distribution action is being signalled. Monitor reporting, wallet ledger movement, and governance audit for changes.",
    steps: [
      distributionStep("Distributor health", "Confirm distributors are active and eligible to receive routed demand.", distributorState),
      distributionStep("Publish opportunities", "Move sponsor-funded opportunities from draft into market.", "done"),
      distributionStep("Work routes", "Accept or decline routed offers so demand can become distributor activity.", "done"),
      distributionStep("Governance queue", "Resolve compliance reviews and disputes before scaling activity.", "done"),
    ],
  };
}

function distributionStep(label: string, description: string, state: JourneyStep["state"]): JourneyStep {
  const workAreas: Record<string, string> = {
    "Distributor health": "Distributor lifecycle and distributor report",
    "Publish opportunities": "Opportunity actions",
    "Work routes": "Route actions and offer routes",
    "Governance queue": "Compliance reviews, disputes, and governance audit",
  };
  const targets: Record<string, string> = {
    "Distributor health": "distribution-distributor-lifecycle",
    "Publish opportunities": "distribution-opportunity-actions",
    "Work routes": "distribution-route-actions",
    "Governance queue": "distribution-compliance-reviews",
  };

  return { label, description, state, workArea: workAreas[label], targetId: targets[label] };
}

function distributionDistributorStepState(status: string): JourneyStep["state"] {
  if (status === "ACTIVE") {
    return "done";
  }
  if (status === "SUSPENDED" || status === "TERMINATED") {
    return "blocked";
  }
  if (status === "-") {
    return "waiting";
  }
  return "review";
}

function formatListValue(record: Record<string, unknown>, key: string): string {
  const value = record[key];
  if (Array.isArray(value)) {
    return value.join(", ");
  }
  return formatDisplay(value);
}
