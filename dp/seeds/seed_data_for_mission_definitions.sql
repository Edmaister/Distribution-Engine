INSERT INTO mission_definitions (
    mission_code,
    mission_name,
    mission_description,
    event_type,
    product,
    sub_product,
    goal_count,
    bonus_reward_amount,
    mission_category,
    is_active
)
VALUES
(
    'TXN_FIRST_SUCCESS',
    'Complete your first transactional referral',
    'Complete 1 successful transactional referral',
    'PRODUCT_COMPLETED',
    'TRANSACTIONAL',
    'EASY_ACCOUNT',
    1,
    25,
    'MILESTONE',
    TRUE
),
(
    'TXN_THREE_SUCCESS',
    'Complete 3 transactional referrals',
    'Complete 3 successful transactional referrals',
    'PRODUCT_COMPLETED',
    'TRANSACTIONAL',
    'EASY_ACCOUNT',
    3,
    100,
    'MILESTONE',
    TRUE
)
ON CONFLICT (mission_code) DO NOTHING;
