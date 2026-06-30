# TASK-110 Onboarding Draft-Save Readiness Checkpoint

Date: 2026-06-30

Status: Accepted for TASK-110.

This checkpoint records the draft-save implementation wave from TASK-102 through TASK-109 and decides the safest next step. It is documentation only. It does not add backend routes, frontend code, services, tests, schema, migrations, database access, secrets, onboarding writes beyond the completed draft-save path, go-live actions, credential lifecycle, webhook delivery, funding, wallet, fulfilment, settlement, retry, audit mutation beyond TASK-109 evidence references, or money movement.

## Purpose

TASK-110 is the decision point after draft persistence, guarded draft-save, frontend company draft-save, and draft-save audit evidence. The checkpoint answers whether the platform should implement submit-for-review next, implement dry-run validation next, or stop for more hardening.

## Source Review

This checkpoint is based on:

- `docs/roadmap/ORDERED_TASK_LIST.md`
- `docs/roadmap/ONBOARDING_PRE_WRITE_READINESS_CHECKPOINT_TASK_100.md`
- `docs/roadmap/ONBOARDING_DRAFT_MIGRATION_FINAL_REVIEW_TASK_101.md`
- `docs/sa/ONBOARDING_DRAFT_PERSISTENCE_SCHEMA_DESIGN.md`
- `docs/sa/ONBOARDING_DRAFT_SAVE_API_BOUNDARY.md`
- `docs/sa/ONBOARDING_AUDIT_EVENT_CAPTURE_DESIGN.md`
- `docs/sa/ONBOARDING_DRY_RUN_VALIDATION_ENDPOINT_CONTRACT.md`
- `dp/migrations/080_onboarding_draft_persistence.sql`
- `services/onboarding/onboarding_draft_repository.py`
- `services/onboarding/onboarding_draft_idempotency_service.py`
- `services/onboarding/onboarding_draft_validation_service.py`
- `services/onboarding/onboarding_draft_audit_evidence_service.py`
- `apps/api/routers/admin_onboarding.py`
- `frontend/src/api/endpoints/adminOnboarding.ts`
- `frontend/src/pages/admin/CompanyOnboardingPage.tsx`

## TASK-102 To TASK-109 Summary

| Task | Outcome | Readiness posture |
| --- | --- | --- |
| TASK-102 | Added additive draft persistence migration `080_onboarding_draft_persistence.sql`. | Draft tables exist in migration chain; no route or write behavior was introduced by the migration alone. |
| TASK-103 | Added clean DB/static migration tests for the draft tables. | CI-safe schema assertions cover tables, keys, indexes, sensitive-field exclusions, and no-live-action schema drift. |
| TASK-104 | Added onboarding draft repository primitives with no route wiring. | Repository supports draft intent, sections, validation snapshots, idempotency references, and audit links without live platform side effects. |
| TASK-105 | Added draft idempotency helper. | Idempotency is hash/scoped and supports replay/conflict handling without raw key storage. |
| TASK-106 | Added draft validation service using read-only readiness aggregation. | Draft payload validation and readiness preview can run safely without creating live entities. |
| TASK-107 | Added guarded admin draft-save endpoint. | `POST /admin/onboarding/drafts` saves draft intent only behind admin/operator permissions and rejects live-action attempts. |
| TASK-108 | Integrated company onboarding UI with draft save. | Company shell can save draft intent while live actions remain disabled and fallback behavior remains available. |
| TASK-109 | Added draft-save audit evidence helper and reference wiring. | Successful draft save creates safe, reference-only audit-link evidence with no webhook/event dispatch. |

## Completed Capabilities

The platform can now:

1. Save onboarding draft intent through a guarded admin route.
2. Validate draft payloads safely before persistence.
3. Produce readiness preview summaries for draft intent.
4. Apply idempotency using scoped hashes and payload hashes.
5. Preserve no-live-action guardrails during draft save.
6. Record safe audit-link evidence references for draft save.
7. Save company onboarding draft intent from the frontend shell.
8. Keep external references as the user-facing boundary while `tenant_code` remains internal.

## Explicitly Not Live

The platform still does not implement:

- submit-for-review;
- dry-run validation routes;
- tenant, account, company, organisation, producer, sponsor, distributor, partner, user, member, role, or invite creation;
- campaign or opportunity creation, publication, launch, approval, pause, close, or go-live;
- link/code generation, issue, rotation, redemption, or mutation;
- credential generation, storage, reveal, rotation, activation, or lifecycle;
- webhook subscription, signing, queueing, retry, replay, or delivery;
- funding, wallet, fulfilment, settlement, payout, reversal, reconciliation, retry, repair, or money movement;
- live DB verification or production smoke testing.

## Validation Baseline

| Task | Validation baseline |
| --- | --- |
| TASK-102 | Migration hygiene passed; local clean DB replay was limited by local Python/runtime setup. |
| TASK-103 | Static migration tests directly executed and compile checks passed; CI-safe assertions cover draft schema readiness. |
| TASK-104 | Repository tests passed under local available tooling and compile checks passed. |
| TASK-105 | Idempotency helper tests passed under local available tooling and compile checks passed. |
| TASK-106 | Validation service tests passed under local available tooling and compile checks passed. |
| TASK-107 | Targeted admin onboarding API and related service tests passed where local dependencies were available; route remained draft-save-only. |
| TASK-108 | Frontend company draft-save tests, related onboarding tests, full frontend test suite, build, and lint passed with existing warning baseline. |
| TASK-109 | Direct helper tests, Python compile checks, Ruff on changed Python files, migration hygiene, line-length sanity, and diff whitespace checks passed. Local `pytest` and `black` were limited by available local tooling. |

Local tooling limitations recorded in TASK-109 remain relevant: the default Windows Python was broken, the bundled runtime lacked some test dependencies such as `pytest`/`httpx`, and the available `black` shim timed out. CI should remain the authority for full backend test execution until the local runtime is repaired.

## Permission And Safety Posture

Current posture:

- Draft save is admin/operator scoped.
- Adjacent-role access is rejected by existing permission tests.
- Actor context comes from authentication, not request body.
- User-facing scope uses external references.
- `tenant_code` is not accepted or displayed as a user-facing onboarding identifier.
- Idempotency stores hashes/references rather than raw key material.
- Audit evidence stores safe summaries and references, not raw before/after payloads.
- Responses and evidence avoid secrets, credentials, raw provider internals, raw audit internals, UCN/private identifiers, webhook delivery internals, funding/wallet/settlement/fulfilment/retry internals, and money movement details.
- No credential lifecycle, webhook dispatch, event replay, go-live activation, funding, fulfilment, settlement, retry, wallet, or money movement is introduced.

## Blockers

TASK-027 remains blocked because approved safe read-only runtime database access is unavailable. It still requires environment name, read-only DB credentials, write-protection confirmation, and approval for runtime/API smoke checks.

TASK-028 remains blocked because TASK-027 has not produced verified live/schema drift results. TASK-028 should only resolve confirmed mismatches or explicitly deferred unknowns.

These blockers do not prevent local/CI-safe dry-run validation work. They do prevent claims of live-state readiness or production onboarding readiness.

## Readiness Decision

Decision: implement a guarded dry-run validation route before submit-for-review.

Rationale:

1. TASK-106 already provides a draft validation service.
2. TASK-099 already defines the dry-run route contract.
3. Dry-run validation is safer than submit-for-review because it is no-op by design.
4. Dry-run validation can harden permissions, safe errors, redaction, missing evidence, and no-mutation assertions before any review state transition exists.
5. Submit-for-review should wait until dry-run validation is proven through API tests and frontend preview integration.

Do not proceed directly to live onboarding, go-live, credential lifecycle, webhook delivery, or money movement. Do not implement submit-for-review until the dry-run route and its frontend preview are complete and reviewed.

## Recommended Next Wave

| Task | Title | Type | Objective |
| --- | --- | --- | --- |
| TASK-111 | Add guarded onboarding dry-run validation route | API/tests | Expose no-op validation using TASK-106 and TASK-099 without persistence side effects. |
| TASK-112 | Add dry-run validation permission and no-mutation tests | API/tests | Prove auth, adjacent-role rejection, safe errors, no persistence, no audit write, no event dispatch, and no live actions. |
| TASK-113 | Integrate frontend dry-run validation preview | Frontend/API integration | Let onboarding shells preview validation/readiness without saving or submitting. |
| TASK-114 | Submit-for-review contract final review | Docs/checkpoint | Decide the minimal submit-for-review boundary after dry-run is proven. |
| TASK-115 | Add submit-for-review repository state transition | Service/repository/tests | Add draft status transition primitives only, with no API route and no live activation. |
| TASK-116 | Add guarded submit-for-review endpoint | API/tests | Expose review submission only after repository transition and evidence guardrails pass. |
| TASK-117 | Integrate frontend submit-for-review controls | Frontend/API integration | Add disabled-by-default guarded submit flow with clear non-live language. |
| TASK-118 | Add submit-for-review audit evidence | Service/tests | Record safe review-submission evidence without webhook/event dispatch. |
| TASK-119 | Add review-flow permission and redaction regression tests | API/tests | Lock review routes to intended roles, scopes, and safe response boundaries. |
| TASK-120 | Submit-for-review readiness checkpoint | Docs | Decide whether a later approval/review workflow is safe to scope. |

## Guardrails For Next Wave

The next wave must preserve:

- no live onboarding;
- no tenant/account/company creation;
- no producer/sponsor/distributor creation;
- no user/member/role creation;
- no invite delivery;
- no campaign/opportunity publication;
- no link/code mutation;
- no credential lifecycle;
- no webhook delivery, retry, replay, queueing, or signing;
- no go-live activation;
- no funding, wallet, fulfilment, settlement, retry, reversal, reconciliation, payout, repair, or money movement;
- no secrets, production data, or live DB access;
- no TASK-027/TASK-028 unblocking without approved runtime verification.

## Readback Checklist

Before starting TASK-111, confirm:

- TASK-102 through TASK-109 are represented accurately;
- draft-save exists, but submit-for-review does not;
- dry-run validation route does not yet exist;
- TASK-111 is no-op validation, not a write command;
- `tenant_code` remains internal;
- external references remain user-facing;
- idempotency and audit evidence avoid raw sensitive material;
- TASK-027 and TASK-028 remain blocked;
- no live credential, webhook, campaign, funding, fulfilment, settlement, retry, go-live, or money movement behavior is introduced.
