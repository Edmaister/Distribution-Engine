import { Award, CheckCircle2, Medal, Send, Share2 } from "lucide-react";
import type { FormEvent } from "react";

import { ActionGuardrail, type GuardrailTone } from "../../../components/ActionGuardrail";
import { DataTable } from "../../../components/DataTable";
import { EmptyState } from "../../../components/EmptyState";
import { InfoTooltip } from "../../../components/InfoTooltip";
import { StatusBadge } from "../../../components/StatusBadge";
import { formatDisplay, getNestedValue, getValue, statusTone } from "../../pageUtils";

type Payload = Record<string, unknown>;
type LoadState = "idle" | "loading";
type BadgeTone = GuardrailTone;

type ProfilePayload = {
  dashboard?: Payload;
  rewards?: Payload;
  missions?: Payload;
  leaderboard?: Payload;
  status?: string;
  unavailableSections?: string[];
};

type ConsumerJourneySectionsProps = {
  alias: string;
  badgeRows: Payload[];
  captureResult?: Payload;
  identityReference: string;
  inviteResult?: Payload;
  inviteTermsAccepted: boolean;
  leaderboardCode: string;
  loading: LoadState;
  missionRows: Payload[];
  preferredHandle: string;
  profile?: ProfilePayload;
  profileReference: string;
  progress?: Payload;
  referralCode: string;
  referralRows: Payload[];
  referralTrackId: string;
  rewardRows: Payload[];
  segment: string;
  shareResult?: Payload;
  shareTermsAccepted: boolean;
  sticker: string;
  onAcceptTerms: () => void;
  onAliasChange: (value: string) => void;
  onBootstrap: () => void;
  onCaptureIdentity: (event: FormEvent) => void;
  onIdentityReferenceChange: (value: string) => void;
  onInviteSubmit: (event: FormEvent) => void;
  onInviteTermsAcceptedChange: (value: boolean) => void;
  onPreferredHandleChange: (value: string) => void;
  onProfileReferenceChange: (value: string) => void;
  onProgressSubmit: (event: FormEvent) => void;
  onReferralCodeChange: (value: string) => void;
  onReferralTrackIdChange: (value: string) => void;
  onRewardsSubmit: (event: FormEvent) => void;
  onSegmentChange: (value: string) => void;
  onShareTermsAcceptedChange: (value: boolean) => void;
  onStickerChange: (value: string) => void;
  onIssueInvite: (event: FormEvent) => void;
};

export function ConsumerJourneySections({
  alias,
  badgeRows,
  captureResult,
  identityReference,
  inviteResult,
  inviteTermsAccepted,
  leaderboardCode,
  loading,
  missionRows,
  preferredHandle,
  profile,
  profileReference,
  progress,
  referralCode,
  referralRows,
  referralTrackId,
  rewardRows,
  segment,
  shareResult,
  shareTermsAccepted,
  sticker,
  onAcceptTerms,
  onAliasChange,
  onBootstrap,
  onCaptureIdentity,
  onIdentityReferenceChange,
  onInviteSubmit,
  onInviteTermsAcceptedChange,
  onPreferredHandleChange,
  onProfileReferenceChange,
  onProgressSubmit,
  onReferralCodeChange,
  onReferralTrackIdChange,
  onRewardsSubmit,
  onSegmentChange,
  onShareTermsAcceptedChange,
  onStickerChange,
  onIssueInvite,
}: ConsumerJourneySectionsProps) {
  return (
    <>
      <div className="grid-2">
        <section className="panel" id="consumer-invite-entry">
          <PanelHeader
            title="Join from invite"
            subtitle="Where the customer starts from a link, QR code, recommendation, or creator prompt."
            tooltip="This validates the trusted entry point and returns the journey reference used in the background."
          />
          <ActionGuardrail
            badge={inviteTermsAccepted ? "Ready" : "Check terms"}
            tone={inviteTermsAccepted ? "success" : "warning"}
            title="Keep entry simple"
            copy="Ask for the smallest possible action. The customer should feel they are joining an opportunity, not managing a referral process."
            items={[
              { label: "Customer accepts terms", value: inviteTermsAccepted ? "Yes" : "No", tone: inviteTermsAccepted ? "success" : "warning" },
              { label: "Outcome", value: "Join journey", tone: "info" },
              { label: "Next screen", value: "Track activation", tone: inviteResult ? "success" : "info" },
            ]}
          />
          <form className="consumer-action-form" onSubmit={onInviteSubmit}>
            <label>
              Invite, QR, or creator code
              <input
                value={referralCode}
                onChange={(event) => onReferralCodeChange(event.target.value)}
                placeholder="Trusted code from the invite"
                required
              />
            </label>
            <label>
              Mobile, email, or display name
              <input
                value={alias}
                onChange={(event) => onAliasChange(event.target.value)}
                placeholder="Optional customer identity signal"
              />
            </label>
            <label className="checkbox-row">
              <input
                checked={inviteTermsAccepted}
                onChange={(event) => onInviteTermsAcceptedChange(event.target.checked)}
                type="checkbox"
              />
              Terms accepted
            </label>
            <button disabled={loading === "loading"} type="submit">
              <Send size={16} />
              Join journey
            </button>
          </form>
          {inviteResult ? (
            <div className="summary-grid">
              <SummaryItem label="Journey" value={valueText(inviteResult, ["referral_track_id", "referralTrackId"])} tone="success" />
              <SummaryItem label="Status" value={eventStatus(inviteResult)} tone={statusTone(eventStatus(inviteResult))} />
              <SummaryItem label="Invite" value={valueText(inviteResult, ["referral_code", "referralCode"])} />
            </div>
          ) : null}
        </section>

        <section className="panel" id="consumer-progress">
          <PanelHeader
            title="Track activation"
            subtitle="Where the customer sees what happened, why it matters, and what comes next."
            tooltip="Use this after a trusted entry point has produced a journey reference."
          />
          <ActionGuardrail
            badge="Read-only"
            tone="success"
            title="Radical transparency"
            copy="This should explain what happened, what is still required, and when the customer gets value."
            items={[
              { label: "Action type", value: "Read-only", tone: "success" },
              { label: "System change", value: "None", tone: "success" },
              { label: "Recommended after", value: "Join journey", tone: inviteResult ? "success" : "warning" },
            ]}
          />
          <form className="consumer-action-form" onSubmit={onProgressSubmit}>
            <label>
              Journey reference
              <input
                value={referralTrackId}
                onChange={(event) => onReferralTrackIdChange(event.target.value)}
                placeholder="Referral journey reference"
                required
              />
            </label>
            <button disabled={loading === "loading"} type="submit">
              <CheckCircle2 size={16} />
              Load progress
            </button>
          </form>
          <form className="consumer-action-form" onSubmit={onCaptureIdentity}>
            <label>
              Identity reference
              <input
                value={identityReference}
                onChange={(event) => onIdentityReferenceChange(event.target.value)}
                placeholder="Optional verified identity reference"
              />
            </label>
            <button disabled={loading === "loading" || !referralTrackId || !identityReference} type="submit">
              Confirm identity
            </button>
          </form>
          {progress ? (
            <div className="summary-grid">
              <SummaryItem label="Current status" value={eventStatus(progress)} tone={statusTone(eventStatus(progress))} />
              <SummaryItem label="Next milestone" value={nestedText(progress, ["next_milestone"], "Review journey events")} />
              <SummaryItem label="Identity" value={captureResult ? "Confirmed" : "Optional"} tone={captureResult ? "success" : "info"} />
            </div>
          ) : (
            <EmptyState label="Load a journey reference to show customer progress." />
          )}
        </section>
      </div>

      <div className="grid-2">
        <section className="panel" id="consumer-rewards">
          <PanelHeader
            title="Value and rewards"
            subtitle="Where the customer sees rewards, cashback, missions, badges, and earning movement."
            tooltip="This is the referrer profile view. The profile reference is usually supplied by sign-in."
          />
          <ActionGuardrail
            badge={profileReference ? "Ready" : "Needs profile"}
            tone={profileReference ? "success" : "warning"}
            title="Earnings everywhere"
            copy="Every action should show value: reward, saving, cashback, commission, progress, or recognition."
            items={[
              { label: "Action type", value: "Read-only", tone: "success" },
              { label: "System change", value: "None", tone: "success" },
              { label: "Needs profile", value: profileReference ? "Ready" : "Missing", tone: profileReference ? "success" : "warning" },
            ]}
          />
          <form className="consumer-action-form" onSubmit={onRewardsSubmit}>
            <label>
              Profile reference
              <input
                value={profileReference}
                onChange={(event) => onProfileReferenceChange(event.target.value)}
                placeholder="Customer profile reference"
                required
              />
            </label>
            <button disabled={loading === "loading"} type="submit">
              <Award size={16} />
              Load value
            </button>
          </form>
          {profile ? (
            <>
              <div className="summary-grid">
                <SummaryItem label="Earned" value={moneyText(profile.rewards, ["earned_amount", "total_earned", "totalAmount"])} tone="success" />
                <SummaryItem label="Pending" value={moneyText(profile.rewards, ["pending_amount", "pendingAmount"])} tone="warning" />
                <SummaryItem label="Missions" value={String(missionRows.length)} />
              </div>
              {profile.unavailableSections?.length ? (
                <div className="banner warning" role="status">
                  <StatusBadge label="Partial data" tone="warning" />
                  <span className="muted">
                    Some value sections are temporarily unavailable: {profile.unavailableSections.join(", ")}.
                  </span>
                </div>
              ) : null}
              <DataTable
                columns={[textColumn("name", "Mission"), textColumn("status", "Status"), textColumn("progress", "Progress")]}
                rows={missionRows}
                emptyText="No missions returned."
              />
            </>
          ) : (
            <EmptyState label="Load rewards once the customer profile is known." />
          )}
        </section>

        <section className="panel" id="consumer-share">
          <PanelHeader
            title="Become an advocate"
            subtitle="Where an eligible customer creates an invite, earns, and grows the network."
            tooltip="This prepares the referrer profile, accepts programme terms, and issues an invite code."
          />
          <ActionGuardrail
            badge={shareTermsAccepted ? "Ready" : "Check terms"}
            tone={shareTermsAccepted ? "success" : "warning"}
            title="Network effect"
            copy="Create a new invite only when the customer understands the value and is eligible to advocate."
            items={[
              { label: "Terms accepted", value: shareTermsAccepted ? "Yes" : "No", tone: shareTermsAccepted ? "success" : "warning" },
              { label: "System change", value: "Invite code", tone: "info" },
              { label: "Recommended after", value: "Review rewards", tone: profile ? "success" : "warning" },
            ]}
          />
          <form className="consumer-action-form" onSubmit={onIssueInvite}>
            <label>
              Sticker
              <input value={sticker} onChange={(event) => onStickerChange(event.target.value)} />
            </label>
            <label>
              Segment
              <input value={segment} onChange={(event) => onSegmentChange(event.target.value)} />
            </label>
            <label>
              Preferred handle
              <input
                value={preferredHandle}
                onChange={(event) => onPreferredHandleChange(event.target.value)}
                placeholder="Optional friendly code"
              />
            </label>
            <label className="checkbox-row">
              <input
                checked={shareTermsAccepted}
                onChange={(event) => onShareTermsAcceptedChange(event.target.checked)}
                type="checkbox"
              />
              Terms accepted
            </label>
            <button disabled={loading === "loading" || !profileReference} type="button" onClick={onBootstrap}>
              Prepare profile
            </button>
            <button disabled={loading === "loading" || !profileReference} type="button" onClick={onAcceptTerms}>
              Accept terms
            </button>
            <button disabled={loading === "loading" || !profileReference} type="submit">
              <Share2 size={16} />
              Create advocacy invite
            </button>
          </form>
          {shareResult ? (
            <div className="summary-grid">
              <SummaryItem label="Invite code" value={valueText(shareResult, ["referral_code", "referralCode", "code"])} tone="success" />
              <SummaryItem label="Status" value={eventStatus(shareResult)} tone={statusTone(eventStatus(shareResult))} />
              <SummaryItem label="Profile" value={profileReference || "-"} />
            </div>
          ) : null}
        </section>
      </div>

      <div className="grid-2">
        <section className="panel" id="consumer-rank">
          <PanelHeader
            title="Reputation and milestones"
            subtitle="Where a customer sees status, rank, badges, and professional gamification."
            tooltip="Reputation is supporting context that helps customers understand progress and trust."
          />
          <div className="summary-grid">
            <SummaryItem label="Rank" value={nestedText(profile?.leaderboard ?? profile?.dashboard, ["rank"], "Not loaded")} />
            <SummaryItem label="Leaderboard" value={leaderboardCode || "-"} />
            <SummaryItem label="Rewards rows" value={String(rewardRows.length)} />
          </div>
          <DataTable
            columns={[textColumn("badge_name", "Badge"), textColumn("status", "Status"), textColumn("earned_at", "Earned")]}
            rows={badgeRows}
            emptyText="No badges returned."
          />
        </section>

        <section className="panel">
          <PanelHeader
            title="Referral activity"
            subtitle="A simple list of people or invites connected to this profile."
            tooltip="This keeps referral movement visible without exposing backend payloads."
          />
          {referralRows.length > 0 ? (
            <DataTable
              columns={[textColumn("referral_code", "Invite"), textColumn("status", "Status"), textColumn("created_at", "Created")]}
              rows={referralRows}
              emptyText="No referrals returned."
            />
          ) : (
            <div className="empty-with-icon">
              <Medal size={18} />
              <span>No referral activity returned yet.</span>
            </div>
          )}
        </section>
      </div>
    </>
  );
}

function PanelHeader({
  title,
  subtitle,
  tooltip,
}: {
  title: string;
  subtitle: string;
  tooltip: string;
}) {
  return (
    <div className="section-title-row">
      <div>
        <h3>{title}</h3>
        <p>{subtitle}</p>
      </div>
      <InfoTooltip text={tooltip} />
    </div>
  );
}

function SummaryItem({ label, value, tone }: { label: string; value: string; tone?: BadgeTone }) {
  return (
    <div className="summary-item">
      <span>{label}</span>
      <strong>{value}</strong>
      {tone ? <StatusBadge label={tone} tone={tone} /> : null}
    </div>
  );
}

function textColumn(key: string, header: string) {
  return {
    key,
    header,
    render: (row: Payload) => formatDisplay(row[key]),
  };
}

function valueText(payload: unknown, keys: string[], fallback = "-") {
  if (!payload || typeof payload !== "object") {
    return fallback;
  }
  return formatDisplay(getValue(payload as Payload, keys, fallback));
}

function nestedText(payload: unknown, path: string[], fallback = "-") {
  if (!payload || typeof payload !== "object") {
    return fallback;
  }
  return formatDisplay(getNestedValue(payload as Payload, path, fallback));
}

function moneyText(payload: unknown, keys: string[]) {
  const value = valueText(payload, keys, "0.00");
  return value === "-" ? "0.00" : value;
}

function eventStatus(payload: unknown) {
  return valueText(payload, ["status", "referral_status", "processing_status"], "Not started");
}
