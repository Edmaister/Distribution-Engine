CREATE TABLE IF NOT EXISTS settlement_batches (
    batch_id UUID PRIMARY KEY,
    tenant_code TEXT NOT NULL,
    batch_reference TEXT NOT NULL,
    batch_type TEXT NOT NULL,
    status TEXT NOT NULL,
    total_count INTEGER NOT NULL,
    total_amount NUMERIC(18,2) NOT NULL,
    created_by TEXT,
    approved_by TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    approved_at TIMESTAMP,
    settled_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_settlement_batches_tenant
ON settlement_batches(tenant_code);

CREATE INDEX IF NOT EXISTS idx_settlement_batches_status
ON settlement_batches(status);
