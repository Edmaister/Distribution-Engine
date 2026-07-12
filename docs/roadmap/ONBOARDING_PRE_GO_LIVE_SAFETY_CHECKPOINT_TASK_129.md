# TASK-129 Pre-Go-Live Safety Checkpoint

Date: 2026-07-12

Status: Complete.

## Purpose

TASK-129 creates a checkpoint before any go-live or downstream activation work is
considered. It is documentation only. It does not add backend routes, frontend
code, services, tests, schema, migrations, live DB access, secrets, production
data, credential lifecycle, webhook delivery, funding, fulfilment, settlement,
retry, wallet, go-live, billing, ledger, or money movement.

The decision is: the onboarding review-decision wave is useful for internal
operator classification, but it is not a production activation workflow. The
platform must stop before go-live planning unless a future task explicitly
scopes live verification, schema state expansion, launch permissions,
activation idempotency, rollback, downstream dependency checks, and domain-owned
no-dispatch/no-money gates.

## Boundary Classification

Product boundary: Shared Platform.

Required boundary docs checked:

- `AGENTS.md`
- `docs/product/README.md`
- `docs/roadmap/README.md`
- `docs/roadmap/ORDERED_TASK_LIST.md`
- `docs/roadmap/ONBOARDING_REVIEW_DECISION_WORKFLOW_CONTRACT_FINAL_REVIEW_TASK_121.md`
- `docs/roadmap/ONBOARDING_APPROVAL_TO_GO_LIVE_SEPARATION_TASK_128.md`
- `docs/roadmap/TASK_027_LOCAL_DB_VERIFICATION_RESULTS.md`
- `docs/roadmap/TASK_028_SCHEMA_UNCERTAINTY_RESOLUTION.md`

Shared primitive impact: onboarding review workflow, live verification posture,
admin/operator RBAC, idempotency, safe audit evidence, redaction, external
reference scope, and no-live-action guardrails.

Source duplication: No.

## Source Review

Reviewed implementation and evidence sources:

- `services/onboarding/onboarding_review_decision_service.py`
- `apps/api/routers/admin_onboarding.py`
- `frontend/src/api/endpoints/adminOnboarding.ts`
- `frontend/src/pages/admin/CompanyOnboardingPage.tsx`
- `test/test_onboarding_review_decision_service.py`
- `test/api/test_admin_onboarding_api.py`
- `test/test_onboarding_draft_audit_evidence_service.py`
- `docs/roadmap/ORDERED_TASK_LIST.md`
- `docs/roadmap/TASK_027_LOCAL_DB_VERIFICATION_RESULTS.md`
- `docs/roadmap/TASK_028_SCHEMA_UNCERTAINTY_RESOLUTION.md`

No live DB access was attempted for this checkpoint. No secrets were inspected.

## Review Workflow Capabilities Now Available

The review workflow foundation now supports:

- guarded onboarding state, dry-run validation, draft save, and
  submit-for-review flows;
- `READY_FOR_REVIEW` as the schema-backed submitted state;
- internal review-decision service primitives for submitted drafts;
- guarded admin/operator API review-decision endpoint;
- frontend review-decision controls for submitted drafts;
- `APPROVED_FOR_INTERNAL_REVIEW` and `BLOCKED` review outcomes;
- scoped idempotency through `ONBOARDING_DRAFT_REVIEW_DECISION`;
- safe reference-only review-decision audit evidence;
- redaction of secrets, raw provider payloads, raw audit payloads, webhook
  internals, funding/wallet/settlement/fulfilment/retry internals, and money
  internals;
- admin/operator role restriction and adjacent-role rejection;
- external reference scope checks and rejection of user-supplied `tenant_code`;
- regression coverage for RBAC, stale versions, idempotency replay/conflict,
  validation blockers, unsupported schema outcomes, redaction, safe errors,
  no-dispatch, and no-live-action behavior.

The review-decision response and frontend model explicitly keep:

- `approval_to_launch: false`
- `go_live_enabled: false`
- `no_live_action_confirmed: true`

## Still Not A Go-Live Workflow

The current review workflow does not implement or approve:

- approval-to-launch;
- go-live readiness;
- live onboarding;
- tenant, account, organisation, user, member, role, seat, identity-provider, or
  invite creation;
- campaign or opportunity publication, launch, pause, close, or activation;
- link/code generation, issue, rotation, redemption, or mutation;
- credential generation, storage, reveal, rotation, activation, or delivery;
- webhook subscription activation, signing, queueing, retry, replay, delivery,
  or dispatch;
- event dispatch;
- funding, wallet, fulfilment, settlement, payout, reversal, reconciliation,
  repair, billing, ledger, or money movement.

`APPROVED_FOR_INTERNAL_REVIEW` remains review classification only. It must not be
renamed, displayed, mapped, or treated as "approved to launch" without a future
reviewed go-live task chain.

## TASK-027 And TASK-028 Posture

TASK-027 local verification is recorded:

- local DB metadata/state checks were completed with read-only posture;
- a strict local read-only verifier role was created and verified;
- local onboarding draft persistence tables were aligned and verified;
- local protected read-only API smoke checks passed for health, OpenAPI, audit
  summary, failure summary, and funding dashboard;
- no mutating route was called.

TASK-027 is not globally complete for production readiness:

- staging and production were not accessed;
- non-local credentials and approvals remain required;
- migration tracking remains unidentified locally;
- staging/production drift is unknown.

TASK-028 local schema uncertainty resolution is recorded:

- local TASK-001 unknowns were resolved from TASK-027 evidence;
- confirmed local drift was routed to follow-up work;
- `funding_reconciliation_runs.correlation_id` drift was assigned to TASK-148
  and later addressed by an additive migration task;
- service-governed status fields remain current facts, not database-enforced
  guarantees.

These results improve local confidence, but they do not authorize production
activation, external go-live claims, or downstream money/dispatch behavior.

## Pre-Go-Live Stop Gate

Stop before go-live planning unless all of the following are true in a future
explicitly scoped task:

1. Non-local environment access is approved for read-only verification.
2. Staging and production schema/state checks are completed or explicitly
   deferred with risk acceptance.
3. Migration tracking or equivalent applied-migration evidence is identified.
4. Go-live lifecycle states are schema-backed and reviewed.
5. Approval-to-launch permissions are separately defined from review-decision
   permissions.
6. Launch approval idempotency, retry, failure, replay, and rollback behavior is
   documented and tested.
7. Safe audit evidence is defined for approval, activation attempts, failures,
   reversals, and support actions.
8. Redaction rules cover secrets, credentials, provider payloads, raw audit
   payloads, webhook internals, funding/wallet/settlement/fulfilment/retry
   internals, and money internals.
9. Downstream owner checks exist for account, identity, campaign, link/code,
   credential, webhook, event, funding, fulfilment, settlement, wallet, billing,
   ledger, and money domains.
10. No-dispatch and no-money gates remain default until each downstream domain
    has its own reviewed activation scope.

If any item is missing, the safe next action is to continue review-readiness,
contract, test, or verification work, not go-live implementation.

## Allowed Next Work

Allowed next work after this checkpoint:

- summarize the review-decision wave and decide safe priorities in TASK-130;
- add documentation or tests that strengthen review-only posture;
- plan non-local read-only verification with approved credentials;
- close confirmed local drift through separate schema/service tasks;
- refine product packaging for Referral SaaS and DLaaS without enabling live
  activation;
- improve operator visibility into blocked/ready-for-review states without
  adding launch actions.

## Blocked Next Work

Blocked until separately scoped and reviewed:

- approval-to-launch implementation;
- go-live workflow implementation;
- live onboarding/provisioning;
- credential lifecycle work;
- webhook delivery/dispatch/retry/replay;
- event dispatch;
- account/user/role/invite creation;
- campaign/opportunity publication or activation;
- funding, wallet, fulfilment, settlement, billing, ledger, payout, reversal,
  reconciliation, repair, retry, or money movement.

## Readiness Decision

Decision: not ready for go-live planning.

The review workflow foundation can continue into TASK-130 for a review-wave
readiness checkpoint. It must not proceed into approval-to-launch, activation,
or downstream domain implementation from this checkpoint.

## Validation

Documentation/readback only.

This checkpoint confirms:

- review-decision capabilities are listed as current facts;
- `APPROVED_FOR_INTERNAL_REVIEW` remains separate from approval-to-launch;
- `approval_to_launch` and `go_live_enabled` remain false in the current
  review-decision contract;
- TASK-027 has local read-only evidence but no staging/production verification;
- TASK-028 records local schema uncertainty resolution and remaining global
  unknowns;
- explicit stop conditions exist before go-live planning;
- no backend code, frontend code, services, routes, tests, schema, migrations,
  live DB access, secrets, production data, credential lifecycle, webhook
  delivery, funding, fulfilment, settlement, retry, wallet, go-live, billing,
  ledger, or money movement was introduced.
