import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import type { ReactElement } from "react";
import { createMemoryRouter, Outlet, RouterProvider } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  getReferralSaasReport,
  previewReferralSaasReportExport,
} from "../../api/endpoints/referralSaasReports";
import { ReferralSaasReportsPage } from "./ReferralSaasReportsPage";

vi.mock("../../api/endpoints/referralSaasReports", () => ({
  getReferralSaasReport: vi.fn(),
  previewReferralSaasReportExport: vi.fn(),
}));

const mockedGetReferralSaasReport = vi.mocked(getReferralSaasReport);
const mockedPreviewReferralSaasReportExport = vi.mocked(previewReferralSaasReportExport);

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

function mockExportPreview(format = "json") {
  mockedPreviewReferralSaasReportExport.mockResolvedValue({
    status: "ok",
    guardrail: "Inline export preview only; no persisted export is created.",
    account_scope: {
      source: "explicit_tenant_code",
      account_ref: "acct_fnb_referrals",
      external_tenant_ref: "org_fnb_referrals",
    },
    export_preview: {
      preview: {
        status: "PREVIEW_READY",
        export_format: format,
        content_type: format === "csv" ? "text/csv" : "application/json",
        metadata: {
          row_count: 1,
          redactions: ["raw_ucn"],
        },
        payload:
          format === "csv"
            ? "metric_name,value\nconversion.attribution_rate,0.9"
            : JSON.stringify([{ metric_name: "conversion.attribution_rate", value: 0.9 }], null, 2),
      },
      creation_status: "NOT_IMPLEMENTED",
      storage_status: "NOT_IMPLEMENTED",
      delivery_status: "NOT_IMPLEMENTED",
      audit_status: "NOT_IMPLEMENTED",
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
    mockExportPreview();
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
    expect(screen.getByText(/Export storage, download URLs, and audit rows remain future work/i)).toBeInTheDocument();
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

  it("previews JSON exports inline without enabling persisted exports", async () => {
    renderWorkspace(<ReferralSaasReportsPage />);

    await screen.findAllByText("conversion.attribution_rate");
    fireEvent.click(screen.getByRole("button", { name: "Preview JSON" }));

    await waitFor(() =>
      expect(mockedPreviewReferralSaasReportExport).toHaveBeenCalledWith({
        reportType: "campaign_performance",
        tenantCode: "FNB",
        format: "json",
        redactionProfile: "tenant_safe",
        rowLimit: 10,
      }),
    );
    expect(await screen.findByText("PREVIEW_READY")).toBeInTheDocument();
    expect(screen.getByText("application/json")).toBeInTheDocument();
    expect(screen.getByLabelText("Export preview payload")).toHaveTextContent(
      "conversion.attribution_rate",
    );
    expect(JSON.stringify(mockedPreviewReferralSaasReportExport.mock.calls)).not.toMatch(
      /account_ref|external_tenant_ref/i,
    );
    expect(screen.queryByText(/export id/i)).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /^download$/i })).not.toBeInTheDocument();
    expect(screen.queryByText(/scheduled export/i)).not.toBeInTheDocument();
  });

  it("previews CSV exports with the selected row limit", async () => {
    mockExportPreview("csv");
    renderWorkspace(<ReferralSaasReportsPage />);

    await screen.findAllByText("conversion.attribution_rate");
    fireEvent.change(screen.getByLabelText("Preview row limit"), { target: { value: "25" } });
    fireEvent.click(screen.getByRole("button", { name: "Preview CSV" }));

    await waitFor(() =>
      expect(mockedPreviewReferralSaasReportExport).toHaveBeenCalledWith({
        reportType: "campaign_performance",
        tenantCode: "FNB",
        format: "csv",
        redactionProfile: "tenant_safe",
        rowLimit: 25,
      }),
    );
    expect(await screen.findByText("text/csv")).toBeInTheDocument();
  });
});
