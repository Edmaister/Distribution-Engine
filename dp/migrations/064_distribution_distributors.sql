CREATE TABLE IF NOT EXISTS distribution_distributors (
    distributor_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    tenant_code TEXT NOT NULL,
    distributor_code TEXT NOT NULL,
    distributor_name TEXT NOT NULL,
    distributor_type TEXT NOT NULL,

    status TEXT NOT NULL DEFAULT 'ONBOARDING',

    contact_email TEXT,
    contact_phone TEXT,

    channels TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    segments TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    regions TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],

    capabilities JSONB NOT NULL DEFAULT '{}'::jsonb,
    eligibility JSONB NOT NULL DEFAULT '{}'::jsonb,
    operating_limits JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    status_changed_at TIMESTAMP NOT NULL DEFAULT NOW(),

    UNIQUE (tenant_code, distributor_code)
);

CREATE INDEX IF NOT EXISTS idx_distribution_distributors_tenant
ON distribution_distributors(tenant_code);

CREATE INDEX IF NOT EXISTS idx_distribution_distributors_status
ON distribution_distributors(status);

CREATE INDEX IF NOT EXISTS idx_distribution_distributors_type
ON distribution_distributors(distributor_type);

CREATE INDEX IF NOT EXISTS idx_distribution_distributors_segments
ON distribution_distributors USING GIN(segments);

CREATE INDEX IF NOT EXISTS idx_distribution_distributors_regions
ON distribution_distributors USING GIN(regions);
