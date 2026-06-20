CREATE TABLE IF NOT EXISTS tenants (
    tenant_code TEXT PRIMARY KEY,
    tenant_name TEXT NOT NULL,
    industry TEXT NOT NULL, -- banking, telco, retail, insurance
    currency TEXT DEFAULT 'ZAR',
    locale TEXT DEFAULT 'en-ZA',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

ALTER TABLE referral_instances
ADD COLUMN IF NOT EXISTS tenant_code TEXT;

UPDATE referral_instances
SET tenant_code = 'FNB'
WHERE tenant_code IS NULL;

ALTER TABLE referral_instances
ALTER COLUMN tenant_code SET NOT NULL;

CREATE INDEX IF NOT EXISTS idx_referral_instances_tenant_track
ON referral_instances (tenant_code, referral_track_id);
