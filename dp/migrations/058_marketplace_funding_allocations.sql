-- migrations/phase_11_2_marketplace_funding_allocations.sql

CREATE TABLE IF NOT EXISTS marketplace_funding_allocations (
    allocation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    reward_id UUID NOT NULL,
    wallet_id UUID NOT NULL,

    tenant_code TEXT NOT NULL,
    sponsor_code TEXT NOT NULL,

    amount NUMERIC(18,2) NOT NULL CHECK (amount > 0),

    status TEXT NOT NULL DEFAULT 'RESERVED'
        CHECK (status IN ('RESERVED', 'RELEASED', 'DEBITED', 'REVERSED')),

    correlation_id TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    reserved_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    released_at TIMESTAMP WITHOUT TIME ZONE,
    debited_at TIMESTAMP WITHOUT TIME ZONE,
    reversed_at TIMESTAMP WITHOUT TIME ZONE,

    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_marketplace_funding_allocations_reward
ON marketplace_funding_allocations (reward_id);

CREATE INDEX IF NOT EXISTS ix_marketplace_funding_allocations_wallet
ON marketplace_funding_allocations (wallet_id);

CREATE INDEX IF NOT EXISTS ix_marketplace_funding_allocations_tenant_sponsor
ON marketplace_funding_allocations (tenant_code, sponsor_code);

CREATE INDEX IF NOT EXISTS ix_marketplace_funding_allocations_status
ON marketplace_funding_allocations (status);