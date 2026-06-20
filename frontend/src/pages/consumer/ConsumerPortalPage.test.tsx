import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactElement } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ConsumerPortalPage } from "./ConsumerPortalPage";
import { getConsumerExperience, getConsumerInsuranceProof } from "../../api/endpoints/consumerPortal";
import { expectNamedInteractiveElements } from "../../test/accessibility";

vi.mock("../../api/endpoints/consumerPortal", () => ({
  acceptConsumerTerms: vi.fn(),
  bootstrapConsumerReferrer: vi.fn(),
  captureConsumerRefereeUcn: vi.fn(),
  getConsumerExperience: vi.fn(),
  getConsumerInsuranceProof: vi.fn(),
  getConsumerReferralDashboard: vi.fn(),
  issueConsumerReferralCode: vi.fn(),
  validateConsumerReferralCode: vi.fn(),
}));

const mockedGetConsumerExperience = vi.mocked(getConsumerExperience);
const mockedGetConsumerInsuranceProof = vi.mocked(getConsumerInsuranceProof);

function renderWithQuery(ui: ReactElement) {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

function rewardsPanel(container: HTMLElement) {
  const panel = container.querySelector("#consumer-rewards");
  if (!panel) {
    throw new Error("Consumer rewards panel was not rendered");
  }
  return within(panel as HTMLElement);
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((settled) => {
    resolve = settled;
  });
  return { promise, resolve };
}

describe("ConsumerPortalPage", () => {
  beforeEach(() => {
    localStorage.clear();
    mockedGetConsumerInsuranceProof.mockResolvedValue({});
  });

  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("loads value and rewards from the consumer experience aggregate", async () => {
    mockedGetConsumerExperience.mockResolvedValue({
      status: "ok",
      tenantCode: "FNB",
      referrerUcn: "UCN-123",
      referralTrackId: "TRACK-1",
      leaderboardCode: "GLOBAL_OVERALL",
      unavailableSections: [],
      guardrail: "Read-only aggregate.",
      sections: {
        profile: { status: "ok", data: { referrals: [{ referral_track_id: "TRACK-1" }] } },
        rewards: { status: "ok", data: { earned_amount: "125.50", pending_amount: "20.00" } },
        missions: { status: "ok", data: { items: [{ name: "VIP onboarding", status: "OPEN", progress: "2/3" }] } },
        leaderboard: { status: "ok", data: { rank: "Gold" } },
      },
    });

    const { container } = renderWithQuery(<ConsumerPortalPage />);
    const panel = rewardsPanel(container);

    fireEvent.change(panel.getByLabelText("Profile reference"), { target: { value: "UCN-123" } });
    fireEvent.click(panel.getByRole("button", { name: /load value/i }));

    await waitFor(() => {
      expect(mockedGetConsumerExperience).toHaveBeenCalledWith({
        tenantCode: "FNB",
        referrerUcn: "UCN-123",
        referralTrackId: undefined,
        leaderboardCode: "SMOKE-LEADERBOARD",
      });
    });

    expect(await screen.findByText("VIP onboarding")).toBeInTheDocument();
    expect(panel.getByText("125.50")).toBeInTheDocument();
    expect(panel.getByText("20.00")).toBeInTheDocument();
    expect(screen.queryByText("Partial data")).not.toBeInTheDocument();
  });

  it("shows a partial-data state when aggregate sections are unavailable", async () => {
    mockedGetConsumerExperience.mockResolvedValue({
      status: "partial",
      tenantCode: "FNB",
      referrerUcn: "UCN-123",
      referralTrackId: null,
      leaderboardCode: "GLOBAL_OVERALL",
      unavailableSections: ["missions", "leaderboard"],
      guardrail: "Read-only aggregate.",
      sections: {
        profile: { status: "ok", data: { referrals: [] } },
        rewards: { status: "ok", data: { earned_amount: "50.00", pending_amount: "0.00" } },
        missions: { status: "unavailable", data: null, error: "Mission service unavailable" },
        leaderboard: { status: "unavailable", data: null, error: "Leaderboard unavailable" },
      },
    });

    const { container } = renderWithQuery(<ConsumerPortalPage />);
    const panel = rewardsPanel(container);

    fireEvent.change(panel.getByLabelText("Profile reference"), { target: { value: "UCN-123" } });
    fireEvent.click(panel.getByRole("button", { name: /load value/i }));

    expect(await screen.findByText("Partial data")).toBeInTheDocument();
    expect(screen.getByText(/missions, leaderboard/i)).toBeInTheDocument();
    expect(panel.getByText("No missions returned.")).toBeInTheDocument();
  });

  it("shows action-specific loading feedback while value is loading", async () => {
    const pendingExperience = deferred<Record<string, unknown>>();
    mockedGetConsumerExperience.mockReturnValue(pendingExperience.promise);

    const { container } = renderWithQuery(<ConsumerPortalPage />);
    const panel = rewardsPanel(container);

    fireEvent.change(panel.getByLabelText("Profile reference"), { target: { value: "UCN-123" } });
    fireEvent.click(panel.getByRole("button", { name: /load value/i }));

    expect(await screen.findByText("Loading value and rewards")).toBeInTheDocument();

    pendingExperience.resolve({
      status: "ok",
      sections: {
        profile: { status: "ok", data: {} },
        rewards: { status: "ok", data: {} },
        missions: { status: "ok", data: {} },
        leaderboard: { status: "ok", data: {} },
      },
      unavailableSections: [],
    });

    await waitFor(() => {
      expect(screen.queryByText("Loading value and rewards")).not.toBeInTheDocument();
    });
  });

  it("shows structured API errors from the aggregate load", async () => {
    mockedGetConsumerExperience.mockRejectedValue({
      status: 503,
      message: "Experience temporarily unavailable",
    });

    const { container } = renderWithQuery(<ConsumerPortalPage />);
    const panel = rewardsPanel(container);

    fireEvent.change(panel.getByLabelText("Profile reference"), { target: { value: "UCN-123" } });
    fireEvent.click(panel.getByRole("button", { name: /load value/i }));

    expect(await screen.findByText("Status 503")).toBeInTheDocument();
    expect(screen.getByText("Experience temporarily unavailable")).toBeInTheDocument();
  });

  it("keeps consumer journey controls accessible by name", () => {
    const { container } = renderWithQuery(<ConsumerPortalPage />);

    expectNamedInteractiveElements(container);
  });
});
