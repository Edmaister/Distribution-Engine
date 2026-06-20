# Production Readiness Runbook

This runbook describes the operational path for running the Referral Engine API,
worker, migrations, and IDS/Hogan event flow.

## Components

| Component | Purpose | Start command |
| --- | --- | --- |
| API | Public, partner, admin, worker, and enterprise event endpoints | `uvicorn apps.api.main:app --host 0.0.0.0 --port ${PORT:-8000}` |
| Referral worker | Consumes queued referral events and advances journeys | `python -m apps.Workers.sqs_referral_worker` |
| Postgres | Referral, journey, rewards, inbox, and audit storage | External managed DB or local Postgres |
| SQS or local queue | Event handoff from API/inbox to worker | `APP_SQS_QUEUE_URL` or `LOCAL_QUEUE_FILE` |

## Required Environment

Core:

- `APP_ENV`
- `APP_DB_DSN`
- `ADMIN_API_KEY`
- `FINANCE_ADMIN_API_KEY`
- `DISTRIBUTION_ADMIN_API_KEY`
- `SYSTEM_ADMIN_API_KEY`
- `WORKER_SECRET`
- `REFERRAL_CODE_SECRET`

Tenant / partner keys:

- `FNB_PARTNER_API_KEY`
- `FNB_TENANT_USER_API_KEY`
- `FNB_TENANT_ADMIN_API_KEY`
- `PNP_PARTNER_API_KEY`
- `PNP_TENANT_USER_API_KEY`
- `PNP_TENANT_ADMIN_API_KEY`

Queue / cloud:

- `APP_SQS_QUEUE_URL`
- `APP_SQS_DLQ_URL`
- `APP_SQS_MAX_RECEIVE_COUNT`
- `AWS_REGION`

Optional:

- `REDIS_URL`
- `APP_CORS_ALLOW_ORIGINS`
- `APP_VERSION`
- `HEALTH_CACHE_TTL_SECONDS`

Local-only fallback:

- If `APP_SQS_QUEUE_URL` is not set, events are appended to `LOCAL_QUEUE_FILE`
  and can be processed by the local worker flow.

## Database Migration Order

1. Confirm `APP_DB_DSN` points at the intended database.
2. Run migrations:

   ```bash
   python scripts/init_db.py
   ```

3. Apply seeds only when the environment expects seed data:

   ```bash
   python scripts/seed_db.py
   ```

4. Confirm IDS/Hogan inbox exists:

   ```sql
   SELECT COUNT(*) FROM enterprise_event_inbox;
   ```

5. Confirm compatibility view exists:

   ```sql
   SELECT COUNT(*) FROM enterprise_events;
   ```

6. Apply the admin audit migration once admin audit logging is being enabled:

   ```sql
   \i dp/migrations/071_admin_audit_log.sql
   ```

7. Confirm schema-aware readiness:

   ```bash
   curl -fsS http://localhost:8000/readyz
   ```

   `/readyz` includes a `schema` section with grouped checks. If a group is not
   ready, the response lists missing tables and the migration range to apply.

   Schema groups:

   - `foundation`: base referral and enterprise inbox tables through
     `061_enterprise_event_inbox.sql`
   - `funding`: sponsor wallet, funding contract, billing, and budget
     governance tables from `057` through `063`
   - `distribution`: distribution marketplace tables from `064` through `069`
   - `multi_currency`: FX and cross-border settlement tables in
     `072_multi_currency.sql`
   - `admin_audit`: cross-cutting admin action audit table in
     `071_admin_audit_log.sql`

Important: do not run seed scripts in production unless the seed files have
been reviewed for that environment.

## Deployment Paths

### Docker

API image:

```bash
docker build -f Dockerfile -t referrals-api .
```

Worker image:

```bash
docker build -f Dockerfile.worker -t referrals-worker .
```

### Kubernetes / Helm

See:

- `docs/DEPLOY_OPTIONS.md`
- `docs/HELM_MIGRATIONS.md`

The Helm migration hook can run `scripts/init_db.py` before API deployment.
Use out-of-band migrations if production change control requires manual DB
approval.

## Startup Verification

After API startup:

```bash
curl -fsS http://localhost:8000/healthz
curl -fsS http://localhost:8000/readyz
curl -fsS http://localhost:8000/health
```

Expected:

- `/healthz` returns service liveness.
- `/readyz` confirms DB, schema, and SQS readiness.
- `/health` confirms combined readiness.

If `/readyz` returns `503`, inspect `components.schema.groups`. Missing tables
will be listed with a migration hint for the affected capability group.

## 9/10 Release Gate

A release is eligible for production only when all gates below pass in the
target environment or in the deployment candidate environment that mirrors it.

| Gate | Command or evidence | Pass rule |
| --- | --- | --- |
| Migration hygiene | `python scripts/check_migrations.py` and `python scripts/check_distribution_migrations.py` | No naming, replay, duplicate-prefix, or psql artifact failures |
| Migration replay | `python scripts/init_db.py` against a clean candidate DB | Migrations complete without manual edits |
| Backend tests | `pytest` | No failed tests |
| Frontend quality | `cd frontend && npm run check` | Lint baseline, tests, smoke, and production build pass |
| Runtime readiness | `curl -fsS <base-url>/readyz` | Status is `ok`; schema groups are ready |
| Role journey smoke | `python scripts/core_role_journey_smoke.py --base-url <base-url>` | Consumer, producer, distributor, and admin sessions resolve and wrong-scope calls are rejected |
| Target-state smoke | `python scripts/target_state_smoke.py --base-url <base-url>` | Health, OpenAPI, enterprise event, role journey, finance, distribution, audit, and metrics checks pass |
| Data quality | `python -m pytest test/test_data_quality_service.py -q` plus any environment-specific report | No critical data-quality issues for journeys promoted to customer-facing proof |
| Security evidence | Review `docs/SECURITY_AUTH.md` and `docs/RELEASE_SECURITY_CHECKLIST.md` | Auth, tenant scope, secrets, PII, and audit evidence are signed off |
| Onboarding evidence | Review `docs/ONBOARDING_RUNBOOK.md` | Tenant, partner, channel, monitoring, handover, and rollback evidence is complete |

Do not promote a release if any critical gate fails. Warnings are allowed only
when the release owner records the risk, owner, expiry date, and rollback
decision.

Recommended pre-release command pack:

```bash
python scripts/check_migrations.py
python scripts/check_distribution_migrations.py
python scripts/init_db.py
pytest
cd frontend && npm run check
```

Recommended post-deploy command pack:

```bash
python scripts/core_role_journey_smoke.py --base-url <base-url>
python scripts/target_state_smoke.py --base-url <base-url>
curl -fsS <base-url>/readyz
curl -fsS <base-url>/metrics
```

## Rollback Criteria

Rollback or halt rollout immediately when any of these occur:

- `/readyz` is not `ok` for more than one check interval after deployment.
- The target-state smoke or core role journey smoke fails.
- Error rate, request latency, or timeout metrics materially regress from the
  pre-release baseline.
- BFF aggregate metrics show sustained `partial` responses for a core journey.
- Admin audit writes fail or `admin_audit_writes_total{result="failure"}` rises.
- Tenant-scope, role-scope, or PII leakage is suspected.
- Data-quality validation reports a critical issue for a customer-facing proof,
  reward, mission, or leaderboard journey.
- Worker queues stop draining or DLQ volume rises after the release.

Rollback verification:

1. Confirm the previous version is serving traffic.
2. Re-run `/readyz`, `/health`, and the core role journey smoke.
3. Confirm error rate and BFF partial-response metrics return to baseline.
4. Record the failed gate, first bad version, rollback version, and customer
   impact in the release notes.

Confirm OpenAPI exposes the IDS/Hogan endpoints:

- `POST /enterprise/events`
- `GET /admin/enterprise-events/summary`
- `GET /admin/enterprise-events`
- `POST /admin/enterprise-events/{inbox_event_id}/replay`

## IDS/Hogan Smoke Test

Use a non-qualifying event first. This proves ingestion without changing a
referral journey.

```bash
curl -X POST http://localhost:8000/enterprise/events \
  -H "Content-Type: application/json" \
  -H "x-api-key: <partner-or-admin-key>" \
  -d '{
    "source": "HOGAN",
    "sourceEventId": "smoke-ignored-001",
    "eventType": "CUSTOMER_PROFILE_UPDATED",
    "occurredAt": "2026-06-10T13:00:00Z"
  }'
```

Expected response:

```json
{
  "status": "ok",
  "processingStatus": "IGNORED",
  "queued": false
}
```

Then confirm it landed in the inbox:

```sql
SELECT tenant_code, source_system, source_event_id, event_type, processing_status
FROM enterprise_event_inbox
WHERE source_event_id = 'smoke-ignored-001';
```

Use qualifying events only against a known test referral track.

## IDS/Hogan Operations

Summary:

```bash
curl http://localhost:8000/admin/enterprise-events/summary \
  -H "x-api-key: <admin-key>"
```

Recent events:

```bash
curl "http://localhost:8000/admin/enterprise-events?processingStatus=QUEUED&limit=50" \
  -H "x-api-key: <admin-key>"
```

Dashboard view:

```bash
curl "http://localhost:8000/admin/enterprise-events/dashboard?days=7&problemLimit=25" \
  -H "x-api-key: <admin-key>"
```

Dry-run replay:

```bash
curl -X POST "http://localhost:8000/admin/enterprise-events/<inbox-event-id>/replay?dryRun=true" \
  -H "x-api-key: <admin-key>"
```

Queue replay:

```bash
curl -X POST "http://localhost:8000/admin/enterprise-events/<inbox-event-id>/replay?dryRun=false" \
  -H "x-api-key: <admin-key>"
```

Replay only queues the stored `normalized_payload`. Events without a normalized
payload are skipped because there is no platform progress event to process.

## Existing Replay Tools

Referral projection replay:

```bash
curl -X POST "http://localhost:8000/internal/replay/referrals/<referral-track-id>?dry_run=true" \
  -H "x-api-key: <admin-key>"
```

DLQ replay:

```bash
curl -X POST http://localhost:8000/admin/dlq/replay \
  -H "Content-Type: application/json" \
  -H "x-api-key: <admin-key>" \
  -d '<dlq-payload>'
```

Fulfilment replay:

```bash
curl -X POST http://localhost:8000/admin/fulfilment/replay/<audit-id> \
  -H "x-api-key: <admin-key>"
```

## Monitoring

Prometheus endpoint:

```bash
curl http://localhost:8000/metrics
```

Key checks:

- API readiness: `db_ready`, `sqs_ready`, `kafka_ready`
- Request rate and latency: `http_requests_total`,
  `http_request_duration_seconds`
- Rewards: `rewards_applied_total`
- Enterprise events: `enterprise_events_ingested_total`
- Enterprise inbox replay: `enterprise_event_replays_total`
- Enterprise inbox current counts: `enterprise_event_inbox_current`
- Admin audit health: `admin_audit_writes_total`
- BFF aggregate health: `bff_aggregate_requests_total`,
  `bff_aggregate_sections_total`,
  `bff_aggregate_section_latency_seconds`

See:

- `docs/MONITORING.md`
- `docs/ALERTING.md`
- `docs/SECURITY_AUTH.md`

## Incident Checks

### API Is Up But Not Ready

1. Check `/readyz`.
2. Confirm `APP_DB_DSN`.
3. Confirm database network access.
4. Confirm SQS settings if `APP_SQS_QUEUE_URL` is set.

### IDS Events Arrive But Journey Does Not Advance

1. Check `GET /admin/enterprise-events`.
2. Confirm `processingStatus`.
3. If `IGNORED`, check whether the event is non-qualifying or missing
   `tenantCode` / `referralTrackId`.
4. If `QUEUED`, confirm the worker is running.
5. If the event was out of order, the journey will not advance until prior
   milestones exist.
6. After prerequisites exist, use dry-run replay first, then queue replay if
   appropriate.

### Worker Is Not Processing

1. Confirm `WORKER_SECRET` is set for API worker endpoint calls.
2. Confirm `APP_SQS_QUEUE_URL` and `AWS_REGION`.
3. Confirm the worker container is running.
4. Check DLQ and `/admin/dlq/replay`.

### Admin Audit Writes Are Failing

1. Check `/readyz` and confirm the `admin_audit` schema group is ready.
2. Confirm the `admin_audit_log` table exists in the connected database.
3. Check database permissions for inserting into `admin_audit_log`.
4. Review logs for `Admin audit write failed`.
5. Confirm `admin_audit_writes_total{result="failure"}` stops increasing
   after the database or schema issue is resolved.

### Duplicate IDS Events

Duplicates are expected to return `DUPLICATE` and should not queue another
journey event. Dedupe is based on source system plus source event id when
available, otherwise source system plus payload hash.

## Pre-Production Checklist

- Full test suite passes.
- Migrations applied to target DB.
- `/healthz`, `/readyz`, `/health`, and `/metrics` respond.
- API and worker are both running.
- `POST /enterprise/events` accepts a harmless smoke event.
- Admin inbox summary/list endpoints respond.
- Dry-run replay works for a known normalized inbox event.
- Production secrets are configured outside the image.
- Seed scripts are disabled or approved for the environment.
- Alerting and dashboards are connected.
