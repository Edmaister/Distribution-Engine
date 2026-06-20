CREATE TABLE IF NOT EXISTS funding_contract_ledger (
    ledger_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    contract_id UUID NOT NULL
        REFERENCES funding_contracts(contract_id),

    event_type TEXT NOT NULL,

    amount NUMERIC(18,2) NOT NULL,

    reward_id UUID,
    allocation_id UUID,

    correlation_id TEXT,

    metadata JSONB,

    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
