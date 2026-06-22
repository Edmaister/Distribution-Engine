# Event Ingestion Public Contract

Status: Accepted for TASK-012 on 2026-06-22.

## Purpose

TASK-012 defines the stable DLaaS event ingestion contract over the current progress and enterprise-event ingestion paths.

This is a contract document only. It does not add a new endpoint, change authentication, change migrations, rename fields, alter event processing, create a webhook event catalog, or modify reward, funding, fulfilment, settlement, audit, tenant, privacy, or retry behavior.

## Source Documents And Code

- `docs/product/DLAAS_TARGET_STATE.md`
- `docs/sa/AUDIT_RETRY_POLICY_STANDARD.md`
- `docs/sa/OUTCOME_TRACE_RESPONSE_CONTRACT.md`
- `docs/sa/API_SURFACE_MAP.md`
- `docs/sa/CURRENT_STATE_MAP.md`
- `docs/sa/CAPABILITY_GAP_MATRIX.md`
- `docs/sa/STATE_MACHINE_MAP.md`
- `apps/api/routers/progress.py`
- `apps/api/routers/enterprise_events.py`
- `apps/api/routers/admin_enterprise_events.py`
- `apps/api/schemas/progress.py`
- `apps/api/schemas/enterprise_events.py`
- `apps/Workers/ids_consumer.py`
- `services/progress_service.py`
- `services/enterprise_event_inbox_service.py`
- `dp/migrations/013_progress_events.sql`
- `dp/migrations/061_enterprise_event_inbox.sql`
- `test/test_progress_service.py`
- `test/test_worker_ids_consumer.py`
- `test/test_enterprise_event_inbox_admin.py`

## Current Ingestion Surfaces

| Surface | Current route | Current auth | Current owner | Current source truth |
| --- | --- | --- | --- | --- |
| Progress ingestion | `POST /v1/progress` | Partner key | `apps/api/routers/progress.py` -> `services/progress_service.py` | `referral_progress_events`; queued `REFERRAL_PROGRESS_RECORDED` payload |
| Enterprise ingestion | `POST /enterprise/events` | Admin or partner key | `apps/api/routers/enterprise_events.py` -> `apps/Workers/ids_consumer.py` | `enterprise_event_inbox`; optional normalized progress payload |
| Enterprise diagnostics | `GET /admin/enterprise-events*` | System admin key | `apps/api/routers/admin_enterprise_events.py` -> `services/enterprise_event_inbox_service.py` | `enterprise_event_inbox` |
| Enterprise replay | `POST /admin/enterprise-events/{inbox_event_id}/replay` | System admin key | `apps/api/routers/admin_enterprise_events.py` -> `services/enterprise_event_inbox_service.py` | Requeues stored `normalized_payload` when replayable |

The public DLaaS event contract should wrap these current facts before any new route family is implemented. The target public API may be versioned later, but its behavior must stay compatible with the source-of-truth semantics below.

## Contract Summary

Recommended future public route family:

```text
POST /v1/events
GET /v1/events/{event_ref}
GET /v1/events?filters...
```

Recommended first implementation approach:

```text
ingest_event(
  *,
  tenant_code: str,
  source_system: str,
  source_event_id: str | None,
  event_type: str,
  referral_track_id: str | None,
  correlation_id: str | None,
  occurred_at: datetime | None,
  payload: dict,
  identity: dict,
) -> EventIngestionResult
```

The first public route should resolve `tenant_code` from authenticated identity or an approved external tenant boundary. It must not trust a request body `tenantCode` over authenticated tenant scope for partner/public callers.

## Request Contract

Canonical public request fields:

| Field | Required | Meaning | Current mapping |
| --- | --- | --- | --- |
| `eventType` | Yes | Source event type or platform progress event type. | `ProgressPostRequest.eventType`; `EnterpriseEventIngestRequest.eventType` |
| `sourceSystem` | Recommended | External system name. Defaults exist today but public clients should send it. | `source_system`; normalized uppercase |
| `sourceEventId` | Recommended | Upstream idempotency/event identity. | `source_event_id`; used in dedupe key when present |
| `referralTrackId` | Conditional | Current golden thread for outcome progress. | `referral_track_id` |
| `correlationId` | Recommended | Cross-system trace reference. | `enterprise_event_inbox.correlation_id`; defaults to referral track ID in enterprise worker when absent |
| `occurredAt` | Recommended | Source event occurrence time. | Defaults to current time in current workers when absent or invalid |
| `journeyCode` | Optional | Journey/ruleset hint. | Validated against journey definitions when supplied |
| `journeyVersion` | Optional | Journey/ruleset version. | Defaults to `v1` in current enterprise worker |
| `product` | Conditional | Product family for progress events that require it. | Normalized by progress service |
| `subProduct` | Conditional | Product variant for progress events that require it. | Normalized by progress service |
| `refereeUCN` | Conditional and sensitive | Customer identity used by current progress validation. | Converted to lookup/hash evidence in queued payload |
| `accountNumber` | Conditional and sensitive | Account evidence for selected banking events. | Converted to lookup/masked/hash evidence in queued payload |
| `meta` or extra fields | Optional | Source-specific evidence. | Stored in progress `meta` or enterprise raw payload |

Sensitive input values such as raw UCN, account numbers, provider payloads, tokens, secrets, and signing material must not be echoed in public diagnostic responses. Where current processing needs them, downstream evidence should use lookup keys, hashes, masks, or redacted flags.

## Auth And Tenant Scope

Current facts:

- `POST /v1/progress` requires `require_partner_key`.
- `POST /enterprise/events` requires `require_admin_or_partner_key`.
- `POST /enterprise/events` sets `tenantCode` from authenticated identity when the identity has a non-`INTERNAL` tenant.
- Admin diagnostics and replay require system admin auth.

Target contract:

| Caller | Tenant derivation | Allowed ingestion |
| --- | --- | --- |
| Partner/API client | Tenant must come from credential or external identifier mapped to internal `tenant_code`. Body `tenantCode` cannot expand scope. | Tenant-scoped events only |
| Internal/system admin | May submit explicit tenant when acting as trusted internal source. | Tenant-scoped or controlled internal events |
| Worker/replay | Must use stored event tenant and normalized payload evidence. | Replay of previously accepted inbox event only |

Unauthorized requests return `401`. Authenticated callers without tenant/source scope return `403`. Tenant mismatches must not leak whether another tenant's event or referral exists.

## Idempotency Contract

Current source truth:

- `referral_progress_events.dedupe_key` is unique.
- `referral_progress_events` also has a partial unique index on `(source_system, source_event_id)` when `source_event_id` is present.
- `enterprise_event_inbox.dedupe_key` is unique.
- Enterprise dedupe key is `sha256(source_system|source_event_id)` when a source event ID exists, otherwise `sha256(source_system|payload_hash)`.
- Progress dedupe key is `sha256(source_system|source_event_id)` when a source event ID exists, otherwise `sha256(source_system|referral_track_id|event_type|occurred_at)`.

Target rule:

- Public clients should provide `sourceSystem` and `sourceEventId` for stable idempotency.
- The platform may derive a fallback dedupe key when source event ID is absent, but fallback keys are less stable and should be surfaced as diagnostic evidence.
- Duplicate events must not enqueue duplicate downstream work or create duplicate reward, commission, funding, fulfilment, settlement, or webhook side effects.
- Duplicate handling must return a successful no-op style result when the prior event is already accepted, queued, ignored, or duplicate-safe.

## Processing Outcomes

| Outcome | HTTP guidance | Current source status | Meaning |
| --- | --- | --- | --- |
| `accepted` | `202` preferred for future public route; current progress uses `201` | `QUEUED` or inserted progress row | Event accepted and queued or recorded for processing |
| `recorded` | `201` for current progress route | Progress row inserted | Progress event recorded and downstream event queued |
| `duplicate` | `200` preferred; `409` only for unsafe conflicts | `DUPLICATE` or progress `deduped=true` | Dedupe guard found prior event; no new side effects |
| `ignored` | `202` or `200` with diagnostics | `IGNORED` | Event was stored but did not qualify for progress routing |
| `invalid` | `400` or `422` | No accepted source row required | Payload shape, unsupported event, journey mismatch, or missing required evidence |
| `conflict` | `409` | Current progress self-referral conflict | Valid request shape but unsafe business conflict |
| `failed` | `500` for unexpected failure; stored as `FAILED` when accepted first | `FAILED` | Accepted source could not be queued or processed due to dependency/system failure |
| `replayable` | `200` on admin dry run | Existing inbox row | Stored normalized payload can be requeued |
| `replayed` | `202` or `200` | `QUEUED` after admin replay | Previously accepted event was requeued |

Future public responses should use one envelope, even where current routes have route-specific bodies.

## Response Contract

Recommended future public response:

```json
{
  "status": "accepted",
  "processingStatus": "QUEUED",
  "eventType": "ACCOUNT_ACTIVATED",
  "progressEventType": "ACCOUNT_ACTIVATED",
  "tenantRef": "resolved-or-redacted-external-ref",
  "referralTrackId": "11111111-1111-4111-8111-111111111111",
  "correlationId": "corr-123",
  "sourceSystem": "HOGAN",
  "sourceEventId": "ids-123",
  "dedupeKey": "sha256...",
  "queued": true,
  "diagnostics": [],
  "links": {
    "outcomeTrace": null
  }
}
```

Public diagnostics should include safe codes and source references, not raw payloads:

```json
{
  "code": "EVENT_IGNORED",
  "severity": "INFO",
  "message": "Event was stored but is not eligible for referral progress routing.",
  "source": "enterprise_event_inbox",
  "nextVerification": "Check event type, journey, referralTrackId, and required identifiers."
}
```

## Error Shape

Recommended future public error envelope:

```json
{
  "error": {
    "code": "EVENT_VALIDATION_FAILED",
    "message": "eventType is required.",
    "correlationId": "request-correlation-id",
    "details": []
  }
}
```

| HTTP status | Use |
| --- | --- |
| `400` | Valid JSON but invalid event semantics, unsupported journey, missing required source evidence, product/sub-product mismatch, or invalid timestamp handling if strict parsing is enabled. |
| `401` | Missing or invalid credentials. |
| `403` | Authenticated caller lacks tenant, source-system, or route scope. |
| `404` | Diagnostic lookup or replay target not found or inaccessible. Public ingestion should avoid revealing cross-tenant referral existence. |
| `409` | Unsafe business conflict such as self-referral or tenant/source conflict. Do not use `409` for ordinary duplicate no-op results unless the duplicate payload conflicts with a prior accepted event. |
| `422` | Request model/schema validation failure. |
| `500` | Unexpected system failure after safe logging. Response must not expose secrets, raw payloads, stack traces, or internal config details. |

## Event Validation Rules

Current validation that future public routes must preserve or wrap safely:

- `eventType` is required.
- Progress `referralTrackId` is required.
- Product-specific banking progress events require `product` and `subProduct`.
- `UCN_CAPTURED` requires `refereeUCN`.
- `ACCOUNT_OPENED` requires `refereeUCN` and `accountNumber`.
- Product events requiring identity reject missing or mismatched `refereeUCN`.
- Self-referral is rejected with a conflict.
- Explicit `journeyCode` and `journeyVersion` must match the referral's current journey when already bound.
- Unsupported event types for a journey are rejected.
- Enterprise events without tenant or without eligible progress routing are stored as `IGNORED`, not forced through progress processing.

These are current facts, not a full future event catalog. A later webhook/event-catalog task must define broader event families before public documentation promises additional event names.

## Queueing, Retry, Replay, And Diagnostics

Current facts:

- Progress ingestion inserts `referral_progress_events` and queues `REFERRAL_PROGRESS_RECORDED` only when the progress row is newly inserted.
- Duplicate progress events return `deduped=true` and do not enqueue.
- Enterprise ingestion inserts `enterprise_event_inbox`, stores raw payload, stores normalized payload when eligible, and queues only qualifying normalized progress events.
- Enterprise enqueue failure updates the inbox row to `FAILED` and returns an API-level failure through the router.
- Admin replay can dry-run replayability or requeue stored `normalized_payload`, then marks processing status `QUEUED`.
- Admin replay writes admin audit evidence through `try_write_admin_audit`.

Target public contract:

- Read-only diagnostics may expose processing status, dedupe evidence, safe error summaries, and outcome trace linkage when available.
- Replay, repair, requeue, or manual override must remain admin/internal until separate permission and audit contracts authorize public self-service.
- Replayed events must reference the original stored event and preserve correlation/dedupe evidence.
- Failed events must distinguish validation failures, ignored non-qualifying events, duplicate no-ops, and system/queue failures.

## Relationship To Outcome Trace

The outcome trace contract from TASK-010 and implementation from TASK-011 consume event evidence from:

- `referral_progress_events`
- `enterprise_event_inbox`
- `referral_processing_audit`

Event ingestion responses should include `referralTrackId`, `correlationId`, `sourceSystem`, `sourceEventId`, and `dedupeKey` where available so later diagnostics can link to the outcome trace without exposing raw sensitive payloads.

When an event cannot be linked to an outcome, diagnostics should use missing-evidence style language such as:

- `OUTCOME_NOT_FOUND`
- `NO_SOURCE_EVIDENCE`
- `JOIN_AMBIGUOUS`
- `SOURCE_UNAVAILABLE`

## Privacy And Redaction

Public ingestion and diagnostics must not return:

- raw UCN values;
- raw account numbers;
- provider response payloads;
- webhook signing material;
- API keys, tokens, or secrets;
- unrestricted raw `raw_payload`;
- stack traces or internal config details.

Allowed safe evidence includes:

- masked account numbers;
- one-way lookup/hash keys where already used by current services;
- source system;
- source event ID;
- dedupe key;
- correlation ID;
- processing status;
- safe validation messages.

## Backward Compatibility

Existing routes remain current implementation facts:

- `POST /v1/progress`
- `POST /enterprise/events`
- `GET /admin/enterprise-events*`
- `POST /admin/enterprise-events/{inbox_event_id}/replay`

TASK-012 does not require renaming or removing these routes. A future public DLaaS route should wrap or delegate to current behavior and may normalize response shape without breaking existing clients.

## Follow-Up Implementation Tasks

- Implement a public/internal event ingestion route family only after API family and permission matrix work authorizes it.
- Add contract tests for duplicate, invalid, ignored, queued, failed, and replayed outcomes.
- Add tenant-scope tests proving body `tenantCode` cannot override credential scope.
- Define the webhook/event lifecycle catalog before promising broad outbound event names.
- Connect ingestion diagnostics to outcome trace once the internal outcome trace API exists.
- Add public-safe diagnostic lookup responses without exposing raw payloads.

## Validation Notes

This contract is based on static repository inspection only. No live database, production data, runtime credentials, or schema drift check was used.

The current schema and tests are sufficient to define the public ingestion behavior, idempotency expectations, and diagnostics vocabulary. They are not sufficient to authorize new public replay/repair operations or a broad event catalog without later tasks.
