CREATE TABLE IF NOT EXISTS rewards (
    id BIGSERIAL PRIMARY KEY,
    referral_track_id VARCHAR(100) NOT NULL,
    beneficiary_type VARCHAR(20) NOT NULL,
    beneficiary_ref VARCHAR(255),
    product VARCHAR(100) NOT NULL,
    sub_product VARCHAR(100),
    reward_type VARCHAR(100) NOT NULL,
    amount NUMERIC(18,2) NOT NULL DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT 'APPLIED',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_rewards_referrer_base
    ON rewards (referral_track_id, beneficiary_type, product, reward_type)
    WHERE beneficiary_type IN ('REFERRER', 'REFEREE');
	
ALTER TABLE rewards
ADD COLUMN IF NOT EXISTS reward_source VARCHAR(50),
ADD COLUMN IF NOT EXISTS mission_code VARCHAR(100);

UPDATE rewards
SET reward_source = 'BASE'
WHERE reward_source IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_rewards_base
    ON rewards (referral_track_id, beneficiary_type, product, reward_type, reward_source)
    WHERE reward_source = 'BASE';
	
CREATE UNIQUE INDEX IF NOT EXISTS uq_rewards_mission_bonus
    ON rewards (referral_track_id, beneficiary_type, mission_code, reward_source)
    WHERE reward_source = 'MISSION_BONUS';