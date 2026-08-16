-- TASK-403: Referral runtime programme version binding
-- Stores the published programme version identity used when a referral instance
-- is created, while preserving legacy referrals with NULL runtime binding.

ALTER TABLE referral_instances
    ADD COLUMN IF NOT EXISTS programme_version_id UUID
        REFERENCES referral_saas_programme_versions(programme_version_id),
    ADD COLUMN IF NOT EXISTS programme_runtime_context JSONB NOT NULL DEFAULT '{}'::jsonb;

CREATE INDEX IF NOT EXISTS idx_referral_instances_programme_version
    ON referral_instances (tenant_code, programme_version_id);

CREATE INDEX IF NOT EXISTS idx_referral_instances_programme_runtime_context
    ON referral_instances USING GIN (programme_runtime_context);
