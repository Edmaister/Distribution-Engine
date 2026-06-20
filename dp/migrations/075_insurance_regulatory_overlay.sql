-- Seed Insurance regulatory overlay content for compliant customer-facing
-- recommendations and progress prompts.

INSERT INTO disclosure_library (disclosure_code, disclosure_text, channel)
VALUES
    (
        'INSURANCE_PRODUCT_INFO',
        'Insurance product information is general in nature and does not replace the policy wording, exclusions, waiting periods, or advice from a licensed representative.',
        'ALL'
    )
ON CONFLICT (disclosure_code) DO UPDATE
SET disclosure_text = EXCLUDED.disclosure_text,
    channel = EXCLUDED.channel,
    is_active = TRUE;

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
    'INSURANCE_QUOTE_ACCEPTANCE_INFO',
    'NEXT_BEST_ACTION',
    'Insurance quote is ready',
    'You can review the quote, policy terms, exclusions, waiting periods, and premium details before choosing whether to continue.',
    'View details',
    'OPEN_INFO',
    TRUE,
    FALSE,
    TRUE,
    '["TCF","FAIS","MARKET_CONDUCT","INSURANCE_CONDUCT"]'::jsonb,
    'v1.0'
),
(
    'INSURANCE_POLICY_ACTIVATION_INFO',
    'NEXT_BEST_ACTION',
    'Policy activation step is available',
    'If you choose to continue, policy activation and any reward depend on the policy being issued and the first premium being paid successfully.',
    'View details',
    'OPEN_INFO',
    TRUE,
    FALSE,
    TRUE,
    '["TCF","FAIS","MARKET_CONDUCT","INSURANCE_CONDUCT"]'::jsonb,
    'v1.0'
),
(
    'INSURANCE_PROGRESS_INFO',
    'INFO',
    'Your insurance referral progress is available',
    'You can review where the policy application is in the quote, issue, premium, and reward journey.',
    'View progress',
    'VIEW_PROGRESS',
    TRUE,
    FALSE,
    TRUE,
    '["TCF","FAIS","MARKET_CONDUCT","INSURANCE_CONDUCT"]'::jsonb,
    'v1.0'
),
(
    'INSURANCE_POLICY_COMPLETE_INFO',
    'INFO',
    'Insurance referral is complete',
    'The policy journey is complete once the required policy issue and first-premium conditions have been confirmed.',
    'View progress',
    'VIEW_PROGRESS',
    TRUE,
    FALSE,
    TRUE,
    '["TCF","FAIS","MARKET_CONDUCT","INSURANCE_CONDUCT"]'::jsonb,
    'v1.0'
)
ON CONFLICT (template_code) DO UPDATE
SET category = EXCLUDED.category,
    title_template = EXCLUDED.title_template,
    body_template = EXCLUDED.body_template,
    cta_label = EXCLUDED.cta_label,
    cta_action = EXCLUDED.cta_action,
    is_active = TRUE,
    is_credit_related = EXCLUDED.is_credit_related,
    requires_disclaimer = EXCLUDED.requires_disclaimer,
    regulatory_tags = EXCLUDED.regulatory_tags,
    template_version = EXCLUDED.template_version,
    updated_at = NOW();
