import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import type { ReactElement } from "react";
import { createMemoryRouter, Outlet, RouterProvider } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { getReferralSaasReport } from "../../api/endpoints/referralSaasReports";
import { ReferralSaasReportsPage } from "./ReferralSaasReportsPage";

vi.mock("../../api/endpoints/referralSaasReports", () => ({
  getReferralSaasReport: vi.fn(),
}));

const mockedGetReferralSaasReport = vi.mocked(getReferralSaasReport);

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

function mockReport(reportType = "campaign_performance") {
  mockedGetReferralSaasReport.mockResolvedValue({
    status: "ok",
    guardrail: "Read-only Referral SaaS report wrapper; does not create exports.",
    account_scope: {
      source: "explicit_tenant_code",
      account_ref: "acct_fnb_referrals",
      external_tenant_ref: "org_fnb_referrals",
    },
    report: {
      report_type: reportType,
      source_report_type: "distribution_overview",
      catalog_status: "AVAILABLE",
      export_status: "NOT_IMPLEMENTED",
      freshness: { status: "FRESH", sources: [] },
      source_warnings: [
        {
          code: "PARTIAL_SOURCE_COVERAGE",
          severity: "WARNING",
          message: "Some report sources are intentionally aggregate-only.",
        },
      ],
      redactions: ["raw_ucn"],
      metrics: [
        {
          name: "conversion.attribution_rate",
          value: 0.9,
          metric_class: "OPERATIONAL",
          dimensions: {
            campaign_code: "CAMP001",
            metric_name: "conversion.attribution_rate",
          },
        },
      ],
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

describe("ReferralSaasReportsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockReport();
  });

  afterEach(() => {
    cleanup();
  });

  it("renders tenant-safe report metrics, warnings, and redactions", async () => {
    renderWorkspace(<ReferralSaasReportsPage />);

    expect(await screen.findByRole("heading", { name: "Tenant-safe reporting" })).toBeInTheDocument();
    expect(mockedGetReferralSaasReport).toHaveBeenCalledWith({
      reportType: "campaign_performance",
      tenantCode: "FNB",
    });
    expect(await screen.findAllByText("conversion.attribution_rate")).not.toHaveLength(0);
    expect(screen.getByText("PARTIAL_SOURCE_COVERAGE")).toBeInTheDocument();
    expect(screen.getByText("raw_ucn")).toBeInTheDocument();
    expect(screen.getByText("NOT_IMPLEMENTED")).toBeInTheDocument();
    expect(screen.getByText(/does not create persisted exports/i)).toBeInTheDocument();
    expect(screen.queryByText("raw_customer_identifier")).not.toBeInTheDocument();
  });

  it("switches report types through the catalog selector", async () => {
    renderWorkspace(<ReferralSaasReportsPage />);

    await screen.findByRole("heading", { name: "Tenant-safe reporting" });
    fireEvent.click(screen.getByRole("button", { name: "Attribution" }));

    await waitFor(() =>
      expect(mockedGetReferralSaasReport).toHaveBeenLastCalledWith({
        reportType: "attribution_quality",
        tenantCode: "FNB",
      }),
    );
  });

  it("keeps account references display-only and never sends them in report requests", async () => {
    renderWorkspace(<ReferralSaasReportsPage />);

    await screen.findAllByText("conversion.attribution_rate");
    const posturePanel = panelByHeading("Report posture");

    expect(posturePanel.getByText("explicit_tenant_code")).toBeInTheDocument();
    expect(JSON.stringify(mockedGetReferralSaasReport.mock.calls)).not.toMatch(
      /account_ref|external_tenant_ref/i,
    );
  });
});
