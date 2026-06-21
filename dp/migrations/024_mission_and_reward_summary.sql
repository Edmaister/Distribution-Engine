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

-- Migration 005 created an earlier gamification table with referrer_hash
-- columns. On clean replay, CREATE TABLE IF NOT EXISTS above preserves that
-- table, so add the canonical referral-track columns before indexes/services
-- reference them.
ALTER TABLE user_mission_progress
    ADD COLUMN IF NOT EXISTS id UUID DEFAULT gen_random_uuid(),
    ADD COLUMN IF NOT EXISTS referral_track_id UUID,
    ADD COLUMN IF NOT EXISTS beneficiary_type TEXT,
    ADD COLUMN IF NOT EXISTS beneficiary_ref TEXT,
    ADD COLUMN IF NOT EXISTS progress_count INT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS goal_count INT NOT NULL DEFAULT 1,
    ADD COLUMN IF NOT EXISTS is_complete BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS bonus_reward_applied BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

UPDATE user_mission_progress
SET beneficiary_type = COALESCE(beneficiary_type, 'REFERRER');

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'user_mission_progress'
          AND column_name = 'referrer_hash'
    ) THEN
        EXECUTE '
            UPDATE user_mission_progress
            SET beneficiary_ref = COALESCE(beneficiary_ref, referrer_hash)
        ';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'user_mission_progress'
          AND column_name = 'progress'
    ) THEN
        EXECUTE '
            UPDATE user_mission_progress
            SET progress_count = COALESCE(progress_count, progress)
        ';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'user_mission_progress'
          AND column_name = 'status'
    ) THEN
        EXECUTE '
            UPDATE user_mission_progress
            SET is_complete = COALESCE(is_complete, status = ''COMPLETED'')
        ';
    END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS ux_user_mission_progress_referral_mission_beneficiary
    ON user_mission_progress (referral_track_id, mission_code, beneficiary_type, beneficiary_ref);

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

-- Migration 005 also created an earlier user_badges table keyed by
-- referrer_hash. Preserve it but add the canonical columns required by the
-- badge services and later indexes.
ALTER TABLE user_badges
    ADD COLUMN IF NOT EXISTS id UUID DEFAULT gen_random_uuid(),
    ADD COLUMN IF NOT EXISTS referral_track_id UUID,
    ADD COLUMN IF NOT EXISTS beneficiary_type TEXT,
    ADD COLUMN IF NOT EXISTS beneficiary_ref TEXT,
    ADD COLUMN IF NOT EXISTS award_reason TEXT,
    ADD COLUMN IF NOT EXISTS metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS awarded_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

UPDATE user_badges
SET beneficiary_type = COALESCE(beneficiary_type, 'REFERRER');

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'user_badges'
          AND column_name = 'referrer_hash'
    ) THEN
        EXECUTE '
            UPDATE user_badges
            SET beneficiary_ref = COALESCE(beneficiary_ref, referrer_hash)
        ';
    END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS ux_user_badges_referral_beneficiary_badge
    ON user_badges (referral_track_id, beneficiary_type, beneficiary_ref, badge_code);

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
