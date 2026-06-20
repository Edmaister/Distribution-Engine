CREATE TABLE IF NOT EXISTS sponsor_wallets (
    wallet_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    tenant_code TEXT NOT NULL,
    sponsor_code TEXT NOT NULL,
    sponsor_name TEXT NOT NULL,

    currency TEXT NOT NULL DEFAULT 'ZAR',

    current_balance NUMERIC(18,2) NOT NULL DEFAULT 0,
    reserved_balance NUMERIC(18,2) NOT NULL DEFAULT 0,

    status TEXT NOT NULL DEFAULT 'ACTIVE',

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    UNIQUE (tenant_code, sponsor_code, currency)
);

CREATE TABLE IF NOT EXISTS sponsor_wallet_ledger (
    ledger_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    wallet_id UUID NOT NULL REFERENCES sponsor_wallets(wallet_id),
    tenant_code TEXT NOT NULL,

    transaction_type TEXT NOT NULL,
    amount NUMERIC(18,2) NOT NULL,

    balance_before NUMERIC(18,2) NOT NULL,
    balance_after NUMERIC(18,2) NOT NULL,

    correlation_id TEXT,
    metadata JSONB,

    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sponsor_wallets_tenant
ON sponsor_wallets (tenant_code);

CREATE INDEX IF NOT EXISTS idx_sponsor_wallets_sponsor
ON sponsor_wallets (tenant_code, sponsor_code);

CREATE INDEX IF NOT EXISTS idx_sponsor_wallet_ledger_wallet
ON sponsor_wallet_ledger (wallet_id);

CREATE INDEX IF NOT EXISTS idx_sponsor_wallet_ledger_tenant
ON sponsor_wallet_ledger (tenant_code);

CREATE INDEX IF NOT EXISTS idx_sponsor_wallet_ledger_created
ON sponsor_wallet_ledger (created_at);