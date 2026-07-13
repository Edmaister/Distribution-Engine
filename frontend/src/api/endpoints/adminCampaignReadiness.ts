import { apiRequest } from "../client";

export type CampaignReadinessOperation =
  | "CONTROL_PLANE_VIEW"
  | "CREATE_TRACK"
  | "GENERATE_LINKS"
  | "ACTIVATE_CAMPAIGN";

export type AdminCampaignReadinessRequest = {
  campaignCode: string;
  tenantCode: string;
  operation?: CampaignReadinessOperation;
  opportunityId?: string;
  includeEvidence?: boolean;
};

export type AdminCampaignReadinessResponse = {
  status?: string;
  readiness?: Record<string, unknown>;
  guardrail?: string;
};

export function getAdminCampaignReadiness(
  request: AdminCampaignReadinessRequest,
): Promise<AdminCampaignReadinessResponse> {
  return apiRequest<AdminCampaignReadinessResponse>(
    `admin/campaigns/${encodeURIComponent(request.campaignCode)}/readiness`,
    {
      query: {
        tenant_code: request.tenantCode,
        operation: request.operation,
        opportunity_id: request.opportunityId,
        include_evidence: request.includeEvidence ?? true,
      },
    },
  );
}
