CREATE TABLE IF NOT EXISTS referral_event_failures (
    id BIGSERIAL PRIMARY KEY,
    referral_track_id UUID NULL,
    event_type VARCHAR(100) NULL,
    source_system VARCHAR(100) NOT NULL DEFAULT 'sqs',
    source_event_id VARCHAR(255) NULL,
    dedupe_key VARCHAR(255) NULL,
    failure_category VARCHAR(50) NOT NULL,
    failure_reason TEXT NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'OPEN',
    retry_count INT NOT NULL DEFAULT 1,
    payload_json JSONB NULL,
    first_failed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_failed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ NULL,
    resolution_note TEXT NULL
);

CREATE INDEX IF NOT EXISTS idx_referral_event_failures_referral_track_id
    ON referral_event_failures(referral_track_id);

CREATE INDEX IF NOT EXISTS idx_referral_event_failures_source_event_id
    ON referral_event_failures(source_event_id);

CREATE INDEX IF NOT EXISTS idx_referral_event_failures_failure_category
    ON referral_event_failures(failure_category);

CREATE INDEX IF NOT EXISTS idx_referral_event_failures_status
    ON referral_event_failures(status);

CREATE INDEX IF NOT EXISTS idx_referral_event_failures_first_failed_at
    ON referral_event_failures(first_failed_at);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'uq_referral_event_failures_source_event'
    ) THEN
        ALTER TABLE referral_event_failures
        ADD CONSTRAINT uq_referral_event_failures_source_event
        UNIQUE (source_system, source_event_id);
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'uq_referral_event_failures_dedupe_key'
    ) THEN
        ALTER TABLE referral_event_failures
        ADD CONSTRAINT uq_referral_event_failures_dedupe_key
        UNIQUE (dedupe_key);
    END IF;
END $$;
