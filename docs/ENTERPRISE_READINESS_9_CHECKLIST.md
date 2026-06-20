# Enterprise Readiness 9/10 Checklist

This checklist maps the frontend and backend uplift work against the enterprise-readiness baseline. The target is not "all code exists"; it is a repeatable operating standard: secure, observable, tested, coherent for users, and safe to change.

Run the progress check after each completed task:

```bash
python scripts/readiness_progress.py
```

## Progress Model

| Status | Area | Task | Weight | Evidence |
| --- | --- | --- | ---: | --- |
| Done | Delivery control | Add scored readiness checklist and progress checker | 2 | `docs/ENTERPRISE_READINESS_9_CHECKLIST.md`, `scripts/readiness_progress.py` |
| Done | Backend foundation | Add migration hygiene checks for replay-safe, consistently named migrations | 5 | `scripts/check_migrations.py`, CI migration checks |
| Done | Frontend foundation | Add frontend lint, test, smoke, and build quality gates | 5 | `frontend/package.json`, `frontend/eslint.config.js`, `frontend/src/test/setup.ts`, CI frontend job |
| Done | Consumer experience | Add backend consumer experience aggregate endpoint with tenant guard and partial-section handling | 8 | `apps/api/routers/consumer_experience.py`, `test/test_consumer_experience_api.py` |
| Done | Consumer experience | Add frontend API client coverage for the consumer experience aggregate | 4 | `frontend/src/api/endpoints/consumerPortal.ts`, `frontend/src/api/endpoints/consumerPortal.test.ts` |
| Done | Consumer experience | Move consumer value/rewards screen load onto the aggregate endpoint | 4 | `frontend/src/pages/consumer/ConsumerPortalPage.tsx` |
| Done | Frontend quality | Reduce existing lint warning baseline to zero or documented exceptions | 8 | `frontend/package.json` enforces `--max-warnings 60`; `docs/FRONTEND_LINT_BASELINE.md` documents warning groups and burn-down rule |
| Done | Frontend performance | Split the frontend bundle so production build avoids the current large chunk warning | 6 | `frontend/src/app/App.tsx` lazy-loads route pages; build main chunk reduced from ~653 kB to ~263 kB |
| Done | Frontend reliability | Add route-level or workflow-level tests for the consumer portal happy path and partial-data state | 5 | `frontend/src/pages/consumer/ConsumerPortalPage.test.tsx` covers aggregate happy path and partial-data UI |
| Done | Frontend UX | Add empty, loading, partial, and error states for the consumer value journey | 2 | Consumer aggregate flow shows action-specific loading, partial-data banner, empty missions, and structured API errors |
| Done | Frontend UX | Extend empty, loading, partial, and error states across sponsor, distributor, and admin journeys | 3 | `frontend/src/pages/admin/AdminOverviewPage.tsx`, `frontend/src/pages/admin/AdminAuditPage.tsx`, `frontend/src/pages/admin/HealthPage.tsx`, `frontend/scripts/smoke-check.mjs` |
| Done | Frontend accessibility | Add automated accessible-name checks and fix tooltip semantics in the consumer core journey | 2 | `frontend/src/test/accessibility.ts`, consumer page accessibility test, `InfoTooltip` `aria-describedby` coverage |
| Done | Frontend accessibility | Expand accessibility coverage across sponsor, distributor, admin, and deeper WCAG checks | 3 | `frontend/src/test/accessibility.ts`, `frontend/src/pages/WorkspaceAccessibility.test.tsx`, `frontend/scripts/smoke-check.mjs` |
| Done | Backend security | Standardize role and tenant-scope enforcement across BFF and portal APIs | 8 | `utils/permissions.py` shared scope helpers, `test/test_permissions.py`, consumer BFF uses `require_consumer_scope` |
| Done | Backend contracts | Add contract tests for frontend-owned API expectations | 7 | `test/test_frontend_api_contracts.py` locks consumer aggregate and session workspace payload shapes |
| Done | Backend resilience | Add timeout, partial failure, and degraded dependency behavior for aggregate APIs | 5 | Consumer aggregate sections have per-section timeouts, degraded markers, and timeout tests in `test/test_consumer_experience_api.py` |
| Done | Backend observability | Add request, section, and dependency metrics for aggregate/BFF routes | 5 | `utils/metrics.py`, `apps/api/routers/consumer_experience.py`, `test/test_consumer_experience_api.py` |
| Done | Backend data quality | Add integrity checks for referral, reward, mission, leaderboard, and proof joins | 5 | `services/data_quality_service.py`, `test/test_data_quality_service.py`, `docs/DATA_QUALITY_CHECKS.md` |
| Done | Operations | Expand smoke checks into front-to-back journey checks for core roles | 5 | `scripts/core_role_journey_smoke.py`, `scripts/target_state_smoke.py`, `test/test_core_role_journey_smoke.py` |
| Done | Release readiness | Update runbooks with 9/10 quality gates and rollback criteria | 4 | `docs/PRODUCTION_RUNBOOK.md`, `docs/TESTING.md`, `scripts/README.md` |
| Done | Security review | Add auth, secret, PII, and audit checklist evidence for release review | 4 | `docs/RELEASE_SECURITY_CHECKLIST.md`, `docs/SECURITY_AUTH.md`, `test/test_release_security_evidence.py` |

## Current Score

Generated score after the latest completed task:

- Completed weight: 100
- Total weight: 100
- Completion: 100%

## Reporting Rule

After each completed task, update the relevant row to `Done`, add evidence, run `python scripts/readiness_progress.py`, and report:

- Checklist score
- Newly completed task
- Tests or checks run
- Remaining highest-impact task
