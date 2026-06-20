-- Streamed events from enterprise systems
CREATE TABLE IF NOT EXISTS enterprise_events (
  event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  referral_track_id UUID,
  event_type TEXT NOT NULL,
  occurred_at TIMESTAMPTZ NOT NULL,
  attributes JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
