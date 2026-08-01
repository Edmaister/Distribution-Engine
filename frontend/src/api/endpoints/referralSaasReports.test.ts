import { afterEach, describe, expect, it, vi } from "vitest";

import {
  createReferralSaasAccountReportExportFile,
  createReferralSaasAccountReportExportRequest,
  downloadReferralSaasAccountReportExportFile,
  getReferralSaasAccountReportExportFileMetadata,
  getReferralSaasAccountReport,
  getReferralSaasReport,
  previewReferralSaasAccountReportExport,
  previewReferralSaasReportExport,
  validateReferralSaasAccountReportExport,
  validateReferralSaasReportExport,
} from "./referralSaasReports";

describe("referral SaaS reports api", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

  it("requests a tenant-scoped report with repeated dimensions and safe filters", async () => {
    localStorage.setItem("amplifi.apiBaseUrl", "https://api.example.test");
    localStorage.setItem("amplifi.apiKey", "report-key");
    const fetchMock = vi.fn(async () => {
      return new Response(JSON.stringify({ status: "ok", report: {} }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    });
    vi.stubGlobal("fetch", fetchMock);

    await getReferralSaasReport({
      reportType: "campaign_performance",
      tenantCode: "FNB",
      dimensions: ["campaign_ref", "metric_name"],
      filters: { campaign_code: "CAMP001", sponsor_code: "BOXER" },
      dataWindowStart: "2026-07-01T00:00:00Z",
      dataWindowEnd: "2026-07-12T00:00:00Z",
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, options] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    const requestUrl = new URL(url);

    expect(requestUrl.origin).toBe("https://api.example.test");
    expect(requestUrl.pathname).toBe("/v1/referral-saas/reports/campaign_performance");
    expect(requestUrl.searchParams.get("tenant_code")).toBe("FNB");
    expect(requestUrl.searchParams.getAll("dimensions")).toEqual(["campaign_ref", "metric_name"]);
    expect(requestUrl.searchParams.get("campaign_code")).toBe("CAMP001");
    expect(requestUrl.searchParams.get("sponsor_code")).toBe("BOXER");
    expect(requestUrl.searchParams.get("data_window_start")).toBe("2026-07-01T00:00:00Z");
    expect(requestUrl.searchParams.get("data_window_end")).toBe("2026-07-12T00:00:00Z");
    expect(options.method).toBe("GET");
    expect(options.headers).toMatchObject({ "x-api-key": "report-key" });
  });

  it("validates an export request with report filters in the body", async () => {
    localStorage.setItem("amplifi.apiBaseUrl", "https://api.example.test");
    const fetchMock = vi.fn(async () => {
      return new Response(JSON.stringify({ status: "ok", export_request: {} }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    });
    vi.stubGlobal("fetch", fetchMock);

    await validateReferralSaasReportExport({
      reportType: "link_code_performance",
      tenantCode: "FNB",
      format: "csv",
      redactionProfile: "tenant_safe",
      dimensions: ["source_type", "metric_name"],
      filters: { campaign_ref: "CAMP001", source_type: "ROUTE_REFERRAL_LINK" },
      rowLimit: 250,
    });

    const [url, options] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    const requestUrl = new URL(url);

    expect(requestUrl.pathname).toBe("/v1/referral-saas/reports/link_code_performance/exports/validate");
    expect(requestUrl.searchParams.get("tenant_code")).toBe("FNB");
    expect(options.method).toBe("POST");
    expect(JSON.parse(String(options.body))).toEqual({
      format: "csv",
      redaction_profile: "tenant_safe",
      dimensions: ["source_type", "metric_name"],
      filters: { campaign_ref: "CAMP001", source_type: "ROUTE_REFERRAL_LINK" },
      row_limit: 250,
    });
  });

  it("previews an export without accepting caller supplied account refs", async () => {
    localStorage.setItem("amplifi.apiBaseUrl", "https://api.example.test");
    const fetchMock = vi.fn(async () => {
      return new Response(JSON.stringify({ status: "ok", export_preview: {} }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    });
    vi.stubGlobal("fetch", fetchMock);

    await previewReferralSaasReportExport({
      reportType: "attribution_quality",
      tenantCode: "FNB",
      format: "json",
      redactionProfile: "tenant_safe",
      filters: {
        campaign_code: "CAMP001",
      },
      rowLimit: 10,
    });

    const [url, options] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    const requestUrl = new URL(url);
    const body = JSON.parse(String(options.body));

    expect(requestUrl.pathname).toBe("/v1/referral-saas/reports/attribution_quality/exports/preview");
    expect(requestUrl.searchParams.get("tenant_code")).toBe("FNB");
    expect(options.method).toBe("POST");
    expect(body).toEqual({
      format: "json",
      redaction_profile: "tenant_safe",
      filters: { campaign_code: "CAMP001" },
      row_limit: 10,
    });
    expect(JSON.stringify(body)).not.toMatch(/account_ref|external_tenant_ref/i);
  });

  it("requests a selected-customer report without tenant code", async () => {
    localStorage.setItem("amplifi.apiBaseUrl", "https://api.example.test");
    const fetchMock = vi.fn(async () => {
      return new Response(JSON.stringify({ status: "ok", report: {} }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    });
    vi.stubGlobal("fetch", fetchMock);

    await getReferralSaasAccountReport({
      accountRef: "acct-fnb",
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: "fnb-platform",
        context: "setup",
      },
      reportType: "campaign_performance",
      dimensions: ["campaign_code", "metric_name"],
      filters: { campaign_code: "CAMP001" },
    });

    const [url, options] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    const requestUrl = new URL(url);

    expect(requestUrl.pathname).toBe("/v1/referral-saas/accounts/acct-fnb/reports/campaign_performance");
    expect(requestUrl.searchParams.get("ref_type")).toBe("external_tenant_ref");
    expect(requestUrl.searchParams.get("external_ref")).toBe("fnb-platform");
    expect(requestUrl.searchParams.get("context")).toBe("setup");
    expect(requestUrl.searchParams.get("campaign_code")).toBe("CAMP001");
    expect(requestUrl.searchParams.get("tenant_code")).toBeNull();
    expect(options.method).toBe("GET");
  });

  it("validates and previews selected-customer exports without tenant code", async () => {
    localStorage.setItem("amplifi.apiBaseUrl", "https://api.example.test");
    const fetchMock = vi.fn(async () => {
      return new Response(JSON.stringify({ status: "ok", export_preview: {} }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    });
    vi.stubGlobal("fetch", fetchMock);
    const request = {
      accountRef: "acct-fnb",
      accountScope: {
        refType: "external_tenant_ref" as const,
        externalRef: "fnb-platform",
        context: "setup" as const,
      },
      reportType: "link_code_performance" as const,
      format: "csv" as const,
      redactionProfile: "tenant_safe" as const,
      filters: { campaign_code: "CAMP001" },
      rowLimit: 50,
    };

    await validateReferralSaasAccountReportExport(request);
    await previewReferralSaasAccountReportExport(request);

    for (const [url, options] of fetchMock.mock.calls as unknown as [string, RequestInit][]) {
      const requestUrl = new URL(url);
      const body = JSON.parse(String(options.body));

      expect(requestUrl.pathname).toMatch(
        /^\/v1\/referral-saas\/accounts\/acct-fnb\/reports\/link_code_performance\/exports\/(validate|preview)$/,
      );
      expect(requestUrl.searchParams.get("ref_type")).toBe("external_tenant_ref");
      expect(requestUrl.searchParams.get("external_ref")).toBe("fnb-platform");
      expect(requestUrl.searchParams.get("tenant_code")).toBeNull();
      expect(body).toEqual({
        format: "csv",
        redaction_profile: "tenant_safe",
        filters: { campaign_code: "CAMP001" },
        row_limit: 50,
      });
      expect(JSON.stringify(body)).not.toMatch(/tenant_code|account_ref|external_tenant_ref/i);
    }
  });

  it("creates a selected-customer export request without caller supplied tenant code", async () => {
    localStorage.setItem("amplifi.apiBaseUrl", "https://api.example.test");
    const fetchMock = vi.fn(async () => {
      return new Response(JSON.stringify({ status: "accepted", reportExport: {} }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    });
    vi.stubGlobal("fetch", fetchMock);

    await createReferralSaasAccountReportExportRequest({
      accountRef: "acct-fnb",
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: "fnb-platform",
        context: "setup",
      },
      reportType: "campaign_performance",
      format: "csv",
      redactionProfile: "tenant_safe",
      filters: { campaign_code: "CAMP001" },
      rowLimit: 100,
      correlationId: "report-export-acct-fnb-campaign-performance",
      idempotencyKey: "report-export-acct-fnb-campaign-performance-csv",
    });

    const [url, options] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    const requestUrl = new URL(url);
    const body = JSON.parse(String(options.body));

    expect(requestUrl.pathname).toBe("/v1/referral-saas/accounts/acct-fnb/reports/campaign_performance/exports");
    expect(requestUrl.searchParams.get("tenant_code")).toBeNull();
    expect(options.method).toBe("POST");
    expect(body).toEqual({
      format: "csv",
      redaction_profile: "tenant_safe",
      filters: { campaign_code: "CAMP001" },
      row_limit: 100,
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: "fnb-platform",
        context: "setup",
      },
      correlationId: "report-export-acct-fnb-campaign-performance",
      idempotencyKey: "report-export-acct-fnb-campaign-performance-csv",
    });
    expect(JSON.stringify(body)).not.toMatch(/tenant_code|downloadUrl|scheduledDelivery|billing|money/i);
  });

  it("creates and downloads a selected-customer export file through customer-scoped routes", async () => {
    localStorage.setItem("amplifi.apiBaseUrl", "https://api.example.test");
    const fetchMock = vi.fn(async () => {
      return new Response(JSON.stringify({ status: "ok", reportExport: {} }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    });
    vi.stubGlobal("fetch", fetchMock);
    const accountScope = {
      refType: "external_tenant_ref" as const,
      externalRef: "fnb-platform",
      context: "setup" as const,
    };

    await createReferralSaasAccountReportExportFile({
      accountRef: "acct-fnb",
      accountScope,
      reportType: "campaign_performance",
      exportRequestId: "export-1",
      correlationId: "report-export-file-acct-fnb",
      idempotencyKey: "report-export-file-acct-fnb-export-1",
    });
    await getReferralSaasAccountReportExportFileMetadata({
      accountRef: "acct-fnb",
      accountScope,
      exportRequestId: "export-1",
    });
    await downloadReferralSaasAccountReportExportFile({
      accountRef: "acct-fnb",
      accountScope,
      exportRequestId: "export-1",
      correlationId: "report-export-download-acct-fnb",
    });

    const calls = fetchMock.mock.calls as unknown as Array<[string, RequestInit]>;
    const [createUrl, createOptions] = calls[0];
    const createBody = JSON.parse(String(createOptions.body));
    const metadataUrl = new URL(String(calls[1][0]));
    const downloadUrl = new URL(String(calls[2][0]));

    expect(new URL(createUrl).pathname).toBe(
      "/v1/referral-saas/accounts/acct-fnb/reports/campaign_performance/exports/export-1/file",
    );
    expect(createOptions.method).toBe("POST");
    expect(createBody.accountScope).toEqual(accountScope);
    expect(JSON.stringify(createBody)).not.toMatch(/tenant_code|downloadUrl|credential|money/i);
    expect(metadataUrl.pathname).toBe("/v1/referral-saas/accounts/acct-fnb/exports/export-1");
    expect(metadataUrl.searchParams.get("ref_type")).toBe("external_tenant_ref");
    expect(metadataUrl.searchParams.get("external_ref")).toBe("fnb-platform");
    expect(downloadUrl.pathname).toBe("/v1/referral-saas/accounts/acct-fnb/exports/export-1/download");
    expect(downloadUrl.searchParams.get("correlation_id")).toBe("report-export-download-acct-fnb");
    expect(downloadUrl.searchParams.get("tenant_code")).toBeNull();
  });
});
