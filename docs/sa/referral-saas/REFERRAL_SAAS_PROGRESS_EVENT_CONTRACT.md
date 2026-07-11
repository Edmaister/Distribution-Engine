# Referral SaaS Progress Event Contract

TASK ID: TASK-138

## Boundary

This contract belongs to the Referral Management and Campaign Attribution SaaS
product boundary. It packages the existing shared progress-event primitive for
Referral SaaS without forking event ingestion away from DLaaS.

Required boundary docs checked:

- `docs/product/README.md`
- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/README.md`
- `docs/roadmap/referral-saas/ROADMAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_VALIDATION_RECOVERY_CONTRACT.md`
- `docs/sa/EVENT_INGESTION_PUBLIC_CONTRACT.md`
- `docs/sa/AUDIT_RETRY_POLICY_STANDARD.md`

Source files inspected:

- `apps/api/routers/progress.py`
- `apps/api/schemas/progress.py`
- `services/progress_service.py`
- `services/journey_definitions.py`
- `services/progress_definitions.py`
- `services/journey_orchestrator.py`
- `dp/migrations/013_progress_events.sql`
- `dp/migrations/017_fix_referral_progress_event_type_constraint.sql`
- `dp/migrations/018_add_referral_processing_audit.sql`
- `dp/migrations/019_dedup_update_for_testfile.sql`
- `dp/migrations/020_referral_event_failures.sql`
- `test/test_progress_service.py`
- `test/test_progress_api.py`

## Purpose

Referral SaaS needs a product-ready progress-event contract so tenants can send
journey milestones after referral validation and see safe status updates,
dedupe evidence, and support diagnostics.

This workflow answers:

1. Can this authenticated tenant record a progress event for this referral
   journey?
2. Is the event valid for the referral's journey, product, identity, and
   transition rules?
3. Was the event newly recorded, deduped, rejected, queued, or failed?

This task documents the current source of truth and the product hardening path.
It does not change runtime behavior.

## Current Implementation Facts

Current progress route:

- `POST /v1/progress`
- implemented in `apps/api/routers/progress.py`
- protected by `require_partner_key`
- derives `tenant_code` from authenticated partner identity
- calls `services.progress_service.handle_progress_event`

Current progress request schema:

- `referralTrackId`
- `product`
- `subProduct`
- `eventType`
- `journeyCode`
- `journeyVersion`
- `refereeUCN`
- `accountNumber`
- `meta`
- `sourceSystem`
- `sourceEventId`

Current progress response schema:

- `status`
- `referralTrackId`
- `product`
- `subProduct`
- `eventType`
- `journeyCode`
- `journeyVersion`
- `deduped`
- `message`
- `sourceSystem`
- `sourceEventId`
- `occurredAt`
- `dedupeKey`

Current service behavior:

- normalizes source system, product, sub-product, event type, and journey
- derives a canonical payload hash
- derives `dedupe_key` from `sourceSystem|sourceEventId` when a source event ID
  exists
- derives fallback `dedupe_key` from source system, referral track ID, event
  type, and occurred time when no source event ID exists
- loads `referral_instances` by `referral_track_id` and tenant
- rejects missing referral instances
- validates journey code/version compatibility
- validates event support against journey definitions
- validates required identifiers through `vertical_identifier_service`
- rejects self-referral
- validates product/sub-product binding
- validates referee UCN against stored raw UCN or hash where required
- inserts `referral_progress_events` with payload hash and dedupe key
- returns `201` when newly recorded
- returns `200` with `deduped=true` when the dedupe key already exists
- enqueues `REFERRAL_PROGRESS_RECORDED` only for newly inserted events

## Current Event And Journey Coverage

Current schema enum exposes these progress event names:

- `UCN_CAPTURED`
- `ACCOUNT_OPENED`
- `ACCOUNT_ACTIVATED`
- `FUNDED`
- `DEBIT_ORDER_SWITCHED`
- `SALARY_SWITCHED`
- `FIRST_TRANSACTION_COMPLETED`

Current banking journey definition:

- `BANKING_TRANSACTIONAL:v1`
- core sequence: `VALIDATED`, `UCN_CAPTURED`, `ACCOUNT_OPENED`,
  `ACCOUNT_ACTIVATED`, `FUNDED`
- completion events: `DEBIT_ORDER_SWITCHED`, `SALARY_SWITCHED`,
  `FIRST_TRANSACTION_COMPLETED`

Current code also contains journey/progress definitions and tests for:

- `INSURANCE_POLICY:v1`
- `RETAIL_LOYALTY:v1`

Launch-readiness warning:

- the inspected migration constraint for `referral_progress_events.event_type`
  lists the banking-style event set only
- before productizing non-banking events, live schema and clean DB replay must
  verify that the DB constraint accepts the event names supported by service
  and tests

## Current Persistence And Evidence

Progress events persist in `referral_progress_events` with:

- `referral_track_id`
- `event_type`
- `product`
- `sub_product`
- `source_system`
- `source_event_id`
- `occurred_at`
- `received_at`
- `event_payload_hash`
- `dedupe_key`
- `idempotency_version`
- `meta`

Important schema posture:

- `ux_progress_events_source_event` is unique on `(source_system,
  source_event_id)` when `source_event_id` exists
- `ux_progress_events_dedupe_key` is unique on `dedupe_key`
- `uq_rpe_track_event` was dropped by migration 019, so duplicate handling is
  centered on dedupe/source-event identity rather than one event type per track

Related evidence tables:

- `referral_processing_audit`
- `referral_event_failures`
- `enterprise_event_inbox`

## Orchestration Boundary

Progress ingestion records and queues events. The downstream orchestrator
consumes `REFERRAL_PROGRESS_RECORDED` and updates the referral journey snapshot.

`services.journey_orchestrator.handle_referral_progress_recorded` currently:

- ignores non-progress wrapper events
- ignores upstream-deduped events
- normalizes the progress event type
- loads the referral instance by tenant and track ID
- rejects self-referral
- validates journey transition rules
- classifies duplicate, valid, invalid, backward, and out-of-order transitions
- updates milestone timestamps and progress snapshot fields
- applies mission progress
- can issue base rewards when reward policy and eligibility allow it

Referral SaaS must treat these as shared platform effects. TASK-138 does not
change reward, mission, funding, fulfilment, or attribution behavior.

## Product Outcome States

Recommended Referral SaaS progress ingestion states:

- `RECORDED`
- `DEDUPED`
- `REJECTED_NOT_FOUND`
- `REJECTED_UNSUPPORTED_EVENT`
- `REJECTED_JOURNEY_MISMATCH`
- `REJECTED_IDENTIFIER_REQUIRED`
- `REJECTED_IDENTITY_MISMATCH`
- `REJECTED_SELF_REFERRAL`
- `REJECTED_PRODUCT_MISMATCH`
- `QUEUED`
- `FAILED_TO_QUEUE`
- `FAILED`

Current response mapping:

- `201`, `status=ok`, `deduped=false` maps to `RECORDED`
- `200`, `status=ok`, `deduped=true` maps to `DEDUPED`
- `404`, `Referral instance not found` maps to `REJECTED_NOT_FOUND`
- `400`, unsupported journey/event/identifier/product errors map to rejected
  product states
- `409`, `SELF_REFERRAL_NOT_ALLOWED` maps to `REJECTED_SELF_REFERRAL`

## Target Product Contract Direction

Candidate product route:

```text
POST /referral-saas/events/progress
```

The current `/v1/progress` route can remain the implementation route. A future
product wrapper should delegate to existing progress service behavior instead
of creating a second ingestion path.

Minimum product request:

```json
{
  "referralTrackId": "uuid",
  "eventType": "ACCOUNT_OPENED",
  "sourceSystem": "CORE_BANKING",
  "sourceEventId": "core-evt-123",
  "product": "TRANSACTIONAL",
  "subProduct": "DDA13",
  "journeyCode": "BANKING_TRANSACTIONAL",
  "journeyVersion": "v1",
  "refereeUCN": "sensitive-input",
  "accountNumber": "sensitive-input",
  "meta": {
    "channel": "api"
  }
}
```

Minimum product response:

```json
{
  "progressStatus": "RECORDED",
  "referralTrackId": "uuid",
  "eventType": "ACCOUNT_OPENED",
  "journeyCode": "BANKING_TRANSACTIONAL",
  "journeyVersion": "v1",
  "deduped": false,
  "sourceSystem": "CORE_BANKING",
  "sourceEventId": "core-evt-123",
  "dedupeKey": "sha256...",
  "diagnostics": []
}
```

Product responses must not echo raw `refereeUCN`, raw account number, raw
provider payloads, tokens, secrets, or stack traces.

## Idempotency

Current idempotency posture is strong for event ingestion:

- source event ID gives stable dedupe across retries
- fallback dedupe exists when source event ID is absent
- duplicate progress events return `deduped=true`
- duplicates do not enqueue downstream work

Product requirements:

- public/partner clients should send `sourceSystem` and `sourceEventId`
- fallback dedupe should be treated as weaker diagnostic evidence
- duplicate response should be safe and successful when no conflict exists
- conflicting duplicate payloads require a separate implementation decision and
  tests before product APIs promise conflict semantics

## Retry And Recovery

Retry classes for Referral SaaS progress ingestion:

- validation failures: no retry until payload is corrected
- missing referral track: no automatic retry unless validation evidence is
  expected to arrive later and an operator decides to replay
- duplicate event: no side effect, safe no-op
- unsupported journey/event: no retry until configuration/schema is corrected
- transient queue/dependency failure: bounded retry or operator replay must be
  supported by stored event evidence before product launch
- schema/constraint mismatch: stop and create a follow-up task

Manual replay, repair, or requeue must remain operator/internal until a later
permission and audit contract authorizes product self-service.

## Privacy And Redaction

Progress ingestion may require sensitive evidence, but product-facing responses
and diagnostics must not expose:

- raw UCN values
- raw account numbers
- full provider payloads
- hashes where they allow unnecessary correlation by public users
- secrets, signing material, or credentials

Allowed safe evidence:

- referral track ID
- event type
- source system
- source event ID
- dedupe key
- masked account number when already produced by service code
- safe validation error code/message
- high-level processing status

## Future Tests

Implementation work following this contract should add or preserve tests for:

- tenant is derived from authenticated identity
- body tenant cannot override credential tenant
- successful event returns recorded status and dedupe evidence
- duplicate event returns `deduped=true` and does not enqueue
- missing referral track is tenant-safe and non-leaking
- missing required identifiers are rejected
- self-referral returns a stable conflict code
- product/sub-product mismatch is rejected
- journey mismatch is rejected
- unsupported journey/event is rejected
- sensitive inputs are not echoed in product responses
- queue failure has a recoverable evidence path
- non-banking journey event names match live DB constraints before launch
- referrer progress read model remains tenant-safe

## Implementation Slices

Recommended sequence:

1. Add product response mapping/redaction tests around current `/v1/progress`.
2. Add stable product error codes for current rejection branches.
3. Verify clean DB and live DB constraints for all product-supported event
   names.
4. Add queue-failure evidence and retry/replay diagnostics if missing.
5. Add support-facing progress event diagnostics for operator workflow.
6. Connect progress evidence into attribution trace under TASK-139.

## Explicit Non-Goals

This task does not implement:

- schema migrations
- new routes
- service behavior changes
- frontend changes
- new event names
- enterprise event ingestion changes
- reward, mission, funding, fulfilment, settlement, or sponsor billing changes
- attribution trace composition
- operator repair/replay UI
- reporting/export
- live DB verification

## Readiness Decision

Referral SaaS already has strong progress-event primitives: tenant-scoped
ingestion, source-event dedupe, payload hashing, journey validation, identity
checks, queue emission, and progress read models. The path to 10/10 is to wrap
these primitives in a stable product contract, add redaction and diagnostic
tests, verify event-name/schema alignment, and define operator-safe recovery for
queue or processing failures.
