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

## TASK-431 Baseline Evidence

At the TASK-431 baseline, the operations read model used
`referral_saas_support_cases` for work-item,
priority, status, owner, customer, jurisdiction, and update-time evidence. The table
has `created_at`, `updated_at`, and `closed_at`, but no governed target policy,
effective policy version, due time, pause ledger, elapsed service time, or breach
evidence. Consequently the API correctly returns:

- `withinServiceTargetPercent: null`;
- `serviceTargetStatus: UNAVAILABLE`; and
- `serviceTarget.dueAt: null` for each work item.

`provider_sla_metrics` is not an acceptable substitute because it belongs to the
provider/fulfilment boundary rather than customer-support operations.

## Governed Policy Contract

The implementation persists an effective-dated policy selected from the
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

## Read Semantics

The backend exposes plain-language service-target outcomes from approved schema
and persisted clock evidence. The canonical concepts are:

- on track;
- approaching target;
- overdue;
- paused under an approved reason;
- completed within target;
- completed after target; and
- unavailable when no valid policy or clock evidence exists.

These concepts are represented by the implemented service-target projection and
remain governed by its database migration and service contract.

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
4. Replace the blanket unavailable UI only after database-backed API evidence is
   proven while retaining `UNAVAILABLE` for individual missing or unsupported
   evidence.
5. Run account/jurisdiction leakage, calendar, pause/resume, reopen, boundary-time,
   idempotency, audit, degraded-state, and end-to-end verification.

Each implementation step requires its own ordered task and reviewed schema/API
contract. TASK-431 defined the boundary; TASK-432 through TASK-436 implement and
prove the bounded capability.

## Implementation Status

- TASK-432 implements the persistence foundation without seeded target values.
- TASK-433 implements Amplifi-admin policy lifecycle commands and deterministic,
  fail-closed approved-policy resolution.
- TASK-434 implements policy-pinned, server-owned support-case clock lifecycle,
  ordinary elapsed-time due calculation, completion, reopen evidence, and approved
  pause/resume commands. Unsupported business-calendar calculation fails closed.
- TASK-435 implements jurisdiction-safe rolling 30-day aggregation and server-owned
  due-state presentation in the existing Operations read model and UI.
- TASK-436 proves the complete policy-to-clock-to-Operations path on migrated
  PostgreSQL across Namibia and Zambia, including replay, pause/resume, completion,
  audit evidence, unsupported evidence, jurisdiction isolation, and cleanup.
- `UNAVAILABLE` remains required for missing, ambiguous, or unsupported evidence;
  measured percentages are returned only when an eligible persisted denominator
  exists.

## Acceptance Criteria

- Current and target state are explicitly separated.
- Referral SaaS operational targets are not conflated with DLaaS provider SLAs.
- Policy, clock, pause, versioning, audit, permission, and aggregation semantics are
  defined before implementation.
- `UNAVAILABLE` remains the honest response whenever authoritative persistence or
  supported calculation evidence does not exist.
- Downstream work can be implemented without frontend-owned timing or duplicated
  operational state.
- A migrated PostgreSQL release check proves policy governance, clock lifecycle,
  Operations aggregation, jurisdiction isolation, idempotency, audit, degraded
  behavior, and cleanup.
