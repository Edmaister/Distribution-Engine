CREATE TABLE IF NOT EXISTS funding_reconciliation_runs (
    run_id UUID PRIMARY KEY,
    tenant_code TEXT NOT NULL,
    run_date TIMESTAMP NOT NULL,
    expected_amount NUMERIC(18,2) NOT NULL,
    actual_amount NUMERIC(18,2) NOT NULL,
    variance_amount NUMERIC(18,2) NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_funding_reconciliation_runs_tenant
ON funding_reconciliation_runs(tenant_code);

CREATE INDEX IF NOT EXISTS idx_funding_reconciliation_runs_status
ON funding_reconciliation_runs(status);
