CREATE TABLE IF NOT EXISTS settlement_exceptions (
    exception_id UUID PRIMARY KEY,
    batch_id UUID REFERENCES settlement_batches(batch_id),
    settlement_id UUID,
    exception_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'OPEN',
    exception_message TEXT,
    correlation_id TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMP,
    resolved_by TEXT
);

CREATE INDEX IF NOT EXISTS idx_settlement_exceptions_batch
ON settlement_exceptions(batch_id);

CREATE INDEX IF NOT EXISTS idx_settlement_exceptions_settlement
ON settlement_exceptions(settlement_id);

CREATE INDEX IF NOT EXISTS idx_settlement_exceptions_status
ON settlement_exceptions(status);

CREATE INDEX IF NOT EXISTS idx_settlement_exceptions_severity
ON settlement_exceptions(severity);

CREATE INDEX IF NOT EXISTS idx_settlement_exceptions_type
ON settlement_exceptions(exception_type);