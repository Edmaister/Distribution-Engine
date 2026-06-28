import {
  Activity,
  Building2,
  CheckCircle2,
  CircleDashed,
  Flag,
  Gauge,
  GitBranch,
  GitPullRequestArrow,
  KeyRound,
  Link as LinkIcon,
  RadioTower,
  ShieldCheck,
  Sparkles,
  Target,
  Users,
  type LucideIcon,
} from "lucide-react";
import { Link } from "react-router-dom";
import { StatusBadge } from "../../components/StatusBadge";
import { SummaryItem } from "../../components/SummaryItem";

type DemoStatus = "Ready" | "Available" | "UI pending" | "Blocked";

type DemoItem = {
  title: string;
  description: string;
  path?: string;
  status: DemoStatus;
  icon: LucideIcon;
};

type DemoSection = {
  id: string;
  title: string;
  subtitle: string;
  icon: LucideIcon;
  items: DemoItem[];
};

const demoSections: DemoSection[] = [
  {
    id: "setup-journey",
    title: "Setup journey",
    subtitle: "Draft the organisation, participants, and access model before readiness review.",
    icon: Building2,
    items: [
      {
        title: "Company / organisation onboarding",
        description: "Capture organisation_ref, external_tenant_ref, country, industry, and admin contact.",
        path: "/admin/onboarding/company",
        status: "Ready",
        icon: Building2,
      },
      {
        title: "Producer / sponsor onboarding",
        description: "Draft producer_ref or sponsor_ref, ownership, funding intention, and campaign role.",
        path: "/admin/onboarding/producer-sponsor",
        status: "Ready",
        icon: Target,
      },
      {
        title: "Distributor onboarding",
        description: "Draft distributor_ref, channel model, market, contact, and participation intent.",
        path: "/admin/onboarding/distributor",
        status: "Ready",
        icon: Users,
      },
      {
        title: "User / member role setup",
        description: "Review invite intent, participant type, role family, and access scope.",
        path: "/admin/onboarding/members-roles",
        status: "Ready",
        icon: ShieldCheck,
      },
    ],
  },
  {
    id: "readiness-review",
    title: "Readiness review",
    subtitle: "Connect setup inputs to campaign, integration, and demo-safe go-live evidence.",
    icon: CheckCircle2,
    items: [
      {
        title: "Campaign / opportunity setup",
        description: "Review campaign_code, opportunity_ref, distribution model, outcome, reward, and funding intent.",
        path: "/admin/onboarding/campaign-opportunity",
        status: "Ready",
        icon: Target,
      },
      {
        title: "Webhook / API setup",
        description: "Review callback placeholder, event categories, auth method intent, and payload format.",
        path: "/admin/onboarding/webhook-api",
        status: "Ready",
        icon: KeyRound,
      },
      {
        title: "Onboarding readiness checklist",
        description: "See blockers, next actions, and disabled go-live controls in one review surface.",
        path: "/admin/onboarding/readiness",
        status: "Ready",
        icon: CheckCircle2,
      },
    ],
  },
  {
    id: "operational-monitoring",
    title: "Operational monitoring",
    subtitle: "Move from setup to existing read-only operations and demand surfaces.",
    icon: Gauge,
    items: [
      {
        title: "Demand marketplace",
        description: "Review company-created demand and campaign discovery.",
        path: "/admin/distribution",
        status: "Available",
        icon: GitPullRequestArrow,
      },
      {
        title: "Demand operations",
        description: "Review distributor eligibility, producer demand, routing, wallets, and governance controls.",
        path: "/admin/distribution/operations",
        status: "Available",
        icon: Gauge,
      },
      {
        title: "Channel operations",
        description: "Review messaging delivery, retries, and channel audit evidence.",
        path: "/admin/channels",
        status: "Available",
        icon: RadioTower,
      },
      {
        title: "Event fabric",
        description: "Review enterprise event intake and platform event visibility.",
        path: "/admin/events",
        status: "Available",
        icon: GitBranch,
      },
      {
        title: "Runtime health",
        description: "Review platform readiness and dependency signals.",
        path: "/admin/health",
        status: "Available",
        icon: Activity,
      },
      {
        title: "Distributor safe status",
        description: "Review distributor-facing safe status without raw provider or settlement internals.",
        path: "/distributor",
        status: "Available",
        icon: Users,
      },
    ],
  },
  {
    id: "diagnostics-support",
    title: "Diagnostics and support",
    subtitle: "Track backend-ready diagnostics that still need dedicated frontend screens.",
    icon: Sparkles,
    items: [
      {
        title: "Operator control-plane BFF",
        description: "Backend aggregate is available for read-only operator sections; dedicated UI is pending.",
        status: "UI pending",
        icon: Gauge,
      },
      {
        title: "Outcome trace",
        description: "Admin API can inspect outcome evidence safely; dedicated frontend inspector is pending.",
        status: "UI pending",
        icon: LinkIcon,
      },
      {
        title: "Liability projection",
        description: "Admin API can project liability state without money movement; dedicated UI is pending.",
        status: "UI pending",
        icon: CircleDashed,
      },
      {
        title: "Campaign readiness",
        description: "Admin API can expose readiness blockers and warnings; dedicated UI is pending.",
        status: "UI pending",
        icon: CheckCircle2,
      },
      {
        title: "Link/code diagnostics",
        description: "Admin API can inspect safe link and code state; dedicated UI is pending.",
        status: "UI pending",
        icon: LinkIcon,
      },
      {
        title: "Tenant-safe analytics",
        description: "Admin API can provide safe aggregate analytics; dedicated report UI is pending.",
        status: "UI pending",
        icon: Activity,
      },
      {
        title: "Webhook catalog and payload preview",
        description: "Admin APIs can list event types and build non-delivering previews; dedicated UI is pending.",
        status: "UI pending",
        icon: RadioTower,
      },
    ],
  },
];

const personaPaths = [
  {
    title: "Platform operator",
    description: "Start setup, review readiness, then move into monitoring and support diagnostics.",
    status: "Demo path",
    icon: ShieldCheck,
  },
  {
    title: "Producer / sponsor / company admin",
    description: "Use external references, campaign setup intent, and readiness evidence without funding actions.",
    status: "Setup path",
    icon: Building2,
  },
  {
    title: "Distributor / partner admin",
    description: "Use distributor onboarding and safe status surfaces without route activation or settlement commands.",
    status: "Portal path",
    icon: Users,
  },
];

function statusTone(status: DemoStatus) {
  if (status === "Ready" || status === "Available") {
    return "success";
  }
  if (status === "UI pending") {
    return "info";
  }
  return "warning";
}

export function OperatorDemoHomePage() {
  const readyLinks = demoSections.flatMap((section) => section.items).filter((item) => item.path).length;
  const pendingDiagnostics = demoSections
    .flatMap((section) => section.items)
    .filter((item) => item.status === "UI pending").length;

  return (
    <>
      <section className="page-header">
        <div>
          <div className="page-kicker">DLaaS demo - Operator home</div>
          <h1 className="page-title">Operator demo home</h1>
          <p className="page-copy">
            Start with onboarding, review go-live readiness, then move into
            read-only monitoring, diagnostics, and support surfaces without
            executing live platform actions.
          </p>
        </div>
        <StatusBadge label="Demo shell" tone="info" />
      </section>

      <section className="grid-3">
        <SummaryItem label="Demo journey links" value={readyLinks} />
        <SummaryItem label="Diagnostics UI pending" value={pendingDiagnostics} />
        <SummaryItem label="Internal tenant_code" value="Hidden" />
      </section>

      <section className="banner warning" role="note">
        <ShieldCheck size={18} />
        <div>
          <strong>This page does not execute live platform actions.</strong>
          <div className="table-subtext">
            It does not create, update, activate, launch, publish, approve,
            settle, fund, fulfil, retry, deliver, or mutate records. It uses
            external references for the visible journey and keeps internal
            tenant partitioning out of the operator demo path.
          </div>
        </div>
      </section>

      <section className="grid-2">
        {demoSections.map((section) => (
          <DemoPanel key={section.id} section={section} />
        ))}
      </section>

      <section className="grid-2">
        <section className="panel" aria-labelledby="persona-paths-heading">
          <div className="panel-header">
            <div>
              <h2 className="panel-title" id="persona-paths-heading">
                Persona paths
              </h2>
              <div className="panel-subtitle">
                Demo navigation stays aligned to the platform operating model.
              </div>
            </div>
            <Users size={18} />
          </div>
          <div className="panel-body capability-grid">
            {personaPaths.map((path) => (
              <article className="capability-card" key={path.title}>
                <div className="capability-icon">
                  <path.icon size={18} />
                </div>
                <div>
                  <div className="capability-title">{path.title}</div>
                  <div className="capability-copy">{path.description}</div>
                </div>
                <StatusBadge label={path.status} tone="info" />
              </article>
            ))}
          </div>
        </section>

        <section className="panel" aria-labelledby="demo-blockers-heading">
          <div className="panel-header">
            <div>
              <h2 className="panel-title" id="demo-blockers-heading">
                Demo blockers and guardrails
              </h2>
              <div className="panel-subtitle">
                Release and live verification blockers stay visible.
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
                  and runtime smoke-check approval exist.
                </div>
              </div>
              <StatusBadge label="Blocked" tone="warning" />
            </div>
            <div className="route-item">
              <div>
                <div className="route-name">TASK-028 drift resolution</div>
                <div className="route-path">
                  Blocked until verified live/schema mismatch results exist or
                  specific unknowns are explicitly deferred.
                </div>
              </div>
              <StatusBadge label="Blocked" tone="warning" />
            </div>
            <div className="route-item">
              <div>
                <div className="route-name">No live command path</div>
                <div className="route-path">
                  Launch, publish, credential lifecycle, webhook delivery,
                  funding, wallet, fulfilment, settlement, and retry commands
                  remain out of scope for this demo page.
                </div>
              </div>
              <StatusBadge label="Guardrail" tone="info" />
            </div>
          </div>
          <div className="action-button-row">
            <button className="button" disabled type="button">
              Start live demo later
            </button>
            <button className="button secondary" disabled type="button">
              Run live smoke check later
            </button>
            <button className="button secondary" disabled type="button">
              Publish campaign later
            </button>
            <button className="button secondary" disabled type="button">
              Deliver webhook later
            </button>
          </div>
        </section>
      </section>
    </>
  );
}

function DemoPanel({ section }: { section: DemoSection }) {
  const Icon = section.icon;

  return (
    <section className="panel" aria-labelledby={`${section.id}-heading`}>
      <div className="panel-header">
        <div>
          <h2 className="panel-title" id={`${section.id}-heading`}>
            {section.title}
          </h2>
          <div className="panel-subtitle">{section.subtitle}</div>
        </div>
        <Icon size={18} />
      </div>
      <div className="panel-body route-list">
        {section.items.map((item) => (
          <DemoRouteItem item={item} key={item.title} />
        ))}
      </div>
    </section>
  );
}

function DemoRouteItem({ item }: { item: DemoItem }) {
  const Icon = item.icon;
  const body = (
    <>
      <div className="capability-icon">
        <Icon size={18} />
      </div>
      <div>
        <div className="route-name">{item.title}</div>
        <div className="route-path">{item.description}</div>
      </div>
      <StatusBadge label={item.status} tone={statusTone(item.status)} />
    </>
  );

  if (item.path) {
    return (
      <Link className="route-item" to={item.path}>
        {body}
      </Link>
    );
  }

  return (
    <div className="route-item" aria-label={`${item.title} frontend pending`}>
      {body}
    </div>
  );
}
