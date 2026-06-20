CREATE TABLE IF NOT EXISTS referral_processing_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    referral_track_id UUID NULL,
    event_id UUID NULL,
    event_type TEXT NULL,
    occurred_at TIMESTAMP NULL,
    processed_at TIMESTAMP NOT NULL DEFAULT now(),

    processing_status TEXT NOT NULL,   -- PROCESSED / IGNORED / FAILED
    reason TEXT NULL,                  -- deduped / invalid_transition / out_of_order / error

    previous_status TEXT NULL,
    new_status TEXT NULL,

    metadata JSONB NULL
);

CREATE INDEX IF NOT EXISTS idx_referral_processing_audit_track_id
    ON referral_processing_audit (referral_track_id);

CREATE INDEX IF NOT EXISTS idx_referral_processing_audit_event_type
    ON referral_processing_audit (event_type);

CREATE INDEX IF NOT EXISTS idx_referral_processing_audit_processed_at
    ON referral_processing_audit (processed_at);