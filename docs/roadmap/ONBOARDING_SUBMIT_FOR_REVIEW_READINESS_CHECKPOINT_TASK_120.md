# Onboarding Submit-For-Review Readiness Checkpoint

Task: TASK-120
Date: 2026-07-05
Status: Complete

## Purpose

This checkpoint closes the dry-run validation and submit-for-review foundation wave from TASK-111 through TASK-119. It records what is now available, what remains explicitly not live, and whether the next review workflow wave can be scoped safely.

The decision is intentionally narrow: the platform is ready to scope an internal review decision workflow foundation, but not approval-to-launch, go-live, live onboarding, provisioning, credential lifecycle, webhook delivery, funding, fulfilment, settlement, retry, wallet, or money movement.

## Source Review

Reviewed sources:

- `docs/roadmap/ORDERED_TASK_LIST.md`
- `docs/roadmap/ONBOARDING_DRAFT_SAVE_READINESS_CHECKPOINT_TASK_110.md`
- `docs/roadmap/ONBOARDING_SUBMIT_FOR_REVIEW_CONTRACT_FINAL_REVIEW_TASK_114.md`
- `docs/sa/ONBOARDING_DRY_RUN_VALIDATION_ENDPOINT_CONTRACT.md`
- `docs/sa/ONBOARDING_AUDIT_EVENT_CAPTURE_DESIGN.md`
- `apps/api/routers/admin_onboarding.py`
- `services/onboarding/onboarding_submit_for_review_service.py`
- `services/onboarding/onboarding_draft_audit_evidence_service.py`
- `test/api/test_admin_onboarding_api.py`
- `AGENTS.md`

No live DB access was attempted. No secrets were inspected.

## Completed Wave Summary

TASK-111 added guarded dry-run validation at `POST /admin/onboarding/validate`. It returns readiness preview, missing evidence, blockers, warnings, redactions, and no-live-action guardrails without persistence.

TASK-112 locked dry-run validation permission, redaction, safe-error, and no-mutation behavior with API regression tests.

TASK-113 integrated frontend dry-run validation preview into the company onboarding shell while preserving draft-save behavior, shell fallback, disabled live actions, and no `tenant_code` user-facing exposure.

TASK-114 completed the submit-for-review contract review and approved a saved-draft status transition only. It explicitly deferred approval, go-live, live onboarding, credential lifecycle, webhook delivery, and money movement.

TASK-115 added submit-for-review service primitives that transition eligible saved drafts to `READY_FOR_REVIEW` with optimistic version, idempotency, validation, role, and safe-error handling.

TASK-116 exposed guarded `POST /admin/onboarding/drafts/{draft_ref}/submit-for-review` for admin/operator users only. The endpoint validates persisted evidence, external scope, expected version, and idempotency while rejecting user-facing `tenant_code`.

TASK-117 integrated frontend submit-for-review controls into the company onboarding shell. The UI submits saved drafts for review only and keeps account creation, invites, go-live, credentials, webhooks, funding, fulfilment, settlement, retry, wallet, and money actions disabled.

TASK-118 added safe reference-only submit-for-review audit evidence through `onboarding_draft_audit_links`. Evidence includes actor, role, external references, draft ref/version, idempotency hash reference, correlation ID, before/after hashes, validation/readiness summaries, redaction categories, and no-live-action confirmation. It does not dispatch events or webhooks.

TASK-119 added review-flow API regression coverage for state, dry-run validation, draft save, and submit-for-review routes. Tests confirm unauthorized and adjacent-role rejection, cross-scope submit rejection, safe missing-draft behavior, redaction, no raw `tenant_code`, no secret/provider/audit/webhook/money internals, and no live mutation invocation.

## Available Capabilities

The platform can now:

- Read onboarding state safely through the admin onboarding read route.
- Run no-op onboarding dry-run validation.
- Save onboarding draft intent behind guarded admin/operator controls.
- Store draft sections, validation snapshots, idempotency hash references, and audit-link references.
- Submit saved drafts for review as a draft status transition to `READY_FOR_REVIEW`.
- Return safe bounded submit-for-review responses for success, replay, stale version, invalid state, validation blockers, missing draft, conflict, and unauthorized/adjacent roles.
- Show frontend company onboarding controls for draft save, dry-run validation preview, and submit-for-review without enabling live platform actions.
- Record reference-only submit-for-review audit evidence without event/webhook dispatch.
- Regression-test RBAC, external scope, redaction, safe errors, no `tenant_code` exposure, and no-live-action guarantees.

## Explicitly Not Live

The wave does not implement or enable:

- Approval workflow decisions beyond submitted-for-review status.
- Go-live, activation, launch, or production onboarding.
- Tenant/company/account creation.
- User/member creation, invite delivery, identity-provider writes, or role assignment.
- Campaign/opportunity publication.
- Credential generation, rotation, activation, storage, or display.
- Webhook subscription activation, delivery, signing, queueing, dispatch, retry, or replay.
- Funding, wallet, fulfilment, settlement, retry, billing, ledger, or money movement.
- Audit event dispatch or external event persistence.
- Live DB verification or live environment smoke checks.

`tenant_code` remains internal and must not become a user-facing onboarding identifier.

## Validation Baseline

The latest roadmap validation records the following baseline:

- `test/api/test_admin_onboarding_api.py`: 78 tests passed in TASK-119.
- `test/test_onboarding_submit_for_review_service.py`: 9 tests passed in TASK-119.
- `test/test_onboarding_draft_audit_evidence_service.py`: 11 tests passed in TASK-119.
- `test/test_onboarding_draft_validation_service.py`: 9 tests passed in TASK-119.
- `scripts/check_migrations.py`: passed in TASK-119.
- Ruff and Python compile checks passed for changed Python files in TASK-119.
- Frontend submit-for-review validation in TASK-117 passed targeted helper/page/smoke tests, full frontend tests, build, and lint with the existing warning baseline.

Known local limitation from earlier tasks: Black timed out locally on some changed Python files before producing a result, with no formatting error reported by Ruff or diff checks.

## Permission And Safety Posture

The onboarding review flow is currently guarded by admin/operator role checks. Adjacent roles are rejected before projection, validation, repository, transition, or audit helpers run.

Responses are bounded and safe:

- Unknown or cross-scope draft references return safe not-found behavior.
- User-supplied `tenant_code` is rejected and not echoed.
- Secret-like, credential, provider, audit, webhook delivery, retry, funding, wallet, fulfilment, settlement, and money-movement internals are redacted or omitted.
- Submit-for-review audit evidence is reference-only and does not dispatch events or webhooks.
- Idempotency stores hash/reference evidence rather than raw idempotency keys or secret material.
- Live/go-live actions remain disabled.

## Blockers

TASK-027 remains blocked because approved safe read-only runtime database access is not available.

TASK-028 remains blocked because TASK-027 live DB verification is blocked and no verified drift results exist.

This checkpoint does not unblock TASK-027 or TASK-028.

## Readiness Decision

Decision: ready to scope the next review workflow foundation wave with strict boundaries.

The next wave may introduce internal review-decision contracts, service primitives, guarded endpoints, audit evidence, and frontend controls for review outcomes such as approved for internal review, changes requested, or rejected. Those outcomes must remain review-state classifications only.

The next wave must not turn review approval into go-live. Any approval wording must be explicitly separated from launch, provisioning, account creation, campaign publication, credentials, webhook delivery, funding, fulfilment, settlement, retry, wallet, and money movement.

## Recommended Next Wave

Recommended TASK-121 onward wave:

1. TASK-121: Review decision workflow contract final review.
2. TASK-122: Add review decision service primitives.
3. TASK-123: Add review decision validation and eligibility tests.
4. TASK-124: Add guarded admin review decision endpoint.
5. TASK-125: Add review decision audit evidence references.
6. TASK-126: Add frontend review decision controls.
7. TASK-127: Add review decision RBAC and redaction regression tests.
8. TASK-128: Document approval-to-go-live separation.
9. TASK-129: Add pre-go-live safety checkpoint.
10. TASK-130: Review workflow readiness checkpoint.

The wave should stay small, reviewable, and no-live-action by default.

## Guardrails For Next Work

Any next task must stop if it requires:

- Live DB access, production data, or secrets.
- Schema or migration changes unless explicitly scoped and reviewed.
- Auth weakening or broad permission refactors.
- Account creation, invite delivery, identity-provider writes, role assignment, campaign publication, credential lifecycle, webhook delivery, event dispatch, go-live, funding, wallet, fulfilment, settlement, retry, billing, ledger, or money movement.
- Exposing `tenant_code` as a user-facing identifier.
- Exposing raw secrets, provider internals, audit internals, webhook delivery internals, funding/wallet/settlement/fulfilment/retry internals, or raw sensitive payloads.

## Readback Checklist

- TASK-111 through TASK-119 are represented.
- Available capabilities are limited to read, dry-run, draft save, submit-for-review, safe evidence, frontend controls, and tests.
- Explicitly not-live boundaries are documented.
- TASK-027 and TASK-028 remain blocked.
- The readiness decision allows only a review workflow foundation wave, not live approval/go-live.
- Recommended next tasks are small enough for one branch/one PR each.
- No implementation, schema, migrations, live DB access, secrets, downstream delivery, or money movement were introduced by this checkpoint.
