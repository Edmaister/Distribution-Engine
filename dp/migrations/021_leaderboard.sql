-- =========================================================
-- 013_leaderboards.sql
-- Final Leaderboard Core
-- =========================================================

BEGIN;

-- =========================================================
-- 1. Leaderboard Definitions
-- =========================================================
CREATE TABLE IF NOT EXISTS leaderboard_definitions (
    leaderboard_code         TEXT PRIMARY KEY,
    leaderboard_name         TEXT NOT NULL,
    description              TEXT,

    scope_type               TEXT NOT NULL,   -- GLOBAL / TENANT / PRODUCT / CAMPAIGN / SEASONAL
    subject_type             TEXT NOT NULL,   -- REFERRER

    tenant_code              TEXT,
    product                  TEXT,
    sub_product              TEXT,
    journey_code             TEXT,
    journey_version          TEXT,

    aggregation_method       TEXT NOT NULL DEFAULT 'RAW_SUM',
    normalization_enabled    BOOLEAN NOT NULL DEFAULT FALSE,
    weighting_config_json    JSONB,

    active                   BOOLEAN NOT NULL DEFAULT TRUE,
    effective_from           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    effective_to             TIMESTAMPTZ,

    created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_lb_def_active
    ON leaderboard_definitions (active);

CREATE INDEX IF NOT EXISTS idx_lb_def_scope
    ON leaderboard_definitions (
        scope_type,
        tenant_code,
        product,
        sub_product,
        journey_code,
        journey_version
    );


-- =========================================================
-- 2. Leaderboard Scoring Rules
-- =========================================================
CREATE TABLE IF NOT EXISTS leaderboard_scoring_rules (
    id                       BIGSERIAL PRIMARY KEY,

    leaderboard_code         TEXT NOT NULL
        REFERENCES leaderboard_definitions(leaderboard_code)
        ON DELETE CASCADE,

    journey_code             TEXT,
    journey_version          TEXT,

    product                  TEXT,
    sub_product              TEXT,

    milestone_code           TEXT NOT NULL,   -- VALIDATED / ACCOUNT_OPENED / etc.
    score_type               TEXT NOT NULL,   -- MILESTONE / BONUS
    score_value              INT NOT NULL,

    max_awards_per_referral  INT NOT NULL DEFAULT 1,

    active                   BOOLEAN NOT NULL DEFAULT TRUE,
    effective_from           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    effective_to             TIMESTAMPTZ,

    created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_lb_rules_expr
ON leaderboard_scoring_rules (
    leaderboard_code,
    COALESCE(journey_code, ''),
    COALESCE(journey_version, ''),
    COALESCE(product, ''),
    COALESCE(sub_product, ''),
    milestone_code,
    score_type
);

CREATE INDEX IF NOT EXISTS idx_lb_rules_lookup
ON leaderboard_scoring_rules (
    leaderboard_code,
    active,
    product,
    sub_product,
    journey_code,
    journey_version
);


-- =========================================================
-- 3. Leaderboard Entries (Derived Projection)
-- =========================================================
CREATE TABLE IF NOT EXISTS leaderboard_entries (
    leaderboard_code             TEXT NOT NULL
        REFERENCES leaderboard_definitions(leaderboard_code)
        ON DELETE CASCADE,

    referrer_ucn                 TEXT NOT NULL,
    referrer_ucn_hash            TEXT NOT NULL,

    display_name                 TEXT,

    total_score                  INT NOT NULL DEFAULT 0,
    referral_score               INT NOT NULL DEFAULT 0,
    milestone_score              INT NOT NULL DEFAULT 0,
    bonus_score                  INT NOT NULL DEFAULT 0,

    referrals_count              INT NOT NULL DEFAULT 0,
    completed_referrals_count    INT NOT NULL DEFAULT 0,

    last_event_at                TIMESTAMPTZ,
    rank_position                INT,
    rank_tier                    TEXT,

    tenant_code                  TEXT,
    segment                      TEXT,
    product                      TEXT,
    sub_product                  TEXT,

    created_at                   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                   TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (leaderboard_code, referrer_ucn)
);

CREATE INDEX IF NOT EXISTS idx_lb_entries_rank
    ON leaderboard_entries (leaderboard_code, rank_position);

CREATE INDEX IF NOT EXISTS idx_lb_entries_score
    ON leaderboard_entries (
        leaderboard_code,
        total_score DESC,
        completed_referrals_count DESC
    );

CREATE INDEX IF NOT EXISTS idx_lb_entries_hash
    ON leaderboard_entries (referrer_ucn_hash);

CREATE INDEX IF NOT EXISTS idx_lb_entries_display_name
    ON leaderboard_entries (display_name);


-- =========================================================
-- 4. Seed Leaderboard Definitions
-- =========================================================
INSERT INTO leaderboard_definitions (
    leaderboard_code,
    leaderboard_name,
    description,
    scope_type,
    subject_type,
    tenant_code,
    product,
    sub_product,
    journey_code,
    journey_version,
    aggregation_method,
    normalization_enabled,
    active
)
VALUES
(
    'GLOBAL_TRANSACTIONAL',
    'Global Transactional Leaderboard',
    'Ranks referrers based on the banking transactional journey.',
    'GLOBAL',
    'REFERRER',
    NULL,
    NULL,
    NULL,
    'BANKING_TRANSACTIONAL',
    'v1',
    'RAW_SUM',
    FALSE,
    TRUE
),
(
    'GLOBAL_OVERALL',
    'Global Overall Leaderboard',
    'Ranks referrers across all included journeys. At launch this behaves as transactional-only until more journeys are onboarded.',
    'GLOBAL',
    'REFERRER',
    NULL,
    NULL,
    NULL,
    NULL,
    NULL,
    'RAW_SUM',
    FALSE,
    TRUE
)
ON CONFLICT (leaderboard_code) DO NOTHING;


-- =========================================================
-- 5. Seed Scoring Rules
-- Transactional rules apply to both boards at launch
-- =========================================================

-- GLOBAL_TRANSACTIONAL
INSERT INTO leaderboard_scoring_rules (
    leaderboard_code,
    journey_code,
    journey_version,
    product,
    sub_product,
    milestone_code,
    score_type,
    score_value,
    max_awards_per_referral,
    active
)
VALUES
('GLOBAL_TRANSACTIONAL', 'BANKING_TRANSACTIONAL', 'v1', NULL, NULL, 'VALIDATED',                   'MILESTONE', 10, 1, TRUE),
('GLOBAL_TRANSACTIONAL', 'BANKING_TRANSACTIONAL', 'v1', NULL, NULL, 'ACCOUNT_OPENED',              'MILESTONE', 20, 1, TRUE),
('GLOBAL_TRANSACTIONAL', 'BANKING_TRANSACTIONAL', 'v1', NULL, NULL, 'ACCOUNT_ACTIVATED',           'MILESTONE', 30, 1, TRUE),
('GLOBAL_TRANSACTIONAL', 'BANKING_TRANSACTIONAL', 'v1', NULL, NULL, 'FUNDED',                      'MILESTONE', 50, 1, TRUE),
('GLOBAL_TRANSACTIONAL', 'BANKING_TRANSACTIONAL', 'v1', NULL, NULL, 'DEBIT_ORDER_SWITCHED',        'MILESTONE', 20, 1, TRUE),
('GLOBAL_TRANSACTIONAL', 'BANKING_TRANSACTIONAL', 'v1', NULL, NULL, 'SALARY_SWITCHED',             'MILESTONE', 30, 1, TRUE),
('GLOBAL_TRANSACTIONAL', 'BANKING_TRANSACTIONAL', 'v1', NULL, NULL, 'FIRST_TRANSACTION_COMPLETED', 'MILESTONE', 15, 1, TRUE),
('GLOBAL_TRANSACTIONAL', 'BANKING_TRANSACTIONAL', 'v1', NULL, NULL, 'COMPLETION_BONUS',            'BONUS',     25, 1, TRUE)
ON CONFLICT DO NOTHING;

-- GLOBAL_OVERALL
INSERT INTO leaderboard_scoring_rules (
    leaderboard_code,
    journey_code,
    journey_version,
    product,
    sub_product,
    milestone_code,
    score_type,
    score_value,
    max_awards_per_referral,
    active
)
VALUES
('GLOBAL_OVERALL', 'BANKING_TRANSACTIONAL', 'v1', NULL, NULL, 'VALIDATED',                   'MILESTONE', 10, 1, TRUE),
('GLOBAL_OVERALL', 'BANKING_TRANSACTIONAL', 'v1', NULL, NULL, 'ACCOUNT_OPENED',              'MILESTONE', 20, 1, TRUE),
('GLOBAL_OVERALL', 'BANKING_TRANSACTIONAL', 'v1', NULL, NULL, 'ACCOUNT_ACTIVATED',           'MILESTONE', 30, 1, TRUE),
('GLOBAL_OVERALL', 'BANKING_TRANSACTIONAL', 'v1', NULL, NULL, 'FUNDED',                      'MILESTONE', 50, 1, TRUE),
('GLOBAL_OVERALL', 'BANKING_TRANSACTIONAL', 'v1', NULL, NULL, 'DEBIT_ORDER_SWITCHED',        'MILESTONE', 20, 1, TRUE),
('GLOBAL_OVERALL', 'BANKING_TRANSACTIONAL', 'v1', NULL, NULL, 'SALARY_SWITCHED',             'MILESTONE', 30, 1, TRUE),
('GLOBAL_OVERALL', 'BANKING_TRANSACTIONAL', 'v1', NULL, NULL, 'FIRST_TRANSACTION_COMPLETED', 'MILESTONE', 15, 1, TRUE),
('GLOBAL_OVERALL', 'BANKING_TRANSACTIONAL', 'v1', NULL, NULL, 'COMPLETION_BONUS',            'BONUS',     25, 1, TRUE)
ON CONFLICT DO NOTHING;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'leaderboard_entries'
          AND column_name = 'badge'
    ) AND NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'leaderboard_entries'
          AND column_name = 'rank_tier'
    ) THEN
        ALTER TABLE leaderboard_entries
        RENAME COLUMN badge TO rank_tier;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'leaderboard_entries'
          AND column_name = 'rank_tier'
    ) THEN
        ALTER TABLE leaderboard_entries
        ADD COLUMN rank_tier TEXT;
    END IF;
END $$;

COMMIT;

