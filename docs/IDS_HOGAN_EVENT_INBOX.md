# IDS / Hogan Event Inbox

IDS/Hogan events are treated as enterprise source events, not direct reward
instructions.

## Flow

```text
Hogan / IDS event
        |
        v
POST /enterprise/events
        |
        v
enterprise_event_inbox
        |
        v
normalize qualifying event
        |
        v
enqueue REFERRAL_PROGRESS_RECORDED
        |
        v
worker processes journey progress
        |
        v
reward policy / fulfilment can run from journey state
```

## API Endpoint

`POST /enterprise/events`

Authentication:

- Requires an admin or partner API key.
- Partner keys derive the tenant from the key, for example the local FNB test
  key sets `tenantCode` to `FNB`.
- Admin keys can send `tenantCode` in the payload.

Common request fields:

- `eventType`
- `source` or `sourceSystem`
- `sourceEventId`
- `tenantCode`
- `referralTrackId`
- `correlationId`
- `occurredAt`

The response reports whether the event was `QUEUED`, `IGNORED`, or
`DUPLICATE`.

## Admin Operations

`GET /admin/enterprise-events/summary`

- Returns counts grouped by inbox processing status.

`GET /admin/enterprise-events`

- Lists recent inbox events.
- Supports filters for `processingStatus`, `sourceSystem`,
  `referralTrackId`, and `limit`.

`GET /admin/enterprise-events/dashboard`

- Returns dashboard-oriented counts for a time window.
- Includes breakdowns by processing status, source system, and event type.
- Includes recent problem events with status `IGNORED`, `FAILED`, or
  `DUPLICATE`.
- Supports `tenantCode`, `days`, and `problemLimit`.

`POST /admin/enterprise-events/{inboxEventId}/replay`

- Defaults to `dryRun=true`.
- If the inbox event has a `normalized_payload`, dry run reports that it is
  replayable.
- With `dryRun=false`, the normalized payload is queued again for worker
  processing.
- Events without a normalized payload are skipped, because there is no platform
  progress event to replay yet.

## Metrics

Prometheus metrics for this flow:

- `enterprise_events_ingested_total{source_system,event_type,processing_status}`
- `enterprise_event_replays_total{event_type,status}`
- `enterprise_event_inbox_current{processing_status}`

The inbox current gauge is refreshed when
`GET /admin/enterprise-events/summary` is called.

## Inbox Table

The inbox migration is `dp/migrations/061_enterprise_event_inbox.sql`.

It stores:

- `tenant_code`
- `source_system`
- `source_event_id`
- `correlation_id`
- `referral_track_id`
- `event_type`
- `occurred_at`
- `received_at`
- `raw_payload`
- `normalized_payload`
- `payload_hash`
- `dedupe_key`
- `processing_status`
- `processed_at`
- `error_message`

Processing statuses:

- `RECEIVED`
- `QUEUED`
- `IGNORED`
- `FAILED`
- `DUPLICATE`

## Qualifying Events

`apps/Workers/ids_consumer.py` currently maps:

| IDS/Hogan event | Platform progress event |
| --- | --- |
| `ACCOUNT_ACTIVATED` | `ACCOUNT_ACTIVATED` |
| `DEBIT_ORDER_SWITCHED` | `DEBIT_ORDER_SWITCHED` |
| `SALARY_DEPOSIT` | `SALARY_SWITCHED` |
| `SALARY_SWITCHED` | `SALARY_SWITCHED` |
| `POLICY_ACTIVATED` | `POLICY_ACTIVATED` |

Events that are not qualifying, or do not include both a tenant and a referral
track id, are stored but marked `IGNORED`.

Duplicate source events are detected using a deterministic `dedupe_key` and are
not queued again.

## Runtime Note

The migration has been applied in the current local database used for smoke
testing. Other environments still need `061_enterprise_event_inbox.sql` applied
before using the endpoint.
