ALTER TABLE platform_accounts
    ADD COLUMN IF NOT EXISTS legal_organisation_name TEXT,
    ADD COLUMN IF NOT EXISTS trading_name TEXT,
    ADD COLUMN IF NOT EXISTS registration_number TEXT;

UPDATE platform_accounts
SET legal_organisation_name = account_name
WHERE legal_organisation_name IS NULL;

ALTER TABLE platform_accounts
    ALTER COLUMN legal_organisation_name SET NOT NULL;

ALTER TABLE platform_organisations
    ADD COLUMN IF NOT EXISTS legal_organisation_name TEXT,
    ADD COLUMN IF NOT EXISTS trading_name TEXT,
    ADD COLUMN IF NOT EXISTS registration_number TEXT;

UPDATE platform_organisations
SET legal_organisation_name = organisation_name
WHERE legal_organisation_name IS NULL;

ALTER TABLE platform_organisations
    ALTER COLUMN legal_organisation_name SET NOT NULL;

CREATE INDEX IF NOT EXISTS idx_platform_accounts_registration_number
    ON platform_accounts (registration_number)
    WHERE registration_number IS NOT NULL;
