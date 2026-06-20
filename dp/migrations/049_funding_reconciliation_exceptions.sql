CREATE TABLE IF NOT EXISTS funding_reconciliation_exceptions (
    exception_id UUID PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES funding_reconciliation_runs(run_id),
    tenant_code TEXT NOT NULL,
    exception_type TEXT NOT NULL,
    reference_id TEXT,
    expected_amount NUMERIC(18,2),
    actual_amount NUMERIC(18,2),
    variance_amount NUMERIC(18,2),
    status TEXT NOT NULL DEFAULT 'OPEN',
    correlation_id TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_funding_reconciliation_exceptions_tenant
ON funding_reconciliation_exceptions(tenant_code);

CREATE INDEX IF NOT EXISTS idx_funding_reconciliation_exceptions_status
ON funding_reconciliation_exceptions(status);

CREATE INDEX IF NOT EXISTS idx_funding_reconciliation_exceptions_run
ON funding_reconciliation_exceptions(run_id);