-- TASK-384: governed journey template and customer journey configuration schema.
-- This is storage only: it does not switch runtime journey execution.

CREATE TABLE IF NOT EXISTS referral_saas_journey_templates (
    journey_template_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_code TEXT NOT NULL UNIQUE,
    template_name TEXT NOT NULL,
    template_family TEXT NOT NULL,
    owner_scope TEXT NOT NULL DEFAULT 'AMPLIFI_GOVERNED',
    status TEXT NOT NULL DEFAULT 'DRAFT',
    safe_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    governance_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_by_ref TEXT NOT NULL,
    updated_by_ref TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    archived_at TIMESTAMPTZ,
    CONSTRAINT referral_saas_journey_templates_family_chk
        CHECK (template_family IN ('REFERRAL', 'CAMPAIGN_ATTRIBUTION', 'DISTRIBUTION', 'PARTNER', 'CUSTOM')),
    CONSTRAINT referral_saas_journey_templates_owner_scope_chk
        CHECK (owner_scope IN ('AMPLIFI_GOVERNED')),
    CONSTRAINT referral_saas_journey_templates_status_chk
        CHECK (status IN ('DRAFT', 'APPROVED', 'DISABLED', 'ARCHIVED'))
);

CREATE TABLE IF NOT EXISTS referral_saas_journey_template_versions (
    journey_template_version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    journey_template_id UUID NOT NULL REFERENCES referral_saas_journey_templates(journey_template_id),
    template_code TEXT NOT NULL,
    template_version TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'DRAFT',
    definition_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    milestone_schema JSONB NOT NULL DEFAULT '[]'::jsonb,
    transition_rules JSONB NOT NULL DEFAULT '[]'::jsonb,
    evidence_requirements JSONB NOT NULL DEFAULT '[]'::jsonb,
    allowed_configuration_schema JSONB NOT NULL DEFAULT '{}'::jsonb,
    payload_hash TEXT NOT NULL,
    approved_by_ref TEXT,
    approved_at TIMESTAMPTZ,
    created_by_ref TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    archived_at TIMESTAMPTZ,
    CONSTRAINT referral_saas_journey_template_versions_version_unique
        UNIQUE (journey_template_id, template_version),
    CONSTRAINT referral_saas_journey_template_versions_code_version_unique
        UNIQUE (template_code, template_version),
    CONSTRAINT referral_saas_journey_template_versions_status_chk
        CHECK (status IN ('DRAFT', 'APPROVED', 'DISABLED', 'ARCHIVED'))
);

CREATE TABLE IF NOT EXISTS referral_saas_customer_journey_drafts (
    customer_journey_draft_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES platform_accounts(account_id),
    journey_template_version_id UUID NOT NULL REFERENCES referral_saas_journey_template_versions(journey_template_version_id),
    draft_name TEXT NOT NULL,
    draft_status TEXT NOT NULL DEFAULT 'DRAFT',
    draft_version INTEGER NOT NULL DEFAULT 1,
    configuration_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    payload_hash TEXT NOT NULL,
    last_validation_status TEXT NOT NULL DEFAULT 'NOT_VALIDATED',
    idempotency_key_hash TEXT,
    correlation_id TEXT,
    created_by_ref TEXT NOT NULL,
    updated_by_ref TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    archived_at TIMESTAMPTZ,
    CONSTRAINT referral_saas_customer_journey_drafts_status_chk
        CHECK (draft_status IN ('DRAFT', 'VALIDATION_FAILED', 'VALIDATED', 'READY_FOR_REVIEW', 'PUBLISHED', 'DISCARDED', 'ARCHIVED')),
    CONSTRAINT referral_saas_customer_journey_drafts_validation_status_chk
        CHECK (last_validation_status IN ('NOT_VALIDATED', 'PASSED', 'PASSED_WITH_WARNINGS', 'BLOCKED'))
);

CREATE TABLE IF NOT EXISTS referral_saas_customer_journey_versions (
    customer_journey_version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES platform_accounts(account_id),
    customer_journey_draft_id UUID REFERENCES referral_saas_customer_journey_drafts(customer_journey_draft_id),
    journey_template_version_id UUID NOT NULL REFERENCES referral_saas_journey_template_versions(journey_template_version_id),
    customer_journey_code TEXT NOT NULL,
    version_number INTEGER NOT NULL,
    version_status TEXT NOT NULL DEFAULT 'PUBLISHED',
    published_configuration_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    payload_hash TEXT NOT NULL,
    published_by_ref TEXT NOT NULL,
    published_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    archived_by_ref TEXT,
    archived_at TIMESTAMPTZ,
    archive_reason TEXT,
    rollback_from_version_id UUID REFERENCES referral_saas_customer_journey_versions(customer_journey_version_id),
    safe_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    governance_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT referral_saas_customer_journey_versions_unique
        UNIQUE (account_id, customer_journey_code, version_number),
    CONSTRAINT referral_saas_customer_journey_versions_status_chk
        CHECK (version_status IN ('PUBLISHED', 'ACTIVE', 'SUPERSEDED', 'ARCHIVED'))
);

CREATE TABLE IF NOT EXISTS referral_saas_journey_validation_results (
    journey_validation_result_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES platform_accounts(account_id),
    customer_journey_draft_id UUID REFERENCES referral_saas_customer_journey_drafts(customer_journey_draft_id),
    journey_template_version_id UUID NOT NULL REFERENCES referral_saas_journey_template_versions(journey_template_version_id),
    validation_status TEXT NOT NULL,
    blockers JSONB NOT NULL DEFAULT '[]'::jsonb,
    warnings JSONB NOT NULL DEFAULT '[]'::jsonb,
    safe_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    payload_hash TEXT NOT NULL,
    idempotency_key_hash TEXT,
    correlation_id TEXT,
    validated_by_ref TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT referral_saas_journey_validation_results_status_chk
        CHECK (validation_status IN ('PASSED', 'PASSED_WITH_WARNINGS', 'BLOCKED', 'FAILED'))
);

CREATE TABLE IF NOT EXISTS referral_saas_campaign_journey_bindings (
    campaign_journey_binding_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES platform_accounts(account_id),
    campaign_code TEXT NOT NULL,
    customer_journey_version_id UUID NOT NULL REFERENCES referral_saas_customer_journey_versions(customer_journey_version_id),
    binding_status TEXT NOT NULL DEFAULT 'DRAFT',
    binding_payload_hash TEXT NOT NULL,
    idempotency_key_hash TEXT,
    correlation_id TEXT,
    bound_by_ref TEXT NOT NULL,
    bound_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    unbound_by_ref TEXT,
    unbound_at TIMESTAMPTZ,
    safe_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    governance_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT referral_saas_campaign_journey_bindings_status_chk
        CHECK (binding_status IN ('DRAFT', 'ACTIVE', 'SUPERSEDED', 'ARCHIVED'))
);

CREATE TABLE IF NOT EXISTS referral_saas_journey_configuration_idempotency_keys (
    journey_config_idempotency_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES platform_accounts(account_id),
    operation_type TEXT NOT NULL,
    idempotency_key_hash TEXT NOT NULL,
    request_payload_hash TEXT NOT NULL,
    response_payload_hash TEXT,
    resource_type TEXT NOT NULL,
    resource_id UUID,
    response_status TEXT NOT NULL,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT referral_saas_journey_config_idempotency_response_status_chk
        CHECK (response_status IN ('SUCCESS', 'REPLAY', 'CONFLICT', 'FAILED'))
);

CREATE TABLE IF NOT EXISTS referral_saas_journey_configuration_audit (
    journey_configuration_audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES platform_accounts(account_id),
    journey_template_id UUID REFERENCES referral_saas_journey_templates(journey_template_id),
    journey_template_version_id UUID REFERENCES referral_saas_journey_template_versions(journey_template_version_id),
    customer_journey_draft_id UUID REFERENCES referral_saas_customer_journey_drafts(customer_journey_draft_id),
    customer_journey_version_id UUID REFERENCES referral_saas_customer_journey_versions(customer_journey_version_id),
    campaign_journey_binding_id UUID REFERENCES referral_saas_campaign_journey_bindings(campaign_journey_binding_id),
    event_type TEXT NOT NULL,
    event_status TEXT NOT NULL,
    actor_ref TEXT NOT NULL,
    actor_role TEXT,
    previous_status TEXT,
    next_status TEXT,
    reason_code TEXT,
    correlation_id TEXT,
    idempotency_key_hash TEXT,
    evidence_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    redactions JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT referral_saas_journey_configuration_audit_status_chk
        CHECK (event_status IN ('RECORDED', 'DUPLICATE', 'DENIED', 'FAILED', 'BLOCKED'))
);

CREATE INDEX IF NOT EXISTS idx_referral_saas_journey_templates_status
    ON referral_saas_journey_templates (status, template_family);

CREATE INDEX IF NOT EXISTS idx_referral_saas_journey_template_versions_template
    ON referral_saas_journey_template_versions (journey_template_id, status);

CREATE INDEX IF NOT EXISTS idx_referral_saas_customer_journey_drafts_account
    ON referral_saas_customer_journey_drafts (account_id, draft_status);

CREATE INDEX IF NOT EXISTS idx_referral_saas_customer_journey_versions_account
    ON referral_saas_customer_journey_versions (account_id, version_status);

CREATE UNIQUE INDEX IF NOT EXISTS idx_referral_saas_customer_journey_versions_active
    ON referral_saas_customer_journey_versions (account_id, customer_journey_code)
    WHERE version_status = 'ACTIVE';

CREATE INDEX IF NOT EXISTS idx_referral_saas_journey_validation_results_draft
    ON referral_saas_journey_validation_results (customer_journey_draft_id, validation_status);

CREATE INDEX IF NOT EXISTS idx_referral_saas_campaign_journey_bindings_account
    ON referral_saas_campaign_journey_bindings (account_id, campaign_code, binding_status);

CREATE UNIQUE INDEX IF NOT EXISTS idx_referral_saas_campaign_journey_bindings_active
    ON referral_saas_campaign_journey_bindings (account_id, campaign_code)
    WHERE binding_status = 'ACTIVE';

CREATE UNIQUE INDEX IF NOT EXISTS idx_referral_saas_journey_config_idempotency_unique
    ON referral_saas_journey_configuration_idempotency_keys (
        COALESCE(account_id, '00000000-0000-0000-0000-000000000000'::uuid),
        operation_type,
        idempotency_key_hash
    );

CREATE INDEX IF NOT EXISTS idx_referral_saas_journey_configuration_audit_account
    ON referral_saas_journey_configuration_audit (account_id, created_at);

CREATE INDEX IF NOT EXISTS idx_referral_saas_journey_configuration_audit_correlation
    ON referral_saas_journey_configuration_audit (correlation_id);
