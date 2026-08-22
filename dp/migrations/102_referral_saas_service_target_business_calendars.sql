-- TASK-438: Persist governed Referral SaaS service-target business calendars.
-- No calendars or working hours are seeded. Calendar-backed clocks remain
-- unavailable until later tasks add calculation, governance, and resolution.

CREATE TABLE IF NOT EXISTS referral_saas_service_target_calendar_versions (
    service_target_calendar_version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    calendar_code TEXT NOT NULL,
    version_number INTEGER NOT NULL,
    scope_type TEXT NOT NULL DEFAULT 'GLOBAL',
    account_id UUID REFERENCES platform_accounts(account_id),
    calendar_name TEXT NOT NULL,
    business_timezone TEXT NOT NULL,
    lifecycle_status TEXT NOT NULL DEFAULT 'DRAFT',
    effective_from TIMESTAMPTZ NOT NULL,
    effective_to TIMESTAMPTZ,
    created_by_ref TEXT NOT NULL,
    reviewed_by_ref TEXT,
    reviewed_at TIMESTAMPTZ,
    approved_by_ref TEXT,
    approved_at TIMESTAMPTZ,
    correlation_id TEXT NOT NULL,
    idempotency_key_hash TEXT NOT NULL,
    request_payload_hash TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    redactions JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    retired_at TIMESTAMPTZ,
    CONSTRAINT referral_saas_service_target_calendar_version_ck CHECK (version_number > 0),
    CONSTRAINT referral_saas_service_target_calendar_scope_ck CHECK (
        (scope_type = 'GLOBAL' AND account_id IS NULL)
        OR (scope_type = 'ACCOUNT' AND account_id IS NOT NULL)
    ),
    CONSTRAINT referral_saas_service_target_calendar_lifecycle_ck CHECK (
        lifecycle_status IN ('DRAFT', 'IN_REVIEW', 'APPROVED', 'RETIRED')
    ),
    CONSTRAINT referral_saas_service_target_calendar_window_ck CHECK (
        effective_to IS NULL OR effective_to > effective_from
    ),
    CONSTRAINT referral_saas_service_target_calendar_redactions_ck CHECK (
        jsonb_typeof(redactions) = 'array'
    )
);

CREATE TABLE IF NOT EXISTS referral_saas_service_target_calendar_weekly_intervals (
    service_target_calendar_weekly_interval_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_target_calendar_version_id UUID NOT NULL
        REFERENCES referral_saas_service_target_calendar_versions(service_target_calendar_version_id),
    local_day_of_week SMALLINT NOT NULL,
    local_start_time TIME NOT NULL,
    local_end_time TIME NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT referral_saas_service_target_calendar_day_ck CHECK (
        local_day_of_week BETWEEN 1 AND 7
    ),
    CONSTRAINT referral_saas_service_target_calendar_weekly_interval_ck CHECK (
        local_start_time < local_end_time
    ),
    UNIQUE (
        service_target_calendar_version_id,
        local_day_of_week,
        local_start_time,
        local_end_time
    )
);

CREATE TABLE IF NOT EXISTS referral_saas_service_target_calendar_date_exceptions (
    service_target_calendar_date_exception_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_target_calendar_version_id UUID NOT NULL
        REFERENCES referral_saas_service_target_calendar_versions(service_target_calendar_version_id),
    local_date DATE NOT NULL,
    exception_type TEXT NOT NULL,
    local_start_time TIME,
    local_end_time TIME,
    reason_code TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT referral_saas_service_target_calendar_exception_type_ck CHECK (
        exception_type IN ('CLOSED', 'WORKING_INTERVAL')
    ),
    CONSTRAINT referral_saas_service_target_calendar_exception_times_ck CHECK (
        (exception_type = 'CLOSED'
            AND local_start_time IS NULL
            AND local_end_time IS NULL)
        OR (exception_type = 'WORKING_INTERVAL'
            AND local_start_time IS NOT NULL
            AND local_end_time IS NOT NULL
            AND local_start_time < local_end_time)
    ),
    UNIQUE (
        service_target_calendar_version_id,
        local_date,
        exception_type,
        local_start_time,
        local_end_time
    )
);

CREATE TABLE IF NOT EXISTS referral_saas_service_target_calendar_audit (
    service_target_calendar_audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_target_calendar_version_id UUID NOT NULL
        REFERENCES referral_saas_service_target_calendar_versions(service_target_calendar_version_id),
    account_id UUID REFERENCES platform_accounts(account_id),
    event_type TEXT NOT NULL,
    event_status TEXT NOT NULL,
    actor_ref TEXT NOT NULL,
    actor_role TEXT NOT NULL,
    reason_code TEXT,
    correlation_id TEXT NOT NULL,
    idempotency_key_hash TEXT NOT NULL,
    request_payload_hash TEXT NOT NULL,
    evidence_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    redactions JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT referral_saas_service_target_calendar_audit_status_ck CHECK (
        event_status IN ('RECORDED', 'REPLAY', 'DENIED', 'FAILED', 'BLOCKED')
    ),
    CONSTRAINT referral_saas_service_target_calendar_audit_redactions_ck CHECK (
        jsonb_typeof(redactions) = 'array'
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_referral_saas_service_target_calendar_version
    ON referral_saas_service_target_calendar_versions (
        UPPER(calendar_code),
        version_number,
        scope_type,
        COALESCE(account_id, '00000000-0000-0000-0000-000000000000'::uuid)
    );

CREATE UNIQUE INDEX IF NOT EXISTS idx_referral_saas_service_target_calendar_idempotency
    ON referral_saas_service_target_calendar_versions (idempotency_key_hash);

CREATE INDEX IF NOT EXISTS idx_referral_saas_service_target_calendar_resolution
    ON referral_saas_service_target_calendar_versions (
        UPPER(calendar_code), scope_type, account_id, lifecycle_status, effective_from
    );

CREATE UNIQUE INDEX IF NOT EXISTS idx_referral_saas_service_target_calendar_one_closure
    ON referral_saas_service_target_calendar_date_exceptions (
        service_target_calendar_version_id, local_date
    )
    WHERE exception_type = 'CLOSED';

CREATE INDEX IF NOT EXISTS idx_referral_saas_service_target_calendar_audit_correlation
    ON referral_saas_service_target_calendar_audit (correlation_id, created_at);
