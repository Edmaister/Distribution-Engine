CREATE TABLE IF NOT EXISTS funding_limits (
    limit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_code TEXT NOT NULL,
    account_id UUID NOT NULL,
    daily_limit NUMERIC(18,2) NOT NULL DEFAULT 0,
    monthly_limit NUMERIC(18,2) NOT NULL DEFAULT 0,
    exposure_limit NUMERIC(18,2) NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_funding_limits_tenant_account
ON funding_limits (tenant_code, account_id);

CREATE INDEX IF NOT EXISTS idx_funding_limits_active
ON funding_limits (tenant_code, account_id, is_active);