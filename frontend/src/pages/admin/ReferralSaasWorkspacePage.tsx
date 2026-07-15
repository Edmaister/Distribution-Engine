import {
  BarChart3,
  Building2,
  CheckCircle2,
  ClipboardCheck,
  Link as LinkIcon,
  ListChecks,
  PlayCircle,
  Route,
  ShieldCheck,
  Split,
  Target,
  type LucideIcon,
} from "lucide-react";
import { Link } from "react-router-dom";

import { KpiCard } from "../../components/KpiCard";
import { StatusBadge } from "../../components/StatusBadge";

type WorkspaceLink = {
  title: string;
  route: string;
  description: string;
  badge: string;
  icon: LucideIcon;
};

const primaryWorkflows: WorkspaceLink[] = [
  {
    title: "Account setup",
    route: "/admin/referral-saas/account-setup",
    description: "External-reference setup, membership posture, and launch readiness gates.",
    badge: "Setup",
    icon: Building2,
  },
  {
    title: "Account maintenance",
    route: "/admin/referral-saas/account-maintenance",
    description: "Read-only account health, setup drift, blocked commands, and evidence routing.",
    badge: "Maintain",
    icon: ShieldCheck,
  },
  {
    title: "Campaign readiness",
    route: "/admin/referral-saas/campaigns",
    description: "Campaign setup evidence, blockers, warnings, and safe launch posture.",
    badge: "Campaigns",
    icon: Target,
  },
  {
    title: "Links and codes",
    route: "/admin/referral-saas/link-codes",
    description: "Issue, reuse, validate, recover, and capture identity through product wrappers.",
    badge: "Referral",
    icon: LinkIcon,
  },
  {
    title: "Reports",
    route: "/admin/referral-saas/reports",
    description: "Tenant-safe report catalog, freshness, redactions, and inline export preview.",
    badge: "Reporting",
    icon: BarChart3,
  },
];

const supportWorkflows: WorkspaceLink[] = [
  {
    title: "Support hub",
    route: "/admin/referral-saas/support",
    description: "Route support cases to the right read-only evidence surface.",
    badge: "Triage",
    icon: ShieldCheck,
  },
  {
    title: "Link inspection",
    route: "/admin/referral-saas/operator-links",
    description: "Inspect source evidence for referral codes, campaign codes, and links.",
    badge: "Inspect",
    icon: Route,
  },
  {
    title: "Attribution trace",
    route: "/admin/referral-saas/attribution-trace",
    description: "Explain outcome attribution from campaign, link/code, participant, and event evidence.",
    badge: "Trace",
    icon: Split,
  },
  {
    title: "Progress status",
    route: "/admin/referral-saas/progress-status",
    description: "Review safe progress, product status, redactions, and missing evidence.",
    badge: "Status",
    icon: ListChecks,
  },
];

const boundaries = [
  "Focused on referral management and campaign attribution only",
  "No distributor marketplace, wallet, settlement, funding, billing, or treasury controls",
  "No repair, replay, retry, reward, payout, invoice, or money movement actions",
  "No raw UCN, provider payload, DLQ payload, token, secret, or cross-tenant evidence rendering",
];

const testingSteps: WorkspaceLink[] = [
  {
    title: "1. Check account setup",
    route: "/admin/referral-saas/account-setup",
    description: "Start here to confirm the account, external references, membership posture, and readiness gates.",
    badge: "Start",
    icon: Building2,
  },
  {
    title: "2. Review account maintenance",
    route: "/admin/referral-saas/account-maintenance",
    description: "Confirm existing setup evidence, health drift, guardrails, and unavailable maintenance commands.",
    badge: "Review",
    icon: ShieldCheck,
  },
  {
    title: "3. Check campaign readiness",
    route: "/admin/referral-saas/campaigns",
    description: "Then confirm the campaign has the setup evidence needed before referral traffic is tested.",
    badge: "Next",
    icon: Target,
  },
  {
    title: "4. Test links and codes",
    route: "/admin/referral-saas/link-codes",
    description: "Issue, reuse, validate, and recover referral codes through the product workflow.",
    badge: "Action",
    icon: LinkIcon,
  },
  {
    title: "5. Prove attribution and reporting",
    route: "/admin/referral-saas/support",
    description: "Use support triage to inspect link evidence, progress/status, attribution trace, and reports.",
    badge: "Verify",
    icon: ClipboardCheck,
  },
];

export function ReferralSaasWorkspacePage() {
  return (
    <>
      <section className="page-header">
        <div>
          <div className="page-kicker">Referral Management and Campaign Attribution SaaS</div>
          <h1 className="page-title">Start testing Referral SaaS</h1>
          <p className="page-copy">
            This screen is the front door for testing account setup, campaign
            readiness, referral links/codes, attribution evidence, and
            tenant-safe reporting without broader DLaaS workflows.
          </p>
        </div>
        <StatusBadge label="Ringfenced" tone="success" />
      </section>

      <section className="grid-3">
        <div className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">What this screen is for</h2>
              <div className="panel-subtitle">A guided launch and testing cockpit for the focused SaaS product.</div>
            </div>
            <StatusBadge label="Workspace" tone="info" />
          </div>
          <div className="panel-body">
            <p className="page-copy">
              Use it to move through the product in the same order a customer or
              operator would: setup, campaign readiness, referral link/code
              flow, attribution investigation, and reports.
            </p>
          </div>
        </div>
        <div className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">What you can do here</h2>
              <div className="panel-subtitle">Open the right product surface without DLaaS noise.</div>
            </div>
            <StatusBadge label="9 paths" tone="success" />
          </div>
          <div className="panel-body">
            <p className="page-copy">
              You can check readiness, issue or validate referral codes, inspect
              support evidence, review progress/status, trace attribution, and
              confirm tenant-safe reports.
            </p>
          </div>
        </div>
        <div className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">What to do first</h2>
              <div className="panel-subtitle">Start with account setup, then move left to right.</div>
            </div>
            <PlayCircle size={18} />
          </div>
          <div className="panel-body">
            <p className="page-copy">
              Click <strong>Check account setup</strong>. If setup is blocked,
              fix that first. If it is usable, continue to campaign readiness,
              then links/codes, then support evidence and reports.
            </p>
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2 className="panel-title">Recommended test path</h2>
            <div className="panel-subtitle">
              Follow this order when you are doing local live testing from the UI.
            </div>
          </div>
          <StatusBadge label="Start here" tone="success" />
        </div>
        <div className="panel-body route-list">
          {testingSteps.map((step) => (
            <WorkspaceLinkItem item={step} key={step.route} />
          ))}
        </div>
      </section>

      <section className="grid-4">
        <KpiCard label="Core areas to test" value={primaryWorkflows.length} footnote="Setup, maintenance, campaigns, links/codes, reports" icon={CheckCircle2} />
        <KpiCard label="Investigation areas" value={supportWorkflows.length} footnote="Support, inspection, trace, status" icon={ShieldCheck} />
        <KpiCard label="DLaaS items shown" value="0" footnote="Marketplace, wallet, funding, settlement hidden" icon={Target} />
        <KpiCard label="Money actions available" value="0" footnote="No payout, invoice, wallet, or settlement actions" icon={BarChart3} />
      </section>

      <section className="grid-2">
        <WorkspacePanel title="All product work areas" subtitle="Use these after the recommended test path when you need a specific surface." items={primaryWorkflows} />
        <WorkspacePanel title="All investigation areas" subtitle="Read-only support paths for link/code, progress, and attribution evidence." items={supportWorkflows} />
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2 className="panel-title">Workspace boundary</h2>
            <div className="panel-subtitle">
              This shell intentionally excludes broader DLaaS workflows from the Referral SaaS operating path.
            </div>
          </div>
          <StatusBadge label="No source fork" tone="info" />
        </div>
        <div className="panel-body route-list">
          {boundaries.map((boundary) => (
            <div className="route-item" key={boundary}>
              <div>
                <div className="route-name">{boundary}</div>
                <div className="route-path">Shared platform primitives remain single-source behind the product surfaces.</div>
              </div>
              <StatusBadge label="Guarded" tone="warning" />
            </div>
          ))}
        </div>
      </section>
    </>
  );
}

function WorkspacePanel({
  title,
  subtitle,
  items,
}: {
  title: string;
  subtitle: string;
  items: WorkspaceLink[];
}) {
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <h2 className="panel-title">{title}</h2>
          <div className="panel-subtitle">{subtitle}</div>
        </div>
      </div>
      <div className="panel-body route-list">
        {items.map((item) => {
          return (
            <WorkspaceLinkItem item={item} key={item.route} />
          );
        })}
      </div>
    </section>
  );
}

function WorkspaceLinkItem({ item }: { item: WorkspaceLink }) {
  const Icon = item.icon;
  return (
    <Link className="route-item route-link" to={item.route}>
      <div>
        <div className="route-name">{item.title}</div>
        <div className="route-path">{item.description}</div>
      </div>
      <span className="support-hub-route">
        <Icon size={15} />
        {item.badge}
      </span>
    </Link>
  );
}
