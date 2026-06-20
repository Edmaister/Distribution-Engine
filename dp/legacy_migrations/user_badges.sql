CREATE TABLE IF NOT EXISTS user_badges (
    id BIGSERIAL PRIMARY KEY,
    referrer_hash VARCHAR(255) NOT NULL,
    badge_code VARCHAR(100) NOT NULL,
    awarded_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_user_badges
    ON user_badges (referrer_hash, badge_code);