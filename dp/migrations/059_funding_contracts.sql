CREATE TABLE IF NOT EXISTS funding_contracts (
    contract_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    tenant_code TEXT NOT NULL,

    sponsor_code TEXT NOT NULL,
    sponsor_name TEXT NOT NULL,

    contract_name TEXT NOT NULL,

    contract_value NUMERIC(18,2) NOT NULL,

    committed_amount NUMERIC(18,2) NOT NULL DEFAULT 0,
    utilised_amount NUMERIC(18,2) NOT NULL DEFAULT 0,
    remaining_amount NUMERIC(18,2) NOT NULL,

    start_date DATE NOT NULL,
    end_date DATE NOT NULL,

    status TEXT NOT NULL DEFAULT 'ACTIVE',

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
