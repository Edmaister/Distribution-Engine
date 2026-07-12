import { Outlet, useLocation } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
import { HealthBanner } from "./HealthBanner";
import { SessionRoleBanner } from "../auth/SessionRoleBanner";
import { BackendSessionProvider } from "../auth/useBackendSession";

const titles: Record<string, [string, string]> = {
  "/admin": ["Amplifi Admin", "Platform operator command centre"],
  "/admin/onboarding/company": ["Company Onboarding", "Organisation setup and external identifier shell"],
  "/admin/onboarding/producer-sponsor": [
    "Producer Onboarding",
    "Sponsor setup, funding-readiness placeholders, and campaign ownership shell",
  ],
  "/admin/onboarding/distributor": [
    "Distributor Onboarding",
    "Distributor setup, channel intent, and portal readiness shell",
  ],
  "/admin/onboarding/members-roles": [
    "User & Role Setup",
    "Invite, membership, and role-family assignment shell",
  ],
  "/admin/onboarding/campaign-opportunity": [
    "Campaign Setup",
    "Campaign, opportunity, readiness, and go-live shell",
  ],
  "/admin/onboarding/webhook-api": [
    "Webhook & API Setup",
    "Credential, callback, catalog, and payload preview shell",
  ],
  "/admin/onboarding/readiness": [
    "Onboarding Readiness",
    "Demo-safe go-live checklist and blockers",
  ],
  "/admin/demo-home": [
    "Operator Demo Home",
    "Onboarding journey, readiness review, and read-only monitoring path",
  ],
  "/admin/health": ["Runtime Health", "Platform readiness and dependency signals"],
  "/admin/audit": ["Trust & Audit", "Platform-sensitive action visibility"],
  "/admin/channels": ["Channel Operations", "Messaging delivery, retries, and channel audit evidence"],
  "/admin/referral-saas/reports": ["Referral SaaS Reports", "Tenant-safe report catalog and export preview readiness"],
  "/admin/events": ["Event Fabric", "Hogan and enterprise event intake"],
  "/admin/distribution": ["Demand Marketplace", "Company-created demand and campaign discovery"],
  "/admin/distribution/operations": ["Demand Operations", "Distributor eligibility, producer demand, routing, wallets, and governance controls"],
  "/admin/multi-currency": ["Treasury Rail", "FX rates and cross-border settlements"],
  "/admin/settlements": ["Settlement Rail", "Settlement exposure and batch controls"],
  "/admin/billing": ["Funding Spine", "Producer billing and funding controls"],
  "/partner": ["Partner Integration", "Credentials, webhook delivery health, and integration guardrails"],
  "/sponsor": ["Producer Workspace", "Campaigns, funding exposure, partner readiness, and company performance"],
  "/sponsor/operations": ["Producer Operations", "Supply launch, campaign lifecycle, billing, statements, wallet ledgers, and contracts"],
  "/distributor": ["Distributor Earnings Hub", "Earnings, referrals, reputation, opportunities, and rank"],
  "/distributor/wallet": ["My Wallet", "Wallet balances, settlement movement, and payout readiness"],
  "/distributor/operations": ["Earnings Operations", "Offer decisions, referral links, wallets, profile, and detailed records"],
  "/consumer": ["Conversion Journey", "Invisible onboarding, activation, and advocacy for demand conversion"],
};

export function AppShell({ refreshKey, onRefresh }: { refreshKey: number; onRefresh: () => void }) {
  const location = useLocation();
  const [title, subtitle] = titles[location.pathname] || titles["/admin"];
  const immersiveProducerWorkspace = location.pathname === "/sponsor";
  const shellClass =
    location.pathname === "/sponsor" || location.pathname === "/sponsor/operations"
      ? "app-shell producer-app-shell"
      : location.pathname === "/distributor" ||
          location.pathname === "/distributor/wallet" ||
          location.pathname === "/distributor/operations" ||
          location.pathname === "/admin/distribution" ||
          location.pathname === "/admin/distribution/operations"
        ? "app-shell distributor-app-shell"
        : "app-shell";

  return (
    <BackendSessionProvider refreshKey={refreshKey}>
      <div className={shellClass}>
        <Sidebar />
        <main className="main-shell">
          {immersiveProducerWorkspace ? null : <TopBar title={title} subtitle={subtitle} onRefresh={onRefresh} />}
          <div className="content">
            {immersiveProducerWorkspace ? null : (
              <>
                <HealthBanner refreshKey={refreshKey} />
                <SessionRoleBanner />
              </>
            )}
            <Outlet context={{ refreshKey }} />
          </div>
        </main>
      </div>
    </BackendSessionProvider>
  );
}
