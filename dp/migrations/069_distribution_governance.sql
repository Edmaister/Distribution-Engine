CREATE TABLE IF NOT EXISTS distribution_compliance_reviews (
    review_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    tenant_code TEXT NOT NULL,
    distributor_id UUID NOT NULL
        REFERENCES distribution_distributors(distributor_id),
    distributor_code TEXT NOT NULL,

    review_type TEXT NOT NULL,
    review_status TEXT NOT NULL DEFAULT 'OPEN',
    review_result TEXT,

    reviewer TEXT,
    notes TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    reviewed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS distribution_disputes (
    dispute_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    tenant_code TEXT NOT NULL,
    route_id UUID
        REFERENCES distribution_offer_routes(route_id),
    opportunity_id UUID
        REFERENCES distribution_opportunities(opportunity_id),
    distributor_id UUID
        REFERENCES distribution_distributors(distributor_id),

    raised_by TEXT NOT NULL,
    reason_code TEXT NOT NULL,
    description TEXT,

    dispute_status TEXT NOT NULL DEFAULT 'OPEN',
    resolution_notes TEXT,
    resolved_by TEXT,
    resolved_at TIMESTAMP,

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS distribution_governance_audit (
    audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    tenant_code TEXT NOT NULL,
    distributor_id UUID
        REFERENCES distribution_distributors(distributor_id),
    route_id UUID
        REFERENCES distribution_offer_routes(route_id),
    dispute_id UUID
        REFERENCES distribution_disputes(dispute_id),
    compliance_review_id UUID
        REFERENCES distribution_compliance_reviews(review_id),

    action_type TEXT NOT NULL,
    reason_code TEXT,
    actor TEXT,
    notes TEXT,
    before_state JSONB NOT NULL DEFAULT '{}'::jsonb,
    after_state JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_distribution_compliance_reviews_tenant
ON distribution_compliance_reviews(tenant_code);

CREATE INDEX IF NOT EXISTS idx_distribution_compliance_reviews_distributor
ON distribution_compliance_reviews(distributor_id);

CREATE INDEX IF NOT EXISTS idx_distribution_compliance_reviews_status
ON distribution_compliance_reviews(review_status);

CREATE INDEX IF NOT EXISTS idx_distribution_disputes_tenant
ON distribution_disputes(tenant_code);

CREATE INDEX IF NOT EXISTS idx_distribution_disputes_distributor
ON distribution_disputes(distributor_id);

CREATE INDEX IF NOT EXISTS idx_distribution_disputes_route
ON distribution_disputes(route_id);

CREATE INDEX IF NOT EXISTS idx_distribution_disputes_status
ON distribution_disputes(dispute_status);

CREATE INDEX IF NOT EXISTS idx_distribution_governance_audit_tenant
ON distribution_governance_audit(tenant_code);

CREATE INDEX IF NOT EXISTS idx_distribution_governance_audit_distributor
ON distribution_governance_audit(distributor_id);

CREATE INDEX IF NOT EXISTS idx_distribution_governance_audit_action
ON distribution_governance_audit(action_type);
