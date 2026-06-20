CREATE TABLE IF NOT EXISTS reconciliation_runs (
    run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    tenant_code TEXT,
    provider_key TEXT NOT NULL,

    total_records INTEGER NOT NULL,
    matched_count INTEGER NOT NULL,
    missing_count INTEGER NOT NULL,
    duplicate_count INTEGER NOT NULL,
    overpaid_count INTEGER NOT NULL,
    underpaid_count INTEGER NOT NULL,

    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS reconciliation_results (
    result_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    run_id UUID NOT NULL
        REFERENCES reconciliation_runs(run_id),

    provider_reference TEXT,

    status TEXT NOT NULL,

    platform_amount NUMERIC(18,2),
    provider_amount NUMERIC(18,2),

    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);