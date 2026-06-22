# SaaS Usage And Billing Separation Model

Status: Accepted for TASK-025 on 2026-06-22.

## Purpose

TASK-025 defines the SaaS usage, quota, plan, subscription, and billing boundary for DLaaS packaging.

This is a contract document only. It does not add schema, migrations, API routes, billing provider integration, usage writers, rollup jobs, quota enforcement, frontend screens, money movement, invoice mutation, sponsor billing changes, or live database checks.

## Problem Statement

DLaaS needs platform SaaS packaging: accounts, plans, seats, usage tracking, quotas, subscriptions, billing hooks, and support operations. The repository already has useful primitives such as partner credentials, rate limiting, runtime metrics, sponsor utilisation billing, sponsor invoices, funding contracts, webhooks, reporting, and audit.

Those primitives are not the same as SaaS billing. Runtime metrics are not durable billable usage. Partner clients are not full account-scoped API keys. Sponsor utilisation billing is not platform subscription billing. Reward, funding, fulfilment, and settlement money flows are customer/distribution obligations, not SaaS subscription revenue.

## Decision

Define a separate SaaS packaging boundary:

- SaaS usage records meter platform consumption by account, tenant, credential, actor, and feature.
- SaaS plans and subscriptions determine entitlements, quotas, billing cadence, and commercial terms.
- SaaS billing hooks transform accepted usage and subscription state into platform billing events.
- Sponsor utilisation billing remains a separate domain for producer/sponsor recovery and must not be reused as the platform subscription billing model.
- Operational metrics, analytics reports, liability projections, funding ledgers, and settlement evidence remain source-specific and must not be treated as billing-grade usage unless a future usage writer records a durable usage event.

## Source Truth

Current source candidates and boundaries:

| Source | Current role | SaaS boundary |
| --- | --- | --- |
| `docs/sa/TENANT_ACCOUNT_LIFECYCLE_MEMBERSHIP_MODEL.md` | Future account, tenant, membership, seat, and external reference model. | Account and tenant ownership source for usage and subscription scope. |
| `docs/API_PERMISSION_MATRIX.md` | API family auth, tenant scope, idempotency, audit, and safe error guardrails. | Future usage/billing APIs must follow this matrix. |
| `apps/api/middleware/rate_limit.py` | Runtime request throttling by key/client/tenant. | Useful quota-enforcement candidate, but not durable usage metering. |
| `utils/metrics.py` | Prometheus counters/gauges/histograms for operations. | Useful observability signal, but not billing-grade usage. |
| `services/partner_seam_service.py` | Partner clients, tokens, webhook subscriptions/deliveries, secret protection. | Reusable credential/integration source, not the whole SaaS API-key product. |
| `services/marketplace_funding/sponsor_billing_service.py` | Sponsor utilisation invoices, payment receipts, and sponsor payment/reversal flows. | Must remain sponsor billing, not platform SaaS billing. |
| `docs/sa/TENANT_SAFE_ANALYTICS_REPORTING_CONTRACT.md` | Tenant-safe analytics dimensions, freshness, exports, and ledger reconciliation. | Reporting may summarize usage later, but does not create billable usage. |
| `services/outcome_trace_service.py` and `services/liability_projection_service.py` | Outcome, liability, money-phase evidence. | May supply feature usage dimensions; must not be counted as platform revenue obligations. |

## Non-Goals

TASK-025 does not:

- create `usage_events`, `usage_rollups`, `plans`, `subscriptions`, invoices, or billing customer tables;
- modify sponsor invoices, sponsor wallet records, funding records, fulfilment records, settlement records, or liability projection behavior;
- add billing provider APIs or invoice webhooks;
- change rate-limit behavior;
- add API-key creation, rotation, revocation, or entitlement enforcement;
- start TASK-026 or any white-label/embed work.

## Domain Separation

| Domain | Owns | Must not be confused with |
| --- | --- | --- |
| SaaS platform billing | Account subscription charges, plan fees, seat fees, platform usage charges, overage charges, billing customer IDs, payment-provider hooks. | Sponsor utilisation invoices, reward liabilities, funding reservations, fulfilment payouts, settlement ledgers. |
| SaaS usage metering | Durable accepted usage events, rollups, quota counters, entitlement decisions, usage attribution. | Prometheus metrics, request logs, analytics reports, raw rate-limit counters. |
| Sponsor utilisation billing | Sponsor/producer invoice recovery for funded campaigns and sponsor obligations. | Platform subscription or plan billing. |
| Funding/liability/settlement | Reward, commission, funding, fulfilment, settlement, wallet, invoice, and audit evidence over distribution obligations. | SaaS account revenue, plan fees, usage charges, or overages. |
| Analytics/reporting | Read-only tenant/operator reporting with freshness and safe dimensions. | Billing-grade usage write path or invoice source of truth. |

## SaaS Packaging Entities

Future implementation should keep these entities distinct:

| Entity | Purpose | Required boundary |
| --- | --- | --- |
| `account` | Commercial SaaS customer account that owns one or more tenants/environments. | Maps to internal tenants but is not the same as `tenant_code`. |
| `tenant` | Internal platform isolation and source-data partition. | `tenant_code` remains internal for partitioning, audit, funding, fulfilment, settlement, and reporting. |
| `plan` | Commercial packaging: feature entitlements, included usage, limits, billing cadence. | Does not directly mutate campaign, reward, funding, fulfilment, or settlement state. |
| `subscription` | Account's active plan relationship and billing state. | Drives entitlements and billing hooks, not sponsor invoices. |
| `seat` | User/member entitlement attached to account/tenant membership. | Seat counts can be billable usage, but membership auth remains separate. |
| `api_credential` | Account/tenant/integration credential with scopes and lifecycle. | Partner seam clients may be reusable as an integration source but are not full SaaS credentials yet. |
| `usage_event` | Immutable billing-grade record of accepted platform consumption. | Must be idempotent and durable; not replaced by metrics/logs. |
| `usage_rollup` | Aggregated usage by account, tenant, credential, period, and usage type. | Rebuildable from usage events and not authoritative without source event lineage. |
| `quota_counter` | Current enforcement counter for plan or feature limits. | Can be near-real-time but should reconcile to usage events. |
| `billing_hook` | Outbound billing-provider or invoice-system event. | Must be idempotent, auditable, and separate from sponsor billing hooks. |

## Billable Usage Event Catalog

Initial candidate usage events should map to current service hooks, but future implementation must add durable event writes before billing.

| Usage event | Trigger candidate | Current hook candidate | Billing posture |
| --- | --- | --- | --- |
| `API_REQUEST_ACCEPTED` | Accepted authenticated API request. | Rate-limit middleware, session/auth helpers, API routers. | Candidate billable event; must exclude health/metrics and rejected auth. |
| `EVENT_INGESTED` | Accepted public/partner enterprise or progress event. | Progress/event ingestion services and enterprise inbox. | Candidate billable event with idempotency by source event identity. |
| `CAMPAIGN_CREATED` | Campaign or opportunity created. | Campaign and distribution opportunity services. | Candidate plan/usage event, not money movement. |
| `CAMPAIGN_ACTIVE_DAY` | Campaign remains active during a billing day. | Campaign/opportunity lifecycle sources. | Candidate rollup event; requires clear active-state definition. |
| `LINK_ISSUED` | Distribution/referral link or code issued. | Referral code, campaign link, route referral link services. | Candidate billable event; must dedupe idempotent issue calls. |
| `OUTCOME_RECORDED` | Qualified or completed distribution outcome recorded. | Outcome trace/progress/reward source truth. | Candidate billable event; not the same as reward liability. |
| `REWARD_OR_COMMISSION_CALCULATED` | Reward or distributor commission obligation calculated. | Reward and commission services. | Candidate usage event; must not count fulfilment/settlement phases as new usage. |
| `WEBHOOK_DELIVERY_ATTEMPTED` | Outbound webhook delivery attempt created or attempted. | Partner seam delivery rows/worker. | Candidate billable or quota event; failed attempts may be included only if plan says so. |
| `WEBHOOK_SUBSCRIPTION_ACTIVE_DAY` | Webhook subscription remains active during a billing day. | Partner seam subscriptions. | Candidate rollup event. |
| `REPORT_EXPORT_CREATED` | Tenant/operator export generated. | Future analytics export API from TASK-024. | Candidate usage event; must obey export redaction/audit rules. |
| `SEAT_ACTIVE_DAY` | Account member/seat active during a billing day. | Future account/membership model. | Candidate plan entitlement and usage event. |
| `STORAGE_RETENTION_GB_DAY` | Retained artifacts or exports consume billable storage. | Future export/artifact retention service. | Later candidate only; requires storage source truth. |

Events that are not billable by default:

- Retry, replay, repair, fulfilment, settlement approval, reversal, payout, and funding mutation commands.
- Internal worker retries caused by platform failures.
- Health checks, readiness checks, metrics scrapes, and unauthorized requests.
- Sponsor invoice creation, sponsor payment allocation, and sponsor payment reversal.

## Usage Event Contract

Future usage writers should emit immutable events with a shape like:

```json
{
  "usage_event_id": "stable-id-or-uuid",
  "idempotency_key": "source-family:source-id:usage-type",
  "usage_type": "API_REQUEST_ACCEPTED",
  "account_ref": "internal-account-reference",
  "tenant_code": "INTERNAL_TENANT",
  "external_tenant_ref": "external-tenant-reference-when-safe",
  "credential_ref": "safe-credential-reference",
  "actor_ref": "safe-actor-reference",
  "source_family": "api",
  "source_id": "safe-source-row-reference",
  "quantity": 1,
  "unit": "request",
  "occurred_at": "ISO-8601 timestamp",
  "billing_period": "YYYY-MM",
  "metadata": {}
}
```

Required rules:

- Usage writes must be idempotent by source event and usage type.
- Usage must be attributed to account, tenant, credential or actor where available.
- `tenant_code` may be stored internally, but external APIs should expose external tenant/account references.
- Usage metadata must not include secrets, raw provider payloads, raw UCNs, private customer identifiers, raw settlement internals, or unrestricted audit payloads.
- Usage event correction must be additive through adjustment/reversal events, not destructive edits.

## Rollups And Quotas

Rollups should be derived from immutable usage events:

| Rollup | Purpose |
| --- | --- |
| Account-period rollup | Billing line item source by account, period, usage type, unit, and quantity. |
| Tenant-period rollup | Tenant-level usage visibility and reporting. |
| Credential-period rollup | API key/client usage attribution and abuse investigation. |
| Feature-period rollup | Plan entitlement and overage analysis. |
| Quota counter | Near-real-time enforcement state for plan limits. |

Quota enforcement rules:

- Reads and commands must validate entitlements before expensive or mutating work when possible.
- Quota denial should return safe `quota_exceeded` or `plan_limit_exceeded` errors.
- Quota counters may be fast-path state, but billing must reconcile to usage events.
- Quota bypasses must be explicit, auditable, and limited to operator/support roles.

## Plan And Subscription Boundary

Future plans should define:

- included seats;
- included API requests;
- included ingested events;
- included active campaigns;
- included links/codes;
- included webhook subscriptions or delivery attempts;
- export and retention limits;
- overage pricing keys;
- feature entitlements;
- billing cadence and trial rules.

Future subscriptions should define:

- account and tenant scope;
- plan code and plan version;
- subscription status;
- billing period;
- billing customer reference;
- payment provider reference where applicable;
- trial, suspension, cancellation, and grace-period states;
- entitlement snapshot for reproducible billing.

Subscription state must not mutate campaign, reward, funding, fulfilment, settlement, or sponsor billing state directly. It may deny or gate future platform actions through entitlements and quota checks.

## Billing Hook Boundary

Future billing hooks should be generated from subscriptions, usage rollups, and explicit adjustment events.

Billing hooks must:

- be idempotent by account, billing period, hook type, and source rollup version;
- carry safe billing customer references, not private identifiers;
- include usage type, quantity, unit, period, plan code, and currency/pricing reference where available;
- include audit/correlation references;
- avoid raw provider payloads, tokens, secrets, and unrelated tenant data;
- keep platform SaaS invoices separate from sponsor invoices.

Recommended hook families:

- `SAAS_SUBSCRIPTION_CREATED`
- `SAAS_SUBSCRIPTION_CHANGED`
- `SAAS_USAGE_ROLLED_UP`
- `SAAS_INVOICE_REQUESTED`
- `SAAS_PAYMENT_STATUS_UPDATED`
- `SAAS_CREDIT_ADJUSTMENT_RECORDED`

## Sponsor Billing Separation

Sponsor billing remains the source for sponsor utilisation invoices, sponsor payment receipts, allocations, payment reversals, and sponsor-facing statements.

SaaS billing must not:

- reuse sponsor invoice tables as platform subscription invoices;
- reuse sponsor payment receipt tables as SaaS payment records;
- count sponsor invoice lines as SaaS usage charges;
- use sponsor wallet/funding contracts as SaaS subscription balances;
- mix sponsor payment state with account subscription state.

Where a future account is also a sponsor/producer, the account may have both SaaS subscription billing and sponsor utilisation billing. The two ledgers must stay separate and reconciled by explicit references only.

## API And Auth Direction

TASK-025 does not add APIs. Future route families may include:

```text
GET /admin/saas/accounts/{account_ref}/usage
GET /admin/saas/accounts/{account_ref}/subscription
POST /admin/saas/usage-events
POST /admin/saas/billing-hooks/replay
GET /v1/account/usage
GET /v1/account/subscription
```

Implementation guardrails:

- Account/tenant membership auth must come from the account lifecycle and permission contracts.
- Tenant scope must derive from identity for non-admin callers.
- Usage writes require idempotency, validation, and audit.
- Usage reads and subscription reads are read-only and do not require idempotency keys.
- Billing hook replay is a guarded admin command with idempotency and audit.
- Safe errors must use `validation_error`, `permission_denied`, `quota_exceeded`, `plan_limit_exceeded`, `billing_unavailable`, or `not_found` style categories without leaking sensitive data.

## Reporting Relationship

SaaS usage reporting should follow TASK-024:

- Usage reports must be tenant/account scoped.
- Usage report freshness must be explicit.
- Usage exports must be redacted and auditable when persisted.
- Usage reports are not ledger-backed money totals unless they are tied to a billing rollup or invoice hook.
- Platform SaaS revenue reporting must be separated from reward, commission, funding, fulfilment, settlement, and sponsor utilisation totals.

## Validation Expectations

Future implementation tasks must add tests for:

- idempotent usage event writes;
- duplicate source-event suppression;
- usage attribution to account, tenant, credential, actor, and feature;
- quota counter increments and quota denial;
- plan entitlement checks and rejected feature access;
- usage rollup accuracy by billing period;
- sponsor-vs-SaaS separation;
- billing hook idempotency and replay safety;
- redaction of secrets, private identifiers, provider payloads, and settlement internals;
- tenant and account isolation for usage reads and exports.

## Follow-Up Implementation Tasks

Later tasks should:

- add an additive SaaS schema for accounts, plans, subscriptions, usage events, rollups, quota counters, and billing hooks;
- implement a small idempotent usage writer behind one low-risk source such as accepted API requests or webhook deliveries;
- integrate quota enforcement only after plan/subscription source truth exists;
- add SaaS account usage read APIs after account membership and tenant-scope checks are implemented;
- integrate billing provider hooks only after usage rollups and sponsor-vs-SaaS separation tests exist.

## Readback Validation

TASK-025 readback should confirm that this model defines billable usage events, rollups, quotas, plans, subscriptions, billing hooks, idempotency rules, attribution rules, sponsor-vs-SaaS separation, reporting relationships, safe API direction, and future tests without adding schema, routes, services, frontend changes, or money movement.
