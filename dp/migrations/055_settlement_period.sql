CREATE TABLE IF NOT EXISTS settlement_periods (
    period_id UUID PRIMARY KEY,
    tenant_code TEXT NOT NULL,
    period_code TEXT NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    status TEXT NOT NULL DEFAULT 'OPEN',
    created_by TEXT,
    closed_by TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    closed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_settlement_periods_tenant
ON settlement_periods(tenant_code);

CREATE INDEX IF NOT EXISTS idx_settlement_periods_status
ON settlement_periods(status);

CREATE UNIQUE INDEX IF NOT EXISTS idx_settlement_periods_code
ON settlement_periods(tenant_code, period_code);

ALTER TABLE fulfilment_settlement_ledger
ADD COLUMN IF NOT EXISTS period_id UUID;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_fulfilment_settlement_period'
    ) THEN
        ALTER TABLE fulfilment_settlement_ledger
        ADD CONSTRAINT fk_fulfilment_settlement_period
        FOREIGN KEY (period_id)
        REFERENCES settlement_periods(period_id);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_settlement_period_id
ON fulfilment_settlement_ledger (period_id);
