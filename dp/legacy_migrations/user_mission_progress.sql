CREATE TABLE IF NOT EXISTS user_mission_progress (
    id BIGSERIAL PRIMARY KEY,
    referrer_hash VARCHAR(255) NOT NULL,
    mission_code VARCHAR(100) NOT NULL,
    progress INTEGER NOT NULL DEFAULT 0,
    goal INTEGER NOT NULL,
    completed BOOLEAN NOT NULL DEFAULT FALSE,
    completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_user_mission_progress
    ON user_mission_progress (referrer_hash, mission_code);