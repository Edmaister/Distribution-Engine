# Referral SaaS Operational Service-Target Contract

## Purpose

Define the governed source required before Amplifi Global can report service-target
performance for Referral SaaS operational work. This contract closes the design gap
identified by TASK-425 without inventing an SLA percentage in the frontend or
reusing DLaaS provider and fulfilment SLA evidence.

## Product Boundary

- Product boundary: Referral SaaS with Shared Platform time, audit, idempotency,
  permission, and observability primitives.
- Source duplication: No. The Operations Workspace continues to consume one
  authoritative operations read model.
- In scope: account-scoped Referral SaaS operational work represented by persisted
  support cases and later explicitly approved Referral SaaS work types.
- Out of scope: provider fulfilment SLAs, distributor routing, funding, settlement,
  billing, payouts, wallets, commissions, treasury, and other DLaaS operations.

## Current-State Evidence

The current operations read model uses `referral_saas_support_cases` for work-item,
priority, status, owner, customer, jurisdiction, and update-time evidence. The table
has `created_at`, `updated_at`, and `closed_at`, but no governed target policy,
effective policy version, due time, pause ledger, elapsed service time, or breach
evidence. Consequently the API correctly returns:

- `withinServiceTargetPercent: null`;
- `serviceTargetStatus: UNAVAILABLE`; and
- `serviceTarget.dueAt: null` for each work item.

`provider_sla_metrics` is not an acceptable substitute because it belongs to the
provider/fulfilment boundary rather than customer-support operations.

## Target-State Policy Contract

A future implementation must persist an effective-dated policy selected from the
work item's permitted jurisdiction, work type/category, and priority. Policy
resolution must be deterministic, account-safe, and explainable. A policy must
define:

- policy reference and immutable version;
- operating jurisdiction and business timezone;
- applicable work type, category, and priority;
- target duration and measurement unit;
- business calendar and holiday-calendar reference where applicable;
- start event, completion event, and approved pause reasons;
- warning threshold used to identify work approaching its target;
- effective-from/effective-to dates and lifecycle state; and
- creator, reviewer, approver, correlation, and audit evidence.

Policy changes apply prospectively. Existing work retains the resolved policy
version and target evidence captured when its service clock starts unless an
explicit, audited migration is approved.

## Clock And Lifecycle Contract

The operational clock must be server-owned. It starts from the persisted event
defined by the resolved policy, normally support-case creation for the first
supported work type. Assignment or UI access must not silently reset it.

The future persistence model must record, without deriving history from mutable UI
state:

- service clock start;
- resolved target due time;
- accumulated paused duration;
- pause and resume events with reason, actor, and timestamp;
- completion time;
- breach time when applicable; and
- the policy reference/version used for the calculation.

Only policy-approved waiting states may pause a clock. A status label alone is not
sufficient evidence. Reopening completed work must either continue the original
clock or start a linked clock according to an explicit policy rule; it must never
erase the original outcome.

## Target-State Read Semantics

The future backend may expose plain-language service-target outcomes after the
schema and clock implementation are approved. The canonical concepts are:

- on track;
- approaching target;
- overdue;
- paused under an approved reason;
- completed within target;
- completed after target; and
- unavailable when no valid policy or clock evidence exists.

These are target-state semantic concepts, not current implemented status values.
Exact API enums and schema names must be introduced only by the implementation
task and verified against its database migration and service contract.

The Operations Workspace percentage must be calculated by the backend from a
declared reporting window and an explicit eligible denominator. Unavailable,
excluded, and still-open work must be handled by documented rules. The response
must include the reporting window, eligible count, within-target count, excluded
count, and policy coverage so the percentage is explainable. The frontend must not
calculate or repair this metric.

## Safety And Governance Controls

- Tenant/account and permitted-jurisdiction filters apply before aggregation.
- Policy writes and exceptional clock changes require explicit permissions,
  idempotency, audit evidence, and separation of duties where approval is used.
- Raw tenant codes, internal identifiers, secrets, provider payloads, and
  cross-customer evidence remain redacted from operator-facing responses.
- Clock calculations use server timestamps and one documented timezone/calendar
  strategy; browser time is never authoritative.
- Missing policy, invalid policy coverage, stale evidence, or calculation failure
  produces an unavailable/degraded response rather than a fabricated target.
- No service-target command may repair/replay referrals, change campaigns, deliver
  messages, create credentials, bill, or move money.

## Implementation Sequence

1. Add the reviewed effective-dated policy, resolved target, and pause-event schema.
2. Add policy resolution and clock lifecycle services with deterministic tests.
3. Extend the existing Operations Workspace read model and filters; do not create a
   second work-item model.
4. Replace the current unavailable UI only after database-backed API evidence is
   proven.
5. Run account/jurisdiction leakage, calendar, pause/resume, reopen, boundary-time,
   idempotency, audit, degraded-state, and end-to-end verification.

Each implementation step requires its own ordered task and reviewed schema/API
contract. TASK-431 defines the boundary only; it does not claim runtime SLA support.

## Implementation Status

- TASK-432 implements the persistence foundation without seeded target values.
- TASK-433 implements Amplifi-admin policy lifecycle commands and deterministic,
  fail-closed approved-policy resolution.
- Support-case clock creation and lifecycle, due-time calculation, read-model
  aggregation, UI enablement, and end-to-end proof remain downstream work.
- `UNAVAILABLE` with a null percentage remains the required Operations Workspace
  response until those runtime evidence steps are complete.

## Acceptance Criteria

- Current and target state are explicitly separated.
- Referral SaaS operational targets are not conflated with DLaaS provider SLAs.
- Policy, clock, pause, versioning, audit, permission, and aggregation semantics are
  defined before implementation.
- The existing `UNAVAILABLE` behavior remains the only honest runtime response until
  authoritative persistence and calculation exist.
- Downstream work can be implemented without frontend-owned timing or duplicated
  operational state.
