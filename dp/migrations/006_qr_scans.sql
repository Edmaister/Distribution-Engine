-- 006_qr_scans.sql — Referral Domain (STRICT SEPARATION)
-- Purpose:
--   Store referral QR scan telemetry (device/ip/raw payload) and link it to the
--   referral_instances golden thread via referral_track_id *after validation*.
--
-- NOTE:
--   This table is telemetry/audit. Do NOT bloat referral_instances with scan fields.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS referral_qr_scans (
  scan_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- The resolved referral code (what validation uses)
  referral_code      TEXT NOT NULL,

  -- Optional: the raw QR payload as scanned (may include prefixes/params)
  qr_code            TEXT,

  -- Linkage to the validated journey (golden thread). Null until validated.
  referral_track_id  UUID REFERENCES referral_instances(referral_track_id),

  device_fingerprint TEXT,
  ip_address         TEXT,

  status             TEXT NOT NULL DEFAULT 'SCANNED',
  created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT referral_qr_status_chk
    CHECK (status IN ('SCANNED', 'VALIDATED', 'COMPLETED', 'BLOCKED', 'INVALID', 'EXPIRED'))
);

CREATE INDEX IF NOT EXISTS idx_qr_referral_code
  ON referral_qr_scans (referral_code);

CREATE INDEX IF NOT EXISTS idx_qr_referral_track_id
  ON referral_qr_scans (referral_track_id);

CREATE INDEX IF NOT EXISTS idx_qr_device_fingerprint
  ON referral_qr_scans (device_fingerprint);

CREATE INDEX IF NOT EXISTS idx_qr_ip_address
  ON referral_qr_scans (ip_address);