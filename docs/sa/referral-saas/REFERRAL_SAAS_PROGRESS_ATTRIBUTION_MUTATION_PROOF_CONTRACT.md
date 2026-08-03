# Referral SaaS Progress And Attribution Mutation Proof Contract

Task: TASK-339
Status: Complete
Product boundary: Referral SaaS

## Boundary

This contract belongs to the Referral Management and Campaign Attribution SaaS
product boundary. It defines the proof path that connects campaign/link/code
setup, referral validation, progress-event ingestion, attribution trace, and
customer-scoped reporting.

Required boundary docs checked:

- `AGENTS.md`
- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/referral-saas/ROADMAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_PROGRESS_EVENT_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_ATTRIBUTION_TRACE_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_E2E_LIVE_VERIFICATION_PLAN.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_SELECTED_CUSTOMER_MUTATION_PHYSICAL_VERIFICATION.md`
- `docs/roadmap/ORDERED_TASK_LIST.md`

Source duplication: No.

## Purpose

TASK-271 and TASK-272 proved the selected-customer campaign mutation path up to
campaign activation posture, referral code issue/validation, report preview, and
export preview. The remaining proof gap is deeper: prove that a selected
Referral SaaS customer can record referral journey progress and then read back
the attribution evidence that explains the resulting customer outcome.

The proof runner built from this contract must answer:

1. Can a selected customer execute an allowed referral campaign/link/code setup
   path without leaking internal tenant identifiers?
2. Can the same proof safely ingest progress events through the shared progress
   primitive?
3. Can repeated progress submissions dedupe instead of creating duplicate
   journey evidence?
4. Can attribution trace and customer-scoped reports read back the campaign,
   link/code, progress-event, and outcome evidence?
5. Can the proof prove that no provider, credential, auth, invite, billing,
   money, DLaaS marketplace, repair, replay, or source-fork side effect
   occurred?

This task defines the contract only. It does not implement the proof runner or
execute it.

## Selected-Customer Scope

The proof must start from an explicit selected customer:

- `external_tenant_ref`
- optional `organisation_ref`
- selected `account_ref`
- customer-facing account name
- operating jurisdiction

The runner must resolve the customer through Referral SaaS account wrappers and
use customer-scoped routes for campaign, link/code, reports, support evidence,
and account context wherever those wrappers exist.

The proof must fail if any response exposes:

- `tenant_code`
- internal tenant/account link internals not already approved for the selected
  customer surface
- raw UCN
- raw identity hashes
- provider secrets
- credential material
- bearer tokens
- cross-customer evidence

## Deterministic Proof Identity

The runner must generate or accept a deterministic proof suffix and use it in:

- campaign name
- campaign code or campaign setup reference when supported
- source system
- source event IDs
- idempotency keys
- operator/audit notes
- safe evidence labels

Recommended suffix shape:

```text
task-339-progress-attribution-proof-<timestamp-or-user-supplied-suffix>
```

The proof must be repeatable with a user-supplied suffix. Reusing the same
suffix with the same payload must replay safely. Reusing the same idempotency
key with different content must return a conflict rather than mutating a second
path silently.

## Required Proof Path

The TASK-340 runner must perform the following path in order.

| Step | Action | Required evidence |
| --- | --- | --- |
| 1 | Resolve selected customer | Account exists, account scope is selected-customer safe, no internal tenant leak. |
| 2 | Prepare campaign/link/code evidence | Use existing selected-customer campaign setup/link-code wrappers or a controlled existing active campaign if the environment already provides one. |
| 3 | Issue or reuse referral code | Referral code/link evidence is tenant-safe and connected to the selected customer/campaign proof. |
| 4 | Validate referral entry | Validation creates or resolves a referral track ID for the proof path. |
| 5 | Record first progress event | `POST /v1/progress` records a supported journey event with source-system and source-event proof identity. |
| 6 | Replay first progress event | Same progress payload/source event dedupes and does not enqueue duplicate journey work. |
| 7 | Record later progress event | A valid next milestone is recorded when the journey and identifiers allow it. |
| 8 | Read attribution trace | Trace includes safe outcome, link/code, campaign attribution, progress-event, missing-evidence, warning, redaction, and audit posture. |
| 9 | Read customer reports | Campaign/performance/progress/attribution report wrappers reflect the proof evidence or explicitly return a safe partial-source warning. |
| 10 | Confirm no adjacent effects | No provider/webhook dispatch, credential creation, invitation delivery, auth claim propagation, repair/replay execution, billing, money movement, export delivery job, or DLaaS marketplace mutation. |

## Allowed Writes

The proof may create or update only the following bounded Referral SaaS evidence:

- inactive or proof-scoped campaign setup evidence through existing guarded
  campaign wrappers
- campaign policy/review/activation posture when required by existing selected
  customer campaign setup proof rules
- referral code/link issue or reuse evidence
- referral validation/referral instance evidence
- `referral_progress_events`
- progress-related audit/failure evidence produced by the shared progress
  primitive
- existing safe account-audit/proof metadata emitted by the selected-customer
  wrappers

## Required Readbacks

The runner must verify readback from at least these surfaces:

- selected customer/account resolution
- referral validation response
- progress ingestion response
- progress idempotency/dedupe response
- attribution trace response
- customer-scoped report response

If an environment cannot produce a complete attribution trace because a source
join is intentionally absent, the proof may pass only when the trace returns a
known safe partial state with missing-evidence codes and redactions. A silent
empty trace or cross-customer fallback is a failure.

## Progress Event Requirements

Progress ingestion must use the existing shared progress event primitive. The
proof must not add a Referral SaaS-only progress table or alternate ingestion
route.

Minimum progress payload requirements:

- referral track ID from the validation path
- product/sub-product supported by the selected customer proof path
- supported journey code/version
- supported event type
- required identity fields for the journey
- source system containing the proof suffix
- source event ID containing the proof suffix
- metadata that is safe to log and safe to expose in sanitized proof evidence

Expected states:

- first valid event: recorded
- identical replay: deduped
- unsupported event or invalid journey: controlled rejected state if tested
- missing referral track: controlled not-found state if tested

The runner must fail if duplicate submission creates duplicate progress rows for
the same dedupe/source identity.

## Attribution Requirements

Attribution trace proof must connect as much of the following evidence as the
current implementation can safely provide:

- referral track ID
- campaign or campaign attribution evidence
- referral code/link evidence
- progress events
- participant-safe evidence
- audit/correlation evidence
- missing-evidence and warning evidence
- redactions

Trace completeness may be `COMPLETE` or an explicitly explained partial state.
The runner must not treat `UNAVAILABLE`, cross-tenant missing data, or unredacted
internal evidence as success.

## Report Requirements

Report readback must check that customer-scoped reports stay inside the selected
customer context and either:

- include the proof campaign/progress/attribution evidence, or
- return a safe partial-source warning explaining why the proof evidence is not
  yet reflected in the selected report source.

The proof must not create persisted export files, scheduled deliveries, signed
URLs, storage objects, billing records, or money movement unless a later
explicit task approves that scope.

## No-Adjacent-Action Guardrails

The proof must explicitly confirm no side effects in these domains:

- no live provider call
- no webhook dispatch
- no invite delivery
- no credential creation
- no bearer token or secret generation
- no auth-claim propagation
- no login activation
- no seat assignment unless the proof explicitly calls a separate governed
  People and Access provisioning task
- no support repair/replay/retry execution
- no export delivery job
- no billing, invoice, wallet, funding, fulfilment, settlement, commission,
  payout, or money movement
- no DLaaS marketplace, distributor, sponsor, treasury, or settlement workflow
- no source duplication or product fork

## Failure Handling

The runner must report failures with enough safe evidence to tell whether the
failure is:

- environment not ready
- selected customer not active
- campaign/link/code prerequisite missing
- referral validation failed
- progress event rejected
- progress dedupe mismatch
- attribution trace missing/partial
- report readback lagging or unsupported
- tenant-scope/redaction violation
- adjacent side effect detected

Controlled environment-not-ready states should be explicit. They must not be
reported as product success.

## Rollback And Cleanup Posture

The proof path should prefer uniquely suffixed test evidence over destructive
cleanup. Runtime cleanup is not required for TASK-340 unless the runner adds a
safe dry-run cleanup report.

Rollback posture:

- revert proof-runner code/docs if the implementation is wrong
- do not delete customer, campaign, referral, progress, or audit rows without a
  separately reviewed cleanup task
- keep proof evidence tenant-safe and sanitized

## TASK-340 Runner Acceptance Checklist

The TASK-340 runner is ready when it can:

- run from CLI against local or staging API base URL
- accept admin key, selected customer refs, and optional suffix
- create or reuse proof-scoped campaign/link/code evidence
- validate a referral entry and capture referral track ID
- record and replay progress events
- read attribution trace and customer-scoped report evidence
- fail on tenant-scope leaks
- fail on duplicate progress mutation instead of dedupe
- fail on adjacent provider/auth/billing/money/DLaaS side effects
- emit a sanitized JSON proof result
- include focused tests for payload construction, idempotency key handling,
  redaction checks, controlled partial states, and no-side-effect assertions

## TASK-341 Execution Evidence Checklist

The TASK-341 evidence document is ready when it records:

- environment and command
- selected customer
- proof suffix
- campaign/link/code identifiers
- referral track ID
- progress event statuses and dedupe status
- attribution trace status and missing-evidence posture
- report readback status
- no-internal-leak result
- no-adjacent-action confirmations
- final pass/fail or controlled-blocked outcome

## TASK-340 Implementation

TASK-340 adds `scripts/referral_saas_progress_attribution_physical_check.py`.
The runner reuses the existing selected-customer mutation proof for campaign
setup, policy/review/activation posture, referral code issue, and referral
validation. It then captures the validation `referralTrackId`, posts the first
`UCN_CAPTURED` progress event, replays the same event expecting dedupe, posts a
later `ACCOUNT_OPENED` milestone, reads operator progress status, reads
attribution trace, and reads the selected customer's campaign-performance
report.

The runner remains a proof tool only. It does not add a Referral SaaS-specific
progress route, schema, table, or fork. It fails on unsafe secret/adjacent
payload fields, duplicate progress mutation instead of dedupe, missing referral
track ID, unavailable trace state, and missing customer-scoped report readback.
TASK-341 must still execute this runner against approved local/staging data and
record sanitized evidence.

## Launch Rating Impact

TASK-339 closes ambiguity in the progress/attribution proof design and TASK-340
adds the repeatable runner. Current rating remains:

- Referral Management: 9.99/10
- Campaign Attribution: 9.999/10

Campaign Attribution should only move to 10/10 after TASK-341 records
successful execution evidence, subject to non-local proof and remaining
provider/auth governance gates.
