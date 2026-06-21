# Platform Audit And Retry Policy Standard

## Task Trace

| Item | Value |
| --- | --- |
| TASK ID | TASK-002 |
| Linked enhancements | DLaaS-002; DLaaS-012 |
| Linked capabilities | 14. Audit trail; 27. Observability; 28. Idempotency/retry handling |
| Status | Current policy standard. Implementation changes require separate tasks. |

## Purpose

Distribution Layer as a Service needs one standard for audit evidence, idempotency, retry behavior, and failure classification before adding new APIs, operator workflows, webhooks, or money-moving features.

This document does not introduce new database fields, statuses, APIs, or product behavior. It defines the policy future implementation tasks must satisfy, using current schema and service behavior as the source of truth.

## Confirmed Source Truth

| Area | Current evidence |
| --- | --- |
| Admin audit | `admin_audit_log`; `services/admin_audit_service.py`; `apps/api/routers/admin_audit.py` |
| Referral/progress processing audit | `referral_processing_audit`; `referral_event_failures`; `referral_progress_events.dedupe_key` |
| Enterprise event ingestion | `enterprise_event_inbox.processing_status`, `dedupe_key`, `correlation_id`; `services/enterprise_event_inbox_service.py` |
| Reward/fulfilment idempotency | `fulfilment_audit.idempotency_key`; `services/fulfilment_idempotency.py`; `services/fulfilment/service.py` |
| Fulfilment retry | `fulfilment_audit.attempt_no`, `max_attempts`, `failure_reason`, `error_code`; `services/fulfilment_retry_*`; admin fulfilment routes |
| Funding traceability | `funding_transactions`, `funding_reservations`, `funding_resolution_audit`, funding exception/reconciliation tables |
| Settlement traceability | Fulfilment settlement ledger, settlement batch, approval, exception, reversal, and certification services/tables |
| Webhook delivery retry | `partner_webhook_deliveries.delivery_status`, `attempt_count`, `last_error`, `next_attempt_at`; `services/partner_seam_service.py`; partner webhook tests |
| Governance audit | `distribution_governance_audit` includes `action_type`, `reason_code`, `actor`, `before_state`, `after_state` |

## Current Gap

Audit, retry, idempotency, and failure handling exist by domain. The gap is that future DLaaS tasks do not yet have one platform policy for:

- which actions require idempotency keys;
- which actions require bounded retry;
- which actions require actor and reason capture;
- which actions require before and after state;
- which actions must write audit records;
- which failures are retried, stopped, or sent to manual review.

## Platform Policy

### 1. Audit-Required Actions

| Action family | Audit required? | Minimum evidence |
| --- | --- | --- |
| Event ingestion that creates or advances attribution, qualification, reward, funding, fulfilment, settlement, or webhook state | Yes | Tenant/source, event identity, dedupe/idempotency evidence, processing result, correlation reference, failure reason when applicable |
| Reward, commission, funding, fulfilment, settlement, invoice, wallet, or payout mutation | Yes | Tenant, actor/system source, target, before state when available, after state, amount/currency when applicable, reason, correlation reference |
| Manual repair, replay, requeue, reversal, exception resolution, approval, rejection, suspension, revoke, or override | Yes | Actor, role, tenant, target, reason, before state, after state, correlation reference, source payload reference when safe |
| Credential, webhook subscription, API integration, or security-sensitive mutation | Yes | Actor, tenant/client, target, action, status, reason where applicable, correlation reference |
| Read-only operator access to sensitive exports, audit logs, DLQ payloads, or settlement evidence | Yes when exported or exposed outside normal UI access | Actor, tenant, filter scope, export target/type, timestamp |
| Ordinary safe read/list calls | No by default | Access must still be authorized and observable through normal request logs/metrics |

### 2. Required Audit Fields

Future audit-capable implementations must capture these fields when the source truth can provide them:

| Field | Requirement |
| --- | --- |
| Tenant/account scope | Required for tenant-scoped actions. If not currently available, mark as a gap before implementation. |
| Actor | Required for human/admin/partner actions. System actions must identify the service or worker source. |
| Actor role/source | Required for permission review and support trace. |
| Action domain | Required. Use the platform area, such as event ingestion, reward, funding, fulfilment, settlement, webhook, credential, governance, or repair. |
| Action type | Required. Use a verb phrase specific enough for investigation. |
| Action status | Required. Must distinguish success, failure, duplicate/no-op, queued/pending, and manual-review outcomes where applicable. |
| Target type and target ID | Required for entity-specific mutations. |
| Correlation reference | Required for event, async, money, retry, webhook, and repair flows. Current code uses `correlation_id` in several places, but consistency is still a gap. |
| Idempotency or dedupe key reference | Required for duplicate-sensitive writes and async processing. |
| Before state | Required for manual, money, status, credential, and governance mutations when a prior row/state exists. |
| After state | Required for manual, money, status, credential, and governance mutations. |
| Reason | Required for manual actions, repairs, reversals, rejects, exceptions, failed final outcomes, and policy overrides. |
| Failure category and raw error reference | Required for failed/retried actions. Raw provider payloads must not leak to customer/partner surfaces. |
| Retry metadata | Required for retryable async work: attempt number, max attempts, next attempt time where available, and final/DLQ state when exhausted. |

### 3. Idempotency Expectations

| Action family | Idempotency expectation | Current examples |
| --- | --- | --- |
| External event ingestion | Must have a deterministic dedupe or idempotency key before downstream side effects. Duplicate events must not create duplicate rewards, funding reservations, fulfilments, settlements, or webhooks. | `referral_progress_events.dedupe_key`; `enterprise_event_inbox.dedupe_key` |
| Reward or commission creation/application | Must use a stable business key, source event ID, or unique database guard. Duplicate handling must be explicit and observable. | Reward service and commission event uniqueness identified in TASK-001 |
| Funding reservation/release/settle | Must be idempotent by reward/outcome/reservation identity. Duplicate release/settle must not double-count available funds or liabilities. | `funding_reservations.reward_id` uniqueness and funding state guards identified in TASK-001 |
| Fulfilment execution | Must use a stable fulfilment idempotency key. Duplicate fulfilment must be skipped or returned as existing evidence, never processed twice. | `fulfilment_audit.idempotency_key`; `SKIPPED_DUPLICATE` service behavior |
| Settlement approval/processing/reversal | Must be guarded by settlement item/batch/reversal identity and state transitions. Duplicate approval or reversal must not create duplicate ledger movement. | Settlement services/tables identified in TASK-001 |
| Webhook subscription mutations | Must use tenant/client scope and duplicate-safe create/update behavior. |
| Webhook delivery | Must track delivery row identity, event identity where available, attempt count, outcome, and retry schedule. Duplicate delivery attempts must be observable. | `partner_webhook_deliveries` |
| Manual repair/replay/requeue | Must reference the original event/row and create a repair correlation. Repeated repair commands must be safe or clearly rejected. |
| Read-only APIs | Do not need idempotency keys, but must be side-effect free and authorized. |

### 4. Retry Classes

These classes are policy categories, not new database enum values.

| Class | Meaning | Expected behavior |
| --- | --- | --- |
| No retry | Validation, authorization, missing source truth, unsafe state, or non-retryable provider response. | Stop, return/write failure evidence, require corrected input or manual action. |
| Immediate duplicate/no-op | Duplicate request/event where prior result exists or work is already complete. | Return existing state or mark duplicate/no-op; do not run side effects again. |
| Bounded retry | Transient provider, network, queue, timeout, or dependency issue. | Retry with max attempts and backoff; preserve attempt evidence. |
| Delayed/manual review | Business rule, funding, settlement, risk, or data-integrity issue that cannot be resolved safely by automatic retry. | Stop automatic mutation, surface operator action, require actor/reason for repair. |
| Final failure | Attempts exhausted or failure classified as permanent. | Mark final/DLQ/failed state according to existing source truth, write audit evidence, expose safe status only. |
| Compensation/reversal | Prior money or fulfilment movement must be reversed or offset. | Require explicit audit, actor/system source, reason, before/after, and reconciliation evidence. |

### 5. Failure Categories

These categories are target policy language for future docs, tests, and operator UX. They must be mapped to existing fields or implemented in a separate task before becoming API/schema behavior.

| Category | Use when | Retry default |
| --- | --- | --- |
| `VALIDATION` | Payload, state transition, or required field is invalid. | No retry |
| `AUTHORIZATION` | Actor/client lacks permission or tenant scope. | No retry |
| `DUPLICATE` | Idempotency/dedupe guard detects repeated work. | No side effect |
| `TRANSIENT_DEPENDENCY` | Network, timeout, queue, or provider instability. | Bounded retry |
| `PROVIDER_FINAL` | Provider rejects the action permanently. | No retry unless repaired |
| `FUNDING_NOT_READY` | Funds, reservation, wallet, or budget is unavailable or blocked. | Manual review or delayed retry only when state can change safely |
| `SETTLEMENT_EXCEPTION` | Settlement item/batch/reversal/reconciliation has an exception. | Manual review |
| `SCHEMA_OR_CONTRACT` | Live DB, payload contract, or source truth does not match expectation. | Stop and create follow-up task |
| `DATA_INTEGRITY` | Missing/corrupt relationship, impossible state, or mismatch across money/audit evidence. | Stop and require investigation |
| `UNKNOWN` | Unexpected failure before classification. | Conservative stop or bounded retry only if no money side effect occurred |

## Domain Requirements

### Event Ingestion

- Must validate auth, tenant/source, payload shape, and event identity before side effects.
- Must use dedupe/idempotency evidence for external events.
- Must record accepted, queued, duplicate, ignored, failed, and replayed outcomes using existing source truth.
- Must not trigger reward, funding, fulfilment, settlement, or webhook side effects twice for the same source event.
- Failed/replayed events need operator-visible diagnostics and correlation evidence.

### Rewards And Commissions

- Reward/commission decisions must trace to source event, rule/policy source, participant, amount, currency when applicable, and target status.
- Duplicate application must be blocked by stable business keys or database uniqueness.
- Money-affecting transitions require audit evidence.
- Customer/partner surfaces must receive safe derived status, not raw internal failure payloads.

### Funding

- Reservation, release, settlement, reconciliation, and exception flows require correlation evidence.
- Funding mutations require before/after money state where the current service/table can provide it.
- Funding failures must distinguish insufficient/unavailable funding from system errors and data-integrity gaps.
- Automatic retry is not allowed when it could double-reserve, double-release, or double-settle funds.

### Fulfilment

- Fulfilment execution must be idempotent.
- Retry must be bounded by attempt count and max attempts.
- Provider/transient failures may retry; permanent provider failures and exhausted attempts must move to final/DLQ handling according to current fulfilment source truth.
- Replays and manual retries require actor/reason capture when human-triggered.

### Settlement

- Batch approvals, rejects, processing, settlement, disputes, reversals, and certifications require audit evidence.
- Reversal/compensation must capture reason, target, before/after, and correlation evidence.
- Settlement exceptions must be operator-visible and must not be exposed directly to customers/partners without safe copy.

### Webhooks And Integrations

- Outbound webhook delivery must record delivery status, attempt count, last error, and next attempt when available.
- Retry must be bounded and observable.
- Subscription and credential changes require audit evidence and tenant/client scope.
- Dead-letter/export behavior must avoid leaking secrets and must preserve enough evidence for support investigation.

### Manual Repair And Operator Actions

- Manual actions require actor, role/source, tenant scope, target, reason, before state, after state, and correlation evidence.
- Repair commands must be either idempotent or reject unsafe repeated execution.
- Operators must see what happened, what happens next, whether action is required, and the source evidence behind the recommendation.

## Future API Requirements

Future API tasks that mutate DLaaS-critical state must explicitly document:

- authentication and tenant/client scope;
- validation rules;
- idempotency key or duplicate handling;
- retry behavior for async work;
- failure categories and safe error shape;
- audit event written;
- events/webhooks emitted;
- database entities touched;
- tests for duplicate, retry exhaustion, permission denial, and audit evidence.

Read-only APIs must still document auth, tenant scope, validation, errors, and whether the response is a safe customer/partner view or an operator-only view.

## Future Test Requirements

Implementation tasks that touch these areas must add or update tests for:

- audit record creation on sensitive mutation;
- actor/reason capture for manual action;
- before/after state capture where supported by source truth;
- duplicate request/event handling;
- retryable failure scheduling;
- retry exhaustion/final failure/DLQ behavior;
- no double reward, double commission, double reservation, double payout, or double settlement;
- permission denial and cross-tenant denial;
- safe customer/partner status mapping;
- redaction of provider errors, secrets, and restricted payloads.

## Acceptance Coverage For TASK-002

| Required by TASK-002 | Covered by |
| --- | --- |
| Actions requiring idempotency keys | Idempotency expectations table |
| Bounded retry expectations | Retry classes and domain requirements |
| Actor/reason capture | Required audit fields and manual repair requirements |
| Before/after state | Required audit fields and money/manual domain requirements |
| Audit records | Audit-required actions and domain requirements |
| Event ingestion coverage | Event ingestion domain requirements |
| Reward coverage | Rewards and commissions domain requirements |
| Funding coverage | Funding domain requirements |
| Fulfilment coverage | Fulfilment domain requirements |
| Settlement coverage | Settlement domain requirements |
| Webhook coverage | Webhooks and integrations domain requirements |
| Repair action coverage | Manual repair and operator actions |

## Follow-Up Dependencies

- TASK-027 must still verify live DB/schema reality before money, settlement, webhook, or API implementation relies on this standard.
- TASK-028 must resolve schema uncertainty discovered by TASK-001 and TASK-027.
- Future implementation tasks must map this policy to concrete service code, schema constraints, API contracts, and tests before shipping behavior changes.
