# Sponsor Billing

Sponsor billing is the Phase 11.4 commercial layer that turns funded reward
activity into sponsor-facing invoices and payment records.

## Current Capability

The platform now supports:

- Sponsor invoice creation
- Invoice lines
- Invoice payment records
- Invoice issuing
- Paid and partially paid invoice status
- Invoice generation from unbilled funding contract utilisation
- Sponsor statement read model for invoices, payments, and outstanding balances
- Billing dashboard read model for operational totals, status counts, and overdue exposure
- Payment reversal records and invoice balance correction
- VAT reporting read model with invoice-level detail and grouped totals
- Scheduled-generation service and admin trigger with dry-run preview
- Payment receipt allocation across one or more invoices
- Unapplied sponsor payment credit tracking
- Payment allocation reversal records
- Sponsor portal read APIs for dashboard, invoices, statements, receipts, wallet
  balance, funding forecasts, contracts, and utilisation ledger activity

## Data Model

Primary tables:

- `sponsor_invoices`
- `sponsor_invoice_lines`
- `sponsor_invoice_payments`
- `sponsor_invoice_payment_reversals`
- `sponsor_payment_receipts`
- `sponsor_payment_allocations`
- `sponsor_payment_allocation_reversals`

Generated invoice lines can link back to `funding_contract_ledger.ledger_id`
through `source_ledger_id`. This makes billing idempotent: a utilised contract
ledger entry can only appear on one invoice line.

## Admin API

Manual invoice:

```text
POST /admin/funding/sponsor-billing/invoices
```

Generate invoice from unbilled contract utilisation:

```text
POST /admin/funding/sponsor-billing/invoices/generate-from-utilisation
```

Run scheduled-generation preview or execution:

```text
POST /admin/funding/sponsor-billing/scheduled-generation
```

List invoices:

```text
GET /admin/funding/sponsor-billing/invoices?tenant_code=FNB
```

Get invoice detail:

```text
GET /admin/funding/sponsor-billing/invoices/{invoice_id}
```

Generate sponsor statement:

```text
GET /admin/funding/sponsor-billing/statements?tenant_code=FNB&sponsor_code=BOXER&period_start=2026-06-01&period_end=2026-06-30
```

Generate billing dashboard:

```text
GET /admin/funding/sponsor-billing/dashboard?tenant_code=FNB&period_start=2026-06-01&period_end=2026-06-30
```

Generate VAT report:

```text
GET /admin/funding/sponsor-billing/vat-report?tenant_code=FNB&period_start=2026-06-01&period_end=2026-06-30
```

Issue invoice:

```text
POST /admin/funding/sponsor-billing/invoices/{invoice_id}/issue
```

Record payment:

```text
POST /admin/funding/sponsor-billing/invoices/{invoice_id}/payments
```

Allocate a sponsor payment receipt across invoices:

```text
POST /admin/funding/sponsor-billing/payment-receipts
```

Get a sponsor payment receipt:

```text
GET /admin/funding/sponsor-billing/payment-receipts/{receipt_id}
```

Reverse payment:

```text
POST /admin/funding/sponsor-billing/payments/{payment_id}/reversals
```

Reverse payment allocation:

```text
POST /admin/funding/sponsor-billing/payment-allocations/{allocation_id}/reversals
```

## Sponsor Portal API

Sponsor-facing read endpoints are scoped by tenant and sponsor:

```text
GET /v1/tenants/{tenant_code}/sponsors/{sponsor_code}/billing/dashboard
GET /v1/tenants/{tenant_code}/sponsors/{sponsor_code}/billing/invoices
GET /v1/tenants/{tenant_code}/sponsors/{sponsor_code}/billing/invoices/{invoice_id}
GET /v1/tenants/{tenant_code}/sponsors/{sponsor_code}/billing/statements
GET /v1/tenants/{tenant_code}/sponsors/{sponsor_code}/billing/payment-receipts
GET /v1/tenants/{tenant_code}/sponsors/{sponsor_code}/billing/payment-receipts/{receipt_id}
GET /v1/tenants/{tenant_code}/sponsors/{sponsor_code}/billing/wallet
GET /v1/tenants/{tenant_code}/sponsors/{sponsor_code}/billing/contracts
GET /v1/tenants/{tenant_code}/sponsors/{sponsor_code}/billing/contracts/{contract_id}
GET /v1/tenants/{tenant_code}/sponsors/{sponsor_code}/billing/contracts/{contract_id}/ledger
GET /v1/tenants/{tenant_code}/sponsors/{sponsor_code}/billing/forecast
```

These endpoints are read-only and use partner/admin API-key access. They enforce
tenant access and hide invoice, receipt, contract, or ledger details that do not
belong to the requested sponsor.

## Generated Invoice Flow

```text
Funding contract budget utilised
  -> BUDGET_UTILISED ledger entry
  -> Generate sponsor invoice for billing period
  -> Create one invoice line per unbilled utilisation ledger entry
  -> Optional issue
  -> Payment recorded
  -> Invoice becomes PARTIALLY_PAID or PAID
  -> Payment reversal can restore outstanding balance when a correction is needed
```

## Payment Allocation Flow

```text
Sponsor payment received
  -> Payment receipt created
  -> Receipt allocated to one or more issued invoices
  -> Invoice paid/outstanding balances updated
  -> Unapplied amount remains on the receipt as sponsor credit
  -> Allocation reversal restores invoice outstanding balance and unapplied credit
```

## Scheduled Generation

The scheduled generation endpoint scans active funding contracts for a tenant
and billing period, then finds unbilled `BUDGET_UTILISED` ledger entries.

By default it runs in `dry_run` mode. In dry-run mode it returns which contracts
are ready, skipped, or failed without creating invoices. Setting
`dry_run=false` creates invoices and can optionally issue them immediately when
`issue=true`.

## Remaining Work

The Phase 11.4 application foundation is in place. Remaining operational work is
to apply the billing migration in each live database and, if needed, add a
dedicated sponsor identity model instead of partner-level sponsor scoping.
