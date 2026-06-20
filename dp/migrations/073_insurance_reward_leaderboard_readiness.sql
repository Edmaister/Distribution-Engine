-- Configure Insurance leaderboard scoring so the second vertical has
-- commercial recognition rules from a clean migration replay.

INSERT INTO leaderboard_definitions (
    leaderboard_code,
    leaderboard_name,
    description,
    scope_type,
    subject_type,
    tenant_code,
    product,
    sub_product,
    journey_code,
    journey_version,
    aggregation_method,
    normalization_enabled,
    active
)
VALUES
(
    'GLOBAL_INSURANCE',
    'Global Insurance Leaderboard',
    'Ranks referrers based on the Insurance policy journey.',
    'GLOBAL',
    'REFERRER',
    NULL,
    'INSURANCE',
    NULL,
    'INSURANCE_POLICY',
    'v1',
    'RAW_SUM',
    FALSE,
    TRUE
)
ON CONFLICT (leaderboard_code) DO NOTHING;

INSERT INTO leaderboard_scoring_rules (
    leaderboard_code,
    journey_code,
    journey_version,
    product,
    sub_product,
    milestone_code,
    score_type,
    score_value,
    max_awards_per_referral,
    active,
    effective_from,
    created_at,
    updated_at
)
VALUES
('GLOBAL_INSURANCE', 'INSURANCE_POLICY', 'v1', 'INSURANCE', NULL, 'QUOTE_REQUESTED',    'MILESTONE', 15, 1, TRUE, NOW(), NOW(), NOW()),
('GLOBAL_INSURANCE', 'INSURANCE_POLICY', 'v1', 'INSURANCE', NULL, 'QUOTE_ACCEPTED',     'MILESTONE', 25, 1, TRUE, NOW(), NOW(), NOW()),
('GLOBAL_INSURANCE', 'INSURANCE_POLICY', 'v1', 'INSURANCE', NULL, 'POLICY_ISSUED',      'MILESTONE', 40, 1, TRUE, NOW(), NOW(), NOW()),
('GLOBAL_INSURANCE', 'INSURANCE_POLICY', 'v1', 'INSURANCE', NULL, 'FIRST_PREMIUM_PAID', 'MILESTONE', 60, 1, TRUE, NOW(), NOW(), NOW()),
('GLOBAL_INSURANCE', 'INSURANCE_POLICY', 'v1', 'INSURANCE', NULL, 'COMPLETION_BONUS',   'BONUS',     35, 1, TRUE, NOW(), NOW(), NOW())
ON CONFLICT DO NOTHING;
