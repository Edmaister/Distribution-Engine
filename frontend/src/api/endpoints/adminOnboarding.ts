import { apiRequest } from "../client";

export type AdminOnboardingStateParams = {
  external_tenant_ref?: string;
  organisation_ref?: string;
  producer_ref?: string;
  sponsor_ref?: string;
  distributor_ref?: string;
  campaign_code?: string;
  opportunity_ref?: string;
};

export type OnboardingReadinessCategory = {
  category: string;
  display_label: string;
  status: string;
  safe_display_status?: {
    status: string;
    label: string;
    action_required: boolean;
    go_live_enabled: boolean;
  };
  evidence_summary: string;
  blockers: string[];
  next_actions: string[];
};

export type AdminOnboardingReadiness = {
  contract_version: string;
  overall_status: string;
  categories: OnboardingReadinessCategory[];
  summary: {
    ready_count: number;
    in_progress_count: number;
    blocked_count: number;
    missing_evidence_count: number;
    permission_limited_count: number;
    go_live_disabled_count: number;
    total_count: number;
  };
};

export type AdminOnboardingStateResponse = {
  status: string;
  readiness: AdminOnboardingReadiness;
  guardrail: string;
};

export function getAdminOnboardingState(
  params: AdminOnboardingStateParams = {},
): Promise<AdminOnboardingStateResponse> {
  return apiRequest<AdminOnboardingStateResponse>("admin/onboarding/state", {
    query: params,
  });
}
