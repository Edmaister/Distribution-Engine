CREATE TABLE IF NOT EXISTS settlement_reversals (
    reversal_id UUID PRIMARY KEY,
    settlement_id UUID NOT NULL,
    tenant_code TEXT NOT NULL,
    reversal_reason TEXT NOT NULL,
    amount NUMERIC(18,2) NOT NULL,
    status TEXT NOT NULL DEFAULT 'REQUESTED',
    requested_by TEXT NOT NULL,
    approved_by TEXT,
    correlation_id TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    approved_at TIMESTAMP,
    executed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_settlement_reversals_settlement
ON settlement_reversals(settlement_id);

CREATE INDEX IF NOT EXISTS idx_settlement_reversals_tenant
ON settlement_reversals(tenant_code);

CREATE INDEX IF NOT EXISTS idx_settlement_reversals_status
ON settlement_reversals(status);

ALTER TABLE settlement_reversals
ADD COLUMN IF NOT EXISTS correlation_id TEXT;

CREATE INDEX IF NOT EXISTS idx_settlement_reversals_correlation
ON settlement_reversals(correlation_id);
