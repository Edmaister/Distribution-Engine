CREATE TABLE IF NOT EXISTS sponsor_invoices (
    invoice_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    tenant_code TEXT NOT NULL,
    sponsor_code TEXT NOT NULL,
    sponsor_name TEXT NOT NULL,

    contract_id UUID
        REFERENCES funding_contracts(contract_id),

    invoice_number TEXT NOT NULL UNIQUE,

    invoice_period_start DATE,
    invoice_period_end DATE,
    due_date DATE,

    currency TEXT NOT NULL DEFAULT 'ZAR',

    subtotal_amount NUMERIC(18,2) NOT NULL DEFAULT 0,
    vat_amount NUMERIC(18,2) NOT NULL DEFAULT 0,
    total_amount NUMERIC(18,2) NOT NULL DEFAULT 0,
    paid_amount NUMERIC(18,2) NOT NULL DEFAULT 0,
    outstanding_amount NUMERIC(18,2) NOT NULL DEFAULT 0,

    status TEXT NOT NULL DEFAULT 'DRAFT',

    issued_at TIMESTAMP,
    paid_at TIMESTAMP,

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sponsor_invoice_lines (
    line_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    invoice_id UUID NOT NULL
        REFERENCES sponsor_invoices(invoice_id)
        ON DELETE CASCADE,

    line_type TEXT NOT NULL DEFAULT 'UTILISATION',
    description TEXT NOT NULL,

    quantity NUMERIC(18,2) NOT NULL DEFAULT 1,
    unit_amount NUMERIC(18,2) NOT NULL,
    line_amount NUMERIC(18,2) NOT NULL,

    reward_id UUID,
    allocation_id UUID,
    settlement_id UUID,
    source_ledger_id UUID
        REFERENCES funding_contract_ledger(ledger_id),

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sponsor_invoice_payments (
    payment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    invoice_id UUID NOT NULL
        REFERENCES sponsor_invoices(invoice_id)
        ON DELETE CASCADE,

    amount NUMERIC(18,2) NOT NULL,
    payment_reference TEXT,
    paid_at TIMESTAMP NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sponsor_invoice_payment_reversals (
    reversal_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    payment_id UUID NOT NULL
        REFERENCES sponsor_invoice_payments(payment_id),

    invoice_id UUID NOT NULL
        REFERENCES sponsor_invoices(invoice_id),

    amount NUMERIC(18,2) NOT NULL,
    reason TEXT NOT NULL,
    reversed_by TEXT,
    reversed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sponsor_payment_receipts (
    receipt_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    tenant_code TEXT NOT NULL,
    sponsor_code TEXT NOT NULL,
    currency TEXT NOT NULL DEFAULT 'ZAR',

    amount NUMERIC(18,2) NOT NULL,
    applied_amount NUMERIC(18,2) NOT NULL DEFAULT 0,
    unapplied_amount NUMERIC(18,2) NOT NULL DEFAULT 0,

    payment_reference TEXT,
    received_at TIMESTAMP NOT NULL DEFAULT NOW(),
    status TEXT NOT NULL DEFAULT 'UNAPPLIED',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sponsor_payment_allocations (
    allocation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    receipt_id UUID NOT NULL
        REFERENCES sponsor_payment_receipts(receipt_id),

    invoice_id UUID NOT NULL
        REFERENCES sponsor_invoices(invoice_id),

    payment_id UUID NOT NULL
        REFERENCES sponsor_invoice_payments(payment_id),

    amount NUMERIC(18,2) NOT NULL,
    allocated_by TEXT,
    allocated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sponsor_payment_allocation_reversals (
    reversal_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    allocation_id UUID NOT NULL
        REFERENCES sponsor_payment_allocations(allocation_id),

    receipt_id UUID NOT NULL
        REFERENCES sponsor_payment_receipts(receipt_id),

    invoice_id UUID NOT NULL
        REFERENCES sponsor_invoices(invoice_id),

    payment_id UUID NOT NULL
        REFERENCES sponsor_invoice_payments(payment_id),

    amount NUMERIC(18,2) NOT NULL,
    reason TEXT NOT NULL,
    reversed_by TEXT,
    reversed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sponsor_invoices_tenant
ON sponsor_invoices (tenant_code);

CREATE INDEX IF NOT EXISTS idx_sponsor_invoices_sponsor
ON sponsor_invoices (tenant_code, sponsor_code);

CREATE INDEX IF NOT EXISTS idx_sponsor_invoices_contract
ON sponsor_invoices (contract_id);

CREATE INDEX IF NOT EXISTS idx_sponsor_invoices_status
ON sponsor_invoices (status);

CREATE INDEX IF NOT EXISTS idx_sponsor_invoice_lines_invoice
ON sponsor_invoice_lines (invoice_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_sponsor_invoice_lines_source_ledger
ON sponsor_invoice_lines (source_ledger_id)
WHERE source_ledger_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_sponsor_invoice_payments_invoice
ON sponsor_invoice_payments (invoice_id);

CREATE INDEX IF NOT EXISTS idx_sponsor_invoice_payment_reversals_payment
ON sponsor_invoice_payment_reversals (payment_id);

CREATE INDEX IF NOT EXISTS idx_sponsor_invoice_payment_reversals_invoice
ON sponsor_invoice_payment_reversals (invoice_id);

CREATE INDEX IF NOT EXISTS idx_sponsor_payment_receipts_sponsor
ON sponsor_payment_receipts (tenant_code, sponsor_code);

CREATE INDEX IF NOT EXISTS idx_sponsor_payment_receipts_status
ON sponsor_payment_receipts (status);

CREATE INDEX IF NOT EXISTS idx_sponsor_payment_allocations_receipt
ON sponsor_payment_allocations (receipt_id);

CREATE INDEX IF NOT EXISTS idx_sponsor_payment_allocations_invoice
ON sponsor_payment_allocations (invoice_id);

CREATE INDEX IF NOT EXISTS idx_sponsor_payment_allocation_reversals_allocation
ON sponsor_payment_allocation_reversals (allocation_id);
