# TASK-100 Onboarding Pre-Write Readiness Checkpoint

Date: 2026-06-30

Status: Accepted for TASK-100.

This checkpoint records the completed onboarding read-only integration and contract-hardening wave from TASK-091 through TASK-099. It is documentation only. It does not add backend routes, frontend code, services, tests, schema, migrations, persistence, live DB access, secrets, onboarding writes, audit writes, event persistence, credential lifecycle, webhook delivery, go-live activation, funding, wallet, fulfilment, settlement, retry, or money movement.

## Purpose

TASK-091 through TASK-099 completed the second onboarding readiness wave after the TASK-090 read-model checkpoint. The purpose of TASK-100 is to confirm what is now ready, what remains explicitly not live, and whether the platform can safely consider a narrow draft-persistence foundation wave.

The key decision is not to start full onboarding writes. The key decision is whether the project is ready to consider draft persistence foundations under strict guardrails.

## Completed Wave Summary

| Task | Outcome | Current posture |
| --- | --- | --- |
| TASK-091 | Connected producer/sponsor onboarding to read-only state. | Frontend shell hydrates safe evidence from the admin onboarding state endpoint with fallback and disabled money/credential actions. |
| TASK-092 | Connected distributor onboarding to read-only state. | Frontend shell hydrates safe distributor evidence with fallback and disabled lifecycle, route, wallet, and money actions. |
| TASK-093 | Connected member/role onboarding to read-only state. | Frontend shell hydrates permission/missing-evidence state with disabled invite, user, membership, role, identity-provider, and audit actions. |
| TASK-094 | Connected campaign/opportunity setup to read-only state. | Frontend shell hydrates campaign/opportunity readiness blockers with disabled create, publish, link/code, route, reward, funding, go-live, and money actions. |
| TASK-095 | Connected webhook/API setup to read-only state. | Frontend shell hydrates integration evidence with disabled credential, subscription, signing, delivery, retry, and go-live actions. |
| TASK-096 | Added frontend onboarding API helper contract tests. | The helper now has regression coverage for external-reference queries, response handling, fallback, and no sensitive leakage. |
| TASK-097 | Aligned backend/frontend onboarding response envelope. | Frontend types and tests now require the backend envelope: `status`, `onboarding_state`, `readiness`, and `guardrail`. |
| TASK-098 | Designed draft persistence schema and rollback plan. | Future schema intent, tables, idempotency, retention, rollback, and migration safety are documented only. |
| TASK-099 | Designed dry-run validation endpoint contract. | Future no-op validation route semantics, safe errors, permissions, idempotency, and no-persistence guarantees are documented only. |

## Completed Read-Only Frontend Integrations

The following onboarding shells now consume the read-only onboarding state endpoint where available while preserving local fallback:

- producer/sponsor onboarding;
- distributor onboarding;
- member/role onboarding;
- campaign/opportunity setup;
- webhook/API setup.

Together with earlier work, the operator demo home, company/organisation onboarding shell, and onboarding readiness checklist also consume read-only onboarding state. The frontend journey can now demonstrate a coherent onboarding path without creating or updating live platform records.

## Completed Contract And Test Hardening

The wave hardened the onboarding read contract through:

- focused frontend API helper contract tests for `getAdminOnboardingState`;
- backend/frontend response schema alignment;
- shared frontend response fixture for the full admin onboarding envelope;
- required `onboarding_state` envelope alignment with the backend route;
- backend API assertions for the stable read-only envelope;
- permission tests from TASK-088 proving unauthorized and adjacent-role access is rejected.

The current read-only admin route remains `GET /admin/onboarding/state`.

## Completed Future-Write Design Work

Future-write design is now documented but not implemented:

- `docs/sa/ONBOARDING_DRAFT_SAVE_API_BOUNDARY.md`
- `docs/sa/ONBOARDING_AUDIT_EVENT_CAPTURE_DESIGN.md`
- `docs/sa/ONBOARDING_DRAFT_PERSISTENCE_SCHEMA_DESIGN.md`
- `docs/sa/ONBOARDING_DRY_RUN_VALIDATION_ENDPOINT_CONTRACT.md`

These documents define the boundaries for future draft persistence, idempotency, audit/event evidence, rollback, dry-run validation, no-persistence guarantees, and no-live-action semantics.

## What The Platform Can Demonstrate Now

The platform can now demonstrate:

1. Full frontend onboarding journey across company, producer/sponsor, distributor, member/role, campaign/opportunity, webhook/API, readiness, and operator demo surfaces.
2. Read-only backend onboarding state endpoint.
3. Read-only integration across operator demo home and onboarding shells.
4. Safe missing-evidence and fallback states.
5. External-reference-based user-facing identifiers.
6. No `tenant_code` user-facing dependency.
7. Disabled live/go-live/credential/webhook/funding/money actions.
8. Permission rejection for unauthenticated and adjacent-role access to onboarding read state.
9. Contract-level designs for draft persistence and dry-run validation.

This is suitable for internal demo and planning conversations. It is not live onboarding.

## Explicitly Not Live

The platform still does not implement:

- draft persistence;
- onboarding save or update;
- tenant, company, account, or organisation creation;
- producer, sponsor, distributor, partner, member, user, seat, role, or identity-provider creation;
- invite delivery;
- campaign or opportunity publication;
- link/code generation;
- credential generation, rotation, reveal, storage, or lifecycle;
- webhook subscription, signing, queueing, retry, replay, or delivery;
- go-live activation;
- funding records, wallets, reservations, invoices, fulfilment, settlement, payout, reversal, repair, retry, reconciliation, or money movement;
- live DB verification or production smoke testing.

## Validation Baseline

Recorded validation from TASK-091 through TASK-099:

| Task | Validation recorded |
| --- | --- |
| TASK-091 | `npm.cmd test -- ProducerSponsorOnboardingPage.test.tsx` passed with 7 tests. |
| TASK-092 | `npm.cmd test -- DistributorOnboardingPage.test.tsx` passed with 7 tests. |
| TASK-093 | `npm.cmd test -- MemberRoleOnboardingPage.test.tsx` passed with 7 tests; related onboarding/demo smoke tests passed with 38 tests; full frontend tests passed with 90 tests; build and lint passed with existing warning baseline. |
| TASK-094 | `npm.cmd test -- CampaignOpportunitySetupPage.test.tsx` passed with 7 tests; Distribution Command Centre targeted test passed after test-isolation hardening; onboarding smoke test passed; full frontend tests passed with 94 tests; build and lint passed with existing warning baseline. |
| TASK-095 | `npm.cmd test -- WebhookApiSetupPage.test.tsx` passed with 8 tests; related onboarding tests passed with 48 tests; onboarding smoke test passed; full frontend tests passed with 98 tests; build and lint passed with existing warning baseline. |
| TASK-096 | `npm.cmd test -- adminOnboarding.test.ts` passed with 5 tests; related onboarding/demo tests passed with 70 tests; full frontend tests passed with 103 tests; build and lint passed with existing warning baseline of 42 warnings, 0 errors. |
| TASK-097 | Targeted frontend onboarding API/page tests passed with 70 tests; full frontend tests passed with 103 tests; build and lint passed with existing warning baseline; backend targeted onboarding API/projection/readiness tests passed with 27 tests; Ruff checks passed. |
| TASK-098 | Documentation/readback only. Draft persistence schema intent, additive migration strategy, rollback, idempotency, audit linkage, retention, redaction, and no-live-action semantics were confirmed. |
| TASK-099 | Documentation/readback only. Dry-run semantics, safe errors, no-persistence guarantee, external-reference scope, redaction, permissions, idempotency, and no-live-action semantics were confirmed. |

Known warning baseline: frontend lint currently passes with the existing project warning baseline, recorded as 42 warnings and 0 errors in the latest relevant tasks.

## Permission And Safety Posture

Current permission and safety posture:

- `GET /admin/onboarding/state` is authenticated and admin/operator scoped.
- Admin, distribution admin, and system admin access are allowed by current tests.
- Finance admin, partner, producer, distributor, consumer, and unauthenticated access are rejected by current tests.
- Adjacent-role rejection happens before read-only projection helpers run.
- The route accepts external onboarding references only.
- User-supplied `tenant_code` is ignored or excluded from frontend query construction and backend scope handling.
- Responses avoid user-facing `tenant_code`.
- Secrets, credentials, provider internals, audit internals, private identifiers, funding/wallet/settlement/fulfilment/retry internals, and money movement details remain outside the read-model response contract.
- Live command buttons and workflows remain disabled in frontend onboarding shells.

## Remaining Blockers

TASK-027 remains blocked because approved safe read-only runtime database access is unavailable. It still requires environment name, read-only credentials, write-protection confirmation, and approval for runtime/API smoke checks before any database connection is attempted.

TASK-028 remains blocked because TASK-027 has not produced verified live/schema drift evidence. TASK-028 should only resolve confirmed mismatches or explicitly deferred unknowns.

These blockers do not prevent local read-only contract development or a carefully staged draft-persistence foundation. They do prevent claims of live-state readiness, release confidence, or production onboarding readiness.

## Pre-Write Readiness Decision

Decision: the platform is ready to consider a tightly scoped draft-persistence foundation wave, but it is not ready for live onboarding writes.

Allowed direction:

- final review before migration;
- additive draft table migration only;
- clean DB replay tests;
- repository/service foundations without route wiring;
- idempotency helper tests;
- validation service tests;
- eventual draft-save endpoint only after prior foundations pass and only for saving draft intent.

Not allowed:

- full onboarding writes;
- live tenant/account/company creation;
- member/user/invite/role mutation;
- campaign publication;
- credential lifecycle;
- webhook delivery;
- go-live activation;
- funding, wallet, fulfilment, settlement, retry, audit mutation beyond explicitly scoped draft-save evidence, or money movement.

## Recommended Next Wave

The next wave should be cautious and draft-persistence-only. It should not jump to live onboarding.

### TASK-101: Draft Persistence Migration Design Final Review

Type: Docs/checkpoint.
Goal: Final review before any migration.
Dependencies: TASK-098; TASK-099; TASK-100.
Stop conditions: Stop if review requires adding migrations, writing code, accessing live DB, inspecting secrets, or enabling writes.
Validation expectation: Documentation/readback confirms schema design, rollback, clean DB replay plan, TASK-027/TASK-028 posture, and no-live-action guardrails.
Explicit non-goals: Do not add migrations, services, routes, frontend code, draft writes, audit writes, credential lifecycle, webhook delivery, go-live, funding, fulfilment, settlement, retry, wallet, or money movement.

### TASK-102: Add Onboarding Draft Persistence Migration

Type: DB migration.
Goal: Add draft tables only, no write route and no production writes.
Dependencies: TASK-101.
Stop conditions: Stop if migration needs live DB access, production data, secrets, route implementation, services, frontend code, or live action semantics.
Validation expectation: Migration check and clean DB replay pass; schema matches TASK-098; no route or write path exists.
Explicit non-goals: Do not add draft-save routes, account creation, invite delivery, campaign publication, credential lifecycle, webhook delivery, audit writes, funding, fulfilment, settlement, retry, wallet, go-live, or money movement.

### TASK-103: Add Clean DB Migration Replay Tests For Onboarding Draft Tables

Type: Tests.
Goal: Prove clean DB readiness for onboarding draft tables.
Dependencies: TASK-102.
Stop conditions: Stop if tests require live DB access, production data, secrets, or write APIs.
Validation expectation: Migration hygiene and clean DB replay tests pass; draft tables, indexes, and constraints are verified locally/CI only.
Explicit non-goals: Do not add services, routes, frontend code, draft writes, audit writes, credential lifecycle, webhook delivery, go-live, funding, fulfilment, settlement, retry, wallet, or money movement.

### TASK-104: Add Onboarding Draft Repository With No Route Wiring

Type: Service/repository.
Goal: Add repository primitives and repository tests only, with no API exposure.
Dependencies: TASK-102; TASK-103.
Stop conditions: Stop if repository work requires route wiring, frontend changes, live DB access, secrets, or live action semantics.
Validation expectation: Repository tests cover create/read/update draft-intent primitives, stale version behavior, redaction boundaries, and no-live-action fields.
Explicit non-goals: Do not add API routes, frontend integration, account creation, invite delivery, campaign publication, credential lifecycle, webhook delivery, audit writes, funding, fulfilment, settlement, retry, wallet, go-live, or money movement.

### TASK-105: Add Draft Idempotency Helper

Type: Service/tests.
Goal: Implement idempotency key hashing, scoping, payload hash comparison, replay, and conflict logic only.
Dependencies: TASK-104.
Stop conditions: Stop if helper requires route wiring, live DB access, secrets, or non-draft side effects.
Validation expectation: Tests cover same-key/same-payload replay, same-key/different-payload conflict, scoped keys, hash-only storage, and no sensitive leakage.
Explicit non-goals: Do not make live commands idempotent, add routes, write audit rows, dispatch events, generate credentials, deliver webhooks, fund, fulfil, settle, retry, activate go-live, or move money.

### TASK-106: Add Draft Validation Service Using Read-Only Readiness Aggregation

Type: Service/tests.
Goal: Validate draft payloads and produce readiness preview without persistence side effects.
Dependencies: TASK-104; TASK-105; TASK-099.
Stop conditions: Stop if validation needs live DB access, secrets, route implementation, persistence beyond explicitly scoped draft reads, or live action semantics.
Validation expectation: Tests cover field validation, cross-section validation, permission-shaped inputs, missing evidence, safe errors, redaction, and go-live disabled state.
Explicit non-goals: Do not add API routes, create accounts, send invites, publish campaigns, generate credentials, deliver webhooks, write audit rows, fund, fulfil, settle, retry, activate go-live, or move money.

### TASK-107: Add Admin Draft Save Endpoint Behind Strict Guardrails

Type: API.
Goal: Save draft intent only; no activation, invites, credentials, webhook delivery, or money movement.
Dependencies: TASK-104; TASK-105; TASK-106.
Stop conditions: Stop if endpoint requires live DB access, production data, secrets, auth weakening, broad permission refactors, live entity creation, or money actions.
Validation expectation: API tests cover auth, adjacent-role rejection, external-reference scope, idempotency, stale update, duplicate draft, safe errors, redaction, no audit/event unless explicitly scoped, and no-live-action behavior.
Explicit non-goals: Do not create tenants, users, invites, campaigns, credentials, webhooks, funding, wallets, fulfilments, settlements, retries, go-live activation, or money movement.

### TASK-108: Frontend Draft-Save Integration Behind Disabled/Live-Safe Controls

Type: Frontend/API integration.
Goal: Save draft only if prior tasks pass; no submit/go-live.
Dependencies: TASK-107.
Stop conditions: Stop if frontend work enables live actions, credential lifecycle, webhook delivery, invite delivery, campaign publication, funding, fulfilment, settlement, retry, wallet, go-live, or money movement.
Validation expectation: Frontend tests cover save draft, safe errors, fallback, disabled live actions, no secret display, external references, and no `tenant_code` user-facing dependency.
Explicit non-goals: Do not implement submit-for-review, go-live, account creation, invite delivery, credential generation, webhook delivery, funding, fulfilment, settlement, retry, wallet, or money movement.

### TASK-109: Audit/Event Evidence Implementation For Draft Save Only

Type: Service/tests.
Goal: Add audit evidence only for draft save, with no webhook dispatch.
Dependencies: TASK-107.
Stop conditions: Stop if implementation dispatches events/webhooks, stores raw sensitive payloads, touches money domains, or enables live onboarding.
Validation expectation: Tests cover actor, role, external references, correlation ID, idempotency reference, before/after hash, changed sections, redaction, and no webhook/event dispatch unless explicitly scoped as internal evidence.
Explicit non-goals: Do not add webhook delivery, event replay, repair, credential lifecycle, invite delivery, campaign publication, funding, fulfilment, settlement, retry, wallet, go-live, or money movement.

### TASK-110: Checkpoint Draft-Save Implementation Readiness

Type: Docs.
Goal: Decide whether submit-for-review or dry-run validation can be implemented next.
Dependencies: TASK-102; TASK-103; TASK-104; TASK-105; TASK-106; TASK-107; TASK-108; TASK-109.
Stop conditions: Stop if checkpoint requires implementation work, live DB access, secrets, schema changes, migrations, writes, go-live, credential lifecycle, webhook delivery, funding, fulfilment, settlement, retry, audit mutation beyond completed draft-save evidence, or money movement.
Validation expectation: Documentation/readback confirms draft-save readiness, remaining blockers, validation baseline, and safe next priorities.
Explicit non-goals: Do not implement submit-for-review, dry-run route, live onboarding, credential lifecycle, webhook delivery, funding, fulfilment, settlement, retry, wallet, go-live, or money movement.

## Guardrails For TASK-101 Onward

The next wave must preserve:

- no live onboarding;
- no tenant/account/company creation;
- no producer/sponsor/distributor creation;
- no user/member/role creation;
- no invite delivery;
- no campaign/opportunity publication;
- no credential lifecycle;
- no webhook delivery;
- no go-live activation;
- no funding, wallet, fulfilment, settlement, retry, or money movement;
- no secrets or production data;
- no live DB access unless a task explicitly requests approved safe read-only verification;
- TASK-027/TASK-028 remain blocked unless separately resolved.

## Readback Checklist

Before starting TASK-101 or any downstream write-adjacent task, confirm:

- TASK-091 through TASK-099 outcomes are represented accurately;
- read-only integrations remain read-only;
- response schema remains aligned;
- `onboarding_state` remains required in the frontend response type;
- `tenant_code` remains internal;
- external references remain user-facing;
- draft persistence is not yet implemented;
- dry-run validation is not yet implemented;
- no live action is enabled;
- TASK-027 and TASK-028 remain blocked;
- the next task is the smallest safe step and does not jump to live onboarding.
