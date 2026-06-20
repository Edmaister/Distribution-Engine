-- 013_progress_events.sql

-- Ensure referral_instances has a unique referral_track_id for FK support.
-- Only run this if it is not already unique.
-- ALTER TABLE referral_instances
--     ADD CONSTRAINT uq_referral_instances_referral_track_id UNIQUE (referral_track_id);

CREATE TABLE IF NOT EXISTS referral_progress_events (
    id BIGSERIAL PRIMARY KEY,
    referral_track_id UUID NOT NULL,
    event_type TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    meta JSONB NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_rpe_track_event UNIQUE (referral_track_id, event_type),

    CONSTRAINT fk_rpe_referral_track
        FOREIGN KEY (referral_track_id)
        REFERENCES referral_instances(referral_track_id)
        ON DELETE CASCADE,

    CONSTRAINT chk_rpe_event_type CHECK (
        event_type IN (
            'ACCOUNT_OPENED',
            'ACCOUNT_ACTIVATED',
            'FUNDED',
            'DEBIT_ORDER_SWITCHED',
            'SALARY_SWITCHED',
            'FIRST_TRANSACTION_COMPLETED'
        )
    )
);

ALTER TABLE referral_instances
    ADD COLUMN IF NOT EXISTS account_opened_at TIMESTAMPTZ NULL,
    ADD COLUMN IF NOT EXISTS account_activated_at TIMESTAMPTZ NULL,
    ADD COLUMN IF NOT EXISTS funded_at TIMESTAMPTZ NULL,
    ADD COLUMN IF NOT EXISTS debit_order_switched_at TIMESTAMPTZ NULL,
    ADD COLUMN IF NOT EXISTS salary_switched_at TIMESTAMPTZ NULL,
    ADD COLUMN IF NOT EXISTS first_transaction_completed_at TIMESTAMPTZ NULL;

-- Keep only if raw storage is allowed by your policy
ALTER TABLE referral_instances
    ADD COLUMN IF NOT EXISTS referee_ucn TEXT NULL,
    ADD COLUMN IF NOT EXISTS referee_account_number TEXT NULL;

ALTER TABLE referral_instances
    ADD COLUMN IF NOT EXISTS referee_ucn_hash TEXT NULL,
    ADD COLUMN IF NOT EXISTS referee_account_hash TEXT NULL,
    ADD COLUMN IF NOT EXISTS referee_account_masked TEXT NULL;

CREATE INDEX IF NOT EXISTS idx_rpe_track_id
    ON referral_progress_events(referral_track_id);

CREATE INDEX IF NOT EXISTS idx_rpe_event_type
    ON referral_progress_events(event_type);

CREATE INDEX IF NOT EXISTS idx_ri_referee_ucn
    ON referral_instances(referee_ucn);
	
ALTER TABLE referral_instances
ADD COLUMN IF NOT EXISTS product VARCHAR(100),
ADD COLUMN IF NOT EXISTS sub_product VARCHAR(100);

ALTER TABLE referral_progress_events
ADD COLUMN IF NOT EXISTS product VARCHAR(100),
ADD COLUMN IF NOT EXISTS sub_product VARCHAR(100);

BEGIN;

ALTER TABLE referral_progress_events
ADD COLUMN IF NOT EXISTS source_system VARCHAR(100),
ADD COLUMN IF NOT EXISTS source_event_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS occurred_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS event_payload_hash VARCHAR(64),
ADD COLUMN IF NOT EXISTS dedupe_key VARCHAR(64),
ADD COLUMN IF NOT EXISTS idempotency_version INT NOT NULL DEFAULT 1;

-- Backfill old rows so the new model is usable immediately
UPDATE referral_progress_events
SET
    source_system = COALESCE(source_system, 'PROGRESS_API'),
    occurred_at   = COALESCE(occurred_at, created_at, NOW())
WHERE source_system IS NULL
   OR occurred_at IS NULL;

-- If you want source_system always present from now on
ALTER TABLE referral_progress_events
ALTER COLUMN source_system SET NOT NULL;

ALTER TABLE referral_progress_events
ALTER COLUMN occurred_at SET NOT NULL;

-- Strongest key when upstream provides a real source event id
CREATE UNIQUE INDEX IF NOT EXISTS ux_progress_events_source_event
ON referral_progress_events (source_system, source_event_id)
WHERE source_event_id IS NOT NULL;

-- Main fallback / universal idempotency key
CREATE UNIQUE INDEX IF NOT EXISTS ux_progress_events_dedupe_key
ON referral_progress_events (dedupe_key);

-- Helpful lookup indexes
CREATE INDEX IF NOT EXISTS ix_progress_events_track_occurred
ON referral_progress_events (referral_track_id, occurred_at);

CREATE INDEX IF NOT EXISTS ix_progress_events_track_event_type
ON referral_progress_events (referral_track_id, event_type);

COMMIT;