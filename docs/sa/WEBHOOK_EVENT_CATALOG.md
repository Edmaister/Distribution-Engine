# DLaaS Webhook Event Catalog

Status: Accepted for TASK-020 on 2026-06-22.

TASK-020 defines the first DLaaS outbound webhook event catalog. This is a contract document only. It does not add event emitters, API routes, schema, migrations, subscription validation code, payload persistence, or delivery behavior.

## Source Truth

Current webhook delivery mechanics are backed by:

- `partner_clients`
- `partner_access_tokens`
- `partner_webhook_subscriptions`
- `partner_webhook_deliveries`
- `partner_webhook_alert_notifications`
- `services/partner_seam_service.py`
- `apps/api/routers/partner_seam.py`
- `apps/Workers/partner_webhook_worker.py`
- `docs/PARTNER_SEAM.md`
- `docs/API_PERMISSION_MATRIX.md`
- `docs/sa/API_SURFACE_MAP.md`
- `docs/sa/STATE_MACHINE_MAP.md`
- `docs/sa/AUDIT_RETRY_POLICY_STANDARD.md`
- `docs/sa/OUTCOME_TRACE_RESPONSE_CONTRACT.md`
- `docs/sa/LIABILITY_STATE_MODEL.md`

Current partner seam stores `event_type` as text on subscriptions, deliveries, and alert notifications. It supports tenant/client scoped subscriptions, HTTPS target URL validation, protected signing secrets, signed delivery headers, retry attempts, failed/cancelled exception views, partner/admin retry, alert notification evidence, and dead-letter export.

## Naming Rules

Event names are stable external contract names and must be uppercase snake case.

```text
<DOMAIN>_<BUSINESS_EVENT>
```

Examples:

- `CAMPAIGN_PUBLISHED`
- `OUTCOME_COMPLETED`
- `REWARD_APPLIED`
- `FULFILMENT_SUCCEEDED`

Do not use raw provider statuses, table names, route names, worker names, or internal exception names as webhook `event_type` values.

## Payload Envelope

Future emitted webhook payloads should use one envelope shape:

```json
{
  "event_id": "uuid-or-stable-event-id",
  "event_type": "OUTCOME_COMPLETED",
  "schema_version": "2026-06-22",
  "occurred_at": "ISO-8601 timestamp",
  "tenant": {
    "external_tenant_ref": "partner-facing-reference"
  },
  "subject": {
    "type": "outcome",
    "id": "safe-subject-reference"
  },
  "correlation": {
    "correlation_id": "safe-correlation-reference",
    "source_event_id": "safe-source-event-reference"
  },
  "data": {},
  "redactions": []
}
```

Payload rules:

- Prefer `external_tenant_ref` or role-specific external references for partner-facing tenant context. `tenant_code` remains internal unless a current backward-compatible route explicitly requires it.
- Include enough safe correlation evidence for support without exposing raw provider payloads, raw UCNs, access tokens, client secrets, signing secrets, settlement internals, or unrestricted audit metadata.
- Keep source statuses inside `data.source_status` only when the status is approved for the receiving surface. Use safe status mappings for fulfilment and settlement on partner/customer surfaces.
- Include `schema_version` so later payload additions can be additive.

## Initial Event Catalog

These events are eligible for future emission because they map to current source truth. TASK-020 does not implement emission.

| Event type | Family | Current source truth | Trigger meaning | Payload subject | Notes |
| --- | --- | --- | --- | --- | --- |
| `CAMPAIGN_PUBLISHED` | Campaign | `distribution_opportunities.opportunity_status = PUBLISHED`; campaign services/routes | A campaign/opportunity has become available for distribution. | `campaign` or `opportunity` | Do not expose internal readiness blocker internals. |
| `CAMPAIGN_CLOSED` | Campaign | `distribution_opportunities.opportunity_status = CLOSED`; campaign services/routes | A campaign/opportunity is no longer available for new distribution. | `campaign` or `opportunity` | Include safe reason only when available. |
| `OUTCOME_COMPLETED` | Outcome | `referral_instances`, `campaign_track_events.status = COMPLETED`, progress events, outcome trace contract | A tracked distribution outcome has reached completion evidence. | `outcome` | Existing partner seam tests already use this event type. |
| `OUTCOME_BLOCKED` | Outcome | `campaign_track_events.status = BLOCKED`; qualification decision contract | An outcome cannot proceed because current evidence blocks qualification or completion. | `outcome` | External payload must use safe blocker categories. |
| `REWARD_APPLIED` | Reward | `rewards`; `services/reward_service.py`; reward service event tests | A reward obligation has been applied or recorded. | `reward` | Keep reward and commission payloads separate. |
| `REWARD_FULFILLED` | Reward | `rewards.status = FULFILLED`; fulfilment evidence | A reward has safe fulfilment evidence. | `reward` | Do not expose provider internals. |
| `REWARD_FAILED` | Reward | `rewards.status = FAILED`; fulfilment failure evidence where linked | Reward processing has failed or needs attention. | `reward` | Use safe failure category, not raw error text. |
| `REWARD_REVERSED` | Reward | `rewards.status = REVERSED`; reversal evidence where present | A reward obligation or downstream movement has been reversed. | `reward` | Requires audit/correlation evidence before emission. |
| `FUNDING_RESERVED` | Funding | `funding_reservations.status = RESERVED`; marketplace allocation `RESERVED` | Funding has been reserved for an obligation. | `funding_obligation` | Funding is phase evidence over a reward or commission. |
| `FUNDING_RELEASED` | Funding | `funding_reservations.status = RELEASED`; marketplace allocation `RELEASED` | A previous reservation has been released. | `funding_obligation` | Do not imply settlement or fulfilment. |
| `FUNDING_SETTLED` | Funding | `funding_reservations.status = SETTLED`; funding/settlement evidence | Funding movement has settlement evidence. | `funding_obligation` | Must preserve no-double-counting rules. |
| `FUNDING_REVERSED` | Funding | marketplace allocation `REVERSED`; funding reversal evidence where available | Funding movement has been reversed. | `funding_obligation` | Requires safe reason and audit/correlation evidence. |
| `FULFILMENT_PENDING` | Fulfilment | fulfilment source status `PENDING` | Fulfilment work is waiting to start. | `fulfilment` | External status should be safe mapped. |
| `FULFILMENT_PROCESSING` | Fulfilment | fulfilment source status `PROCESSING` | Fulfilment work is in progress. | `fulfilment` | External status should be safe mapped. |
| `FULFILMENT_SUCCEEDED` | Fulfilment | fulfilment source status `SUCCESS` | Fulfilment has succeeded. | `fulfilment` | Do not expose provider reference unless explicitly safe. |
| `FULFILMENT_FAILED` | Fulfilment | fulfilment source statuses `FAILED_RETRYABLE`, `FAILED_FINAL`, `DLQ` | Fulfilment failed or needs operator/partner attention. | `fulfilment` | External payload must not leak raw provider or DLQ internals. |
| `FULFILMENT_DUPLICATE_SKIPPED` | Fulfilment | fulfilment source status `SKIPPED_DUPLICATE` | Duplicate fulfilment work was safely skipped. | `fulfilment` | Indicates no second side effect occurred. |
| `SETTLEMENT_PENDING` | Settlement | settlement source statuses `PENDING`, `PROCESSING` | Settlement work is waiting or processing. | `settlement` | External status should be safe mapped. |
| `SETTLEMENT_SETTLED` | Settlement | settlement source status `SETTLED`; settlement batch/item evidence | Settlement has completed. | `settlement` | Do not expose raw ledger internals. |
| `SETTLEMENT_FAILED` | Settlement | settlement source status `FAILED`; exception evidence where linked | Settlement failed or needs attention. | `settlement` | Use safe failure category. |
| `SETTLEMENT_REVERSED` | Settlement | settlement source status `REVERSED`; reversal rows | Settlement movement has been reversed. | `settlement` | Requires audit/correlation evidence before emission. |
| `SETTLEMENT_DISPUTED` | Settlement | settlement source status `DISPUTED`; open exception evidence | Settlement is disputed or blocked by exception evidence. | `settlement` | Partner/customer payload must not expose internal exception details. |
| `INTEGRATION_WEBHOOK_DELIVERY_FAILED` | Integration | `partner_webhook_deliveries.delivery_status = FAILED`; alerts/dead-letter export | A webhook delivery reached failed state. | `webhook_delivery` | This is an integration-health event, not a retry command. |
| `INTEGRATION_WEBHOOK_DELIVERY_RETRY_QUEUED` | Integration | partner/admin retry changes failed/cancelled delivery to `PENDING`; admin audit action `PARTNER_WEBHOOK_DELIVERY_RETRY` | A failed/cancelled delivery was queued for retry. | `webhook_delivery` | Retry remains guarded by partner/system admin authorization. |
| `INTEGRATION_WEBHOOK_SUBSCRIPTION_CHANGED` | Integration | `partner_webhook_subscriptions.status`; secret rotation routes | A webhook subscription or signing-secret state changed. | `webhook_subscription` | Never include signing secret or hash in event payload. |

## Delivery Mapping

The catalog maps onto current partner seam delivery mechanics as follows:

| Contract concern | Current mechanism |
| --- | --- |
| Subscription scope | `partner_webhook_subscriptions` stores `tenant_code`, `client_id`, `event_type`, `target_url`, status, metadata, and signing-secret fields. |
| Active delivery selection | `queue_webhook_deliveries` queues rows for active subscriptions matching tenant and event type. |
| Delivery row | `partner_webhook_deliveries` stores delivery ID, webhook ID, client ID, tenant, event type, payload, delivery status, attempts, last error, next attempt, and delivered timestamp. |
| Delivery statuses | `PENDING`, `SENT`, `FAILED`, `CANCELLED`. |
| Signing | Worker sends `X-Amplifi-Webhook-Id`, `X-Amplifi-Delivery-Id`, `X-Amplifi-Event-Type`, `X-Amplifi-Timestamp`, and `X-Amplifi-Signature`. |
| Retry | Worker retries transient HTTP `0`, `429`, and `5xx` outcomes while attempts remain below `WEBHOOK_MAX_ATTEMPTS = 3`, with `WEBHOOK_BACKOFF_SECONDS = 60`. |
| Dead-letter evidence | Failed/cancelled delivery rows are exposed through exception and dead-letter export views. |
| Alerting | `partner_webhook_alert_notifications` records repeated failure notification evidence. |
| Manual retry | Partner-scoped and system-admin retry routes requeue failed/cancelled delivery rows and write audit evidence. |

## Emission Rules For Future Implementation

Future event emission tasks must:

- use only catalog event names or update this catalog first;
- prove source truth and tenant/client scope before queueing a webhook;
- create one delivery row per matching active subscription;
- include a stable event identity or correlation reference where current source truth supports it;
- avoid emitting duplicate money, fulfilment, settlement, or webhook side effects for duplicate source events;
- use safe payload fields and redactions from the outcome trace, liability, and safe status contracts;
- keep event emission separate from source state mutation unless the future task explicitly owns both;
- add tests for catalog name validation, payload redaction, tenant scope, duplicate handling, retry exhaustion, signing headers, dead-letter export, and permission denial.

## Non-Goals

TASK-020 does not:

- add a webhook event catalog table;
- add event producer code;
- validate subscription `event_type` against the catalog;
- change partner seam APIs;
- change webhook retry behavior;
- change signing-secret storage;
- change reward, funding, fulfilment, settlement, audit, auth, privacy, tenant, or data-isolation behavior.

## Follow-Up Implementation Tasks

- Add catalog validation for subscription creation when the API is ready to reject unknown event types without breaking existing subscriptions.
- Add event producer helpers that queue `partner_webhook_deliveries` from source services after each source-specific task proves idempotency and audit behavior.
- Add payload builders for campaign, outcome, reward, funding, fulfilment, settlement, and integration events.
- Add webhook event contract tests and OpenAPI documentation for partner subscription event types.
- Update outcome trace webhook matching to use this catalog where payload correlation evidence is safe and explicit.

## Readback Validation

TASK-020 readback should confirm the catalog covers campaign, outcome, reward, funding, fulfilment, settlement, and integration event families; maps delivery to current partner seam tables and worker behavior; preserves signed delivery, retry, alert, and dead-letter rules; and avoids exposing raw provider, settlement, secret, token, or private identifier data.
