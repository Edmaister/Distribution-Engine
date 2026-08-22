-- TASK-432: Persist governed Referral SaaS operational service-target evidence.
-- No policy values are seeded here. Runtime remains unavailable until a later
-- task resolves approved policies and owns the clock lifecycle.

CREATE TABLE IF NOT EXISTS referral_saas_operational_service_target_policies (
    service_target_policy_id UUID PRIMARY KEY,
    policy_code TEXT NOT NULL,
    version_number INTEGER NOT NULL,
    operating_jurisdiction_code TEXT NOT NULL,
    work_type TEXT NOT NULL,
    work_category TEXT NOT NULL,
    priority TEXT NOT NULL,
    business_timezone TEXT NOT NULL,
    target_duration_minutes INTEGER NOT NULL,
    warning_threshold_minutes INTEGER NOT NULL,
    business_calendar_ref TEXT,
    start_event TEXT NOT NULL,
    completion_event TEXT NOT NULL,
    approved_pause_reasons JSONB NOT NULL DEFAULT '[]'::jsonb,
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
    CONSTRAINT referral_saas_service_target_policy_version_ck CHECK (version_number > 0),
    CONSTRAINT referral_saas_service_target_policy_duration_ck CHECK (target_duration_minutes > 0),
    CONSTRAINT referral_saas_service_target_policy_warning_ck CHECK (
        warning_threshold_minutes >= 0 AND warning_threshold_minutes < target_duration_minutes
    ),
    CONSTRAINT referral_saas_service_target_policy_window_ck CHECK (
        effective_to IS NULL OR effective_to > effective_from
    ),
    CONSTRAINT referral_saas_service_target_policy_pause_reasons_ck CHECK (
        jsonb_typeof(approved_pause_reasons) = 'array'
    ),
    CONSTRAINT referral_saas_service_target_policy_lifecycle_ck CHECK (
        lifecycle_status IN ('DRAFT', 'IN_REVIEW', 'APPROVED', 'RETIRED')
    ),
    UNIQUE (policy_code, version_number)
);

CREATE TABLE IF NOT EXISTS referral_saas_operational_service_target_clocks (
    service_target_clock_id UUID PRIMARY KEY,
    support_case_id UUID NOT NULL UNIQUE
        REFERENCES referral_saas_support_cases(support_case_id),
    account_id UUID NOT NULL REFERENCES platform_accounts(account_id),
    service_target_policy_id UUID NOT NULL
        REFERENCES referral_saas_operational_service_target_policies(service_target_policy_id),
    policy_code TEXT NOT NULL,
    policy_version_number INTEGER NOT NULL,
    clock_status TEXT NOT NULL DEFAULT 'RUNNING',
    started_at TIMESTAMPTZ NOT NULL,
    warning_at TIMESTAMPTZ NOT NULL,
    due_at TIMESTAMPTZ NOT NULL,
    accumulated_paused_seconds BIGINT NOT NULL DEFAULT 0,
    completed_at TIMESTAMPTZ,
    breached_at TIMESTAMPTZ,
    completion_outcome TEXT,
    correlation_id TEXT NOT NULL,
    idempotency_key_hash TEXT NOT NULL,
    request_payload_hash TEXT NOT NULL,
    created_by_ref TEXT NOT NULL,
    updated_by_ref TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    redactions JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT referral_saas_service_target_clock_policy_version_ck CHECK (policy_version_number > 0),
    CONSTRAINT referral_saas_service_target_clock_status_ck CHECK (
        clock_status IN ('RUNNING', 'PAUSED', 'COMPLETED')
    ),
    CONSTRAINT referral_saas_service_target_clock_times_ck CHECK (
        started_at <= warning_at AND warning_at < due_at
    ),
    CONSTRAINT referral_saas_service_target_clock_pause_ck CHECK (accumulated_paused_seconds >= 0),
    CONSTRAINT referral_saas_service_target_clock_completed_ck CHECK (
        completed_at IS NULL OR completed_at >= started_at
    ),
    CONSTRAINT referral_saas_service_target_clock_breached_ck CHECK (
        breached_at IS NULL OR breached_at >= started_at
    ),
    CONSTRAINT referral_saas_service_target_clock_outcome_ck CHECK (
        completion_outcome IS NULL OR completion_outcome IN ('WITHIN_TARGET', 'LATE')
    )
);

CREATE TABLE IF NOT EXISTS referral_saas_operational_service_target_pause_events (
    service_target_pause_event_id UUID PRIMARY KEY,
    service_target_clock_id UUID NOT NULL
        REFERENCES referral_saas_operational_service_target_clocks(service_target_clock_id),
    support_case_id UUID NOT NULL REFERENCES referral_saas_support_cases(support_case_id),
    account_id UUID NOT NULL REFERENCES platform_accounts(account_id),
    event_type TEXT NOT NULL,
    pause_reason_code TEXT NOT NULL,
    event_at TIMESTAMPTZ NOT NULL,
    actor_ref TEXT NOT NULL,
    actor_role TEXT NOT NULL,
    correlation_id TEXT NOT NULL,
    idempotency_key_hash TEXT NOT NULL,
    request_payload_hash TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    redactions JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT referral_saas_service_target_pause_event_type_ck CHECK (
        event_type IN ('PAUSED', 'RESUMED')
    ),
    UNIQUE (service_target_clock_id, idempotency_key_hash)
);

CREATE TABLE IF NOT EXISTS referral_saas_operational_service_target_audit (
    service_target_audit_id UUID PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_ref UUID NOT NULL,
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
    CONSTRAINT referral_saas_service_target_audit_entity_ck CHECK (
        entity_type IN ('POLICY', 'CLOCK', 'PAUSE_EVENT')
    )
);

CREATE INDEX IF NOT EXISTS idx_referral_saas_service_target_policy_resolution
    ON referral_saas_operational_service_target_policies (
        operating_jurisdiction_code, work_type, work_category, priority,
        lifecycle_status, effective_from
    );

CREATE UNIQUE INDEX IF NOT EXISTS idx_referral_saas_service_target_policy_idempotency
    ON referral_saas_operational_service_target_policies (idempotency_key_hash);

CREATE INDEX IF NOT EXISTS idx_referral_saas_service_target_clocks_account_status
    ON referral_saas_operational_service_target_clocks (account_id, clock_status, due_at);

CREATE UNIQUE INDEX IF NOT EXISTS idx_referral_saas_service_target_clocks_idempotency
    ON referral_saas_operational_service_target_clocks (idempotency_key_hash);

CREATE INDEX IF NOT EXISTS idx_referral_saas_service_target_pause_events_clock_time
    ON referral_saas_operational_service_target_pause_events (service_target_clock_id, event_at);

CREATE INDEX IF NOT EXISTS idx_referral_saas_service_target_audit_correlation
    ON referral_saas_operational_service_target_audit (correlation_id, created_at);
