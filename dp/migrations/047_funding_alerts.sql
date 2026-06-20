CREATE TABLE IF NOT EXISTS funding_alerts (
    alert_id UUID PRIMARY KEY,
    tenant_code TEXT NOT NULL,
    account_id UUID NOT NULL REFERENCES funding_accounts(account_id),
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    alert_message TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'OPEN',
    correlation_id TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    acknowledged_at TIMESTAMP,
    resolved_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_funding_alerts_tenant
ON funding_alerts(tenant_code);

CREATE INDEX IF NOT EXISTS idx_funding_alerts_account
ON funding_alerts(account_id);

CREATE INDEX IF NOT EXISTS idx_funding_alerts_status
ON funding_alerts(status);

CREATE INDEX IF NOT EXISTS idx_funding_alerts_type
ON funding_alerts(alert_type);