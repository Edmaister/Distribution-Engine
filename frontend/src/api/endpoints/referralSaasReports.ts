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

export type ReferralSaasCustomerAccountScopeRequest = {
  refType: "external_tenant_ref" | "organisation_ref";
  externalRef: string;
  context?: "setup" | "runtime";
};

export type ReferralSaasAccountReportRequest = Omit<ReferralSaasReportRequest, "tenantCode"> & {
  accountRef: string;
  accountScope: ReferralSaasCustomerAccountScopeRequest;
};

export type ReferralSaasAccountExportRequest = Omit<ReferralSaasExportRequest, "tenantCode"> & {
  accountRef: string;
  accountScope: ReferralSaasCustomerAccountScopeRequest;
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

export type ReferralSaasExportFileResponse = {
  status?: string;
  reportExport?: Record<string, unknown>;
  account_scope?: ReferralSaasAccountScope;
  guardrail?: string;
  no_download_url_created_confirmed?: boolean;
  no_scheduled_delivery_created_confirmed?: boolean;
  no_tenant_code_exposure_confirmed?: boolean;
  no_billing_or_money_movement_confirmed?: boolean;
};

export type ReferralSaasAccountExportFileRequest = ReferralSaasAccountExportRequest & {
  correlationId: string;
  idempotencyKey: string;
  reasonCode?: string;
};

export type ReferralSaasAccountExportFileCreateRequest = {
  accountRef: string;
  accountScope: ReferralSaasCustomerAccountScopeRequest;
  reportType: ReferralSaasReportType;
  exportRequestId: string;
  correlationId: string;
  idempotencyKey: string;
  reasonCode?: string;
};

export type ReferralSaasAccountExportFileReadRequest = {
  accountRef: string;
  accountScope: ReferralSaasCustomerAccountScopeRequest;
  exportRequestId: string;
  correlationId?: string;
};

export type ReferralSaasReportDeliveryCadence = "daily" | "weekly" | "monthly";

export type ReferralSaasReportDeliveryScheduleStatus =
  | "draft"
  | "ready"
  | "paused"
  | "cancelled"
  | "blocked";

export type ReferralSaasAccountReportDeliveryScheduleRequest = {
  accountRef: string;
  accountScope: ReferralSaasCustomerAccountScopeRequest;
  reportType: ReferralSaasReportType;
  cadence: ReferralSaasReportDeliveryCadence;
  timezone: string;
  format?: ReferralSaasExportFormat;
  redactionProfile?: "tenant_safe";
  recipientContactRefs?: string[];
  retentionDays?: number;
  campaignRef?: string;
  scheduleStatus?: ReferralSaasReportDeliveryScheduleStatus;
  reasonCode?: string;
  correlationId: string;
  idempotencyKey: string;
};

export type ReferralSaasAccountReportDeliveryScheduleUpdateRequest = {
  accountRef: string;
  accountScope: ReferralSaasCustomerAccountScopeRequest;
  scheduleId: string;
  reportType?: ReferralSaasReportType;
  cadence?: ReferralSaasReportDeliveryCadence;
  timezone?: string;
  format?: ReferralSaasExportFormat;
  redactionProfile?: "tenant_safe";
  recipientContactRefs?: string[];
  retentionDays?: number;
  campaignRef?: string;
  scheduleStatus?: ReferralSaasReportDeliveryScheduleStatus;
  reasonCode?: string;
  correlationId: string;
  idempotencyKey: string;
};

export type ReferralSaasAccountReportDeliveryScheduleListRequest = {
  accountRef: string;
  accountScope: ReferralSaasCustomerAccountScopeRequest;
  reportType: ReferralSaasReportType;
};

export type ReferralSaasAccountReportDeliveryScheduleReadinessRequest = {
  accountRef: string;
  accountScope: ReferralSaasCustomerAccountScopeRequest;
  scheduleId: string;
};

export type ReferralSaasReportDeliveryScheduleResponse = {
  status?: string;
  reportDeliverySchedule?: Record<string, unknown>;
  deliverySchedules?: Record<string, unknown>[];
  reportDeliveryScheduleReadiness?: Record<string, unknown>;
  account_scope?: ReferralSaasAccountScope;
  guardrail?: string;
  guardrails?: string[];
  redactions?: string[];
  no_live_delivery_executed_confirmed?: boolean;
  no_email_sent_confirmed?: boolean;
  no_webhook_dispatch_confirmed?: boolean;
  no_credential_or_auth_change_confirmed?: boolean;
  no_campaign_activation_confirmed?: boolean;
  no_billing_or_money_movement_confirmed?: boolean;
};

function reportPath(reportType: ReferralSaasReportType, suffix = ""): string {
  return `v1/referral-saas/reports/${encodeURIComponent(reportType)}${suffix}`;
}

function accountReportPath(
  accountRef: string,
  reportType: ReferralSaasReportType,
  suffix = "",
): string {
  return `v1/referral-saas/accounts/${encodeURIComponent(accountRef)}/reports/${encodeURIComponent(reportType)}${suffix}`;
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

function accountScopeQuery(request: ReferralSaasAccountReportRequest | ReferralSaasAccountExportRequest) {
  return {
    ref_type: request.accountScope.refType,
    external_ref: request.accountScope.externalRef,
    context: request.accountScope.context || "setup",
  };
}

function accountReportQuery(request: ReferralSaasAccountReportRequest) {
  return {
    ...accountScopeQuery(request),
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

function exportRequestBody(request: ReferralSaasAccountExportFileRequest) {
  return {
    ...exportBody(request),
    accountScope: {
      refType: request.accountScope.refType,
      externalRef: request.accountScope.externalRef,
      context: request.accountScope.context || "setup",
    },
    correlationId: request.correlationId,
    idempotencyKey: request.idempotencyKey,
    reasonCode: request.reasonCode,
  };
}

function exportFileCommandBody(request: ReferralSaasAccountExportFileCreateRequest) {
  return {
    accountScope: {
      refType: request.accountScope.refType,
      externalRef: request.accountScope.externalRef,
      context: request.accountScope.context || "setup",
    },
    correlationId: request.correlationId,
    idempotencyKey: request.idempotencyKey,
    reasonCode: request.reasonCode,
  };
}

function exportFileQuery(request: ReferralSaasAccountExportFileReadRequest) {
  return {
    ref_type: request.accountScope.refType,
    external_ref: request.accountScope.externalRef,
    context: request.accountScope.context || "setup",
    correlation_id: request.correlationId,
  };
}

function deliveryScheduleBody(
  request:
    | ReferralSaasAccountReportDeliveryScheduleRequest
    | ReferralSaasAccountReportDeliveryScheduleUpdateRequest,
) {
  return {
    accountScope: {
      refType: request.accountScope.refType,
      externalRef: request.accountScope.externalRef,
      context: request.accountScope.context || "setup",
    },
    cadence: request.cadence,
    timezone: request.timezone,
    format: request.format,
    redactionProfile: request.redactionProfile,
    recipientContactRefs: request.recipientContactRefs,
    retentionDays: request.retentionDays,
    campaignRef: request.campaignRef,
    scheduleStatus: request.scheduleStatus,
    reasonCode: request.reasonCode,
    correlationId: request.correlationId,
    idempotencyKey: request.idempotencyKey,
  };
}

function deliveryScheduleQuery(
  request:
    | ReferralSaasAccountReportDeliveryScheduleListRequest
    | ReferralSaasAccountReportDeliveryScheduleReadinessRequest,
) {
  return {
    ref_type: request.accountScope.refType,
    external_ref: request.accountScope.externalRef,
    context: request.accountScope.context || "setup",
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

export function getReferralSaasAccountReport(
  request: ReferralSaasAccountReportRequest,
): Promise<ReferralSaasReportResponse> {
  return apiRequest<ReferralSaasReportResponse>(accountReportPath(request.accountRef, request.reportType), {
    query: accountReportQuery(request),
  });
}

export function validateReferralSaasAccountReportExport(
  request: ReferralSaasAccountExportRequest,
): Promise<ReferralSaasExportValidationResponse> {
  return apiRequest<ReferralSaasExportValidationResponse>(
    accountReportPath(request.accountRef, request.reportType, "/exports/validate"),
    {
      method: "POST",
      query: accountScopeQuery(request),
      body: exportBody(request),
    },
  );
}

export function previewReferralSaasAccountReportExport(
  request: ReferralSaasAccountExportRequest,
): Promise<ReferralSaasExportPreviewResponse> {
  return apiRequest<ReferralSaasExportPreviewResponse>(
    accountReportPath(request.accountRef, request.reportType, "/exports/preview"),
    {
      method: "POST",
      query: accountScopeQuery(request),
      body: exportBody(request),
    },
  );
}

export function createReferralSaasAccountReportExportRequest(
  request: ReferralSaasAccountExportFileRequest,
): Promise<ReferralSaasExportFileResponse> {
  return apiRequest<ReferralSaasExportFileResponse>(
    accountReportPath(request.accountRef, request.reportType, "/exports"),
    {
      method: "POST",
      body: exportRequestBody(request),
    },
  );
}

export function createReferralSaasAccountReportExportFile(
  request: ReferralSaasAccountExportFileCreateRequest,
): Promise<ReferralSaasExportFileResponse> {
  return apiRequest<ReferralSaasExportFileResponse>(
    accountReportPath(
      request.accountRef,
      request.reportType,
      `/exports/${encodeURIComponent(request.exportRequestId)}/file`,
    ),
    {
      method: "POST",
      body: exportFileCommandBody(request),
    },
  );
}

export function getReferralSaasAccountReportExportFileMetadata(
  request: ReferralSaasAccountExportFileReadRequest,
): Promise<ReferralSaasExportFileResponse> {
  return apiRequest<ReferralSaasExportFileResponse>(
    `v1/referral-saas/accounts/${encodeURIComponent(request.accountRef)}/exports/${encodeURIComponent(
      request.exportRequestId,
    )}`,
    {
      query: exportFileQuery(request),
    },
  );
}

export function downloadReferralSaasAccountReportExportFile(
  request: ReferralSaasAccountExportFileReadRequest,
): Promise<ReferralSaasExportFileResponse> {
  return apiRequest<ReferralSaasExportFileResponse>(
    `v1/referral-saas/accounts/${encodeURIComponent(request.accountRef)}/exports/${encodeURIComponent(
      request.exportRequestId,
    )}/download`,
    {
      query: exportFileQuery(request),
    },
  );
}

export function createReferralSaasAccountReportDeliverySchedule(
  request: ReferralSaasAccountReportDeliveryScheduleRequest,
): Promise<ReferralSaasReportDeliveryScheduleResponse> {
  return apiRequest<ReferralSaasReportDeliveryScheduleResponse>(
    accountReportPath(request.accountRef, request.reportType, "/delivery-schedules"),
    {
      method: "POST",
      body: deliveryScheduleBody(request),
    },
  );
}

export function listReferralSaasAccountReportDeliverySchedules(
  request: ReferralSaasAccountReportDeliveryScheduleListRequest,
): Promise<ReferralSaasReportDeliveryScheduleResponse> {
  return apiRequest<ReferralSaasReportDeliveryScheduleResponse>(
    accountReportPath(request.accountRef, request.reportType, "/delivery-schedules"),
    {
      query: deliveryScheduleQuery(request),
    },
  );
}

export function updateReferralSaasAccountReportDeliverySchedule(
  request: ReferralSaasAccountReportDeliveryScheduleUpdateRequest,
): Promise<ReferralSaasReportDeliveryScheduleResponse> {
  return apiRequest<ReferralSaasReportDeliveryScheduleResponse>(
    `v1/referral-saas/accounts/${encodeURIComponent(request.accountRef)}/delivery-schedules/${encodeURIComponent(
      request.scheduleId,
    )}`,
    {
      method: "PATCH",
      body: deliveryScheduleBody(request),
    },
  );
}

export function getReferralSaasAccountReportDeliveryScheduleReadiness(
  request: ReferralSaasAccountReportDeliveryScheduleReadinessRequest,
): Promise<ReferralSaasReportDeliveryScheduleResponse> {
  return apiRequest<ReferralSaasReportDeliveryScheduleResponse>(
    `v1/referral-saas/accounts/${encodeURIComponent(request.accountRef)}/delivery-schedules/${encodeURIComponent(
      request.scheduleId,
    )}/readiness`,
    {
      query: deliveryScheduleQuery(request),
    },
  );
}
