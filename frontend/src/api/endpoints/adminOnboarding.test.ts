import { afterEach, describe, expect, it, vi } from "vitest";

import {
  getAdminOnboardingState,
  type AdminOnboardingStateResponse,
} from "./adminOnboarding";

const successResponse: AdminOnboardingStateResponse = {
  status: "ok",
  onboarding_state: {
    contract_version: "onboarding.v1",
    generated_at: "2026-06-30T00:00:00Z",
    scope: {
      external_tenant_ref: "acme-distribution",
      organisation_ref: "org-acme",
      producer_ref: "prod-acme",
      sponsor_ref: "sponsor-acme",
      distributor_ref: "dist-acme",
      campaign_code: "CAMP-ACME",
      opportunity_ref: "opp-acme",
      resolved_tenant: { status: "UNAVAILABLE" },
    },
    sections: {
      organisation_profile: {
        status: "READY",
        data: {
          organisation_ref: "org-acme",
          external_tenant_ref: "acme-distribution",
        },
        missing_evidence: [],
      },
      webhook_api_setup: {
        status: "MISSING_EVIDENCE",
        missing_evidence: [
          {
            section: "webhook_api_setup",
            code: "NO_BACKEND_SOURCE",
            severity: "warning",
            message: "Read-only integration evidence is not available.",
          },
        ],
      },
    },
    readiness: {
      organisation_profile: "READY",
      webhook_api_setup: "MISSING_EVIDENCE",
    },
    missing_evidence: [
      {
        section: "webhook_api_setup",
        code: "NO_BACKEND_SOURCE",
        severity: "warning",
        message: "Read-only integration evidence is not available.",
      },
    ],
    redactions: ["TENANT_CODE_INTERNAL", "SECRETS_REDACTED"],
    guardrails: ["READ_ONLY_PROJECTION", "NO_MUTATION"],
    source_warnings: ["WEBHOOK_API_SETUP_SOURCE_UNAVAILABLE"],
  },
  readiness: {
    contract_version: "onboarding.v1",
    scope: {
      external_tenant_ref: "acme-distribution",
      resolved_tenant: { status: "UNAVAILABLE" },
    },
    overall_status: "GO_LIVE_DISABLED",
    categories: [
      {
        category: "organisation_profile",
        display_label: "Organisation profile",
        status: "READY",
        safe_display_status: {
          status: "READY",
          label: "Ready",
          action_required: false,
          go_live_enabled: false,
        },
        evidence_summary: "Organisation evidence is available.",
        blockers: [],
        next_actions: ["Continue to participant setup."],
      },
      {
        category: "webhook_api_setup",
        display_label: "Webhook/API setup",
        status: "MISSING_EVIDENCE",
        safe_display_status: {
          status: "NEEDS_ATTENTION",
          label: "Needs evidence",
          action_required: true,
          go_live_enabled: false,
        },
        evidence_summary: "Webhook/API evidence is unavailable.",
        blockers: ["NO_BACKEND_SOURCE"],
        next_actions: ["Review setup shell before go-live."],
      },
    ],
    summary: {
      ready_count: 1,
      in_progress_count: 0,
      blocked_count: 0,
      missing_evidence_count: 1,
      permission_limited_count: 0,
      go_live_disabled_count: 2,
      total_count: 2,
    },
    guardrails: ["READ_ONLY_AGGREGATION", "NO_GO_LIVE_ACTIONS"],
    missing_evidence: [
      {
        section: "webhook_api_setup",
        code: "NO_BACKEND_SOURCE",
        severity: "warning",
        message: "Read-only integration evidence is not available.",
      },
    ],
    source_warnings: ["WEBHOOK_API_SETUP_SOURCE_UNAVAILABLE"],
    redactions: ["TENANT_CODE_INTERNAL", "SECRETS_REDACTED"],
  },
  guardrail:
    "Read-only admin onboarding state. This endpoint does not create records or move money.",
};

describe("admin onboarding api helper", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

  it("requests the read-only onboarding state endpoint with external references only", async () => {
    const fetchMock = mockFetch(successResponse);

    await getAdminOnboardingState({
      external_tenant_ref: " acme-distribution ",
      organisation_ref: " org-acme ",
      producer_ref: " prod-acme ",
      sponsor_ref: " ",
      distributor_ref: " dist-acme ",
      campaign_code: " CAMP-ACME ",
      opportunity_ref: " opp-acme ",
      tenant_code: "INTERNAL-SHOULD-NOT-BE-SENT",
    } as Parameters<typeof getAdminOnboardingState>[0] & {
      tenant_code: string;
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, options] = fetchMock.mock.calls[0] as unknown as [
      string,
      RequestInit,
    ];
    const requestUrl = new URL(url);

    expect(requestUrl.origin).toBe("https://api.example.test");
    expect(requestUrl.pathname).toBe("/admin/onboarding/state");
    expect(requestUrl.searchParams.get("external_tenant_ref")).toBe(
      "acme-distribution",
    );
    expect(requestUrl.searchParams.get("organisation_ref")).toBe("org-acme");
    expect(requestUrl.searchParams.get("producer_ref")).toBe("prod-acme");
    expect(requestUrl.searchParams.get("distributor_ref")).toBe("dist-acme");
    expect(requestUrl.searchParams.get("campaign_code")).toBe("CAMP-ACME");
    expect(requestUrl.searchParams.get("opportunity_ref")).toBe("opp-acme");
    expect(requestUrl.searchParams.has("sponsor_ref")).toBe(false);
    expect(requestUrl.searchParams.has("tenant_code")).toBe(false);
    expect(options.method).toBe("GET");
    expect(options.headers).toMatchObject({ "x-api-key": "admin-key" });
  });

  it("returns the projection, readiness categories, blockers, next actions, and guardrails", async () => {
    mockFetch(successResponse);

    const result = await getAdminOnboardingState({
      external_tenant_ref: "acme-distribution",
    });
    const state = result.onboarding_state;

    expect(result.status).toBe("ok");
    expect(state).toBeDefined();
    expect(state?.contract_version).toBe("onboarding.v1");
    expect(state?.sections.organisation_profile.status).toBe("READY");
    expect(state?.sections.webhook_api_setup.missing_evidence[0]).toMatchObject(
      {
        code: "NO_BACKEND_SOURCE",
        severity: "warning",
      },
    );
    expect(result.readiness.overall_status).toBe("GO_LIVE_DISABLED");
    expect(result.readiness.categories[1]).toMatchObject({
      category: "webhook_api_setup",
      status: "MISSING_EVIDENCE",
      blockers: ["NO_BACKEND_SOURCE"],
      next_actions: ["Review setup shell before go-live."],
    });
    expect(result.readiness.summary).toMatchObject({
      missing_evidence_count: 1,
      go_live_disabled_count: 2,
      total_count: 2,
    });
    expect(result.guardrail).toContain("Read-only admin onboarding state");
  });

  it("handles partial missing-evidence responses without assuming live integration data", async () => {
    mockFetch({
      ...successResponse,
      onboarding_state: {
        ...successResponse.onboarding_state,
        scope: {
          external_tenant_ref: "unknown-demo-tenant",
          resolved_tenant: { status: "UNAVAILABLE" },
        },
        sections: {},
        missing_evidence: [
          {
            section: "tenant_resolution",
            code: "NO_RESOLVED_TENANT",
            severity: "warning",
            message: "Tenant could not be resolved from external references.",
          },
        ],
      },
      readiness: {
        ...successResponse.readiness,
        scope: {
          external_tenant_ref: "unknown-demo-tenant",
          resolved_tenant: { status: "UNAVAILABLE" },
        },
        categories: [
          {
            category: "organisation_profile",
            display_label: "Organisation profile",
            status: "MISSING_EVIDENCE",
            evidence_summary: "Organisation evidence is unavailable.",
            blockers: ["NO_RESOLVED_TENANT"],
            next_actions: [
              "Confirm external tenant and organisation references.",
            ],
          },
        ],
        summary: {
          ready_count: 0,
          in_progress_count: 0,
          blocked_count: 0,
          missing_evidence_count: 1,
          permission_limited_count: 0,
          go_live_disabled_count: 1,
          total_count: 1,
        },
      },
    });

    const result = await getAdminOnboardingState({
      external_tenant_ref: "unknown-demo-tenant",
    });
    const state = result.onboarding_state;

    expect(state).toBeDefined();
    expect(state?.scope.resolved_tenant).toEqual({
      status: "UNAVAILABLE",
    });
    expect(result.readiness.categories[0]).toMatchObject({
      status: "MISSING_EVIDENCE",
      blockers: ["NO_RESOLVED_TENANT"],
    });
    expect(result.readiness.categories[0].next_actions).toContain(
      "Confirm external tenant and organisation references.",
    );
  });

  it("uses the shared API error contract for safe fallback handling", async () => {
    mockFetch(
      {
        detail: {
          code: "readiness_unavailable",
          message: "Read-only onboarding state is unavailable.",
        },
      },
      503,
    );

    await expect(
      getAdminOnboardingState({ external_tenant_ref: "acme-distribution" }),
    ).rejects.toMatchObject({
      status: 503,
      message: expect.stringContaining("readiness_unavailable"),
    });
  });

  it("does not depend on or expose sensitive internal values in the safe response", async () => {
    mockFetch(successResponse);

    const result = await getAdminOnboardingState({
      external_tenant_ref: "acme-distribution",
    });
    const state = result.onboarding_state;
    const rendered = JSON.stringify(result).toLowerCase();

    expect(state).toBeDefined();
    expect(state?.scope.resolved_tenant).toEqual({
      status: "UNAVAILABLE",
    });
    expect(rendered).toContain("tenant_code_internal");
    expect(rendered).not.toContain('"tenant_code":');
    expect(rendered).not.toContain("internal-tenant");
    expect(rendered).not.toContain("secret-value");
    expect(rendered).not.toContain("api-key-value");
    expect(rendered).not.toContain("client-secret-value");
    expect(rendered).not.toContain("signing-secret-value");
    expect(rendered).not.toContain("provider-payload-value");
    expect(rendered).not.toContain("raw-audit-value");
    expect(rendered).not.toContain("wallet-account-value");
    expect(rendered).not.toContain("settlement-internal-value");
    expect(rendered).not.toContain("fulfilment-internal-value");
    expect(rendered).not.toContain("retry-internal-value");
    expect(rendered).not.toContain("money-movement-value");
  });
});

function mockFetch(payload: unknown, status = 200): ReturnType<typeof vi.fn> {
  localStorage.setItem("amplifi.apiBaseUrl", "https://api.example.test");
  localStorage.setItem("amplifi.apiKey", "admin-key");
  const fetchMock = vi.fn(async () => {
    return new Response(JSON.stringify(payload), {
      status,
      headers: { "Content-Type": "application/json" },
    });
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}
