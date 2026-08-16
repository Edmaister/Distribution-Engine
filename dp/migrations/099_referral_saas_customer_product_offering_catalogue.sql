-- TASK-407: Referral SaaS customer product/offering catalogue foundation.
-- This stores the customer's real product taxonomy separately from Amplifi
-- service packaging fields. It does not migrate programme rows, activate
-- campaigns, create referrals, apply rewards, dispatch providers, create
-- credentials, mutate auth claims, bill, settle, pay out, fund, or move money.

CREATE TABLE IF NOT EXISTS referral_saas_customer_product_lines (
    customer_product_line_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES platform_accounts(account_id),
    external_product_line_ref TEXT NOT NULL,
    product_line_name TEXT NOT NULL,
    product_line_category TEXT NOT NULL,
    operating_jurisdiction_code TEXT NOT NULL,
    lifecycle_status TEXT NOT NULL DEFAULT 'DRAFT',
    description TEXT,
    safe_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    governance_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    payload_hash TEXT NOT NULL,
    idempotency_key_hash TEXT,
    correlation_id TEXT,
    created_by_ref TEXT NOT NULL,
    updated_by_ref TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    archived_at TIMESTAMPTZ,
    CONSTRAINT referral_saas_customer_product_lines_status_chk
        CHECK (lifecycle_status IN ('DRAFT', 'ACTIVE', 'SUSPENDED', 'RETIRED', 'ARCHIVED'))
);

CREATE TABLE IF NOT EXISTS referral_saas_customer_product_offerings (
    customer_product_offering_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES platform_accounts(account_id),
    customer_product_line_id UUID NOT NULL
        REFERENCES referral_saas_customer_product_lines(customer_product_line_id),
    external_offering_ref TEXT NOT NULL,
    offering_name TEXT NOT NULL,
    offering_family TEXT,
    operating_jurisdiction_code TEXT NOT NULL,
    lifecycle_status TEXT NOT NULL DEFAULT 'DRAFT',
    description TEXT,
    safe_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    governance_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    payload_hash TEXT NOT NULL,
    idempotency_key_hash TEXT,
    correlation_id TEXT,
    created_by_ref TEXT NOT NULL,
    updated_by_ref TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    archived_at TIMESTAMPTZ,
    CONSTRAINT referral_saas_customer_product_offerings_status_chk
        CHECK (lifecycle_status IN ('DRAFT', 'ACTIVE', 'SUSPENDED', 'RETIRED', 'ARCHIVED'))
);

CREATE TABLE IF NOT EXISTS referral_saas_customer_product_catalogue_idempotency_keys (
    product_catalogue_idempotency_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES platform_accounts(account_id),
    operation_type TEXT NOT NULL,
    idempotency_key_hash TEXT NOT NULL,
    request_payload_hash TEXT NOT NULL,
    response_payload_hash TEXT,
    resource_type TEXT NOT NULL,
    resource_id UUID,
    response_status TEXT NOT NULL,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT referral_saas_customer_product_catalogue_idempotency_status_chk
        CHECK (response_status IN ('SUCCESS', 'REPLAY', 'CONFLICT', 'FAILED', 'BLOCKED'))
);

CREATE TABLE IF NOT EXISTS referral_saas_customer_product_catalogue_audit (
    product_catalogue_audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES platform_accounts(account_id),
    customer_product_line_id UUID
        REFERENCES referral_saas_customer_product_lines(customer_product_line_id),
    customer_product_offering_id UUID
        REFERENCES referral_saas_customer_product_offerings(customer_product_offering_id),
    event_type TEXT NOT NULL,
    event_status TEXT NOT NULL,
    actor_ref TEXT NOT NULL,
    actor_role TEXT,
    previous_status TEXT,
    next_status TEXT,
    reason_code TEXT,
    correlation_id TEXT,
    idempotency_key_hash TEXT,
    evidence_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    redactions JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT referral_saas_customer_product_catalogue_audit_status_chk
        CHECK (event_status IN ('RECORDED', 'DUPLICATE', 'DENIED', 'FAILED', 'BLOCKED'))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_referral_saas_customer_product_lines_active_ref
    ON referral_saas_customer_product_lines (
        account_id,
        operating_jurisdiction_code,
        UPPER(external_product_line_ref)
    )
    WHERE lifecycle_status IN ('DRAFT', 'ACTIVE', 'SUSPENDED');

CREATE INDEX IF NOT EXISTS idx_referral_saas_customer_product_lines_account
    ON referral_saas_customer_product_lines (
        account_id,
        operating_jurisdiction_code,
        lifecycle_status,
        updated_at
    );

CREATE UNIQUE INDEX IF NOT EXISTS idx_referral_saas_customer_product_offerings_active_ref
    ON referral_saas_customer_product_offerings (
        account_id,
        customer_product_line_id,
        operating_jurisdiction_code,
        UPPER(external_offering_ref)
    )
    WHERE lifecycle_status IN ('DRAFT', 'ACTIVE', 'SUSPENDED');

CREATE INDEX IF NOT EXISTS idx_referral_saas_customer_product_offerings_line
    ON referral_saas_customer_product_offerings (
        account_id,
        customer_product_line_id,
        lifecycle_status,
        updated_at
    );

CREATE UNIQUE INDEX IF NOT EXISTS idx_referral_saas_customer_product_catalogue_idempotency_unique
    ON referral_saas_customer_product_catalogue_idempotency_keys (
        operation_type,
        idempotency_key_hash,
        COALESCE(account_id, '00000000-0000-0000-0000-000000000000'::uuid)
    );

CREATE INDEX IF NOT EXISTS idx_referral_saas_customer_product_catalogue_audit_account
    ON referral_saas_customer_product_catalogue_audit (
        account_id,
        event_type,
        created_at
    );

CREATE INDEX IF NOT EXISTS idx_referral_saas_customer_product_catalogue_audit_correlation
    ON referral_saas_customer_product_catalogue_audit (
        correlation_id,
        created_at
    );
