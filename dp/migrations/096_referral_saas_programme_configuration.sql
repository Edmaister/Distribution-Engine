-- TASK-397: Referral SaaS programme draft/version schema foundation.
-- This stores account-scoped programme configuration only. It does not publish
-- campaigns, switch referral runtime execution, dispatch providers, create
-- credentials, mutate auth claims, bill, settle, pay out, or move money.

CREATE TABLE IF NOT EXISTS referral_saas_programme_drafts (
    programme_draft_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES platform_accounts(account_id),
    source_programme_version_id UUID,
    customer_journey_version_id UUID NOT NULL
        REFERENCES referral_saas_customer_journey_versions(customer_journey_version_id),
    programme_name TEXT NOT NULL,
    programme_description TEXT,
    operating_jurisdiction_code TEXT NOT NULL,
    product_code TEXT NOT NULL DEFAULT 'REFERRAL_SAAS',
    sub_product_code TEXT NOT NULL,
    programme_status TEXT NOT NULL DEFAULT 'DRAFT',
    draft_version INTEGER NOT NULL DEFAULT 1,
    campaign_defaults JSONB NOT NULL DEFAULT '{}'::jsonb,
    incentive_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    engagement_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    integration_readiness_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
    commercial_entitlement_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
    validation_result_id UUID,
    last_validation_status TEXT NOT NULL DEFAULT 'NOT_VALIDATED',
    review_status TEXT NOT NULL DEFAULT 'NOT_SUBMITTED',
    effective_from DATE,
    effective_to DATE,
    configuration_checksum TEXT,
    payload_hash TEXT NOT NULL,
    idempotency_key_hash TEXT,
    correlation_id TEXT,
    created_by_ref TEXT NOT NULL,
    updated_by_ref TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    archived_at TIMESTAMPTZ,
    CONSTRAINT referral_saas_programme_drafts_status_chk
        CHECK (programme_status IN ('DRAFT', 'VALIDATION_FAILED', 'VALIDATED', 'READY_FOR_REVIEW', 'APPROVED_FOR_PUBLISH', 'BLOCKED', 'DISCARDED', 'ARCHIVED')),
    CONSTRAINT referral_saas_programme_drafts_validation_status_chk
        CHECK (last_validation_status IN ('NOT_VALIDATED', 'READY', 'NEEDS_ATTENTION', 'BLOCKED', 'FAILED')),
    CONSTRAINT referral_saas_programme_drafts_review_status_chk
        CHECK (review_status IN ('NOT_SUBMITTED', 'READY_FOR_REVIEW', 'APPROVED', 'BLOCKED', 'CHANGES_REQUESTED')),
    CONSTRAINT referral_saas_programme_drafts_effective_dates_chk
        CHECK (effective_to IS NULL OR effective_from IS NULL OR effective_to > effective_from)
);

CREATE TABLE IF NOT EXISTS referral_saas_programme_versions (
    programme_version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES platform_accounts(account_id),
    programme_draft_id UUID REFERENCES referral_saas_programme_drafts(programme_draft_id),
    source_programme_version_id UUID REFERENCES referral_saas_programme_versions(programme_version_id),
    customer_journey_version_id UUID NOT NULL
        REFERENCES referral_saas_customer_journey_versions(customer_journey_version_id),
    programme_code TEXT NOT NULL,
    programme_name TEXT NOT NULL,
    programme_description TEXT,
    operating_jurisdiction_code TEXT NOT NULL,
    product_code TEXT NOT NULL DEFAULT 'REFERRAL_SAAS',
    sub_product_code TEXT NOT NULL,
    version_number INTEGER NOT NULL,
    version_status TEXT NOT NULL DEFAULT 'PUBLISHED',
    published_configuration_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
    campaign_defaults_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
    incentive_refs_snapshot JSONB NOT NULL DEFAULT '[]'::jsonb,
    engagement_refs_snapshot JSONB NOT NULL DEFAULT '[]'::jsonb,
    integration_readiness_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
    commercial_entitlement_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
    validation_result_id UUID,
    review_status TEXT NOT NULL,
    reviewed_by_ref TEXT,
    reviewed_at TIMESTAMPTZ,
    review_reason TEXT,
    effective_from DATE NOT NULL,
    effective_to DATE,
    configuration_checksum TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    published_by_ref TEXT NOT NULL,
    published_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    retired_by_ref TEXT,
    retired_at TIMESTAMPTZ,
    retirement_reason TEXT,
    rollback_from_version_id UUID REFERENCES referral_saas_programme_versions(programme_version_id),
    safe_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    governance_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT referral_saas_programme_versions_unique
        UNIQUE (account_id, programme_code, version_number),
    CONSTRAINT referral_saas_programme_versions_status_chk
        CHECK (version_status IN ('PUBLISHED', 'ACTIVE', 'RETIRED', 'ROLLBACK_READY', 'ARCHIVED')),
    CONSTRAINT referral_saas_programme_versions_review_status_chk
        CHECK (review_status IN ('APPROVED', 'POLICY_APPROVED')),
    CONSTRAINT referral_saas_programme_versions_effective_dates_chk
        CHECK (effective_to IS NULL OR effective_to > effective_from)
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'referral_saas_programme_drafts_source_version_fk'
    ) THEN
        ALTER TABLE referral_saas_programme_drafts
            ADD CONSTRAINT referral_saas_programme_drafts_source_version_fk
            FOREIGN KEY (source_programme_version_id)
            REFERENCES referral_saas_programme_versions(programme_version_id);
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS referral_saas_programme_validation_results (
    programme_validation_result_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES platform_accounts(account_id),
    programme_draft_id UUID REFERENCES referral_saas_programme_drafts(programme_draft_id),
    programme_version_id UUID REFERENCES referral_saas_programme_versions(programme_version_id),
    customer_journey_version_id UUID
        REFERENCES referral_saas_customer_journey_versions(customer_journey_version_id),
    validation_status TEXT NOT NULL,
    publish_allowed BOOLEAN NOT NULL DEFAULT FALSE,
    campaign_binding_allowed BOOLEAN NOT NULL DEFAULT FALSE,
    plain_language_summary TEXT NOT NULL,
    blockers JSONB NOT NULL DEFAULT '[]'::jsonb,
    warnings JSONB NOT NULL DEFAULT '[]'::jsonb,
    configuration_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
    guardrails JSONB NOT NULL DEFAULT '[]'::jsonb,
    payload_hash TEXT NOT NULL,
    idempotency_key_hash TEXT,
    correlation_id TEXT,
    validated_by_ref TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT referral_saas_programme_validation_results_status_chk
        CHECK (validation_status IN ('READY', 'NEEDS_ATTENTION', 'BLOCKED', 'FAILED'))
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'referral_saas_programme_drafts_validation_result_fk'
    ) THEN
        ALTER TABLE referral_saas_programme_drafts
            ADD CONSTRAINT referral_saas_programme_drafts_validation_result_fk
            FOREIGN KEY (validation_result_id)
            REFERENCES referral_saas_programme_validation_results(programme_validation_result_id);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'referral_saas_programme_versions_validation_result_fk'
    ) THEN
        ALTER TABLE referral_saas_programme_versions
            ADD CONSTRAINT referral_saas_programme_versions_validation_result_fk
            FOREIGN KEY (validation_result_id)
            REFERENCES referral_saas_programme_validation_results(programme_validation_result_id);
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS referral_saas_programme_configuration_idempotency_keys (
    programme_config_idempotency_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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
    CONSTRAINT referral_saas_programme_config_idempotency_response_status_chk
        CHECK (response_status IN ('SUCCESS', 'REPLAY', 'CONFLICT', 'FAILED', 'BLOCKED'))
);

CREATE TABLE IF NOT EXISTS referral_saas_programme_configuration_audit (
    programme_configuration_audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES platform_accounts(account_id),
    programme_draft_id UUID REFERENCES referral_saas_programme_drafts(programme_draft_id),
    programme_version_id UUID REFERENCES referral_saas_programme_versions(programme_version_id),
    programme_validation_result_id UUID
        REFERENCES referral_saas_programme_validation_results(programme_validation_result_id),
    customer_journey_version_id UUID
        REFERENCES referral_saas_customer_journey_versions(customer_journey_version_id),
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
    CONSTRAINT referral_saas_programme_configuration_audit_status_chk
        CHECK (event_status IN ('RECORDED', 'DUPLICATE', 'DENIED', 'FAILED', 'BLOCKED'))
);

CREATE INDEX IF NOT EXISTS idx_referral_saas_programme_drafts_account
    ON referral_saas_programme_drafts (account_id, programme_status, updated_at);

CREATE INDEX IF NOT EXISTS idx_referral_saas_programme_drafts_journey_version
    ON referral_saas_programme_drafts (account_id, customer_journey_version_id);

CREATE INDEX IF NOT EXISTS idx_referral_saas_programme_versions_account
    ON referral_saas_programme_versions (account_id, version_status, published_at);

CREATE UNIQUE INDEX IF NOT EXISTS idx_referral_saas_programme_versions_active
    ON referral_saas_programme_versions (account_id, programme_code)
    WHERE version_status = 'ACTIVE';

CREATE INDEX IF NOT EXISTS idx_referral_saas_programme_versions_journey_version
    ON referral_saas_programme_versions (account_id, customer_journey_version_id);

CREATE INDEX IF NOT EXISTS idx_referral_saas_programme_validation_results_draft
    ON referral_saas_programme_validation_results (programme_draft_id, validation_status);

CREATE UNIQUE INDEX IF NOT EXISTS idx_referral_saas_programme_config_idempotency_unique
    ON referral_saas_programme_configuration_idempotency_keys (
        COALESCE(account_id, '00000000-0000-0000-0000-000000000000'::uuid),
        operation_type,
        idempotency_key_hash
    );

CREATE INDEX IF NOT EXISTS idx_referral_saas_programme_configuration_audit_account
    ON referral_saas_programme_configuration_audit (account_id, created_at);

CREATE INDEX IF NOT EXISTS idx_referral_saas_programme_configuration_audit_correlation
    ON referral_saas_programme_configuration_audit (correlation_id);
