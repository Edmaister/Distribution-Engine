-- TASK-402: governed programme-scoped incentive and engagement bindings.
-- This stores approved catalogue references for published programme versions only.
-- It does not apply rewards, award badges, mutate missions, score leaderboards,
-- activate campaigns, dispatch providers, create credentials, bill, settle,
-- pay out, invoice, fund, or move money.

CREATE TABLE IF NOT EXISTS referral_saas_programme_incentive_bindings (
    programme_incentive_binding_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES platform_accounts(account_id),
    programme_version_id UUID NOT NULL
        REFERENCES referral_saas_programme_versions(programme_version_id),
    binding_type TEXT NOT NULL,
    catalogue_type TEXT NOT NULL,
    catalogue_ref TEXT NOT NULL,
    catalogue_version_ref TEXT,
    effective_from DATE NOT NULL,
    effective_to DATE,
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
    CONSTRAINT referral_saas_programme_incentive_binding_type_chk
        CHECK (binding_type IN ('INCENTIVE', 'ENGAGEMENT')),
    CONSTRAINT referral_saas_programme_incentive_catalogue_type_chk
        CHECK (catalogue_type IN ('REWARD_POLICY', 'MISSION', 'BADGE', 'LEADERBOARD')),
    CONSTRAINT referral_saas_programme_incentive_status_chk
        CHECK (binding_status IN ('ACTIVE', 'ARCHIVED')),
    CONSTRAINT referral_saas_programme_incentive_effective_dates_chk
        CHECK (effective_to IS NULL OR effective_to > effective_from)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_referral_saas_programme_incentive_active
    ON referral_saas_programme_incentive_bindings (
        account_id,
        programme_version_id,
        binding_type,
        catalogue_type,
        UPPER(catalogue_ref)
    )
    WHERE binding_status = 'ACTIVE';

CREATE INDEX IF NOT EXISTS idx_referral_saas_programme_incentive_version
    ON referral_saas_programme_incentive_bindings (
        account_id,
        programme_version_id,
        binding_status
    );
