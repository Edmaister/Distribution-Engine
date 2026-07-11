# TASK-121 Onboarding Review Decision Workflow Contract Final Review

Date: 2026-07-11

Status: Accepted for TASK-121.

## Purpose

TASK-121 defines the smallest safe boundary for internal review decisions after
submit-for-review. It is a documentation checkpoint only. It does not add
backend routes, frontend code, services, tests, schema, migrations, live DB
access, secrets, live onboarding, approval-to-launch, account creation, invite
delivery, campaign publication, credential lifecycle, webhook delivery, funding,
wallet, fulfilment, settlement, retry, go-live, or money movement.

The decision is: the next wave may add internal review decision primitives, but
only as review-state classification. A review decision must not provision,
activate, publish, launch, generate credentials, dispatch events or webhooks,
fund, fulfil, settle, retry, create wallets, bill, or move money.

## Boundary Classification

Product boundary: Shared Platform.

Required boundary docs checked:

- `AGENTS.md`
- `docs/product/README.md`
- `docs/roadmap/README.md`
- `docs/roadmap/ORDERED_TASK_LIST.md`
- `docs/roadmap/ONBOARDING_SUBMIT_FOR_REVIEW_CONTRACT_FINAL_REVIEW_TASK_114.md`
- `docs/roadmap/ONBOARDING_SUBMIT_FOR_REVIEW_READINESS_CHECKPOINT_TASK_120.md`
- `docs/sa/ONBOARDING_DRAFT_SAVE_API_BOUNDARY.md`
- `docs/sa/ONBOARDING_DRAFT_PERSISTENCE_SCHEMA_DESIGN.md`
- `docs/sa/ONBOARDING_AUDIT_EVENT_CAPTURE_DESIGN.md`

Shared primitive impact: onboarding draft lifecycle, admin/operator RBAC,
idempotency, safe audit evidence, redaction, external reference scope, and
no-live-action guardrails.

Source duplication: No.

## Source Review

Reviewed implementation sources:

- `dp/migrations/080_onboarding_draft_persistence.sql`
- `apps/api/routers/admin_onboarding.py`
- `services/onboarding/onboarding_submit_for_review_service.py`
- `services/onboarding/onboarding_draft_idempotency_service.py`
- `services/onboarding/onboarding_draft_audit_evidence_service.py`
- `test/api/test_admin_onboarding_api.py`
- `test/test_onboarding_submit_for_review_service.py`
- `test/test_onboarding_draft_audit_evidence_service.py`

No live DB access was attempted. No secrets were inspected.

## Current Facts

The current implementation supports draft save, dry-run validation, and
submit-for-review.

The submit-for-review service transitions eligible drafts to
`READY_FOR_REVIEW`. It requires admin/operator role, a saved draft, expected
draft version, validation evidence, scoped idempotency, and no validation
blockers. It returns safe results for submitted, replayed, rejected,
idempotency conflict, stale version, invalid state, validation blockers, missing
draft, and permission denial.

The current database status constraint for `onboarding_drafts.status` allows:

- `DRAFT_CREATED`
- `DRAFT_UPDATED`
- `VALIDATION_FAILED`
- `READY_FOR_REVIEW`
- `BLOCKED`
- `DISCARDED`

The schema does not currently allow separate persisted statuses such as
`REVIEW_APPROVED`, `CHANGES_REQUESTED`, or `REVIEW_REJECTED`.

The idempotency helper currently supports:

- `ONBOARDING_DRAFT_CREATE`
- `ONBOARDING_DRAFT_UPDATE`
- `ONBOARDING_DRAFT_VALIDATE`
- `ONBOARDING_DRAFT_SUBMIT_FOR_REVIEW`
- `ONBOARDING_DRAFT_DISCARD`

It does not currently support a review-decision operation type.

Submit-for-review audit evidence is reference-only. It stores actor, role,
permission scope, external references, draft reference and version, operation,
action status, review status, idempotency reference, correlation ID,
before/after hashes, changed state, redactions, validation/readiness summaries,
and no-live-action confirmation. It does not dispatch events or webhooks.

## Readiness Decision

Decision: proceed to TASK-122 only as narrowly scoped service/repository
primitives for internal review decisions.

TASK-122 must stop if it cannot implement review decisions safely within the
current schema and existing repository primitives. Because the current status
constraint does not include approved/rejected decision statuses, TASK-122 must
not casually invent persisted statuses. It has three safe options:

1. Represent the first internal review decision only with existing schema-backed
   statuses and metadata if that is enough for the primitive.
2. Stop and document that a reviewed schema/migration task is required before
   approval, rejection, or changes-requested states can be persisted.
3. Add no implementation and return an explicit stop decision if the current
   primitives cannot support a safe bounded decision.

Do not jump directly to route wiring, frontend controls, approval-to-launch,
go-live, live onboarding, provisioning, account creation, invite delivery,
campaign publication, credential lifecycle, webhook delivery, funding, wallet,
fulfilment, settlement, retry, billing, ledger, or money movement.

## Minimal Review Decision Boundary

The minimal review decision boundary is:

- submitted draft only;
- admin/operator only;
- internal review classification only;
- explicit expected draft version;
- scoped idempotency;
- required decision reason;
- safe validation/readiness re-check or verified current validation evidence;
- safe result envelope;
- no external route exposure until later guarded API task;
- no frontend controls until later guarded frontend task;
- no event or webhook dispatch;
- no live platform mutation;
- no money-domain mutation.

Review decisions are not launch decisions. Approval language must mean only
"accepted by internal review for a later checkpoint" unless a future task
separately implements approval-to-go-live with reviewed schema, permissions,
audit, rollback, live DB verification, and safety gates.

## Allowed Review Outcomes

These are contract outcomes for TASK-122 to evaluate. They are not all current
database statuses.

| Outcome | Meaning | Current schema posture |
| --- | --- | --- |
| `APPROVED_FOR_INTERNAL_REVIEW` | Review accepts the submitted draft for a later pre-go-live checkpoint. | Not schema-backed as a status today; may require metadata-only representation or stop decision. |
| `CHANGES_REQUESTED` | Reviewer requires corrections before further review. | Not schema-backed as a status today; may require `BLOCKED` with safe metadata or stop decision. |
| `REJECTED` | Reviewer rejects the draft from continuing in the current form. | Not schema-backed as a status today; may require `BLOCKED`, `DISCARDED`, or stop decision depending on semantics. |
| `BLOCKED` | A blocker prevents review from progressing. | Schema-backed, but must not hide whether the next action is change, rejection, or operational block. |
| `NO_OP_REPLAYED` | Same idempotency key and same payload replayed. | Supported by idempotency pattern, but review-decision operation support is not implemented yet. |

TASK-122 must name any chosen current-state mapping explicitly in tests. If the
mapping would blur approval, rejection, blocked, discarded, or changes-requested
semantics, it must stop for schema review.

## State Transition Boundary

Allowed source status:

- `READY_FOR_REVIEW` only.

Blocked source statuses:

- `DRAFT_CREATED`
- `DRAFT_UPDATED`
- `VALIDATION_FAILED`
- `BLOCKED`
- `DISCARDED`

Future persisted target status must be one of the schema-backed statuses unless
a reviewed migration expands the lifecycle vocabulary.

Required transition checks:

- draft exists and is accessible through external reference scope;
- current status is `READY_FOR_REVIEW`;
- expected version matches current draft version;
- actor is authorized as admin/operator;
- idempotency key is valid and scoped to actor, external tenant reference,
  operation type, and draft reference;
- validation/readiness evidence is current enough for review decision;
- unsafe fields, live-action attempts, secrets, raw provider payloads, raw audit
  payloads, webhook internals, funding/wallet/settlement/fulfilment/retry
  internals, and money internals remain blocked or redacted.

## Permission Posture

Review decisions are stronger than submit-for-review and must be admin/operator
only at first.

Required posture:

- use the existing onboarding admin role family unless a later permission task
  narrows it further;
- reject adjacent roles before repository, idempotency, validation, audit, or
  transition helpers run;
- do not trust actor role, actor reference, or permission scope from request
  body;
- preserve external references as the user-facing scope;
- reject user-supplied `tenant_code`;
- return safe not-found or permission-denied behavior for inaccessible or
  cross-scope drafts;
- keep support/read-only viewers read-only.

## Idempotency Posture

TASK-122 may add a new supported operation type only if it is narrowly scoped
and tested. Recommended operation direction:

- `ONBOARDING_DRAFT_REVIEW_DECISION`

Required idempotency behavior:

- idempotency key required;
- scope includes actor, external tenant reference, operation type, and
  `draft_ref`;
- request hash includes expected version, review outcome, reason category, safe
  reason hash or bounded reason text, and target state mapping;
- same key and same payload returns replayed safe result;
- same key with different payload returns `IDEMPOTENCY_CONFLICT`;
- replay does not create duplicate audit evidence;
- invalid idempotency material returns a safe validation error;
- raw idempotency keys are never stored or returned.

If the idempotency helper cannot support the operation without broad refactor,
TASK-122 must stop.

## Audit Evidence Expectations

TASK-122 should not dispatch events or webhooks. TASK-125 owns review-decision
audit evidence references, but TASK-122 should shape result data so that later
evidence can be recorded safely.

Required future audit evidence:

- actor reference and actor role;
- permission scope;
- external references;
- draft reference and draft version;
- review decision operation type;
- prior status and resulting status or metadata mapping;
- review outcome;
- reason category and safe reason reference;
- idempotency reference/hash;
- correlation ID;
- before and after state hashes;
- changed state;
- validation/readiness summary;
- redaction categories;
- no-live-action confirmation.

Audit evidence must not include raw secrets, API keys, client secrets, signing
material, tokens, passwords, certificates, raw provider payloads, raw audit
payloads, UCNs/private identifiers, webhook delivery internals,
funding/wallet/settlement/fulfilment/retry internals, SQL, stack traces, or
money details.

## Safe Error Model

Review decisions should use bounded safe errors:

| Code | Meaning |
| --- | --- |
| `DRAFT_NOT_FOUND` | Draft reference is missing, inaccessible, or unavailable. |
| `INVALID_STATE` / `INVALID_DRAFT_STATE` | Draft cannot receive a review decision from its current state. |
| `STALE_DRAFT` | Expected version does not match current draft version. |
| `IDEMPOTENCY_CONFLICT` | Idempotency key was reused with a different review-decision payload. |
| `VALIDATION_BLOCKED` | Validation, missing evidence, permission, unsafe field, or readiness blockers prevent decision. |
| `PERMISSION_DENIED` | Actor is not authorized for review decision. |
| `UNSUPPORTED_REVIEW_OUTCOME` | Requested outcome is not supported by the current reviewed contract. |
| `UNSUPPORTED_SCHEMA_STATE` | Required target state is not schema-backed and must stop for review. |
| `UNSAFE_OPERATION` / `UNSAFE_OPERATION_ATTEMPTED` | Request attempts a live action or unsafe field. |

Errors must not expose stack traces, SQL, table names, raw exception details,
secrets, provider internals, audit internals, webhook internals, money internals,
private identifiers, or internal tenant identifiers as user-facing values.

## Rollback Expectations

Review decision rollback should be conservative:

1. Disable future endpoint exposure before changing persisted state.
2. Keep existing drafts readable.
3. Do not destructively delete drafts, idempotency rows, or audit-link evidence.
4. Do not require downstream cleanup because review decisions must not create
   tenants, accounts, users, roles, invites, campaigns, credentials, webhooks,
   funding records, wallets, fulfilments, settlements, retries, billing, ledger
   entries, or money movement.
5. If a future primitive is reverted, previously reviewed drafts remain in
   their persisted status and can be handled by support policy.
6. If status semantics prove wrong, stop for migration/backfill review rather
   than silently reclassifying review outcomes.

## Explicit Non-Goals

TASK-121 and TASK-122 do not authorize:

- API route exposure;
- frontend controls;
- approval-to-launch;
- go-live;
- live onboarding;
- tenant, account, organisation, producer, sponsor, distributor, partner,
  referrer, customer, user, member, role, seat, or identity-provider creation;
- invite delivery;
- campaign or opportunity creation, publication, launch, pause, close, or
  activation;
- link/code generation, issue, rotation, redemption, or mutation;
- credential generation, storage, reveal, rotation, or activation;
- webhook subscription, signing, queueing, retry, replay, delivery, or dispatch;
- event dispatch;
- funding, wallet, fulfilment, settlement, retry, payout, reversal,
  reconciliation, repair, billing, ledger, or money movement.

## Recommended Next Tasks

TASK-122 should proceed only if it can add safe service/repository primitives:

- evaluate current `READY_FOR_REVIEW` drafts only;
- require expected version and idempotency key;
- use existing repository primitives where safe;
- add or stop on review-decision operation idempotency support;
- return safe results for success, replay, conflict, stale version, invalid
  state, missing draft, validation-blocked, unsupported outcome, unsupported
  schema state, and permission denial;
- add targeted service tests;
- do not add routes, frontend, audit-link creation, event dispatch, schema,
  migrations, live DB access, or money movement.

TASK-123 should harden validation and eligibility tests before any route is
exposed.

TASK-124 should expose a guarded endpoint only after service behavior is proven.

TASK-125 should add safe review-decision audit evidence references only after
the endpoint contract is known.

TASK-126 should add frontend controls only after the endpoint and audit
boundaries are guarded and tested.

TASK-127 should lock RBAC, scope, redaction, and no-live-action behavior with
regression tests before approval-to-go-live separation is documented in
TASK-128.

## TASK-027 And TASK-028

TASK-027 remains blocked because approved safe read-only runtime database access
is unavailable. TASK-028 remains blocked because TASK-027 live DB verification
is blocked and no verified drift results exist.

These blockers do not prevent local/CI-safe service primitives for internal
review decisions. They do prevent claims of production/live onboarding readiness,
live DB drift confidence, external demo readiness, or go-live safety.

## Readback Checklist

- TASK-121 is Shared Platform work.
- Review decisions are internal classification only.
- `READY_FOR_REVIEW` is the only allowed source status.
- Current schema does not support separate approved/rejected review statuses.
- TASK-122 must not invent persisted statuses without reviewed schema support.
- Expected version, idempotency, validation evidence, and admin/operator role are
  required.
- `tenant_code` remains internal-only.
- Audit evidence remains safe and reference-only when later implemented.
- No route, frontend, schema, migration, event dispatch, webhook delivery, live
  onboarding, approval-to-launch, go-live, funding, wallet, fulfilment,
  settlement, retry, billing, ledger, or money movement is introduced.
- TASK-027 and TASK-028 remain blocked.
