CREATE TABLE IF NOT EXISTS fulfilment_policies (
    fulfilment_policy_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_code TEXT NOT NULL,
    reward_type TEXT NOT NULL,
    execution_model TEXT NOT NULL,
    funding_model TEXT NOT NULL,
    settlement_model TEXT NOT NULL,
    provider_key TEXT NOT NULL,
    sla_seconds INTEGER DEFAULT 300,
    max_retries INTEGER DEFAULT 3,
    retry_backoff_seconds INTEGER DEFAULT 60,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fulfilment_policies_lookup
ON fulfilment_policies (
    tenant_code,
    reward_type,
    status
);