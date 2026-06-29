import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactElement } from "react";
import { createMemoryRouter, Outlet, RouterProvider } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { DistributionCommandCentrePage } from "./DistributionCommandCentrePage";
import {
  acceptAdminRoute,
  activateAdminDistributor,
  creditAdminDistributorWallet,
  getAdminDistributorWalletLedger,
  getAdminDistributorWallets,
  getAdminDistributionAttributionExceptions,
  getAdminDistributionDistributorReport,
  getAdminDistributionGovernanceReport,
  getAdminDistributionOpportunityReport,
  getAdminDistributionOverview,
  getAdminDistributors,
  getAdminGovernanceAudit,
  getAdminOpportunities,
  getAdminRoutes,
  getAdminComplianceReviews,
  getAdminDisputes,
  publishAdminOpportunity,
} from "../../api/endpoints/distribution";

vi.mock("../../api/endpoints/distribution", () => ({
  acceptAdminRoute: vi.fn(),
  activateAdminDistributor: vi.fn(),
  applyAdminDistributorGovernanceAction: vi.fn(),
  closeAdminOpportunity: vi.fn(),
  completeAdminComplianceReview: vi.fn(),
  createAdminComplianceReview: vi.fn(),
  createAdminDispute: vi.fn(),
  creditAdminDistributorWallet: vi.fn(),
  declineAdminRoute: vi.fn(),
  getAdminComplianceReviews: vi.fn(),
  getAdminDisputes: vi.fn(),
  getAdminDistributionAttributionExceptions: vi.fn(),
  getAdminDistributorWalletLedger: vi.fn(),
  getAdminDistributorWallets: vi.fn(),
  getAdminDistributionDistributorReport: vi.fn(),
  getAdminDistributionGovernanceReport: vi.fn(),
  getAdminDistributionOpportunityReport: vi.fn(),
  getAdminDistributionOverview: vi.fn(),
  getAdminDistributors: vi.fn(),
  getAdminGovernanceAudit: vi.fn(),
  getAdminOpportunities: vi.fn(),
  getAdminRoutes: vi.fn(),
  holdAdminDistributorWallet: vi.fn(),
  payoutAdminDistributorWallet: vi.fn(),
  publishAdminOpportunity: vi.fn(),
  releaseHoldAdminDistributorWallet: vi.fn(),
  reopenAdminOpportunity: vi.fn(),
  resolveAdminDispute: vi.fn(),
  reverseAdminDistributorWallet: vi.fn(),
  suspendAdminDistributor: vi.fn(),
  terminateAdminDistributor: vi.fn(),
}));

const mockedAcceptAdminRoute = vi.mocked(acceptAdminRoute);
const mockedActivateAdminDistributor = vi.mocked(activateAdminDistributor);
const mockedCreditAdminDistributorWallet = vi.mocked(
  creditAdminDistributorWallet,
);
const mockedGetAdminComplianceReviews = vi.mocked(getAdminComplianceReviews);
const mockedGetAdminDisputes = vi.mocked(getAdminDisputes);
const mockedGetAdminDistributorWalletLedger = vi.mocked(
  getAdminDistributorWalletLedger,
);
const mockedGetAdminDistributorWallets = vi.mocked(getAdminDistributorWallets);
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
const mockedGetAdminGovernanceAudit = vi.mocked(getAdminGovernanceAudit);
const mockedGetAdminOpportunities = vi.mocked(getAdminOpportunities);
const mockedGetAdminRoutes = vi.mocked(getAdminRoutes);
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

function input(container: HTMLElement, selector: string) {
  const element = container.querySelector(selector);
  if (!element) {
    throw new Error(`${selector} was not rendered`);
  }
  return element as HTMLInputElement;
}

function select(container: HTMLElement, selector: string) {
  const element = container.querySelector<HTMLSelectElement>(selector);
  if (!element) {
    throw new Error(`${selector} was not rendered`);
  }
  return element;
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
  mockedGetAdminDistributorWalletLedger.mockResolvedValue([
    {
      transaction_type: "CREDIT",
      amount: "25.00",
      balance_before: "125.00",
      balance_after: "150.00",
      created_at: "2026-06-18T08:00:00Z",
    },
  ]);
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

describe("DistributionCommandCentrePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    mockDistributionOperationsData();
    vi.spyOn(window, "confirm").mockReturnValue(true);
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    localStorage.clear();
  });

  it("loads the admin operations command-centre panels from distribution data", async () => {
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
    expect(mockedGetAdminDistributors).toHaveBeenCalledWith("FNB");
  });

  it("runs guarded lifecycle and funding workflows", async () => {
    const { container } = renderWorkspace(
      <DistributionCommandCentrePage mode="operations" />,
    );

    await screen.findByRole("heading", { name: "Demand Operations" });

    const lifecycle = panel(container, "#distribution-distributor-lifecycle");
    const wallet = panel(container, "#distribution-wallet-operations");

    const activateButton = lifecycle.getByRole("button", {
      name: /^activate$/i,
    });
    const distributorSelect = select(
      container,
      "#distribution-distributor-action",
    );
    await waitFor(() => expect(distributorSelect.value).toBe("DIST-1"));
    await waitFor(() => expect(activateButton).toBeEnabled());

    fireEvent.click(activateButton);
    await waitFor(() =>
      expect(mockedActivateAdminDistributor).toHaveBeenCalledWith("DIST-1"),
    );

    await waitFor(() =>
      expect(wallet.getByRole("button", { name: /^credit$/i })).toBeEnabled(),
    );
    fireEvent.change(input(container, "#wallet-action-amount"), {
      target: { value: "10.00" },
    });
    fireEvent.change(input(container, "#wallet-action-correlation"), {
      target: { value: "ADMIN-WORKFLOW-1" },
    });
    fireEvent.click(wallet.getByRole("button", { name: /^credit$/i }));
    await waitFor(() => {
      expect(mockedCreditAdminDistributorWallet).toHaveBeenCalledWith(
        "WALLET-1",
        expect.objectContaining({
          amount: "10.00",
          correlation_id: "ADMIN-WORKFLOW-1",
        }),
      );
    });
  });

  it("runs guarded opportunity and route workflows", async () => {
    const { container } = renderWorkspace(
      <DistributionCommandCentrePage mode="operations" />,
    );

    await screen.findByRole("heading", { name: "Demand Operations" });

    const opportunity = panel(container, "#distribution-opportunity-actions");
    const route = panel(container, "#distribution-route-actions");

    await waitFor(() =>
      expect(
        opportunity.getByRole("button", { name: /^publish$/i }),
      ).toBeEnabled(),
    );
    fireEvent.click(opportunity.getByRole("button", { name: /^publish$/i }));
    await waitFor(() =>
      expect(mockedPublishAdminOpportunity).toHaveBeenCalledWith("OPP-1"),
    );

    await waitFor(() =>
      expect(route.getByRole("button", { name: /^accept$/i })).toBeEnabled(),
    );
    fireEvent.click(route.getByRole("button", { name: /^accept$/i }));
    await waitFor(() =>
      expect(mockedAcceptAdminRoute).toHaveBeenCalledWith("ROUTE-1"),
    );
  });
});
