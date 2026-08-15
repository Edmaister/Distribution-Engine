-- TASK-391: governed incentive bindings for published customer journey versions.
-- This stores approved catalogue references only. It does not apply rewards,
-- award badges, score leaderboards, fund, settle, pay out, invoice, or move money.

CREATE TABLE IF NOT EXISTS referral_saas_customer_journey_incentive_bindings (
    customer_journey_incentive_binding_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES platform_accounts(account_id),
    customer_journey_version_id UUID NOT NULL
        REFERENCES referral_saas_customer_journey_versions(customer_journey_version_id),
    incentive_type TEXT NOT NULL,
    catalogue_ref TEXT NOT NULL,
    binding_status TEXT NOT NULL DEFAULT 'ACTIVE',
    binding_payload_hash TEXT NOT NULL,
    idempotency_key_hash TEXT,
    correlation_id TEXT,
    bound_by_ref TEXT NOT NULL,
    bound_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    archived_by_ref TEXT,
    archived_at TIMESTAMPTZ,
    safe_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    governance_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT referral_saas_customer_journey_incentive_type_chk
        CHECK (incentive_type IN ('REWARD_POLICY', 'MISSION', 'BADGE', 'LEADERBOARD')),
    CONSTRAINT referral_saas_customer_journey_incentive_status_chk
        CHECK (binding_status IN ('ACTIVE', 'ARCHIVED'))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_referral_saas_customer_journey_incentive_active
    ON referral_saas_customer_journey_incentive_bindings (
        account_id,
        customer_journey_version_id,
        incentive_type,
        UPPER(catalogue_ref)
    )
    WHERE binding_status = 'ACTIVE';

CREATE INDEX IF NOT EXISTS idx_referral_saas_customer_journey_incentive_version
    ON referral_saas_customer_journey_incentive_bindings (
        account_id,
        customer_journey_version_id,
        binding_status
    );
