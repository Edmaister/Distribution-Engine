-- ============================================
-- PRIVACY: AUDIT + JURISDICTION CONFIG
-- ============================================

-- Enable extension (safe to run multiple times)
CREATE EXTENSION IF NOT EXISTS pgcrypto;


-- ============================================
-- 1. PRIVACY ERASURE AUDIT TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS privacy_erasure_audit (
    audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    correlation_id UUID NOT NULL,
    tenant_code TEXT NOT NULL,
    referrer_code_id UUID,
    requested_by TEXT,
    status TEXT NOT NULL,

    referral_instances_anonymised INTEGER DEFAULT 0,
    referrer_codes_anonymised INTEGER DEFAULT 0,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);


-- Indexes (important for audit lookups)
CREATE INDEX IF NOT EXISTS idx_privacy_audit_correlation
    ON privacy_erasure_audit (correlation_id);

CREATE INDEX IF NOT EXISTS idx_privacy_audit_tenant
    ON privacy_erasure_audit (tenant_code);

CREATE INDEX IF NOT EXISTS idx_privacy_audit_created_at
    ON privacy_erasure_audit (created_at DESC);


-- ============================================
-- 2. PRIVACY JURISDICTIONS (RETENTION CONFIG)
-- ============================================
CREATE TABLE IF NOT EXISTS privacy_jurisdictions (
    tenant_code TEXT NOT NULL,
    jurisdiction_code TEXT NOT NULL,
    retention_days INTEGER NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    PRIMARY KEY (tenant_code, jurisdiction_code)
);


-- ============================================
-- 3. SEED DEFAULT DATA
-- ============================================

-- South Africa POPIA (example: 5 years)
INSERT INTO privacy_jurisdictions (
    tenant_code,
    jurisdiction_code,
    retention_days
)
VALUES
    ('FNB', 'ZA', 1825),
    ('DEFAULT', 'GLOBAL', 1825)
ON CONFLICT (tenant_code, jurisdiction_code)
DO UPDATE SET
    retention_days = EXCLUDED.retention_days,
    updated_at = now();


-- ============================================
-- 4. OPTIONAL FUTURE-PROOFING
-- ============================================

-- Status constraint (optional but recommended)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_privacy_audit_status'
    ) THEN
        ALTER TABLE privacy_erasure_audit
        ADD CONSTRAINT chk_privacy_audit_status
        CHECK (status IN ('erased', 'not_found', 'blocked', 'failed'));
    END IF;
END$$;

INSERT INTO privacy_jurisdictions (
    tenant_code,
    jurisdiction_code,
    retention_days
)
VALUES
    ('FNB', 'ZA', 1825),
    ('FNB', 'GLOBAL', 1825),
    ('DEFAULT', 'GLOBAL', 1825)
ON CONFLICT (tenant_code, jurisdiction_code)
DO UPDATE SET
    retention_days = EXCLUDED.retention_days,
    updated_at = now();