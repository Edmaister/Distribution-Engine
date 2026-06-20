CREATE TABLE IF NOT EXISTS funding_reservations (
    reservation_id UUID PRIMARY KEY,

    reward_id TEXT NOT NULL,
    tenant_code TEXT NOT NULL,

    account_id UUID NOT NULL
        REFERENCES funding_accounts(account_id),

    amount NUMERIC(18,2) NOT NULL,

    funding_transaction_id UUID
        REFERENCES funding_transactions(transaction_id),

    status TEXT NOT NULL,

    correlation_id TEXT,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT funding_reservations_amount_check
        CHECK (amount > 0),

    CONSTRAINT funding_reservations_status_check
        CHECK (status IN ('RESERVED', 'RELEASED', 'SETTLED'))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_funding_reservations_reward
    ON funding_reservations(reward_id);

CREATE INDEX IF NOT EXISTS idx_funding_reservations_tenant
    ON funding_reservations(tenant_code);

CREATE INDEX IF NOT EXISTS idx_funding_reservations_status
    ON funding_reservations(status);

CREATE INDEX IF NOT EXISTS idx_funding_reservations_account
    ON funding_reservations(account_id);