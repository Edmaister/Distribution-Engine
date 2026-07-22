import { lazy, Suspense, useState, type ReactNode } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { LoadingState } from "../components/LoadingState";
import { AppShell } from "../layout/AppShell";

const AdminOverviewPage = lazy(() =>
  import("../pages/admin/AdminOverviewPage").then((module) => ({ default: module.AdminOverviewPage })),
);
const AdminAuditPage = lazy(() =>
  import("../pages/admin/AdminAuditPage").then((module) => ({ default: module.AdminAuditPage })),
);
const CompanyOnboardingPage = lazy(() =>
  import("../pages/admin/CompanyOnboardingPage").then((module) => ({
    default: module.CompanyOnboardingPage,
  })),
);
const ProducerSponsorOnboardingPage = lazy(() =>
  import("../pages/admin/ProducerSponsorOnboardingPage").then((module) => ({
    default: module.ProducerSponsorOnboardingPage,
  })),
);
const DistributorOnboardingPage = lazy(() =>
  import("../pages/admin/DistributorOnboardingPage").then((module) => ({
    default: module.DistributorOnboardingPage,
  })),
);
const MemberRoleOnboardingPage = lazy(() =>
  import("../pages/admin/MemberRoleOnboardingPage").then((module) => ({
    default: module.MemberRoleOnboardingPage,
  })),
);
const CampaignOpportunitySetupPage = lazy(() =>
  import("../pages/admin/CampaignOpportunitySetupPage").then((module) => ({
    default: module.CampaignOpportunitySetupPage,
  })),
);
const WebhookApiSetupPage = lazy(() =>
  import("../pages/admin/WebhookApiSetupPage").then((module) => ({
    default: module.WebhookApiSetupPage,
  })),
);
const OnboardingReadinessChecklistPage = lazy(() =>
  import("../pages/admin/OnboardingReadinessChecklistPage").then((module) => ({
    default: module.OnboardingReadinessChecklistPage,
  })),
);
const OperatorDemoHomePage = lazy(() =>
  import("../pages/admin/OperatorDemoHomePage").then((module) => ({
    default: module.OperatorDemoHomePage,
  })),
);
const ChannelOperationsPage = lazy(() =>
  import("../pages/admin/ChannelOperationsPage").then((module) => ({
    default: module.ChannelOperationsPage,
  })),
);
const ReferralSaasReportsPage = lazy(() =>
  import("../pages/admin/ReferralSaasReportsPage").then((module) => ({
    default: module.ReferralSaasReportsPage,
  })),
);
const ReferralSaasAccountSetupPage = lazy(() =>
  import("../pages/admin/ReferralSaasAccountSetupPage").then((module) => ({
    default: module.ReferralSaasAccountSetupPage,
  })),
);
const ReferralSaasAccountMaintenancePage = lazy(() =>
  import("../pages/admin/ReferralSaasAccountMaintenancePage").then((module) => ({
    default: module.ReferralSaasAccountMaintenancePage,
  })),
);
const ReferralSaasWorkspacePage = lazy(() =>
  import("../pages/admin/ReferralSaasWorkspacePage").then((module) => ({
    default: module.ReferralSaasWorkspacePage,
  })),
);
const ReferralSaasCampaignReadinessPage = lazy(() =>
  import("../pages/admin/ReferralSaasCampaignReadinessPage").then((module) => ({
    default: module.ReferralSaasCampaignReadinessPage,
  })),
);
const ReferralSaasLinkCodeWorkflowPage = lazy(() =>
  import("../pages/admin/ReferralSaasLinkCodeWorkflowPage").then((module) => ({
    default: module.ReferralSaasLinkCodeWorkflowPage,
  })),
);
const ReferralSaasOperatorLinkInspectPage = lazy(() =>
  import("../pages/admin/ReferralSaasOperatorLinkInspectPage").then((module) => ({
    default: module.ReferralSaasOperatorLinkInspectPage,
  })),
);
const ReferralSaasAttributionTracePage = lazy(() =>
  import("../pages/admin/ReferralSaasAttributionTracePage").then((module) => ({
    default: module.ReferralSaasAttributionTracePage,
  })),
);
const ReferralSaasProgressStatusPage = lazy(() =>
  import("../pages/admin/ReferralSaasProgressStatusPage").then((module) => ({
    default: module.ReferralSaasProgressStatusPage,
  })),
);
const ReferralSaasSupportHubPage = lazy(() =>
  import("../pages/admin/ReferralSaasSupportHubPage").then((module) => ({
    default: module.ReferralSaasSupportHubPage,
  })),
);
const EnterpriseEventsPage = lazy(() =>
  import("../pages/admin/EnterpriseEventsPage").then((module) => ({ default: module.EnterpriseEventsPage })),
);
const HealthPage = lazy(() =>
  import("../pages/admin/HealthPage").then((module) => ({ default: module.HealthPage })),
);
const BillingSpinePage = lazy(() =>
  import("../pages/admin/BillingSpinePage").then((module) => ({ default: module.BillingSpinePage })),
);
const DistributionCommandCentrePage = lazy(() =>
  import("../pages/admin/DistributionCommandCentrePage").then((module) => ({
    default: module.DistributionCommandCentrePage,
  })),
);
const DistributionOperationsPage = lazy(() =>
  import("../pages/admin/DistributionCommandCentrePage").then((module) => ({
    default: module.DistributionOperationsPage,
  })),
);
const MultiCurrencyPage = lazy(() =>
  import("../pages/admin/MultiCurrencyPage").then((module) => ({ default: module.MultiCurrencyPage })),
);
const SettlementOperationsPage = lazy(() =>
  import("../pages/admin/SettlementOperationsPage").then((module) => ({
    default: module.SettlementOperationsPage,
  })),
);
const ConsumerPortalPage = lazy(() =>
  import("../pages/consumer/ConsumerPortalPage").then((module) => ({ default: module.ConsumerPortalPage })),
);
const DistributorPortalPage = lazy(() =>
  import("../pages/distributor/DistributorPortalPage").then((module) => ({
    default: module.DistributorPortalPage,
  })),
);
const DistributorOperationsPage = lazy(() =>
  import("../pages/distributor/DistributorPortalPage").then((module) => ({
    default: module.DistributorOperationsPage,
  })),
);
const DistributorWalletPage = lazy(() =>
  import("../pages/distributor/DistributorWalletPage").then((module) => ({
    default: module.DistributorWalletPage,
  })),
);
const PartnerIntegrationPage = lazy(() =>
  import("../pages/partner/PartnerIntegrationPage").then((module) => ({ default: module.PartnerIntegrationPage })),
);
const SponsorPortalPage = lazy(() =>
  import("../pages/sponsor/SponsorPortalPage").then((module) => ({ default: module.SponsorPortalPage })),
);
const SponsorOperationsPage = lazy(() =>
  import("../pages/sponsor/SponsorPortalPage").then((module) => ({ default: module.SponsorOperationsPage })),
);

function lazyWorkspace(element: ReactNode) {
  return <Suspense fallback={<LoadingState label="Loading workspace" />}>{element}</Suspense>;
}

export function App() {
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <Routes>
      <Route
        element={<AppShell refreshKey={refreshKey} onRefresh={() => setRefreshKey((value) => value + 1)} />}
      >
        <Route path="/admin" element={lazyWorkspace(<AdminOverviewPage />)} />
        <Route path="/admin/onboarding/company" element={lazyWorkspace(<CompanyOnboardingPage />)} />
        <Route
          path="/admin/onboarding/producer-sponsor"
          element={lazyWorkspace(<ProducerSponsorOnboardingPage />)}
        />
        <Route
          path="/admin/onboarding/distributor"
          element={lazyWorkspace(<DistributorOnboardingPage />)}
        />
        <Route
          path="/admin/onboarding/members-roles"
          element={lazyWorkspace(<MemberRoleOnboardingPage />)}
        />
        <Route
          path="/admin/onboarding/campaign-opportunity"
          element={lazyWorkspace(<CampaignOpportunitySetupPage />)}
        />
        <Route
          path="/admin/onboarding/webhook-api"
          element={lazyWorkspace(<WebhookApiSetupPage />)}
        />
        <Route
          path="/admin/onboarding/readiness"
          element={lazyWorkspace(<OnboardingReadinessChecklistPage />)}
        />
        <Route path="/admin/demo-home" element={lazyWorkspace(<OperatorDemoHomePage />)} />
        <Route path="/admin/health" element={lazyWorkspace(<HealthPage />)} />
        <Route path="/admin/audit" element={lazyWorkspace(<AdminAuditPage />)} />
        <Route path="/admin/channels" element={lazyWorkspace(<ChannelOperationsPage />)} />
        <Route path="/admin/referral-saas" element={lazyWorkspace(<ReferralSaasWorkspacePage />)} />
        <Route path="/admin/referral-saas/account-setup" element={lazyWorkspace(<ReferralSaasAccountSetupPage />)} />
        <Route path="/admin/referral-saas/account-maintenance" element={lazyWorkspace(<ReferralSaasAccountMaintenancePage />)} />
        <Route path="/admin/referral-saas/account-maintenance/:accountId" element={lazyWorkspace(<ReferralSaasAccountMaintenancePage />)} />
        <Route path="/admin/referral-saas/account-maintenance/:accountId/:customerModule" element={lazyWorkspace(<ReferralSaasAccountMaintenancePage />)} />
        <Route path="/admin/referral-saas/account-maintenance/:accountId/:customerModule/:customerSubModule" element={lazyWorkspace(<ReferralSaasAccountMaintenancePage />)} />
        <Route path="/admin/referral-saas/campaigns" element={lazyWorkspace(<ReferralSaasCampaignReadinessPage />)} />
        <Route path="/admin/referral-saas/link-codes" element={lazyWorkspace(<ReferralSaasLinkCodeWorkflowPage />)} />
        <Route path="/admin/referral-saas/operator-links" element={lazyWorkspace(<ReferralSaasOperatorLinkInspectPage />)} />
        <Route path="/admin/referral-saas/support" element={lazyWorkspace(<ReferralSaasSupportHubPage />)} />
        <Route path="/admin/referral-saas/attribution-trace" element={lazyWorkspace(<ReferralSaasAttributionTracePage />)} />
        <Route path="/admin/referral-saas/progress-status" element={lazyWorkspace(<ReferralSaasProgressStatusPage />)} />
        <Route path="/admin/referral-saas/reports" element={lazyWorkspace(<ReferralSaasReportsPage />)} />
        <Route path="/admin/events" element={lazyWorkspace(<EnterpriseEventsPage />)} />
        <Route path="/admin/distribution" element={lazyWorkspace(<DistributionCommandCentrePage />)} />
        <Route path="/admin/distribution/operations" element={lazyWorkspace(<DistributionOperationsPage />)} />
        <Route path="/admin/multi-currency" element={lazyWorkspace(<MultiCurrencyPage />)} />
        <Route path="/admin/settlements" element={lazyWorkspace(<SettlementOperationsPage />)} />
        <Route path="/admin/billing" element={lazyWorkspace(<BillingSpinePage />)} />
        <Route path="/sponsor" element={lazyWorkspace(<SponsorPortalPage />)} />
        <Route path="/sponsor/operations" element={lazyWorkspace(<SponsorOperationsPage />)} />
        <Route path="/partner" element={lazyWorkspace(<PartnerIntegrationPage />)} />
        <Route path="/distributor" element={lazyWorkspace(<DistributorPortalPage />)} />
        <Route path="/distributor/wallet" element={lazyWorkspace(<DistributorWalletPage />)} />
        <Route path="/distributor/operations" element={lazyWorkspace(<DistributorOperationsPage />)} />
        <Route path="/consumer" element={lazyWorkspace(<ConsumerPortalPage />)} />
        <Route path="*" element={<Navigate to="/admin" replace />} />
      </Route>
    </Routes>
  );
}

export default App;
