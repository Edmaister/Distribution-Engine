-- TASK-302: Persist selected-customer Referral SaaS Integrations configuration intent.
--
-- This stores safe API/webhook/message-provider setup evidence only. It does
-- not store provider secrets, create credentials, dispatch webhooks, send
-- invites, activate memberships, assign seats, change auth claims, activate
-- campaigns, trigger go-live, bill, or move money.

CREATE TABLE IF NOT EXISTS referral_saas_integration_configurations (
    integration_configuration_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES platform_accounts(account_id),
    account_tenant_id UUID REFERENCES platform_account_tenants(account_tenant_id),
    external_ref_id UUID REFERENCES platform_external_tenant_refs(external_ref_id),
    tenant_code TEXT NOT NULL REFERENCES tenants(tenant_code),
    configuration_status TEXT NOT NULL,
    api_environment JSONB NOT NULL DEFAULT '{}'::jsonb,
    webhook_intent JSONB NOT NULL DEFAULT '{}'::jsonb,
    message_providers JSONB NOT NULL DEFAULT '{}'::jsonb,
    safe_setup_posture JSONB NOT NULL DEFAULT '{}'::jsonb,
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
    CONSTRAINT referral_saas_integration_configurations_status_chk CHECK (
        configuration_status IN (
            'INTEGRATION_CONFIGURATION_SAVED',
            'INTEGRATION_CONFIGURATION_DRAFT_ONLY'
        )
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_referral_saas_integration_configurations_idem
    ON referral_saas_integration_configurations (account_id, idempotency_key_hash);

CREATE INDEX IF NOT EXISTS idx_referral_saas_integration_configurations_account
    ON referral_saas_integration_configurations (account_id, created_at DESC)
    WHERE archived_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_referral_saas_integration_configurations_tenant
    ON referral_saas_integration_configurations (tenant_code, created_at DESC)
    WHERE archived_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_referral_saas_integration_configurations_correlation
    ON referral_saas_integration_configurations (correlation_id)
    WHERE archived_at IS NULL;
