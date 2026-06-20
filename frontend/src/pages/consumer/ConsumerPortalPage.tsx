import {
  BadgeDollarSign,
  CheckCircle2,
  type LucideIcon,
  MessageCircle,
  Sparkles,
  Smartphone,
  Trophy,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { FormEvent, useState } from "react";

import {
  acceptConsumerTerms,
  bootstrapConsumerReferrer,
  captureConsumerRefereeUcn,
  getConsumerExperience,
  getConsumerInsuranceProof,
  getConsumerReferralDashboard,
  issueConsumerReferralCode,
  validateConsumerReferralCode,
} from "../../api/endpoints/consumerPortal";
import type { GuardrailTone } from "../../components/ActionGuardrail";
import { ErrorPanel } from "../../components/ErrorPanel";
import { InfoTooltip } from "../../components/InfoTooltip";
import { InsuranceJourneyProofPanel } from "../../components/InsuranceJourneyProofPanel";
import { JourneyTracker, type JourneyStep } from "../../components/JourneyTracker";
import { KpiCard } from "../../components/KpiCard";
import { LoadingState } from "../../components/LoadingState";
import { StatusBadge } from "../../components/StatusBadge";
import {
  asArray,
  formatDisplay,
  getNestedValue,
  getValue,
} from "../pageUtils";
import { ConsumerJourneySections } from "./components/ConsumerJourneySections";

const TENANT_KEY = "amplifi.consumerPortal.tenant";
const PROFILE_KEY = "amplifi.consumerPortal.profile";
const LEADERBOARD_KEY = "amplifi.consumerPortal.leaderboard";
const TRACK_KEY = "amplifi.consumerPortal.referralTrack";

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

function sectionData(payload: Payload, sectionName: string): Payload | undefined {
  const sections = payload.sections;
  if (!sections || typeof sections !== "object") {
    return undefined;
  }

  const section = (sections as Record<string, unknown>)[sectionName];
  if (!section || typeof section !== "object") {
    return undefined;
  }

  const data = (section as Record<string, unknown>).data;
  return data && typeof data === "object" ? (data as Payload) : undefined;
}

function unavailableSectionsFrom(payload: Payload): string[] {
  const sections = payload.unavailableSections;
  return Array.isArray(sections) ? sections.map(String) : [];
}

function storedValue(key: string, fallback: string) {
  return window.localStorage.getItem(key) ?? fallback;
}

function remember(key: string, value: string) {
  window.localStorage.setItem(key, value);
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

function rowsFrom(payload: unknown, paths: string[][]) {
  if (!payload || typeof payload !== "object") {
    return [];
  }

  for (const path of paths) {
    const rows = asArray(getNestedValue(payload as Payload, path));
    if (rows.length > 0) {
      return rows;
    }
  }

  return [];
}

function eventStatus(payload: unknown) {
  return valueText(payload, ["status", "referral_status", "processing_status"], "Not started");
}

function currentStepStatus(stepId: string, context: {
  inviteResult?: Payload;
  progress?: Payload;
  profile?: ProfilePayload;
  shareResult?: Payload;
}): JourneyStep["state"] {
  if (stepId === "consumer-invite-entry") {
    return context.inviteResult ? "done" : "current";
  }
  if (stepId === "consumer-progress") {
    if (!context.inviteResult) return "waiting";
    return context.progress ? "done" : "current";
  }
  if (stepId === "consumer-rewards") {
    if (!context.progress) return "waiting";
    return context.profile ? "done" : "current";
  }
  if (stepId === "consumer-share") {
    if (!context.profile) return "waiting";
    return context.shareResult ? "done" : "current";
  }
  if (!context.shareResult) return "waiting";
  return "current";
}

function consumerSteps(context: {
  inviteResult?: Payload;
  progress?: Payload;
  profile?: ProfilePayload;
  shareResult?: Payload;
}): JourneyStep[] {
  return [
    {
      label: "Discover",
      description: "Arrive through a QR code, link, creator post, recommendation, or campaign prompt.",
      state: currentStepStatus("consumer-invite-entry", context),
      workArea: "Join from invite",
      targetId: "consumer-invite-entry",
      help: "The customer should experience this as a simple trusted entry point, not referral administration.",
    },
    {
      label: "Join",
      description: "Capture the minimum identity signal needed to start the customer journey.",
      state: currentStepStatus("consumer-progress", context),
      workArea: "Track activation",
      targetId: "consumer-progress",
      help: "In target state this is mobile, email, or digital identity, with campaign context already known.",
    },
    {
      label: "Establish",
      description: "Open, buy, register, sign, or complete the product setup.",
      state: currentStepStatus("consumer-rewards", context),
      workArea: "Value and rewards",
      targetId: "consumer-rewards",
      help: "The platform should show the value and progress attached to product setup.",
    },
    {
      label: "Activate",
      description: "Fund, transact, switch salary, make a first purchase, or complete the value trigger.",
      state: currentStepStatus("consumer-share", context),
      workArea: "Become an advocate",
      targetId: "consumer-share",
      help: "Activation is the moment to make the next earning opportunity feel natural.",
    },
    {
      label: "Advocate",
      description: "Share, earn, build reputation, and grow the network.",
      state: currentStepStatus("consumer-rank", context),
      workArea: "Reputation and milestones",
      targetId: "consumer-rank",
      help: "This is where the customer starts becoming part of the distribution network.",
    },
  ];
}

function guidanceText(context: {
  inviteResult?: Payload;
  progress?: Payload;
  profile?: ProfilePayload;
  shareResult?: Payload;
}) {
  if (!context.inviteResult) {
    return {
      title: "Join from a trusted prompt",
      body: "Start from the QR code, link, recommendation, influencer content, or referral code. The platform should feel simple while the distribution network works in the background.",
      tone: "info" as BadgeTone,
    };
  }
  if (!context.progress) {
    return {
      title: "Show what is next",
      body: "The customer joined. Now make the next step obvious: open, switch, buy, register, fund, transact, or complete the qualifying action.",
      tone: "warning" as BadgeTone,
    };
  }
  if (!context.profile) {
    return {
      title: "Make value visible",
      body: "Progress is visible. Show rewards, cashback, pending value, badges, and trust signals so the customer understands why the journey matters.",
      tone: "info" as BadgeTone,
    };
  }
  if (!context.shareResult) {
    return {
      title: "Convert customer to advocate",
      body: "Once value is understood, invite the customer to share and earn. This is where customer experience becomes distribution growth.",
      tone: "info" as BadgeTone,
    };
  }
  return {
    title: "Lifecycle loop is connected",
    body: "The customer can join, progress, see value, and become an advocate from one experience.",
    tone: "success" as BadgeTone,
  };
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

function ErrorMessage({ error }: { error?: unknown }) {
  if (error === undefined || error === null) return null;
  return <ErrorPanel error={error} />;
}

function ExperiencePrincipleCard({
  icon: Icon,
  title,
  copy,
  badge,
  tone,
}: {
  icon: LucideIcon;
  title: string;
  copy: string;
  badge: string;
  tone: BadgeTone;
}) {
  return (
    <div className="consumer-principle-card">
      <div className="consumer-principle-icon">
        <Icon size={18} />
      </div>
      <div>
        <h3>{title}</h3>
        <p>{copy}</p>
      </div>
      <StatusBadge label={badge} tone={tone} />
    </div>
  );
}

function CustomerPhoneJourney({
  inviteResult,
  progress,
  profile,
  shareResult,
}: {
  inviteResult?: Payload;
  progress?: Payload;
  profile?: ProfilePayload;
  shareResult?: Payload;
}) {
  const activeIndex = shareResult ? 4 : profile ? 3 : progress ? 2 : inviteResult ? 1 : 0;
  const chatStages = [
    {
      title: "Discover",
      stage: "Prospect",
      message: "Hi, Meridian invited you to switch and earn value back. Tap to see your offer.",
      reply: "Show me",
      detail: "QR, link, creator content, or recommendation",
    },
    {
      title: "Join",
      stage: "Known customer",
      message: "Great. We only need your mobile number or digital identity to start.",
      reply: aliasOrFallback(inviteResult, "I'm in"),
      detail: "Minimum identity, quiet verification",
    },
    {
      title: "Establish",
      stage: "Customer",
      message: "Your account setup is in progress. Complete the product step to unlock the reward.",
      reply: "Continue setup",
      detail: "Open, buy, sign, or register",
    },
    {
      title: "Activate",
      stage: "Value moment",
      message: "Almost there. Fund, transact, switch, or make the first purchase to qualify.",
      reply: "Track my reward",
      detail: "Activation proves revenue and value",
    },
    {
      title: "Advocate",
      stage: "Distributor",
      message: "You can now share your invite and earn when someone else activates.",
      reply: "Create invite",
      detail: "Customer becomes network growth",
    },
  ];
  const activeStage = chatStages[activeIndex];

  return (
    <section className="consumer-os-stage">
      <div className="consumer-phone">
        <div className="consumer-phone-notch" />
        <div className="consumer-phone-screen">
          <div className="consumer-chat-top">
            <div className="consumer-chat-avatar">M</div>
            <div>
              <strong>Meridian Bank</strong>
              <span>Amplifi assisted</span>
            </div>
          </div>
          <div className="consumer-chat-body">
            <div className="consumer-chat-date">Today</div>
            <div className="consumer-chat-bubble inbound">{activeStage.message}</div>
            <div className="consumer-chat-bubble outbound">{activeStage.reply}</div>
            <div className="consumer-chat-card">
              <div className="consumer-chat-card-kicker">{activeStage.stage}</div>
              <strong>{activeStage.title}</strong>
              <span>{activeStage.detail}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="consumer-stage-rail">
        <div className="section-title-row">
          <div>
            <h3>
              <MessageCircle size={16} />
              Almost invisible customer journey
            </h3>
            <p>The target CX is delivered like a guided conversation, while Amplifi handles attribution, funding, rewards, and settlement behind it.</p>
          </div>
          <StatusBadge label="OS pattern" tone="info" />
        </div>
        <div className="consumer-stage-list">
          {chatStages.map((stage, index) => (
            <div className={`consumer-stage-card ${index === activeIndex ? "active" : ""}`} key={stage.title}>
              <div className="consumer-stage-num">{index + 1}</div>
              <div>
                <strong>{stage.title}</strong>
                <p>{stage.detail}</p>
              </div>
              <StatusBadge label={index < activeIndex ? "Done" : index === activeIndex ? "Now" : "Next"} tone={index < activeIndex ? "success" : index === activeIndex ? "info" : "neutral"} />
            </div>
          ))}
        </div>
        <div className="consumer-lifecycle-strip">
          <Smartphone size={15} />
          <span>Prospect</span>
          <span>Customer</span>
          <span>Advocate</span>
          <span>Distributor</span>
        </div>
      </div>
    </section>
  );
}

function ConversionValueMap({
  inviteResult,
  progress,
  profile,
  shareResult,
}: {
  inviteResult?: Payload;
  progress?: Payload;
  profile?: ProfilePayload;
  shareResult?: Payload;
}) {
  return (
    <section className="consumer-value-map">
      <div className="consumer-value-map-panel primary">
        <div className="consumer-value-map-kicker">Conversion operating model</div>
        <h2>What this page is proving</h2>
        <p>
          This is not meant to be a customer app screen. It is a working view of the conversion loop:
          attribution, activation progress, visible value, and the point where a customer can become an advocate.
        </p>
        <div className="consumer-proof-list">
          <ConversionProofRow
            label="Attribution"
            value="Can we prove where the customer came from?"
            target="Join from invite"
            tone={inviteResult ? "success" : "info"}
          />
          <ConversionProofRow
            label="Activation"
            value="Can we show what the customer still needs to do?"
            target="Track activation"
            tone={progress ? "success" : "warning"}
          />
          <ConversionProofRow
            label="Value"
            value="Can we show reward, mission, badge, or progress value?"
            target="Value and rewards"
            tone={profile ? "success" : "info"}
          />
          <ConversionProofRow
            label="Advocacy"
            value="Can we turn an activated customer into a new demand channel?"
            target="Become an advocate"
            tone={shareResult ? "success" : "neutral"}
          />
        </div>
      </div>

      <div className="consumer-value-map-panel">
        <div className="section-title-row compact">
          <div>
            <h3>Where the work happens</h3>
            <p>Use this as the operator map for the local test screen.</p>
          </div>
          <StatusBadge label="Practical map" tone="info" />
        </div>
        <div className="consumer-work-map">
          <ConsumerWorkMapRow step="1" label="Join from invite" targetId="consumer-invite-entry" copy="Validate the trusted code and create the journey reference." />
          <ConsumerWorkMapRow step="2" label="Track activation" targetId="consumer-progress" copy="Load progress and optionally confirm identity." />
          <ConsumerWorkMapRow step="3" label="Value and rewards" targetId="consumer-rewards" copy="Show rewards, missions, and earned value." />
          <ConsumerWorkMapRow step="4" label="Become an advocate" targetId="consumer-share" copy="Prepare the profile and issue an invite code." />
          <ConsumerWorkMapRow step="5" label="Reputation" targetId="consumer-rank" copy="Review badges, rank, and referral activity." />
        </div>
      </div>
    </section>
  );
}

function ConversionProofRow({
  label,
  value,
  target,
  tone,
}: {
  label: string;
  value: string;
  target: string;
  tone: BadgeTone;
}) {
  return (
    <div className="consumer-proof-row">
      <div>
        <strong>{label}</strong>
        <span>{value}</span>
      </div>
      <StatusBadge label={target} tone={tone} />
    </div>
  );
}

function ConsumerWorkMapRow({
  step,
  label,
  targetId,
  copy,
}: {
  step: string;
  label: string;
  targetId: string;
  copy: string;
}) {
  return (
    <a className="consumer-work-map-row" href={`#${targetId}`}>
      <span>{step}</span>
      <div>
        <strong>{label}</strong>
        <p>{copy}</p>
      </div>
    </a>
  );
}

function aliasOrFallback(payload: unknown, fallback: string) {
  const alias = valueText(payload, ["alias", "display_name", "displayName"], "");
  return alias || fallback;
}

export function ConsumerPortalPage() {
  const [tenantCode, setTenantCode] = useState(() => storedValue(TENANT_KEY, "FNB"));
  const [profileReference, setProfileReference] = useState(() => storedValue(PROFILE_KEY, ""));
  const [leaderboardCode, setLeaderboardCode] = useState(() => storedValue(LEADERBOARD_KEY, "SMOKE-LEADERBOARD"));
  const [referralTrackId, setReferralTrackId] = useState(() => storedValue(TRACK_KEY, ""));
  const [referralCode, setReferralCode] = useState("");
  const [alias, setAlias] = useState("");
  const [identityReference, setIdentityReference] = useState("");
  const [inviteTermsAccepted, setInviteTermsAccepted] = useState(false);
  const [shareTermsAccepted, setShareTermsAccepted] = useState(false);
  const [sticker, setSticker] = useState("FRIENDS");
  const [segment, setSegment] = useState("CONSUMER");
  const [preferredHandle, setPreferredHandle] = useState("");
  const [inviteResult, setInviteResult] = useState<Payload>();
  const [captureResult, setCaptureResult] = useState<Payload>();
  const [progress, setProgress] = useState<Payload>();
  const [profile, setProfile] = useState<ProfilePayload>();
  const [shareResult, setShareResult] = useState<Payload>();
  const [loading, setLoading] = useState<LoadState>("idle");
  const [loadingMessage, setLoadingMessage] = useState("Working");
  const [error, setError] = useState<unknown>();
  const { data: insuranceProof = null } = useQuery({
    queryKey: ["consumer", "insurance-proof", tenantCode, referralTrackId || ""],
    queryFn: () => getConsumerInsuranceProof(tenantCode, referralTrackId || undefined),
    enabled: Boolean(tenantCode),
  });

  const context = { inviteResult, progress, profile, shareResult };
  const guidance = guidanceText(context);
  const steps = consumerSteps(context);
  const progressStatus = eventStatus(progress ?? inviteResult);
  const missionRows = rowsFrom(profile?.missions ?? progress, [
    ["items"],
    ["missions"],
    ["mission_progress"],
    ["summary", "missions"],
  ]);
  const rewardRows = rowsFrom(profile?.rewards ?? progress, [
    ["items"],
    ["rewards"],
    ["reward_events"],
    ["summary", "rewards"],
  ]);
  const referralRows = rowsFrom(profile?.dashboard, [
    ["referrals"],
    ["items"],
    ["summary", "referrals"],
  ]);
  const badgeRows = rowsFrom(profile?.dashboard, [
    ["badges"],
    ["earned_badges"],
    ["summary", "badges"],
  ]);

  async function runAction(action: () => Promise<void>, loadingCopy = "Working") {
    setLoading("loading");
    setLoadingMessage(loadingCopy);
    setError(undefined);
    try {
      await action();
    } catch (caught) {
      setError(caught);
    } finally {
      setLoading("idle");
    }
  }

  function saveAccessSettings() {
    remember(TENANT_KEY, tenantCode);
    remember(PROFILE_KEY, profileReference);
    remember(LEADERBOARD_KEY, leaderboardCode);
    remember(TRACK_KEY, referralTrackId);
  }

  function submitInvite(event: FormEvent) {
    event.preventDefault();
    void runAction(
      async () => {
        saveAccessSettings();
        const result = await validateConsumerReferralCode({
          tenantCode,
          referralCode,
          alias: alias || undefined,
          acceptedTerms: inviteTermsAccepted,
        });
        setInviteResult(result);
        const trackId = valueText(result, ["referral_track_id", "referralTrackId", "track_id"], "");
        if (trackId) {
          setReferralTrackId(trackId);
          remember(TRACK_KEY, trackId);
        }
      },
      "Joining journey",
    );
  }

  function submitCaptureIdentity(event: FormEvent) {
    event.preventDefault();
    void runAction(
      async () => {
        saveAccessSettings();
        const result = await captureConsumerRefereeUcn(referralTrackId, identityReference);
        setCaptureResult(result);
      },
      "Confirming identity",
    );
  }

  function submitProgress(event: FormEvent) {
    event.preventDefault();
    void runAction(
      async () => {
        saveAccessSettings();
        setProgress(await getConsumerReferralDashboard(referralTrackId));
      },
      "Loading progress",
    );
  }

  function submitRewards(event: FormEvent) {
    event.preventDefault();
    void runAction(
      async () => {
        saveAccessSettings();
        const experience = await getConsumerExperience({
          tenantCode,
          referrerUcn: profileReference,
          referralTrackId: referralTrackId || undefined,
          leaderboardCode,
        });
        setProfile({
          status: valueText(experience, ["status"], "ok"),
          unavailableSections: unavailableSectionsFrom(experience),
          dashboard: sectionData(experience, "profile"),
          rewards: sectionData(experience, "rewards"),
          missions: sectionData(experience, "missions"),
          leaderboard: sectionData(experience, "leaderboard"),
        });
      },
      "Loading value and rewards",
    );
  }

  function submitBootstrap() {
    void runAction(
      async () => {
        saveAccessSettings();
        setShareResult(await bootstrapConsumerReferrer(profileReference, tenantCode));
      },
      "Preparing advocate profile",
    );
  }

  function submitAcceptTerms() {
    void runAction(
      async () => {
        saveAccessSettings();
        setShareResult(await acceptConsumerTerms(profileReference, tenantCode));
      },
      "Accepting advocacy terms",
    );
  }

  function submitIssueInvite(event: FormEvent) {
    event.preventDefault();
    void runAction(
      async () => {
        saveAccessSettings();
        setShareResult(
          await issueConsumerReferralCode({
            referrerUcn: profileReference,
            tenantCode,
            sticker,
            segment,
            preferredHandle: preferredHandle || undefined,
            acceptedTerms: shareTermsAccepted,
          }),
        );
      },
      "Creating advocacy invite",
    );
  }

  return (
    <div className="page-stack">
      <section className="page-hero">
        <div>
          <p className="eyebrow">Distributor - Demand</p>
          <h1>Conversion Journey</h1>
          <p>
            A low-friction customer path that starts from a trusted prompt, makes value visible,
            and turns happy customers into advocates without exposing platform plumbing.
          </p>
        </div>
        <StatusBadge label={guidance.title} tone={guidance.tone} />
      </section>

      <ConversionValueMap
        inviteResult={inviteResult}
        progress={progress}
        profile={profile}
        shareResult={shareResult}
      />

      <section className="consumer-principle-grid">
        <ExperiencePrincipleCard
          icon={Smartphone}
          title="Ask for less"
          copy="The customer should only provide what is needed for this moment: code, identity, consent, or next action."
          badge="CX rule"
          tone="info"
        />
        <ExperiencePrincipleCard
          icon={CheckCircle2}
          title="Show the next step"
          copy="Every state should explain what happened, what is next, and where the customer gets value."
          badge="Clarity"
          tone="success"
        />
        <ExperiencePrincipleCard
          icon={BadgeDollarSign}
          title="Make value visible"
          copy="Rewards, cashback, missions, badges, rank, and progress should be visible before asking for advocacy."
          badge="Value"
          tone="success"
        />
        <ExperiencePrincipleCard
          icon={Sparkles}
          title="Hide the machinery"
          copy="Attribution, funding, rewards, settlement, and routing should work quietly behind the experience."
          badge="OS pattern"
          tone="info"
        />
      </section>

      <section className="panel" id="consumer-access">
        <PanelHeader
          title="Quiet platform context"
          subtitle="These settings are visible for local testing. In the target experience they come from the link, QR code, signed-in profile, or campaign context."
          tooltip="The end-state customer should not manage tenant, profile, or leaderboard plumbing directly."
        />
        <form className="consumer-action-form" onSubmit={(event) => event.preventDefault()}>
          <label>
            Tenant
            <input value={tenantCode} onChange={(event) => setTenantCode(event.target.value)} />
          </label>
          <label>
            Profile reference
            <input
              value={profileReference}
              onChange={(event) => setProfileReference(event.target.value)}
              placeholder="Customer profile reference"
            />
          </label>
          <label>
            Leaderboard
            <input
              value={leaderboardCode}
              onChange={(event) => setLeaderboardCode(event.target.value)}
            />
          </label>
          <button className="secondary-button" type="button" onClick={saveAccessSettings}>
            Save settings
          </button>
        </form>
      </section>

      <div className="grid-3">
        <KpiCard
          icon={Sparkles}
          label="Lifecycle stage"
          value={progressStatus}
          footnote="Prospect to customer to advocate"
        />
        <KpiCard
          icon={BadgeDollarSign}
          label="Visible value"
          value={moneyText(profile?.rewards ?? progress, ["total_amount", "earned_amount", "totalRewards"])}
          footnote="Reward, cashback, or earning signal"
        />
        <KpiCard
          icon={Trophy}
          label="Reputation"
          value={nestedText(profile?.leaderboard ?? profile?.dashboard, ["rank"], "Not loaded")}
          footnote="Rank, trust, and recognition"
        />
      </div>

      <section className="panel">
        <PanelHeader
          title="Lifecycle loop"
          subtitle="The customer experience should feel almost invisible: discover, join, establish, activate, then become an advocate."
          tooltip="This is the consumer-facing expression of the Distribution Operating System vision."
        />
        <div className="summary-grid">
          <SummaryItem label="1. Discover" value="QR, link, creator, recommendation" tone="info" />
          <SummaryItem label="2. Join" value="Mobile, email, or digital identity" tone={inviteResult ? "success" : "info"} />
          <SummaryItem label="3. Establish" value="Open, buy, sign, or register" tone={progress ? "success" : "neutral"} />
          <SummaryItem label="4. Activate" value="Fund, transact, switch, purchase" tone={progress ? "success" : "neutral"} />
          <SummaryItem label="5. Advocate" value="Share, earn, build network" tone={shareResult ? "success" : "neutral"} />
        </div>
      </section>

      <JourneyTracker
        title="Customer journey map"
        subtitle="Each stage points to the work area where the customer, advocate, or support user completes that outcome."
        badge={guidance.title}
        tone={guidance.tone}
        currentTitle={guidance.title}
        currentCopy={guidance.body}
        steps={steps}
      />

      <InsuranceJourneyProofPanel proof={insuranceProof} role="consumer" />

      {loading === "loading" ? <LoadingState label={loadingMessage} /> : null}
      <ErrorMessage error={error} />

      <ConsumerJourneySections
        alias={alias}
        badgeRows={badgeRows}
        captureResult={captureResult}
        identityReference={identityReference}
        inviteResult={inviteResult}
        inviteTermsAccepted={inviteTermsAccepted}
        leaderboardCode={leaderboardCode}
        loading={loading}
        missionRows={missionRows}
        preferredHandle={preferredHandle}
        profile={profile}
        profileReference={profileReference}
        progress={progress}
        referralCode={referralCode}
        referralRows={referralRows}
        referralTrackId={referralTrackId}
        rewardRows={rewardRows}
        segment={segment}
        shareResult={shareResult}
        shareTermsAccepted={shareTermsAccepted}
        sticker={sticker}
        onAcceptTerms={submitAcceptTerms}
        onAliasChange={setAlias}
        onBootstrap={submitBootstrap}
        onCaptureIdentity={submitCaptureIdentity}
        onIdentityReferenceChange={setIdentityReference}
        onInviteSubmit={submitInvite}
        onInviteTermsAcceptedChange={setInviteTermsAccepted}
        onPreferredHandleChange={setPreferredHandle}
        onProfileReferenceChange={setProfileReference}
        onProgressSubmit={submitProgress}
        onReferralCodeChange={setReferralCode}
        onReferralTrackIdChange={setReferralTrackId}
        onRewardsSubmit={submitRewards}
        onSegmentChange={setSegment}
        onShareTermsAcceptedChange={setShareTermsAccepted}
        onStickerChange={setSticker}
        onIssueInvite={submitIssueInvite}
      />
    </div>
  );
}
