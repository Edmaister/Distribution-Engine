# TASK-114 Onboarding Submit-For-Review Contract Final Review

Date: 2026-07-05

Status: Accepted for TASK-114.

This checkpoint decides the minimal safe submit-for-review boundary after guarded draft save, dry-run validation, dry-run permission/no-mutation tests, and frontend dry-run preview have been proven. It is documentation only. It does not add backend routes, frontend code, services, tests, schema, migrations, database access, secrets, production data, submit-for-review implementation, approval, go-live, account creation, campaign publication, credential lifecycle, webhook delivery, funding, wallet, fulfilment, settlement, retry, or money movement.

## Purpose

TASK-114 is the decision gate before any submit-for-review implementation. It answers whether submit-for-review can proceed, and if so, what the smallest safe next implementation must be.

The decision is: submit-for-review may proceed only as repository/service transition primitives in TASK-115. TASK-115 must not expose an API route, frontend control, approval workflow, go-live action, account creation, campaign publication, credential lifecycle, webhook delivery, funding, wallet, fulfilment, settlement, retry, or money movement.

## Source Review

This checkpoint is based on:

- `docs/roadmap/ORDERED_TASK_LIST.md`
- `docs/roadmap/ONBOARDING_DRAFT_SAVE_READINESS_CHECKPOINT_TASK_110.md`
- `docs/sa/ONBOARDING_DRAFT_SAVE_API_BOUNDARY.md`
- `docs/sa/ONBOARDING_DRY_RUN_VALIDATION_ENDPOINT_CONTRACT.md`
- `docs/sa/ONBOARDING_AUDIT_EVENT_CAPTURE_DESIGN.md`
- `docs/sa/ONBOARDING_DRAFT_PERSISTENCE_SCHEMA_DESIGN.md`
- `apps/api/routers/admin_onboarding.py`
- `test/api/test_admin_onboarding_api.py`
- `services/onboarding/onboarding_draft_repository.py`
- `services/onboarding/onboarding_draft_idempotency_service.py`
- `services/onboarding/onboarding_draft_validation_service.py`
- `services/onboarding/onboarding_draft_audit_evidence_service.py`
- `frontend/src/pages/admin/CompanyOnboardingPage.tsx`

## What Is Proven

The platform has proven these foundations before submit-for-review:

| Capability | Evidence |
| --- | --- |
| Guarded draft-save endpoint | `POST /admin/onboarding/drafts` persists draft intent only, uses admin/operator auth, idempotency, validation, safe response fields, and draft-save audit-link evidence. |
| Frontend company draft-save | Company onboarding can save draft intent while keeping create/go-live/live actions disabled. |
| Dry-run validation route | `POST /admin/onboarding/validate` returns validation/readiness preview without draft writes, audit writes, event persistence, or live actions. |
| Dry-run permission and no-mutation tests | API tests cover unauthenticated rejection, adjacent-role rejection, authorized admin/operator access, redaction, no repository persistence, and no validation call for rejected identities. |
| Frontend dry-run validation preview | Company onboarding can preview validation safely without saving, submitting, enabling live actions, exposing `tenant_code`, or displaying secrets. |
| Draft validation service | `validate_onboarding_draft` returns safe validation status, readiness preview, missing evidence, blockers, warnings, next actions, guardrails, and redactions. |
| Idempotency helper | `evaluate_draft_idempotency` already recognizes `ONBOARDING_DRAFT_SUBMIT_FOR_REVIEW`, hashes idempotency keys, scopes by actor/external tenant/action/draft, and detects replay/conflict. |
| Draft audit evidence for save only | Draft-save audit evidence is safe, reference-only, and does not dispatch events or webhooks. |

## Readiness Decision

Submit-for-review may proceed, but only in the following order:

1. TASK-115 adds repository/service transition primitives only.
2. TASK-116 exposes a guarded endpoint only after TASK-115 tests prove transition safety.
3. TASK-117 integrates frontend controls only after the endpoint is guarded and tested.
4. TASK-118 adds submit-for-review audit evidence only as safe reference evidence.
5. TASK-119 locks review-flow permissions, redaction, and no-live-action behavior with regression tests.

Do not jump directly to route wiring, frontend controls, approval, go-live, live onboarding, account creation, invite delivery, campaign publication, credential lifecycle, webhook delivery, funding, wallet, fulfilment, settlement, retry, or money movement.

## Minimal Boundary

The minimal submit-for-review boundary is:

- saved draft only;
- admin/operator only;
- transition existing draft lifecycle status only;
- no approval;
- no activation;
- no tenant, account, company, organisation, producer, sponsor, distributor, partner, user, member, role, or invite creation;
- no campaign or opportunity publication;
- no link/code generation or mutation;
- no credential generation, storage, reveal, rotation, or activation;
- no webhook subscription, signing, queueing, retry, replay, or delivery;
- no funding, wallet, fulfilment, settlement, retry, payout, reversal, reconciliation, or money movement.

The transition means "ready for human/operator review." It must not imply go-live readiness, downstream provisioning, credential activation, partner webhook readiness, funding readiness, fulfilment readiness, settlement readiness, or production launch.

## State Transition Semantics

TASK-115 should implement transition primitives with these semantics:

| Item | Decision |
| --- | --- |
| Allowed source statuses | `DRAFT_CREATED`, `DRAFT_UPDATED`, or `VALIDATION_FAILED` only when current validation allows review. |
| Blocked source statuses | `READY_FOR_REVIEW`, `SUBMITTED_FOR_REVIEW`, `BLOCKED`, and `DISCARDED` require explicit safe no-op, conflict, or invalid-state behavior. |
| Target status | Prefer `READY_FOR_REVIEW` if matching current schema/state vocabulary. Use `SUBMITTED_FOR_REVIEW` only if implementation proves it is canonical and does not conflict with existing status constraints. |
| Invalid state | Return safe `INVALID_STATE` / `INVALID_DRAFT_STATE`; do not mutate the draft. |
| Missing draft | Return safe `DRAFT_NOT_FOUND`; do not leak SQL/table details. |
| Stale version | Require expected version and return `STALE_DRAFT` on mismatch. |
| Duplicate/replay | Same idempotency key, same scope, same payload returns prior safe result; same key with different payload returns `IDEMPOTENCY_CONFLICT`. |
| Idempotency posture | Use hashed idempotency keys and scoped uniqueness. Do not store raw idempotency material. |
| Validation posture | Run or require safe validation evidence before status transition. Do not proceed when unsafe fields, live actions, or critical blockers exist. |

The repository currently exposes `update_draft_metadata_or_status`, and the idempotency helper already supports `ONBOARDING_DRAFT_SUBMIT_FOR_REVIEW`. TASK-115 should wrap those primitives in a focused service rather than exposing route behavior.

## Validation Posture

Submit-for-review requires validation evidence:

- dry-run validation must pass, or produce only acceptable review-time missing evidence;
- unsafe fields and live-action attempts must block transition;
- permission-limited or readiness-blocked states must block transition;
- missing evidence must remain explicit and safe;
- readiness preview must keep go-live disabled;
- validation must not create accounts, publish campaigns, generate credentials, deliver webhooks, fund, fulfil, settle, retry, or move money.

The first implementation should be conservative: if validation status is ambiguous, missing, stale, permission-limited, unsafe, or blocked, do not transition.

## Permission Posture

Submit-for-review is a mutation of draft state and must be narrower than read-only state and dry-run preview.

Required posture:

- platform/admin/operator identities only for the first implementation;
- use the existing onboarding admin role family unless a later permission task narrows it further;
- adjacent roles rejected, including finance, partner, producer, distributor, consumer, support/read-only, public, and worker identities unless a later reviewed task explicitly grants scoped behavior;
- actor context comes from authentication, not request body;
- external references define user-facing scope;
- `tenant_code` remains internal-only and must not be accepted as a user-facing submit scope;
- cross-scope or inaccessible drafts must return safe denial/not-found behavior.

Support/read-only viewers may inspect safe state only through read routes. They must not submit drafts for review.

## Audit Evidence Posture

TASK-115 should not dispatch events or webhooks. TASK-118 will own submit-for-review audit evidence. When audit evidence is added, it must be safe and reference-only.

Required future evidence:

- actor reference and actor role;
- permission scope;
- external references;
- `draft_ref` and draft version;
- operation type `ONBOARDING_DRAFT_SUBMIT_FOR_REVIEW`;
- action status;
- correlation ID;
- idempotency reference/hash;
- before and after status hash or summary;
- changed status section;
- validation/readiness summary;
- redaction categories;
- no-live-action confirmation.

Audit evidence must not include raw secrets, API keys, client secrets, signing material, tokens, passwords, certificates, raw provider payloads, raw audit payloads, UCNs/private identifiers, webhook delivery internals, funding/wallet/settlement/fulfilment/retry internals, SQL, stack traces, or money details.

## Safe Error Model

Submit-for-review should use bounded safe errors:

| Code | Meaning |
| --- | --- |
| `DRAFT_NOT_FOUND` | Draft reference is missing, inaccessible, or unavailable. |
| `INVALID_STATE` / `INVALID_DRAFT_STATE` | Draft cannot transition from its current state. |
| `STALE_DRAFT` | Expected version does not match current draft version. |
| `IDEMPOTENCY_CONFLICT` | Idempotency key was reused with a different submit payload. |
| `VALIDATION_BLOCKED` | Validation, missing evidence, permission, unsafe field, or readiness blockers prevent review. |
| `PERMISSION_DENIED` | Actor is not authorized for submit-for-review. |
| `UNSAFE_OPERATION` / `UNSAFE_OPERATION_ATTEMPTED` | Request attempts a live action or unsafe field. |

Errors must not expose stack traces, SQL, table names, raw exception details, secrets, provider internals, audit internals, webhook internals, money internals, private identifiers, or internal tenant identifiers as user-facing values.

## Rollback Expectations

Submit-for-review rollback should be operationally conservative:

1. Disable any future endpoint before changing persisted state.
2. Keep existing drafts readable.
3. Do not destructively delete drafts or audit/idempotency evidence.
4. If a transition primitive is reverted, drafts remain saved in their prior or review state.
5. No downstream cleanup should be required because submit-for-review must not create live tenants, accounts, campaigns, credentials, webhooks, funding records, wallets, fulfilments, settlements, retries, or money movement.
6. If a later route is disabled, clients should see a safe unavailable/disabled response rather than partial live behavior.

## Explicit Non-Goals

TASK-114 and the next TASK-115 boundary do not authorize:

- approval;
- go-live;
- tenant, account, organisation, producer, sponsor, distributor, partner, referrer, customer, user, member, role, seat, or identity-provider creation;
- invite delivery;
- campaign or opportunity creation, publication, launch, pause, close, or activation;
- link/code generation, issue, rotation, redemption, or mutation;
- credential generation, storage, reveal, rotation, or activation;
- webhook subscription, signing, queueing, retry, replay, or delivery;
- event dispatch;
- audit mutation beyond a later safe reference-only task;
- funding, wallet, fulfilment, settlement, retry, payout, reversal, reconciliation, repair, or money movement.

## Recommended Next Tasks

TASK-115 should proceed as repository/service transition primitives only:

- add a focused submit-for-review transition helper or service;
- use existing draft repository primitives where safe;
- require existing saved draft and expected version;
- use `ONBOARDING_DRAFT_SUBMIT_FOR_REVIEW` idempotency semantics;
- produce safe result objects for success, replay, conflict, stale, invalid state, missing draft, and validation-blocked cases;
- add targeted service/repository tests;
- do not add route wiring.

TASK-116 should expose the endpoint only after TASK-115 is green.

TASK-117 should add frontend submit-for-review controls only after TASK-116 is guarded and tested.

TASK-118 should add safe submit-for-review audit evidence only after the endpoint contract is known.

TASK-119 should add permission and redaction regression tests before any broader review workflow.

## Guardrails For TASK-115

TASK-115 must preserve:

- repository/service tests only;
- no API route;
- no frontend;
- no schema or migration unless the current schema cannot support the transition and the task stops for review first;
- no live DB access;
- no secrets or production data;
- no approval workflow;
- no live activation;
- no audit/event dispatch;
- no credential lifecycle;
- no webhook delivery;
- no account creation;
- no invite delivery;
- no campaign publication;
- no funding, wallet, fulfilment, settlement, retry, or money movement.

If TASK-115 discovers the current draft schema or repository cannot safely support transition semantics, it should update the roadmap with the finding and stop rather than inventing broad schema or route behavior.

## TASK-027 And TASK-028

TASK-027 remains blocked because approved safe read-only runtime database access is unavailable. TASK-028 remains blocked because no verified live/schema drift results exist.

These blockers do not prevent local/CI-safe repository/service transition primitives for saved drafts. They do prevent claims of production/live onboarding readiness, live DB drift confidence, or external demo readiness based on deployed state.

## Readback Checklist

Before starting TASK-115, confirm:

- submit-for-review is not approval;
- submit-for-review is not go-live;
- submit-for-review is a saved-draft status transition only;
- TASK-115 has no API route and no frontend work;
- allowed source statuses and target status are explicit;
- stale version behavior is explicit;
- idempotency uses hashed key references and scoped replay/conflict handling;
- validation blockers prevent transition;
- adjacent roles cannot submit;
- support/read-only cannot submit;
- external references remain user-facing;
- `tenant_code` remains internal-only;
- audit/event dispatch is not introduced;
- safe audit evidence, when later implemented, uses references and hashes only;
- rollback does not require downstream cleanup because no live action occurs;
- no account creation, invite delivery, campaign publication, credential lifecycle, webhook delivery, funding, wallet, fulfilment, settlement, retry, go-live, or money movement is introduced;
- TASK-027 and TASK-028 remain blocked unless separately completed or explicitly deferred by a reviewed decision.
