-- TASK-273: Persist Referral SaaS report export requests.
--
-- This records the customer-scoped export request/audit foundation only. It
-- does not store export files, create download URLs, schedule delivery, bill,
-- expose tenant codes in public responses (NO_TENANT_CODE_EXPOSURE), or move
-- money.

CREATE TABLE IF NOT EXISTS referral_saas_report_export_requests (
    export_request_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES platform_accounts(account_id),
    account_tenant_id UUID REFERENCES platform_account_tenants(account_tenant_id),
    external_ref_id UUID REFERENCES platform_external_tenant_refs(external_ref_id),
    tenant_code TEXT NOT NULL REFERENCES tenants(tenant_code),
    report_type TEXT NOT NULL,
    export_format TEXT NOT NULL,
    redaction_profile TEXT NOT NULL,
    row_limit INTEGER NOT NULL,
    row_count INTEGER NOT NULL DEFAULT 0,
    request_status TEXT NOT NULL,
    storage_status TEXT NOT NULL,
    delivery_status TEXT NOT NULL,
    download_status TEXT NOT NULL,
    download_url TEXT,
    dimensions JSONB NOT NULL DEFAULT '[]'::jsonb,
    filters JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    redactions JSONB NOT NULL DEFAULT '[]'::jsonb,
    reason_code TEXT,
    correlation_id TEXT,
    idempotency_key_hash TEXT NOT NULL,
    request_payload_hash TEXT NOT NULL,
    requested_by_ref TEXT NOT NULL,
    requested_by_role TEXT,
    requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT referral_saas_report_export_requests_format_chk CHECK (
        export_format IN ('json', 'csv')
    ),
    CONSTRAINT referral_saas_report_export_requests_redaction_chk CHECK (
        redaction_profile = 'tenant_safe'
    ),
    CONSTRAINT referral_saas_report_export_requests_row_limit_chk CHECK (
        row_limit BETWEEN 1 AND 50000
    ),
    CONSTRAINT referral_saas_report_export_requests_row_count_chk CHECK (
        row_count >= 0
    ),
    CONSTRAINT referral_saas_report_export_requests_status_chk CHECK (
        request_status IN (
            'REQUESTED',
            'REPLAYED',
            'READY_FOR_FILE_STORAGE',
            'FAILED',
            'CANCELLED',
            'EXPIRED'
        )
    ),
    CONSTRAINT referral_saas_report_export_requests_storage_chk CHECK (
        storage_status IN ('NOT_STORED', 'PENDING', 'STORED', 'FAILED', 'EXPIRED')
    ),
    CONSTRAINT referral_saas_report_export_requests_delivery_chk CHECK (
        delivery_status IN (
            'NOT_REQUESTED',
            'PENDING',
            'DELIVERED',
            'FAILED'
        )
    ),
    CONSTRAINT referral_saas_report_export_requests_download_chk CHECK (
        download_status IN ('NOT_AVAILABLE', 'PENDING', 'AVAILABLE', 'EXPIRED')
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_referral_saas_report_export_requests_idem
    ON referral_saas_report_export_requests (
        account_id,
        report_type,
        idempotency_key_hash
    );

CREATE INDEX IF NOT EXISTS idx_referral_saas_report_export_requests_account
    ON referral_saas_report_export_requests (account_id, requested_at DESC);

CREATE INDEX IF NOT EXISTS idx_referral_saas_report_export_requests_tenant
    ON referral_saas_report_export_requests (tenant_code, requested_at DESC);

CREATE INDEX IF NOT EXISTS idx_referral_saas_report_export_requests_correlation
    ON referral_saas_report_export_requests (correlation_id);
