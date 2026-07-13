import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import type { ReactElement } from "react";
import { createMemoryRouter, Outlet, RouterProvider } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { getAdminCampaignReadiness } from "../../api/endpoints/adminCampaignReadiness";
import { ReferralSaasCampaignReadinessPage } from "./ReferralSaasCampaignReadinessPage";

vi.mock("../../api/endpoints/adminCampaignReadiness", () => ({
  getAdminCampaignReadiness: vi.fn(),
}));

const mockedGetAdminCampaignReadiness = vi.mocked(getAdminCampaignReadiness);

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

function mockReadiness() {
  mockedGetAdminCampaignReadiness.mockResolvedValue({
    status: "ok",
    guardrail:
      "Read-only admin campaign readiness. This endpoint does not mutate campaigns.",
    readiness: {
      tenant_code: "FNB",
      campaign_code: "CAMP001",
      operation: "CONTROL_PLANE_VIEW",
      canonical_lifecycle: "ACTIVE",
      readiness: "READY_WITH_WARNINGS",
      can_proceed: true,
      evaluated_at: "2026-07-13T05:00:00Z",
      blockers: [],
      warnings: [
        {
          code: "NO_ACTIVE_POLICY",
          severity: "WARNING",
          source: "marketing_campaign_policies",
          message: "No active effective campaign policy was found.",
        },
      ],
      unknowns: [],
      evidence: {
        campaign: {
          campaign_code: "CAMP001",
          tenant_code: "FNB",
          segment: "Retail",
          name: "Referral launch",
          is_active: true,
          uses_count: 3,
        },
        policy: {
          campaign_code: "CAMP001",
          version: 2,
          is_active: true,
          rolling_window_days: 60,
        },
        links: {},
      },
    },
  });
}

function panelByHeading(heading: string) {
  const headingElement = screen.getByRole("heading", { name: heading });
  const panel = headingElement.closest(".panel");
  if (!panel) {
    throw new Error(`${heading} panel was not rendered`);
  }
  return within(panel as HTMLElement);
}

describe("ReferralSaasCampaignReadinessPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockReadiness();
  });

  afterEach(() => {
    cleanup();
  });

  it("renders campaign readiness from the existing read-only service", async () => {
    renderWorkspace(<ReferralSaasCampaignReadinessPage />);

    expect(await screen.findByRole("heading", { name: "Campaign readiness" })).toBeInTheDocument();
    expect(mockedGetAdminCampaignReadiness).toHaveBeenCalledWith({
      campaignCode: "CAMP001",
      tenantCode: "FNB",
      operation: "CONTROL_PLANE_VIEW",
      opportunityId: "",
      includeEvidence: true,
    });
    expect(await screen.findAllByText("READY_WITH_WARNINGS")).not.toHaveLength(0);
    expect(screen.getByText("ACTIVE")).toBeInTheDocument();
    expect(screen.getByText("Can proceed")).toBeInTheDocument();
    expect(screen.getByText("NO_ACTIVE_POLICY")).toBeInTheDocument();
    expect(screen.getByText("No campaign mutation")).toBeInTheDocument();
    expect(screen.getByText("No marketplace or money expansion")).toBeInTheDocument();
  });

  it("switches operation and carries only current campaign readiness scope", async () => {
    renderWorkspace(<ReferralSaasCampaignReadinessPage />);

    await screen.findByRole("heading", { name: "Campaign readiness" });
    fireEvent.click(screen.getByRole("button", { name: "Links" }));

    await waitFor(() =>
      expect(mockedGetAdminCampaignReadiness).toHaveBeenLastCalledWith({
        campaignCode: "CAMP001",
        tenantCode: "FNB",
        operation: "GENERATE_LINKS",
        opportunityId: "",
        includeEvidence: true,
      }),
    );
    expect(JSON.stringify(mockedGetAdminCampaignReadiness.mock.calls)).not.toMatch(
      /account_ref|external_tenant_ref/i,
    );
  });

  it("redacts tenant evidence from rendered campaign and policy evidence", async () => {
    renderWorkspace(<ReferralSaasCampaignReadinessPage />);

    await screen.findByText("Can proceed");
    const campaignEvidence = panelByHeading("Campaign evidence");

    expect(campaignEvidence.getByText("campaign_code")).toBeInTheDocument();
    expect(campaignEvidence.getByText("Referral launch")).toBeInTheDocument();
    expect(campaignEvidence.queryByText("tenant_code")).not.toBeInTheDocument();
  });

  it("updates scope inputs without exposing product account refs or mutation controls", async () => {
    renderWorkspace(<ReferralSaasCampaignReadinessPage />);

    await screen.findByRole("heading", { name: "Campaign readiness" });
    fireEvent.change(screen.getByLabelText("Campaign code"), { target: { value: "camp002" } });
    fireEvent.change(screen.getByLabelText("Tenant code bridge"), { target: { value: "absa" } });
    fireEvent.change(screen.getByLabelText("Opportunity ID"), { target: { value: "opp-123" } });

    await waitFor(() =>
      expect(mockedGetAdminCampaignReadiness).toHaveBeenLastCalledWith({
        campaignCode: "CAMP002",
        tenantCode: "ABSA",
        operation: "CONTROL_PLANE_VIEW",
        opportunityId: "opp-123",
        includeEvidence: true,
      }),
    );
    expect(screen.queryByRole("button", { name: /^activate campaign$/i })).not.toBeInTheDocument();
    expect(screen.queryByText(/account_ref/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/external_tenant_ref/i)).not.toBeInTheDocument();
  });

  it("links into the existing setup and reporting workflow", async () => {
    renderWorkspace(<ReferralSaasCampaignReadinessPage />);

    await screen.findByText("Can proceed");
    expect(screen.getByRole("link", { name: /Account setup readiness/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/account-setup",
    );
    expect(screen.getByRole("link", { name: /Referral SaaS reports/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/reports",
    );
  });
});
