CREATE TABLE IF NOT EXISTS fulfilment_settlement_ledger (
    settlement_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    tenant_code TEXT NOT NULL,

    reward_id UUID NOT NULL,
    audit_id UUID NOT NULL,

    provider_key TEXT NOT NULL,
    provider_reference TEXT,

    amount NUMERIC(18, 2) NOT NULL,
    currency TEXT NOT NULL DEFAULT 'ZAR',

    status TEXT NOT NULL DEFAULT 'PENDING',

    settlement_date TIMESTAMP NULL,
    settled_at TIMESTAMP NULL,
    failed_at TIMESTAMP NULL,
    reversed_at TIMESTAMP NULL,

    failure_reason TEXT NULL,
    reversal_reason TEXT NULL,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_fulfilment_settlement_status
    CHECK (
        status IN (
            'PENDING',
            'PROCESSING',
            'SETTLED',
            'FAILED',
            'REVERSED',
            'DISPUTED'
        )
    )
);

CREATE INDEX IF NOT EXISTS idx_settlement_tenant_code
ON fulfilment_settlement_ledger (tenant_code);

CREATE INDEX IF NOT EXISTS idx_settlement_reward_id
ON fulfilment_settlement_ledger (reward_id);

CREATE INDEX IF NOT EXISTS idx_settlement_audit_id
ON fulfilment_settlement_ledger (audit_id);

CREATE INDEX IF NOT EXISTS idx_settlement_provider_reference
ON fulfilment_settlement_ledger (provider_reference);

CREATE INDEX IF NOT EXISTS idx_settlement_status
ON fulfilment_settlement_ledger (status);

CREATE INDEX IF NOT EXISTS idx_settlement_provider_key
ON fulfilment_settlement_ledger (provider_key);
