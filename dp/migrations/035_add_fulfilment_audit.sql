CREATE TABLE IF NOT EXISTS fulfilment_audit (
    audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    tenant_code TEXT NOT NULL,
    referral_track_id TEXT,
    referrer_ucn TEXT,
    referee_ucn TEXT,

    reward_type TEXT NOT NULL,
    fulfilment_provider TEXT NOT NULL,
    fulfilment_policy_id UUID,

    idempotency_key TEXT NOT NULL UNIQUE,

    status TEXT NOT NULL DEFAULT 'PENDING',
    previous_status TEXT,

    attempt_no INT NOT NULL DEFAULT 1,
    max_attempts INT NOT NULL DEFAULT 3,

    provider_reference TEXT,
    provider_status TEXT,
    provider_response JSONB,

    failure_reason TEXT,
    error_code TEXT,

    correlation_id TEXT,
    event_type TEXT,

    requested_at TIMESTAMP NOT NULL DEFAULT now(),
    processing_started_at TIMESTAMP,
    completed_at TIMESTAMP,
    failed_at TIMESTAMP,

    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);


CREATE INDEX IF NOT EXISTS idx_fulfilment_audit_lookup
ON fulfilment_audit (
    tenant_code,
    referral_track_id,
    reward_type,
    status
);

CREATE INDEX IF NOT EXISTS idx_fulfilment_audit_status_attempts
ON fulfilment_audit (
    status,
    attempt_no,
    max_attempts
);

CREATE INDEX IF NOT EXISTS idx_fulfilment_audit_correlation
ON fulfilment_audit (
    correlation_id
);

CREATE INDEX IF NOT EXISTS idx_fulfilment_audit_provider_reference
ON fulfilment_audit (
    provider_reference
);