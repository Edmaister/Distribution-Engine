# Referral SaaS Service-Target Business Calendar Contract

## Purpose

Define the governed calendar primitive required for operational service-target
policies that measure working time rather than continuous elapsed time. The
contract extends the existing TASK-431 through TASK-436 policy-to-clock model; it
does not introduce a second clock, frontend timer, or DLaaS provider-SLA model.

## Product Boundary

- Product boundary: Referral SaaS with Shared Platform time, audit, idempotency,
  permission, and observability primitives.
- Source duplication: No. One shared calendar calculator must serve the existing
  service-target clock lifecycle.
- In scope: versioned working schedules, holidays and exceptional closures,
  timezone/DST rules, deterministic deadline calculation, immutable resolution,
  safe administration, and release evidence.
- Out of scope: employee scheduling, appointment booking, payroll calendars,
  campaign scheduling, provider fulfilment SLAs, billing, settlement, and money.

## Current-State Evidence

Operational service-target policies already carry `business_timezone` and an
optional `business_calendar_ref`. The clock service correctly returns
`BUSINESS_CALENDAR_UNAVAILABLE` when that reference is present because no governed
calendar definition or calculation engine exists. Continuous elapsed-time policies
remain implemented and proven by TASK-434 through TASK-436.

## Calendar Ownership And Scope

A calendar is an Amplifi-governed shared definition selected by stable reference
and immutable version. A policy must pin the exact calendar reference and version
when its clock starts. Calendar edits are prospective and must never recalculate
an existing clock silently.

Each calendar version must define:

- stable calendar code and positive version number;
- IANA business timezone;
- lifecycle state: `DRAFT`, `IN_REVIEW`, `APPROVED`, or `RETIRED`;
- effective-from and optional effective-to timestamps;
- weekly working intervals by local day of week;
- dated full-day holidays and exceptional closures;
- optional dated exceptional working intervals;
- creator, independent reviewer/approver, reason, correlation, idempotency, and
  audit evidence; and
- redactions that exclude tenant codes, secrets, raw provider payloads, and
  unrelated customer evidence.

Calendar versions are global Shared Platform primitives only where their schedules
are genuinely universal. Customer-specific working schedules require explicit
account scope and must not be inferred from jurisdiction alone.

## Schedule Rules

- Working intervals use local wall-clock times in the calendar's IANA timezone.
- Intervals for one day must be ordered, non-overlapping, and have positive
  duration.
- Overnight intervals are represented as two day-bounded intervals; implicit
  cross-midnight ranges are invalid.
- A full-day closure overrides the weekly schedule for that local date.
- An exceptional working interval overrides a closure only when explicitly
  represented and approved.
- A date cannot contain conflicting closure and exceptional schedule evidence.
- Empty weekly schedules, invalid timezone identifiers, overlapping intervals,
  duplicate dates, and ambiguous effective versions fail validation.
- No default weekends, public holidays, or working hours may be invented.

## Timezone And DST Semantics

All persisted clock timestamps remain UTC. Calendar evaluation converts each
candidate instant through the pinned IANA timezone and schedule version.

- A nonexistent local time caused by a forward DST transition advances to the
  first valid instant after the gap.
- An ambiguous repeated local time uses the earlier UTC instant for an interval
  start and the later UTC instant for an interval end, preserving the full approved
  working interval.
- Calculation must remain deterministic for the timezone database version used by
  the runtime. Release evidence records that runtime version.
- Browser locale, browser time, and operator device time are never authoritative.

## Calculation Contract

The shared calculator exposes deterministic operations over one approved calendar
version:

1. `add_working_minutes(started_at, minutes)` returns the first UTC instant after
   exactly that many approved working minutes have elapsed.
2. `working_seconds_between(started_at, ended_at)` returns approved working time
   inside the half-open interval `[started_at, ended_at)`.
3. `is_working_instant(at)` reports whether the instant falls inside an approved
   working interval.

Clock start remains the persisted policy start event, even outside working hours.
Warning and due timestamps advance from that instant through approved working
intervals. Policy-approved pause time remains separate clock evidence and is not
double-counted as working time. Completion compares the persisted completion
instant with the server-calculated due timestamp.

## Resolution And Version Pinning

- Policy creation may reference only an approved calendar version effective for
  the policy window, or defer resolution until policy approval under an explicit
  validated rule.
- Clock start resolves exactly one approved effective calendar version.
- Missing, retired-only, ambiguous, out-of-window, invalid, or timezone-incompatible
  evidence returns `BUSINESS_CALENDAR_UNAVAILABLE` and creates no clock.
- The clock persists the pinned calendar code/version and enough safe calculation
  evidence to explain warning and due timestamps.
- Later calendar versions apply only to clocks started under policies that resolve
  those versions prospectively.

## Administration And Audit

Calendar writes are Amplifi-admin-only until a separate governed delegation model
exists. Creation, review, approval, return-to-draft, and retirement require:

- explicit permission checks;
- independent approval;
- canonical payload hashing and idempotent replay;
- effective-window and overlap validation;
- append-oriented audit evidence with actor, reason, correlation, before/after
  lifecycle state, and safe schedule summary; and
- no mutation of policies, clocks, cases, campaigns, credentials, billing, or money.

## API And UI Boundary

Later tasks may expose a safe administration API and Amplifi Global configuration
surface. The UI should present timezone, weekly hours, closures, exceptions,
effective dates, lifecycle, and impact in plain language. It must preview example
deadline calculations before approval and must not expose internal tenant scope or
calculate authoritative deadlines in the browser.

## Failure And Degraded Behavior

Calendar resolution or calculation failure is fail-closed. The support case remains
usable, but its service-target evidence is `UNAVAILABLE`; no synthetic due date or
percentage is emitted. Existing elapsed-time policies continue independently.

## Ordered Implementation Path

1. Persist immutable calendar versions, weekly intervals, date exceptions, and
   audit evidence.
2. Implement and unit-test the shared timezone-aware calculator.
3. Add governed calendar administration and deterministic resolution.
4. Pin calendar evidence into the existing service-target clock lifecycle.
5. Add safe administration UX and calculation preview.
6. Prove DST boundaries, holidays, exceptions, version changes, isolation,
   idempotency, audit, degraded behavior, and cleanup on PostgreSQL.

## Acceptance Criteria

- Current fail-closed behavior and target behavior are explicitly separated.
- Calendar scope, versioning, weekly schedules, exceptions, timezone/DST rules,
  calculation operations, policy resolution, clock pinning, permissions, audit,
  idempotency, redaction, and degraded behavior are defined.
- No schedule, holiday, deadline, or service-target result is guessed.
- The design extends the existing policy and clock services without source forks.
- Downstream schema, service, API, UI, and release-proof tasks can implement the
  capability without making new architectural decisions.
