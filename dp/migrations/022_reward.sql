CREATE TABLE IF NOT EXISTS rewards (
    id BIGSERIAL PRIMARY KEY,
    referral_track_id VARCHAR(100) NOT NULL,
    beneficiary_type VARCHAR(20) NOT NULL,
    beneficiary_ref VARCHAR(255) NOT NULL,
    product VARCHAR(100) NOT NULL,
    sub_product VARCHAR(100),
    reward_type VARCHAR(100) NOT NULL,
    amount NUMERIC(18,2) NOT NULL DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT 'EARNED',
    reward_source VARCHAR(50) NOT NULL DEFAULT 'BASE',
    mission_code VARCHAR(100),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_rewards_beneficiary_type
        CHECK (beneficiary_type IN ('REFERRER', 'REFEREE')),

    CONSTRAINT chk_rewards_reward_source
        CHECK (reward_source IN ('BASE', 'MISSION_BONUS')),

    CONSTRAINT chk_rewards_amount_positive
        CHECK (amount >= 0)
);

CREATE INDEX IF NOT EXISTS idx_rewards_referral_track_id
    ON rewards (referral_track_id);

CREATE INDEX IF NOT EXISTS idx_rewards_beneficiary
    ON rewards (beneficiary_type, beneficiary_ref);

CREATE INDEX IF NOT EXISTS idx_rewards_product_sub_product
    ON rewards (product, sub_product);

CREATE INDEX IF NOT EXISTS idx_rewards_status
    ON rewards (status);

CREATE INDEX IF NOT EXISTS idx_rewards_created_at
    ON rewards (created_at);

CREATE UNIQUE INDEX IF NOT EXISTS uq_rewards_base
    ON rewards (
        referral_track_id,
        beneficiary_type,
        beneficiary_ref,
        product,
        reward_type,
        reward_source
    )
    WHERE reward_source = 'BASE';

CREATE UNIQUE INDEX IF NOT EXISTS uq_rewards_mission_bonus
    ON rewards (
        referral_track_id,
        beneficiary_type,
        beneficiary_ref,
        mission_code,
        reward_source
    )
    WHERE reward_source = 'MISSION_BONUS';