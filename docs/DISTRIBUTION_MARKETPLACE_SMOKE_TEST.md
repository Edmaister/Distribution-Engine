# Distribution Marketplace Smoke Test

This runbook proves the distribution marketplace backend without building the
final branded front end.

It covers three things:

- Runtime API checks
- Migration rollout readiness
- End-to-end marketplace flow

## Safety Position

The read-only smoke check does not create data and does not apply migrations.

The full write-flow smoke check creates clearly named smoke-test records in the
configured database. Use it only against a local, dev, or disposable test
environment.

## Local Runtime Smoke Check

Start the API locally, then run:

```powershell
.\.venv_codex\Scripts\python.exe scripts\distribution_marketplace_smoke.py
```

Default values:

- Base URL: `http://127.0.0.1:8000`
- Admin key: `test-admin-key`
- Tenant code: `FNB`

The read-only check verifies:

- `/health` responds
- `/openapi.json` includes the distribution marketplace endpoints
- Admin endpoints reject missing API keys
- Reporting endpoints respond with an admin API key

To point it somewhere else:

```powershell
.\.venv_codex\Scripts\python.exe scripts\distribution_marketplace_smoke.py --base-url http://127.0.0.1:8000 --admin-key test-admin-key --tenant-code FNB
```

## Full End-To-End Write Flow

Only run this when you are comfortable creating smoke-test records:

```powershell
.\.venv_codex\Scripts\python.exe scripts\distribution_marketplace_smoke.py --write-flow
```

The write flow proves:

```text
Distributor is created
  -> Distributor is activated
  -> Distributor wallet is created
  -> Commission rule is created
  -> Opportunity is created and published
  -> Distributor is matched to the opportunity
  -> Offer route is created
  -> Distributor portal can see and accept the offer
  -> Commission is calculated and credited to wallet
  -> Wallet ledger is visible
  -> Compliance review is created and completed
  -> Dispute is created and resolved
  -> Reporting endpoints return marketplace summaries
```

Smoke records use names like:

- `SMOKE-DIST-YYYYMMDDHHMMSS`
- `SMOKE-CAMPAIGN-YYYYMMDDHHMMSS`
- `SMOKE-OPP-YYYYMMDDHHMMSS`

## Migration Rollout Readiness

Before applying migrations in any real environment, run the static migration
check:

```powershell
.\.venv_codex\Scripts\python.exe scripts\check_distribution_migrations.py
```

This confirms the required distribution migration files exist:

- `064_distribution_distributors.sql`
- `065_distribution_distributor_wallets.sql`
- `066_distribution_commissions.sql`
- `067_distribution_opportunities.sql`
- `068_distribution_offer_routes.sql`
- `069_distribution_governance.sql`

Reporting does not need a migration because it reads from the existing
distribution tables.

To also check the configured database tables, set `APP_DB_DSN` and run:

```powershell
.\.venv_codex\Scripts\python.exe scripts\check_distribution_migrations.py --database
```

Required live tables:

- `distribution_distributors`
- `distribution_distributor_wallets`
- `distribution_distributor_wallet_ledger`
- `distribution_commission_rules`
- `distribution_commission_events`
- `distribution_opportunities`
- `distribution_offer_routes`
- `distribution_compliance_reviews`
- `distribution_disputes`
- `distribution_governance_audit`

## Manual API Checklist

If testing from `/docs`, use `x-api-key: test-admin-key` locally.

1. Confirm health and docs:
   - `GET /health`
   - `GET /docs`
   - `GET /openapi.json`

2. Confirm admin auth:
   - Call `GET /admin/distribution/reporting/overview?tenant_code=FNB`
     without an API key and expect rejection.
   - Call the same endpoint with `x-api-key: test-admin-key` and expect a
     successful response.

3. Confirm the full distribution path:
   - Create distributor
   - Activate distributor
   - Create distributor wallet
   - Create commission rule
   - Create opportunity
   - Publish opportunity
   - Match distributors
   - Route opportunity
   - View distributor portal offers
   - Accept or decline offer
   - Calculate commission
   - View wallet ledger
   - Complete governance review
   - Check reporting

## Completion Signal

The distribution marketplace backend is smoke-test ready when these pass:

```powershell
.\.venv_codex\Scripts\python.exe scripts\check_distribution_migrations.py
.\.venv_codex\Scripts\python.exe scripts\distribution_marketplace_smoke.py
.\.venv_codex\Scripts\python.exe -m pytest test\api\distribution test\services\test_distribution_routing_service.py
.\.venv_codex\Scripts\python.exe -m pytest
```
