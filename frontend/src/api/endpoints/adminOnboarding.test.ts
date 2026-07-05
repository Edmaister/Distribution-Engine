import { afterEach, describe, expect, it, vi } from "vitest";

import {
  getAdminOnboardingState,
  saveAdminOnboardingDraft,
  submitAdminOnboardingDraftForReview,
  validateAdminOnboardingDryRun,
  type AdminOnboardingDraftSaveResponse,
  type AdminOnboardingSubmitForReviewResponse,
  type AdminOnboardingDryRunValidationResponse,
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

const draftSaveResponse: AdminOnboardingDraftSaveResponse = {
  status: "saved",
  draft_ref: "draft_acme_distribution",
  draft_status: "DRAFT_CREATED",
  idempotency_status: "NEW_REQUEST",
  validation_result: {
    status: "WARNING",
    validated_scope: {
      external_tenant_ref: "acme-distribution",
      organisation_ref: "org-acme",
    },
  },
  validation_summary: {
    status: "WARNING",
    safe_error_count: 0,
    missing_evidence_count: 1,
    blocker_count: 0,
  },
  readiness_preview: successResponse.readiness,
  missing_evidence: [
    {
      section: "company",
      field: "industry",
      code: "MISSING_EVIDENCE",
      message: "Industry evidence is not complete.",
      severity: "warning",
    },
  ],
  blockers: [],
  next_actions: ["Review company draft evidence before go-live review."],
  guardrails: ["NO_LIVE_ACTIONS", "NO_MONEY_MOVEMENT"],
  redactions: ["TENANT_CODE_INTERNAL", "SECRETS_REDACTED"],
  no_live_action_confirmed: true,
};

const dryRunValidationResponse: AdminOnboardingDryRunValidationResponse = {
  status: "ok",
  validation_result: {
    status: "MISSING_EVIDENCE",
    validated_scope: {
      external_tenant_ref: "acme-distribution",
      organisation_ref: "org-acme",
      resolved_tenant: { status: "UNAVAILABLE" },
    },
    validated_sections: ["company"],
    checks: [],
  },
  readiness_preview: successResponse.readiness,
  missing_evidence: [
    {
      section: "company",
      field: "industry",
      code: "MISSING_EVIDENCE",
      message: "Industry evidence is not complete.",
      severity: "warning",
    },
  ],
  blockers: [],
  warnings: [
    {
      section: "readiness",
      field: null,
      code: "GO_LIVE_DISABLED",
      message: "Dry-run validation does not enable go-live.",
      severity: "info",
    },
  ],
  safe_errors: [],
  next_actions: ["Review company draft evidence before go-live review."],
  guardrails: ["DRY_RUN_ONLY", "NO_PERSISTENCE", "NO_LIVE_MUTATION"],
  redactions: ["TENANT_CODE_INTERNAL", "SECRETS_REDACTED"],
  no_persistence_confirmed: true,
  no_live_action_confirmed: true,
};

const submitForReviewResponse: AdminOnboardingSubmitForReviewResponse = {
  status: "submitted_for_review",
  draft_ref: "draft_acme_distribution",
  draft_status: "READY_FOR_REVIEW",
  draft_version: 2,
  idempotency_status: "NEW_REQUEST",
  validation_summary: {
    status: "READY",
    safe_error_count: 0,
    missing_evidence_count: 0,
    blocker_count: 0,
  },
  readiness_summary: {
    overall_status: "READY_FOR_REVIEW",
    ready_count: 1,
    blocked_count: 0,
    missing_evidence_count: 0,
    go_live_disabled_count: 1,
    total_count: 1,
    go_live_enabled: false,
  },
  missing_evidence: [],
  blockers: [],
  next_actions: ["Review submitted draft evidence before any later approval."],
  guardrails: ["SUBMIT_FOR_REVIEW_ONLY", "NO_VALUE_TRANSFER"],
  redactions: ["internal_identifier"],
  audit_evidence_ref: null,
  audit_link_ref: null,
  audit_evidence_status: "NOT_RECORDED_IN_TASK_116",
  no_live_action_confirmed: true,
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

    expect(result.status).toBe("ok");
    expect(result.onboarding_state.contract_version).toBe("onboarding.v1");
    expect(result.onboarding_state.sections.organisation_profile.status).toBe(
      "READY",
    );
    expect(
      result.onboarding_state.sections.webhook_api_setup.missing_evidence[0],
    ).toMatchObject({
      code: "NO_BACKEND_SOURCE",
      severity: "warning",
    });
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

    expect(result.onboarding_state.scope.resolved_tenant).toEqual({
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
    const rendered = JSON.stringify(result).toLowerCase();

    expect(result.onboarding_state.scope.resolved_tenant).toEqual({
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

  it("saves onboarding draft intent with external references and sanitized sections only", async () => {
    const fetchMock = mockFetch(draftSaveResponse);

    const result = await saveAdminOnboardingDraft({
      external_tenant_ref: " acme-distribution ",
      organisation_ref: " org-acme ",
      producer_ref: " ",
      idempotency_key: " company-draft-key ",
      correlation_id: " company-onboarding-shell ",
      tenant_code: "INTERNAL-SHOULD-NOT-BE-SENT",
      sections: {
        company: {
          organisation_name: "Acme Distribution Ltd",
          external_tenant_ref: "acme-distribution",
          organisation_ref: "org-acme",
          admin_contact: "ops@example.test",
          tenant_code: "INTERNAL-SHOULD-NOT-BE-SENT",
          api_key: "SECRET-API-KEY",
          client_secret: "SECRET-CLIENT",
          publish_campaign: true,
          activate_go_live: true,
        },
      },
    } as Parameters<typeof saveAdminOnboardingDraft>[0] & {
      tenant_code: string;
    });

    expect(result).toMatchObject({
      status: "saved",
      draft_ref: "draft_acme_distribution",
      draft_status: "DRAFT_CREATED",
      idempotency_status: "NEW_REQUEST",
      no_live_action_confirmed: true,
    });

    const [url, options] = fetchMock.mock.calls[0] as unknown as [
      string,
      RequestInit,
    ];
    const requestUrl = new URL(url);
    const body = JSON.parse(String(options.body));
    const renderedBody = JSON.stringify(body).toLowerCase();

    expect(requestUrl.pathname).toBe("/admin/onboarding/drafts");
    expect(options.method).toBe("POST");
    expect(body).toMatchObject({
      external_tenant_ref: "acme-distribution",
      organisation_ref: "org-acme",
      idempotency_key: "company-draft-key",
      correlation_id: "company-onboarding-shell",
      sections: {
        company: {
          organisation_name: "Acme Distribution Ltd",
          external_tenant_ref: "acme-distribution",
          organisation_ref: "org-acme",
          admin_contact: "ops@example.test",
        },
      },
    });
    expect(body).not.toHaveProperty("tenant_code");
    expect(body).not.toHaveProperty("producer_ref");
    expect(renderedBody).not.toContain("tenant_code");
    expect(renderedBody).not.toContain("secret-api-key");
    expect(renderedBody).not.toContain("secret-client");
    expect(renderedBody).not.toContain("publish_campaign");
    expect(renderedBody).not.toContain("activate_go_live");
  });

  it("surfaces safe draft-save conflicts through the shared API error contract", async () => {
    mockFetch(
      {
        detail: {
          code: "IDEMPOTENCY_CONFLICT",
          message:
            "The onboarding draft request conflicts with an earlier request.",
          no_live_action_confirmed: true,
        },
      },
      409,
    );

    await expect(
      saveAdminOnboardingDraft({
        external_tenant_ref: "acme-distribution",
        organisation_ref: "org-acme",
        idempotency_key: "company-draft-key",
        sections: {
          company: {
            organisation_name: "Acme Distribution Ltd",
          },
        },
      }),
    ).rejects.toMatchObject({
      status: 409,
      message: expect.stringContaining("IDEMPOTENCY_CONFLICT"),
    });
  });

  it("runs dry-run validation with external refs and sanitized sections only", async () => {
    const fetchMock = mockFetch(dryRunValidationResponse);

    const result = await validateAdminOnboardingDryRun({
      external_tenant_ref: " acme-distribution ",
      organisation_ref: " org-acme ",
      producer_ref: " ",
      draft_ref: " draft-acme ",
      validation_scope: [" company ", "readiness"],
      idempotency_key: " client-preview-key ",
      correlation_id: " company-validation-preview ",
      tenant_code: "INTERNAL-SHOULD-NOT-BE-SENT",
      sections: {
        company: {
          organisation_name: "Acme Distribution Ltd",
          external_tenant_ref: "acme-distribution",
          organisation_ref: "org-acme",
          admin_contact: "ops@example.test",
          tenant_code: "INTERNAL-SHOULD-NOT-BE-SENT",
          api_key: "SECRET-API-KEY",
          client_secret: "SECRET-CLIENT",
          access_token: "SECRET-TOKEN",
          private_key: "SECRET-PRIVATE-KEY",
          funding_internal: "funding-internal",
          publish_campaign: true,
          activate_go_live: true,
        },
      },
    } as Parameters<typeof validateAdminOnboardingDryRun>[0] & {
      tenant_code: string;
    });

    expect(result).toMatchObject({
      status: "ok",
      no_persistence_confirmed: true,
      no_live_action_confirmed: true,
    });

    const [url, options] = fetchMock.mock.calls[0] as unknown as [
      string,
      RequestInit,
    ];
    const requestUrl = new URL(url);
    const body = JSON.parse(String(options.body));
    const renderedBody = JSON.stringify(body).toLowerCase();

    expect(requestUrl.pathname).toBe("/admin/onboarding/validate");
    expect(options.method).toBe("POST");
    expect(body).toMatchObject({
      external_tenant_ref: "acme-distribution",
      organisation_ref: "org-acme",
      draft_ref: "draft-acme",
      validation_scope: ["company", "readiness"],
      idempotency_key: "client-preview-key",
      correlation_id: "company-validation-preview",
      sections: {
        company: {
          organisation_name: "Acme Distribution Ltd",
          external_tenant_ref: "acme-distribution",
          organisation_ref: "org-acme",
          admin_contact: "ops@example.test",
        },
      },
    });
    expect(body).not.toHaveProperty("tenant_code");
    expect(body).not.toHaveProperty("producer_ref");
    expect(renderedBody).not.toContain("tenant_code");
    expect(renderedBody).not.toContain("secret-api-key");
    expect(renderedBody).not.toContain("secret-client");
    expect(renderedBody).not.toContain("secret-token");
    expect(renderedBody).not.toContain("secret-private-key");
    expect(renderedBody).not.toContain("funding_internal");
    expect(renderedBody).not.toContain("publish_campaign");
    expect(renderedBody).not.toContain("activate_go_live");
  });

  it("surfaces safe dry-run validation errors through the shared API error contract", async () => {
    mockFetch(
      {
        detail: {
          code: "UNSAFE_OPERATION_ATTEMPTED",
          message: "The validation request contains unsafe fields.",
          no_live_action_confirmed: true,
        },
      },
      422,
    );

    await expect(
      validateAdminOnboardingDryRun({
        external_tenant_ref: "acme-distribution",
        organisation_ref: "org-acme",
        validation_scope: ["company"],
      }),
    ).rejects.toMatchObject({
      status: 422,
      message: expect.stringContaining("UNSAFE_OPERATION_ATTEMPTED"),
    });
  });

  it("submits a saved draft for review with external references and optimistic version only", async () => {
    const fetchMock = mockFetch(submitForReviewResponse);

    const result = await submitAdminOnboardingDraftForReview(
      " draft_acme_distribution ",
      {
        external_tenant_ref: " acme-distribution ",
        organisation_ref: " org-acme ",
        producer_ref: " ",
        expected_version: 1,
        idempotency_key: " submit-review-key ",
        correlation_id: " company-submit-review ",
        tenant_code: "INTERNAL-SHOULD-NOT-BE-SENT",
      } as Parameters<typeof submitAdminOnboardingDraftForReview>[1] & {
        tenant_code: string;
      },
    );

    expect(result).toMatchObject({
      status: "submitted_for_review",
      draft_ref: "draft_acme_distribution",
      draft_status: "READY_FOR_REVIEW",
      idempotency_status: "NEW_REQUEST",
      no_live_action_confirmed: true,
    });

    const [url, options] = fetchMock.mock.calls[0] as unknown as [
      string,
      RequestInit,
    ];
    const requestUrl = new URL(url);
    const body = JSON.parse(String(options.body));
    const renderedBody = JSON.stringify(body).toLowerCase();

    expect(requestUrl.pathname).toBe(
      "/admin/onboarding/drafts/draft_acme_distribution/submit-for-review",
    );
    expect(options.method).toBe("POST");
    expect(body).toMatchObject({
      external_tenant_ref: "acme-distribution",
      organisation_ref: "org-acme",
      expected_version: 1,
      idempotency_key: "submit-review-key",
      correlation_id: "company-submit-review",
    });
    expect(body).not.toHaveProperty("tenant_code");
    expect(body).not.toHaveProperty("producer_ref");
    expect(renderedBody).not.toContain("tenant_code");
    expect(renderedBody).not.toContain("secret");
    expect(renderedBody).not.toContain("api_key");
    expect(renderedBody).not.toContain("client_secret");
    expect(renderedBody).not.toContain("wallet");
    expect(renderedBody).not.toContain("settlement");
    expect(renderedBody).not.toContain("fulfilment");
    expect(renderedBody).not.toContain("retry");
    expect(renderedBody).not.toContain("money_movement");
  });

  it("surfaces safe submit-for-review conflicts through the shared API error contract", async () => {
    mockFetch(
      {
        detail: {
          code: "STALE_DRAFT",
          message: "Draft changed before it could be submitted for review.",
          no_live_action_confirmed: true,
        },
      },
      409,
    );

    await expect(
      submitAdminOnboardingDraftForReview("draft_acme_distribution", {
        external_tenant_ref: "acme-distribution",
        organisation_ref: "org-acme",
        expected_version: 1,
        idempotency_key: "submit-review-key",
      }),
    ).rejects.toMatchObject({
      status: 409,
      message: expect.stringContaining("STALE_DRAFT"),
    });
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
