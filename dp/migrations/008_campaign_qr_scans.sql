-- Campaign Domain QR scan ledger (separate migration/file in campaign domain)
CREATE TABLE IF NOT EXISTS campaign_qr_scans (
  scan_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  campaign_code      TEXT NOT NULL,
  campaign_track_id  UUID REFERENCES campaign_attributions(campaign_track_id),

  device_fingerprint TEXT,
  ip_address         TEXT,

  status             TEXT NOT NULL DEFAULT 'SCANNED',
  created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT campaign_qr_status_chk
    CHECK (status IN ('SCANNED', 'VALIDATED', 'ATTRIBUTED', 'COMPLETED', 'BLOCKED', 'INVALID', 'EXPIRED'))
);

CREATE INDEX IF NOT EXISTS idx_qr_campaign_code
  ON campaign_qr_scans (campaign_code);

CREATE INDEX IF NOT EXISTS idx_qr_campaign_track_id
  ON campaign_qr_scans (campaign_track_id);