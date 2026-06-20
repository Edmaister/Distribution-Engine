import { cleanup, render, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactElement } from "react";
import { createMemoryRouter, Outlet, RouterProvider } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AdminAuditPage } from "./admin/AdminAuditPage";
import { HealthPage } from "./admin/HealthPage";
import { DistributorPortalPage } from "./distributor/DistributorPortalPage";
import { SponsorPortalPage } from "./sponsor/SponsorPortalPage";
import {
  expectNamedInteractiveElements,
  expectNoPositiveTabIndex,
  expectValidAriaReferences,
} from "../test/accessibility";

vi.mock("../auth/useBackendSession", () => ({
  normalizeSessionRole: (role: unknown) => String(role || "").toLowerCase(),
  useBackendSession: () => ({ status: "idle", session: null }),
}));

vi.mock("../api/endpoints/adminAudit", () => ({
  getAdminAuditEntries: vi.fn().mockResolvedValue([]),
  getAdminAuditSummary: vi.fn().mockResolvedValue({ summary: { total: 0 }, total: 0 }),
}));

vi.mock("../api/endpoints/health", () => ({
  getHealth: vi.fn().mockResolvedValue({ components: {} }),
  getReadiness: vi.fn().mockResolvedValue({ components: { schema: { groups: {} } } }),
}));

vi.mock("../api/endpoints/distribution", () => ({
  acceptDistributorPortalOffer: vi.fn().mockResolvedValue({}),
  declineDistributorPortalOffer: vi.fn().mockResolvedValue({}),
  getAdminDistributors: vi.fn().mockResolvedValue({ items: [] }),
  getDistributorPortalChannelReadiness: vi.fn().mockResolvedValue({}),
  getDistributorPortalChannelRecommendations: vi.fn().mockResolvedValue({ items: [] }),
  getDistributorPortalConversions: vi.fn().mockResolvedValue({ items: [] }),
  getDistributorExperience: vi.fn().mockResolvedValue({ sections: {} }),
  getDistributorPortalInsuranceProof: vi.fn().mockResolvedValue({ steps: [] }),
  getDistributorPortalOutcomeMoneyReview: vi.fn().mockResolvedValue({ items: [] }),
  getDistributorPortalOffers: vi.fn().mockResolvedValue({ items: [] }),
  getDistributorPortalPerformance: vi.fn().mockResolvedValue({}),
  getDistributorPortalProfile: vi.fn().mockResolvedValue({}),
  getDistributorPortalWalletLedger: vi.fn().mockResolvedValue({ items: [] }),
  getDistributorPortalWallets: vi.fn().mockResolvedValue({ items: [] }),
  getRecognitionBadges: vi.fn().mockResolvedValue({ items: [] }),
  getRecognitionMissions: vi.fn().mockResolvedValue({ items: [] }),
  getRecognitionProgress: vi.fn().mockResolvedValue({}),
  getTenantLeaderboard: vi.fn().mockResolvedValue({ items: [] }),
  linkDistributorPortalOfferReferral: vi.fn().mockResolvedValue({}),
}));

vi.mock("../api/endpoints/sponsorBilling", () => ({
  closeProducerSupplyOpportunity: vi.fn().mockResolvedValue({}),
  createProducerSupplyLaunch: vi.fn().mockResolvedValue({}),
  getAdminSponsorWallets: vi.fn().mockResolvedValue({ items: [] }),
  getProducerSupplyChannelReadiness: vi.fn().mockResolvedValue({}),
  getProducerSupplyChannelRecommendations: vi.fn().mockResolvedValue({ items: [] }),
  getProducerSupplyConversions: vi.fn().mockResolvedValue({ items: [] }),
  getSponsorExperience: vi.fn().mockResolvedValue({ sections: {} }),
  getProducerSupplyInsuranceProof: vi.fn().mockResolvedValue({ steps: [] }),
  getProducerSupplyOutcomeMoneyReview: vi.fn().mockResolvedValue({ items: [] }),
  getProducerSupplyOpportunities: vi.fn().mockResolvedValue({ items: [] }),
  getProducerSupplyOpportunityPerformance: vi.fn().mockResolvedValue({ items: [] }),
  getProducerSupplyPerformanceOverview: vi.fn().mockResolvedValue({}),
  getSponsorPortalContractLedger: vi.fn().mockResolvedValue({ items: [] }),
  getSponsorPortalContracts: vi.fn().mockResolvedValue({ items: [] }),
  getSponsorPortalDashboard: vi.fn().mockResolvedValue({}),
  getSponsorPortalForecast: vi.fn().mockResolvedValue({}),
  getSponsorPortalInvoices: vi.fn().mockResolvedValue({ items: [] }),
  getSponsorPortalPaymentReceipts: vi.fn().mockResolvedValue({ items: [] }),
  getSponsorPortalStatement: vi.fn().mockResolvedValue({}),
  getSponsorPortalWallet: vi.fn().mockResolvedValue({}),
  getSponsorPortalWalletLedger: vi.fn().mockResolvedValue({ items: [] }),
  publishProducerSupplyOpportunity: vi.fn().mockResolvedValue({}),
  reopenProducerSupplyOpportunity: vi.fn().mockResolvedValue({}),
  updateProducerSupplyOpportunity: vi.fn().mockResolvedValue({}),
}));

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

function expectAccessibleWorkspace(container: HTMLElement) {
  expect(container.querySelector("h1")).not.toBeNull();
  expectNamedInteractiveElements(container);
  expectNoPositiveTabIndex(container);
  expectValidAriaReferences(container);
}

describe("workspace accessibility", () => {
  afterEach(() => {
    cleanup();
    localStorage.clear();
  });

  it("covers representative admin workspaces", async () => {
    const audit = renderWorkspace(<AdminAuditPage />);
    await waitFor(() => expect(audit.container.querySelector("h1")).not.toBeNull());
    expectAccessibleWorkspace(audit.container);
    cleanup();

    const health = renderWorkspace(<HealthPage />);
    await waitFor(() => expect(health.container.querySelector("h1")).not.toBeNull());
    expectAccessibleWorkspace(health.container);
  });

  it("covers sponsor and distributor entry workspaces", async () => {
    const sponsor = renderWorkspace(<SponsorPortalPage />);
    await waitFor(() => expect(sponsor.container.querySelector("h1")).not.toBeNull());
    expectAccessibleWorkspace(sponsor.container);
    cleanup();

    const distributor = renderWorkspace(<DistributorPortalPage />);
    await waitFor(() => expect(distributor.container.querySelector("h1")).not.toBeNull());
    expectAccessibleWorkspace(distributor.container);
  });
});
