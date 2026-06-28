import { Send, XCircle } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import {
  acceptDistributorPortalOffer,
  declineDistributorPortalOffer,
  getAdminDistributors,
  getDistributorExperience,
  getDistributorPortalWalletLedger,
  getRecognitionBadges,
  getRecognitionMissions,
  getRecognitionProgress,
  getTenantLeaderboard,
  linkDistributorPortalOfferReferral,
} from "../../api/endpoints/distribution";
import { DataTable } from "../../components/DataTable";
import { EmptyState } from "../../components/EmptyState";
import { ErrorPanel } from "../../components/ErrorPanel";
import { FieldLabel } from "../../components/FieldLabel";
import { ActionGuardrail, GuardrailItem, GuardrailTone } from "../../components/ActionGuardrail";
import { InsuranceJourneyProofPanel } from "../../components/InsuranceJourneyProofPanel";
import { JourneyStep, JourneyTracker } from "../../components/JourneyTracker";
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
import { DistributorHubView } from "./components/DistributorHubView";

const TENANT_KEY = "amplifi.distributorPortal.tenant";
const DISTRIBUTOR_KEY = "amplifi.distributorPortal.distributor";
const DEFAULT_LEADERBOARD_CODE = "GLOBAL_OVERALL";

type DistributorPageMode = "hub" | "operations";

export function DistributorOperationsPage() {
  return <DistributorPortalPage mode="operations" />;
}

export function DistributorPortalPage({ mode = "hub" }: { mode?: DistributorPageMode }) {
  const { refreshKey } = useRefreshContext();
  const backend = useBackendSession(refreshKey, "distributor-workspace");
  const [tenantCode, setTenantCode] = useState(localStorage.getItem(TENANT_KEY) || "FNB");
  const [distributorCode, setDistributorCode] = useState(localStorage.getItem(DISTRIBUTOR_KEY) || "");
  const [submitted, setSubmitted] = useState({
    tenantCode: localStorage.getItem(TENANT_KEY) || "FNB",
    distributorCode: localStorage.getItem(DISTRIBUTOR_KEY) || "",
  });
  const [distributorOptions, setDistributorOptions] = useState<Record<string, unknown>[]>([]);
  const [distributorOptionsLoading, setDistributorOptionsLoading] = useState(false);
  const [distributorOptionsError, setDistributorOptionsError] = useState<string | null>(null);
  const [profile, setProfile] = useState<unknown>(null);
  const [performance, setPerformance] = useState<unknown>(null);
  const [leaderboard, setLeaderboard] = useState<unknown>(null);
  const [leaderboardError, setLeaderboardError] = useState<string | null>(null);
  const [recognitionProgress, setRecognitionProgress] = useState<unknown>(null);
  const [recognitionBadges, setRecognitionBadges] = useState<unknown>(null);
  const [recognitionMissions, setRecognitionMissions] = useState<unknown>(null);
  const [recognitionErrors, setRecognitionErrors] = useState<string[]>([]);
  const [offers, setOffers] = useState<Record<string, unknown>[]>([]);
  const [conversions, setConversions] = useState<unknown>(null);
  const [wallets, setWallets] = useState<Record<string, unknown>[]>([]);
  const [walletLedger, setWalletLedger] = useState<Record<string, unknown>[]>([]);
  const [insuranceProof, setInsuranceProof] = useState<unknown>(null);
  const [outcomeMoneyReview, setOutcomeMoneyReview] = useState<unknown>(null);
  const [channelReadiness, setChannelReadiness] = useState<unknown>(null);
  const [channelRecommendations, setChannelRecommendations] = useState<unknown>(null);
  const [selectedOfferRouteId, setSelectedOfferRouteId] = useState("");
  const [selectedWalletId, setSelectedWalletId] = useState("");
  const [selectedAcceptedRouteId, setSelectedAcceptedRouteId] = useState("");
  const [referralTrackId, setReferralTrackId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [actionError, setActionError] = useState<unknown>(null);
  const [actionResult, setActionResult] = useState<Record<string, unknown> | null>(null);
  const [localRefreshKey, setLocalRefreshKey] = useState(0);
  const distributorSessionLocked =
    backend.status === "confirmed" &&
    normalizeSessionRole(backend.session?.role) === "distributor" &&
    Boolean(backend.session?.distributor_code);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cleanedTenant = tenantCode.trim().toUpperCase();
    const cleanedDistributor = distributorCode.trim().toUpperCase();
    localStorage.setItem(TENANT_KEY, cleanedTenant);
    localStorage.setItem(DISTRIBUTOR_KEY, cleanedDistributor);
    setTenantCode(cleanedTenant);
    setDistributorCode(cleanedDistributor);
    setSubmitted({ tenantCode: cleanedTenant, distributorCode: cleanedDistributor });
  }

  useEffect(() => {
    if (!distributorSessionLocked || !backend.session?.distributor_code) {
      return;
    }

    const scopedTenant = String(backend.session.tenant_code || backend.session.tenant || "FNB").toUpperCase();
    const scopedDistributor = String(backend.session.distributor_code).toUpperCase();

    localStorage.setItem(TENANT_KEY, scopedTenant);
    localStorage.setItem(DISTRIBUTOR_KEY, scopedDistributor);
    setTenantCode(scopedTenant);
    setDistributorCode(scopedDistributor);
    setSubmitted({ tenantCode: scopedTenant, distributorCode: scopedDistributor });
  }, [
    distributorSessionLocked,
    backend.session?.tenant_code,
    backend.session?.tenant,
    backend.session?.distributor_code,
  ]);

  useEffect(() => {
    const cleanedTenant = tenantCode.trim().toUpperCase();
    if (!cleanedTenant) {
      setDistributorOptions([]);
      setDistributorOptionsError(null);
      return;
    }

    let alive = true;
    setDistributorOptionsLoading(true);
    setDistributorOptionsError(null);
    getAdminDistributors(cleanedTenant, 100)
      .then((payload) => {
        if (alive) {
          setDistributorOptions(asArray(payload));
        }
      })
      .catch((requestError) => {
        if (alive) {
          setDistributorOptions([]);
          setDistributorOptionsError(requestError?.message || "Could not load distributors for this tenant.");
        }
      })
      .finally(() => alive && setDistributorOptionsLoading(false));
    return () => {
      alive = false;
    };
  }, [tenantCode, refreshKey]);

  useEffect(() => {
    if (!submitted.tenantCode || !submitted.distributorCode) {
      return;
    }

    let alive = true;
    setLoading(true);
    setError(null);
    Promise.all([
      getDistributorExperience(submitted.tenantCode, submitted.distributorCode),
      getTenantLeaderboard(submitted.tenantCode, DEFAULT_LEADERBOARD_CODE).catch((requestError) => ({
        leaderboardError: requestError?.message || "Leaderboard could not be loaded.",
      })),
      getRecognitionProgress(submitted.distributorCode).catch(() => ({
        recognitionError: "No progress signal returned for this reference.",
        recognitionKind: "Progress",
      })),
      getRecognitionBadges(submitted.distributorCode).catch(() => ({
        recognitionError: "No badge signal returned for this reference.",
        recognitionKind: "Badges",
      })),
      getRecognitionMissions(submitted.distributorCode).catch(() => ({
        recognitionError: "No mission signal returned for this reference.",
        recognitionKind: "Missions",
      })),
    ])
      .then(([
        experiencePayload,
        leaderboardPayload,
        progressPayload,
        badgePayload,
        missionPayload,
      ]) => {
        if (alive) {
          const sections = getNestedValue(experiencePayload, ["sections"], {}) as Record<string, unknown>;
          const profilePayload = getNestedValue(sections.profile, ["data"], null);
          const performancePayload = getNestedValue(sections.performance, ["data"], null);
          const offerPayload = getNestedValue(sections.opportunities, ["data"], null);
          const conversionPayload = getNestedValue(sections.conversions, ["data"], null);
          const walletPayload = getNestedValue(sections.wallet, ["data"], null);
          const outcomeMoneyReviewPayload = getNestedValue(sections.outcomeMoney, ["data"], null);
          const insuranceProofPayload = getNestedValue(sections.proof, ["data"], null);
          const channelPayload = getNestedValue(sections.channels, ["data"], null);

          setProfile(profilePayload);
          setPerformance(performancePayload);
          setOffers(asArray(offerPayload));
          setConversions(conversionPayload);
          setOutcomeMoneyReview(outcomeMoneyReviewPayload);
          setWallets(asArray(walletPayload));
          setInsuranceProof(insuranceProofPayload);
          setChannelReadiness(getNestedValue(channelPayload, ["readiness"], null));
          setChannelRecommendations(getNestedValue(channelPayload, ["recommendations"], null));
          if (
            leaderboardPayload &&
            typeof leaderboardPayload === "object" &&
            "leaderboardError" in leaderboardPayload
          ) {
            setLeaderboard(null);
            setLeaderboardError(String(leaderboardPayload.leaderboardError));
          } else {
            setLeaderboard(leaderboardPayload);
            setLeaderboardError(null);
          }
          const recognitionPayloads = [progressPayload, badgePayload, missionPayload];
          setRecognitionProgress(extractRecognitionPayload(progressPayload));
          setRecognitionBadges(extractRecognitionPayload(badgePayload));
          setRecognitionMissions(extractRecognitionPayload(missionPayload));
          setRecognitionErrors(
            recognitionPayloads
              .filter(isRecognitionError)
              .map((payload) => `${payload.recognitionKind}: ${payload.recognitionError}`),
          );
        }
      })
      .catch((requestError) => alive && setError(requestError))
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [submitted, refreshKey, localRefreshKey]);

  useEffect(() => {
    const routedOffers = offers.filter((offer) => getValue(offer, ["route_status", "status"]) === "ROUTED");
    if (!routedOffers.length) {
      setSelectedOfferRouteId("");
      return;
    }

    const current = routedOffers.find((offer) => getValue(offer, ["route_id", "offer_route_id", "id"]) === selectedOfferRouteId);
    setSelectedOfferRouteId(getValue(current || routedOffers[0], ["route_id", "offer_route_id", "id"], ""));
  }, [offers, selectedOfferRouteId]);

  useEffect(() => {
    const acceptedOffers = offers.filter((offer) => getValue(offer, ["route_status", "status"]) === "ACCEPTED");
    if (!acceptedOffers.length) {
      setSelectedAcceptedRouteId("");
      return;
    }

    const current = acceptedOffers.find((offer) => getValue(offer, ["route_id", "offer_route_id", "id"]) === selectedAcceptedRouteId);
    setSelectedAcceptedRouteId(getValue(current || acceptedOffers[0], ["route_id", "offer_route_id", "id"], ""));
  }, [offers, selectedAcceptedRouteId]);

  useEffect(() => {
    if (!wallets.length) {
      setSelectedWalletId("");
      return;
    }

    const current = wallets.find((wallet) => getValue(wallet, ["wallet_id", "id"]) === selectedWalletId);
    setSelectedWalletId(getValue(current || wallets[0], ["wallet_id", "id"], ""));
  }, [wallets, selectedWalletId]);

  useEffect(() => {
    if (!submitted.tenantCode || !submitted.distributorCode || !selectedWalletId) {
      setWalletLedger([]);
      return;
    }

    let alive = true;
    getDistributorPortalWalletLedger(submitted.tenantCode, submitted.distributorCode, selectedWalletId)
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
  }, [submitted, selectedWalletId, refreshKey, localRefreshKey]);

  const routedOffers = offers.filter((offer) => getValue(offer, ["route_status", "status"]) === "ROUTED");
  const acceptedOffers = offers.filter((offer) => getValue(offer, ["route_status", "status"]) === "ACCEPTED");
  const selectedOffer = offers.find((offer) => getValue(offer, ["route_id", "offer_route_id", "id"]) === selectedOfferRouteId);
  const selectedAcceptedOffer = offers.find((offer) => getValue(offer, ["route_id", "offer_route_id", "id"]) === selectedAcceptedRouteId);
  const selectedOfferStatus = selectedOffer ? getValue(selectedOffer, ["route_status", "status"]) : "-";
  const selectedWallet = wallets.find((wallet) => getValue(wallet, ["wallet_id", "id"]) === selectedWalletId);
  const topChannel = getNestedValue(channelRecommendations, ["top_channel"], {});
  const topChannelCode = formatDisplay(getNestedValue(topChannel, ["channel_code"], "-"));
  const topChannelScore = formatDisplay(getNestedValue(topChannel, ["recommendation_score"], "-"));
  const topChannelAction = formatDisplay(getNestedValue(topChannel, ["recommended_action"], "No channel recommendation returned."));
  const channelReadyCount = Number(getNestedValue(channelReadiness, ["summary", "ready_count"], 0)) || 0;
  const channelCount = Number(getNestedValue(channelReadiness, ["summary", "count"], 0)) || 0;
  const channelStatus = formatDisplay(getNestedValue(channelReadiness, ["status"], "UNKNOWN"));
  const walletCurrency = currencyFrom(selectedWallet || performance);
  const totalCommission = formatCurrency(getNestedValue(performance, ["total_commission_amount"], "0.00"), walletCurrency);
  const walletAvailable = formatCurrency(
    getNestedValue(performance, ["wallet_available_balance"], getValue(selectedWallet || {}, ["available_balance"], "0.00")),
    walletCurrency,
  );
  const pendingRewards = formatCurrency(
    getNestedValue(performance, ["pending_reward_amount"], getNestedValue(performance, ["wallet_held_balance"], "0.00")),
    walletCurrency,
  );
  const acceptedCount = Number(getNestedValue(performance, ["accepted_count"], 0));
  const routedCount = Number(getNestedValue(performance, ["routed_count"], offers.length));
  const acceptanceRate = formatPercent(getNestedValue(performance, ["acceptance_rate"], "0.0000"));
  const conversionRows = asArray(getNestedValue(conversions, ["items"], []));
  const conversionCount = Number(getNestedValue(performance, ["conversion_count"], conversionRows.length));
  const completedConversions = Number(getNestedValue(performance, ["completed_conversion_count"], getNestedValue(conversions, ["completed_count"], 0)));
  const conversionCompletionRate = formatPercent(getNestedValue(performance, ["conversion_completion_rate"], "0.0000"));
  const attributedConversions = Number(getNestedValue(conversions, ["attributed_count"], conversionRows.filter((row) => getValue(row, ["route_id"], "")).length));
  const unlinkedConversions = Number(getNestedValue(conversions, ["unlinked_count"], Math.max(conversionRows.length - attributedConversions, 0)));
  const conversionAttributionRate = formatPercent(getNestedValue(conversions, ["attribution_rate"], "0.0000"));
  const safeStatusSummary = getDistributorSafeStatusSummary({
    conversionRows,
    profile,
    offers,
    performance,
    wallets,
    attributedConversions,
    unlinkedConversions,
  });
  const offerGuard = getOfferDecisionGuardrail({ selectedOffer, selectedOfferStatus, actionLoading });
  const linkGuard = getConversionLinkGuardrail({
    selectedOffer: selectedAcceptedOffer,
    referralTrackId,
    actionLoading,
  });
  const attributionGuard = getDistributorAttributionGuardrail({
    conversionCount,
    attributedConversions,
    unlinkedConversions,
    attributionRate: conversionAttributionRate,
  });
  const leaderboardRows = asArray(leaderboard);
  const leaderboardTotal = getNestedValue(leaderboard, ["totalCount"], leaderboardRows.length);
  const recognitionProgressCount = countRecognitionProgress(recognitionProgress);
  const recognitionBadgeCount = countRecognitionItems(recognitionBadges);
  const recognitionMissionCount = countRecognitionMissions(recognitionMissions);
  const distributorGuidance = getDistributorGuidance({
    hasDistributor: Boolean(submitted.tenantCode && submitted.distributorCode),
    profile,
    performance,
    offers,
    conversions: conversionRows,
    wallets,
    routedOfferCount: routedOffers.length,
  });
  const distributorDisplayName = getNestedValue(profile, ["distributor_name"], submitted.distributorCode || "Distributor");
  const activeReferralCount = Math.max(conversionRows.length - completedConversions, 0);
  const topOfferRows = offers.slice(0, 3);
  const referralPreviewRows = conversionRows.slice(0, 4);
  const currentRank = getCurrentDistributorRank(leaderboardRows, submitted.distributorCode);
  const heroMomentum = completedConversions > 0 ? `${completedConversions} completed referral${completedConversions === 1 ? "" : "s"}` : "Waiting for completions";

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

  function decideOffer(action: "accept" | "decline", offer: Record<string, unknown>) {
    const routeId = getValue(offer, ["route_id", "offer_route_id", "id"], "");
    const status = getValue(offer, ["route_status", "status"], "");
    if (!routeId || status !== "ROUTED" || actionLoading) {
      return;
    }

    const label = action === "accept" ? "Accept offer" : "Decline offer";
    if (!window.confirm(`${label}?`)) {
      return;
    }

    setSelectedOfferRouteId(routeId);
    runAction(label, () =>
      action === "accept"
        ? acceptDistributorPortalOffer(submitted.tenantCode, submitted.distributorCode, routeId)
        : declineDistributorPortalOffer(submitted.tenantCode, submitted.distributorCode, routeId),
    );
  }

  function submitAcceptOffer(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedOffer) {
      return;
    }
    decideOffer("accept", selectedOffer);
  }

  function submitDeclineOffer(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedOffer) {
      return;
    }
    decideOffer("decline", selectedOffer);
  }

  function submitLinkReferral(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cleanedReferralTrackId = referralTrackId.trim();
    if (!selectedAcceptedRouteId || !cleanedReferralTrackId || actionLoading) {
      return;
    }

    runAction("Link customer journey", () =>
      linkDistributorPortalOfferReferral(
        submitted.tenantCode,
        submitted.distributorCode,
        selectedAcceptedRouteId,
        cleanedReferralTrackId,
      ),
    );
  }

  return (
    <>
      {mode === "hub" ? (
        <DistributorHubView
          acceptanceRate={acceptanceRate}
          acceptedCount={acceptedCount}
          activeReferralCount={activeReferralCount}
          attributedConversions={attributedConversions}
          completedConversions={completedConversions}
          conversionAttributionRate={conversionAttributionRate}
          conversionRows={conversionRows}
          currentRank={currentRank}
          distributorDisplayName={distributorDisplayName}
          heroMomentum={heroMomentum}
          leaderboardError={leaderboardError}
          leaderboardRows={leaderboardRows}
          leaderboardTotal={leaderboardTotal}
          pendingRewards={pendingRewards}
          performance={performance}
          profile={profile}
          referralPreviewRows={referralPreviewRows}
          routedCount={routedCount}
          selectedWallet={selectedWallet}
          submitted={submitted}
          topOfferRows={topOfferRows}
          totalCommission={totalCommission}
          unlinkedConversions={unlinkedConversions}
          walletAvailable={walletAvailable}
          walletCurrency={walletCurrency}
        />
      ) : (
        <section className="page-header">
          <div>
            <div className="page-kicker">Distributor operations</div>
            <h1 className="page-title">Earnings Operations</h1>
            <p className="page-copy">
              Operational controls for routed offer decisions, referral links, wallet activity, distributor profile,
              performance, and detailed portal records.
            </p>
          </div>
          <StatusBadge label="Operations" tone="info" />
        </section>
      )}

      <section className="panel" id="distributor-identity">
        <div className="panel-header">
          <div>
            <PanelTitle
              help="Sets the tenant and distributor context for portal requests."
              title="Distributor identity"
            />
            <div className="panel-subtitle">Used for portal profile, offer, wallet, and performance requests.</div>
          </div>
        </div>
        <div className="panel-body">
          <form className="form-row sponsor-picker-row" onSubmit={submit}>
            <div className="field">
              <FieldLabel
                help="The tenant whose distributor portal should be loaded."
                htmlFor="distributor-tenant"
                label="Tenant code"
              />
              <input
                className="input"
                disabled={distributorSessionLocked}
                id="distributor-tenant"
                value={tenantCode}
                onChange={(event) => setTenantCode(event.target.value)}
              />
              {distributorSessionLocked ? <div className="field-hint">Backend-confirmed tenant scope.</div> : null}
            </div>
            <div className="field">
              <FieldLabel
                help="A convenience picker loaded from the admin distributor list."
                htmlFor="distributor-picker"
                label="Distributor picker"
              />
              <select
                className="input"
                disabled={distributorSessionLocked || distributorOptionsLoading || !distributorOptions.length}
                id="distributor-picker"
                value={distributorCode}
                onChange={(event) => setDistributorCode(event.target.value)}
              >
                <option value="">
                  {distributorOptionsLoading
                    ? "Loading distributors..."
                    : distributorOptions.length
                      ? "Select a distributor"
                      : "No distributors found"}
                </option>
                {distributorOptions.map((option) => {
                  const code = getValue(option, ["distributor_code"]);
                  const name = getValue(option, ["distributor_name", "name"]);
                  const type = getValue(option, ["distributor_type", "type"]);
                  const status = getValue(option, ["status"]);
                  return (
                    <option key={code} value={code}>
                      {name} - {code} - {type} - {status}
                    </option>
                  );
                })}
              </select>
              {distributorOptionsError ? <div className="field-hint danger-text">{distributorOptionsError}</div> : null}
            </div>
            <div className="field">
              <FieldLabel
                help="The distributor code used by the portal API."
                htmlFor="distributor-code"
                label="Distributor code"
              />
              <input
                className="input"
                disabled={distributorSessionLocked}
                id="distributor-code"
                value={distributorCode}
                onChange={(event) => setDistributorCode(event.target.value)}
              />
              <div className="field-hint">
                {distributorSessionLocked
                  ? "Backend-confirmed distributor scope."
                  : "Select from the list or enter a code manually."}
              </div>
            </div>
            <button className="button" disabled={distributorSessionLocked} type="submit">
              {distributorSessionLocked ? "Loaded from session" : "Load distributor"}
            </button>
          </form>
        </div>
      </section>

      {!submitted.tenantCode || !submitted.distributorCode ? (
        <EmptyState label="Enter a tenant code and distributor code to load the distributor portal view." />
      ) : loading ? (
        <LoadingState label="Loading distributor portal" />
      ) : error ? (
        <ErrorPanel error={error} />
      ) : mode === "operations" ? (
        <>
          <JourneyTracker
            badge={distributorGuidance.badge}
            currentCopy={distributorGuidance.copy}
            currentTitle={distributorGuidance.title}
            steps={distributorGuidance.steps}
            subtitle="Step-by-step path from distributor identity through routed offers, earnings, and performance."
            title="Distributor journey"
            tone={distributorGuidance.tone}
          />

          <InsuranceJourneyProofPanel proof={insuranceProof} role="distributor" />

          <DistributorSafeStatusPanel summary={safeStatusSummary} />

          <section className="panel" id="distributor-channel-intelligence">
            <div className="panel-header">
              <div>
                <PanelTitle
                  help="Backend-scored channel recommendation for distributor route and customer progress messaging."
                  title="Channel intelligence"
                />
                <div className="panel-subtitle">Explainable channel fit for routed offers and follow-up prompts.</div>
              </div>
              <StatusBadge label={topChannelCode !== "-" ? topChannelCode : "Check"} tone={topChannelCode !== "-" ? "success" : "warning"} />
            </div>
            <div className="panel-body">
              <div className="summary-grid">
                <SummaryItem label="Recommended" value={topChannelCode} />
                <SummaryItem label="Score" value={topChannelScore} />
                <SummaryItem label="Adapters ready" value={channelCount ? `${channelReadyCount}/${channelCount}` : "-"} />
                <SummaryItem label="Readiness" value={channelStatus} />
                <SummaryItem label="Event" value={getNestedValue(channelRecommendations, ["event_type"], "ROUTE_ASSIGNED")} />
                <SummaryItem label="Audience" value={getNestedValue(channelRecommendations, ["audience"], "DISTRIBUTOR")} />
              </div>
              <div className="route-list">
                <div className="route-item">
                  <div>
                    <div className="route-name">{topChannelAction}</div>
                    <div className="route-path">{formatDisplay(getNestedValue(channelRecommendations, ["guardrail"], "Recommendations do not send messages or bypass consent checks."))}</div>
                  </div>
                  <StatusBadge label={formatDisplay(getNestedValue(topChannel, ["provider_status"], "CHECK"))} tone={statusTone(formatDisplay(getNestedValue(topChannel, ["provider_status"], "CHECK")))} />
                </div>
              </div>
            </div>
          </section>

          <OutcomeMoneyReviewPanel
            review={outcomeMoneyReview}
            title="Distributor outcome money"
          />

          <section className="panel" id="distributor-recognition">
            <div className="panel-header">
              <div>
                <PanelTitle
                  help="Progress, badge, mission, and rank signals from the existing recognition APIs. These are keyed by the distributor code as the recognition reference in this local workspace."
                  title="Recognition signals"
                />
                <div className="panel-subtitle">Progress, missions, badges, and rank returned for this distributor reference.</div>
              </div>
              <StatusBadge
                label={recognitionErrors.length ? "Partial" : "Live"}
                tone={recognitionErrors.length ? "warning" : "success"}
              />
            </div>
            <div className="panel-body">
              <div className="summary-grid">
                <SummaryItem label="Reference" value={submitted.distributorCode || "-"} />
                <SummaryItem label="Progress records" value={recognitionProgressCount} />
                <SummaryItem label="Badges" value={recognitionBadgeCount} />
                <SummaryItem label="Missions" value={recognitionMissionCount} />
                <SummaryItem label="Leaderboard" value={DEFAULT_LEADERBOARD_CODE} />
                <SummaryItem label="Ranked rows" value={leaderboardTotal} />
              </div>
              {recognitionErrors.length ? (
                <div className="recognition-warning-list">
                  {recognitionErrors.map((message) => (
                    <div className="state-panel" key={message}>
                      {message}
                    </div>
                  ))}
                </div>
              ) : null}
            </div>
          </section>

          <section className="grid-2">
            <div className="panel" id="distributor-offer-decision">
              <div className="panel-header">
                <div>
                  <PanelTitle
                    help="Lets the distributor accept or decline routed opportunities from their portal view."
                    title="Offer decision"
                  />
                  <div className="panel-subtitle">Only routed offers can be accepted or declined.</div>
                </div>
                <StatusBadge label={selectedOfferStatus} tone={statusTone(selectedOfferStatus)} />
              </div>
              <div className="panel-body">
                <div className="action-select-row">
                  <div className="field">
                    <FieldLabel
                      help="The offer route the distributor is deciding on."
                      htmlFor="portal-offer-route"
                      label="Offer route"
                    />
                    <select
                      className="input"
                      id="portal-offer-route"
                      value={selectedOfferRouteId}
                      onChange={(event) => setSelectedOfferRouteId(event.target.value)}
                    >
                      {routedOffers.length ? null : <option value="">No routed offers returned</option>}
                      {routedOffers.map((offer) => {
                        const routeId = getValue(offer, ["route_id", "offer_route_id", "id"], "");
                        return (
                          <option key={routeId} value={routeId}>
                            {offerLabel(offer)}
                          </option>
                        );
                      })}
                    </select>
                  </div>
                </div>
                <div className="action-button-row">
                  <form onSubmit={submitAcceptOffer}>
                    <button
                      className="button"
                      disabled={!selectedOfferRouteId || selectedOfferStatus !== "ROUTED" || actionLoading !== null}
                      type="submit"
                    >
                      <Send size={16} />
                      Accept
                    </button>
                  </form>
                  <form onSubmit={submitDeclineOffer}>
                    <button
                      className="button secondary"
                      disabled={!selectedOfferRouteId || selectedOfferStatus !== "ROUTED" || actionLoading !== null}
                      type="submit"
                    >
                      <XCircle size={16} />
                      Decline
                    </button>
                  </form>
                </div>
                <SelectedOfferSummary offer={selectedOffer} />
                <ActionGuardrail
                  badge={offerGuard.badge}
                  tone={offerGuard.tone}
                  title={offerGuard.title}
                  copy={offerGuard.copy}
                  items={offerGuard.items}
                />
              </div>
            </div>

            <div className="panel" id="distributor-wallet-activity">
              <div className="panel-header">
                <div>
                  <PanelTitle
                    help="Shows the selected wallet balance and recent ledger movements."
                    title="Wallet activity"
                  />
                  <div className="panel-subtitle">Balances and movement history available to the distributor.</div>
                </div>
                <StatusBadge label={selectedWallet ? getValue(selectedWallet, ["status", "wallet_status"]) : "-"} tone={statusTone(selectedWallet ? getValue(selectedWallet, ["status", "wallet_status"]) : "-")} />
              </div>
              <div className="panel-body">
                <div className="action-select-row">
                  <div className="field">
                    <FieldLabel
                      help="The wallet whose ledger movements should be shown."
                      htmlFor="portal-wallet"
                      label="Wallet"
                    />
                    <select
                      className="input"
                      id="portal-wallet"
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
                </div>
                <SelectedWalletSummary wallet={selectedWallet} />
              </div>
            </div>
          </section>

          {actionError ? <ErrorPanel error={actionError} /> : null}
          {actionResult ? <PortalActionResult payload={actionResult} /> : null}

          <section className="panel" id="customer-conversions">
            <div className="panel-header">
              <div>
                <PanelTitle
                  help="Customer journey state for referral tracks attributed to this distributor. These states come from referral progress and enterprise activation events."
                  title="Customer conversions"
                />
                <div className="panel-subtitle">Validated customers, activation progress, and next conversion step.</div>
              </div>
              <StatusBadge
                label={`${formatDisplay(attributedConversions)}/${formatDisplay(conversionRows.length)} linked | ${conversionAttributionRate}`}
                tone={unlinkedConversions > 0 ? "warning" : attributedConversions > 0 ? "success" : "neutral"}
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
            </div>
            <DataTable
              emptyText="No customer conversion journeys returned for this distributor."
              rows={conversionRows}
              columns={[
                {
                  key: "customer",
                  header: "Customer journey",
                  render: (row) => (
                    <div>
                      <strong>{getValue(row, ["display_status", "status"], "In progress")}</strong>
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
                  render: (row) => conversionNextStep(row),
                },
                {
                  key: "source",
                  header: "Source offer",
                  render: (row) => (
                    <div>
                      <strong>{getValue(row, ["opportunity_title", "opportunity_code"], "Unlinked")}</strong>
                      <div className="table-subtext">{getValue(row, ["route_id"], "Needs route link")}</div>
                    </div>
                  ),
                },
                {
                  key: "attribution",
                  header: "Attribution",
                  render: (row) => (
                    <StatusBadge
                      label={getValue(row, ["route_id"], "") ? "Linked" : "Unlinked"}
                      tone={getValue(row, ["route_id"], "") ? "success" : "warning"}
                    />
                  ),
                },
                {
                  key: "state",
                  header: "Safe status",
                  render: (row) => (
                    <ConversionSafeStatus row={row} />
                  ),
                },
              ]}
            />
          </section>

          <section className="grid-2">
            <div className="panel" id="customer-conversion-link">
              <div className="panel-header">
                <div>
                  <PanelTitle
                    help="Links an accepted offer route to the customer referral journey once the referral track is known."
                    title="Link customer journey"
                  />
                  <div className="panel-subtitle">Connect accepted demand to the customer conversion golden thread.</div>
                </div>
                <StatusBadge label={acceptedOffers.length ? `${acceptedOffers.length} accepted` : "No accepted routes"} tone={acceptedOffers.length ? "success" : "neutral"} />
              </div>
              <div className="panel-body">
                <form className="action-select-row" onSubmit={submitLinkReferral}>
                  <div className="field">
                    <FieldLabel
                      help="Accepted offer route that should be tied to a customer referral track."
                      htmlFor="accepted-offer-route"
                      label="Accepted route"
                    />
                    <select
                      className="input"
                      id="accepted-offer-route"
                      value={selectedAcceptedRouteId}
                      onChange={(event) => setSelectedAcceptedRouteId(event.target.value)}
                    >
                      {acceptedOffers.length ? null : <option value="">No accepted routes returned</option>}
                      {acceptedOffers.map((offer) => {
                        const routeId = getValue(offer, ["route_id", "offer_route_id", "id"], "");
                        return (
                          <option key={routeId} value={routeId}>
                            {offerLabel(offer)}
                          </option>
                        );
                      })}
                    </select>
                  </div>
                  <div className="field">
                    <FieldLabel
                      help="Referral track returned when the customer validates or starts their referred journey."
                      htmlFor="referral-track-id"
                      label="Referral track"
                    />
                    <input
                      className="input"
                      id="referral-track-id"
                      placeholder="Referral track ID"
                      value={referralTrackId}
                      onChange={(event) => setReferralTrackId(event.target.value)}
                    />
                  </div>
                  <button
                    className="button"
                    disabled={!selectedAcceptedRouteId || !referralTrackId.trim() || actionLoading !== null}
                    type="submit"
                  >
                    Link journey
                  </button>
                </form>
                <ActionGuardrail
                  badge={linkGuard.badge}
                  tone={linkGuard.tone}
                  title={linkGuard.title}
                  copy={linkGuard.copy}
                  items={linkGuard.items}
                />
              </div>
            </div>

            <div className="panel" id="distributor-profile">
              <div className="panel-header">
                <div>
                  <PanelTitle
                    help="Distributor lifecycle, channels, segments, and regions returned from the portal profile."
                    title="Profile"
                  />
                  <div className="panel-subtitle">Distributor lifecycle, channels, and eligibility.</div>
                </div>
              </div>
              <div className="panel-body">
                <div className="summary-grid">
                  <SummaryItem label="Name" value={getNestedValue(profile, ["distributor_name"])} />
                  <SummaryItem label="Type" value={getNestedValue(profile, ["distributor_type"])} />
                  <SummaryItem label="Status" value={getNestedValue(profile, ["status"])} />
                  <SummaryItem label="Channels" value={formatList(getNestedValue(profile, ["channels"], []))} />
                  <SummaryItem label="Segments" value={formatList(getNestedValue(profile, ["segments"], []))} />
                  <SummaryItem label="Regions" value={formatList(getNestedValue(profile, ["regions"], []))} />
                </div>
              </div>
            </div>
            <div className="panel" id="distributor-performance">
              <div className="panel-header">
                <div>
                  <PanelTitle
                    help="Offer routing outcomes and wallet performance for the selected distributor."
                    title="Performance"
                  />
                  <div className="panel-subtitle">Offer routing, acceptance, and earnings position.</div>
                </div>
              </div>
              <div className="panel-body">
                <div className="summary-grid">
                  <SummaryItem label="Routed" value={getNestedValue(performance, ["routed_count"], 0)} />
                  <SummaryItem label="Accepted" value={getNestedValue(performance, ["accepted_count"], 0)} />
                  <SummaryItem label="Declined" value={getNestedValue(performance, ["declined_count"], 0)} />
                  <SummaryItem label="Acceptance" value={acceptanceRate} />
                  <SummaryItem label="Journeys" value={getNestedValue(performance, ["conversion_count"], conversionRows.length)} />
                  <SummaryItem label="Completed" value={getNestedValue(performance, ["completed_conversion_count"], completedConversions)} />
                  <SummaryItem label="Completion" value={conversionCompletionRate} />
                  <SummaryItem label="Available" value={walletAvailable} />
                  <SummaryItem label="Paid out" value={formatCurrency(getNestedValue(performance, ["wallet_paid_out_balance"], "0.00"), walletCurrency)} />
                </div>
              </div>
            </div>
          </section>

          <section className="panel" id="distributor-offer-inbox">
            <div className="panel-header">
              <div>
                <PanelTitle
                  help="All matched opportunities returned to this distributor, with route status."
                  title="Offer inbox"
                />
                <div className="panel-subtitle">Matched opportunities and route status.</div>
              </div>
            </div>
            <DataTable
              emptyText="No offers returned for this distributor."
              rows={offers}
              columns={[
                { key: "route", header: "Route", render: (row) => <span className="mono">{getValue(row, ["route_id", "offer_route_id", "id"])}</span> },
                { key: "opportunity", header: "Opportunity", render: (row) => getValue(row, ["title", "opportunity_name", "opportunity_id", "campaign_code"]) },
                { key: "sponsor", header: "Sponsor", render: (row) => getValue(row, ["sponsor_code", "sponsor_name"]) },
                { key: "reward", header: "Reward", render: (row) => moneyValue(row, ["estimated_reward_amount", "estimated_commission_amount", "reward_amount", "commission_amount", "reward"], "0.00") },
                {
                  key: "link",
                  header: "Journey link",
                  render: (row) => <RouteLinkStatus offer={row} />,
                },
                {
                  key: "status",
                  header: "Status",
                  render: (row) => {
                    const status = getValue(row, ["status", "route_status"]);
                    return <StatusBadge label={status} tone={statusTone(status)} />;
                  },
                },
                {
                  key: "decision",
                  header: "Decision",
                  render: (row) => (
                    <OfferInboxActions
                      loadingKey={actionLoading}
                      offer={row}
                      onAccept={(offer) => decideOffer("accept", offer)}
                      onDecline={(offer) => decideOffer("decline", offer)}
                    />
                  ),
                },
              ]}
            />
          </section>

          <section className="panel" id="distributor-wallets">
            <div className="panel-header">
              <div>
                <PanelTitle
                  help="Distributor wallet balances by currency and status."
                  title="Wallets"
                />
                <div className="panel-subtitle">Balances available through the distributor portal.</div>
              </div>
            </div>
            <DataTable
              emptyText="No wallets returned for this distributor."
              rows={wallets}
              columns={[
                { key: "wallet", header: "Wallet", render: (row) => <span className="mono">{getValue(row, ["wallet_id", "id"])}</span> },
                { key: "currency", header: "Currency", render: (row) => getValue(row, ["currency"]) },
                { key: "available", header: "Available", render: (row) => moneyValue(row, ["available_balance", "balance"], "0.00") },
                { key: "held", header: "Held", render: (row) => moneyValue(row, ["held_balance", "hold_balance", "reserved_balance"], "0.00") },
                { key: "paid", header: "Paid out", render: (row) => moneyValue(row, ["paid_out_balance"], "0.00") },
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

          <section className="panel" id="distributor-wallet-ledger">
            <div className="panel-header">
              <div>
                <PanelTitle
                  help="Ledger entries explain how wallet balances moved over time."
                  title="Wallet ledger"
                />
                <div className="panel-subtitle">Recent movement history for the selected wallet.</div>
              </div>
            </div>
            <DataTable
              emptyText="No wallet ledger entries returned for this wallet."
              rows={walletLedger}
              columns={[
                { key: "type", header: "Type", render: (row) => getValue(row, ["transaction_type"]) },
                { key: "amount", header: "Amount", render: (row) => moneyValue(row, ["amount"], "0.00") },
                { key: "before", header: "Before", render: (row) => moneyValue(row, ["balance_before"], "0.00") },
                { key: "after", header: "After", render: (row) => moneyValue(row, ["balance_after"], "0.00") },
                { key: "created", header: "Created", render: (row) => <span className="mono">{getValue(row, ["created_at"])}</span> },
              ]}
            />
          </section>
        </>
      ) : null}
    </>
  );
}

type DistributorSafeStatusItem = {
  title: string;
  status: string;
  label: string;
  summary: string;
  next: string;
  actionCategory: string;
  sourceFamilies: string[];
  sourceConfidence: string;
  missingEvidence: Record<string, unknown>[];
  tone: BadgeTone;
};

function DistributorSafeStatusPanel({ summary }: { summary: DistributorSafeStatusItem[] }) {
  return (
    <section className="panel" id="distributor-safe-status">
      <div className="panel-header">
        <div>
          <PanelTitle
            help="Distributor-safe status uses role-scoped projection fields where available. It hides raw tenant, provider, funding, settlement, audit, and private customer details."
            title="Distributor safe status"
          />
          <div className="panel-subtitle">
            Partner-safe onboarding, participation, route, outcome, commission, and support signals.
          </div>
        </div>
        <StatusBadge
          label={summary.some((item) => item.status === "ACTION_REQUIRED") ? "Action required" : "Safe view"}
          tone={summary.some((item) => item.status === "ACTION_REQUIRED") ? "warning" : "success"}
        />
      </div>
      <div className="panel-body route-list">
        {summary.map((item) => (
          <div className="route-item" key={item.title}>
            <div>
              <div className="route-name">{item.title}</div>
              <div className="route-path">{item.summary}</div>
              <div className="route-path">{item.next}</div>
              <div className="table-subtext">
                Action: {safeDisplay(item.actionCategory)} | Source:{" "}
                {item.sourceFamilies.length ? item.sourceFamilies.map(safeDisplay).join(", ") : "safe projection"} | Confidence:{" "}
                {safeDisplay(item.sourceConfidence)}
              </div>
              {item.missingEvidence.length ? (
                <div className="table-subtext">
                  Missing evidence:{" "}
                  {item.missingEvidence
                    .map((evidence) =>
                      [
                        safeDisplay(getNestedValue(evidence, ["section"], "unknown")),
                        safeDisplay(getNestedValue(evidence, ["code"], "NO_SOURCE_EVIDENCE")),
                        safeDisplay(getNestedValue(evidence, ["severity"], "INFO")),
                      ].join(" / "),
                    )
                    .join("; ")}
                </div>
              ) : null}
            </div>
            <StatusBadge label={item.label} tone={item.tone} />
          </div>
        ))}
      </div>
    </section>
  );
}

function ConversionSafeStatus({ row }: { row: Record<string, unknown> }) {
  const item = conversionSafeStatusItem(row);
  return (
    <div>
      <StatusBadge label={item.label} tone={item.tone} />
      <div className="table-subtext">{item.next}</div>
      {item.missingEvidence.length ? (
        <div className="table-subtext">
          Missing evidence:{" "}
          {item.missingEvidence
            .map((evidence) => safeDisplay(getNestedValue(evidence, ["code"], "NO_SOURCE_EVIDENCE")))
            .join(", ")}
        </div>
      ) : null}
    </div>
  );
}

function getDistributorSafeStatusSummary({
  conversionRows,
  profile,
  offers,
  performance,
  wallets,
  attributedConversions,
  unlinkedConversions,
}: {
  conversionRows: Record<string, unknown>[];
  profile: unknown;
  offers: Record<string, unknown>[];
  performance: unknown;
  wallets: Record<string, unknown>[];
  attributedConversions: number;
  unlinkedConversions: number;
}): DistributorSafeStatusItem[] {
  const conversionItems = conversionRows.map(conversionSafeStatusItem);
  const firstAction = conversionItems.find((item) => item.status === "ACTION_REQUIRED");
  const firstMissing = conversionItems.find((item) => item.missingEvidence.length);
  const completed = conversionItems.filter((item) => item.status === "FULFILLED").length;
  const inProgress = conversionItems.filter((item) => item.status === "IN_PROGRESS").length;
  const actionRequired = conversionItems.filter((item) => item.status === "ACTION_REQUIRED").length;
  const distributorStatus = String(getNestedValue(profile, ["status"], "") || "");
  const routed = offers.filter((offer) => getValue(offer, ["route_status", "status"]) === "ROUTED").length;
  const accepted = Number(getNestedValue(performance, ["accepted_count"], 0)) || 0;
  const commissionTotal = numberValue(getNestedValue(performance, ["total_commission_amount"], "0"));
  const availableBalance = numberValue(getNestedValue(performance, ["wallet_available_balance"], "0"));

  return [
    {
      title: "Distributor onboarding status",
      ...buildLocalSafeStatus({
        status: distributorStatus === "ACTIVE" ? "APPROVED" : distributorStatus ? "ACTION_REQUIRED" : "UNAVAILABLE",
        label: distributorStatus === "ACTIVE" ? "Ready" : distributorStatus ? "Needs review" : "Unavailable",
        summary:
          distributorStatus === "ACTIVE"
            ? "Distributor profile is active and can participate in visible opportunities."
            : distributorStatus
              ? "Distributor profile needs support review before new participation is assumed."
              : "Distributor profile status is not available in this response.",
        next:
          distributorStatus === "ACTIVE"
            ? "No distributor profile action is required."
            : "Confirm onboarding status with support before treating this distributor as ready.",
        actionCategory: distributorStatus === "ACTIVE" ? "NONE" : "COMPLETE_PROFILE",
        sourceFamilies: ["profile"],
        sourceConfidence: distributorStatus ? "MEDIUM" : "LOW",
      }),
    },
    {
      title: "Campaign / opportunity participation status",
      ...buildLocalSafeStatus({
        status: accepted > 0 ? "APPROVED" : routed > 0 ? "PENDING" : "UNAVAILABLE",
        label: accepted > 0 ? "Participating" : routed > 0 ? "Review offers" : "Unavailable",
        summary:
          accepted > 0
            ? `${accepted} accepted route${accepted === 1 ? "" : "s"} can support active distribution work.`
            : routed > 0
              ? `${routed} routed offer${routed === 1 ? "" : "s"} need a visible decision.`
              : "No routed or accepted opportunities were returned for this distributor.",
        next:
          routed > 0 && accepted === 0
            ? "Review routed offers in the offer decision panel."
            : "Monitor opportunities as producer demand changes.",
        actionCategory: routed > 0 && accepted === 0 ? "ACCEPT_OFFER" : "NONE",
        sourceFamilies: ["campaign"],
        sourceConfidence: offers.length ? "MEDIUM" : "LOW",
      }),
    },
    {
      title: "Route / link / code readiness status",
      ...buildLocalSafeStatus({
        status: unlinkedConversions > 0 ? "PENDING" : attributedConversions > 0 ? "APPROVED" : "UNAVAILABLE",
        label: unlinkedConversions > 0 ? "Needs link" : attributedConversions > 0 ? "Linked" : "Unavailable",
        summary:
          unlinkedConversions > 0
            ? `${unlinkedConversions} customer journey${unlinkedConversions === 1 ? "" : "ies"} still need route attribution.`
            : attributedConversions > 0
              ? "Visible customer journeys are linked to distributor routes."
              : "No route-linked customer journeys were returned.",
        next:
          unlinkedConversions > 0
            ? "Use accepted routes and referral tracks to complete attribution."
            : "No route-link action is required right now.",
        actionCategory: unlinkedConversions > 0 ? "WAITING_FOR_EVENT" : "NONE",
        sourceFamilies: ["campaign", "outcome"],
        sourceConfidence: conversionRows.length ? "MEDIUM" : "LOW",
      }),
    },
    {
      title: "Outcome progress status",
      ...buildLocalSafeStatus({
        status: actionRequired > 0 ? "ACTION_REQUIRED" : inProgress > 0 ? "IN_PROGRESS" : completed > 0 ? "FULFILLED" : "UNAVAILABLE",
        label:
          actionRequired > 0
            ? "Action required"
            : inProgress > 0
              ? "In progress"
              : completed > 0
                ? "Fulfilled"
                : "Unavailable",
        summary: conversionRows.length
          ? `${completed} fulfilled, ${inProgress} in progress, ${actionRequired} need support review.`
          : "No customer conversion journeys were returned.",
        next:
          firstAction?.next ||
          firstMissing?.next ||
          "Watch the safe status shown on each customer conversion row.",
        actionCategory: firstAction?.actionCategory || firstMissing?.actionCategory || "NONE",
        sourceFamilies: ["outcome"],
        sourceConfidence: conversionRows.length ? "MEDIUM" : "LOW",
        missingEvidence: firstMissing?.missingEvidence || [],
      }),
    },
    {
      title: "Reward / commission status",
      ...buildLocalSafeStatus({
        status: commissionTotal > 0 || availableBalance > 0 ? "APPROVED" : wallets.length ? "PENDING" : "UNAVAILABLE",
        label: commissionTotal > 0 || availableBalance > 0 ? "Visible" : wallets.length ? "Pending" : "Unavailable",
        summary:
          commissionTotal > 0 || availableBalance > 0
            ? "Commission and earning signals are visible in safe business language."
            : wallets.length
              ? "Wallet context exists, but no visible commission movement is available yet."
              : "No wallet or commission context was returned.",
        next:
          commissionTotal > 0 || availableBalance > 0
            ? "Continue monitoring visible earning and wallet readiness signals."
            : "Wait for qualified outcomes or support-confirmed earning evidence.",
        actionCategory: "NONE",
        sourceFamilies: ["commission", "wallet"],
        sourceConfidence: wallets.length || commissionTotal > 0 ? "MEDIUM" : "LOW",
      }),
    },
    {
      title: "Support / next action guidance",
      ...buildLocalSafeStatus({
        status: firstAction ? "ACTION_REQUIRED" : firstMissing ? "PENDING" : "APPROVED",
        label: firstAction ? "Contact support" : firstMissing ? "Waiting" : "No action",
        summary: firstAction?.summary || firstMissing?.summary || "No support action is required from visible safe status evidence.",
        next: firstAction?.next || firstMissing?.next || "Continue monitoring offers, journeys, and safe status changes.",
        actionCategory: firstAction?.actionCategory || firstMissing?.actionCategory || "NONE",
        sourceFamilies: firstAction?.sourceFamilies || firstMissing?.sourceFamilies || ["outcome"],
        sourceConfidence: firstAction?.sourceConfidence || firstMissing?.sourceConfidence || "MEDIUM",
        missingEvidence: firstAction?.missingEvidence || firstMissing?.missingEvidence || [],
      }),
    },
  ];
}

function conversionSafeStatusItem(row: Record<string, unknown>): DistributorSafeStatusItem {
  const safeStatus = getNestedValue(row, ["distributor_safe_status"], null);
  if (safeStatus && typeof safeStatus === "object") {
    const record = safeStatus as Record<string, unknown>;
    const status = safeDisplay(getNestedValue(record, ["status"], "UNAVAILABLE"));
    return {
      title: safeDisplay(getNestedValue(row, ["display_status", "status"], "Customer journey")),
      status,
      label: safeDisplay(getNestedValue(record, ["label"], statusLabel(status))),
      summary: safeDisplay(getNestedValue(record, ["summary"], "Status is available for this distributor view.")),
      next: safeDisplay(getNestedValue(record, ["what_happens_next"], "Continue monitoring this journey.")),
      actionCategory: safeDisplay(getNestedValue(record, ["action_category"], "NOT_AVAILABLE")),
      sourceFamilies: asArray(getNestedValue(record, ["source_families"], [])).map(safeDisplay),
      sourceConfidence: safeDisplay(getNestedValue(record, ["source_confidence"], "LOW")),
      missingEvidence: asArray(getNestedValue(record, ["missing_evidence"], [])) as Record<string, unknown>[],
      tone: safeStatusTone(status),
    };
  }

  const fallbackStatus = getValue(row, ["is_complete"], "false") === "true" ? "FULFILLED" : "UNAVAILABLE";
  return {
    title: safeDisplay(getNestedValue(row, ["display_status", "status"], "Customer journey")),
    ...buildLocalSafeStatus({
      status: fallbackStatus,
      label: fallbackStatus === "FULFILLED" ? "Fulfilled" : "Unavailable",
      summary:
        fallbackStatus === "FULFILLED"
          ? "Customer journey is complete, but the dedicated safe-status projection was not returned."
          : "Safe distributor status is not available in this response.",
      next:
        fallbackStatus === "FULFILLED"
          ? "No action is required from this row."
          : "Check again when the portal response includes distributor_safe_status.",
      actionCategory: fallbackStatus === "FULFILLED" ? "NONE" : "NOT_AVAILABLE",
      sourceFamilies: ["outcome"],
      sourceConfidence: "LOW",
      missingEvidence: [
        {
          section: "safe_status",
          code: "NO_SOURCE_EVIDENCE",
          severity: "INFO",
        },
      ],
    }),
  };
}

function buildLocalSafeStatus({
  status,
  label,
  summary,
  next,
  actionCategory,
  sourceFamilies,
  sourceConfidence,
  missingEvidence = [],
}: {
  status: string;
  label: string;
  summary: string;
  next: string;
  actionCategory: string;
  sourceFamilies: string[];
  sourceConfidence: string;
  missingEvidence?: Record<string, unknown>[];
}): Omit<DistributorSafeStatusItem, "title"> {
  return {
    status,
    label,
    summary,
    next,
    actionCategory,
    sourceFamilies,
    sourceConfidence,
    missingEvidence,
    tone: safeStatusTone(status),
  };
}

function safeStatusTone(status: string): BadgeTone {
  if (["FULFILLED", "SETTLED", "APPROVED", "QUALIFIED"].includes(status)) {
    return "success";
  }
  if (["PENDING", "IN_PROGRESS"].includes(status)) {
    return "info";
  }
  if (["ACTION_REQUIRED", "UNAVAILABLE", "ADJUSTED"].includes(status)) {
    return "warning";
  }
  if (["DECLINED", "EXPIRED"].includes(status)) {
    return "neutral";
  }
  return "neutral";
}

function statusLabel(status: string): string {
  return status
    .toLowerCase()
    .split("_")
    .map((part) => part.slice(0, 1).toUpperCase() + part.slice(1))
    .join(" ");
}

function safeDisplay(value: unknown): string {
  return formatDisplay(value).replace(/tenant_code/gi, "internal tenant reference").replace(/ucn/gi, "private identifier");
}

function OutcomeMoneyReviewPanel({ review, title }: { review: unknown; title: string }) {
  const summary = getNestedValue(review, ["summary"], {});
  const attentionItems = asArray(getNestedValue(review, ["attention_items"], []));
  const guardrails = asArray(getNestedValue(review, ["guardrails"], []));
  const completed = getNestedValue(summary, ["completed_outcome_count"], 0);
  const attention = Number(getNestedValue(summary, ["attention_count"], 0)) || 0;
  const adminReview = Number(getNestedValue(summary, ["admin_review_count"], 0)) || 0;

  return (
    <section className="panel" id="distributor-outcome-money">
      <div className="panel-header">
        <div>
          <PanelTitle
            help="Role-scoped outcome-to-money review. Distributor users see commission and wallet evidence without Admin repair controls."
            title={title}
          />
          <div className="panel-subtitle">Completed outcomes traced into distributor-owned money evidence.</div>
        </div>
        <StatusBadge label={attention ? `${attention} need review` : "Ready"} tone={attention ? "warning" : "success"} />
      </div>
      <div className="panel-body">
        <div className="summary-grid">
          <SummaryItem label="Completed" value={completed} />
          <SummaryItem label="Ready" value={getNestedValue(summary, ["ready_count"], 0)} />
          <SummaryItem label="Distributor review" value={attention} />
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
          )) : <div className="empty-state">No distributor-owned money gaps returned.</div>}
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

function SelectedOfferSummary({ offer }: { offer?: Record<string, unknown> }) {
  if (!offer) {
    return <div className="state-panel">No routed offer selected.</div>;
  }

  return (
    <SummaryGrid
      actionResult
      items={[
        ["Opportunity", getValue(offer, ["title", "opportunity_code", "opportunity_id"])],
        ["Sponsor", getValue(offer, ["sponsor_code", "sponsor_name"])],
        ["Reward", moneyValue(offer, ["estimated_reward_amount", "estimated_commission_amount", "reward_amount"], "0.00")],
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
        ["Currency", getValue(wallet, ["currency"])],
        ["Available", moneyValue(wallet, ["available_balance"], "0.00")],
        ["Held", moneyValue(wallet, ["held_balance"], "0.00")],
      ]}
    />
  );
}

function OfferInboxActions({
  offer,
  loadingKey,
  onAccept,
  onDecline,
}: {
  offer: Record<string, unknown>;
  loadingKey: string | null;
  onAccept: (offer: Record<string, unknown>) => void;
  onDecline: (offer: Record<string, unknown>) => void;
}) {
  const routeId = getValue(offer, ["route_id", "offer_route_id", "id"], "");
  const status = getValue(offer, ["route_status", "status"], "");
  const canDecide = Boolean(routeId && status === "ROUTED" && !loadingKey);

  if (status !== "ROUTED") {
    return <span className="muted">Decided</span>;
  }

  return (
    <div className="action-button-row">
      <button className="button" disabled={!canDecide} type="button" onClick={() => onAccept(offer)}>
        <Send size={16} />
        Accept
      </button>
      <button className="button secondary" disabled={!canDecide} type="button" onClick={() => onDecline(offer)}>
        <XCircle size={16} />
        Decline
      </button>
    </div>
  );
}

function PortalActionResult({ payload }: { payload: Record<string, unknown> }) {
  const result = (payload.result && typeof payload.result === "object" ? payload.result : {}) as Record<string, unknown>;
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <h2 className="panel-title">Action result</h2>
          <div className="panel-subtitle">{getValue(payload, ["action"], "Portal action")} completed.</div>
        </div>
        <StatusBadge label="Updated" tone="success" />
      </div>
      <div className="panel-body">
        <div className="summary-grid">
          <SummaryItem label="Route" value={getValue(result, ["route_id"], "-")} />
          <SummaryItem label="Opportunity" value={getValue(result, ["opportunity_id"], "-")} />
          <SummaryItem label="Status" value={getValue(result, ["route_status", "status"], "-")} />
        </div>
      </div>
    </section>
  );
}

function offerLabel(offer: Record<string, unknown>): string {
  const linkState = getValue(offer, ["has_referral_link"], "false") === "true" ? "linked" : "needs journey";
  return `${getValue(offer, ["title", "opportunity_code", "opportunity_id"])} | ${moneyValue(
    offer,
    ["estimated_reward_amount", "estimated_commission_amount", "reward_amount"],
    "0.00",
  )} | ${linkState}`;
}

function RouteLinkStatus({ offer }: { offer: Record<string, unknown> }) {
  const hasLink = getValue(offer, ["has_referral_link"], "false") === "true";
  const linkCount = getValue(offer, ["referral_link_count"], "0");
  const latestTrack = getValue(offer, ["latest_referral_track_id"], "");

  return (
    <div>
      <StatusBadge label={hasLink ? `${formatDisplay(linkCount)} linked` : "Needs journey"} tone={hasLink ? "success" : "warning"} />
      <div className="table-subtext mono">{latestTrack || "No referral track"}</div>
    </div>
  );
}

function walletLabel(wallet: Record<string, unknown>): string {
  return `${getValue(wallet, ["currency"])} | ${moneyValue(wallet, ["available_balance"], "0.00")} available`;
}

function formatList(value: unknown): string {
  if (Array.isArray(value)) {
    return value.length ? value.join(", ") : "-";
  }

  return formatDisplay(value);
}

function conversionNextStep(row: Record<string, unknown>): string {
  if (getValue(row, ["is_complete"], "false") === "true") {
    return "Reward and settlement review";
  }

  const explicitNext = getValue(row, ["next_milestone"], "");
  if (explicitNext) {
    return explicitNext;
  }

  if (!getValue(row, ["ucn_captured_at"], "")) {
    return "Capture customer identity";
  }
  if (!getValue(row, ["account_opened_at"], "")) {
    return "Open account";
  }
  if (!getValue(row, ["account_activated_at"], "")) {
    return "Activate account";
  }
  if (!getValue(row, ["funded_at"], "")) {
    return "Fund account";
  }
  if (
    !getValue(row, ["salary_switched_at"], "") &&
    !getValue(row, ["debit_order_switched_at"], "") &&
    !getValue(row, ["first_transaction_completed_at"], "")
  ) {
    return "Confirm salary, debit order, or first transaction";
  }

  return "Review conversion outcome";
}

type RecognitionErrorPayload = {
  recognitionError: string;
  recognitionKind: string;
};

function isRecognitionError(payload: unknown): payload is RecognitionErrorPayload {
  return Boolean(
    payload &&
      typeof payload === "object" &&
      "recognitionError" in payload &&
      "recognitionKind" in payload,
  );
}

function extractRecognitionPayload(payload: unknown): unknown {
  return isRecognitionError(payload) ? null : payload;
}

function countRecognitionItems(payload: unknown): number {
  if (!payload || typeof payload !== "object") {
    return 0;
  }

  const count = getNestedValue(payload, ["count"], undefined);
  if (typeof count === "number") {
    return count;
  }

  return asArray(payload).length;
}

function countRecognitionProgress(payload: unknown): number {
  if (!payload || typeof payload !== "object") {
    return 0;
  }

  const total = getNestedValue(payload, ["totalReferrals"], getNestedValue(payload, ["total_referrals"], undefined));
  if (typeof total === "number") {
    return total;
  }

  return asArray(payload).length;
}

function countRecognitionMissions(payload: unknown): number {
  if (!payload || typeof payload !== "object") {
    return 0;
  }

  const total = getNestedValue(payload, ["totalCount"], getNestedValue(payload, ["total_count"], undefined));
  if (typeof total === "number") {
    return total;
  }

  const record = payload as Record<string, unknown>;
  return ["core", "boost", "milestone"].reduce((sum, key) => {
    const value = record[key];
    return sum + (Array.isArray(value) ? value.length : 0);
  }, 0);
}

type BadgeTone = GuardrailTone;

type Guardrail = {
  badge: string;
  tone: BadgeTone;
  title: string;
  copy: string;
  items: GuardrailItem[];
};

function getOfferDecisionGuardrail({
  selectedOffer,
  selectedOfferStatus,
  actionLoading,
}: {
  selectedOffer: Record<string, unknown> | undefined;
  selectedOfferStatus: string;
  actionLoading: string | null;
}): Guardrail {
  if (!selectedOffer) {
    return {
      badge: "Blocked",
      tone: "neutral",
      title: "Select a routed offer",
      copy: "Offer actions are disabled until a routed offer is available.",
      items: [
        { label: "Selected offer", value: "Missing", tone: "warning" },
        { label: "Decision", value: "None", tone: "neutral" },
        { label: "System change", value: "None", tone: "success" },
      ],
    };
  }

  if (actionLoading) {
    return {
      badge: "Running",
      tone: "info",
      title: "Offer decision in progress",
      copy: "Wait for the response before accepting or declining another offer.",
      items: [
        { label: "Current action", value: actionLoading, tone: "info" },
        { label: "Offer status", value: selectedOfferStatus, tone: statusTone(selectedOfferStatus) as BadgeTone },
        { label: "System change", value: "Route status", tone: "warning" },
      ],
    };
  }

  const ready = selectedOfferStatus === "ROUTED";
  return {
    badge: ready ? "Ready" : "Blocked",
    tone: ready ? "success" : "neutral",
    title: ready ? "Offer can be accepted or declined" : "Offer already has a decision",
    copy: ready
      ? "Accepting confirms the matched opportunity. Declining records that the distributor will not take this route."
      : "Only routed offers can be actioned from this portal.",
    items: [
      { label: "Offer status", value: selectedOfferStatus, tone: statusTone(selectedOfferStatus) as BadgeTone },
      { label: "Decision", value: ready ? "Accept or decline" : "None", tone: ready ? "success" : "neutral" },
      { label: "System change", value: ready ? "Route status" : "None", tone: ready ? "warning" : "success" },
    ],
  };
}

function getConversionLinkGuardrail({
  selectedOffer,
  referralTrackId,
  actionLoading,
}: {
  selectedOffer: Record<string, unknown> | undefined;
  referralTrackId: string;
  actionLoading: string | null;
}): Guardrail {
  if (!selectedOffer) {
    return {
      badge: "Blocked",
      tone: "neutral",
      title: "Accept an offer first",
      copy: "A customer journey can only be linked after the distributor has accepted an offer route.",
      items: [
        { label: "Accepted route", value: "Missing", tone: "warning" },
        { label: "Referral track", value: referralTrackId.trim() ? "Provided" : "Missing", tone: referralTrackId.trim() ? "success" : "warning" },
        { label: "System change", value: "None", tone: "success" },
      ],
    };
  }

  if (actionLoading) {
    return {
      badge: "Running",
      tone: "info",
      title: "Linking customer journey",
      copy: "Wait for the response before linking another customer journey.",
      items: [
        { label: "Current action", value: actionLoading, tone: "info" },
        { label: "Accepted route", value: getValue(selectedOffer, ["route_id", "id"], "-"), tone: "success" },
        { label: "System change", value: "Route attribution", tone: "warning" },
      ],
    };
  }

  const hasReferral = Boolean(referralTrackId.trim());
  return {
    badge: hasReferral ? "Ready" : "Needs track",
    tone: hasReferral ? "success" : "warning",
    title: hasReferral ? "Ready to link route and customer journey" : "Enter the referral track",
    copy: hasReferral
      ? "This will make the accepted offer traceable to a specific customer conversion journey."
      : "The referral track is created when the customer validates or starts their referred journey.",
    items: [
      { label: "Accepted route", value: getValue(selectedOffer, ["route_id", "id"], "-"), tone: "success" },
      { label: "Referral track", value: hasReferral ? "Provided" : "Missing", tone: hasReferral ? "success" : "warning" },
      { label: "System change", value: "Route attribution", tone: "warning" },
    ],
  };
}

function getDistributorAttributionGuardrail({
  conversionCount,
  attributedConversions,
  unlinkedConversions,
  attributionRate,
}: {
  conversionCount: number;
  attributedConversions: number;
  unlinkedConversions: number;
  attributionRate: string;
}): Guardrail {
  if (conversionCount <= 0) {
    return {
      badge: "Waiting",
      tone: "neutral",
      title: "No customer journeys yet",
      copy: "Customer journeys will appear after customers validate or start a referred journey.",
      items: [
        { label: "Journeys", value: "0", tone: "neutral" },
        { label: "Linked journeys", value: "0", tone: "neutral" },
        { label: "Next action", value: "Wait for journey", tone: "info" },
      ],
    };
  }

  if (unlinkedConversions > 0) {
    return {
      badge: "Needs link",
      tone: "warning",
      title: "Link customer journeys to accepted routes",
      copy: "Some journeys are not tied to accepted demand yet. Link them so earnings, recognition, and producer reporting can trace the work correctly.",
      items: [
        { label: "Unlinked journeys", value: String(unlinkedConversions), tone: "warning" },
        { label: "Linked journeys", value: String(attributedConversions), tone: attributedConversions > 0 ? "success" : "neutral" },
        { label: "Attribution rate", value: attributionRate, tone: "warning" },
      ],
    };
  }

  return {
    badge: "Linked",
    tone: "success",
    title: "Customer journeys are route-attributed",
    copy: "Visible journeys are linked to accepted demand, so performance and earning signals can use route attribution.",
    items: [
      { label: "Unlinked journeys", value: "0", tone: "success" },
      { label: "Linked journeys", value: String(attributedConversions), tone: "success" },
      { label: "Attribution rate", value: attributionRate, tone: "success" },
    ],
  };
}

function getDistributorGuidance({
  hasDistributor,
  profile,
  performance,
  offers,
  conversions,
  wallets,
  routedOfferCount,
}: {
  hasDistributor: boolean;
  profile: unknown;
  performance: unknown;
  offers: Record<string, unknown>[];
  conversions: Record<string, unknown>[];
  wallets: Record<string, unknown>[];
  routedOfferCount: number;
}): {
  badge: string;
  tone: BadgeTone;
  title: string;
  copy: string;
  steps: JourneyStep[];
} {
  const distributorStatus = String(getNestedValue(profile, ["status"], "-"));
  const acceptedCount = numberValue(getNestedValue(performance, ["accepted_count"], "0"));
  const availableBalance = numberValue(getNestedValue(performance, ["wallet_available_balance"], "0"));
  const completedConversions = conversions.filter((item) => getValue(item, ["is_complete"], "false") === "true").length;
  const hasWallet = wallets.length > 0;
  const profileState = distributorProfileStepState(distributorStatus);

  if (!hasDistributor) {
    return {
      badge: "Load",
      tone: "info",
      title: "Load distributor",
      copy: "Enter the tenant and distributor code to see opportunities, routed offers, wallet balances, and performance.",
      steps: distributorSteps("current", "waiting", "waiting", "waiting", "waiting"),
    };
  }

  if (profileState === "blocked") {
    return {
      badge: distributorStatus,
      tone: "warning",
      title: "Distributor is not active",
      copy: "The distributor profile is loaded, but the current status may prevent new offer activity until the lifecycle state is resolved.",
      steps: distributorSteps("blocked", "waiting", "waiting", hasWallet ? "review" : "waiting", "waiting"),
    };
  }

  if (routedOfferCount > 0) {
    return {
      badge: "Offers",
      tone: "info",
      title: "Decide on routed offers",
      copy: "There are routed offers waiting for the distributor to accept or decline. Action those offers before focusing on wallet movement.",
      steps: distributorSteps(profileState, "current", acceptedCount > 0 ? "done" : "waiting", hasWallet ? "done" : "waiting", "waiting"),
    };
  }

  if (!offers.length) {
    return {
      badge: "No offers",
      tone: "neutral",
      title: "Wait for matched opportunities",
      copy: "No matched opportunities are currently available for this distributor. Keep the profile and wallet ready for new routed offers.",
      steps: distributorSteps(profileState, "waiting", "waiting", hasWallet ? "done" : "waiting", "waiting"),
    };
  }

  if (acceptedCount > 0 && !conversions.length) {
    return {
      badge: "Conversions",
      tone: "info",
      title: "Wait for customer journey events",
      copy: "Offers have been accepted, but no customer conversion journeys are visible yet. The next step is referral validation or activation events flowing into the journey engine.",
      steps: distributorSteps(profileState, "done", "done", hasWallet ? "done" : "waiting", "current"),
    };
  }

  if (conversions.length && completedConversions === 0) {
    return {
      badge: "In progress",
      tone: "info",
      title: "Customer journeys are moving",
      copy: "Customer journeys are visible, but none have completed yet. Watch the next-step column for the missing activation or switch signal.",
      steps: distributorSteps(profileState, "done", acceptedCount > 0 ? "done" : "waiting", hasWallet ? "done" : "waiting", "current"),
    };
  }

  if (!hasWallet || availableBalance <= 0) {
    return {
      badge: "Earnings",
      tone: hasWallet ? "info" : "warning",
      title: hasWallet ? "Monitor earnings movement" : "Confirm wallet setup",
      copy: hasWallet
        ? "Offers are visible, but wallet balance is not showing available earnings yet. Monitor accepted routes and ledger movement."
        : "Offers are visible, but no distributor wallet was returned. Confirm wallet setup before payout activity is expected.",
      steps: distributorSteps(profileState, "done", acceptedCount > 0 ? "done" : "waiting", hasWallet ? "current" : "current", "waiting"),
    };
  }

  return {
    badge: "Stable",
    tone: "success",
    title: "Distributor position is healthy",
    copy: "The distributor is loaded, offers are visible, wallet data is available, and performance can be monitored from this portal.",
    steps: distributorSteps(profileState, "done", acceptedCount > 0 ? "done" : "waiting", "done", "current"),
  };
}

function distributorSteps(
  identity: JourneyStep["state"],
  offers: JourneyStep["state"],
  acceptedWork: JourneyStep["state"],
  earnings: JourneyStep["state"],
  performance: JourneyStep["state"],
): JourneyStep[] {
  return [
    {
      label: "Load distributor",
      description: "Choose the tenant and distributor context for the portal.",
      workArea: "Distributor identity",
      targetId: "distributor-identity",
      state: identity,
    },
    {
      label: "Review offers",
      description: "Check matched opportunities and routed offers.",
      workArea: "Offer inbox",
      targetId: "distributor-offer-inbox",
      state: offers,
    },
    {
      label: "Accept work",
      description: "Accept or decline routed offers that need a decision.",
      workArea: "Offer decision",
      targetId: "distributor-offer-decision",
      state: acceptedWork,
    },
    {
      label: "Track earnings",
      description: "Review wallet balances and ledger movement.",
      workArea: "Wallet activity, wallets, and wallet ledger",
      targetId: "distributor-wallet-activity",
      state: earnings,
    },
    {
      label: "Monitor performance",
      description: "Watch routed, accepted, declined, and commission outcomes.",
      workArea: "Performance",
      targetId: "distributor-performance",
      state: performance,
    },
  ];
}

function distributorProfileStepState(status: string): JourneyStep["state"] {
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

function numberValue(value: unknown): number {
  const parsed = Number(String(value ?? "0").replace(/[^0-9.-]/g, ""));
  return Number.isFinite(parsed) ? parsed : 0;
}

function getCurrentDistributorRank(rows: Record<string, unknown>[], distributorCode: string): string {
  if (!rows.length) {
    return "#-";
  }

  const distributor = distributorCode.toLowerCase();
  const current = rows.find((row) => getValue(row, ["displayName", "display_name"], "").toLowerCase().includes(distributor));
  return `#${getValue(current || rows[0], ["rankPosition", "rank_position"], "-")}`;
}
