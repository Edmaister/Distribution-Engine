BEGIN;

CREATE TABLE IF NOT EXISTS user_portfolio_mission_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    referrer_ucn TEXT NOT NULL,
    mission_code TEXT NOT NULL,

    progress_count INTEGER NOT NULL DEFAULT 0,
    goal_count INTEGER NOT NULL,
    is_complete BOOLEAN NOT NULL DEFAULT FALSE,
    completed_at TIMESTAMPTZ,
    bonus_reward_applied BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_user_portfolio_mission_progress_referrer_mission
        UNIQUE (referrer_ucn, mission_code),

    CONSTRAINT chk_user_portfolio_mission_progress_goal_count
        CHECK (goal_count > 0),

    CONSTRAINT chk_user_portfolio_mission_progress_progress_count
        CHECK (progress_count >= 0)
);

CREATE INDEX IF NOT EXISTS idx_user_portfolio_mission_progress_referrer
ON user_portfolio_mission_progress (referrer_ucn);

CREATE INDEX IF NOT EXISTS idx_user_portfolio_mission_progress_complete
ON user_portfolio_mission_progress (referrer_ucn, is_complete, completed_at DESC);

COMMIT;
