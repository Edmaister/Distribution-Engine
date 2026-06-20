-- Preserve webhook signing material for outbound delivery workers.
-- Existing rows created before this migration must be rotated by creating a new
-- subscription because the original signing secret was only returned once.

ALTER TABLE partner_webhook_subscriptions
    ADD COLUMN IF NOT EXISTS signing_secret_value TEXT;

UPDATE partner_webhook_subscriptions
SET signing_secret_value = signing_secret_hash
WHERE signing_secret_value IS NULL;

ALTER TABLE partner_webhook_subscriptions
    ALTER COLUMN signing_secret_value SET NOT NULL;
