# scripts/ - Operational Utilities

These scripts are integrated with the platform's shared `utils/` modules for
database access, Kafka, and logging. They help SAs and DevOps with
initialization, seeding, backfilling, nightly refreshes, and health checks.

## Prerequisites

- Python 3.10+
- Env vars configured:
  - `APP_DB_DSN`, for example `postgresql://user:pass@localhost:5432/referrals`
  - `APP_KAFKA_BROKER` optional
  - `APP_KAFKA_CLIENT`, one of `confluent`, `kafka-python`, or `stdout`
  - `LOG_LEVEL`, default `INFO`
  - Optional crypto: `UCN_ENC_KEY` or `UCN_SALT`

## Scripts

- `init_db.py` - Apply numbered SQL migrations in `dp/migrations` in order.
- `seed_db.py` - Apply SQL seeds in `dp/seeds` in order.
- `backfill_events.py` - Import historical enterprise events into `enterprise_events`.
- `refresh_recommendations.py` - Precompute user NBAs and campaign insights.
- `refresh_materialized_views.py` - Refresh admin materialized views.
- `health_check.py` - Validate DB and Kafka connectivity.
- `check_distribution_migrations.py` - Check distribution marketplace migration file readiness, with optional live table checks.
- `distribution_marketplace_smoke.py` - Smoke-test the live distribution marketplace API.
- `multi_currency_smoke.py` - Smoke-test the live multi-currency API.
- `admin_audit_smoke.py` - Smoke-test that sensitive admin actions write audit rows.
- `core_role_journey_smoke.py` - Smoke-test consumer, producer, distributor, and admin workspace sessions, read paths, and scope rejection.
- `target_state_smoke.py` - Run a target-state smoke pack across readiness, enterprise events, role journeys, multi-currency, distribution, admin audit, and metrics.

## Usage

```bash
python scripts/init_db.py
python scripts/seed_db.py
python scripts/backfill_events.py --file ./events.csv
python scripts/refresh_recommendations.py --sticker PREMIER --tenant FNB --top-k 3
python scripts/refresh_materialized_views.py
python scripts/health_check.py
python scripts/check_distribution_migrations.py
python scripts/distribution_marketplace_smoke.py
python scripts/multi_currency_smoke.py
python scripts/admin_audit_smoke.py
python scripts/core_role_journey_smoke.py
python scripts/target_state_smoke.py
python scripts/target_state_smoke.py --write-flow
```

## Migration Replay Contract

Active migrations must live in `dp/migrations` and use the
`NNN_description.sql` naming convention. Historical unnumbered SQL artifacts
belong in `dp/legacy_migrations` until they are renumbered, made idempotent, and
proved safe to replay from an empty database.
