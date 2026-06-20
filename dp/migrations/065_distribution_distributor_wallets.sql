CREATE TABLE IF NOT EXISTS distribution_distributor_wallets (
    wallet_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    distributor_id UUID NOT NULL
        REFERENCES distribution_distributors(distributor_id),

    tenant_code TEXT NOT NULL,
    distributor_code TEXT NOT NULL,
    currency TEXT NOT NULL DEFAULT 'ZAR',

    current_balance NUMERIC(18,2) NOT NULL DEFAULT 0,
    available_balance NUMERIC(18,2) NOT NULL DEFAULT 0,
    held_balance NUMERIC(18,2) NOT NULL DEFAULT 0,
    paid_out_balance NUMERIC(18,2) NOT NULL DEFAULT 0,
    reversed_balance NUMERIC(18,2) NOT NULL DEFAULT 0,

    status TEXT NOT NULL DEFAULT 'ACTIVE',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    UNIQUE (distributor_id, currency)
);

CREATE TABLE IF NOT EXISTS distribution_distributor_wallet_ledger (
    ledger_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    wallet_id UUID NOT NULL
        REFERENCES distribution_distributor_wallets(wallet_id),

    distributor_id UUID NOT NULL
        REFERENCES distribution_distributors(distributor_id),

    tenant_code TEXT NOT NULL,
    transaction_type TEXT NOT NULL,
    amount NUMERIC(18,2) NOT NULL,

    balance_before NUMERIC(18,2) NOT NULL,
    balance_after NUMERIC(18,2) NOT NULL,

    correlation_id TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_distribution_wallets_distributor
ON distribution_distributor_wallets(distributor_id);

CREATE INDEX IF NOT EXISTS idx_distribution_wallets_tenant
ON distribution_distributor_wallets(tenant_code);

CREATE INDEX IF NOT EXISTS idx_distribution_wallets_status
ON distribution_distributor_wallets(status);

CREATE INDEX IF NOT EXISTS idx_distribution_wallet_ledger_wallet
ON distribution_distributor_wallet_ledger(wallet_id);

CREATE INDEX IF NOT EXISTS idx_distribution_wallet_ledger_distributor
ON distribution_distributor_wallet_ledger(distributor_id);

CREATE INDEX IF NOT EXISTS idx_distribution_wallet_ledger_tenant
ON distribution_distributor_wallet_ledger(tenant_code);
