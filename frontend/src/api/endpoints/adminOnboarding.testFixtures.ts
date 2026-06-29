import type {
  AdminOnboardingReadiness,
  AdminOnboardingStateProjection,
  AdminOnboardingStateResponse,
} from "./adminOnboarding";

export function createAdminOnboardingStateResponse(
  readinessOverrides: Partial<AdminOnboardingReadiness> = {},
  stateOverrides: Partial<AdminOnboardingStateProjection> = {},
): AdminOnboardingStateResponse {
  return {
    status: "ok",
    onboarding_state: {
      contract_version: "onboarding.v1",
      generated_at: "2026-06-30T00:00:00Z",
      scope: {
        external_tenant_ref: "demo-platform-operator",
        organisation_ref: "demo-organisation",
        producer_ref: "demo-producer",
        sponsor_ref: "demo-sponsor",
        distributor_ref: "demo-distributor",
        campaign_code: "DEMO-CAMPAIGN",
        opportunity_ref: "demo-opportunity",
        resolved_tenant: { status: "UNAVAILABLE" },
      },
      sections: {},
      readiness: {},
      missing_evidence: [],
      redactions: ["TENANT_CODE_INTERNAL"],
      guardrails: ["READ_ONLY_PROJECTION", "NO_LIVE_MUTATION"],
      source_warnings: [],
      ...stateOverrides,
    },
    readiness: {
      contract_version: "onboarding.v1",
      scope: {
        external_tenant_ref: "demo-platform-operator",
        organisation_ref: "demo-organisation",
        resolved_tenant: { status: "UNAVAILABLE" },
      },
      overall_status: "GO_LIVE_DISABLED",
      categories: [],
      summary: {
        ready_count: 0,
        in_progress_count: 0,
        blocked_count: 0,
        missing_evidence_count: 0,
        permission_limited_count: 0,
        go_live_disabled_count: 0,
        total_count: 0,
      },
      guardrails: ["READ_ONLY_AGGREGATION", "NO_LIVE_MUTATION"],
      missing_evidence: [],
      source_warnings: [],
      redactions: ["TENANT_CODE_INTERNAL"],
      ...readinessOverrides,
    },
    guardrail: "Read-only admin onboarding state.",
  };
}
