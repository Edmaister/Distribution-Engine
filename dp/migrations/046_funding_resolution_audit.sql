CREATE TABLE IF NOT EXISTS funding_resolution_audit (
    audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    reward_id TEXT NOT NULL,
    tenant_code TEXT NOT NULL,

    account_id UUID NOT NULL,
    rule_id UUID,

    reward_type TEXT,
    segment_code TEXT,
    campaign_code TEXT,
    sponsor_code TEXT,

    amount NUMERIC(18,2) NOT NULL,

    correlation_id TEXT,

    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_funding_resolution_reward
ON funding_resolution_audit(reward_id);

CREATE INDEX IF NOT EXISTS idx_funding_resolution_tenant
ON funding_resolution_audit(tenant_code);

CREATE INDEX IF NOT EXISTS idx_funding_resolution_account
ON funding_resolution_audit(account_id);
