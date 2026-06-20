CREATE TABLE IF NOT EXISTS reward_policies (
    id BIGSERIAL PRIMARY KEY,
    product VARCHAR(100) NOT NULL,
    sub_product VARCHAR(100),
    reward_type VARCHAR(100) NOT NULL,
    referrer_reward_amount NUMERIC(18,2) NOT NULL DEFAULT 0,
    referee_reward_amount NUMERIC(18,2) NOT NULL DEFAULT 0,
    allow_referee_reward BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_reward_policies_product_sub
    ON reward_policies (product, sub_product, is_active);