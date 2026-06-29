# TASK-090 Onboarding Read-Model Wave Checkpoint

Date: 2026-06-29

Status: Accepted for TASK-090.

This checkpoint records the completed onboarding read-model wave from TASK-081 through TASK-089. It is documentation only. It does not add backend routes, frontend code, services, schema, migrations, persistence, tests, secrets, database access, onboarding writes, go-live actions, credential lifecycle, webhook delivery, funding, wallet, fulfilment, settlement, retry, audit mutation, or money movement.

## Purpose

TASK-070 through TASK-080 created a visible frontend onboarding/demo journey. TASK-081 through TASK-089 moved that journey toward safe backend contracts and read-only state without crossing into live onboarding mutation.

The purpose of this checkpoint is to state what is now available, what remains shell-only, which blockers remain, and what the next safe implementation wave should do before any write endpoint or schema work begins.

## Completed Wave Summary

| Task | Outcome | Current posture |
| --- | --- | --- |
| TASK-081 | Consolidated onboarding data contract | Defines canonical onboarding sections, external references, safe statuses, missing evidence, redaction categories, and `tenant_code` internal boundary. |
| TASK-082 | Read-only onboarding state projection helper | Projects safe onboarding state from supplied evidence, marks missing/shell-only evidence, redacts unsafe keys, and performs no mutation. |
| TASK-083 | Onboarding readiness aggregation service | Aggregates projection output into eight readiness categories with blockers, next actions, guardrails, and go-live disabled state. |
| TASK-084 | Read-only admin onboarding state endpoint | Adds authenticated `GET /admin/onboarding/state` for admin/operator read access using external references only. |
| TASK-085 | Operator demo home readiness integration | Hydrates the operator demo home from read-only onboarding readiness while preserving local fallback and disabled live actions. |
| TASK-086 | Safe onboarding draft/save API boundary | Documents future draft/save contract, idempotency, validation, permissions, safe errors, and strict separation from live commands. |
| TASK-087 | Onboarding audit/event capture design | Documents future audit and event evidence requirements for onboarding mutations without implementing persistence or dispatch. |
| TASK-088 | RBAC and permission contract tests | Locks the read route to intended admin/operator access and rejects adjacent roles safely. |
| TASK-089 | Onboarding shell read-only state integration first slice | Connects the readiness checklist and company/organisation shell to read-only onboarding state with fallback and no live actions. |

## Capabilities Now Available

The platform can now demonstrate:

1. A frontend onboarding journey across company, producer/sponsor, distributor, member/role, campaign/opportunity, webhook/API, readiness, operator home, and distributor-safe status.
2. A canonical onboarding data contract that aligns frontend shell fields with backend/read-model terminology.
3. A read-only onboarding state projection helper that exposes missing evidence explicitly.
4. A read-only readiness aggregation service that produces operator-safe readiness categories.
5. An authenticated admin onboarding state endpoint at `GET /admin/onboarding/state`.
6. Operator demo home hydration from read-only readiness state with local fallback.
7. Company/organisation onboarding and onboarding readiness checklist hydration from read-only state with local fallback.
8. Permission regression coverage for unauthenticated, unauthorized, adjacent-role, and authorized admin/operator access.
9. A future draft/save boundary and audit/event evidence design ready for later implementation planning.

## Current Demo Flow

The current safe demo path is:

1. Open the operator demo home.
2. Show read-only onboarding readiness hydration when the endpoint is available.
3. Walk through company/organisation onboarding, including external reference display and read-only company readiness.
4. Continue through producer/sponsor, distributor, member/role, campaign/opportunity, and webhook/API shells using local demo state.
5. Review the onboarding readiness checklist, including endpoint-backed categories where available.
6. Move into monitoring and diagnostics surfaces.
7. Show distributor-safe status without internal/provider/settlement leakage.

This demo is still read-only and review-only. It is suitable for product walkthroughs and internal readiness discussions, not live onboarding or release certification.

## Remaining Shell-Only Or Local-Only Areas

These areas are not yet hydrated from backend/read-only onboarding state:

- producer/sponsor onboarding page;
- distributor onboarding page;
- member/role onboarding page;
- campaign/opportunity setup page;
- webhook/API setup page.

These areas remain local-only or shell-only:

- onboarding draft/save persistence;
- external reference resolver persistence;
- onboarding draft versioning;
- draft validation endpoint;
- submit-for-review workflow;
- operator review workflow;
- live activation or go-live controls;
- frontend form-to-backend mapping beyond the first read-only shell slice.

## Explicitly Not Live

The completed wave does not implement:

- real tenant, company, account, or organisation creation;
- producer, sponsor, distributor, partner, member, user, seat, role, or identity-provider creation;
- invite delivery;
- campaign or opportunity publication;
- link/code generation or route activation from onboarding;
- API key, credential, token, certificate, signing material, or secret generation;
- webhook subscription activation, signing, queueing, retry, replay, or delivery;
- go-live activation;
- funding account creation, wallet creation, budget reservation, invoice generation, sponsor billing mutation, fulfilment, settlement, payout, reversal, retry, repair, reconciliation, or money movement;
- live DB verification or production smoke testing.

## Validation Baseline

Recorded validation across the wave:

- TASK-082: `python -m pytest test/test_onboarding_state_projection_service.py` passed with 5 tests; Black check passed.
- TASK-083: `python -m pytest test/test_onboarding_readiness_aggregation_service.py test/test_onboarding_state_projection_service.py` passed with 12 tests; Black and Ruff checks passed for changed service/test files with only the existing Ruff settings deprecation warning.
- TASK-084: `python -m pytest test/api/test_admin_onboarding_api.py test/test_onboarding_state_projection_service.py test/test_onboarding_readiness_aggregation_service.py` passed with 21 tests; Black check passed; Ruff passed for new files, while `apps/api/main.py` retained its pre-existing import-layout baseline.
- TASK-085: targeted operator demo home and onboarding smoke tests passed; full frontend `npm.cmd test` passed with 73 tests; build passed; lint passed with the existing warning baseline.
- TASK-088: targeted onboarding API permission tests passed with 15 tests; combined onboarding API/projection/aggregation tests passed with 27 tests; Ruff check passed for the changed test file; local Black invocation timed out before returning.
- TASK-089: changed-page tests passed with 12 tests; related onboarding/demo tests passed with 45 tests; full frontend tests passed with 78 tests; frontend build passed; frontend lint passed with the existing warning baseline.

TASK-090 validation is documentation/readback only.

## Permission And Safety Posture

The current read model preserves these safety boundaries:

- `GET /admin/onboarding/state` requires authenticated admin/operator-style access.
- Finance admin, partner, producer, distributor, consumer, and unauthenticated access are rejected according to current tests.
- The read route accepts external onboarding references and ignores user-supplied `tenant_code` as scope.
- `tenant_code` remains internal and is not used as a user-facing onboarding identifier.
- Missing, shell-only, unresolved, and blocked evidence are surfaced explicitly.
- Secrets, credentials, private identifiers, provider internals, raw audit details, funding/wallet/settlement/fulfilment/retry internals, and money movement details are outside the read-model response contract.
- Frontend pages preserve local fallback and disabled live-action guardrails.

## Remaining Blockers

TASK-027 remains blocked because approved safe read-only runtime database access is not available. It still requires environment name, read-only credentials, write-protection confirmation, and approval for runtime/API smoke checks before any DB connection is attempted.

TASK-028 remains blocked because TASK-027 has not produced verified live/schema drift evidence. TASK-028 should only resolve confirmed mismatches or explicitly deferred unknowns.

These blockers do not prevent local demos or read-only contract development. They do prevent claims of live-state readiness or release confidence.

## Recommended TASK-091 Onward Wave

The next wave should finish read-only/frontend contract alignment before any write implementation. It should not jump directly into onboarding mutation, schema, credential lifecycle, go-live, webhook delivery, funding, fulfilment, settlement, retry, audit mutation, or money movement.

Recommended order:

1. Connect producer/sponsor onboarding shell to read-only onboarding state.
2. Connect distributor onboarding shell to read-only onboarding state.
3. Connect member/role onboarding shell to read-only onboarding state.
4. Connect campaign/opportunity setup shell to read-only onboarding state.
5. Connect webhook/API setup shell to read-only onboarding state.
6. Add frontend API helper contract tests for onboarding state response mapping and safe redaction.
7. Add response schema/type alignment checks for the admin onboarding endpoint and frontend helper.
8. Design onboarding draft persistence schema and rollback plan only; do not add migrations yet.
9. Design a no-op/dry-run validation endpoint contract only; do not implement writes yet.
10. Add a checkpoint before any onboarding write endpoint implementation.

## Guardrails For The Next Wave

- Prefer read-only integration and tests before mutation.
- Keep `tenant_code` internal.
- Use external references for visible onboarding scope.
- Preserve local fallback while backend sources remain incomplete.
- Do not create accounts, distributors, members, campaigns, credentials, webhooks, funding, wallet, fulfilment, settlement, retry, audit, or money records.
- Do not inspect secrets or access live DB.
- Do not add schema or migrations until a dedicated design and rollback task is complete.
- Preserve TASK-027 and TASK-028 as blocked until approved live verification access exists.
