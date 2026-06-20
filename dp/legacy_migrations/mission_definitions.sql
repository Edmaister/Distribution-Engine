CREATE TABLE IF NOT EXISTS mission_definitions (
    id BIGSERIAL PRIMARY KEY,
    mission_code VARCHAR(100) NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    trigger_type VARCHAR(100) NOT NULL,
    product VARCHAR(100) NOT NULL,
    sub_product VARCHAR(100),
    goal INTEGER NOT NULL,
    badge_code VARCHAR(100),
    bonus_reward_type VARCHAR(100),
    bonus_reward_amount NUMERIC(18,2) NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mission_definitions_product_sub
    ON mission_definitions (product, sub_product, trigger_type, is_active);