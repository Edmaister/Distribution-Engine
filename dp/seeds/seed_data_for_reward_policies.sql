INSERT INTO reward_policies (
    product,
    sub_product,
    reward_type,
    referrer_reward_amount,
    referee_reward_amount,
    allow_referee_reward,
    is_active
)
SELECT
    'TRANSACTIONAL',
    'EASY_ACCOUNT',
    'EWALLET',
    50.00,
    25.00,
    TRUE,
    TRUE
WHERE NOT EXISTS (
    SELECT 1
    FROM reward_policies
    WHERE product = 'TRANSACTIONAL'
      AND sub_product = 'EASY_ACCOUNT'
      AND reward_type = 'EWALLET'
)
UNION ALL
SELECT
    'INSURANCE',
    'FUNERAL_PLAN',
    'EWALLET',
    120.00,
    0.00,
    FALSE,
    TRUE
WHERE NOT EXISTS (
    SELECT 1
    FROM reward_policies
    WHERE product = 'INSURANCE'
      AND sub_product = 'FUNERAL_PLAN'
      AND reward_type = 'EWALLET'
);
