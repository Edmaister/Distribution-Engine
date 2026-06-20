-- Sticker-level default policies
CREATE TABLE IF NOT EXISTS cooldown_policies (
  sticker TEXT NOT NULL,
  tenant_code TEXT NOT NULL DEFAULT 'default',
  reward_amounts_json JSONB,
  product_rules_json JSONB,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

UPDATE cooldown_policies
SET tenant_code = 'default'
WHERE tenant_code IS NULL;

ALTER TABLE cooldown_policies
ALTER COLUMN tenant_code SET DEFAULT 'default',
ALTER COLUMN tenant_code SET NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS ux_cooldown_policies_sticker_tenant
ON cooldown_policies (sticker, tenant_code);
