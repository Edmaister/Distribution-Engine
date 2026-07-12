# TASK-130 Review Workflow Readiness Checkpoint

Date: 2026-07-12

Status: Complete.

## Purpose

TASK-130 summarizes the onboarding review-decision wave from TASK-121 through
TASK-129 and decides whether further implementation is safe without broader
live DB/state verification. It is documentation only. It does not add backend
routes, frontend code, services, tests, schema, migrations, live DB access,
secrets, production data, live onboarding, credential lifecycle, webhook
delivery, funding, fulfilment, settlement, retry, wallet, go-live, billing,
ledger, or money movement.

The decision is: the review-decision foundation is ready as a guarded internal
operator workflow, but it is not a launch, activation, or production onboarding
workflow. Further implementation may continue only where it strengthens
review-only posture, product packaging, support visibility, or approved
read-only verification. It must not proceed into approval-to-launch or
downstream activation without a separate reviewed task chain.

## Boundary Classification

Product boundary: Shared Platform.

Required boundary docs checked:

- `AGENTS.md`
- `docs/product/README.md`
- `docs/roadmap/README.md`
- `docs/roadmap/ORDERED_TASK_LIST.md`
- `docs/roadmap/ONBOARDING_REVIEW_DECISION_WORKFLOW_CONTRACT_FINAL_REVIEW_TASK_121.md`
- `docs/roadmap/ONBOARDING_APPROVAL_TO_GO_LIVE_SEPARATION_TASK_128.md`
- `docs/roadmap/ONBOARDING_PRE_GO_LIVE_SAFETY_CHECKPOINT_TASK_129.md`
- `docs/roadmap/TASK_027_LOCAL_DB_VERIFICATION_RESULTS.md`
- `docs/roadmap/TASK_028_SCHEMA_UNCERTAINTY_RESOLUTION.md`

Shared primitive impact: onboarding review lifecycle, admin/operator RBAC,
external reference scope, idempotency, safe audit evidence, redaction,
readiness validation, frontend review controls, live verification posture, and
no-live-action guardrails.

Source duplication: No.

## Source Review

Reviewed implementation and evidence sources:

- `services/onboarding/onboarding_review_decision_service.py`
- `services/onboarding/onboarding_draft_idempotency_service.py`
- `services/onboarding/onboarding_draft_audit_evidence_service.py`
- `apps/api/routers/admin_onboarding.py`
- `frontend/src/api/endpoints/adminOnboarding.ts`
- `frontend/src/pages/admin/CompanyOnboardingPage.tsx`
- `test/test_onboarding_review_decision_service.py`
- `test/test_onboarding_draft_audit_evidence_service.py`
- `test/api/test_admin_onboarding_api.py`
- `docs/roadmap/ORDERED_TASK_LIST.md`
- `docs/roadmap/TASK_027_LOCAL_DB_VERIFICATION_RESULTS.md`
- `docs/roadmap/TASK_028_SCHEMA_UNCERTAINTY_RESOLUTION.md`

No live DB access was attempted for this checkpoint. No secrets were inspected.

## Completed Review Wave

TASK-121 defined the review-decision contract. It established that review
decisions are internal classification only, not launch decisions, and that the
current schema does not support separate persisted approved/rejected review
statuses.

TASK-122 added service primitives for submitted onboarding drafts. The service
records review decisions only for `READY_FOR_REVIEW` drafts, requires
admin/operator role, expected version, scoped idempotency, validation evidence,
and a reason, stores reason evidence as a hash, and returns safe
no-live-action envelopes.

TASK-123 locked review-decision eligibility and validation behavior with service
tests. Coverage includes unsupported schema outcomes, launch-like outcomes,
invalid source states, missing scope, invalid idempotency, validation blockers,
missing evidence, adjacent roles, stale versions, replay/conflict behavior, and
redaction.

TASK-124 exposed the guarded admin/operator review-decision endpoint. The route
uses existing onboarding auth, external-reference scope checks, saved draft
validation, scoped idempotency, stale-version handling, and review-decision
service primitives.

TASK-125 added safe reference-only review-decision audit evidence. Evidence
records actor, role, external references, draft ref/version, operation/status,
review outcome, reason hash reference, idempotency hash reference, correlation
ID, state hashes, validation/readiness summaries, redaction categories, and
no-live-action confirmation. It does not dispatch events or webhooks.

TASK-126 integrated frontend review-decision controls into the company
onboarding workflow. The UI supports `APPROVED_FOR_INTERNAL_REVIEW` and
`BLOCKED`, requires a bounded reason, uses external references and idempotency,
displays audit references, and keeps live actions disabled or out of scope.

TASK-127 added RBAC and redaction regression tests for review-decision routes
and related onboarding review surfaces. Coverage includes authorized
admin/operator access, adjacent-role rejection, nested `tenant_code` rejection,
hostile saved-evidence blocking/redaction, no raw reason/secrets/provider/audit
or value-transfer leakage, and no live mutation calls.

TASK-128 documented the separation between review approval and go-live. It
confirmed that `APPROVED_FOR_INTERNAL_REVIEW` is review classification only,
and current responses keep `approval_to_launch: false` and
`go_live_enabled: false`.

TASK-129 added the pre-go-live safety checkpoint. It created an explicit stop
gate before approval-to-launch, live onboarding, downstream activation,
dispatch, or money-domain planning.

## Current Capability Rating

For an internal onboarding review-decision workflow, the capability is now
strong: approximately 8/10 to 8.5/10.

Strengths:

- clear contract boundary;
- guarded service and API path;
- frontend controls for operators;
- admin/operator RBAC;
- scoped idempotency;
- safe reference-only audit evidence;
- validation and stale-version protection;
- safe error and redaction posture;
- no-live-action and no-money guardrails;
- regression coverage across service, API, audit evidence, and frontend
  surfaces.

It is not 10/10 because the workflow remains intentionally review-only and
because production activation readiness requires non-local verification,
schema-backed launch lifecycle states, downstream activation design, rollback,
and domain-owned dispatch/money controls.

## Remaining Blockers

The remaining blockers are not flaws in the review workflow foundation; they
are the reasons the foundation must not be marketed as live onboarding.

1. Staging and production verification are not complete.
2. Migration tracking or equivalent applied-migration evidence is not identified
   locally.
3. TASK-027 is locally verified but not globally complete for production
   readiness.
4. TASK-028 resolved local schema uncertainty, but staging/production drift is
   unknown.
5. `APPROVED_FOR_INTERNAL_REVIEW` is metadata/review classification, not a
   schema-backed launch state.
6. Separate persisted statuses for changes requested, rejected, and launch
   approved remain unimplemented unless future schema review adds them.
7. Approval-to-launch permission boundaries are not defined.
8. Activation idempotency, retry, replay, failure, and rollback behavior is not
   implemented.
9. Account, identity, campaign, link/code, credential, webhook, event, funding,
   fulfilment, settlement, wallet, billing, ledger, and money domains do not
   have a reviewed activation task chain from this checkpoint.
10. Downstream event/webhook dispatch and money movement remain explicitly out
    of scope.

## No-Live-Action Posture

The current review workflow preserves these facts:

- `APPROVED_FOR_INTERNAL_REVIEW` is not approval-to-launch.
- `approval_to_launch` remains false.
- `go_live_enabled` remains false.
- `no_live_action_confirmed` remains true.
- Review evidence remains reference-only and no-dispatch.
- Raw reason text, idempotency keys, secrets, provider payloads, raw audit
  payloads, webhook internals, funding/wallet/settlement/fulfilment/retry
  internals, and money internals are not returned as user-facing evidence.
- User-supplied `tenant_code` remains unsafe for onboarding review requests.

## Safe Next Priorities

Safe next priorities are:

1. Resume the productized Referral SaaS implementation roadmap where the next
   task is bounded by the Referral SaaS product brief, gap matrix, and ordered
   task list.
2. Continue documentation or tests that strengthen review-only posture,
   redaction, permissions, audit evidence, and idempotency.
3. Plan non-local read-only verification only after the target environment and
   credentials are explicitly approved.
4. Add operator visibility for review decisions only if it does not introduce
   launch, activation, credential, webhook, funding, fulfilment, settlement,
   wallet, billing, ledger, or money actions.
5. Close confirmed local drift through separate reviewed schema/service tasks,
   with money-domain changes treated under the money and audit rules.

Unsafe next priorities are:

- approval-to-launch implementation;
- go-live workflow implementation;
- live onboarding or provisioning;
- credential lifecycle behavior;
- webhook delivery, queueing, replay, retry, or dispatch;
- event dispatch;
- account/user/role/invite creation;
- campaign/opportunity publication or activation;
- funding, fulfilment, settlement, wallet, billing, ledger, payout,
  reconciliation, repair, retry, reversal, or money movement.

## Readiness Decision

Decision: complete the onboarding review-decision foundation wave and do not
continue toward go-live from this wave.

The platform can safely keep review-decision work as an internal guarded
workflow. The next implementation work should return to bounded productization
or verification tasks, especially Referral SaaS launch-readiness slices, unless
a future task explicitly scopes a separate go-live chain.

## Validation

Documentation/readback only.

This checkpoint confirms:

- TASK-121 through TASK-129 are summarized;
- review-decision capabilities are represented as current facts;
- `APPROVED_FOR_INTERNAL_REVIEW` remains review classification only;
- approval-to-launch and go-live remain blocked;
- TASK-027 has local read-only evidence but no staging/production verification;
- TASK-028 resolved local uncertainty but not global environment drift;
- safe next priorities are listed;
- no backend code, frontend code, services, routes, tests, schema, migrations,
  live DB access, secrets, production data, live onboarding, credential
  lifecycle, webhook delivery, funding, fulfilment, settlement, retry, wallet,
  go-live, billing, ledger, or money movement was introduced.
