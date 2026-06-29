import {
  CheckCircle2,
  CircleDashed,
  Flag,
  KeyRound,
  Link as LinkIcon,
  Rocket,
  ShieldCheck,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  getAdminOnboardingState,
  type AdminOnboardingStateResponse,
  type OnboardingReadinessCategory,
} from "../../api/endpoints/adminOnboarding";
import { StatusBadge } from "../../components/StatusBadge";
import { SummaryItem } from "../../components/SummaryItem";

type ReadinessStatus = "Not started" | "In progress" | "Blocked" | "Ready";

type ChecklistItem = {
  title: string;
  status: ReadinessStatus;
  path: string;
  pathLabel: string;
  evidence: string;
  blocker: string;
  nextAction: string;
};

const checklistItems: ChecklistItem[] = [
  {
    title: "Organisation profile",
    status: "Ready",
    path: "/admin/onboarding/company",
    pathLabel: "Company onboarding",
    evidence:
      "External tenant and organisation references can be drafted in the company onboarding shell.",
    blocker: "Backend account lifecycle APIs are still future work.",
    nextAction:
      "Confirm organisation_ref, external_tenant_ref, country, industry, and admin contact.",
  },
  {
    title: "Producer / sponsor setup",
    status: "In progress",
    path: "/admin/onboarding/producer-sponsor",
    pathLabel: "Producer / sponsor onboarding",
    evidence:
      "Producer/sponsor identity, ownership, and funding intention can be captured locally.",
    blocker:
      "No sponsor create, wallet, billing, funding contract, or funding readiness command is wired.",
    nextAction:
      "Draft producer_ref, sponsor_ref, organisation_ref, admin contact, and funding model intention.",
  },
  {
    title: "Distributor setup",
    status: "In progress",
    path: "/admin/onboarding/distributor",
    pathLabel: "Distributor onboarding",
    evidence:
      "Distributor identity, channel, market, and participation intent can be captured locally.",
    blocker:
      "No distributor create, route activation, wallet creation, or marketplace lifecycle command is wired.",
    nextAction:
      "Draft distributor_ref, organisation_ref, channel type, market, and distributor admin contact.",
  },
  {
    title: "Members and roles",
    status: "In progress",
    path: "/admin/onboarding/members-roles",
    pathLabel: "User & role setup",
    evidence:
      "Invite, membership, role-family, participant type, and access scope intent can be drafted.",
    blocker:
      "No user invite, role assignment, membership activation, or auth claim change is wired.",
    nextAction:
      "Confirm intended role families for platform operator, producer/company admin, and distributor/partner admin personas.",
  },
  {
    title: "Campaign / opportunity setup",
    status: "In progress",
    path: "/admin/onboarding/campaign-opportunity",
    pathLabel: "Campaign / opportunity setup",
    evidence:
      "Campaign basics, participant scope, distribution model, outcome, reward, and funding intent can be reviewed.",
    blocker:
      "No campaign create, opportunity publish, link/code generation, policy write, or launch command is wired.",
    nextAction:
      "Draft campaign_code, opportunity_ref, outcome event, reward/commission intent, and funding intention.",
  },
  {
    title: "Webhook / API setup",
    status: "Ready",
    path: "/admin/onboarding/webhook-api",
    pathLabel: "Webhook & API setup",
    evidence:
      "Integration owner, callback placeholder, event categories, auth method intent, and payload preview can be reviewed.",
    blocker:
      "No API keys, secrets, subscriptions, signing, callback registration, or webhook delivery are created.",
    nextAction:
      "Confirm selected event categories, callback URL placeholder, payload format, and security method intent.",
  },
  {
    title: "Security and permissions",
    status: "Blocked",
    path: "/admin/onboarding/members-roles",
    pathLabel: "User & role setup",
    evidence:
      "Permission boundaries are visible in the role setup shell and API permission matrix.",
    blocker:
      "Membership APIs, live DB verification, and TASK-027/TASK-028 drift checks remain blocked before release signoff.",
    nextAction:
      "Keep tenant_code internal, use external references, and complete approved read-only live verification before external release.",
  },
  {
    title: "Go-live controls",
    status: "Blocked",
    path: "/admin/onboarding/campaign-opportunity",
    pathLabel: "Campaign / opportunity setup",
    evidence: "Go-live status can be drafted as a local readiness signal only.",
    blocker:
      "Live activation, campaign publication, funding readiness commands, webhook delivery checks, TASK-027, and TASK-028 are blocked.",
    nextAction:
      "Use this checklist for demo review only; request implementation tasks for real activation workflows later.",
  },
];

const statusOrder: ReadinessStatus[] = [
  "Ready",
  "In progress",
  "Blocked",
  "Not started",
];

const readOnlyScope = {
  external_tenant_ref: "demo-platform-operator",
  organisation_ref: "demo-organisation",
  producer_ref: "demo-producer",
  distributor_ref: "demo-distributor",
  campaign_code: "DEMO-CAMPAIGN",
  opportunity_ref: "demo-opportunity",
};

type LoadState = "loading" | "success" | "fallback";

function statusTone(status: ReadinessStatus) {
  if (status === "Ready") {
    return "success";
  }
  if (status === "In progress") {
    return "info";
  }
  if (status === "Blocked") {
    return "warning";
  }
  return "neutral";
}

function backendStatusTone(status: string) {
  if (status === "READY") {
    return "success";
  }
  if (status === "BLOCKED" || status === "GO_LIVE_DISABLED") {
    return "warning";
  }
  if (status === "MISSING_EVIDENCE" || status === "PERMISSION_LIMITED") {
    return "info";
  }
  return "neutral";
}

function categoryPath(category: OnboardingReadinessCategory) {
  const categoryKey = category.category.toUpperCase();
  if (categoryKey.includes("PRODUCER") || categoryKey.includes("SPONSOR")) {
    return "/admin/onboarding/producer-sponsor";
  }
  if (categoryKey.includes("DISTRIBUTOR")) {
    return "/admin/onboarding/distributor";
  }
  if (categoryKey.includes("MEMBER") || categoryKey.includes("ROLE")) {
    return "/admin/onboarding/members-roles";
  }
  if (
    categoryKey.includes("CAMPAIGN") ||
    categoryKey.includes("OPPORTUNITY") ||
    categoryKey.includes("GO_LIVE")
  ) {
    return "/admin/onboarding/campaign-opportunity";
  }
  if (categoryKey.includes("WEBHOOK") || categoryKey.includes("API")) {
    return "/admin/onboarding/webhook-api";
  }
  return "/admin/onboarding/company";
}

export function OnboardingReadinessChecklistPage() {
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [readOnlyState, setReadOnlyState] =
    useState<AdminOnboardingStateResponse | null>(null);

  useEffect(() => {
    let cancelled = false;

    getAdminOnboardingState(readOnlyScope)
      .then((response) => {
        if (cancelled) {
          return;
        }
        setReadOnlyState(response);
        setLoadState("success");
      })
      .catch(() => {
        if (cancelled) {
          return;
        }
        setReadOnlyState(null);
        setLoadState("fallback");
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const readyCount =
    readOnlyState?.readiness.summary.ready_count ??
    checklistItems.filter((item) => item.status === "Ready").length;
  const blockedCount =
    readOnlyState?.readiness.summary.blocked_count ??
    checklistItems.filter((item) => item.status === "Blocked").length;
  const totalCount =
    readOnlyState?.readiness.summary.total_count ?? checklistItems.length;
  const backendCategories = useMemo(
    () => readOnlyState?.readiness.categories ?? [],
    [readOnlyState],
  );

  return (
    <>
      <section className="page-header">
        <div>
          <div className="page-kicker">DLaaS onboarding - Readiness</div>
          <h1 className="page-title">Onboarding readiness checklist</h1>
          <p className="page-copy">
            Review the demo-safe onboarding journey from organisation setup
            through producer, distributor, member, campaign, and integration
            readiness before moving into operator monitoring.
          </p>
        </div>
        <StatusBadge label="Review only" tone="warning" />
      </section>

      <section className="grid-3">
        <SummaryItem
          label="Ready categories"
          value={`${readyCount}/${totalCount}`}
        />
        <SummaryItem label="Blocked categories" value={`${blockedCount}`} />
        <SummaryItem label="Internal tenant identifier" value="Hidden" />
      </section>

      <section className="panel" aria-labelledby="read-only-state-heading">
        <div className="panel-header">
          <div>
            <h2 className="panel-title" id="read-only-state-heading">
              Read-only platform state
            </h2>
            <div className="panel-subtitle">
              Hydrates from the admin onboarding state endpoint when available.
            </div>
          </div>
          <StatusBadge
            label={
              loadState === "loading"
                ? "Loading"
                : loadState === "success"
                  ? "Read-only"
                  : "Demo fallback"
            }
            tone={loadState === "success" ? "success" : "info"}
          />
        </div>
        <div className="panel-body">
          {loadState === "loading" ? (
            <div className="banner info" role="status">
              <CircleDashed size={18} />
              <div>
                <strong>Loading read-only onboarding state.</strong>
                <div className="table-subtext">
                  The checklist is checking external references without enabling
                  live actions.
                </div>
              </div>
            </div>
          ) : loadState === "fallback" ? (
            <div className="banner warning" role="status">
              <ShieldCheck size={18} />
              <div>
                <strong>Using local demo fallback.</strong>
                <div className="table-subtext">
                  The read-only onboarding state endpoint is unavailable, so
                  this checklist keeps the local shell state visible.
                </div>
              </div>
            </div>
          ) : (
            <div className="grid-3">
              <SummaryItem
                label="Overall readiness"
                value={readOnlyState?.readiness.overall_status ?? "Unavailable"}
              />
              <SummaryItem
                label="Missing evidence"
                value={
                  readOnlyState?.readiness.summary.missing_evidence_count ?? 0
                }
              />
              <SummaryItem
                label="External reference"
                value={readOnlyScope.external_tenant_ref}
              />
            </div>
          )}
        </div>
      </section>

      <section className="banner warning" role="note">
        <ShieldCheck size={18} />
        <div>
          <strong>
            This checklist does not activate go-live, publish campaigns, create
            credentials, or move money.
          </strong>
          <div className="table-subtext">
            It uses local demo readiness only. It does not create, update,
            activate, launch, approve, settle, fund, fulfil, retry, deliver, or
            mutate records.
          </div>
        </div>
      </section>

      <section className="grid-2">
        <section className="panel" aria-labelledby="checklist-heading">
          <div className="panel-header">
            <div>
              <h2 className="panel-title" id="checklist-heading">
                Product journey readiness
              </h2>
              <div className="panel-subtitle">
                Demo-safe statuses with blockers and next actions.
              </div>
            </div>
            <CircleDashed size={18} />
          </div>
          <div className="panel-body route-list">
            {loadState === "success" && backendCategories.length > 0
              ? backendCategories.map((category) => {
                  const label =
                    category.safe_display_status?.label || category.status;
                  return (
                    <Link
                      className="route-item"
                      key={category.category}
                      to={categoryPath(category)}
                    >
                      <div>
                        <div className="route-name">
                          {category.display_label}
                        </div>
                        <div className="route-path">
                          {category.evidence_summary}
                          {category.next_actions[0]
                            ? ` Next: ${category.next_actions[0]}`
                            : ""}
                        </div>
                        {category.blockers[0] ? (
                          <div className="table-subtext">
                            {category.blockers[0]}
                          </div>
                        ) : null}
                      </div>
                      <StatusBadge
                        label={label}
                        tone={backendStatusTone(category.status)}
                      />
                    </Link>
                  );
                })
              : checklistItems.map((item) => (
                  <Link className="route-item" key={item.title} to={item.path}>
                    <div>
                      <div className="route-name">{item.title}</div>
                      <div className="route-path">
                        {item.evidence} Next: {item.nextAction}
                      </div>
                    </div>
                    <StatusBadge
                      label={item.status}
                      tone={statusTone(item.status)}
                    />
                  </Link>
                ))}
          </div>
        </section>

        <section className="panel" aria-labelledby="blockers-heading">
          <div className="panel-header">
            <div>
              <h2 className="panel-title" id="blockers-heading">
                Blockers and stop conditions
              </h2>
              <div className="panel-subtitle">
                Release blockers stay visible even when the demo shell is ready.
              </div>
            </div>
            <Flag size={18} />
          </div>
          <div className="panel-body route-list">
            <div className="route-item">
              <div>
                <div className="route-name">TASK-027 live DB verification</div>
                <div className="route-path">
                  Blocked until approved safe read-only runtime database access,
                  environment name, credentials, write-protection confirmation,
                  and smoke-check approval exist.
                </div>
              </div>
              <StatusBadge label="Blocked" tone="warning" />
            </div>
            <div className="route-item">
              <div>
                <div className="route-name">TASK-028 drift resolution</div>
                <div className="route-path">
                  Blocked until TASK-027 produces verified live/schema mismatch
                  results or specific unknowns are explicitly deferred.
                </div>
              </div>
              <StatusBadge label="Blocked" tone="warning" />
            </div>
            <div className="route-item">
              <div>
                <div className="route-name">No live activation path</div>
                <div className="route-path">
                  Go-live review remains disabled until real account, campaign,
                  credential, funding, fulfilment, settlement, and audit
                  workflows are separately implemented and tested.
                </div>
              </div>
              <StatusBadge label="Guardrail" tone="info" />
            </div>
          </div>
        </section>
      </section>

      <section className="grid-2">
        <section className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Status summary</h2>
              <div className="panel-subtitle">
                Read-only endpoint categories when available, with local demo
                fallback.
              </div>
            </div>
            <Rocket size={18} />
          </div>
          <div className="panel-body route-list">
            {statusOrder.map((status) => {
              const count = checklistItems.filter(
                (item) => item.status === status,
              ).length;
              return (
                <div className="route-item" key={status}>
                  <div>
                    <div className="route-name">{status}</div>
                    <div className="route-path">
                      {count} checklist categories
                    </div>
                  </div>
                  <StatusBadge label={`${count}`} tone={statusTone(status)} />
                </div>
              );
            })}
          </div>
        </section>

        <section className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Safe readiness boundary</h2>
              <div className="panel-subtitle">
                External identifiers stay visible; internal partitioning stays
                hidden.
              </div>
            </div>
            <KeyRound size={18} />
          </div>
          <div className="panel-body capability-grid">
            <BoundaryCard
              icon={LinkIcon}
              title="External references"
              copy="Use external_tenant_ref, organisation_ref, producer_ref, sponsor_ref, and distributor_ref in the visible journey."
            />
            <BoundaryCard
              icon={ShieldCheck}
              title="No live commands"
              copy="Campaign launch, credential lifecycle, distributor route activation, wallet, funding, fulfilment, settlement, retry, and webhook delivery stay disabled."
            />
            <BoundaryCard
              icon={Flag}
              title="Demo review only"
              copy="This page supports operator and company-admin review before implementation tasks add real go-live controls."
            />
          </div>
          <div className="action-button-row">
            <button className="button" disabled type="button">
              Request go-live review later
            </button>
            <button className="button secondary" disabled type="button">
              Mark ready for review later
            </button>
          </div>
        </section>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2 className="panel-title">Onboarding page links</h2>
            <div className="panel-subtitle">
              Open each setup shell without production writes.
            </div>
          </div>
          <CheckCircle2 size={18} />
        </div>
        <div className="panel-body route-list">
          {checklistItems.slice(0, 6).map((item) => (
            <Link className="route-item" key={item.path} to={item.path}>
              <div>
                <div className="route-name">{item.pathLabel}</div>
                <div className="route-path">{item.nextAction}</div>
              </div>
              <CheckCircle2 size={18} />
            </Link>
          ))}
        </div>
      </section>
    </>
  );
}

function BoundaryCard({
  icon: Icon,
  title,
  copy,
}: {
  icon: typeof ShieldCheck;
  title: string;
  copy: string;
}) {
  return (
    <article className="capability-card">
      <div className="capability-icon">
        <Icon size={18} />
      </div>
      <div>
        <div className="capability-title">{title}</div>
        <div className="capability-copy">{copy}</div>
      </div>
      <StatusBadge label="Guardrail" tone="info" />
    </article>
  );
}
