CREATE TABLE IF NOT EXISTS reconciliation_exceptions (
    exception_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    result_id UUID,
    run_id UUID NOT NULL,

    provider_reference TEXT,
    exception_type TEXT NOT NULL,

    status TEXT NOT NULL DEFAULT 'OPEN',

    assigned_to TEXT,
    resolution_notes TEXT,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMP NULL,

    CONSTRAINT chk_reconciliation_exception_status
    CHECK (
        status IN (
            'OPEN',
            'ASSIGNED',
            'IN_REVIEW',
            'RESOLVED',
            'REOPENED'
        )
    )
);