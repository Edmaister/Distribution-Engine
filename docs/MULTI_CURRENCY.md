# Multi-Currency

Multi-currency capability supports controlled money movement across currencies
without changing the existing single-currency ZAR flows.

## Current Capability

The platform now supports:

- FX rate capture by tenant, currency pair, source, and rate date
- Latest active FX rate lookup
- Direct and inverse currency conversion quotes
- Persisted conversion quotes for audit evidence
- Cross-border settlement instruction records
- Multi-currency sponsor wallets through existing wallet currency records
- Multi-currency distributor wallets through existing wallet currency records

## Data Model

Primary tables:

- `fx_rates`
- `currency_conversion_quotes`
- `cross_border_settlements`

Existing money tables already carry currency values, including:

- `sponsor_wallets`
- `sponsor_wallet_ledger`
- `funding_contracts`
- `sponsor_invoices`
- `sponsor_payments`
- `distribution_distributor_wallets`
- `distribution_distributor_wallet_ledger`
- `distribution_commission_rules`
- `distribution_commission_events`
- `fulfilment_settlement_ledger`

## Admin API

Create or update an FX rate:

```text
POST /admin/multi-currency/fx-rates
```

List FX rates:

```text
GET /admin/multi-currency/fx-rates
```

Quote a conversion:

```text
POST /admin/multi-currency/quotes
```

Create a cross-border settlement instruction:

```text
POST /admin/multi-currency/cross-border-settlements
```

List cross-border settlement instructions:

```text
GET /admin/multi-currency/cross-border-settlements
```

## FX Rate Flow

```text
Treasury or approved source supplies FX rate
  -> Rate is stored by tenant, currency pair, source, and date
  -> Latest active rate can be resolved for conversion
  -> Inverse conversion can be calculated when only the reverse pair exists
```

## Conversion Flow

```text
Conversion quote is requested
  -> Platform finds latest active FX rate as of the requested date
  -> Source amount is converted into target currency
  -> Quote can be persisted for audit evidence
```

## Cross-Border Settlement Flow

```text
Cross-border settlement instruction is requested
  -> Platform creates a persisted conversion quote
  -> Settlement instruction records source and target currency amounts
  -> FX rate, rate date, corridor, provider, compliance status, and metadata are retained
  -> Settlement can later be processed by the chosen payment or treasury provider
```

## Current Boundaries

This slice creates the multi-currency foundation. It does not yet automate:

- External FX-rate provider ingestion
- FX gain/loss accounting
- Automatic cross-currency debit from sponsor wallets
- Automatic cross-currency distributor wallet payout
- Provider-specific cross-border payment execution

Those are integration hardening steps after the core capability is proven.

## Runtime Smoke Test

After applying `dp/migrations/072_multi_currency.sql`, run:

```powershell
.\.venv_codex\Scripts\python.exe scripts\multi_currency_smoke.py
```

The smoke test verifies:

- `/health`
- OpenAPI route registration
- Admin auth rejection without an API key
- FX rate creation and listing
- Direct conversion quote
- Inverse conversion quote
- Cross-border settlement instruction creation and listing
