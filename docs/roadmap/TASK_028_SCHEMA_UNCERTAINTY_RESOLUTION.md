# TASK-028 Schema Uncertainty Resolution

Date: 2026-07-12

Status: Local TASK-028 resolution recorded. This resolves TASK-001 unknowns
using TASK-027 local read-only evidence and assigns confirmed drift to follow-up
work. Staging and production were not accessed.

## Scope

This was a documentation and routing task. It did not change schema, service
logic, API behavior, frontend code, seed data, or runtime data.

Evidence came from:

- `docs/roadmap/TASK_027_LOCAL_DB_VERIFICATION_RESULTS.md`
- local read-only metadata queries through `referral_readonly_verifier`
- static inspection of migrations and services named in
  `docs/sa/LIVE_CRITICAL_STATE_INVENTORY.md`

## Resolved Local Facts

| Area | TASK-001 uncertainty | TASK-028 local resolution |
| --- | --- | --- |
| Live DB access | Live schema was not inspected in TASK-001 | Local DB was inspected through a strict read-only verifier role |
| Migration alignment | Onboarding draft persistence tables were initially missing locally | Migration 080 was applied locally and all five onboarding draft tables were verified present |
| Protected API smoke | Protected local admin smoke checks were initially blocked | Local health, OpenAPI, audit summary, failure summary, and funding dashboard read-only smokes now pass |
| `funding_reconciliation_runs.correlation_id` | Static service code reads/writes `correlation_id`, but migration 048 does not define it | Confirmed local drift: the local table does not have `correlation_id`; service/schema mismatch is assigned to TASK-148 |
| Reward ID types | Reward identifiers were mixed across reward/funding/settlement tables | Confirmed local types remain mixed: `rewards.id` is `bigint`, `referral_rewards.reward_id` is `uuid`, `funding_reservations.reward_id` is `text`, and `fulfilment_settlement_ledger.reward_id` is `uuid` |
| `rewards.status` | Static docs said schema default `EARNED`, service accepts wider states | Local DB default is `APPLIED`, current local rows are `APPLIED`, no status check constraint is present, and allowed values remain service-governed |
| Service-governed states | Several status fields had no DB check constraint | Local evidence confirms unconstrained/service-governed fields for `rewards.status`, `fulfilment_audit.status`, `admin_audit_log.action_status`, `referral_event_failures.status`, and `referral_processing_audit.processing_status` |
| `funding_reconciliation_runs.status` | Service writes `MATCHED` and `EXCEPTION`; runtime values unknown | Local field exists but has no rows; no check constraint was observed |

## Confirmed Follow-Up

TASK-148 is added to fix the confirmed
`funding_reconciliation_runs.correlation_id` schema/service drift. It must be a
separate implementation task because it changes schema and affects finance
reconciliation evidence.

## Still Not Resolved Globally

- Staging and production schema were not accessed.
- Migration tracking is still not implemented or identified locally.
- Service-governed status fields remain intentional current facts, not DB
  guarantees.
- Canonical reward/liability identifier design remains a broader money-model
  concern; TASK-028 only records current local reality and avoids pretending one
  canonical ID type exists.
- Uniform audit coverage for every manual repair/retry/money transition remains
  a later audit-taxonomy task.

## Validation

- Documentation/readback only.
- Local DB checks used the strict read-only verifier role.
- No raw sensitive payloads or secrets were recorded.
- No successful data write, schema write, repair, replay, retry, funding,
  fulfilment, settlement, wallet, go-live, or money movement occurred.
