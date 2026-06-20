-- Partner seam foundation: OAuth-style client credentials and webhook delivery queue.

CREATE TABLE IF NOT EXISTS partner_clients (
    client_id TEXT PRIMARY KEY,
    tenant_code TEXT NOT NULL,
    client_name TEXT NOT NULL,
    client_secret_hash TEXT NOT NULL,
    scopes TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT partner_clients_status_chk
        CHECK (status IN ('ACTIVE', 'SUSPENDED', 'REVOKED'))
);

CREATE INDEX IF NOT EXISTS idx_partner_clients_tenant_status
    ON partner_clients (tenant_code, status);

CREATE TABLE IF NOT EXISTS partner_access_tokens (
    token_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    access_token_hash TEXT NOT NULL UNIQUE,
    client_id TEXT NOT NULL REFERENCES partner_clients(client_id),
    tenant_code TEXT NOT NULL,
    scopes TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_partner_access_tokens_client
    ON partner_access_tokens (client_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_partner_access_tokens_active
    ON partner_access_tokens (access_token_hash, expires_at)
    WHERE revoked_at IS NULL;

CREATE TABLE IF NOT EXISTS partner_webhook_subscriptions (
    webhook_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id TEXT NOT NULL REFERENCES partner_clients(client_id),
    tenant_code TEXT NOT NULL,
    event_type TEXT NOT NULL,
    target_url TEXT NOT NULL,
    signing_secret_value TEXT NOT NULL,
    signing_secret_hash TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT partner_webhook_subscriptions_status_chk
        CHECK (status IN ('ACTIVE', 'PAUSED', 'REVOKED')),
    CONSTRAINT partner_webhook_subscriptions_url_chk
        CHECK (target_url ~* '^https://')
);

CREATE INDEX IF NOT EXISTS idx_partner_webhooks_client
    ON partner_webhook_subscriptions (client_id, status);

CREATE INDEX IF NOT EXISTS idx_partner_webhooks_event
    ON partner_webhook_subscriptions (tenant_code, event_type, status);

CREATE TABLE IF NOT EXISTS partner_webhook_deliveries (
    delivery_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    webhook_id UUID NOT NULL REFERENCES partner_webhook_subscriptions(webhook_id),
    client_id TEXT NOT NULL REFERENCES partner_clients(client_id),
    tenant_code TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    delivery_status TEXT NOT NULL DEFAULT 'PENDING',
    attempt_count INT NOT NULL DEFAULT 0,
    last_error TEXT,
    next_attempt_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT partner_webhook_deliveries_status_chk
        CHECK (delivery_status IN ('PENDING', 'SENT', 'FAILED', 'CANCELLED'))
);

CREATE INDEX IF NOT EXISTS idx_partner_webhook_deliveries_status
    ON partner_webhook_deliveries (delivery_status, next_attempt_at, created_at);

CREATE INDEX IF NOT EXISTS idx_partner_webhook_deliveries_client
    ON partner_webhook_deliveries (client_id, created_at DESC);
