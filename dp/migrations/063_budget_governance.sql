CREATE TABLE IF NOT EXISTS funding_budget_adjustment_requests (
    request_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    contract_id UUID NOT NULL
        REFERENCES funding_contracts(contract_id),

    tenant_code TEXT NOT NULL,
    sponsor_code TEXT NOT NULL,

    adjustment_type TEXT NOT NULL DEFAULT 'INCREASE',
    requested_amount NUMERIC(18,2) NOT NULL,
    reason TEXT,

    request_status TEXT NOT NULL DEFAULT 'PENDING',

    requested_by TEXT,
    decided_by TEXT,
    decision_reason TEXT,
    correlation_id TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    decided_at TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_funding_budget_adjustment_requests_contract
ON funding_budget_adjustment_requests(contract_id);

CREATE INDEX IF NOT EXISTS idx_funding_budget_adjustment_requests_tenant
ON funding_budget_adjustment_requests(tenant_code);

CREATE INDEX IF NOT EXISTS idx_funding_budget_adjustment_requests_sponsor
ON funding_budget_adjustment_requests(sponsor_code);

CREATE INDEX IF NOT EXISTS idx_funding_budget_adjustment_requests_status
ON funding_budget_adjustment_requests(request_status);

CREATE TABLE IF NOT EXISTS funding_budget_transfer_requests (
    request_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    source_contract_id UUID NOT NULL
        REFERENCES funding_contracts(contract_id),
    target_contract_id UUID NOT NULL
        REFERENCES funding_contracts(contract_id),

    tenant_code TEXT NOT NULL,
    source_sponsor_code TEXT NOT NULL,
    target_sponsor_code TEXT NOT NULL,

    requested_amount NUMERIC(18,2) NOT NULL,
    reason TEXT,

    request_status TEXT NOT NULL DEFAULT 'PENDING',

    requested_by TEXT,
    decided_by TEXT,
    decision_reason TEXT,
    correlation_id TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    decided_at TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_funding_budget_transfer_requests_source
ON funding_budget_transfer_requests(source_contract_id);

CREATE INDEX IF NOT EXISTS idx_funding_budget_transfer_requests_target
ON funding_budget_transfer_requests(target_contract_id);

CREATE INDEX IF NOT EXISTS idx_funding_budget_transfer_requests_tenant
ON funding_budget_transfer_requests(tenant_code);

CREATE INDEX IF NOT EXISTS idx_funding_budget_transfer_requests_status
ON funding_budget_transfer_requests(request_status);

CREATE TABLE IF NOT EXISTS funding_budget_exceptions (
    exception_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    contract_id UUID
        REFERENCES funding_contracts(contract_id),

    tenant_code TEXT NOT NULL,
    sponsor_code TEXT,

    exception_type TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'WARNING',
    exception_message TEXT NOT NULL,
    amount NUMERIC(18,2),

    exception_status TEXT NOT NULL DEFAULT 'OPEN',

    detected_by TEXT,
    resolved_by TEXT,
    resolution_reason TEXT,
    correlation_id TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_funding_budget_exceptions_contract
ON funding_budget_exceptions(contract_id);

CREATE INDEX IF NOT EXISTS idx_funding_budget_exceptions_tenant
ON funding_budget_exceptions(tenant_code);

CREATE INDEX IF NOT EXISTS idx_funding_budget_exceptions_status
ON funding_budget_exceptions(exception_status);

CREATE INDEX IF NOT EXISTS idx_funding_budget_exceptions_type
ON funding_budget_exceptions(exception_type);

CREATE TABLE IF NOT EXISTS funding_budget_approval_policies (
    policy_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    tenant_code TEXT NOT NULL,
    sponsor_code TEXT,
    request_type TEXT NOT NULL,

    min_amount NUMERIC(18,2) NOT NULL DEFAULT 0,
    max_amount NUMERIC(18,2),

    approval_level TEXT NOT NULL,
    required_role TEXT,
    policy_status TEXT NOT NULL DEFAULT 'ACTIVE',
    priority INTEGER NOT NULL DEFAULT 100,

    description TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_funding_budget_approval_policies_tenant
ON funding_budget_approval_policies(tenant_code);

CREATE INDEX IF NOT EXISTS idx_funding_budget_approval_policies_sponsor
ON funding_budget_approval_policies(sponsor_code);

CREATE INDEX IF NOT EXISTS idx_funding_budget_approval_policies_type
ON funding_budget_approval_policies(request_type);

CREATE INDEX IF NOT EXISTS idx_funding_budget_approval_policies_status
ON funding_budget_approval_policies(policy_status);
