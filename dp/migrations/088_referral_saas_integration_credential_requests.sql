-- TASK-315: Persist selected-customer Referral SaaS Integrations credential requests.
--
-- This stores credential lifecycle request intent and review posture only. It
-- does not store provider secrets, create API keys, create signing material,
-- call providers, dispatch webhooks, send messages, activate memberships,
-- assign seats, change auth claims, activate campaigns, trigger go-live, bill,
-- or move money.
-- Guardrail evidence: no_secret_or_credential_storage,
-- no_credential_lifecycle_execution, no_vault_write, no_provider_call.

CREATE TABLE IF NOT EXISTS referral_saas_integration_credential_requests (
    integration_credential_request_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES platform_accounts(account_id),
    account_tenant_id UUID REFERENCES platform_account_tenants(account_tenant_id),
    external_ref_id UUID REFERENCES platform_external_tenant_refs(external_ref_id),
    tenant_code TEXT NOT NULL REFERENCES tenants(tenant_code),
    integration_configuration_id UUID NOT NULL REFERENCES referral_saas_integration_configurations(integration_configuration_id),
    credential_request_status TEXT NOT NULL,
    review_status TEXT NOT NULL,
    request_type TEXT NOT NULL,
    capability TEXT NOT NULL,
    environment TEXT NOT NULL,
    intended_use JSONB NOT NULL DEFAULT '[]'::jsonb,
    requested_for JSONB NOT NULL DEFAULT '{}'::jsonb,
    safe_request_posture JSONB NOT NULL DEFAULT '{}'::jsonb,
    reason_code TEXT,
    correlation_id TEXT,
    idempotency_key_hash TEXT NOT NULL,
    request_payload_hash TEXT NOT NULL,
    created_by_ref TEXT NOT NULL,
    created_by_role TEXT,
    updated_by_ref TEXT,
    redactions JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    archived_at TIMESTAMPTZ,
    CONSTRAINT referral_saas_integration_credential_requests_status_chk CHECK (
        credential_request_status IN (
            'CREDENTIAL_REQUEST_RECORDED',
            'CREDENTIAL_REQUEST_READY_FOR_REVIEW'
        )
    ),
    CONSTRAINT referral_saas_integration_credential_requests_review_chk CHECK (
        review_status IN (
            'READY_FOR_REVIEW',
            'REVIEW_APPROVED',
            'REVIEW_REJECTED',
            'REVIEW_CANCELLED'
        )
    ),
    CONSTRAINT referral_saas_integration_credential_requests_type_chk CHECK (
        request_type IN (
            'API_KEY_CREATE',
            'API_KEY_ROTATE',
            'API_KEY_REVOKE',
            'WEBHOOK_SIGNING_KEY_CREATE',
            'WEBHOOK_SIGNING_KEY_ROTATE',
            'PROVIDER_CREDENTIAL_REFERENCE_CREATE'
        )
    ),
    CONSTRAINT referral_saas_integration_credential_requests_env_chk CHECK (
        environment IN ('SANDBOX', 'STAGING', 'PRODUCTION')
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_referral_saas_credential_requests_idempotency
    ON referral_saas_integration_credential_requests (account_id, idempotency_key_hash);

CREATE INDEX IF NOT EXISTS idx_referral_saas_credential_requests_account
    ON referral_saas_integration_credential_requests (account_id, created_at DESC)
    WHERE archived_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_referral_saas_integration_credential_requests_config
    ON referral_saas_integration_credential_requests (integration_configuration_id, created_at DESC)
    WHERE archived_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_referral_saas_integration_credential_requests_tenant
    ON referral_saas_integration_credential_requests (tenant_code, created_at DESC)
    WHERE archived_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_referral_saas_integration_credential_requests_correlation
    ON referral_saas_integration_credential_requests (correlation_id)
    WHERE archived_at IS NULL;
