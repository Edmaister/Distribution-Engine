import {
  cleanup,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactElement } from "react";
import { createMemoryRouter, Outlet, RouterProvider } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { CompanyOnboardingPage } from "./CompanyOnboardingPage";
import { CampaignOpportunitySetupPage } from "./CampaignOpportunitySetupPage";
import { DistributionCommandCentrePage } from "./DistributionCommandCentrePage";
import { DistributorOnboardingPage } from "./DistributorOnboardingPage";
import { MemberRoleOnboardingPage } from "./MemberRoleOnboardingPage";
import { OnboardingReadinessChecklistPage } from "./OnboardingReadinessChecklistPage";
import { OperatorDemoHomePage } from "./OperatorDemoHomePage";
import { ProducerSponsorOnboardingPage } from "./ProducerSponsorOnboardingPage";
import { WebhookApiSetupPage } from "./WebhookApiSetupPage";
import { DistributorPortalPage } from "../distributor/DistributorPortalPage";
import { getAdminOnboardingState } from "../../api/endpoints/adminOnboarding";
import { createAdminOnboardingStateResponse } from "../../api/endpoints/adminOnboarding.testFixtures";
import {
  acceptAdminRoute,
  activateAdminDistributor,
  creditAdminDistributorWallet,
  getAdminComplianceReviews,
  getAdminDisputes,
  getAdminDistributionAttributionExceptions,
  getAdminDistributionDistributorReport,
  getAdminDistributionGovernanceReport,
  getAdminDistributionOpportunityReport,
  getAdminDistributionOverview,
  getAdminDistributors,
  getAdminDistributorWalletLedger,
  getAdminDistributorWallets,
  getAdminGovernanceAudit,
  getAdminOpportunities,
  getAdminRoutes,
  getDistributorExperience,
  getDistributorPortalWalletLedger,
  getRecognitionBadges,
  getRecognitionMissions,
  getRecognitionProgress,
  getTenantLeaderboard,
  publishAdminOpportunity,
} from "../../api/endpoints/distribution";

vi.mock("../../auth/useBackendSession", () => ({
  normalizeSessionRole: (role: unknown) => String(role || "").toLowerCase(),
  useBackendSession: () => ({ status: "idle", session: null }),
}));

vi.mock("../../api/endpoints/adminOnboarding", () => ({
  getAdminOnboardingState: vi.fn(),
  saveAdminOnboardingDraft: vi.fn(),
  validateAdminOnboardingDryRun: vi.fn(),
}));

vi.mock("../../api/endpoints/distribution", () => ({
  acceptAdminRoute: vi.fn(),
  acceptDistributorPortalOffer: vi.fn(),
  activateAdminDistributor: vi.fn(),
  applyAdminDistributorGovernanceAction: vi.fn(),
  closeAdminOpportunity: vi.fn(),
  completeAdminComplianceReview: vi.fn(),
  createAdminComplianceReview: vi.fn(),
  createAdminDispute: vi.fn(),
  creditAdminDistributorWallet: vi.fn(),
  declineAdminRoute: vi.fn(),
  declineDistributorPortalOffer: vi.fn(),
  getAdminComplianceReviews: vi.fn(),
  getAdminDisputes: vi.fn(),
  getAdminDistributionAttributionExceptions: vi.fn(),
  getAdminDistributionDistributorReport: vi.fn(),
  getAdminDistributionGovernanceReport: vi.fn(),
  getAdminDistributionOpportunityReport: vi.fn(),
  getAdminDistributionOverview: vi.fn(),
  getAdminDistributors: vi.fn(),
  getAdminDistributorWalletLedger: vi.fn(),
  getAdminDistributorWallets: vi.fn(),
  getAdminGovernanceAudit: vi.fn(),
  getAdminOpportunities: vi.fn(),
  getAdminRoutes: vi.fn(),
  getDistributorExperience: vi.fn(),
  getDistributorPortalWalletLedger: vi.fn(),
  getRecognitionBadges: vi.fn(),
  getRecognitionMissions: vi.fn(),
  getRecognitionProgress: vi.fn(),
  getTenantLeaderboard: vi.fn(),
  holdAdminDistributorWallet: vi.fn(),
  linkDistributorPortalOfferReferral: vi.fn(),
  payoutAdminDistributorWallet: vi.fn(),
  publishAdminOpportunity: vi.fn(),
  releaseHoldAdminDistributorWallet: vi.fn(),
  reopenAdminOpportunity: vi.fn(),
  resolveAdminDispute: vi.fn(),
  reverseAdminDistributorWallet: vi.fn(),
  suspendAdminDistributor: vi.fn(),
  terminateAdminDistributor: vi.fn(),
}));

const mockedGetAdminOnboardingState = vi.mocked(getAdminOnboardingState);
const mockedAcceptAdminRoute = vi.mocked(acceptAdminRoute);
const mockedActivateAdminDistributor = vi.mocked(activateAdminDistributor);
const mockedCreditAdminDistributorWallet = vi.mocked(
  creditAdminDistributorWallet,
);
const mockedGetAdminComplianceReviews = vi.mocked(getAdminComplianceReviews);
const mockedGetAdminDisputes = vi.mocked(getAdminDisputes);
const mockedGetAdminDistributionAttributionExceptions = vi.mocked(
  getAdminDistributionAttributionExceptions,
);
const mockedGetAdminDistributionDistributorReport = vi.mocked(
  getAdminDistributionDistributorReport,
);
const mockedGetAdminDistributionGovernanceReport = vi.mocked(
  getAdminDistributionGovernanceReport,
);
const mockedGetAdminDistributionOpportunityReport = vi.mocked(
  getAdminDistributionOpportunityReport,
);
const mockedGetAdminDistributionOverview = vi.mocked(
  getAdminDistributionOverview,
);
const mockedGetAdminDistributors = vi.mocked(getAdminDistributors);
const mockedGetAdminDistributorWalletLedger = vi.mocked(
  getAdminDistributorWalletLedger,
);
const mockedGetAdminDistributorWallets = vi.mocked(getAdminDistributorWallets);
const mockedGetAdminGovernanceAudit = vi.mocked(getAdminGovernanceAudit);
const mockedGetAdminOpportunities = vi.mocked(getAdminOpportunities);
const mockedGetAdminRoutes = vi.mocked(getAdminRoutes);
const mockedGetDistributorExperience = vi.mocked(getDistributorExperience);
const mockedGetDistributorPortalWalletLedger = vi.mocked(
  getDistributorPortalWalletLedger,
);
const mockedGetRecognitionBadges = vi.mocked(getRecognitionBadges);
const mockedGetRecognitionMissions = vi.mocked(getRecognitionMissions);
const mockedGetRecognitionProgress = vi.mocked(getRecognitionProgress);
const mockedGetTenantLeaderboard = vi.mocked(getTenantLeaderboard);
const mockedPublishAdminOpportunity = vi.mocked(publishAdminOpportunity);

function renderWorkspace(ui: ReactElement) {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  const router = createMemoryRouter([
    {
      path: "/",
      element: <Outlet context={{ refreshKey: 0 }} />,
      children: [{ index: true, element: ui }],
    },
  ]);

  return render(
    <QueryClientProvider client={client}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
}

function panel(container: HTMLElement, selector: string) {
  const element = container.querySelector(selector);
  if (!element) {
    throw new Error(`${selector} was not rendered`);
  }
  return within(element as HTMLElement);
}

function mockDistributionOperationsData() {
  mockedGetAdminDistributors.mockResolvedValue([
    {
      distributor_id: "DIST-1",
      distributor_code: "DST-ALPHA",
      distributor_name: "Alpha Distribution",
      status: "PENDING",
      trust_score: 72,
    },
  ]);
  mockedGetAdminOpportunities.mockResolvedValue([
    {
      opportunity_id: "OPP-1",
      opportunity_code: "OPP-READY",
      title: "Family protection campaign",
      sponsor_code: "SPONSOR-1",
      opportunity_status: "DRAFT",
      total_budget: "50000.00",
    },
  ]);
  mockedGetAdminRoutes.mockResolvedValue([
    {
      route_id: "ROUTE-1",
      opportunity_id: "OPP-1",
      distributor_id: "DIST-1",
      distributor_code: "DST-ALPHA",
      route_status: "ROUTED",
      route_score: "0.91",
    },
  ]);
  mockedGetAdminDistributorWallets.mockResolvedValue([
    {
      wallet_id: "WALLET-1",
      distributor_id: "DIST-1",
      distributor_code: "DST-ALPHA",
      currency: "ZAR",
      available_balance: "150.00",
      held_balance: "25.00",
      status: "ACTIVE",
    },
  ]);
  mockedGetAdminDistributorWalletLedger.mockResolvedValue([]);
  mockedGetAdminComplianceReviews.mockResolvedValue([]);
  mockedGetAdminDisputes.mockResolvedValue([]);
  mockedGetAdminGovernanceAudit.mockResolvedValue([]);
  mockedGetAdminDistributionOverview.mockResolvedValue({
    distributors: { active_count: 0 },
    opportunities: { published_count: 0 },
    routes: { accepted_count: 0 },
    conversions: {
      linked_count: 0,
      completed_count: 0,
      total_referral_count: 0,
      unlinked_count: 0,
      attribution_rate: "0.0000",
    },
    commissions: { total_commission_amount: "0.00" },
    wallets: { current_balance: "150.00" },
    governance: { open_dispute_count: 0 },
  });
  mockedGetAdminDistributionOpportunityReport.mockResolvedValue({ items: [] });
  mockedGetAdminDistributionDistributorReport.mockResolvedValue({ items: [] });
  mockedGetAdminDistributionGovernanceReport.mockResolvedValue({
    compliance_reviews: [],
    disputes: [],
    governance_actions: [],
  });
  mockedGetAdminDistributionAttributionExceptions.mockResolvedValue({
    items: [],
    count: 0,
    completed_count: 0,
  });
  mockedActivateAdminDistributor.mockResolvedValue({
    distributor_id: "DIST-1",
    status: "ACTIVE",
  });
  mockedPublishAdminOpportunity.mockResolvedValue({
    opportunity_id: "OPP-1",
    opportunity_status: "PUBLISHED",
  });
  mockedAcceptAdminRoute.mockResolvedValue({
    route_id: "ROUTE-1",
    route_status: "ACCEPTED",
  });
  mockedCreditAdminDistributorWallet.mockResolvedValue({
    wallet_id: "WALLET-1",
    available_balance: "151.00",
  });
}

function mockDistributorPortalData() {
  mockedGetAdminDistributors.mockResolvedValue([
    {
      distributor_code: "DIST-1",
      distributor_name: "Alpha Brokers",
      distributor_type: "BROKER",
      status: "ACTIVE",
    },
  ]);
  mockedGetDistributorExperience.mockResolvedValue({
    status: "ok",
    sections: {
      profile: {
        status: "ok",
        data: {
          distributor_code: "DIST-1",
          distributor_name: "Alpha Brokers",
          distributor_type: "BROKER",
          status: "ACTIVE",
        },
      },
      performance: {
        status: "ok",
        data: {
          routed_count: 2,
          accepted_count: 1,
          declined_count: 0,
          acceptance_rate: "0.5000",
          conversion_count: 1,
          completed_conversion_count: 0,
          conversion_completion_rate: "0.0000",
          total_commission_amount: "250.00",
          wallet_available_balance: "1500.00",
          wallet_held_balance: "250.00",
          currency: "ZAR",
        },
      },
      opportunities: {
        status: "ok",
        data: [
          {
            route_id: "ROUTE-1",
            opportunity_id: "OPP-1",
            title: "Family cover campaign",
            sponsor_code: "SPONSOR-1",
            route_status: "ROUTED",
            estimated_reward_amount: "100.00",
          },
        ],
      },
      conversions: {
        status: "ok",
        data: {
          items: [
            {
              referral_track_id: "TRACK-SAFE",
              display_status: "Validated",
              status: "VALIDATED",
              progress_percent: 40,
              distributor_safe_status: {
                status: "IN_PROGRESS",
                label: "In progress",
                summary: "Your outcome status is in progress.",
                what_happened: "Outcome evidence was received.",
                what_happens_next: "The platform is waiting for more evidence.",
                action_required: false,
                action_category: "WAITING_FOR_EVENT",
                terminal: false,
                source_families: ["outcome"],
                source_confidence: "LOW",
                missing_evidence: [
                  {
                    section: "attribution",
                    code: "NO_SOURCE_EVIDENCE",
                    severity: "INFO",
                  },
                ],
                redactions: [
                  "private_identifier",
                  "provider_payload",
                  "raw_status",
                ],
              },
            },
          ],
          count: 1,
          attributed_count: 0,
          unlinked_count: 1,
          attribution_rate: "0.0000",
        },
      },
      wallet: {
        status: "ok",
        data: [
          {
            wallet_id: "WALLET-1",
            currency: "ZAR",
            available_balance: "1500.00",
            held_balance: "250.00",
            paid_out_balance: "500.00",
            status: "ACTIVE",
          },
        ],
      },
      outcomeMoney: {
        status: "ok",
        data: { summary: { completed_outcome_count: 0, ready_count: 0 } },
      },
      proof: { status: "ok", data: { steps: [] } },
      channels: {
        status: "ok",
        data: {
          readiness: { status: "READY", summary: { ready_count: 2, count: 2 } },
        },
      },
    },
  });
  mockedGetDistributorPortalWalletLedger.mockResolvedValue([]);
  mockedGetTenantLeaderboard.mockResolvedValue({ items: [] });
  mockedGetRecognitionProgress.mockResolvedValue({ items: [] });
  mockedGetRecognitionBadges.mockResolvedValue({ items: [] });
  mockedGetRecognitionMissions.mockResolvedValue({ items: [] });
}

describe("onboarding demo journey smoke", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.spyOn(window, "confirm").mockReturnValue(true);
    mockedGetAdminOnboardingState.mockResolvedValue(
      createAdminOnboardingStateResponse({
        overall_status: "GO_LIVE_DISABLED",
        categories: [],
        summary: {
          ready_count: 0,
          in_progress_count: 0,
          blocked_count: 0,
          missing_evidence_count: 0,
          permission_limited_count: 0,
          go_live_disabled_count: 1,
          total_count: 1,
        },
      }),
    );
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("links the operator demo home through onboarding, readiness, monitoring, and distributor status", () => {
    renderWorkspace(<OperatorDemoHomePage />);

    expect(
      screen.getByRole("heading", { name: "Operator demo home" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /Company \/ organisation onboarding/ }),
    ).toHaveAttribute("href", "/admin/onboarding/company");
    expect(
      screen.getByRole("link", { name: /Producer \/ sponsor onboarding/ }),
    ).toHaveAttribute("href", "/admin/onboarding/producer-sponsor");
    expect(
      screen.getByRole("link", { name: /Distributor onboarding/ }),
    ).toHaveAttribute("href", "/admin/onboarding/distributor");
    expect(
      screen.getByRole("link", { name: /User \/ member role setup/ }),
    ).toHaveAttribute("href", "/admin/onboarding/members-roles");
    expect(
      screen.getByRole("link", { name: /Campaign \/ opportunity setup/ }),
    ).toHaveAttribute("href", "/admin/onboarding/campaign-opportunity");
    expect(
      screen.getByRole("link", { name: /Webhook \/ API setup/ }),
    ).toHaveAttribute("href", "/admin/onboarding/webhook-api");
    expect(
      screen.getByRole("link", { name: /Onboarding readiness checklist/ }),
    ).toHaveAttribute("href", "/admin/onboarding/readiness");
    expect(
      screen.getByRole("link", { name: /Demand operations/ }),
    ).toHaveAttribute("href", "/admin/distribution/operations");
    expect(
      screen.getByRole("link", { name: /Distributor safe status/ }),
    ).toHaveAttribute("href", "/distributor");
    expect(
      screen.getByRole("button", { name: "Start live demo later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Publish campaign later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Deliver webhook later" }),
    ).toBeDisabled();
  });

  it("renders each onboarding shell with disabled live actions and forward journey links", () => {
    const routeSmokeCases: Array<{
      ui: ReactElement;
      heading: string;
      disabledAction: string;
      forwardLink: RegExp;
    }> = [
      {
        ui: <CompanyOnboardingPage />,
        heading: "Company & organisation onboarding",
        disabledAction: "Create account later",
        forwardLink: /Producer \/ sponsor onboarding/,
      },
      {
        ui: <ProducerSponsorOnboardingPage />,
        heading: "Producer & sponsor onboarding",
        disabledAction: "Configure funding later",
        forwardLink: /Distributor onboarding/,
      },
      {
        ui: <DistributorOnboardingPage />,
        heading: "Distributor onboarding",
        disabledAction: "Create wallet later",
        forwardLink: /User & role setup/,
      },
      {
        ui: <MemberRoleOnboardingPage />,
        heading: "User, member & role setup",
        disabledAction: "Send invite later",
        forwardLink: /Campaign \/ opportunity setup/,
      },
      {
        ui: <CampaignOpportunitySetupPage />,
        heading: "Campaign & opportunity setup wizard",
        disabledAction: "Publish opportunity later",
        forwardLink: /Webhook & API setup/,
      },
      {
        ui: <WebhookApiSetupPage />,
        heading: "Webhook & API credential setup",
        disabledAction: "Create API key later",
        forwardLink: /Campaign \/ opportunity setup/,
      },
    ];

    routeSmokeCases.forEach(({ ui, heading, disabledAction, forwardLink }) => {
      renderWorkspace(ui);

      expect(
        screen.getByRole("heading", { name: heading }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: disabledAction }),
      ).toBeDisabled();
      expect(
        screen.getByRole("link", { name: forwardLink }),
      ).toBeInTheDocument();

      cleanup();
    });
  });

  it("renders the readiness checklist with setup links and disabled go-live controls", () => {
    renderWorkspace(<OnboardingReadinessChecklistPage />);

    expect(
      screen.getByRole("heading", { name: "Onboarding readiness checklist" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /Company onboarding/ }),
    ).toHaveAttribute("href", "/admin/onboarding/company");
    expect(
      screen.getByRole("link", { name: /Producer \/ sponsor onboarding/ }),
    ).toHaveAttribute("href", "/admin/onboarding/producer-sponsor");
    expect(
      screen.getByRole("link", { name: /Distributor onboarding/ }),
    ).toHaveAttribute("href", "/admin/onboarding/distributor");
    expect(
      screen.getByRole("link", { name: /User & role setup/ }),
    ).toHaveAttribute("href", "/admin/onboarding/members-roles");
    expect(
      screen.getByRole("button", { name: "Request go-live review later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Mark ready for review later" }),
    ).toBeDisabled();
    expect(screen.getByText("No live commands")).toBeInTheDocument();
  });

  it("renders read-only operations monitoring without triggering guarded workflows", async () => {
    mockDistributionOperationsData();

    const { container } = renderWorkspace(
      <DistributionCommandCentrePage mode="operations" />,
    );

    expect(
      await screen.findByRole("heading", { name: "Demand Operations" }),
    ).toBeInTheDocument();
    expect(
      panel(container, "#distribution-distributor-lifecycle").getByText(
        "Distributor lifecycle",
      ),
    ).toBeInTheDocument();
    expect(
      panel(container, "#distribution-wallet-operations").getByText(
        "Distributor wallet operations",
      ),
    ).toBeInTheDocument();
    expect(
      panel(container, "#distribution-opportunity-actions").getByText(
        "Opportunity actions",
      ),
    ).toBeInTheDocument();
    expect(
      panel(container, "#distribution-route-actions").getByText(
        "Route actions",
      ),
    ).toBeInTheDocument();
    await waitFor(() =>
      expect(mockedGetAdminDistributors).toHaveBeenCalledWith("FNB"),
    );
    expect(mockedActivateAdminDistributor).not.toHaveBeenCalled();
    expect(mockedCreditAdminDistributorWallet).not.toHaveBeenCalled();
    expect(mockedPublishAdminOpportunity).not.toHaveBeenCalled();
    expect(mockedAcceptAdminRoute).not.toHaveBeenCalled();
  });

  it("renders distributor safe status without unsafe internal identifiers", async () => {
    localStorage.setItem("amplifi.distributorPortal.tenant", "FNB");
    localStorage.setItem("amplifi.distributorPortal.distributor", "DIST-1");
    mockDistributorPortalData();

    const { container } = renderWorkspace(
      <DistributorPortalPage mode="operations" />,
    );

    expect(
      await screen.findByRole("heading", { name: "Earnings Operations" }),
    ).toBeInTheDocument();

    const safeStatusPanel = panel(container, "#distributor-safe-status");
    expect(
      safeStatusPanel.getByText("Outcome progress status"),
    ).toBeInTheDocument();
    expect(
      safeStatusPanel.getByText(/Your outcome status is in progress/),
    ).toBeInTheDocument();
    expect(safeStatusPanel.queryByText(/tenant_code/i)).not.toBeInTheDocument();
    expect(
      safeStatusPanel.queryByText(/provider_payload/i),
    ).not.toBeInTheDocument();
    expect(safeStatusPanel.queryByText(/raw_status/i)).not.toBeInTheDocument();
    expect(safeStatusPanel.queryByText(/ucn/i)).not.toBeInTheDocument();
  });
});
