# Funding Forecasting

Funding forecasting is Phase 11.5. It projects runway and funding needs from
recent burn activity.

## Current Capability

The platform now supports:

- Funding account burn-rate forecasts
- Funding account days-remaining projection
- Funding account recommended top-up calculation
- Sponsor wallet burn-rate forecasts
- Sponsor wallet days-remaining projection
- Sponsor wallet recommended top-up calculation
- Active sponsor contract exhaustion forecasts
- Aggregate sponsor contract runway
- Settlement exposure forecasts by tenant, provider, and currency
- Projected settlement pressure from recent settled throughput
- Forecast risk evaluation for sponsor wallets, sponsor contracts, and
  settlement exposure

## Admin API

List funding account forecasts:

```text
GET /admin/funding/forecast
```

Get one funding account forecast:

```text
GET /admin/funding/forecast/{account_id}
```

List sponsor funding forecasts:

```text
GET /admin/funding/sponsor-forecast
```

Get one sponsor funding forecast:

```text
GET /admin/funding/sponsor-forecast/{tenant_code}/{sponsor_code}
```

List settlement exposure forecasts:

```text
GET /admin/funding/settlement-exposure-forecast
```

Run funding alert and forecast risk evaluation:

```text
POST /admin/funding/alerts/run
```

This evaluates persisted funding account alerts and returns non-persisted
forecast risk items for sponsor wallets, sponsor contract exhaustion, and
settlement exposure. Funding account alerts remain persisted in
`funding_alerts`; sponsor and settlement forecast risks are returned in the run
response so they can be operationalized without changing the existing
account-based alert table.

## Sponsor Portal API

Get a sponsor-facing forecast:

```text
GET /v1/tenants/{tenant_code}/sponsors/{sponsor_code}/billing/forecast
```

This read-only endpoint exposes sponsor wallet runway, recommended top-up,
active contract runway, and aggregate contract exhaustion status for the
requested sponsor.

## Forecast Inputs

Funding account forecasts use recent funding transactions.

Sponsor wallet forecasts use recent sponsor wallet ledger activity. `RESERVE`
and `DEBIT` entries count as burn because they represent committed or consumed
sponsor funding.

Sponsor contract forecasts use active funding contract ledger activity.
`BUDGET_COMMITTED` and `BUDGET_UTILISED` entries count as contract burn.

Settlement exposure forecasts use open fulfilment settlement ledger entries as
current exposure. Recent `SETTLED` ledger entries are used to estimate projected
settlement pressure across the buffer window.

## Forecast Output

Forecasts include:

- Current balance
- Reserved amount
- Available balance
- Burn window
- Total burn
- Average burn per day
- Days remaining
- Target buffer
- Recommended top-up
- Forecast status

Forecast status values:

- `DEPLETED`
- `CRITICAL`
- `LOW`
- `WATCH`
- `HEALTHY`
- `NO_BURN`

## Remaining Work

Remaining Phase 11.5 work:

- Optional schema hardening for first-class sponsor and settlement alert records
  if operations need acknowledgement and resolution workflows for those risk
  scopes
