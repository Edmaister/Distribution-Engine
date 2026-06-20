BEGIN;

-- =========================================================
-- 1. EXTEND badge_definitions.trigger_type CHECK CONSTRAINT
-- =========================================================

ALTER TABLE badge_definitions
DROP CONSTRAINT IF EXISTS badge_definitions_trigger_type_check;

ALTER TABLE badge_definitions
ADD CONSTRAINT badge_definitions_trigger_type_check
CHECK (
    trigger_type = ANY (
        ARRAY[
            'MISSION_COUNT'::text,
            'MISSION_CODE'::text,
            'COMPLETED_REFERRALS_COUNT'::text,
            'EVENT_TYPE'::text,
            'REFERRAL_CREATED_COUNT'::text,
            'HVE_COUNT'::text
        ]
    )
);

-- =========================================================
-- 2. USER_BADGES UNIQUENESS
-- =========================================================

ALTER TABLE user_badges
DROP CONSTRAINT IF EXISTS user_badges_referral_track_id_beneficiary_type_beneficiary__key;

DROP INDEX IF EXISTS idx_user_badges_user_level_unique;

CREATE UNIQUE INDEX IF NOT EXISTS idx_user_badges_user_level_unique
ON user_badges (beneficiary_type, beneficiary_ref, badge_code);

CREATE INDEX IF NOT EXISTS idx_user_badges_referrer_lookup
ON user_badges (beneficiary_type, beneficiary_ref, awarded_at DESC);

-- =========================================================
-- 3. DEACTIVATE OLD REFERRER BADGE DEFINITIONS
-- =========================================================

UPDATE badge_definitions
SET is_active = FALSE
WHERE beneficiary_type = 'REFERRER';

-- =========================================================
-- 4. INSERT / UPSERT NEW BADGE DEFINITIONS
-- =========================================================

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
    'STARTER',
    'Starter',
    'Awarded when your first referral is created.',
    'REFERRAL_OUTCOME',
    'REFERRER',
    'REFERRAL_CREATED_COUNT',
    '1',
    'sparkles',
    10,
    '["TCF","FAIS","MARKET_CONDUCT"]'::jsonb,
    TRUE
),
(
    'CONNECTOR',
    'Connector',
    'Awarded when you create 5 referrals.',
    'REFERRAL_OUTCOME',
    'REFERRER',
    'REFERRAL_CREATED_COUNT',
    '5',
    'users',
    20,
    '["TCF","FAIS","MARKET_CONDUCT"]'::jsonb,
    TRUE
),
(
    'CLOSER',
    'Closer',
    'Awarded when your first referral successfully completes.',
    'REFERRAL_OUTCOME',
    'REFERRER',
    'COMPLETED_REFERRALS_COUNT',
    '1',
    'check-circle',
    30,
    '["TCF","FAIS","MARKET_CONDUCT"]'::jsonb,
    TRUE
),
(
    'BUILDER',
    'Builder',
    'Awarded when 3 of your referrals successfully complete.',
    'REFERRAL_OUTCOME',
    'REFERRER',
    'COMPLETED_REFERRALS_COUNT',
    '3',
    'hammer',
    40,
    '["TCF","FAIS","MARKET_CONDUCT"]'::jsonb,
    TRUE
),
(
    'VALUE_DRIVER',
    'Value Driver',
    'Awarded when value is established on your first referral.',
    'REFERRAL_OUTCOME',
    'REFERRER',
    'HVE_COUNT',
    '1',
    'trending-up',
    50,
    '["TCF","FAIS","MARKET_CONDUCT"]'::jsonb,
    TRUE
),
(
    'POWER_DRIVER',
    'Power Driver',
    'Awarded when value is established across 3 referrals.',
    'REFERRAL_OUTCOME',
    'REFERRER',
    'HVE_COUNT',
    '3',
    'award',
    60,
    '["TCF","FAIS","MARKET_CONDUCT"]'::jsonb,
    TRUE
)
ON CONFLICT (badge_code)
DO UPDATE SET
    badge_name = EXCLUDED.badge_name,
    badge_description = EXCLUDED.badge_description,
    badge_category = EXCLUDED.badge_category,
    beneficiary_type = EXCLUDED.beneficiary_type,
    trigger_type = EXCLUDED.trigger_type,
    trigger_value = EXCLUDED.trigger_value,
    icon_name = EXCLUDED.icon_name,
    display_priority = EXCLUDED.display_priority,
    regulatory_tags = EXCLUDED.regulatory_tags,
    is_active = EXCLUDED.is_active;

COMMIT;
