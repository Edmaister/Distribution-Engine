-- 012_composite_scan_attempts.sql
-- Composite Domain: Scan Attempt Ledger
-- Purpose:
-- - Capture ALL token scans (QR or manual entry)
-- - Resolve to referral OR campaign OR remain UNKNOWN
-- - Provide lineage anchor for orchestrator sessions
-- - Maintain strict domain separation

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS composite_scan_attempts (
  scan_attempt_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Raw token entered or scanned
  code               TEXT NOT NULL,

  -- Determined by composite validator
  token_type         TEXT NOT NULL DEFAULT 'UNKNOWN',

  -- Domain lineage anchors (only one allowed)
  referral_track_id  UUID,
  campaign_track_id  UUID,

  -- Telemetry
  device_fingerprint TEXT,
  ip_address         TEXT,
  qr_payload         TEXT,

  -- Scan lifecycle
  status             TEXT NOT NULL DEFAULT 'SCANNED',

  created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  resolved_at        TIMESTAMPTZ,

  -- Ensure correct type mapping
  CONSTRAINT composite_scan_token_type_chk
    CHECK (token_type IN ('REFERRAL','CAMPAIGN','UNKNOWN')),

  CONSTRAINT composite_scan_status_chk
    CHECK (status IN ('SCANNED','VALIDATED','INVALID','EXPIRED','BLOCKED')),

  CONSTRAINT composite_scan_one_track_chk CHECK (
      (token_type = 'REFERRAL' AND referral_track_id IS NOT NULL AND campaign_track_id IS NULL)
   OR (token_type = 'CAMPAIGN' AND campaign_track_id IS NOT NULL AND referral_track_id IS NULL)
   OR (token_type = 'UNKNOWN'  AND referral_track_id IS NULL AND campaign_track_id IS NULL)
  )
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_composite_scan_code
  ON composite_scan_attempts (code);

CREATE INDEX IF NOT EXISTS idx_composite_scan_device
  ON composite_scan_attempts (device_fingerprint);

CREATE INDEX IF NOT EXISTS idx_composite_scan_referral_track
  ON composite_scan_attempts (referral_track_id);

CREATE INDEX IF NOT EXISTS idx_composite_scan_campaign_track
  ON composite_scan_attempts (campaign_track_id);