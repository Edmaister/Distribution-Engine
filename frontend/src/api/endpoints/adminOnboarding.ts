import { apiRequest } from "../client";

const ADMIN_ONBOARDING_STATE_QUERY_KEYS = [
  "external_tenant_ref",
  "organisation_ref",
  "producer_ref",
  "sponsor_ref",
  "distributor_ref",
  "campaign_code",
  "opportunity_ref",
] as const;

export type AdminOnboardingStateParams = {
  external_tenant_ref?: string;
  organisation_ref?: string;
  producer_ref?: string;
  sponsor_ref?: string;
  distributor_ref?: string;
  campaign_code?: string;
  opportunity_ref?: string;
};

export type OnboardingMissingEvidence = {
  section: string;
  code: string;
  severity: string;
  message: string;
};

export type OnboardingStateScope = AdminOnboardingStateParams & {
  resolved_tenant?: {
    status: string;
  };
};

export type OnboardingStateSection = {
  status: string;
  data?: Record<string, unknown>;
  missing_evidence: OnboardingMissingEvidence[];
};

export type AdminOnboardingStateProjection = {
  contract_version: string;
  generated_at?: string;
  scope: OnboardingStateScope;
  sections: Record<string, OnboardingStateSection>;
  readiness: Record<string, unknown>;
  missing_evidence: OnboardingMissingEvidence[];
  redactions: string[];
  guardrails: string[];
  source_warnings: string[];
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
  scope?: OnboardingStateScope;
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
  guardrails?: string[];
  missing_evidence?: OnboardingMissingEvidence[];
  source_warnings?: string[];
  redactions?: string[];
};

export type AdminOnboardingStateResponse = {
  status: string;
  onboarding_state?: AdminOnboardingStateProjection;
  readiness: AdminOnboardingReadiness;
  guardrail: string;
};

export function getAdminOnboardingState(
  params: AdminOnboardingStateParams = {},
): Promise<AdminOnboardingStateResponse> {
  return apiRequest<AdminOnboardingStateResponse>("admin/onboarding/state", {
    query: buildAdminOnboardingStateQuery(params),
  });
}

function buildAdminOnboardingStateQuery(
  params: AdminOnboardingStateParams,
): AdminOnboardingStateParams {
  return ADMIN_ONBOARDING_STATE_QUERY_KEYS.reduce<AdminOnboardingStateParams>(
    (query, key) => {
      const value = params[key];

      if (typeof value !== "string") {
        return query;
      }

      const trimmed = value.trim();
      if (trimmed) {
        query[key] = trimmed;
      }

      return query;
    },
    {},
  );
}
