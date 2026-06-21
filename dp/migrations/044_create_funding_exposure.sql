CREATE TABLE IF NOT EXISTS funding_account_rules (
    rule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_code TEXT NOT NULL,
    account_id UUID NOT NULL REFERENCES funding_accounts(account_id),

    reward_type TEXT,
    segment_code TEXT,
    campaign_code TEXT,
    sponsor_code TEXT,

    priority INTEGER NOT NULL DEFAULT 100,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

ALTER TABLE funding_account_rules
ADD COLUMN IF NOT EXISTS funding_model TEXT NOT NULL DEFAULT 'TENANT_FUNDED';

ALTER TABLE funding_account_rules
ADD COLUMN IF NOT EXISTS sponsor_wallet_id UUID;

CREATE INDEX IF NOT EXISTS idx_funding_account_rules_funding_model
ON funding_account_rules (tenant_code, funding_model);

CREATE INDEX IF NOT EXISTS idx_funding_account_rules_sponsor_wallet
ON funding_account_rules (sponsor_wallet_id);

CREATE TABLE IF NOT EXISTS funding_exposure (
    exposure_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_code TEXT NOT NULL,
    account_id UUID NOT NULL,
    exposure_date DATE NOT NULL,

    reserved_amount NUMERIC(18,2) NOT NULL DEFAULT 0,
    settled_amount NUMERIC(18,2) NOT NULL DEFAULT 0,
    released_amount NUMERIC(18,2) NOT NULL DEFAULT 0,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT funding_exposure_amounts_check
        CHECK (
            reserved_amount >= 0
            AND settled_amount >= 0
            AND released_amount >= 0
        ),

    CONSTRAINT funding_exposure_tenant_account_date_key
        UNIQUE (tenant_code, account_id, exposure_date)
);

CREATE INDEX IF NOT EXISTS idx_funding_exposure_tenant
ON funding_exposure (tenant_code);

CREATE INDEX IF NOT EXISTS idx_funding_exposure_account
ON funding_exposure (account_id);

CREATE INDEX IF NOT EXISTS idx_funding_exposure_date
ON funding_exposure (exposure_date);
