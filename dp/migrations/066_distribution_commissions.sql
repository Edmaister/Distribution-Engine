CREATE TABLE IF NOT EXISTS distribution_commission_rules (
    rule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    tenant_code TEXT NOT NULL,
    sponsor_code TEXT,
    campaign_code TEXT,
    distributor_type TEXT,
    commission_type TEXT NOT NULL,

    rate NUMERIC(9,6),
    fixed_amount NUMERIC(18,2),
    min_commission NUMERIC(18,2),
    max_commission NUMERIC(18,2),

    currency TEXT NOT NULL DEFAULT 'ZAR',
    rule_status TEXT NOT NULL DEFAULT 'ACTIVE',
    priority INTEGER NOT NULL DEFAULT 100,

    description TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS distribution_commission_events (
    commission_event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    tenant_code TEXT NOT NULL,
    distributor_id UUID NOT NULL
        REFERENCES distribution_distributors(distributor_id),
    distributor_code TEXT NOT NULL,
    wallet_id UUID
        REFERENCES distribution_distributor_wallets(wallet_id),
    rule_id UUID
        REFERENCES distribution_commission_rules(rule_id),

    sponsor_code TEXT,
    campaign_code TEXT,
    source_event_id TEXT,
    activity_type TEXT NOT NULL,

    sale_amount NUMERIC(18,2) NOT NULL DEFAULT 0,
    commission_amount NUMERIC(18,2) NOT NULL,
    currency TEXT NOT NULL DEFAULT 'ZAR',

    commission_status TEXT NOT NULL DEFAULT 'CALCULATED',
    credited_at TIMESTAMP,

    correlation_id TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    UNIQUE (tenant_code, source_event_id)
);

CREATE INDEX IF NOT EXISTS idx_distribution_commission_rules_tenant
ON distribution_commission_rules(tenant_code);

CREATE INDEX IF NOT EXISTS idx_distribution_commission_rules_status
ON distribution_commission_rules(rule_status);

CREATE INDEX IF NOT EXISTS idx_distribution_commission_rules_priority
ON distribution_commission_rules(priority);

CREATE INDEX IF NOT EXISTS idx_distribution_commission_events_distributor
ON distribution_commission_events(distributor_id);

CREATE INDEX IF NOT EXISTS idx_distribution_commission_events_wallet
ON distribution_commission_events(wallet_id);

CREATE INDEX IF NOT EXISTS idx_distribution_commission_events_status
ON distribution_commission_events(commission_status);
