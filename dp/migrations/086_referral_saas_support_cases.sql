-- TASK-297: Persist selected-customer Referral SaaS support cases.
--
-- This adds the support-case foundation only. It does not repair, replay,
-- retry, requeue, mutate referral/campaign/progress/attribution/report/access
-- state, create exports, deliver invites, create credentials, change auth
-- claims, bill, or move money.

CREATE TABLE IF NOT EXISTS referral_saas_support_cases (
    support_case_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES platform_accounts(account_id),
    account_tenant_id UUID REFERENCES platform_account_tenants(account_tenant_id),
    external_ref_id UUID REFERENCES platform_external_tenant_refs(external_ref_id),
    tenant_code TEXT NOT NULL REFERENCES tenants(tenant_code),
    category TEXT NOT NULL,
    priority TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'OPEN',
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    source_surface TEXT,
    assignee_ref TEXT,
    reason_code TEXT,
    correlation_id TEXT,
    idempotency_key_hash TEXT NOT NULL,
    request_payload_hash TEXT NOT NULL,
    created_by_ref TEXT NOT NULL,
    created_by_role TEXT,
    updated_by_ref TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    redactions JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    closed_at TIMESTAMPTZ,
    archived_at TIMESTAMPTZ,
    CONSTRAINT referral_saas_support_cases_category_chk CHECK (
        category IN (
            'VALIDATION_RECOVERY',
            'PROGRESS_DIAGNOSTIC',
            'ATTRIBUTION_REVIEW',
            'READINESS_BLOCKER',
            'REPORTING_FRESHNESS',
            'INTEGRATION_HEALTH',
            'ACCESS_SCOPE',
            'MANUAL_REVIEW_REQUIRED'
        )
    ),
    CONSTRAINT referral_saas_support_cases_priority_chk CHECK (
        priority IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')
    ),
    CONSTRAINT referral_saas_support_cases_status_chk CHECK (
        status IN ('OPEN', 'INVESTIGATING', 'WAITING', 'RESOLVED', 'CLOSED')
    ),
    CONSTRAINT referral_saas_support_cases_title_len_chk CHECK (
        char_length(title) BETWEEN 3 AND 160
    ),
    CONSTRAINT referral_saas_support_cases_summary_len_chk CHECK (
        char_length(summary) BETWEEN 3 AND 2000
    )
);

CREATE TABLE IF NOT EXISTS referral_saas_support_case_evidence_links (
    evidence_link_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    support_case_id UUID NOT NULL REFERENCES referral_saas_support_cases(support_case_id),
    account_id UUID NOT NULL REFERENCES platform_accounts(account_id),
    evidence_type TEXT NOT NULL,
    evidence_ref TEXT NOT NULL,
    safe_status TEXT,
    warning_code TEXT,
    missing_evidence_code TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    redactions JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT referral_saas_support_case_evidence_type_chk CHECK (
        evidence_type IN (
            'LINK_CODE_INSPECTION',
            'ATTRIBUTION_TRACE',
            'PROGRESS_STATUS',
            'CAMPAIGN_READINESS',
            'REPORTING_EVIDENCE',
            'TECHNICAL_SETUP',
            'PEOPLE_ACCESS',
            'OPERATOR_NOTE'
        )
    ),
    CONSTRAINT referral_saas_support_case_evidence_ref_len_chk CHECK (
        char_length(evidence_ref) BETWEEN 1 AND 256
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_referral_saas_support_cases_idem
    ON referral_saas_support_cases (account_id, idempotency_key_hash);

CREATE INDEX IF NOT EXISTS idx_referral_saas_support_cases_account
    ON referral_saas_support_cases (account_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_referral_saas_support_cases_tenant
    ON referral_saas_support_cases (tenant_code, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_referral_saas_support_cases_status
    ON referral_saas_support_cases (account_id, status, priority);

CREATE INDEX IF NOT EXISTS idx_referral_saas_support_cases_correlation
    ON referral_saas_support_cases (correlation_id);

CREATE INDEX IF NOT EXISTS idx_referral_saas_support_case_evidence_case
    ON referral_saas_support_case_evidence_links (support_case_id, created_at);
