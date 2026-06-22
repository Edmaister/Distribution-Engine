# Tenant-Safe Analytics Reporting Contract

Status: Accepted for TASK-024 on 2026-06-22.

## Purpose

TASK-024 defines tenant-safe analytics dimensions, freshness rules, export constraints, and ledger reconciliation boundaries for DLaaS reporting.

This is a contract document only. It does not add API routes, schema, migrations, materialized views, rollup jobs, frontend charts, money movement, repair actions, fulfilment actions, settlement actions, or live database checks.

## Source Truth

Current reporting must be grounded in source-owned facts:

- Outcome and attribution evidence: `services/outcome_trace_service.py`.
- Liability totals and no-double-counting rules: `services/liability_projection_service.py` and `docs/sa/LIABILITY_STATE_MODEL.md`.
- Fulfilment and settlement safe statuses: `services/fulfilment_safe_status.py`.
- Operator control-plane contract: `docs/sa/OPERATOR_CONTROL_PLANE_BFF_CONTRACT.md`.
- Partner/customer-safe status contract: `docs/sa/PARTNER_CUSTOMER_SAFE_STATUS_CONTRACT.md`.
- Webhook event and delivery catalog: `docs/sa/WEBHOOK_EVENT_CATALOG.md`.
- Current reporting candidates: `services/distribution/reporting_service.py`, `services/finance_metrics_service.py`, `utils/metrics.py`, and `dp/migrations/011_materialized_views.sql`.

## Decision

DLaaS analytics must be tenant-scoped, source-owned, freshness-labelled, and explicit about whether a metric is operational or ledger-backed.

Reporting implementation tasks must not invent new dimensions or money totals. They should consume this contract, the outcome trace service, liability projection, safe status mappings, and existing domain reporting sources.

## Reporting Classes

| Class | Meaning | Source expectation |
| --- | --- | --- |
| `OPERATIONAL` | Counts, rates, conversion movement, processing latency, retry health, webhook delivery health, and status distribution. | May come from operational tables, traces, dashboards, or materialized views when freshness is shown. |
| `LEDGER_BACKED` | Money totals that must reconcile to reward, commission, funding, fulfilment, settlement, wallet, invoice, or ledger evidence. | Must use liability projection, finance metrics, funding/settlement ledgers, or future reviewed rollups. |
| `DERIVED_STATUS` | Safe state categories used for operator, partner, customer, and export views. | Must use documented safe mappings or source-specific derived contracts. |
| `FORECAST_OR_ESTIMATE` | Forecast, readiness, budget exposure, recommendation, or projected performance values. | Must be labelled as non-ledger-backed and separated from actual money totals. |

Operational metrics may be useful without being financially authoritative. Ledger-backed totals must never be mixed into operational totals without an explicit class label.

## Required Envelope Fields

Future reporting responses or exports should include:

| Field | Requirement |
| --- | --- |
| `report_type` | Stable report identifier, such as `campaign_performance`, `liability_reconciliation`, or `webhook_health`. |
| `tenant_scope` | Resolved internal tenant scope for backend/operator use. Tenant-facing reports must resolve from identity or validated filter. |
| `external_tenant_ref` | Future public/SaaS-facing tenant reference when exposed outside internal/operator surfaces. |
| `filters` | Safe echo of validated filters, excluding secrets, private identifiers, provider payloads, or raw audit payloads. |
| `dimensions` | Requested dimensions from the approved catalog. |
| `metric_class` | `OPERATIONAL`, `LEDGER_BACKED`, `DERIVED_STATUS`, or `FORECAST_OR_ESTIMATE`. Mixed responses must classify each metric. |
| `data_window_start` / `data_window_end` | Inclusive/exclusive report window, with timezone normalized by API contract. |
| `generated_at` | Time the response or export was generated. |
| `freshness` | Freshness block described below. |
| `source_warnings` | Structured warnings for weak joins, unavailable sources, partial rollups, or stale data. |
| `redactions` | Redactions applied to protect private identifiers or internal data. |

## Dimension Catalog

These dimensions are approved for future TASK-024-based reporting implementation. A later task may add to the catalog only by updating this contract or a successor contract.

| Dimension family | Approved dimensions | Boundary rules |
| --- | --- | --- |
| Tenant/account | `tenant_code` for internal/operator joins; `external_tenant_ref` for SaaS-facing reports; `report_scope`; `environment` where available. | Tenant-facing reports must not depend on caller-supplied `tenant_code` unless the route is explicitly internal/admin. |
| Campaign/opportunity | Campaign code/reference, campaign status, opportunity status, readiness status, blocker category, product, sub-product, journey, channel. | Do not expose internal readiness details externally unless mapped to a safe blocker category. |
| Participant | Participant role, safe participant reference, distributor code, sponsor/producer code, partner/client reference, organisation reference. | Do not expose raw UCNs, private customer identifiers, or cross-role participant internals. |
| Link/code | Link type, source channel, route status, link status, safe code/link state, issued/resolved/voided period. | Public or partner reports use safe link state, not raw attribution internals. |
| Outcome/attribution | Safe outcome reference, referral track reference for operator-only reports, outcome status, trace completeness, attribution source, event family, missing-evidence count. | External views must avoid raw private identifiers and use outcome-safe status categories. |
| Qualification | Decision category, blocker category, policy family, evidence completeness. | Do not expose fraud, policy, or risk internals outside operator-safe views. |
| Reward/commission | Reward type, beneficiary category, liability category, commission category, source family, derived liability state, safe status. | Customer reward and distributor commission totals must stay separate. |
| Funding/liability | Liability category, derived liability state, funding source family, reservation/allocation phase, reconciliation status, currency. | Funding, wallet, invoice, fulfilment, and settlement evidence must not be counted as new obligations. |
| Fulfilment | Safe fulfilment status, terminal flag, action-required flag, provider family only when operator-safe, retry bucket. | External reports must use external-safe mappings and hide raw provider/DLQ internals. |
| Settlement | Safe settlement status, terminal flag, action-required flag, dispute/reversal category, settlement period. | External reports must hide raw settlement internals and exception details. |
| Webhook/integration | Event family, catalog event type, delivery safe status, attempt bucket, subscription status, dead-letter flag, alert flag. | Never expose signing secrets, hashes, payload secrets, or raw delivery payload internals. |
| Audit/support | Audit reference count, support trace completeness, source warning count, redaction count, correlation reference count. | Audit payloads, secrets, raw DLQ payloads, and private identifiers remain internal. |

## Metric Catalog

### Operational Metrics

Operational metrics include:

- Campaign, opportunity, link, route, outcome, qualification, and status counts.
- Conversion counts and rates by safe dimension.
- Event ingestion counts, duplicate counts, failed processing counts, and replay/DLQ counts.
- Fulfilment and settlement counts by safe status, retry bucket, and action-required flag.
- Webhook delivery counts by catalog event type, delivery status, retry bucket, and dead-letter state.
- Processing latency and freshness lag where source timestamps are available.

Operational metrics do not prove money owed, paid, settled, reversed, or disputed.

### Ledger-Backed Money Metrics

Ledger-backed metrics include:

- `obligation_total`
- `reserved_total`
- `released_total`
- `fulfilled_total`
- `settled_total`
- `reversed_total`
- `failed_total`
- `disputed_total`

These totals must be grouped by currency and liability category where applicable. Source evidence must preserve customer reward, referrer reward, and distributor commission separation.

### Forecast Or Estimate Metrics

Forecast or estimate metrics include:

- Budget exposure projections.
- Campaign readiness projections.
- Expected fulfilment or settlement volume.
- Recommendation or optimization outputs.

These values must be labelled as forecast/estimate and must not appear as actual ledger-backed totals.

## Tenant Filter Rules

- Tenant-facing reports must resolve tenant scope from authenticated identity, external tenant reference mapping, or role-specific external reference.
- Internal/operator reports may use `tenant_code`, but cross-tenant access requires an explicit operator role and explicit filter scope.
- Partner, distributor, producer, sponsor, referrer, and customer reports must apply both tenant and participant scope before returning data.
- Empty or broad tenant filters must be rejected unless the caller has a cross-tenant operator role.
- Reports must validate dimension names, date windows, pagination, grouping, sort fields, export format, and row limits before querying.
- Safe errors must not disclose whether another tenant has data.

## Freshness Rules

Every report must include a freshness block:

```json
{
  "status": "FRESH",
  "generated_at": "ISO-8601 timestamp",
  "source_as_of": "ISO-8601 timestamp",
  "data_window_start": "ISO-8601 timestamp",
  "data_window_end": "ISO-8601 timestamp",
  "lag_seconds": 42,
  "sources": [
    {
      "source_family": "liability",
      "status": "FRESH",
      "source_as_of": "ISO-8601 timestamp"
    }
  ]
}
```

Freshness statuses:

| Status | Meaning |
| --- | --- |
| `FRESH` | Source data is available and within the report's freshness expectation. |
| `STALE` | Source data is available but older than the expected freshness window. |
| `PARTIAL` | At least one source is current, but one or more requested source families are stale or incomplete. |
| `BACKFILLING` | Source data is intentionally rebuilding or replaying and may be incomplete. |
| `UNAVAILABLE` | Source data or freshness evidence could not be read. |

Materialized views and rollups must expose their own `refreshed_at` or equivalent source timestamp before they are used for tenant-facing reports.

## Export Rules

Exports are read-only report surfaces. They must:

- Enforce the same tenant, participant, dimension, date-window, pagination, and redaction rules as API responses.
- Include `report_type`, `metric_class`, filters, generated timestamp, freshness, and source warnings.
- Use safe derived statuses for partner/customer-facing exports.
- Exclude raw UCNs, provider payloads, settlement internals, secrets, token material, stored signing secrets, and raw audit payloads.
- Be auditable when persisted, downloaded, scheduled, or sent outside the immediate request.
- Declare retention and expiry for generated files when export storage is implemented.

Supported export formats should start with JSON and CSV unless a future implementation task justifies additional formats.

## Ledger Reconciliation Rules

Ledger-aware reports must preserve the liability model rules:

- Reward and distributor commission obligations are the source of `obligation_total`.
- Funding reservations, wallet movements, invoices, fulfilment records, and settlement rows are phase evidence over obligations, not new obligations.
- A downstream phase must point back to a source obligation or return missing/ambiguous evidence.
- Totals must be grouped by currency and liability category.
- Missing joins must produce source warnings or missing-evidence markers, not quiet zeroes.
- Operational timing differences between campaign/outcome events and settlement ledgers must be surfaced through freshness and source warnings.

Reconciliation status values:

| Status | Meaning |
| --- | --- |
| `MATCHED` | Ledger-backed totals reconcile across required source families for the requested scope. |
| `PARTIAL` | Some source families reconcile, but at least one requested family is missing, stale, or ambiguous. |
| `MISMATCHED` | Source totals conflict and require operator investigation. |
| `UNAVAILABLE` | Reconciliation could not be evaluated because a required source is unavailable. |
| `NOT_APPLICABLE` | The requested metric is operational or forecast-only and does not require ledger reconciliation. |

## API Direction

Future APIs may expose tenant analytics and operator analytics separately. TASK-024 does not add those routes.

Recommended route families for later tasks:

```text
GET /admin/analytics/reports/{report_type}?tenant_code=...
GET /v1/analytics/reports/{report_type}
POST /admin/analytics/exports
POST /v1/analytics/exports
```

Admin/operator surfaces may include operator-safe detail and internal tenant scope. External tenant surfaces must use credential-derived tenant scope and external references where available.

## Privacy And Redaction

Reports must not expose:

- Raw UCNs or private customer identifiers.
- Raw provider payloads or provider error text.
- Raw settlement exception internals.
- Funding account internals, wallet internals, or unrestricted ledger row metadata outside operator-safe reports.
- Access tokens, signing secrets, hashes, credentials, or webhook payload secrets.
- Raw audit payloads, raw DLQ payloads, or unrelated tenant data.

Operator reports may include source IDs and source statuses when needed for investigation, but must still avoid secrets and private identifiers unless a future support contract explicitly permits them.

## Validation Expectations

Future implementation tasks must add tests for:

- Tenant filter enforcement and cross-tenant rejection.
- Approved dimension validation and rejected unknown dimensions.
- Operational versus ledger-backed metric classification.
- Freshness block generation, stale data, partial data, and unavailable source handling.
- Export redaction, filter validation, row limits, and audit evidence where exports are persisted.
- Ledger reconciliation, currency grouping, reward/commission separation, and no-double-counting.
- Safe fulfilment, settlement, webhook, and partner/customer status mapping.

## Follow-Up Implementation Tasks

Later tasks should:

- Add a small read-only analytics service using this contract.
- Decide whether existing materialized views need freshness metadata before tenant-facing use.
- Add tenant-safe report APIs only after permission and query contracts are explicit.
- Add export APIs only after audit, retention, and redaction behavior are tested.
- Add frontend reporting screens only after backend report contracts are implemented and tested.

## Readback Validation

TASK-024 readback should confirm that this contract defines tenant-safe dimensions, tenant filters, freshness indicators, export rules, ledger reconciliation rules, operational-vs-ledger metric separation, source ownership, redaction boundaries, and future test expectations without adding schema, routes, migrations, frontend changes, or money movement.
