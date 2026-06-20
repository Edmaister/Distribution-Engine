import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactElement } from "react";
import { createMemoryRouter, Outlet, RouterProvider } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { SponsorPortalPage } from "./SponsorPortalPage";
import {
  createProducerSupplyLaunch,
  getAdminSponsorWallets,
  getSponsorExperience,
  getSponsorPortalContractLedger,
  getSponsorPortalStatement,
  getSponsorPortalWalletLedger,
  publishProducerSupplyOpportunity,
  updateProducerSupplyOpportunity,
} from "../../api/endpoints/sponsorBilling";

vi.mock("../../auth/useBackendSession", () => ({
  normalizeSessionRole: (role: unknown) => String(role || "").toLowerCase(),
  useBackendSession: () => ({ status: "idle", session: null }),
}));

vi.mock("../../api/endpoints/sponsorBilling", () => ({
  closeProducerSupplyOpportunity: vi.fn(),
  createProducerSupplyLaunch: vi.fn(),
  getAdminSponsorWallets: vi.fn(),
  getSponsorExperience: vi.fn(),
  getSponsorPortalContractLedger: vi.fn(),
  getSponsorPortalStatement: vi.fn(),
  getSponsorPortalWalletLedger: vi.fn(),
  publishProducerSupplyOpportunity: vi.fn(),
  reopenProducerSupplyOpportunity: vi.fn(),
  updateProducerSupplyOpportunity: vi.fn(),
}));

const mockedCreateProducerSupplyLaunch = vi.mocked(createProducerSupplyLaunch);
const mockedGetAdminSponsorWallets = vi.mocked(getAdminSponsorWallets);
const mockedGetSponsorExperience = vi.mocked(getSponsorExperience);
const mockedGetSponsorPortalContractLedger = vi.mocked(getSponsorPortalContractLedger);
const mockedGetSponsorPortalStatement = vi.mocked(getSponsorPortalStatement);
const mockedGetSponsorPortalWalletLedger = vi.mocked(getSponsorPortalWalletLedger);
const mockedPublishProducerSupplyOpportunity = vi.mocked(publishProducerSupplyOpportunity);
const mockedUpdateProducerSupplyOpportunity = vi.mocked(updateProducerSupplyOpportunity);

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

function field(container: HTMLElement, selector: string) {
  const element = container.querySelector(selector);
  if (!element) {
    throw new Error(`${selector} was not rendered`);
  }
  return element as HTMLInputElement;
}

function panel(container: HTMLElement, selector: string) {
  const element = container.querySelector(selector);
  if (!element) {
    throw new Error(`${selector} was not rendered`);
  }
  return within(element as HTMLElement);
}

function mockSponsorData() {
  mockedGetAdminSponsorWallets.mockResolvedValue([
    {
      sponsor_code: "SPONSOR-1",
      sponsor_name: "FNB Rewards",
      available_balance: "75000.00",
    },
  ]);
  mockedGetSponsorExperience.mockResolvedValue({
    status: "ok",
    sections: {
      billing: {
        status: "ok",
        data: {
          invoice_count: 2,
          overdue_count: 1,
          totals: {
            total_amount: "4500.00",
            paid_amount: "1500.00",
            outstanding_amount: "3000.00",
            overdue_outstanding_amount: "750.00",
          },
        },
      },
      wallet: {
        status: "ok",
        data: {
          wallet_id: "WALLET-1",
          sponsor_code: "SPONSOR-1",
          sponsor_name: "FNB Rewards",
          currency: "ZAR",
          available_balance: "75000.00",
          held_balance: "5000.00",
          status: "ACTIVE",
        },
      },
      invoices: {
        status: "ok",
        data: [
          { invoice_id: "INV-1", period: "2026-06", total_amount: "3000.00", status: "OPEN" },
        ],
      },
      contracts: {
        status: "ok",
        data: [
          {
            contract_id: "CONTRACT-1",
            currency: "ZAR",
            status: "ACTIVE",
            committed_amount: "100000.00",
            remaining_amount: "80000.00",
          },
        ],
      },
      receipts: {
        status: "ok",
        data: [{ receipt_id: "RCPT-1", amount: "1500.00", status: "PAID" }],
      },
      forecast: {
        status: "ok",
        data: {
          forecast: {
            wallet: {
              forecast_status: "WARNING",
              days_remaining: 14,
              average_burn_rate_per_day: "1200.00",
              target_buffer: "25000.00",
            },
            contracts: {
              days_remaining: 60,
              average_burn_rate_per_day: "900.00",
            },
          },
        },
      },
      opportunities: {
        status: "ok",
        data: [
          {
            opportunity_id: "OPP-1",
            opportunity_code: "DRAFT-1",
            campaign_code: "CAMPAIGN-1",
            title: "Draft funeral cover",
            description: "Draft demand",
            opportunity_status: "DRAFT",
            total_budget: "10000.00",
            max_allocations: 100,
          },
        ],
      },
      performanceOverview: {
        status: "ok",
        data: {
          opportunities: { published_count: 0 },
          routes: { accepted_count: 2 },
          conversions: { completed_count: 1 },
        },
      },
      opportunityPerformance: {
        status: "ok",
        data: [{ opportunity_id: "OPP-1", accepted_count: 0, conversion_count: 0 }],
      },
      conversions: {
        status: "ok",
        data: { items: [], count: 0, completed_count: 0, completion_rate: "0.0000" },
      },
      outcomeMoney: { status: "ok", data: { items: [] } },
      proof: { status: "ok", data: { steps: [] } },
      channels: {
        status: "ok",
        data: {
          readiness: { status: "READY", summary: { ready_count: 2, count: 2, supported_channels: ["WHATSAPP", "SMS"] } },
          recommendations: {
            top_channel: {
              channel_code: "WHATSAPP",
              recommendation_score: "0.92",
              recommended_action: "Use WhatsApp first",
            },
          },
        },
      },
    },
  });
  mockedGetSponsorPortalWalletLedger.mockResolvedValue([
    {
      transaction_type: "CREDIT",
      amount: "1500.00",
      balance_before: "73500.00",
      balance_after: "75000.00",
      correlation_id: "RCPT-1",
      created_at: "2026-06-18T08:00:00Z",
    },
  ]);
  mockedGetSponsorPortalContractLedger.mockResolvedValue([
    { ledger_id: "LEDGER-1", movement_type: "COMMIT", amount: "10000.00" },
  ]);
  mockedGetSponsorPortalStatement.mockResolvedValue({
    period_start: "2026-06-01",
    period_end: "2026-06-18",
    totals: { invoice_total: "3000.00", payment_total: "1500.00", outstanding_amount: "1500.00" },
  });
  mockedCreateProducerSupplyLaunch.mockResolvedValue({
    launch_id: "LAUNCH-1",
    opportunity: {
      opportunity_id: "OPP-2",
      title: "Youth account activation",
      opportunity_status: "PUBLISHED",
      total_budget: "25000.00",
    },
  });
  mockedUpdateProducerSupplyOpportunity.mockResolvedValue({
    opportunity_id: "OPP-1",
    title: "Updated funeral cover",
    opportunity_status: "DRAFT",
    total_budget: "12000.00",
  });
  mockedPublishProducerSupplyOpportunity.mockResolvedValue({
    opportunity_id: "OPP-1",
    title: "Updated funeral cover",
    opportunity_status: "PUBLISHED",
    total_budget: "12000.00",
  });
}

describe("SponsorPortalPage", () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem("amplifi.sponsorPortal.tenant", "FNB");
    localStorage.setItem("amplifi.sponsorPortal.sponsor", "SPONSOR-1");
    mockSponsorData();
  });

  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("loads sponsor billing and forecast panels from the experience aggregate", async () => {
    const { container } = renderWorkspace(<SponsorPortalPage mode="operations" />);

    expect(await screen.findByRole("heading", { name: "Organisation Workspace" })).toBeInTheDocument();
    expect(panel(container, "#sponsor-billing").getByText("Billing position")).toBeInTheDocument();
    expect(panel(container, "#sponsor-performance").getByText("Funding forecast")).toBeInTheDocument();
    expect(panel(container, "#sponsor-funding").getByText("Wallet position")).toBeInTheDocument();
    expect(screen.getByText("Review overdue billing")).toBeInTheDocument();
    expect(mockedGetSponsorExperience).toHaveBeenCalledWith("FNB", "SPONSOR-1", "ZAR");
  });

  it("loads a billing statement for the selected period and currency", async () => {
    const { container } = renderWorkspace(<SponsorPortalPage mode="operations" />);

    await screen.findByRole("heading", { name: "Organisation Workspace" });

    fireEvent.change(field(container, "#portal-statement-start"), { target: { value: "2026-06-01" } });
    fireEvent.change(field(container, "#portal-statement-end"), { target: { value: "2026-06-18" } });
    fireEvent.change(field(container, "#portal-currency"), { target: { value: "ZAR" } });
    fireEvent.click(panel(container, "#sponsor-statement").getByRole("button", { name: /^load statement$/i }));

    await waitFor(() => {
      expect(mockedGetSponsorPortalStatement).toHaveBeenCalledWith(
        "FNB",
        "SPONSOR-1",
        "2026-06-01",
        "2026-06-18",
        "ZAR",
      );
    });
  });

  it("creates supply, edits a draft, and publishes producer demand", async () => {
    const { container } = renderWorkspace(<SponsorPortalPage mode="operations" />);

    await screen.findByRole("heading", { name: "Organisation Workspace" });

    fireEvent.change(field(container, "#supply-campaign-name"), { target: { value: "Youth account activation" } });
    fireEvent.change(field(container, "#supply-opportunity-title"), { target: { value: "Youth account activation" } });
    fireEvent.change(field(container, "#supply-budget"), { target: { value: "25000.00" } });
    fireEvent.click(screen.getByRole("checkbox", { name: /publish to the demand marketplace/i }));
    fireEvent.click(screen.getByRole("button", { name: /^create and publish$/i }));

    await waitFor(() => {
      expect(mockedCreateProducerSupplyLaunch).toHaveBeenCalledWith(
        "FNB",
        "SPONSOR-1",
        expect.objectContaining({
          campaign_name: "Youth account activation",
          opportunity_title: "Youth account activation",
          total_budget: "25000.00",
          funding_contract_id: "CONTRACT-1",
          publish_now: true,
        }),
      );
    });

    fireEvent.click(screen.getByRole("button", { name: /^edit$/i }));
    expect(await screen.findByText("Edit draft")).toBeInTheDocument();
    fireEvent.change(field(container, "#draft-title"), { target: { value: "Updated funeral cover" } });
    fireEvent.change(field(container, "#draft-budget"), { target: { value: "12000.00" } });
    fireEvent.click(screen.getByRole("button", { name: /^save draft$/i }));

    await waitFor(() => {
      expect(mockedUpdateProducerSupplyOpportunity).toHaveBeenCalledWith(
        "FNB",
        "SPONSOR-1",
        "OPP-1",
        expect.objectContaining({ title: "Updated funeral cover", total_budget: "12000.00" }),
      );
    });

    fireEvent.click(screen.getByRole("button", { name: /^publish$/i }));
    await waitFor(() => expect(mockedPublishProducerSupplyOpportunity).toHaveBeenCalledWith("FNB", "SPONSOR-1", "OPP-1"));
  });
});
