-- Canonical Insurance journey proof seed. This creates one completed
-- Insurance outcome that can be traced across Producer, Distributor, Consumer,
-- and Admin operating surfaces.

INSERT INTO referrer_codes (
    referrer_code_id,
    referrer_ucn,
    referrer_ucn_hash,
    referral_code,
    gaming_handle,
    sticker,
    tenant_code,
    segment
)
VALUES (
    '11111111-1111-4111-8111-111111111111',
    'DIST-INSURANCE-ADVOCATE',
    'hash-DIST-INSURANCE-ADVOCATE',
    'INSURE-ADVOCATE',
    'insurance_advocate',
    'INSURANCE',
    'FNB',
    'INSURANCE_SEGMENT'
)
ON CONFLICT (referrer_code_id) DO UPDATE
SET referrer_ucn = EXCLUDED.referrer_ucn,
    referral_code = EXCLUDED.referral_code,
    gaming_handle = EXCLUDED.gaming_handle,
    sticker = EXCLUDED.sticker,
    tenant_code = EXCLUDED.tenant_code,
    segment = EXCLUDED.segment,
    updated_at = NOW();

INSERT INTO referral_instances (
    referral_track_id,
    referrer_code_id,
    referral_code,
    referrer_ucn,
    referee_ucn,
    tenant_code,
    status,
    product,
    sub_product,
    journey_code,
    journey_version,
    progress_percent,
    progress_band,
    display_status,
    next_milestone,
    accepted_terms,
    accepted_terms_at,
    is_complete,
    completed_at,
    updated_at
)
VALUES (
    '22222222-2222-4222-8222-222222222222',
    '11111111-1111-4111-8111-111111111111',
    'INSURE-ADVOCATE',
    'DIST-INSURANCE-ADVOCATE',
    'POLICY-CUSTOMER-001',
    'FNB',
    'COMPLETED',
    'INSURANCE',
    'FUNERAL_PLAN',
    'INSURANCE_POLICY',
    'v1',
    100,
    'COMPLETE',
    'Policy activated',
    NULL,
    TRUE,
    NOW(),
    TRUE,
    NOW(),
    NOW()
)
ON CONFLICT (referral_track_id) DO UPDATE
SET status = EXCLUDED.status,
    product = EXCLUDED.product,
    sub_product = EXCLUDED.sub_product,
    journey_code = EXCLUDED.journey_code,
    journey_version = EXCLUDED.journey_version,
    progress_percent = EXCLUDED.progress_percent,
    progress_band = EXCLUDED.progress_band,
    display_status = EXCLUDED.display_status,
    next_milestone = EXCLUDED.next_milestone,
    accepted_terms = EXCLUDED.accepted_terms,
    is_complete = EXCLUDED.is_complete,
    completed_at = EXCLUDED.completed_at,
    updated_at = NOW();

INSERT INTO distribution_distributors (
    distributor_id,
    tenant_code,
    distributor_code,
    distributor_name,
    distributor_type,
    status,
    channels,
    segments,
    regions,
    capabilities,
    eligibility,
    metadata
)
VALUES (
    '33333333-3333-4333-8333-333333333333',
    'FNB',
    'DIST-INSURANCE-ADVOCATE',
    'Insurance Advocate Network',
    'AFFILIATE',
    'ACTIVE',
    ARRAY['LINK', 'WHATSAPP']::TEXT[],
    ARRAY['INSURANCE']::TEXT[],
    ARRAY['ZA']::TEXT[],
    '{"insurance":true,"digital_distribution":true}'::jsonb,
    '{"status":"ELIGIBLE"}'::jsonb,
    '{"proof":"INSURANCE_JOURNEY"}'::jsonb
)
ON CONFLICT (tenant_code, distributor_code) DO UPDATE
SET distributor_name = EXCLUDED.distributor_name,
    distributor_type = EXCLUDED.distributor_type,
    status = EXCLUDED.status,
    channels = EXCLUDED.channels,
    segments = EXCLUDED.segments,
    regions = EXCLUDED.regions,
    capabilities = EXCLUDED.capabilities,
    eligibility = EXCLUDED.eligibility,
    metadata = EXCLUDED.metadata,
    updated_at = NOW();

INSERT INTO distribution_distributor_wallets (
    wallet_id,
    distributor_id,
    tenant_code,
    distributor_code,
    currency,
    current_balance,
    available_balance,
    status,
    metadata
)
VALUES (
    '44444444-4444-4444-8444-444444444444',
    '33333333-3333-4333-8333-333333333333',
    'FNB',
    'DIST-INSURANCE-ADVOCATE',
    'ZAR',
    35.00,
    35.00,
    'ACTIVE',
    '{"proof":"INSURANCE_JOURNEY"}'::jsonb
)
ON CONFLICT (distributor_id, currency) DO UPDATE
SET current_balance = EXCLUDED.current_balance,
    available_balance = EXCLUDED.available_balance,
    status = EXCLUDED.status,
    metadata = EXCLUDED.metadata,
    updated_at = NOW();

INSERT INTO distribution_opportunities (
    opportunity_id,
    tenant_code,
    sponsor_code,
    campaign_code,
    opportunity_code,
    title,
    description,
    product_code,
    product_name,
    opportunity_status,
    target_segments,
    target_regions,
    target_channels,
    distributor_types,
    estimated_reward_amount,
    estimated_commission_amount,
    total_budget,
    remaining_budget,
    published_at,
    metadata
)
VALUES (
    '55555555-5555-4555-8555-555555555555',
    'FNB',
    'INSURECO',
    'INS-FUNERAL-2026',
    'OPP-INS-FUNERAL-2026',
    'Funeral policy activation',
    'Insurance proof opportunity for policy issue and first-premium activation.',
    'INSURANCE',
    'Funeral Plan',
    'PUBLISHED',
    ARRAY['INSURANCE']::TEXT[],
    ARRAY['ZA']::TEXT[],
    ARRAY['LINK', 'WHATSAPP']::TEXT[],
    ARRAY['AFFILIATE']::TEXT[],
    250.00,
    35.00,
    5000.00,
    4750.00,
    NOW(),
    '{"journey_code":"INSURANCE_POLICY","proof":"INSURANCE_JOURNEY"}'::jsonb
)
ON CONFLICT (tenant_code, opportunity_code) DO UPDATE
SET title = EXCLUDED.title,
    description = EXCLUDED.description,
    product_code = EXCLUDED.product_code,
    product_name = EXCLUDED.product_name,
    opportunity_status = EXCLUDED.opportunity_status,
    estimated_reward_amount = EXCLUDED.estimated_reward_amount,
    estimated_commission_amount = EXCLUDED.estimated_commission_amount,
    total_budget = EXCLUDED.total_budget,
    remaining_budget = EXCLUDED.remaining_budget,
    metadata = EXCLUDED.metadata,
    updated_at = NOW();

INSERT INTO distribution_offer_routes (
    route_id,
    tenant_code,
    opportunity_id,
    distributor_id,
    route_status,
    route_score,
    route_reasons,
    accepted_at,
    metadata
)
VALUES (
    '66666666-6666-4666-8666-666666666666',
    'FNB',
    '55555555-5555-4555-8555-555555555555',
    '33333333-3333-4333-8333-333333333333',
    'ACCEPTED',
    96.00,
    '["Insurance audience fit","Active advocate"]'::jsonb,
    NOW(),
    '{"proof":"INSURANCE_JOURNEY"}'::jsonb
)
ON CONFLICT (opportunity_id, distributor_id) DO UPDATE
SET route_status = EXCLUDED.route_status,
    route_score = EXCLUDED.route_score,
    route_reasons = EXCLUDED.route_reasons,
    accepted_at = EXCLUDED.accepted_at,
    metadata = EXCLUDED.metadata,
    updated_at = NOW();

INSERT INTO distribution_route_referral_links (
    route_id,
    referral_track_id,
    tenant_code,
    distributor_id,
    opportunity_id,
    link_status,
    metadata
)
VALUES (
    '66666666-6666-4666-8666-666666666666',
    '22222222-2222-4222-8222-222222222222',
    'FNB',
    '33333333-3333-4333-8333-333333333333',
    '55555555-5555-4555-8555-555555555555',
    'ACTIVE',
    '{"proof":"INSURANCE_JOURNEY"}'::jsonb
)
ON CONFLICT (referral_track_id) DO UPDATE
SET route_id = EXCLUDED.route_id,
    distributor_id = EXCLUDED.distributor_id,
    opportunity_id = EXCLUDED.opportunity_id,
    link_status = EXCLUDED.link_status,
    metadata = EXCLUDED.metadata,
    updated_at = NOW();

INSERT INTO referral_rewards (
    reward_id,
    referral_track_id,
    reward_type,
    product,
    amount,
    tenant_code
)
VALUES (
    '77777777-7777-4777-8777-777777777777',
    '22222222-2222-4222-8222-222222222222',
    'CASH',
    'INSURANCE',
    250.00,
    'FNB'
)
ON CONFLICT (referral_track_id, reward_type) DO UPDATE
SET product = EXCLUDED.product,
    amount = EXCLUDED.amount,
    tenant_code = EXCLUDED.tenant_code;

INSERT INTO distribution_commission_events (
    commission_event_id,
    tenant_code,
    distributor_id,
    distributor_code,
    wallet_id,
    sponsor_code,
    campaign_code,
    source_event_id,
    activity_type,
    sale_amount,
    commission_amount,
    commission_status,
    credited_at,
    correlation_id,
    metadata
)
VALUES (
    '88888888-8888-4888-8888-888888888888',
    'FNB',
    '33333333-3333-4333-8333-333333333333',
    'DIST-INSURANCE-ADVOCATE',
    '44444444-4444-4444-8444-444444444444',
    'INSURECO',
    'INS-FUNERAL-2026',
    '22222222-2222-4222-8222-222222222222',
    'CUSTOMER_OUTCOME',
    250.00,
    35.00,
    'CREDITED',
    NOW(),
    '22222222-2222-4222-8222-222222222222',
    '{"proof":"INSURANCE_JOURNEY"}'::jsonb
)
ON CONFLICT (tenant_code, source_event_id) DO UPDATE
SET commission_amount = EXCLUDED.commission_amount,
    commission_status = EXCLUDED.commission_status,
    credited_at = EXCLUDED.credited_at,
    correlation_id = EXCLUDED.correlation_id,
    metadata = EXCLUDED.metadata,
    updated_at = NOW();

INSERT INTO distribution_distributor_wallet_ledger (
    ledger_id,
    wallet_id,
    distributor_id,
    tenant_code,
    transaction_type,
    amount,
    balance_before,
    balance_after,
    correlation_id,
    metadata
)
VALUES (
    '99999999-9999-4999-8999-999999999999',
    '44444444-4444-4444-8444-444444444444',
    '33333333-3333-4333-8333-333333333333',
    'FNB',
    'CREDIT',
    35.00,
    0.00,
    35.00,
    '22222222-2222-4222-8222-222222222222',
    '{"source_event_id":"22222222-2222-4222-8222-222222222222","proof":"INSURANCE_JOURNEY"}'::jsonb
)
ON CONFLICT (ledger_id) DO UPDATE
SET amount = EXCLUDED.amount,
    balance_after = EXCLUDED.balance_after,
    correlation_id = EXCLUDED.correlation_id,
    metadata = EXCLUDED.metadata;

INSERT INTO sponsor_invoices (
    invoice_id,
    tenant_code,
    sponsor_code,
    sponsor_name,
    invoice_number,
    invoice_period_start,
    invoice_period_end,
    due_date,
    currency,
    subtotal_amount,
    vat_amount,
    total_amount,
    outstanding_amount,
    status,
    issued_at,
    metadata
)
VALUES (
    'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
    'FNB',
    'INSURECO',
    'InsureCo',
    'INV-INSURANCE-PROOF-2026',
    CURRENT_DATE,
    CURRENT_DATE,
    CURRENT_DATE + INTERVAL '7 days',
    'ZAR',
    250.00,
    0.00,
    250.00,
    250.00,
    'ISSUED',
    NOW(),
    '{"referral_track_id":"22222222-2222-4222-8222-222222222222","proof":"INSURANCE_JOURNEY"}'::jsonb
)
ON CONFLICT (invoice_number) DO UPDATE
SET subtotal_amount = EXCLUDED.subtotal_amount,
    total_amount = EXCLUDED.total_amount,
    outstanding_amount = EXCLUDED.outstanding_amount,
    status = EXCLUDED.status,
    metadata = EXCLUDED.metadata,
    updated_at = NOW();

INSERT INTO sponsor_invoice_lines (
    line_id,
    invoice_id,
    line_type,
    description,
    quantity,
    unit_amount,
    line_amount,
    reward_id,
    metadata
)
VALUES (
    'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',
    'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
    'UTILISATION',
    'Insurance policy activation outcome',
    1,
    250.00,
    250.00,
    '77777777-7777-4777-8777-777777777777',
    '{"referral_track_id":"22222222-2222-4222-8222-222222222222","proof":"INSURANCE_JOURNEY"}'::jsonb
)
ON CONFLICT (line_id) DO UPDATE
SET line_amount = EXCLUDED.line_amount,
    reward_id = EXCLUDED.reward_id,
    metadata = EXCLUDED.metadata;

INSERT INTO fulfilment_settlement_ledger (
    settlement_id,
    tenant_code,
    reward_id,
    audit_id,
    provider_key,
    provider_reference,
    amount,
    currency,
    status,
    settlement_date,
    settled_at
)
VALUES (
    'cccccccc-cccc-4ccc-8ccc-cccccccccccc',
    'FNB',
    '77777777-7777-4777-8777-777777777777',
    'dddddddd-dddd-4ddd-8ddd-dddddddddddd',
    'TENANT_INSTRUCTION_PROVIDER',
    'INSURANCE-PROOF-SETTLED',
    250.00,
    'ZAR',
    'SETTLED',
    NOW(),
    NOW()
)
ON CONFLICT (settlement_id) DO UPDATE
SET provider_key = EXCLUDED.provider_key,
    provider_reference = EXCLUDED.provider_reference,
    amount = EXCLUDED.amount,
    status = EXCLUDED.status,
    settlement_date = EXCLUDED.settlement_date,
    settled_at = EXCLUDED.settled_at,
    updated_at = NOW();
