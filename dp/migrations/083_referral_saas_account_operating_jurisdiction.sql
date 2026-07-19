-- Referral SaaS account operating jurisdiction for customer profile selection.
-- Additive only: keeps existing account foundation rows valid and avoids
-- exposing internal tenant identifiers as product selectors.

ALTER TABLE platform_accounts
    ADD COLUMN IF NOT EXISTS operating_jurisdiction_code TEXT NOT NULL DEFAULT 'ZA';

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'platform_accounts_operating_jurisdiction_chk'
    ) THEN
        ALTER TABLE platform_accounts
            ADD CONSTRAINT platform_accounts_operating_jurisdiction_chk CHECK (
                operating_jurisdiction_code IN ('ZA', 'BW', 'NA', 'ZM', 'OTHER')
            );
    END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_platform_accounts_operating_jurisdiction
    ON platform_accounts (operating_jurisdiction_code, status);
