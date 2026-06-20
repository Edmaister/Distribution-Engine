import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactElement } from "react";
import { createMemoryRouter, Outlet, RouterProvider } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { DistributorPortalPage } from "./DistributorPortalPage";
import {
  acceptDistributorPortalOffer,
  getAdminDistributors,
  getDistributorExperience,
  getDistributorPortalWalletLedger,
  getRecognitionBadges,
  getRecognitionMissions,
  getRecognitionProgress,
  getTenantLeaderboard,
  linkDistributorPortalOfferReferral,
} from "../../api/endpoints/distribution";

vi.mock("../../auth/useBackendSession", () => ({
  normalizeSessionRole: (role: unknown) => String(role || "").toLowerCase(),
  useBackendSession: () => ({ status: "idle", session: null }),
}));

vi.mock("../../api/endpoints/distribution", () => ({
  acceptDistributorPortalOffer: vi.fn(),
  declineDistributorPortalOffer: vi.fn(),
  getAdminDistributors: vi.fn(),
  getDistributorExperience: vi.fn(),
  getDistributorPortalWalletLedger: vi.fn(),
  getRecognitionBadges: vi.fn(),
  getRecognitionMissions: vi.fn(),
  getRecognitionProgress: vi.fn(),
  getTenantLeaderboard: vi.fn(),
  linkDistributorPortalOfferReferral: vi.fn(),
}));

const mockedAcceptDistributorPortalOffer = vi.mocked(acceptDistributorPortalOffer);
const mockedGetAdminDistributors = vi.mocked(getAdminDistributors);
const mockedGetDistributorExperience = vi.mocked(getDistributorExperience);
const mockedGetDistributorPortalWalletLedger = vi.mocked(getDistributorPortalWalletLedger);
const mockedGetRecognitionBadges = vi.mocked(getRecognitionBadges);
const mockedGetRecognitionMissions = vi.mocked(getRecognitionMissions);
const mockedGetRecognitionProgress = vi.mocked(getRecognitionProgress);
const mockedGetTenantLeaderboard = vi.mocked(getTenantLeaderboard);
const mockedLinkDistributorPortalOfferReferral = vi.mocked(linkDistributorPortalOfferReferral);

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

function field(container: HTMLElement, selector: string) {
  const element = container.querySelector(selector);
  if (!element) {
    throw new Error(`${selector} was not rendered`);
  }
  return element as HTMLInputElement;
}

function mockDistributorData() {
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
          channels: ["WHATSAPP", "FIELD"],
          segments: ["INSURANCE"],
          regions: ["ZA"],
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
          {
            route_id: "ROUTE-2",
            opportunity_id: "OPP-2",
            title: "Youth account campaign",
            sponsor_code: "SPONSOR-2",
            route_status: "ACCEPTED",
            estimated_reward_amount: "150.00",
          },
        ],
      },
      conversions: {
        status: "ok",
        data: {
          items: [
            {
              referral_track_id: "TRACK-UNLINKED",
              display_status: "Validated",
              status: "VALIDATED",
              progress_percent: 40,
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
      outcomeMoney: { status: "ok", data: { summary: { completed_outcome_count: 0, ready_count: 0 } } },
      proof: { status: "ok", data: { steps: [] } },
      channels: {
        status: "ok",
        data: {
          readiness: { status: "READY", summary: { ready_count: 2, count: 2 } },
          recommendations: {
            top_channel: {
              channel_code: "WHATSAPP",
              recommendation_score: "0.94",
              recommended_action: "Send WhatsApp reminder",
              provider_status: "READY",
            },
            event_type: "ROUTE_ASSIGNED",
            audience: "DISTRIBUTOR",
          },
        },
      },
    },
  });
  mockedGetDistributorPortalWalletLedger.mockResolvedValue([
    {
      transaction_type: "CREDIT",
      amount: "250.00",
      balance_before: "1250.00",
      balance_after: "1500.00",
      created_at: "2026-06-18T08:00:00Z",
    },
  ]);
  mockedGetTenantLeaderboard.mockResolvedValue({ items: [] });
  mockedGetRecognitionProgress.mockResolvedValue({ items: [] });
  mockedGetRecognitionBadges.mockResolvedValue({ items: [] });
  mockedGetRecognitionMissions.mockResolvedValue({ items: [] });
  mockedAcceptDistributorPortalOffer.mockResolvedValue({ route_id: "ROUTE-1", route_status: "ACCEPTED" });
  mockedLinkDistributorPortalOfferReferral.mockResolvedValue({
    route_id: "ROUTE-2",
    referral_track_id: "TRACK-123",
    status: "LINKED",
  });
}

describe("DistributorPortalPage", () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem("amplifi.distributorPortal.tenant", "FNB");
    localStorage.setItem("amplifi.distributorPortal.distributor", "DIST-1");
    mockDistributorData();
    vi.spyOn(window, "confirm").mockReturnValue(true);
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("loads distributor opportunities, wallet activity, and performance panels", async () => {
    const { container } = renderWorkspace(<DistributorPortalPage mode="operations" />);

    expect(await screen.findByRole("heading", { name: "Earnings Operations" })).toBeInTheDocument();
    expect(panel(container, "#distributor-offer-decision").getByText("Offer decision")).toBeInTheDocument();
    expect(panel(container, "#distributor-wallet-activity").getByText("Wallet activity")).toBeInTheDocument();
    expect(panel(container, "#distributor-offer-inbox").getByText("Offer inbox")).toBeInTheDocument();
    expect(panel(container, "#distributor-wallet-ledger").getByText("Wallet ledger")).toBeInTheDocument();
    expect(mockedGetDistributorExperience).toHaveBeenCalledWith("FNB", "DIST-1");
    await waitFor(() =>
      expect(mockedGetDistributorPortalWalletLedger).toHaveBeenCalledWith("FNB", "DIST-1", "WALLET-1"),
    );
  });

  it("accepts a routed distributor offer", async () => {
    const { container } = renderWorkspace(<DistributorPortalPage mode="operations" />);

    await screen.findByRole("heading", { name: "Earnings Operations" });

    const offerDecision = panel(container, "#distributor-offer-decision");
    await waitFor(() => expect(offerDecision.getByRole("button", { name: /^accept$/i })).toBeEnabled());
    fireEvent.click(offerDecision.getByRole("button", { name: /^accept$/i }));

    await waitFor(() => {
      expect(mockedAcceptDistributorPortalOffer).toHaveBeenCalledWith("FNB", "DIST-1", "ROUTE-1");
    });
  });

  it("links an accepted offer route to a customer journey", async () => {
    const { container } = renderWorkspace(<DistributorPortalPage mode="operations" />);

    await screen.findByRole("heading", { name: "Earnings Operations" });

    const journeyLink = panel(container, "#customer-conversion-link");
    fireEvent.change(field(container, "#referral-track-id"), { target: { value: "TRACK-123" } });
    await waitFor(() => expect(journeyLink.getByRole("button", { name: /^link journey$/i })).toBeEnabled());
    fireEvent.click(journeyLink.getByRole("button", { name: /^link journey$/i }));

    await waitFor(() => {
      expect(mockedLinkDistributorPortalOfferReferral).toHaveBeenCalledWith("FNB", "DIST-1", "ROUTE-2", "TRACK-123");
    });
  });
});
