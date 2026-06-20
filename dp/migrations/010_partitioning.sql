-- Optional partitioned parents + views (safe, additive). Postgres 11+.

-- enterprise_events monthly partitions by occurred_at
CREATE TABLE IF NOT EXISTS enterprise_events_p (
  event_id UUID DEFAULT gen_random_uuid(),
  referral_track_id UUID,
  event_type TEXT NOT NULL,
  occurred_at TIMESTAMPTZ NOT NULL,
  attributes JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (event_id, occurred_at)
) PARTITION BY RANGE (occurred_at);

CREATE OR REPLACE FUNCTION ensure_enterprise_events_partition(p_year INT, p_month INT) RETURNS VOID AS $$
DECLARE
  start_ts TIMESTAMPTZ := make_timestamp(p_year, p_month, 1, 0, 0, 0);
  end_ts   TIMESTAMPTZ := (start_ts + INTERVAL '1 month');
  partname TEXT := format('enterprise_events_p_%s_%s', p_year, lpad(p_month::text,2,'0'));
BEGIN
  EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF enterprise_events_p FOR VALUES FROM (%L) TO (%L)',
                 partname, start_ts, end_ts);
END; $$ LANGUAGE plpgsql;

CREATE OR REPLACE VIEW enterprise_events_v AS SELECT * FROM enterprise_events_p;

-- referral_qr_scans monthly partitions by created_at
CREATE TABLE IF NOT EXISTS referral_qr_scans_p (
  scan_id UUID DEFAULT gen_random_uuid(),
  referral_code TEXT NOT NULL,
  device_fingerprint TEXT,
  ip_address TEXT,
  status TEXT NOT NULL DEFAULT 'SCANNED',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (scan_id, created_at)
) PARTITION BY RANGE (created_at);

CREATE OR REPLACE FUNCTION ensure_qr_scans_partition(p_year INT, p_month INT) RETURNS VOID AS $$
DECLARE
  start_ts TIMESTAMPTZ := make_timestamp(p_year, p_month, 1, 0, 0, 0);
  end_ts   TIMESTAMPTZ := (start_ts + INTERVAL '1 month');
  partname TEXT := format('referral_qr_scans_p_%s_%s', p_year, lpad(p_month::text,2,'0'));
BEGIN
  EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF referral_qr_scans_p FOR VALUES FROM (%L) TO (%L)',
                 partname, start_ts, end_ts);
END; $$ LANGUAGE plpgsql;

CREATE OR REPLACE VIEW referral_qr_scans_v AS SELECT * FROM referral_qr_scans_p;
