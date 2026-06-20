-- Enterprise event inbox for Hogan/IDS ingestion.
-- Stores raw source events, their normalized platform payload, and processing state.

CREATE TABLE IF NOT EXISTS enterprise_event_inbox (
    inbox_event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_code TEXT NULL,
    source_system TEXT NOT NULL,
    source_event_id TEXT NULL,
    correlation_id TEXT NULL,
    referral_track_id UUID NULL,
    event_type TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    raw_payload JSONB NOT NULL,
    normalized_payload JSONB NULL,
    payload_hash TEXT NOT NULL,
    dedupe_key TEXT NOT NULL,
    processing_status TEXT NOT NULL DEFAULT 'RECEIVED',
    processed_at TIMESTAMPTZ NULL,
    error_message TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT enterprise_event_inbox_status_chk
        CHECK (processing_status IN ('RECEIVED', 'QUEUED', 'IGNORED', 'FAILED', 'DUPLICATE'))
);

DO $$
DECLARE
    has_source_column BOOLEAN;
BEGIN
    IF EXISTS (
        SELECT 1
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public'
          AND c.relname = 'enterprise_events'
          AND c.relkind = 'r'
    ) THEN
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'enterprise_events'
              AND column_name = 'source'
        )
        INTO has_source_column;

        IF has_source_column THEN
            EXECUTE $sql$
                INSERT INTO enterprise_event_inbox (
                    tenant_code,
                    source_system,
                    source_event_id,
                    correlation_id,
                    referral_track_id,
                    event_type,
                    occurred_at,
                    received_at,
                    raw_payload,
                    payload_hash,
                    dedupe_key,
                    processing_status,
                    processed_at,
                    created_at
                )
                SELECT
                    NULL,
                    COALESCE(source, 'IDS'),
                    event_id::text,
                    referral_track_id::text,
                    referral_track_id,
                    event_type,
                    occurred_at,
                    created_at,
                    COALESCE(attributes, '{}'::jsonb),
                    event_id::text,
                    event_id::text,
                    'RECEIVED',
                    NULL,
                    created_at
                FROM enterprise_events
                ON CONFLICT (dedupe_key) DO NOTHING
            $sql$;
        ELSE
            EXECUTE $sql$
                INSERT INTO enterprise_event_inbox (
                    tenant_code,
                    source_system,
                    source_event_id,
                    correlation_id,
                    referral_track_id,
                    event_type,
                    occurred_at,
                    received_at,
                    raw_payload,
                    payload_hash,
                    dedupe_key,
                    processing_status,
                    processed_at,
                    created_at
                )
                SELECT
                    NULL,
                    'IDS',
                    event_id::text,
                    referral_track_id::text,
                    referral_track_id,
                    event_type,
                    occurred_at,
                    created_at,
                    COALESCE(attributes, '{}'::jsonb),
                    event_id::text,
                    event_id::text,
                    'RECEIVED',
                    NULL,
                    created_at
                FROM enterprise_events
                ON CONFLICT (dedupe_key) DO NOTHING
            $sql$;
        END IF;

        IF NOT EXISTS (
            SELECT 1
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public'
              AND c.relname = 'enterprise_events_legacy'
        ) THEN
            ALTER TABLE enterprise_events RENAME TO enterprise_events_legacy;
        ELSE
            ALTER TABLE enterprise_events RENAME TO enterprise_events_legacy_061;
        END IF;
    END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS ux_enterprise_event_inbox_dedupe_key
    ON enterprise_event_inbox (dedupe_key);

CREATE INDEX IF NOT EXISTS idx_enterprise_event_inbox_referral_track_id
    ON enterprise_event_inbox (referral_track_id);

CREATE INDEX IF NOT EXISTS idx_enterprise_event_inbox_source_event
    ON enterprise_event_inbox (source_system, source_event_id)
    WHERE source_event_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_enterprise_event_inbox_status
    ON enterprise_event_inbox (processing_status);

CREATE INDEX IF NOT EXISTS idx_enterprise_event_inbox_received_at
    ON enterprise_event_inbox (received_at);

CREATE OR REPLACE VIEW enterprise_events AS
SELECT
    inbox_event_id AS event_id,
    referral_track_id,
    event_type,
    occurred_at,
    raw_payload AS attributes,
    source_system AS source,
    tenant_code,
    source_event_id,
    correlation_id,
    normalized_payload,
    processing_status,
    processed_at,
    error_message,
    received_at,
    created_at,
    updated_at
FROM enterprise_event_inbox;
