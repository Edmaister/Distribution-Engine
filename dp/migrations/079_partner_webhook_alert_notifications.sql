-- Durable notification evidence for repeated partner webhook delivery failures.

CREATE TABLE IF NOT EXISTS partner_webhook_alert_notifications (
    notification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_code TEXT NOT NULL,
    client_id TEXT NOT NULL,
    webhook_id UUID NOT NULL REFERENCES partner_webhook_subscriptions(webhook_id),
    event_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    channel TEXT NOT NULL DEFAULT 'IN_APP',
    notification_status TEXT NOT NULL DEFAULT 'SENT',
    subject TEXT NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT partner_webhook_alert_notifications_severity_chk
        CHECK (severity IN ('NOTICE', 'WARNING', 'CRITICAL')),
    CONSTRAINT partner_webhook_alert_notifications_channel_chk
        CHECK (channel IN ('IN_APP', 'EMAIL', 'SMS', 'WEBHOOK')),
    CONSTRAINT partner_webhook_alert_notifications_status_chk
        CHECK (notification_status IN ('QUEUED', 'SENT', 'FAILED'))
);

CREATE INDEX IF NOT EXISTS idx_partner_webhook_alert_notifications_scope
    ON partner_webhook_alert_notifications (tenant_code, client_id, webhook_id, event_type, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_partner_webhook_alert_notifications_status
    ON partner_webhook_alert_notifications (notification_status, created_at DESC);
