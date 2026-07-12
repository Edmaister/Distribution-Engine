ALTER TABLE IF EXISTS funding_reconciliation_runs
ADD COLUMN IF NOT EXISTS correlation_id TEXT;

CREATE INDEX IF NOT EXISTS idx_funding_reconciliation_runs_correlation
ON funding_reconciliation_runs(correlation_id);
