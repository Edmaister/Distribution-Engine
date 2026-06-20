BEGIN;

CREATE TABLE IF NOT EXISTS mission_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_code TEXT NOT NULL UNIQUE,
    mission_name TEXT NOT NULL,
    mission_description TEXT NOT NULL,
    product TEXT,
    sub_product TEXT,
    event_type TEXT NOT NULL,
    goal_count INT NOT NULL DEFAULT 1,
    bonus_reward_amount INT NOT NULL DEFAULT 0,
    currency TEXT NOT NULL DEFAULT 'ZAR',
    is_optional BOOLEAN NOT NULL DEFAULT TRUE,
    is_credit_related BOOLEAN NOT NULL DEFAULT FALSE,
    requires_disclaimer BOOLEAN NOT NULL DEFAULT TRUE,
    regulatory_tags JSONB NOT NULL DEFAULT '[]'::jsonb,
    display_priority INT NOT NULL DEFAULT 100,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_mission_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    referral_track_id UUID NOT NULL,
    mission_code TEXT NOT NULL,
    beneficiary_type TEXT NOT NULL CHECK (beneficiary_type IN ('REFERRER', 'REFEREE')),
    beneficiary_ref TEXT NOT NULL,
    progress_count INT NOT NULL DEFAULT 0,
    goal_count INT NOT NULL,
    is_complete BOOLEAN NOT NULL DEFAULT FALSE,
    completed_at TIMESTAMPTZ,
    bonus_reward_applied BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (referral_track_id, mission_code, beneficiary_type, beneficiary_ref)
);

CREATE TABLE IF NOT EXISTS reward_disclosures (
    disclosure_code TEXT PRIMARY KEY,
    disclosure_text TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS mission_display_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    referral_track_id UUID NOT NULL,
    mission_code TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    compliance_json JSONB NOT NULL,
    disclosures_json JSONB NOT NULL,
    channel TEXT NOT NULL,
    shown_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_mission_progress_track
    ON user_mission_progress (referral_track_id, beneficiary_type, mission_code);

CREATE INDEX IF NOT EXISTS idx_mission_display_audit_track
    ON mission_display_audit (referral_track_id, shown_at DESC);

INSERT INTO reward_disclosures (disclosure_code, disclosure_text)
VALUES
(
    'GENERAL_INFO_ONLY',
    'This is general information and not personal financial advice. Please consider your own circumstances and the product terms before acting.'
),
(
    'REWARD_CONDITIONAL',
    'Rewards are conditional and are only applied when the qualifying requirements have been met successfully.'
),
(
    'CREDIT_DISCLOSURE',
    'Credit is subject to assessment, terms and applicable regulation. Information shown here does not guarantee approval.'
)
ON CONFLICT (disclosure_code) DO NOTHING;

INSERT INTO mission_definitions (
    mission_code,
    mission_name,
    mission_description,
    product,
    sub_product,
    event_type,
    goal_count,
    bonus_reward_amount,
    currency,
    is_optional,
    is_credit_related,
    requires_disclaimer,
    regulatory_tags,
    display_priority,
    is_active
)
VALUES
(
    'FIRST_SALARY_SWITCH',
    'Optional mission: first salary switch',
    'If you choose to complete a successful salary switch, you may qualify for a bonus reward.',
    'TRANSACTIONAL',
    NULL,
    'SALARY_SWITCHED',
    1,
    200,
    'ZAR',
    TRUE,
    FALSE,
    TRUE,
    '["TCF","FAIS","MARKET_CONDUCT","BANKING_CODE"]'::jsonb,
    1,
    TRUE
),
(
    'FIRST_DEBIT_ORDER_SWITCH',
    'Optional mission: first debit order switch',
    'If you choose to complete a successful debit order switch, you may qualify for a bonus reward.',
    'TRANSACTIONAL',
    NULL,
    'DEBIT_ORDER_SWITCHED',
    1,
    200,
    'ZAR',
    TRUE,
    FALSE,
    TRUE,
    '["TCF","FAIS","MARKET_CONDUCT","BANKING_CODE"]'::jsonb,
    2,
    TRUE
)
ON CONFLICT (mission_code) DO NOTHING;


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
