CREATE TABLE IF NOT EXISTS referral_saas_support_case_repair_commands (
    repair_command_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    support_case_id UUID NOT NULL REFERENCES referral_saas_support_cases(support_case_id),
    account_id UUID NOT NULL REFERENCES platform_accounts(account_id),
    command_type TEXT NOT NULL CHECK (
        command_type IN (
            'GOVERNED_REPAIR',
            'GOVERNED_REPLAY',
            'GOVERNED_REASSIGNMENT'
        )
    ),
    command_status TEXT NOT NULL CHECK (
        command_status IN (
            'RECORDED',
            'REPLAYED'
        )
    ),
    target_evidence_type TEXT NOT NULL,
    target_evidence_ref TEXT NOT NULL,
    before_state_hash TEXT NOT NULL,
    impact_preview JSONB NOT NULL DEFAULT '{}'::jsonb,
    approval_ref TEXT NOT NULL,
    rollback_plan TEXT NOT NULL,
    reason_code TEXT,
    correlation_id TEXT,
    idempotency_key_hash TEXT NOT NULL,
    request_payload_hash TEXT NOT NULL,
    created_by_ref TEXT NOT NULL,
    created_by_role TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    redactions JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    archived_at TIMESTAMPTZ
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_referral_saas_support_repair_commands_idem
    ON referral_saas_support_case_repair_commands (
        support_case_id,
        idempotency_key_hash
    )
    WHERE archived_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_referral_saas_support_repair_commands_case
    ON referral_saas_support_case_repair_commands (
        support_case_id,
        created_at DESC
    )
    WHERE archived_at IS NULL;
