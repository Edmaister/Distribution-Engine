-- Onboarding draft persistence foundations only.
-- This migration creates storage primitives without enabling draft-save routes,
-- live onboarding, credential lifecycle, webhook delivery, or money movement.

CREATE TABLE IF NOT EXISTS onboarding_drafts (
    draft_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    draft_ref TEXT NOT NULL,
    contract_version TEXT NOT NULL DEFAULT 'onboarding.v1',
    status TEXT NOT NULL DEFAULT 'DRAFT_CREATED',
    draft_version INTEGER NOT NULL DEFAULT 1,
    external_tenant_ref TEXT NOT NULL,
    organisation_ref TEXT NOT NULL,
    producer_ref TEXT,
    sponsor_ref TEXT,
    distributor_ref TEXT,
    campaign_code TEXT,
    opportunity_ref TEXT,
    created_by_ref TEXT NOT NULL,
    created_by_role TEXT NOT NULL,
    updated_by_ref TEXT,
    source TEXT NOT NULL DEFAULT 'ADMIN_ONBOARDING',
    correlation_id TEXT,
    safe_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    redactions JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    discarded_at TIMESTAMPTZ,
    CONSTRAINT onboarding_drafts_draft_ref_key UNIQUE (draft_ref),
    CONSTRAINT onboarding_drafts_version_positive_chk CHECK (draft_version > 0),
    CONSTRAINT onboarding_drafts_status_chk CHECK (
        status IN (
            'DRAFT_CREATED',
            'DRAFT_UPDATED',
            'VALIDATION_FAILED',
            'READY_FOR_REVIEW',
            'BLOCKED',
            'DISCARDED'
        )
    )
);

CREATE TABLE IF NOT EXISTS onboarding_draft_sections (
    section_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    draft_id UUID NOT NULL REFERENCES onboarding_drafts(draft_id),
    section_key TEXT NOT NULL,
    section_status TEXT NOT NULL DEFAULT 'DRAFT',
    section_version INTEGER NOT NULL DEFAULT 1,
    section_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    payload_hash TEXT,
    redaction_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    missing_evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
    source_warnings JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT onboarding_draft_sections_draft_section_key
        UNIQUE (draft_id, section_key),
    CONSTRAINT onboarding_draft_sections_version_positive_chk
        CHECK (section_version > 0),
    CONSTRAINT onboarding_draft_sections_section_key_chk CHECK (
        section_key IN (
            'company',
            'producer_sponsor',
            'distributor',
            'member_role',
            'campaign_opportunity',
            'webhook_api'
        )
    ),
    CONSTRAINT onboarding_draft_sections_status_chk CHECK (
        section_status IN (
            'NOT_STARTED',
            'DRAFT',
            'IN_PROGRESS',
            'READY',
            'BLOCKED',
            'UNAVAILABLE',
            'REVIEW_ONLY'
        )
    )
);

CREATE TABLE IF NOT EXISTS onboarding_draft_validation_results (
    validation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    draft_id UUID NOT NULL REFERENCES onboarding_drafts(draft_id),
    draft_version INTEGER,
    validation_scope TEXT NOT NULL,
    validation_type TEXT NOT NULL DEFAULT 'READINESS',
    validation_status TEXT NOT NULL,
    safe_error_code TEXT,
    section_key TEXT,
    field_name TEXT,
    message TEXT,
    safe_errors JSONB NOT NULL DEFAULT '[]'::jsonb,
    missing_evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
    blockers JSONB NOT NULL DEFAULT '[]'::jsonb,
    warnings JSONB NOT NULL DEFAULT '[]'::jsonb,
    readiness_preview JSONB NOT NULL DEFAULT '{}'::jsonb,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    correlation_id TEXT,
    validated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT onboarding_draft_validation_results_version_positive_chk
        CHECK (draft_version IS NULL OR draft_version > 0),
    CONSTRAINT onboarding_draft_validation_results_type_chk CHECK (
        validation_type IN (
            'FIELD',
            'CROSS_SECTION',
            'PERMISSION',
            'REFERENCE',
            'READINESS',
            'SAFETY'
        )
    ),
    CONSTRAINT onboarding_draft_validation_results_status_chk CHECK (
        validation_status IN (
            'PASSED',
            'FAILED',
            'BLOCKED',
            'WARNING'
        )
    )
);

CREATE TABLE IF NOT EXISTS onboarding_draft_idempotency_keys (
    idempotency_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    draft_id UUID REFERENCES onboarding_drafts(draft_id),
    draft_ref TEXT,
    idempotency_key_hash TEXT NOT NULL,
    scope_hash TEXT NOT NULL,
    actor_ref TEXT NOT NULL,
    external_tenant_ref TEXT NOT NULL,
    operation_type TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    response_hash TEXT,
    result_status TEXT NOT NULL,
    correlation_id TEXT,
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    CONSTRAINT onboarding_draft_idempotency_keys_scope_key
        UNIQUE (idempotency_key_hash, scope_hash),
    CONSTRAINT onboarding_draft_idempotency_keys_status_chk CHECK (
        result_status IN (
            'SUCCESS',
            'DUPLICATE',
            'CONFLICT',
            'VALIDATION_FAILED',
            'BLOCKED',
            'DENIED',
            'STALE',
            'UNSAFE'
        )
    )
);

CREATE TABLE IF NOT EXISTS onboarding_draft_audit_links (
    audit_link_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    draft_id UUID NOT NULL REFERENCES onboarding_drafts(draft_id),
    draft_ref TEXT NOT NULL,
    draft_version INTEGER,
    action_type TEXT NOT NULL,
    action_status TEXT NOT NULL,
    actor_ref TEXT NOT NULL,
    actor_role TEXT NOT NULL,
    audit_ref TEXT,
    event_ref TEXT,
    idempotency_id UUID REFERENCES onboarding_draft_idempotency_keys(idempotency_id),
    correlation_id TEXT NOT NULL,
    before_state_hash TEXT,
    after_state_hash TEXT,
    changed_sections JSONB NOT NULL DEFAULT '[]'::jsonb,
    redactions JSONB NOT NULL DEFAULT '[]'::jsonb,
    evidence_type TEXT NOT NULL,
    evidence_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT onboarding_draft_audit_links_version_positive_chk
        CHECK (draft_version IS NULL OR draft_version > 0),
    CONSTRAINT onboarding_draft_audit_links_status_chk CHECK (
        action_status IN (
            'SUCCESS',
            'VALIDATION_FAILED',
            'DUPLICATE',
            'STALE',
            'BLOCKED',
            'DENIED',
            'UNSAFE',
            'DISCARDED'
        )
    )
);

CREATE INDEX IF NOT EXISTS idx_onboarding_drafts_external_scope
    ON onboarding_drafts (
        external_tenant_ref,
        organisation_ref,
        producer_ref,
        sponsor_ref,
        distributor_ref,
        campaign_code,
        opportunity_ref
    );

CREATE UNIQUE INDEX IF NOT EXISTS idx_onboarding_drafts_active_scope
    ON onboarding_drafts (
        external_tenant_ref,
        organisation_ref,
        COALESCE(producer_ref, ''),
        COALESCE(sponsor_ref, ''),
        COALESCE(distributor_ref, ''),
        COALESCE(campaign_code, ''),
        COALESCE(opportunity_ref, '')
    )
    WHERE status <> 'DISCARDED';

CREATE INDEX IF NOT EXISTS idx_onboarding_drafts_status
    ON onboarding_drafts (status);

CREATE INDEX IF NOT EXISTS idx_onboarding_drafts_created
    ON onboarding_drafts (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_onboarding_drafts_updated
    ON onboarding_drafts (updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_onboarding_drafts_correlation
    ON onboarding_drafts (correlation_id);

CREATE INDEX IF NOT EXISTS idx_onboarding_drafts_expires
    ON onboarding_drafts (expires_at);

CREATE INDEX IF NOT EXISTS idx_onboarding_draft_sections_lookup
    ON onboarding_draft_sections (draft_id, section_key);

CREATE INDEX IF NOT EXISTS idx_onboarding_draft_sections_status
    ON onboarding_draft_sections (draft_id, section_status);

CREATE INDEX IF NOT EXISTS idx_onboarding_draft_sections_payload_hash
    ON onboarding_draft_sections (payload_hash);

CREATE INDEX IF NOT EXISTS idx_onboarding_draft_sections_updated
    ON onboarding_draft_sections (updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_onboarding_draft_validation_results_lookup
    ON onboarding_draft_validation_results (draft_id, validation_scope);

CREATE INDEX IF NOT EXISTS idx_onboarding_draft_validation_results_version
    ON onboarding_draft_validation_results (draft_id, draft_version);

CREATE INDEX IF NOT EXISTS idx_onboarding_draft_validation_results_type
    ON onboarding_draft_validation_results (validation_type);

CREATE INDEX IF NOT EXISTS idx_onboarding_draft_validation_results_status
    ON onboarding_draft_validation_results (validation_status);

CREATE INDEX IF NOT EXISTS idx_onboarding_draft_validation_results_error
    ON onboarding_draft_validation_results (safe_error_code);

CREATE INDEX IF NOT EXISTS idx_onboarding_draft_validation_results_created
    ON onboarding_draft_validation_results (validated_at DESC);

CREATE INDEX IF NOT EXISTS idx_onboarding_draft_validation_results_correlation
    ON onboarding_draft_validation_results (correlation_id);

CREATE INDEX IF NOT EXISTS idx_onboarding_draft_idempotency_keys_key
    ON onboarding_draft_idempotency_keys (idempotency_key_hash);

CREATE INDEX IF NOT EXISTS idx_onboarding_draft_idempotency_keys_actor_scope
    ON onboarding_draft_idempotency_keys (actor_ref, external_tenant_ref);

CREATE INDEX IF NOT EXISTS idx_onboarding_draft_idempotency_keys_draft
    ON onboarding_draft_idempotency_keys (draft_id);

CREATE INDEX IF NOT EXISTS idx_onboarding_draft_idempotency_keys_draft_ref
    ON onboarding_draft_idempotency_keys (draft_ref);

CREATE INDEX IF NOT EXISTS idx_onboarding_draft_idempotency_keys_request
    ON onboarding_draft_idempotency_keys (request_hash);

CREATE INDEX IF NOT EXISTS idx_onboarding_draft_idempotency_keys_correlation
    ON onboarding_draft_idempotency_keys (correlation_id);

CREATE INDEX IF NOT EXISTS idx_onboarding_draft_idempotency_keys_expires
    ON onboarding_draft_idempotency_keys (expires_at);

CREATE INDEX IF NOT EXISTS idx_onboarding_draft_audit_links_draft
    ON onboarding_draft_audit_links (draft_id);

CREATE INDEX IF NOT EXISTS idx_onboarding_draft_audit_links_draft_ref
    ON onboarding_draft_audit_links (draft_ref);

CREATE INDEX IF NOT EXISTS idx_onboarding_draft_audit_links_action
    ON onboarding_draft_audit_links (action_type);

CREATE INDEX IF NOT EXISTS idx_onboarding_draft_audit_links_status
    ON onboarding_draft_audit_links (action_status);

CREATE INDEX IF NOT EXISTS idx_onboarding_draft_audit_links_actor
    ON onboarding_draft_audit_links (actor_ref);

CREATE INDEX IF NOT EXISTS idx_onboarding_draft_audit_links_audit_ref
    ON onboarding_draft_audit_links (audit_ref);

CREATE INDEX IF NOT EXISTS idx_onboarding_draft_audit_links_event_ref
    ON onboarding_draft_audit_links (event_ref);

CREATE INDEX IF NOT EXISTS idx_onboarding_draft_audit_links_idempotency
    ON onboarding_draft_audit_links (idempotency_id);

CREATE INDEX IF NOT EXISTS idx_onboarding_draft_audit_links_correlation
    ON onboarding_draft_audit_links (correlation_id);

CREATE INDEX IF NOT EXISTS idx_onboarding_draft_audit_links_created
    ON onboarding_draft_audit_links (created_at DESC);
