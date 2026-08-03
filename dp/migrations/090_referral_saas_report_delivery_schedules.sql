-- TASK-334: Referral SaaS scheduled report delivery API foundation.
-- This stores customer-scoped delivery schedule intent and audit evidence only.
-- It does not send email, dispatch webhooks, create credentials, change auth
-- claims, activate campaigns, create invoices, or move money.

CREATE TABLE IF NOT EXISTS referral_saas_report_delivery_schedules (
    schedule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES platform_accounts(account_id),
    account_tenant_id UUID REFERENCES platform_account_tenants(account_tenant_id),
    external_ref_id UUID REFERENCES platform_external_tenant_refs(external_ref_id),
    tenant_code TEXT NOT NULL REFERENCES tenants(tenant_code),
    report_type TEXT NOT NULL,
    campaign_ref TEXT,
    cadence TEXT NOT NULL,
    timezone TEXT NOT NULL,
    export_format TEXT NOT NULL DEFAULT 'json',
    redaction_profile TEXT NOT NULL DEFAULT 'tenant_safe',
    recipient_contact_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    retention_days INTEGER NOT NULL DEFAULT 7,
    schedule_status TEXT NOT NULL DEFAULT 'DRAFT',
    next_run_at TIMESTAMPTZ,
    last_run_at TIMESTAMPTZ,
    last_export_request_id UUID REFERENCES referral_saas_report_export_requests(export_request_id),
    last_delivery_status TEXT NOT NULL DEFAULT 'NOT_REQUESTED',
    blocked_reasons JSONB NOT NULL DEFAULT '[]'::jsonb,
    warnings JSONB NOT NULL DEFAULT '[]'::jsonb,
    guardrails JSONB NOT NULL DEFAULT '[]'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    reason_code TEXT,
    correlation_id TEXT,
    idempotency_key_hash TEXT NOT NULL,
    request_payload_hash TEXT NOT NULL,
    requested_by_ref TEXT NOT NULL,
    requested_by_role TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_referral_saas_report_delivery_cadence
        CHECK (cadence IN ('DAILY', 'WEEKLY', 'MONTHLY')),
    CONSTRAINT chk_referral_saas_report_delivery_export_format
        CHECK (export_format IN ('json', 'csv')),
    CONSTRAINT chk_referral_saas_report_delivery_redaction
        CHECK (redaction_profile = 'tenant_safe'),
    CONSTRAINT chk_referral_saas_report_delivery_retention
        CHECK (retention_days BETWEEN 1 AND 7),
    CONSTRAINT chk_referral_saas_report_delivery_schedule_status
        CHECK (schedule_status IN ('DRAFT', 'READY', 'PAUSED', 'CANCELLED', 'BLOCKED', 'FAILED')),
    CONSTRAINT chk_referral_saas_report_delivery_last_status
        CHECK (last_delivery_status IN ('NOT_REQUESTED', 'PENDING', 'DELIVERED', 'FAILED'))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_referral_saas_report_delivery_schedules_idem
    ON referral_saas_report_delivery_schedules(account_id, report_type, idempotency_key_hash);

CREATE INDEX IF NOT EXISTS idx_referral_saas_report_delivery_schedules_account
    ON referral_saas_report_delivery_schedules(account_id, report_type, schedule_status);

CREATE INDEX IF NOT EXISTS idx_referral_saas_report_delivery_schedules_tenant
    ON referral_saas_report_delivery_schedules(tenant_code, report_type, schedule_status);

CREATE INDEX IF NOT EXISTS idx_referral_saas_report_delivery_schedules_correlation
    ON referral_saas_report_delivery_schedules(correlation_id);

COMMENT ON TABLE referral_saas_report_delivery_schedules IS
    'Referral SaaS scheduled report delivery intent only. Guardrail: NO_TENANT_CODE_EXPOSURE, NO_LIVE_DELIVERY_EXECUTED, NO_EMAIL_SENT, NO_WEBHOOK_DISPATCH, NO_CREDENTIAL_OR_AUTH_CHANGE, NO_CAMPAIGN_ACTIVATION, NO_BILLING_OR_MONEY_MOVEMENT.';
