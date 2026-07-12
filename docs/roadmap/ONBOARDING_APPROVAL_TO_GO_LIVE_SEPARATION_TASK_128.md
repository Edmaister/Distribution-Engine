# TASK-128 Approval-To-Go-Live Separation

Date: 2026-07-12

Status: Complete.

## Purpose

TASK-128 documents the boundary between internal onboarding review decisions and
any future go-live or downstream activation workflow. It is documentation only.
It does not add backend routes, frontend code, services, tests, schema,
migrations, live DB access, secrets, live onboarding, credential lifecycle,
webhook delivery, funding, fulfilment, settlement, retry, wallet, go-live, or
money movement.

The decision is: an internal review decision may classify an onboarding draft as
accepted for internal review, but it must not approve the draft for launch or
trigger activation work. Any future approval-to-go-live capability requires a
separate reviewed task chain with schema, permission, audit, rollback, live
verification, and no-money/no-dispatch guardrails.

## Boundary Classification

Product boundary: Shared Platform.

Required boundary docs checked:

- `AGENTS.md`
- `docs/product/README.md`
- `docs/roadmap/README.md`
- `docs/roadmap/ORDERED_TASK_LIST.md`
- `docs/roadmap/ONBOARDING_SUBMIT_FOR_REVIEW_READINESS_CHECKPOINT_TASK_120.md`
- `docs/roadmap/ONBOARDING_REVIEW_DECISION_WORKFLOW_CONTRACT_FINAL_REVIEW_TASK_121.md`

Shared primitive impact: onboarding review workflow, admin/operator RBAC,
idempotency, safe audit evidence, redaction, external reference scope, and
no-live-action guardrails.

Source duplication: No.

## Source Review

Reviewed implementation sources:

- `services/onboarding/onboarding_review_decision_service.py`
- `apps/api/routers/admin_onboarding.py`
- `frontend/src/api/endpoints/adminOnboarding.ts`
- `frontend/src/pages/admin/CompanyOnboardingPage.tsx`
- `test/test_onboarding_review_decision_service.py`
- `test/api/test_admin_onboarding_api.py`
- `test/test_onboarding_draft_audit_evidence_service.py`

No live DB access was attempted. No secrets were inspected.

## Current Facts

The current review-decision service records internal review classifications for
submitted onboarding drafts only. It requires admin/operator role, expected draft
version, external draft scope, scoped idempotency, validation evidence, and a
reason.

Supported review outcomes are currently:

- `APPROVED_FOR_INTERNAL_REVIEW`
- `BLOCKED`

`APPROVED_FOR_INTERNAL_REVIEW` preserves the schema-backed
`READY_FOR_REVIEW` draft status and records review-decision metadata. It does
not persist a launch-approved status.

`BLOCKED` maps to the schema-backed `BLOCKED` status.

`CHANGES_REQUESTED` and `REJECTED` remain unsupported until reviewed schema
support exists. Launch-like outcome text is rejected as an unsupported review
outcome.

The review-decision API response explicitly returns:

- `approval_to_launch: false`
- `go_live_enabled: false`
- `no_live_action_confirmed: true`

The review-decision guardrails include no-live-action posture such as:

- `REVIEW_DECISION_ONLY`
- `NO_LIVE_MUTATION`
- `NO_APPROVAL_TO_LAUNCH`
- `NO_ACCOUNT_CREATION`
- `NO_INVITE_DELIVERY`
- `NO_CAMPAIGN_PUBLICATION`
- `NO_CREDENTIAL_LIFECYCLE`
- `NO_WEBHOOK_DISPATCH`
- `NO_AUDIT_EVENT_DISPATCH`
- `GO_LIVE_DISABLED`
- `NO_MONEY_MOVEMENT`

Review-decision audit evidence is reference-only. It records safe references,
hashes, summaries, redaction categories, dispatch-disabled evidence, and
no-live-action confirmation. It does not dispatch events or webhooks.

Frontend review-decision controls consume the guarded API and expose only the
review classification path. They keep approval-to-launch, go-live, credential,
webhook, funding, fulfilment, settlement, retry, wallet, and money actions
disabled or out of scope.

## Separation Rule

Internal review approval means:

- an admin/operator accepted the submitted draft for internal review purposes;
- validation/readiness evidence was acceptable for this review decision;
- a safe audit-link reference can record the decision;
- the draft may continue to a later checkpoint.

Internal review approval does not mean:

- approval to launch;
- go-live readiness;
- live onboarding;
- tenant, account, organisation, user, member, role, or invite creation;
- campaign/opportunity publication, launch, activation, pause, or close;
- credential generation, storage, activation, reveal, rotation, or delivery;
- webhook subscription activation, signing, queueing, retry, replay, or
  delivery;
- event dispatch;
- funding, wallet, fulfilment, settlement, payout, reversal, reconciliation,
  repair, billing, ledger, or money movement.

Any UI, API, docs, or tests that use approval wording must preserve this
distinction. The current safe label is "approved for internal review", not
"approved to launch" or "go-live approved".

## Future Go-Live Prerequisites

A future approval-to-go-live workflow must be separately scoped and must not be
implemented by extending review-decision semantics in place.

Before any go-live implementation is considered, a future task must define and
review:

- schema-backed lifecycle states for approval-to-go-live, rejection, changes
  requested, rollback, and operational block states;
- explicit permission boundaries beyond the current admin/operator review
  permission if needed;
- live DB/state verification and drift posture, including TASK-027/TASK-028
  status;
- idempotency scope for launch approval and downstream activation attempts;
- retry and failure states for activation work;
- rollback and support procedures;
- safe audit evidence for launch approval, activation attempts, failures, and
  reversals;
- redaction rules for secrets, provider payloads, webhook internals, and money
  internals;
- downstream dependency checks for account, identity, campaign, credential,
  webhook, funding, fulfilment, settlement, wallet, billing, ledger, and money
  domains;
- explicit no-dispatch/no-money gates until each downstream domain has its own
  reviewed task scope.

The existing review-decision endpoint must remain review-only until those
prerequisites are implemented and regression-tested under separate tasks.

## Stop Conditions For Future Work

Stop any future task that tries to treat review approval as launch approval
without a reviewed go-live task chain.

Stop if a task requires or introduces:

- live onboarding without live DB verification;
- persisted launch approval without schema review;
- account/user/role/invite creation;
- campaign publication or activation;
- credential lifecycle behavior;
- webhook delivery, queueing, retry, replay, or dispatch;
- event dispatch;
- funding, wallet, fulfilment, settlement, retry, billing, ledger, or money
  movement;
- raw secrets, provider payloads, raw audit payloads, webhook internals, or
  money internals in responses or audit evidence;
- user-facing `tenant_code`;
- auth weakening or broad permission refactors.

## Acceptance Readback

- TASK-128 is Shared Platform documentation work.
- Review decisions are internal classification only.
- `APPROVED_FOR_INTERNAL_REVIEW` is not approval-to-launch.
- Current responses explicitly keep `approval_to_launch` false and
  `go_live_enabled` false.
- Current evidence remains reference-only and no-dispatch.
- Frontend controls must keep live/go-live and money actions disabled.
- Future go-live work requires a separate reviewed task chain.
- No backend code, frontend code, services, routes, tests, schema, migrations,
  live DB access, secrets, credential lifecycle, webhook delivery, funding,
  fulfilment, settlement, retry, wallet, go-live, billing, ledger, or money
  movement was introduced.
