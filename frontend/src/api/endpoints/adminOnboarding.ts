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

const ADMIN_ONBOARDING_DRAFT_SCOPE_KEYS = [
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
  onboarding_state: AdminOnboardingStateProjection;
  readiness: AdminOnboardingReadiness;
  guardrail: string;
};

export type AdminOnboardingDraftSectionKey =
  | "company"
  | "producer_sponsor"
  | "distributor"
  | "member_role"
  | "campaign_opportunity"
  | "webhook_api";

export type AdminOnboardingDraftSaveRequest = AdminOnboardingStateParams & {
  sections?: Partial<
    Record<AdminOnboardingDraftSectionKey, Record<string, unknown>>
  >;
  draft_sections?: Partial<
    Record<AdminOnboardingDraftSectionKey, Record<string, unknown>>
  >;
  idempotency_key: string;
  correlation_id?: string;
};

export type AdminOnboardingDryRunValidationRequest =
  AdminOnboardingStateParams & {
    draft_ref?: string;
    validation_scope?: AdminOnboardingDraftSectionKey[] | string[];
    sections?: Partial<
      Record<AdminOnboardingDraftSectionKey, Record<string, unknown>>
    >;
    draft_sections?: Partial<
      Record<AdminOnboardingDraftSectionKey, Record<string, unknown>>
    >;
    idempotency_key?: string;
    correlation_id?: string;
  };

export type AdminOnboardingValidationItem = {
  code: string;
  message: string;
  section?: string | null;
  field?: string | null;
  severity: string;
};

export type AdminOnboardingDraftSaveResponse = {
  status: string;
  draft_ref: string;
  draft_status: string;
  draft_version?: number;
  idempotency_status: string;
  validation_result?: Record<string, unknown>;
  validation_summary?: {
    status: string;
    safe_error_count: number;
    missing_evidence_count: number;
    blocker_count: number;
  };
  readiness_preview?: AdminOnboardingReadiness;
  missing_evidence?: AdminOnboardingValidationItem[];
  blockers?: AdminOnboardingValidationItem[];
  next_actions?: string[];
  guardrails?: string[];
  redactions?: string[];
  no_live_action_confirmed: boolean;
};

export type AdminOnboardingSubmitForReviewRequest =
  AdminOnboardingStateParams & {
    expected_version: number;
    idempotency_key: string;
    correlation_id?: string;
  };

export type AdminOnboardingSubmitForReviewResponse = {
  status: string;
  draft_ref: string;
  draft_status: string;
  draft_version?: number;
  idempotency_status: string;
  validation_result?: Record<string, unknown>;
  validation_summary?: {
    status: string;
    safe_error_count: number;
    missing_evidence_count: number;
    blocker_count: number;
  };
  readiness_summary?: {
    overall_status?: string;
    ready_count: number;
    blocked_count: number;
    missing_evidence_count: number;
    go_live_disabled_count: number;
    total_count: number;
    go_live_enabled: boolean;
  };
  missing_evidence?: AdminOnboardingValidationItem[];
  blockers?: AdminOnboardingValidationItem[];
  next_actions?: string[];
  guardrails?: string[];
  redactions?: string[];
  audit_evidence_ref?: string | null;
  audit_link_ref?: string | null;
  audit_evidence_status?: string;
  no_live_action_confirmed: boolean;
};

export type AdminOnboardingReviewOutcome =
  | "APPROVED_FOR_INTERNAL_REVIEW"
  | "BLOCKED";

export type AdminOnboardingReviewDecisionRequest =
  AdminOnboardingStateParams & {
    expected_version: number;
    idempotency_key: string;
    review_outcome: AdminOnboardingReviewOutcome;
    reason_category: string;
    reason: string;
    correlation_id?: string;
  };

export type AdminOnboardingReviewDecisionResponse = {
  status: string;
  draft_ref: string;
  previous_status?: string;
  draft_status: string;
  draft_version?: number;
  review_outcome: AdminOnboardingReviewOutcome | string;
  reason_category?: string;
  idempotency_status: string;
  validation_result?: Record<string, unknown>;
  validation_summary?: {
    status: string;
    safe_error_count: number;
    missing_evidence_count: number;
    blocker_count: number;
  };
  readiness_summary?: {
    overall_status?: string;
    ready_count: number;
    blocked_count: number;
    missing_evidence_count: number;
    go_live_disabled_count: number;
    total_count: number;
    go_live_enabled: boolean;
  };
  missing_evidence?: AdminOnboardingValidationItem[];
  blockers?: AdminOnboardingValidationItem[];
  next_actions?: string[];
  guardrails?: string[];
  redactions?: string[];
  audit_evidence_ref?: string | null;
  audit_link_ref?: string | null;
  audit_evidence_status?: string;
  approval_to_launch: boolean;
  go_live_enabled: boolean;
  no_live_action_confirmed: boolean;
};

export type AdminOnboardingDryRunValidationResponse = {
  status: string;
  validation_result: Record<string, unknown>;
  readiness_preview: AdminOnboardingReadiness;
  missing_evidence: AdminOnboardingValidationItem[];
  blockers: AdminOnboardingValidationItem[];
  warnings: AdminOnboardingValidationItem[];
  safe_errors: AdminOnboardingValidationItem[];
  next_actions: string[];
  guardrails: string[];
  redactions: string[];
  no_persistence_confirmed: boolean;
  no_live_action_confirmed: boolean;
};

export function getAdminOnboardingState(
  params: AdminOnboardingStateParams = {},
): Promise<AdminOnboardingStateResponse> {
  return apiRequest<AdminOnboardingStateResponse>("admin/onboarding/state", {
    query: buildAdminOnboardingStateQuery(params),
  });
}

export function saveAdminOnboardingDraft(
  request: AdminOnboardingDraftSaveRequest,
): Promise<AdminOnboardingDraftSaveResponse> {
  return apiRequest<AdminOnboardingDraftSaveResponse>(
    "admin/onboarding/drafts",
    {
      method: "POST",
      body: buildAdminOnboardingDraftSaveBody(request),
    },
  );
}

export function validateAdminOnboardingDryRun(
  request: AdminOnboardingDryRunValidationRequest,
): Promise<AdminOnboardingDryRunValidationResponse> {
  return apiRequest<AdminOnboardingDryRunValidationResponse>(
    "admin/onboarding/validate",
    {
      method: "POST",
      body: buildAdminOnboardingDryRunBody(request),
    },
  );
}

export function submitAdminOnboardingDraftForReview(
  draftRef: string,
  request: AdminOnboardingSubmitForReviewRequest,
): Promise<AdminOnboardingSubmitForReviewResponse> {
  return apiRequest<AdminOnboardingSubmitForReviewResponse>(
    `admin/onboarding/drafts/${encodeURIComponent(draftRef.trim())}/submit-for-review`,
    {
      method: "POST",
      body: buildAdminOnboardingSubmitForReviewBody(request),
    },
  );
}

export function recordAdminOnboardingReviewDecision(
  draftRef: string,
  request: AdminOnboardingReviewDecisionRequest,
): Promise<AdminOnboardingReviewDecisionResponse> {
  return apiRequest<AdminOnboardingReviewDecisionResponse>(
    `admin/onboarding/drafts/${encodeURIComponent(draftRef.trim())}/review-decision`,
    {
      method: "POST",
      body: buildAdminOnboardingReviewDecisionBody(request),
    },
  );
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

function buildAdminOnboardingDraftSaveBody(
  request: AdminOnboardingDraftSaveRequest,
): AdminOnboardingDraftSaveRequest {
  const scope =
    ADMIN_ONBOARDING_DRAFT_SCOPE_KEYS.reduce<AdminOnboardingStateParams>(
      (allowedScope, key) => {
        const value = request[key];

        if (typeof value !== "string") {
          return allowedScope;
        }

        const trimmed = value.trim();
        if (trimmed) {
          allowedScope[key] = trimmed;
        }

        return allowedScope;
      },
      {},
    );

  const body: AdminOnboardingDraftSaveRequest = {
    ...scope,
    idempotency_key: request.idempotency_key.trim(),
  };

  const correlationId = request.correlation_id?.trim();
  if (correlationId) {
    body.correlation_id = correlationId;
  }

  const sections = safeSections(request.sections || request.draft_sections);
  if (Object.keys(sections).length > 0) {
    body.sections = sections;
  }

  return body;
}

function buildAdminOnboardingDryRunBody(
  request: AdminOnboardingDryRunValidationRequest,
): AdminOnboardingDryRunValidationRequest {
  const scope =
    ADMIN_ONBOARDING_DRAFT_SCOPE_KEYS.reduce<AdminOnboardingStateParams>(
      (allowedScope, key) => {
        const value = request[key];

        if (typeof value !== "string") {
          return allowedScope;
        }

        const trimmed = value.trim();
        if (trimmed) {
          allowedScope[key] = trimmed;
        }

        return allowedScope;
      },
      {},
    );

  const body: AdminOnboardingDryRunValidationRequest = { ...scope };

  const draftRef = request.draft_ref?.trim();
  if (draftRef) {
    body.draft_ref = draftRef;
  }

  const validationScope = request.validation_scope?.filter(
    (value) => typeof value === "string" && value.trim(),
  );
  if (validationScope?.length) {
    body.validation_scope = validationScope.map((value) => value.trim());
  }

  const idempotencyKey = request.idempotency_key?.trim();
  if (idempotencyKey) {
    body.idempotency_key = idempotencyKey;
  }

  const correlationId = request.correlation_id?.trim();
  if (correlationId) {
    body.correlation_id = correlationId;
  }

  const sections = safeSections(request.sections || request.draft_sections);
  if (Object.keys(sections).length > 0) {
    body.sections = sections;
  }

  return body;
}

function buildAdminOnboardingSubmitForReviewBody(
  request: AdminOnboardingSubmitForReviewRequest,
): AdminOnboardingSubmitForReviewRequest {
  const scope =
    ADMIN_ONBOARDING_DRAFT_SCOPE_KEYS.reduce<AdminOnboardingStateParams>(
      (allowedScope, key) => {
        const value = request[key];

        if (typeof value !== "string") {
          return allowedScope;
        }

        const trimmed = value.trim();
        if (trimmed) {
          allowedScope[key] = trimmed;
        }

        return allowedScope;
      },
      {},
    );

  const body: AdminOnboardingSubmitForReviewRequest = {
    ...scope,
    expected_version: Math.max(1, Math.trunc(request.expected_version)),
    idempotency_key: request.idempotency_key.trim(),
  };

  const correlationId = request.correlation_id?.trim();
  if (correlationId) {
    body.correlation_id = correlationId;
  }

  return body;
}

function buildAdminOnboardingReviewDecisionBody(
  request: AdminOnboardingReviewDecisionRequest,
): AdminOnboardingReviewDecisionRequest {
  const scope =
    ADMIN_ONBOARDING_DRAFT_SCOPE_KEYS.reduce<AdminOnboardingStateParams>(
      (allowedScope, key) => {
        const value = request[key];

        if (typeof value !== "string") {
          return allowedScope;
        }

        const trimmed = value.trim();
        if (trimmed) {
          allowedScope[key] = trimmed;
        }

        return allowedScope;
      },
      {},
    );

  const body: AdminOnboardingReviewDecisionRequest = {
    ...scope,
    expected_version: Math.max(1, Math.trunc(request.expected_version)),
    idempotency_key: request.idempotency_key.trim(),
    review_outcome: request.review_outcome,
    reason_category: request.reason_category.trim(),
    reason: request.reason.trim(),
  };

  const correlationId = request.correlation_id?.trim();
  if (correlationId) {
    body.correlation_id = correlationId;
  }

  return body;
}

function safeSections(
  sections:
    | Partial<Record<AdminOnboardingDraftSectionKey, Record<string, unknown>>>
    | undefined,
): Partial<Record<AdminOnboardingDraftSectionKey, Record<string, unknown>>> {
  if (!sections) {
    return {};
  }

  const allowed: Partial<
    Record<AdminOnboardingDraftSectionKey, Record<string, unknown>>
  > = {};
  (Object.keys(sections) as AdminOnboardingDraftSectionKey[]).forEach(
    (sectionKey) => {
      const section = sections[sectionKey];
      if (!section || typeof section !== "object") {
        return;
      }

      const safeEntries = Object.entries(section).filter(
        ([key, value]) =>
          !isUnsafeDraftField(key) && value !== undefined && value !== null,
      );
      if (safeEntries.length > 0) {
        allowed[sectionKey] = Object.fromEntries(safeEntries);
      }
    },
  );
  return allowed;
}

function isUnsafeDraftField(key: string): boolean {
  const normalized = key.trim().toLowerCase().replace(/-/g, "_");
  return [
    "tenant_code",
    "api_key",
    "client_secret",
    "secret",
    "token",
    "password",
    "credential",
    "signing",
    "certificate",
    "private_key",
    "provider",
    "raw",
    "audit",
    "webhook_delivery",
    "deliver_webhook",
    "wallet",
    "settlement",
    "fulfilment",
    "funding_internal",
    "funding_reservation",
    "funding_transaction",
    "retry",
    "money",
    "publish",
    "launch",
    "activate_go_live",
    "send_invite",
    "create_tenant",
    "create_user",
  ].some((unsafePart) => normalized.includes(unsafePart));
}
