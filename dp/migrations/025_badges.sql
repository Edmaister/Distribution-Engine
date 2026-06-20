BEGIN;

CREATE TABLE IF NOT EXISTS badge_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    badge_code TEXT NOT NULL UNIQUE,
    badge_name TEXT NOT NULL,
    badge_description TEXT NOT NULL,
    badge_category TEXT NOT NULL CHECK (
        badge_category IN ('MISSION', 'REFERRAL_OUTCOME', 'STATUS')
    ),
    beneficiary_type TEXT NOT NULL CHECK (
        beneficiary_type IN ('REFERRER')
    ),
    trigger_type TEXT NOT NULL CHECK (
        trigger_type IN ('MISSION_COUNT', 'MISSION_CODE', 'COMPLETED_REFERRALS_COUNT', 'EVENT_TYPE')
    ),
    trigger_value TEXT NOT NULL,
    icon_name TEXT,
    display_priority INT NOT NULL DEFAULT 100,
    regulatory_tags JSONB NOT NULL DEFAULT '[]'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_badges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    referral_track_id UUID NOT NULL,
    beneficiary_type TEXT NOT NULL CHECK (beneficiary_type IN ('REFERRER')),
    beneficiary_ref TEXT NOT NULL,
    badge_code TEXT NOT NULL,
    awarded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    award_reason TEXT,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (referral_track_id, beneficiary_type, beneficiary_ref, badge_code)
);

CREATE TABLE IF NOT EXISTS badge_display_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    referral_track_id UUID NOT NULL,
    badge_code TEXT NOT NULL,
    beneficiary_type TEXT NOT NULL,
    beneficiary_ref TEXT NOT NULL,
    badge_name TEXT NOT NULL,
    badge_description TEXT NOT NULL,
    compliance_json JSONB NOT NULL,
    channel TEXT NOT NULL,
    shown_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_badges_track
    ON user_badges (referral_track_id, beneficiary_type, beneficiary_ref, awarded_at DESC);

CREATE INDEX IF NOT EXISTS idx_badge_display_audit_track
    ON badge_display_audit (referral_track_id, shown_at DESC);

INSERT INTO badge_definitions (
    badge_code,
    badge_name,
    badge_description,
    badge_category,
    beneficiary_type,
    trigger_type,
    trigger_value,
    icon_name,
    display_priority,
    regulatory_tags,
    is_active
)
VALUES
(
    'MISSION_STARTER',
    'Mission Starter',
    'Completed your first optional mission.',
    'MISSION',
    'REFERRER',
    'MISSION_COUNT',
    '1',
    'badge-mission-starter',
    1,
    '["TCF","FAIS","MARKET_CONDUCT"]'::jsonb,
    TRUE
),
(
    'MISSION_MOMENTUM',
    'Mission Momentum',
    'Completed two optional missions.',
    'MISSION',
    'REFERRER',
    'MISSION_COUNT',
    '2',
    'badge-mission-momentum',
    2,
    '["TCF","FAIS","MARKET_CONDUCT"]'::jsonb,
    TRUE
),
(
    'SALARY_SWITCH_ACHIEVER',
    'Salary Switch Achiever',
    'Completed the salary switch mission.',
    'MISSION',
    'REFERRER',
    'MISSION_CODE',
    'FIRST_SALARY_SWITCH',
    'badge-salary-switch',
    3,
    '["TCF","FAIS","MARKET_CONDUCT"]'::jsonb,
    TRUE
),
(
    'DEBIT_SWITCH_ACHIEVER',
    'Debit Switch Achiever',
    'Completed the debit order switch mission.',
    'MISSION',
    'REFERRER',
    'MISSION_CODE',
    'FIRST_DEBIT_ORDER_SWITCH',
    'badge-debit-switch',
    4,
    '["TCF","FAIS","MARKET_CONDUCT"]'::jsonb,
    TRUE
),
(
    'FIRST_SUCCESS',
    'First Success',
    'Achieved your first completed referral outcome.',
    'REFERRAL_OUTCOME',
    'REFERRER',
    'COMPLETED_REFERRALS_COUNT',
    '1',
    'badge-first-success',
    5,
    '["TCF","FAIS","MARKET_CONDUCT"]'::jsonb,
    TRUE
)
ON CONFLICT (badge_code) DO NOTHING;

COMMIT;