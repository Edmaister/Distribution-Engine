import {
  BarChart3,
  Building2,
  CheckCircle2,
  Link as LinkIcon,
  ListChecks,
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

export function ReferralSaasWorkspacePage() {
  return (
    <>
      <section className="page-header">
        <div>
          <div className="page-kicker">Referral Management and Campaign Attribution SaaS</div>
          <h1 className="page-title">Focused workspace</h1>
          <p className="page-copy">
            Operate the Referral SaaS product without mixing in broader DLaaS
            marketplace, wallet, funding, settlement, sponsor billing, or
            treasury workflows.
          </p>
        </div>
        <StatusBadge label="Ringfenced" tone="success" />
      </section>

      <section className="grid-4">
        <KpiCard label="Product workflows" value={primaryWorkflows.length} footnote="SaaS core" icon={CheckCircle2} />
        <KpiCard label="Support workflows" value={supportWorkflows.length} footnote="Read-only diagnostics" icon={ShieldCheck} />
        <KpiCard label="DLaaS controls" value="0" footnote="Hidden from this workspace" icon={Target} />
        <KpiCard label="Money actions" value="0" footnote="Outside Referral SaaS launch" icon={BarChart3} />
      </section>

      <section className="grid-2">
        <WorkspacePanel title="Operate" subtitle="The core SaaS workflow for account, campaign, referral, and reporting work." items={primaryWorkflows} />
        <WorkspacePanel title="Investigate" subtitle="Read-only support paths for link/code, progress, and attribution evidence." items={supportWorkflows} />
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
          const Icon = item.icon;
          return (
            <Link className="route-item route-link" key={item.route} to={item.route}>
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
        })}
      </div>
    </section>
  );
}
