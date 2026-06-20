CREATE TABLE IF NOT EXISTS distribution_route_referral_links (
    route_id UUID NOT NULL
        REFERENCES distribution_offer_routes(route_id) ON DELETE RESTRICT,
    referral_track_id UUID NOT NULL
        REFERENCES referral_instances(referral_track_id) ON DELETE RESTRICT,
    tenant_code TEXT NOT NULL,
    distributor_id UUID NOT NULL
        REFERENCES distribution_distributors(distributor_id) ON DELETE RESTRICT,
    opportunity_id UUID NOT NULL
        REFERENCES distribution_opportunities(opportunity_id) ON DELETE RESTRICT,
    link_status TEXT NOT NULL DEFAULT 'ACTIVE',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    PRIMARY KEY (route_id, referral_track_id),
    CONSTRAINT uq_distribution_route_referral UNIQUE (referral_track_id),
    CONSTRAINT chk_distribution_route_referral_status
        CHECK (link_status IN ('ACTIVE', 'VOIDED'))
);

CREATE INDEX IF NOT EXISTS idx_distribution_route_referral_links_route
ON distribution_route_referral_links(route_id);

CREATE INDEX IF NOT EXISTS idx_distribution_route_referral_links_referral
ON distribution_route_referral_links(referral_track_id);

CREATE INDEX IF NOT EXISTS idx_distribution_route_referral_links_distributor
ON distribution_route_referral_links(distributor_id);

CREATE INDEX IF NOT EXISTS idx_distribution_route_referral_links_opportunity
ON distribution_route_referral_links(opportunity_id);
