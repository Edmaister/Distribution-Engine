CREATE TABLE IF NOT EXISTS settlement_approvals (
    approval_id UUID PRIMARY KEY,
    batch_id UUID NOT NULL REFERENCES settlement_batches(batch_id),
    approval_type TEXT NOT NULL,
    approval_status TEXT NOT NULL DEFAULT 'PENDING',
    requested_by TEXT NOT NULL,
    approved_by TEXT,
    comments TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    approved_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_settlement_approvals_batch
ON settlement_approvals(batch_id);

CREATE INDEX IF NOT EXISTS idx_settlement_approvals_status
ON settlement_approvals(approval_status);