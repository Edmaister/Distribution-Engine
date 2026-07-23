import { afterEach, describe, expect, it, vi } from "vitest";

import {
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
});
