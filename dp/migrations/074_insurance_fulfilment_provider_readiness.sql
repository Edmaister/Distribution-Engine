-- Add journey-aware fulfilment routing so the Insurance vertical can use its
-- own provider route while existing reward-type policies remain valid fallback.

ALTER TABLE fulfilment_policies
    ADD COLUMN IF NOT EXISTS journey_code TEXT,
    ADD COLUMN IF NOT EXISTS journey_version TEXT,
    ADD COLUMN IF NOT EXISTS product_code TEXT;

CREATE INDEX IF NOT EXISTS idx_fulfilment_policies_vertical_lookup
ON fulfilment_policies (
    tenant_code,
    reward_type,
    journey_code,
    journey_version,
    product_code,
    status
);

INSERT INTO fulfilment_policies (
    tenant_code,
    reward_type,
    journey_code,
    journey_version,
    product_code,
    execution_model,
    funding_model,
    settlement_model,
    provider_key,
    sla_seconds,
    max_retries,
    retry_backoff_seconds,
    status,
    metadata,
    created_at,
    updated_at
)
VALUES (
    'FNB',
    'CASH',
    'INSURANCE_POLICY',
    'v1',
    'INSURANCE',
    'TENANT_EXECUTES',
    'PRE_FUNDED_WALLET',
    'BATCH_SETTLEMENT',
    'TENANT_INSTRUCTION_PROVIDER',
    900,
    3,
    120,
    'ACTIVE',
    '{"vertical":"INSURANCE","operating_note":"Issue tenant instruction after first premium is confirmed."}'::jsonb,
    NOW(),
    NOW()
)
ON CONFLICT DO NOTHING;
