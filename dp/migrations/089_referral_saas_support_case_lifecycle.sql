CREATE TABLE IF NOT EXISTS referral_saas_support_case_notes (
    support_case_note_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    support_case_id uuid NOT NULL REFERENCES referral_saas_support_cases(support_case_id),
    account_id uuid NOT NULL,
    note_type text NOT NULL,
    note_text text NOT NULL,
    reason_code text,
    correlation_id text,
    idempotency_key_hash text NOT NULL,
    request_payload_hash text NOT NULL,
    created_by_ref text NOT NULL,
    created_by_role text,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    redactions jsonb NOT NULL DEFAULT '[]'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    archived_at timestamptz,
    CONSTRAINT referral_saas_support_case_notes_type_check CHECK (
        note_type IN ('OPERATOR_NOTE', 'CUSTOMER_UPDATE', 'EVIDENCE_SUMMARY', 'RESOLUTION_NOTE')
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_referral_saas_support_case_notes_idem
    ON referral_saas_support_case_notes (support_case_id, idempotency_key_hash)
    WHERE archived_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_referral_saas_support_case_notes_case
    ON referral_saas_support_case_notes (support_case_id, created_at);

CREATE INDEX IF NOT EXISTS idx_referral_saas_support_case_notes_account
    ON referral_saas_support_case_notes (account_id, created_at);

CREATE TABLE IF NOT EXISTS referral_saas_support_case_status_events (
    support_case_status_event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    support_case_id uuid NOT NULL REFERENCES referral_saas_support_cases(support_case_id),
    account_id uuid NOT NULL,
    from_status text NOT NULL,
    to_status text NOT NULL,
    transition_reason text NOT NULL,
    reason_code text,
    correlation_id text,
    idempotency_key_hash text NOT NULL,
    request_payload_hash text NOT NULL,
    changed_by_ref text NOT NULL,
    changed_by_role text,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    redactions jsonb NOT NULL DEFAULT '[]'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    archived_at timestamptz,
    CONSTRAINT referral_saas_support_case_status_from_check CHECK (
        from_status IN ('OPEN', 'INVESTIGATING', 'WAITING', 'RESOLVED', 'CLOSED')
    ),
    CONSTRAINT referral_saas_support_case_status_to_check CHECK (
        to_status IN ('OPEN', 'INVESTIGATING', 'WAITING', 'RESOLVED', 'CLOSED')
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_referral_saas_support_case_status_idem
    ON referral_saas_support_case_status_events (support_case_id, idempotency_key_hash)
    WHERE archived_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_referral_saas_support_case_status_case
    ON referral_saas_support_case_status_events (support_case_id, created_at);

CREATE INDEX IF NOT EXISTS idx_referral_saas_support_case_status_account
    ON referral_saas_support_case_status_events (account_id, created_at);
