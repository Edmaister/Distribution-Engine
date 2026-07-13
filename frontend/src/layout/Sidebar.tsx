import {
  Activity,
  BadgeDollarSign,
  Building2,
  CheckCircle2,
  Gauge,
  GitBranch,
  GitPullRequestArrow,
  Globe2,
  KeyRound,
  Landmark,
  Link2,
  RadioTower,
  ChartNoAxesColumn,
  ShieldCheck,
  Sparkles,
  Target,
  Trophy,
  Users,
  Wallet,
} from "lucide-react";
import { NavLink } from "react-router-dom";
import { useBackendSession, workspaceForPath } from "../auth/useBackendSession";

const sections = [
  {
    label: "Distributor - Demand",
    links: [
      { to: "/admin/onboarding/distributor", label: "Distributor Onboarding", icon: Users, sub: "Setup" },
      { to: "/distributor", label: "Earnings Hub", icon: Users, sub: "Earn" },
      { to: "/distributor/wallet", label: "My Wallet", icon: Wallet, sub: "Wallet" },
      { to: "/distributor/operations", label: "Earnings Operations", icon: GitPullRequestArrow, sub: "Ops" },
      { to: "/consumer", label: "Conversion Journey", icon: Trophy, sub: "Convert" },
      { to: "/admin/distribution", label: "Demand Marketplace", icon: GitPullRequestArrow, sub: "Demand" },
    ],
  },
  {
    label: "Producer - Supply",
    links: [
      { to: "/partner", label: "Partner Integration", icon: KeyRound, sub: "Connect" },
      { to: "/admin/onboarding/producer-sponsor", label: "Producer Onboarding", icon: Building2, sub: "Setup" },
      { to: "/admin/onboarding/campaign-opportunity", label: "Campaign Setup", icon: Target, sub: "Wizard" },
      { to: "/admin/onboarding/webhook-api", label: "Webhook & API Setup", icon: KeyRound, sub: "Safe" },
      { to: "/sponsor", label: "Producer Workspace", icon: Building2, sub: "Supply" },
      { to: "/sponsor/operations", label: "Producer Operations", icon: GitPullRequestArrow, sub: "Ops" },
      { to: "/admin/billing", label: "Funding Spine", icon: BadgeDollarSign, sub: "Fund" },
      { to: "/admin/multi-currency", label: "Treasury Rail", icon: Globe2, sub: "FX" },
    ],
  },
  {
    label: "Amplifi Admin",
    links: [
      { to: "/admin", label: "Command Centre", icon: Gauge, sub: "Admin" },
      { to: "/admin/demo-home", label: "Demo Home", icon: Sparkles, sub: "Demo" },
      { to: "/admin/onboarding/company", label: "Company Onboarding", icon: Building2, sub: "Setup" },
      { to: "/admin/referral-saas/account-setup", label: "Referral SaaS Setup", icon: Building2, sub: "Account" },
      { to: "/admin/referral-saas/campaigns", label: "Referral SaaS Campaigns", icon: Target, sub: "Ready" },
      { to: "/admin/referral-saas/link-codes", label: "Referral SaaS Links", icon: Link2, sub: "Codes" },
      { to: "/admin/onboarding/members-roles", label: "User & Role Setup", icon: ShieldCheck, sub: "Access" },
      { to: "/admin/onboarding/readiness", label: "Onboarding Readiness", icon: CheckCircle2, sub: "Review" },
      { to: "/admin/distribution/operations", label: "Demand Operations", icon: GitPullRequestArrow, sub: "Ops" },
      { to: "/admin/referral-saas/reports", label: "Referral SaaS Reports", icon: ChartNoAxesColumn, sub: "Reports" },
      { to: "/admin/channels", label: "Channel Operations", icon: RadioTower, sub: "Channels" },
      { to: "/admin/events", label: "Event Fabric", icon: GitBranch },
      { to: "/admin/settlements", label: "Settlement Rail", icon: Landmark },
      { to: "/admin/audit", label: "Trust & Audit", icon: ShieldCheck },
      { to: "/admin/health", label: "Runtime Health", icon: Activity },
    ],
  },
];

export function Sidebar() {
  const backend = useBackendSession();

  return (
    <aside className="sidebar">
      <div className="brand-mark">
        <div className="brand-lockup">
          <span className="brand-glyph">
            <Sparkles size={18} />
          </span>
          <div>
            <div className="brand-title">Amplifi</div>
            <div className="brand-subtitle">Distribution OS</div>
          </div>
        </div>
      </div>
      {sections.map((section) => (
        <nav className="nav-section" key={section.label}>
          <p className="nav-heading">{section.label}</p>
          {section.links.map((link) => {
            const Icon = link.icon;
            const workspace = workspaceForPath(backend.workspaces, link.to);
            const isRecommended = Boolean(
              workspace && backend.recommendedWorkspace?.code === workspace.code,
            );
            const accessLabel = backend.status === "confirmed" && workspace
              ? isRecommended
                ? "Start"
                : workspace.access === "allowed"
                ? "Open"
                : "Check"
              : link.sub;
            const accessClass = backend.status === "confirmed" && workspace
              ? isRecommended
                ? "nav-sub nav-sub-start"
                : workspace.access === "allowed"
                ? "nav-sub nav-sub-allowed"
                : "nav-sub nav-sub-blocked"
              : "nav-sub";
            return (
              <NavLink className="nav-link" end key={link.to} to={link.to}>
                <Icon size={17} />
                <span>{link.label}</span>
                {accessLabel ? <span className={accessClass}>{accessLabel}</span> : null}
              </NavLink>
            );
          })}
        </nav>
      ))}
    </aside>
  );
  }
