INSERT INTO recommendation_templates (
    template_code,
    category,
    title_template,
    body_template,
    cta_label,
    cta_action,
    is_active,
    is_credit_related,
    requires_disclaimer,
    regulatory_tags,
    template_version
)
VALUES
(
    'SALARY_SWITCH_INFO',
    'NEXT_BEST_ACTION',
    'Salary switch is available',
    'If you choose to switch your salary, you may qualify for a reward once the switch is completed successfully.',
    'Learn more',
    'OPEN_INFO',
    TRUE,
    FALSE,
    TRUE,
    '["TCF","FAIS","MARKET_CONDUCT","BANKING_CODE"]'::jsonb,
    'v1.0'
),
(
    'DEBIT_ORDER_SWITCH_INFO',
    'NEXT_BEST_ACTION',
    'Debit order switch is available',
    'If you choose to switch your debit order, you may qualify for a reward once the switch is completed successfully.',
    'Learn more',
    'OPEN_INFO',
    TRUE,
    FALSE,
    TRUE,
    '["TCF","FAIS","MARKET_CONDUCT","BANKING_CODE"]'::jsonb,
    'v1.0'
),
(
    'PROGRESS_INFO',
    'INFO',
    'Your referral progress is available',
    'You can view your current progress, completed steps and any conditions linked to future rewards.',
    'View details',
    'VIEW_PROGRESS',
    TRUE,
    FALSE,
    TRUE,
    '["TCF","BANKING_CODE"]'::jsonb,
    'v1.0'
)
ON CONFLICT (template_code) DO NOTHING;