-- TASK-364: expiring invitation acceptance links for Referral SaaS.
-- Raw acceptance tokens are never stored; only a SHA-256 hash and short hint remain.

CREATE TABLE IF NOT EXISTS referral_saas_membership_acceptance_tokens (
    acceptance_token_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES platform_accounts(account_id),
    membership_id UUID NOT NULL REFERENCES platform_memberships(membership_id),
    tenant_code TEXT REFERENCES tenants(tenant_code),
    token_hash TEXT NOT NULL UNIQUE,
    token_hint TEXT NOT NULL,
    accepted_subject_ref TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ISSUED',
    expires_at TIMESTAMPTZ NOT NULL,
    accepted_at TIMESTAMPTZ,
    expired_at TIMESTAMPTZ,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT referral_saas_membership_acceptance_tokens_status_chk
        CHECK (status IN ('ISSUED', 'ACCEPTED', 'EXPIRED', 'REVOKED'))
);

CREATE INDEX IF NOT EXISTS idx_referral_saas_acceptance_tokens_membership
    ON referral_saas_membership_acceptance_tokens (account_id, membership_id, status);

CREATE INDEX IF NOT EXISTS idx_referral_saas_acceptance_tokens_expiry
    ON referral_saas_membership_acceptance_tokens (status, expires_at);
