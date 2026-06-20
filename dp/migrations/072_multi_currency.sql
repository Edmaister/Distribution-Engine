CREATE TABLE IF NOT EXISTS fx_rates (
    fx_rate_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_code TEXT NOT NULL,
    base_currency TEXT NOT NULL,
    quote_currency TEXT NOT NULL,
    rate NUMERIC(20,8) NOT NULL CHECK (rate > 0),
    rate_date DATE NOT NULL,
    source_system TEXT NOT NULL,
    source_reference TEXT,
    rate_status TEXT NOT NULL DEFAULT 'ACTIVE',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_fx_rates_currency_pair
        CHECK (base_currency <> quote_currency),
    CONSTRAINT uq_fx_rates_source
        UNIQUE (tenant_code, base_currency, quote_currency, rate_date, source_system, source_reference)
);

CREATE INDEX IF NOT EXISTS idx_fx_rates_tenant_pair
ON fx_rates (tenant_code, base_currency, quote_currency, rate_status, rate_date DESC);

CREATE TABLE IF NOT EXISTS currency_conversion_quotes (
    quote_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_code TEXT NOT NULL,
    source_currency TEXT NOT NULL,
    target_currency TEXT NOT NULL,
    source_amount NUMERIC(18,2) NOT NULL CHECK (source_amount > 0),
    target_amount NUMERIC(18,2) NOT NULL CHECK (target_amount >= 0),
    fx_rate_id UUID REFERENCES fx_rates(fx_rate_id),
    rate NUMERIC(20,8) NOT NULL CHECK (rate > 0),
    rate_date DATE NOT NULL,
    conversion_direction TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_currency_conversion_quotes_tenant
ON currency_conversion_quotes (tenant_code, created_at DESC);

CREATE TABLE IF NOT EXISTS cross_border_settlements (
    cross_border_settlement_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_code TEXT NOT NULL,
    settlement_id UUID,
    sponsor_code TEXT,
    distributor_id UUID,
    source_currency TEXT NOT NULL,
    target_currency TEXT NOT NULL,
    source_amount NUMERIC(18,2) NOT NULL CHECK (source_amount > 0),
    target_amount NUMERIC(18,2) NOT NULL CHECK (target_amount >= 0),
    fx_rate_id UUID REFERENCES fx_rates(fx_rate_id),
    rate NUMERIC(20,8) NOT NULL CHECK (rate > 0),
    rate_date DATE NOT NULL,
    settlement_status TEXT NOT NULL DEFAULT 'PENDING',
    corridor TEXT,
    provider_key TEXT,
    provider_reference TEXT,
    compliance_status TEXT NOT NULL DEFAULT 'PENDING',
    failure_reason TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    settled_at TIMESTAMPTZ,
    failed_at TIMESTAMPTZ,
    CONSTRAINT chk_cross_border_currency_pair
        CHECK (source_currency <> target_currency)
);

CREATE INDEX IF NOT EXISTS idx_cross_border_settlements_tenant
ON cross_border_settlements (tenant_code, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_cross_border_settlements_status
ON cross_border_settlements (settlement_status);
