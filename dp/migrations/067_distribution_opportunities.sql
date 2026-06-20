CREATE TABLE IF NOT EXISTS distribution_opportunities (
    opportunity_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    tenant_code TEXT NOT NULL,
    sponsor_code TEXT NOT NULL,
    campaign_code TEXT,
    funding_contract_id UUID,

    opportunity_code TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    product_code TEXT,
    product_name TEXT,

    opportunity_status TEXT NOT NULL DEFAULT 'DRAFT',

    target_segments TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    target_regions TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    target_channels TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    distributor_types TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],

    commission_rule_id UUID
        REFERENCES distribution_commission_rules(rule_id),

    estimated_reward_amount NUMERIC(18,2),
    estimated_commission_amount NUMERIC(18,2),
    total_budget NUMERIC(18,2),
    remaining_budget NUMERIC(18,2),
    max_allocations INTEGER,
    remaining_allocations INTEGER,

    starts_at TIMESTAMP,
    ends_at TIMESTAMP,
    published_at TIMESTAMP,
    closed_at TIMESTAMP,

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    UNIQUE (tenant_code, opportunity_code)
);

CREATE INDEX IF NOT EXISTS idx_distribution_opportunities_tenant
ON distribution_opportunities(tenant_code);

CREATE INDEX IF NOT EXISTS idx_distribution_opportunities_sponsor
ON distribution_opportunities(sponsor_code);

CREATE INDEX IF NOT EXISTS idx_distribution_opportunities_campaign
ON distribution_opportunities(campaign_code);

CREATE INDEX IF NOT EXISTS idx_distribution_opportunities_status
ON distribution_opportunities(opportunity_status);

CREATE INDEX IF NOT EXISTS idx_distribution_opportunities_segments
ON distribution_opportunities USING GIN(target_segments);

CREATE INDEX IF NOT EXISTS idx_distribution_opportunities_regions
ON distribution_opportunities USING GIN(target_regions);

CREATE INDEX IF NOT EXISTS idx_distribution_opportunities_channels
ON distribution_opportunities USING GIN(target_channels);

CREATE INDEX IF NOT EXISTS idx_distribution_opportunities_distributor_types
ON distribution_opportunities USING GIN(distributor_types);
