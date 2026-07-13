import {
  AlertTriangle,
  CheckCircle2,
  FileWarning,
  GitBranch,
  Link as LinkIcon,
  Search,
  ShieldCheck,
  Split,
  Target,
  type LucideIcon,
} from "lucide-react";
import { Link } from "react-router-dom";

import { KpiCard } from "../../components/KpiCard";
import { StatusBadge } from "../../components/StatusBadge";

type SupportCase = {
  title: string;
  category: string;
  lookup: string;
  route: string;
  routeLabel: string;
  description: string;
  icon: LucideIcon;
};

const supportCases: SupportCase[] = [
  {
    title: "Code or link not recognized",
    category: "VALIDATION_RECOVERY",
    lookup: "Referral code, campaign code, route link, or composite code",
    route: "/admin/referral-saas/operator-links",
    routeLabel: "Inspect link/code",
    description: "Start from canonical link/code inspection before opening trace or progress views.",
    icon: LinkIcon,
  },
  {
    title: "Validation failed or customer cannot continue",
    category: "VALIDATION_RECOVERY",
    lookup: "Referral code, alias, terms context, or referral track",
    route: "/admin/referral-saas/link-codes",
    routeLabel: "Review link/code workflow",
    description: "Use product validation recovery and retry posture without creating duplicate support actions.",
    icon: AlertTriangle,
  },
  {
    title: "Progress stuck or delayed",
    category: "PROGRESS_DIAGNOSTIC",
    lookup: "Referral track ID",
    route: "/admin/referral-saas/progress-status",
    routeLabel: "Inspect progress/status",
    description: "Review safe progress, product status, missing evidence, redactions, and next diagnostics.",
    icon: CheckCircle2,
  },
  {
    title: "Attribution missing or partial",
    category: "ATTRIBUTION_REVIEW",
    lookup: "Referral track ID",
    route: "/admin/referral-saas/attribution-trace",
    routeLabel: "Inspect attribution trace",
    description: "Connect outcome, attribution, participant, event, and audit evidence through the trace surface.",
    icon: Split,
  },
  {
    title: "Campaign not ready",
    category: "READINESS_BLOCKER",
    lookup: "Campaign code",
    route: "/admin/referral-saas/campaigns",
    routeLabel: "Review campaign readiness",
    description: "Review setup blockers and warnings without exposing activation controls.",
    icon: Target,
  },
  {
    title: "Report count mismatch",
    category: "REPORTING_FRESHNESS",
    lookup: "Report type, campaign, and date window",
    route: "/admin/referral-saas/reports",
    routeLabel: "Review Referral SaaS reports",
    description: "Use tenant-safe reports, freshness, warnings, redactions, and inline previews.",
    icon: FileWarning,
  },
];

const guardrails = [
  "Read-only evidence first",
  "No support-case writes",
  "No repair, retry, or replay",
  "No reward, funding, fulfilment, settlement, wallet, invoice, or payout controls",
  "No raw UCN, provider payload, audit payload, DLQ payload, token, or secret rendering",
];

export function ReferralSaasSupportHubPage() {
  return (
    <>
      <section className="page-header">
        <div>
          <div className="page-kicker">Referral SaaS - Operator Support</div>
          <h1 className="page-title">Support workflow hub</h1>
          <p className="page-copy">
            Route validation, progress, link/code, attribution, campaign, and
            reporting questions into read-only product diagnostics without
            creating repair, replay, support-case, or money actions.
          </p>
        </div>
        <StatusBadge label="Read-only" tone="info" />
      </section>

      <section className="grid-4">
        <KpiCard label="Support cases" value={supportCases.length} footnote="First-launch case types" icon={Search} />
        <KpiCard label="Read-only routes" value={supportCases.length} footnote="No mutation paths" icon={ShieldCheck} />
        <KpiCard label="Mutation actions" value="0" footnote="Deferred until audited workflow" icon={AlertTriangle} />
        <KpiCard label="Money actions" value="0" footnote="Outside Referral SaaS support" icon={GitBranch} />
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2 className="panel-title">Support triage path</h2>
            <div className="panel-subtitle">
              Start from the safest lookup, then move through bounded product surfaces.
            </div>
          </div>
          <StatusBadge label="No DB access" tone="success" />
        </div>
        <div className="panel-body route-list">
          {supportCases.map((item) => {
            const Icon = item.icon;
            return (
              <Link className="route-item route-link" key={item.title} to={item.route}>
                <div>
                  <div className="route-name">{item.title}</div>
                  <div className="route-path">{item.description}</div>
                  <div className="route-path">Lookup: {item.lookup}</div>
                </div>
                <div className="support-hub-action">
                  <StatusBadge label={item.category} tone="info" />
                  <span className="support-hub-route">
                    <Icon size={15} />
                    {item.routeLabel}
                  </span>
                </div>
              </Link>
            );
          })}
        </div>
      </section>

      <section className="grid-2">
        <div className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Read-only evidence order</h2>
              <div className="panel-subtitle">Support should move from narrow evidence to broader context.</div>
            </div>
          </div>
          <div className="panel-body route-list">
            <Step title="1. Link/code inspection" copy="Confirm source, tenant bridge, missing evidence, warnings, and next diagnostics." />
            <Step title="2. Progress/status" copy="Review safe progress, product status, missing evidence, redactions, and next milestone." />
            <Step title="3. Attribution trace" copy="Inspect outcome, attribution, participant, event, and audit evidence." />
            <Step title="4. Campaign and reports" copy="Check readiness, freshness, aggregate quality, and tenant-safe report evidence." />
          </div>
        </div>

        <div className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Guardrails</h2>
              <div className="panel-subtitle">The hub does not authorize support mutations.</div>
            </div>
            <ShieldCheck size={18} />
          </div>
          <div className="panel-body route-list">
            {guardrails.map((guardrail) => (
              <div className="route-item" key={guardrail}>
                <div>
                  <div className="route-name">{guardrail}</div>
                  <div className="route-path">Deferred unless a later task adds role, audit, idempotency, and tests.</div>
                </div>
                <StatusBadge label="Guarded" tone="warning" />
              </div>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}

function Step({ title, copy }: { title: string; copy: string }) {
  return (
    <div className="route-item">
      <div>
        <div className="route-name">{title}</div>
        <div className="route-path">{copy}</div>
      </div>
      <StatusBadge label="Read-only" tone="info" />
    </div>
  );
}
