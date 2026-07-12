import { apiRequest } from "../client";

export type ReferralSaasReportType =
  | "campaign_performance"
  | "referral_funnel"
  | "link_code_performance"
  | "progress_event_health"
  | "attribution_quality"
  | "safe_status_distribution"
  | "reward_visibility_summary";

export type ReferralSaasExportFormat = "json" | "csv";

export type ReferralSaasReportRequest = {
  reportType: ReferralSaasReportType;
  tenantCode?: string;
  dimensions?: string[];
  filters?: Record<string, string | number | boolean | undefined | null>;
  dataWindowStart?: string;
  dataWindowEnd?: string;
};

export type ReferralSaasExportRequest = ReferralSaasReportRequest & {
  format?: ReferralSaasExportFormat;
  redactionProfile?: "tenant_safe";
  rowLimit?: number;
};

export type ReferralSaasAccountScope = {
  source?: string;
  account_ref?: string | null;
  external_tenant_ref?: string | null;
};

export type ReferralSaasReportResponse = {
  status?: string;
  report?: Record<string, unknown>;
  account_scope?: ReferralSaasAccountScope;
  guardrail?: string;
};

export type ReferralSaasExportValidationResponse = {
  status?: string;
  export_request?: Record<string, unknown>;
  account_scope?: ReferralSaasAccountScope;
  guardrail?: string;
};

export type ReferralSaasExportPreviewResponse = {
  status?: string;
  export_preview?: Record<string, unknown>;
  account_scope?: ReferralSaasAccountScope;
  guardrail?: string;
};

function reportPath(reportType: ReferralSaasReportType, suffix = ""): string {
  return `v1/referral-saas/reports/${encodeURIComponent(reportType)}${suffix}`;
}

function reportQuery(request: ReferralSaasReportRequest) {
  return {
    tenant_code: request.tenantCode,
    dimensions: request.dimensions,
    data_window_start: request.dataWindowStart,
    data_window_end: request.dataWindowEnd,
    ...request.filters,
  };
}

function exportBody(request: ReferralSaasExportRequest) {
  return {
    format: request.format,
    redaction_profile: request.redactionProfile,
    dimensions: request.dimensions,
    filters: request.filters,
    row_limit: request.rowLimit,
    data_window_start: request.dataWindowStart,
    data_window_end: request.dataWindowEnd,
  };
}

export function getReferralSaasReport(request: ReferralSaasReportRequest): Promise<ReferralSaasReportResponse> {
  return apiRequest<ReferralSaasReportResponse>(reportPath(request.reportType), {
    query: reportQuery(request),
  });
}

export function validateReferralSaasReportExport(
  request: ReferralSaasExportRequest,
): Promise<ReferralSaasExportValidationResponse> {
  return apiRequest<ReferralSaasExportValidationResponse>(reportPath(request.reportType, "/exports/validate"), {
    method: "POST",
    query: { tenant_code: request.tenantCode },
    body: exportBody(request),
  });
}

export function previewReferralSaasReportExport(
  request: ReferralSaasExportRequest,
): Promise<ReferralSaasExportPreviewResponse> {
  return apiRequest<ReferralSaasExportPreviewResponse>(reportPath(request.reportType, "/exports/preview"), {
    method: "POST",
    query: { tenant_code: request.tenantCode },
    body: exportBody(request),
  });
}
