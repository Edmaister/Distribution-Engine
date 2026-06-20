CREATE TABLE IF NOT EXISTS settlement_certifications (
    certification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_code TEXT NOT NULL,
    period_id UUID NOT NULL,
    expected_amount NUMERIC(18,2) NOT NULL,
    actual_amount NUMERIC(18,2) NOT NULL,
    variance_amount NUMERIC(18,2) NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING',
    certified_by TEXT,
    certification_notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    certified_at TIMESTAMP,
    CONSTRAINT fk_settlement_certification_period
        FOREIGN KEY (period_id)
        REFERENCES settlement_periods(period_id)
);

CREATE INDEX IF NOT EXISTS idx_settlement_certifications_tenant
ON settlement_certifications(tenant_code);

CREATE INDEX IF NOT EXISTS idx_settlement_certifications_period
ON settlement_certifications(period_id);
