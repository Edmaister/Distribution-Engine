ALTER TABLE rewards
ADD COLUMN IF NOT EXISTS tenant_code TEXT;

UPDATE rewards
SET tenant_code = 'FNB'
WHERE tenant_code IS NULL;

ALTER TABLE rewards
ALTER COLUMN tenant_code SET NOT NULL;
