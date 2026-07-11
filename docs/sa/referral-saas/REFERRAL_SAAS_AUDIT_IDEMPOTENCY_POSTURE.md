# Referral SaaS Audit And Idempotency Posture Inventory

TASK ID: TASK-146

Product boundary: Referral Management and Campaign Attribution SaaS.

Status: Inventory only. No runtime behavior, schema, route, permission,
frontend, audit write, idempotency behavior, retry behavior, repair/replay
action, or test changes are made by this task.

## Boundary

This inventory records the current audit, idempotency, retry, duplicate, and
failure posture for the Referral SaaS product wedge. It uses existing database
schema and service-layer code as source truth and does not create new platform
policy beyond `docs/sa/AUDIT_RETRY_POLICY_STANDARD.md`.

Required boundary docs checked:

- `docs/product/README.md`
- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/README.md`
- `docs/roadmap/referral-saas/ROADMAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_REFERRAL_CODE_ISSUE_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_VALIDATION_RECOVERY_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_PROGRESS_EVENT_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_SUPPORT_WORKFLOW.md`
- `docs/sa/AUDIT_RETRY_POLICY_STANDARD.md`

Source files inspected:

- `apps/api/routers/referrals.py`
- `apps/api/routers/progress.py`
- `apps/api/routers/campaigns.py`
- `apps/api/routers/admin_onboarding.py`
- `services/referral_code.py`
- `services/progress_service.py`
- `services/campaign_readiness_service.py`
- `services/admin_audit_service.py`
- `services/failure_admin_service.py`
- `services/onboarding/onboarding_draft_idempotency_service.py`
- `services/onboarding/onboarding_draft_audit_evidence_service.py`
- `dp/migrations/001_init.sql`
- `dp/migrations/006_qr_scans.sql`
- `dp/migrations/013_progress_events.sql`
- `dp/migrations/018_add_referral_processing_audit.sql`
- `dp/migrations/020_referral_event_failures.sql`
- `dp/migrations/061_enterprise_event_inbox.sql`
- `dp/migrations/071_admin_audit_log.sql`
- `dp/migrations/080_onboarding_draft_persistence.sql`

## Purpose

Referral SaaS can only be production-grade if duplicate requests, retries,
manual support actions, and sensitive changes are traceable and safe.

This inventory answers:

1. Which Referral SaaS flows already have concrete idempotency or duplicate
   protection?
2. Which flows already produce audit or trace evidence?
3. Which repair/replay paths exist but need stronger audit/idempotency wrapping
   before product exposure?
4. Which gaps should block implementation from calling the product 10/10?

## Current Posture Summary

| Area | Current posture | SaaS readiness |
|---|---|---|
| Account/onboarding draft setup | Strong idempotency and safe audit-link evidence exist for draft save and submit-for-review. | Good foundation; product wrapper still needed. |
| Referral code issue/reuse | Get-or-create behavior and database uniqueness exist. | Good duplicate posture; audit/event evidence is not yet a full product command audit. |
| Public referral validation | Creates a new referral instance and QR scan evidence for each successful validation. | Trace evidence exists; idempotency for duplicate validation is not yet formalized. |
| Referee UCN capture | Updates referral instance and emits deterministic progress event source ID. | Useful posture; update itself is not idempotency-keyed. |
| Progress ingestion | Strong dedupe key, source event uniqueness, payload hash, and duplicate no-op behavior exist. | Strongest current idempotency foundation. |
| Campaign setup/policy | Campaign code/ID uniqueness and policy upsert conflict handling exist. | Needs product command idempotency and audit before product route exposure. |
| Campaign readiness | Read-only, side-effect free diagnostic. | Good read posture. |
| Link/code inspection | Read-only, redacted diagnostic. | Good read posture. |
| Attribution trace | Read-only, redacted diagnostic. | Good read posture. |
| Reporting | Read-only tenant-safe analytics guardrail. | Good read posture; exports need future audit/idempotency. |
| Operator failure support | Failure rows, resolve, reprocess, DLQ replay, and referral replay exist. | Useful internal primitives; product exposure needs stronger audit, reason, idempotency, and permission contracts. |

## Flow Inventory

### Account Setup And Onboarding Drafts

Current facts:

- `evaluate_draft_idempotency` requires an idempotency key, actor reference,
  external tenant reference, operation type, and request hash.
- Same key and same payload returns `REPLAY_SAME_PAYLOAD`.
- Same key with different payload returns `CONFLICT_DIFFERENT_PAYLOAD`.
- `onboarding_draft_idempotency_keys` has a unique constraint on
  `(idempotency_key_hash, scope_hash)`.
- Draft save and submit-for-review build safe audit evidence with before/after
  state hashes, changed sections, correlation ID, redactions, and
  `no_live_action_confirmed`.
- Onboarding dry-run validation explicitly returns `NO_AUDIT_WRITE`,
  `NO_EVENT_PERSISTENCE`, and `NO_EVENT_DISPATCH` guardrails.

Current gaps:

- Audit evidence is stored as onboarding audit-link evidence, not necessarily
  a canonical `admin_audit_log` entry for every product operation.
- Product account membership and SaaS account wrappers are still future work.

Future requirement:

- Product account setup commands should preserve existing draft idempotency and
  audit evidence rather than creating a parallel setup command path.

### Referral Code Issue And Reuse

Current facts:

- `get_or_create_referrer_code` checks for an existing row by tenant, sticker,
  and `referrer_ucn_hash`.
- Existing code reuse returns `created=false` and HTTP 200.
- New issue returns `created=true` and HTTP 201.
- `referrer_codes` has uniqueness on `referrer_ucn_hash`, `referral_code`, and
  `gaming_handle`.
- Accepted terms are required before issuing or reusing the code.

Current gaps:

- There is no caller-supplied idempotency key for `POST /referrals/codes`.
- The schema uniqueness on `referrer_ucn_hash` is global, while service lookup
  uses tenant/sticker/referrer hash.
- There is no canonical admin audit row for referral code issue/reuse in the
  inspected service path.

Future requirement:

- Product API wrappers should define whether get-or-create is sufficient or
  whether an idempotency key is required for code issue.
- Audit evidence should capture actor/client, tenant/account, referrer safe
  identity, created/reused outcome, and terms acceptance evidence without
  exposing raw UCNs.

### Public Referral Validation

Current facts:

- `validate_referral_code` validates tenant, code, accepted terms, and alias.
- Successful validation creates a new `referral_instances` row with a new
  `referral_track_id`.
- Successful validation writes `referral_qr_scans` evidence.
- Failure paths return safe error codes for missing tenant/code, terms, alias,
  and code-not-found cases.
- If instance or scan logging fails after code lookup, the response returns a
  recovery-style success/failure mix with `REFERRAL_LOG_FAILED`.

Current gaps:

- No idempotency key or duplicate validation contract exists for repeated
  public validation attempts.
- No unique business key prevents the same referee/alias/device from creating
  repeated validation rows when the caller retries.
- Validation evidence is not yet written as a canonical audit event.

Future requirement:

- Before product launch, public validation needs a duplicate/retry posture:
  return existing referral, reject duplicate, or create multiple attempts with
  explicit evidence.
- Recovery paths must have support diagnostics without leaking raw UCN, device,
  IP, QR payload, or tenant internals.

### Referee UCN Capture

Current facts:

- `capture_referee_ucn` validates referral track, tenant, and active tenant
  state.
- It updates `referral_instances.referee_ucn` and `referee_ucn_hash`.
- It emits a progress event with deterministic source event ID
  `ucn-captured:{referral_track_id}`.
- Progress event dedupe handles repeated downstream event recording.

Current gaps:

- The referral instance update is not protected by a caller idempotency key.
- The update overwrites the referee UCN/hash if called again for the same
  track, subject to route validation.
- No canonical admin audit row is written for UCN capture in the inspected
  service path.

Future requirement:

- Product wrappers should define whether repeated UCN capture with the same
  identity is a safe no-op and whether a different identity must be rejected as
  conflict.

### Progress Event Ingestion

Current facts:

- `handle_progress_event` derives tenant from authenticated partner identity
  via the API route.
- The service derives a canonical payload hash.
- The service derives a `dedupe_key` from `sourceSystem|sourceEventId` when a
  source event ID is present.
- Fallback dedupe uses source system, referral track ID, event type, and
  occurred time when no source event ID exists.
- `referral_progress_events` has unique indexes for source event identity and
  dedupe key.
- Insert uses `ON CONFLICT (dedupe_key) DO NOTHING`.
- Duplicates return `deduped=true` and do not enqueue downstream work.
- New events enqueue `REFERRAL_PROGRESS_RECORDED`.
- Event payload stores lookup hashes for sensitive identifiers rather than
  using raw values as the canonical dedupe evidence.

Current gaps:

- Conflicting duplicate payload behavior is not explicitly surfaced as a
  product conflict; dedupe key wins.
- Queue failure evidence and retry/replay class need product hardening before
  launch.
- Non-banking event names still require DB constraint verification before being
  promised as product-supported.

Future requirement:

- Product progress APIs should require `sourceSystem` and `sourceEventId`.
- Duplicate same-payload and duplicate different-payload behavior should be
  contract-tested.
- Queue/retry failure paths need operator-visible evidence and safe product
  status.

### Campaign Setup, Policy, And Readiness

Current facts:

- Campaign identity is guarded by `marketing_campaigns.campaign_code` primary
  key and `campaign_id` uniqueness.
- Campaign policy upsert uses `ON CONFLICT (campaign_code, tenant_code,
  version) DO UPDATE`.
- Campaign readiness is read-only and side-effect free.
- Campaign readiness returns blockers, warnings, unknowns, safe evidence, and
  evaluated timestamp.

Current gaps:

- Campaign create has no product command idempotency key in the inspected route.
- Policy upsert is duplicate-safe by version but lacks a product command
  idempotency/audit contract.
- Campaign activation/publish commands remain outside first-launch contract.

Future requirement:

- Product campaign setup mutations should require idempotency keys and audit
  evidence before claiming production SaaS readiness.
- Readiness reads should stay side-effect free.

### Link/Code Inspection, Attribution Trace, Safe Status, And Reporting Reads

Current facts:

- Link/code inspection, outcome trace, campaign readiness, and tenant-safe
  analytics are read-only diagnostics in the current routes.
- These routes include guardrails that state no mutations occur.
- Outcome trace and link/code inspection include redaction and missing-evidence
  concepts.
- Tenant-safe analytics rejects unsupported reports/dimensions through service
  validation and returns freshness/source warning concepts.

Current gaps:

- Product account/member wrappers are not implemented for these reads.
- Dedicated Referral SaaS support/reporting UI is not implemented.
- Export APIs are not implemented and therefore have no export audit or
  idempotency posture yet.

Future requirement:

- Reads remain side-effect free and authorized.
- Export creation, scheduled delivery, or persisted report files must add
  audit, idempotency, retention, expiry, and access-control tests before launch.

### Operator Failures, Reprocess, And Replay

Current facts:

- `referral_event_failures` stores failure ID, referral track ID, event type,
  source system, source event ID, dedupe key, failure category, failure reason,
  status, retry count, payload JSON, failure timestamps, resolved timestamp,
  and resolution note.
- `resolve_failure` only updates rows not already `RESOLVED` or `REPROCESSED`.
- `reprocess_failure` rejects missing, already closed, empty payload, invalid
  JSON, and unsupported event types.
- Reprocess only supports `REFERRAL_PROGRESS_RECORDED`.
- `mark_failure_reprocessed` prevents repeated `REPROCESSED` updates.
- DLQ replay and referral replay services exist.
- Referral replay supports `dry_run=true` and non-dry-run mutation.

Current gaps:

- Failure resolve/reprocess use logging evidence, not full canonical
  `admin_audit_log` actor/reason/before/after records in the inspected service.
- Reprocess does not require a caller-supplied idempotency key.
- DLQ replay and non-dry-run referral replay should not be exposed as product
  support actions until role, audit, reason, correlation, and idempotency are
  hardened.

Future requirement:

- Any product repair/replay action must require actor, role, tenant, target,
  reason, correlation reference, before/after state, and idempotency or clear
  duplicate rejection.

## Launch-Critical Gaps

These gaps should block a 10/10 production claim until implemented and tested:

1. Public validation duplicate/idempotency behavior is not formalized.
2. Referral code issue/reuse does not yet have product command audit evidence.
3. Campaign create/policy mutations do not yet have product idempotency and
   audit contracts.
4. Failure resolve/reprocess and replay paths need canonical audit, reason,
   actor, before/after, and idempotency posture before product exposure.
5. Export creation/storage/delivery does not exist and therefore has no audit
   or idempotency posture.
6. Product wrappers must consistently derive tenant/account scope from auth or
   safe account context instead of caller-supplied internal tenant codes.
7. Live DB/state verification must confirm the launch-critical constraints,
   indexes, and statuses before production readiness is claimed.

## Future Tests

When implementation starts, add or preserve tests for:

- same idempotency key and same account setup payload returns replay
- same idempotency key and different account setup payload returns conflict
- referral code issue duplicate returns existing code without creating a second
  code
- referral code issue writes product-safe audit evidence when product wrapper
  exists
- public validation duplicate/retry behavior follows the chosen contract
- progress same source event is deduped and does not enqueue downstream work
- progress duplicate different payload is either rejected or explicitly
  reported according to the final product contract
- campaign create/policy mutations require idempotency and audit in product
  wrappers
- failure resolve/reprocess requires actor, reason, correlation, and audit
  evidence before product exposure
- replay and repair commands are absent or disabled in ordinary support UI
- no raw UCN, account number, provider payload, audit payload, DLQ payload,
  secret, token, funding, settlement, commission, wallet, invoice, or payout
  leakage

## Explicit Non-Goals

- no schema, migration, service, route, permission, frontend, audit write,
  idempotency behavior, retry behavior, repair/replay behavior, export, live DB,
  or test implementation
- no new status enums, API fields, database fields, or product routes
- no public API wrapper implementation
- no support-case table or queue
- no funding, fulfilment, settlement, commission, wallet, invoice, payout,
  sponsor billing, marketplace-depth, white-label/embed, or SaaS billing work

## Readiness Decision

Referral SaaS has strong foundations for progress-event idempotency and
onboarding draft idempotency, plus useful read-only diagnostics and failure
evidence. It does not yet have complete audit/idempotency coverage for every
first-launch product command. TASK-146 records the current source-backed
posture and the implementation gaps that must be closed before claiming a
10/10 production SaaS capability.
