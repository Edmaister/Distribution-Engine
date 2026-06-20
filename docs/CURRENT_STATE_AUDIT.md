# Current-State Audit

Date: 2026-06-09

## Executive Read

This repository is a broad backend platform for a white-label Distribution Layer / Referral Engine. The codebase has real enterprise-oriented building blocks: FastAPI routers, async PostgreSQL services, referral and campaign flows, rewards, missions, badges, leaderboards, privacy, fulfilment, funding, settlement, reconciliation, provider SLA, Helm/Kubernetes artifacts, monitoring, and tests.

The project is not yet production-ready. The main blockers are contract drift between API/worker layers and services, inconsistent admin security, broken local test runtime, migration/script drift, and deployment/config mismatches. The platform direction is strong, but the current implementation needs a stabilization sprint before it can safely support a commercial pilot.

## Observed Inventory

- Python files: 331
- Test files under `test/`: 128
- Static API routes in `apps/api/routers`: 136
- Static admin routes: 103
- Migration-folder items under `dp/migrations`: 71
- Git status: no `.git` repository at workspace root

## What Is Strong

- The architecture is modular enough to support the Distribution Layer vision.
- The main API has health, readiness, metrics, correlation IDs, and a global exception handler.
- The domain has expanded beyond referrals into mission orchestration, reward fulfilment, funding, settlement, reconciliation, privacy, provider SLA, and marketplace funding.
- Most service code has moved to async PostgreSQL patterns using `asyncpg`.
- Worker auth is fail-closed when `WORKER_SECRET` is missing.
- There is meaningful test intent across services, routers, workers, funding, fulfilment, settlement, privacy, and recommendations.

## Critical Findings

### 1. Test suite cannot currently be executed from this workspace

The local virtual environment points to a missing/inaccessible interpreter:

`C:\Users\Carla\AppData\Local\Programs\Python\Python311\python.exe`

The bundled Python available to Codex does not include `pytest`. Therefore the current audit could not validate pass/fail counts.

Additional test readiness issue: `requirements.txt` includes `pytest` and `pytest-cov`, but not `pytest-asyncio`, while the suite contains many `pytest.mark.asyncio` tests.

### 2. Reward API and worker use an old reward-service contract

`services.reward_service.apply_reward` currently expects a `RewardInstruction` object and is async.

But:

- `apps/api/routers/rewards.py` calls `apply_reward(...)` synchronously with keyword arguments.
- `apps/Workers/ids_consumer.py` awaits `apply_reward(...)` but passes the old keyword-argument shape.
- `test/test_rewards_router.py` still validates the old keyword-argument shape.

This is a runtime blocker for reward application paths.

### 3. Many admin routes are not protected consistently

Several admin routers have no router-level security dependency, including finance, fulfilment, funding, funding rules, funding alerts, funding reconciliation, settlement, settlement approvals, settlement batches, reconciliation, funding contracts, and sponsor wallets.

Some admin routers are protected, so the issue is inconsistency rather than total absence of auth.

### 4. Built-in test API keys are accepted by normal security helpers

`utils/security.py` includes hardcoded `test-admin-key`, `test-partner-key`, `test-fnb-key`, and `test-pnp-key` in key resolution. This is useful for tests but unsafe unless gated to `APP_ENV=test` or similar.

### 5. Redis configuration is not wired into the settings model

`apps/api/settings.py` defines `redis_url` outside the `Settings` class. `apps/core/cache.py` reads `getattr(settings, "redis_url", None)`, which means Redis may never be discovered. As a result, Redis-backed cache and rate limiting can silently stay disabled.

### 6. Provider SLA router has duplicate route/function definitions

`apps/api/routers/provider_sla.py` defines `GET /admin/providers/rankings` twice and imports `rank_providers` twice.

### 7. Database migration story is inconsistent

The actual migration folder is `dp/migrations`, but some older docs and config examples still point to `db/migrations`.

Scripts import `utils.db.get_connection`, but `utils/db.py` only exposes async helpers and no `get_connection`.

Duplicate migration prefixes and the malformed settlement certification migration have been addressed in the target-state hardening work. Keep `scripts/check_distribution_migrations.py` in CI so these do not regress.

Several migration files have no `.sql` extension, so naive migration runners will skip them.

### 8. Worker Dockerfile has a Linux case-sensitivity bug

`Dockerfile.worker` runs:

`python -m apps.workers.sqs_referral_worker`

The actual folder is `apps/Workers`. This may work on case-insensitive Windows but will fail in Linux containers.

### 9. CI workflow is not active and has weak gates

The workflow is under `github/workflows/ci.yml`, not `.github/workflows/ci.yml`, so GitHub Actions will not pick it up as-is.

It also contains:

- `pip install -r requirements.txt || true`
- `coverage xml || true`

Those allow important failures to pass.

### 10. Test configuration is split

`pytest.ini` uses `testpaths = test`, while `pyproject.toml` uses `testpaths = ["tests"]`. The actual test folder is `test`.

## Recommended Stabilization Order

### Week 1: Make the baseline executable

1. Rebuild the local virtual environment.
2. Add `pytest-asyncio` or convert async tests to AnyIO.
3. Move CI to `.github/workflows/ci.yml`.
4. Remove `|| true` from dependency install and coverage commands.
5. Add lint/test/security gates.

### Week 2: Fix runtime blockers

1. Update `apps/api/routers/rewards.py` to construct `RewardInstruction` and await `apply_reward`.
2. Update `apps/Workers/ids_consumer.py` to either construct `RewardInstruction` or route through the journey/reward-policy layer.
3. Update tests to validate the new reward contract.
4. Remove duplicate provider rankings route.
5. Fix `Dockerfile.worker` module path.

### Week 3: Secure and configure the admin surface

1. Add consistent admin dependencies to every `/admin/...` router.
2. Gate hardcoded test keys to test/local only.
3. Move tenant/key logic toward a tenant registry or database-backed auth model.
4. Add `redis_url` to the `Settings` model and validate rate limiting under Redis.
5. Ensure Helm values include required runtime secrets: admin keys, worker secret, Redis URL, referral secret, and any SQS/Kafka settings.

### Week 4: Consolidate database and deployment

1. Decide on `dp/` vs `db/`; standardize all scripts/docs.
2. Replace or rewrite sync migration scripts around asyncpg or psql.
3. Rename extensionless migrations or introduce a proper migration manifest.
4. Remove psql meta-commands from SQL migrations.
5. Smoke-test Docker API and worker images.
6. Produce a clean current architecture map and API catalogue.

## MVP Recommendation

Do not try to productize the full Distribution Layer immediately. The right first commercial MVP is:

- One tenant
- One vertical
- One referral/campaign journey
- One reward type
- One fulfilment path
- Admin dashboard for campaign, reward, funding, settlement, privacy, and audit
- Clear metrics: conversions, activations, reward liability, fulfilment success, and campaign ROI

Once that is stable, generalize into mission templates, distributor profiles, sponsor funding, marketplace offers, and intelligence-driven distribution.
