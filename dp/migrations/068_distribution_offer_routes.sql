CREATE TABLE IF NOT EXISTS distribution_offer_routes (
    route_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    tenant_code TEXT NOT NULL,
    opportunity_id UUID NOT NULL
        REFERENCES distribution_opportunities(opportunity_id),
    distributor_id UUID NOT NULL
        REFERENCES distribution_distributors(distributor_id),

    route_status TEXT NOT NULL DEFAULT 'ROUTED',
    route_score NUMERIC(8,2) NOT NULL DEFAULT 0,
    route_reasons JSONB NOT NULL DEFAULT '[]'::jsonb,

    routed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP,
    accepted_at TIMESTAMP,
    declined_at TIMESTAMP,

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    UNIQUE (opportunity_id, distributor_id)
);

CREATE INDEX IF NOT EXISTS idx_distribution_offer_routes_tenant
ON distribution_offer_routes(tenant_code);

CREATE INDEX IF NOT EXISTS idx_distribution_offer_routes_opportunity
ON distribution_offer_routes(opportunity_id);

CREATE INDEX IF NOT EXISTS idx_distribution_offer_routes_distributor
ON distribution_offer_routes(distributor_id);

CREATE INDEX IF NOT EXISTS idx_distribution_offer_routes_status
ON distribution_offer_routes(route_status);
