BEGIN;

CREATE TABLE IF NOT EXISTS recommendation_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_code TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    title_template TEXT NOT NULL,
    body_template TEXT NOT NULL,
    cta_label TEXT NOT NULL,
    cta_action TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_credit_related BOOLEAN NOT NULL DEFAULT FALSE,
    requires_disclaimer BOOLEAN NOT NULL DEFAULT TRUE,
    regulatory_tags JSONB NOT NULL DEFAULT '[]'::jsonb,
    template_version TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS disclosure_library (
    disclosure_code TEXT PRIMARY KEY,
    disclosure_text TEXT NOT NULL,
    channel TEXT NOT NULL DEFAULT 'ALL',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS recommendation_compliance_policies (
    policy_code TEXT PRIMARY KEY,
    policy_version TEXT NOT NULL,
    banned_phrases JSONB NOT NULL DEFAULT '[]'::jsonb,
    advisory_markers JSONB NOT NULL DEFAULT '[]'::jsonb,
    pressure_markers JSONB NOT NULL DEFAULT '[]'::jsonb,
    blocked_ctas JSONB NOT NULL DEFAULT '[]'::jsonb,
    allowed_ctas JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS recommendation_display_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    referral_track_id UUID NOT NULL,
    recommendation_id TEXT NOT NULL,
    template_code TEXT NOT NULL,
    template_version TEXT NOT NULL,
    policy_version TEXT NOT NULL,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    cta_label TEXT NOT NULL,
    cta_action TEXT NOT NULL,
    reward_preview_json JSONB,
    compliance_json JSONB NOT NULL,
    disclosures_json JSONB NOT NULL,
    channel TEXT NOT NULL,
    shown_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_recommendation_display_audit_track
    ON recommendation_display_audit (referral_track_id, shown_at DESC);

INSERT INTO disclosure_library (disclosure_code, disclosure_text, channel)
VALUES
    (
        'GENERAL_INFO_ONLY',
        'This is general information and not personal financial advice. Please consider your own circumstances and the product terms before acting.',
        'ALL'
    ),
    (
        'REWARD_CONDITIONAL',
        'Rewards are conditional and are only applied when the qualifying requirements have been met successfully.',
        'ALL'
    ),
    (
        'CREDIT_DISCLOSURE',
        'Credit is subject to assessment, terms and applicable regulation. Information shown here does not guarantee approval.',
        'ALL'
    )
ON CONFLICT (disclosure_code) DO NOTHING;

INSERT INTO recommendation_compliance_policies (
    policy_code,
    policy_version,
    banned_phrases,
    advisory_markers,
    pressure_markers,
    blocked_ctas,
    allowed_ctas
)
VALUES
(
    'DEFAULT_RECOMMENDATION_POLICY',
    '2026-04-08',
    '[
        "do this now",
        "must do",
        "guaranteed reward",
        "best option for you",
        "you should choose",
        "earn now",
        "instant cash"
    ]'::jsonb,
    '[
        "best for you",
        "suitable for you",
        "recommended for your needs",
        "based on your circumstances"
    ]'::jsonb,
    '[
        "now",
        "immediately",
        "urgent",
        "don''t miss out",
        "last chance"
    ]'::jsonb,
    '[
        "Claim now",
        "Earn now",
        "Take offer now"
    ]'::jsonb,
    '[
        "Learn more",
        "View details",
        "See eligibility",
        "Start application",
        "View progress"
    ]'::jsonb
)
ON CONFLICT (policy_code) DO NOTHING;

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
    'FIRST_TRANSACTION_INFO',
    'NEXT_BEST_ACTION',
    'Card usage activity is available',
    'If you choose to complete your first qualifying transaction, you may qualify for a reward once the transaction is completed successfully.',
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
    'View progress',
    'VIEW_PROGRESS',
    TRUE,
    FALSE,
    TRUE,
    '["TCF","BANKING_CODE"]'::jsonb,
    'v1.0'
),
(
    'PROGRESS_COMPLETE_INFO',
    'INFO',
    'Your referral is complete',
    'You can review your completed journey and any rewards that were applied once qualifying requirements were met.',
    'View progress',
    'VIEW_PROGRESS',
    TRUE,
    FALSE,
    TRUE,
    '["TCF","BANKING_CODE"]'::jsonb,
    'v1.0'
)
ON CONFLICT (template_code) DO NOTHING;

COMMIT;