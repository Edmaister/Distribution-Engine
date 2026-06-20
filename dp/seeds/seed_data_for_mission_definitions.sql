INSERT INTO mission_definitions (
    mission_code,
    title,
    description,
    trigger_type,
    product,
    sub_product,
    goal,
    badge_code,
    bonus_reward_type,
    bonus_reward_amount,
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
    'BADGE_TXN_STARTER',
    'EWALLET',
    25.00,
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
    'BADGE_TXN_CHAMPION',
    'EWALLET',
    100.00,
    TRUE
);