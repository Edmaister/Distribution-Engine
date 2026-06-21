CREATE TABLE IF NOT EXISTS funding_accounts (
    account_id UUID PRIMARY KEY,
    tenant_code TEXT NOT NULL,

    account_name TEXT NOT NULL,
    account_type TEXT NOT NULL,
    currency_code TEXT NOT NULL DEFAULT 'ZAR',

    current_balance NUMERIC(18,2) NOT NULL DEFAULT 0,
    reserved_balance NUMERIC(18,2) NOT NULL DEFAULT 0,
    available_balance NUMERIC(18,2) NOT NULL DEFAULT 0,

    status TEXT NOT NULL DEFAULT 'ACTIVE',

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT funding_accounts_balance_check
        CHECK (current_balance >= 0),

    CONSTRAINT funding_accounts_reserved_check
        CHECK (reserved_balance >= 0),

    CONSTRAINT funding_accounts_available_check
        CHECK (available_balance >= 0),

    CONSTRAINT funding_accounts_balance_integrity_check
        CHECK (available_balance = current_balance - reserved_balance)
);


CREATE TABLE IF NOT EXISTS funding_transactions (
    transaction_id UUID PRIMARY KEY,

    account_id UUID NOT NULL REFERENCES funding_accounts(account_id),
    tenant_code TEXT NOT NULL,

    transaction_type TEXT NOT NULL,
    amount NUMERIC(18,2) NOT NULL,

    reference_id TEXT,
    correlation_id TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT funding_transactions_amount_check
        CHECK (amount > 0)
);


CREATE INDEX IF NOT EXISTS idx_funding_accounts_tenant
    ON funding_accounts(tenant_code);

CREATE INDEX IF NOT EXISTS idx_funding_accounts_status
    ON funding_accounts(status);

CREATE INDEX IF NOT EXISTS idx_funding_transactions_account
    ON funding_transactions(account_id);

CREATE INDEX IF NOT EXISTS idx_funding_transactions_tenant
    ON funding_transactions(tenant_code);

CREATE INDEX IF NOT EXISTS idx_funding_transactions_type
    ON funding_transactions(transaction_type);

CREATE INDEX IF NOT EXISTS idx_funding_transactions_correlation
    ON funding_transactions(correlation_id);

ALTER TABLE funding_accounts
ADD COLUMN IF NOT EXISTS account_code TEXT,
ADD COLUMN IF NOT EXISTS funding_scope TEXT,
ADD COLUMN IF NOT EXISTS segment_code TEXT,
ADD COLUMN IF NOT EXISTS campaign_code TEXT,
ADD COLUMN IF NOT EXISTS sponsor_code TEXT,
ADD COLUMN IF NOT EXISTS priority INTEGER NOT NULL DEFAULT 100;
