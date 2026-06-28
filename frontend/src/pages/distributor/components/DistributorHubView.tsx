import { ArrowRight, CheckCircle2, Clock3, Link2, Search, Sparkles, Star, Trophy, Wallet } from "lucide-react";

import { PanelTitle } from "../../../components/PanelTitle";
import { StatusBadge } from "../../../components/StatusBadge";
import {
  formatDisplay,
  getNestedValue,
  getValue,
  moneyValue,
  statusTone,
} from "../../pageUtils";

type DistributorHubViewProps = {
  acceptanceRate: string;
  acceptedCount: number;
  activeReferralCount: number;
  attributedConversions: number;
  completedConversions: number;
  conversionAttributionRate: string;
  conversionRows: Record<string, unknown>[];
  currentRank: string;
  distributorDisplayName: unknown;
  heroMomentum: string;
  leaderboardError: string | null;
  leaderboardRows: Record<string, unknown>[];
  leaderboardTotal: unknown;
  pendingRewards: string;
  performance: unknown;
  profile: unknown;
  referralPreviewRows: Record<string, unknown>[];
  routedCount: number;
  submitted: { tenantCode: string; distributorCode: string };
  selectedWallet?: Record<string, unknown>;
  topOfferRows: Record<string, unknown>[];
  totalCommission: string;
  unlinkedConversions: number;
  walletAvailable: string;
  walletCurrency: string;
};

export function DistributorHubView({
  acceptanceRate,
  acceptedCount,
  activeReferralCount,
  attributedConversions,
  completedConversions,
  conversionAttributionRate,
  conversionRows,
  currentRank,
  distributorDisplayName,
  heroMomentum,
  leaderboardError,
  leaderboardRows,
  leaderboardTotal,
  pendingRewards,
  performance,
  profile,
  referralPreviewRows,
  routedCount,
  selectedWallet,
  submitted,
  topOfferRows,
  totalCommission,
  unlinkedConversions,
  walletAvailable,
  walletCurrency,
}: DistributorHubViewProps) {
  return (
    <>
      <section className="earnings-command-header">
        <div className="earnings-breadcrumb">
          <span>Amplifi</span>
          <span>Earnings Hub</span>
          <strong>Distributor view</strong>
        </div>
        <div className="earnings-search">
          <Search size={16} />
          <input aria-label="Search campaigns, distributors, settlements" placeholder="Search campaigns, referrals, settlements..." />
        </div>
        <div className="earnings-header-actions">
          <a className="earnings-rank-pill" href="#distributor-leaderboard">
            <Star size={14} />
            Gold Distributor - Rank {currentRank}
          </a>
          <a className="button" href="/distributor/operations">
            <Link2 size={16} />
            Operations
          </a>
        </div>
      </section>

      <section className="earnings-page-hero">
        <div>
          <h1>My Earnings Hub</h1>
          <p>Track campaigns, referral journeys, reputation, wallet movement, and the next action that turns demand into income.</p>
        </div>
        <div className="earnings-identity-pill">
          <span>{String(distributorDisplayName).slice(0, 1) || "D"}</span>
          <strong>{formatDisplay(distributorDisplayName)}</strong>
          <small>{submitted.distributorCode || "Select distributor"}</small>
        </div>
      </section>

      <section className="earnings-hero-grid premium">
        <div className="earnings-hero-card premium">
          <div className="earnings-hero-topline">
            <div>
              <div className="earnings-hero-label">Earnings this month</div>
              <div className="earnings-hero-value">{totalCommission}</div>
            </div>
            <Wallet size={26} />
          </div>
          <div className="earnings-hero-sub">
            <Sparkles size={14} />
            {heroMomentum} - {conversionAttributionRate} referral attribution
          </div>
          <div className="earnings-mini-grid">
            <div>
              <span>Pending</span>
              <strong>{pendingRewards}</strong>
            </div>
            <div>
              <span>Wallet</span>
              <strong>{walletAvailable}</strong>
            </div>
            <div>
              <span>Currency</span>
              <strong>{walletCurrency}</strong>
            </div>
          </div>
        </div>

        <div className="earnings-dark-panel reputation-card">
          <div className="earnings-panel-head">
            <div>
              <PanelTitle help="Professional gamification signals for distributor quality and trust." title="Reputation" />
              <div className="panel-subtitle">Your standing</div>
            </div>
            <StatusBadge
              label={String(getNestedValue(profile, ["status"], "-"))}
              tone={statusTone(String(getNestedValue(profile, ["status"], "-")))}
            />
          </div>
          <div className="status-list spacious">
            <ReputationRow label="Acceptance rate" value={acceptanceRate} />
            <ReputationRow label="Trust score" value={getNestedValue(profile, ["trust_score"], "-")} />
            <ReputationRow label="Completed referrals" value={completedConversions} tone={completedConversions > 0 ? "success" : undefined} />
            <ReputationRow label="Active referrals" value={activeReferralCount} tone={activeReferralCount > 0 ? "success" : undefined} />
          </div>
        </div>
      </section>

      <section className="grid-2 earnings-workspace-grid premium">
        <div className="earnings-dark-panel">
          <div className="earnings-panel-head">
            <div>
              <PanelTitle help="Opportunities matched to this distributor, ranked around earning potential and fit." title="Opportunities for you" />
              <div className="panel-subtitle">Matched campaigns, offers, and earning routes.</div>
            </div>
            <StatusBadge label={`${topOfferRows.length} shown`} tone="info" />
          </div>
          <div className="earnings-card-list">
            {topOfferRows.length ? (
              topOfferRows.map((offer) => (
                <OpportunityCard
                  key={getValue(offer, ["route_id", "offer_route_id", "id"], getValue(offer, ["opportunity_id"]))}
                  offer={offer}
                />
              ))
            ) : (
              <div className="earnings-empty-card">No matched opportunities returned for this distributor.</div>
            )}
            <a className="earnings-outline-button" href="/admin/distribution">
              Browse marketplace
              <ArrowRight size={15} />
            </a>
          </div>
        </div>

        <div className="earnings-dark-panel">
          <div className="earnings-panel-head">
            <div>
              <PanelTitle help="Customer referral tracks attributed to this distributor, with status and next step." title="Existing referrals" />
              <div className="panel-subtitle">
                {completedConversions} complete - {activeReferralCount} active - {unlinkedConversions} need links
              </div>
            </div>
            <StatusBadge
              label={`${formatDisplay(attributedConversions)}/${formatDisplay(conversionRows.length)} linked`}
              tone={unlinkedConversions > 0 ? "warning" : attributedConversions > 0 ? "success" : "neutral"}
            />
          </div>
          <div className="referral-tracker-list">
            {referralPreviewRows.length ? (
              referralPreviewRows.map((row) => (
                <ReferralTrackerRow key={getValue(row, ["referral_track_id"], getValue(row, ["route_id"]))} row={row} />
              ))
            ) : (
              <div className="earnings-empty-card">
                Referral tracks will appear after customers validate or start their referred journey.
              </div>
            )}
          </div>
          <a className="earnings-outline-button" href="/distributor/operations#customer-conversions">
            Track all referrals
            <ArrowRight size={15} />
          </a>
        </div>
      </section>

      <section className="earnings-dark-panel leaderboard-feature" id="distributor-leaderboard">
        <div className="earnings-panel-head">
          <div>
            <PanelTitle
              help="Live recognition ranking from the tenant leaderboard service. It reflects referrer/progress scoring, not wallet payout order."
              title="Leaderboard"
            />
            <div className="panel-subtitle">Community handles only - {formatDisplay(leaderboardTotal)} ranked</div>
          </div>
          <Trophy size={20} />
        </div>
        {leaderboardRows.length ? (
          <div className="leaderboard-modern-list">
            {leaderboardRows.slice(0, 5).map((row) => (
              <LeaderboardRow
                key={`${getValue(row, ["rankPosition", "rank_position"], "-")}-${getValue(row, ["displayName", "display_name"], "-")}`}
                currentCode={submitted.distributorCode}
                row={row}
              />
            ))}
          </div>
        ) : (
          <div className="readiness-list">
            {leaderboardError ? <div className="earnings-empty-card">{leaderboardError}</div> : null}
            <ReadinessRow
              label="Accept routed offers"
              value={`${acceptedCount}/${routedCount}`}
              copy="Accepted routes are the clearest signal that this distributor can convert demand."
              tone={acceptedCount > 0 ? "success" : routedCount > 0 ? "warning" : "neutral"}
            />
            <ReadinessRow
              label="Keep wallet moving"
              value={walletAvailable}
              copy="Available balance confirms earnings are visible and payout readiness can be reviewed."
              tone={
                Number(getNestedValue(performance, ["wallet_available_balance"], getValue(selectedWallet || {}, ["available_balance"], "0"))) > 0
                  ? "success"
                  : "neutral"
              }
            />
          </div>
        )}
      </section>
    </>
  );
}

function OpportunityCard({ offer }: { offer: Record<string, unknown> }) {
  const status = getValue(offer, ["route_status", "status"], "Available");
  const initials = getInitials(getValue(offer, ["title", "opportunity_name", "campaign_name", "opportunity_id"], "OP"));

  return (
    <div className="opportunity-card">
      <span className="opportunity-avatar">{initials}</span>
      <div>
        <strong>{getValue(offer, ["title", "opportunity_name", "campaign_name", "opportunity_id"])}</strong>
        <p>
          {getValue(offer, ["sponsor_code", "sponsor_name", "category"], "Campaign")} -{" "}
          {getValue(offer, ["vertical", "product_category"], "matched route")}
        </p>
      </div>
      <div className="opportunity-reward">
        <strong>{moneyValue(offer, ["estimated_reward_amount", "estimated_commission_amount", "reward_amount"], "0.00")}</strong>
        <span>{status}</span>
      </div>
    </div>
  );
}

function ReferralTrackerRow({ row }: { row: Record<string, unknown> }) {
  const isComplete = getValue(row, ["is_complete"], "false") === "true";
  const progress = Math.max(0, Math.min(100, numberValue(getValue(row, ["progress_percent"], "0"))));
  const title = getValue(row, ["opportunity_title", "opportunity_code", "campaign_code"], "Referral journey");
  const trackId = getValue(row, ["referral_track_id"], "-");
  const safeStatus = distributorSafeStatus(row);

  return (
    <div className="referral-tracker-row">
      <div className={isComplete ? "referral-state-dot complete" : "referral-state-dot"}>
        {isComplete ? <CheckCircle2 size={15} /> : <Clock3 size={15} />}
      </div>
      <div>
        <strong>{title}</strong>
        <p>{safeStatus.next}</p>
        <span className="mono">{trackId}</span>
      </div>
      <div className="referral-progress">
        <StatusBadge label={safeStatus.label} tone={safeStatus.tone} />
        <div>
          <i style={{ width: `${progress}%` }} />
        </div>
      </div>
    </div>
  );
}

function LeaderboardRow({ row, currentCode }: { row: Record<string, unknown>; currentCode: string }) {
  const displayName = getValue(row, ["displayName", "display_name"], "-");
  const isCurrent = displayName.toLowerCase().includes(currentCode.toLowerCase()) && Boolean(currentCode);

  return (
    <div className={isCurrent ? "leaderboard-modern-row current" : "leaderboard-modern-row"}>
      <span>{getValue(row, ["rankPosition", "rank_position"], "-")}</span>
      <strong>{displayName}</strong>
      <small>{getValue(row, ["rankedTier", "rank_tier"], "-")}</small>
      <em>{getValue(row, ["totalScore", "total_score"], "0")}</em>
    </div>
  );
}

function ReputationRow({
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

function ReadinessRow({
  label,
  value,
  copy,
  tone,
}: {
  label: string;
  value: unknown;
  copy: string;
  tone: "success" | "warning" | "danger" | "info" | "neutral";
}) {
  return (
    <div className="readiness-row">
      <div>
        <div className="readiness-label">{label}</div>
        <div className="readiness-copy">{copy}</div>
      </div>
      <StatusBadge label={formatDisplay(value)} tone={tone} />
    </div>
  );
}

function conversionNextStep(row: Record<string, unknown>): string {
  if (getValue(row, ["is_complete"], "false") === "true") {
    return "Completed";
  }
  const explicit = getValue(row, ["next_milestone"], "");
  if (explicit) {
    return explicit;
  }
  return "Continue customer journey";
}

function distributorSafeStatus(row: Record<string, unknown>): {
  label: string;
  next: string;
  tone: "success" | "warning" | "danger" | "info" | "neutral";
} {
  const safeStatus = getNestedValue(row, ["distributor_safe_status"], null);
  if (safeStatus && typeof safeStatus === "object") {
    const status = getValue(safeStatus as Record<string, unknown>, ["status"], "UNAVAILABLE");
    return {
      label: getValue(safeStatus as Record<string, unknown>, ["label"], statusLabel(status)),
      next: getValue(safeStatus as Record<string, unknown>, ["what_happens_next"], conversionNextStep(row)),
      tone: safeStatusTone(status),
    };
  }

  return {
    label: getValue(row, ["is_complete"], "false") === "true" ? "Fulfilled" : "Unavailable",
    next:
      getValue(row, ["is_complete"], "false") === "true"
        ? "No action is required."
        : "Safe status is not available yet.",
    tone: getValue(row, ["is_complete"], "false") === "true" ? "success" : "warning",
  };
}

function safeStatusTone(status: string): "success" | "warning" | "danger" | "info" | "neutral" {
  if (["FULFILLED", "SETTLED", "APPROVED", "QUALIFIED"].includes(status)) {
    return "success";
  }
  if (["PENDING", "IN_PROGRESS"].includes(status)) {
    return "info";
  }
  if (["ACTION_REQUIRED", "UNAVAILABLE", "ADJUSTED"].includes(status)) {
    return "warning";
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

function numberValue(value: unknown): number {
  const parsed = Number(String(value ?? "0").replace(/[^0-9.-]/g, ""));
  return Number.isFinite(parsed) ? parsed : 0;
}

function getInitials(value: string): string {
  const words = value.split(/\s+/).filter(Boolean);
  return words
    .slice(0, 2)
    .map((word) => word[0]?.toUpperCase() || "")
    .join("");
}
