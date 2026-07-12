# Referral SaaS Reporting And Export Contract

TASK ID: TASK-142

Product boundary: Referral Management and Campaign Attribution SaaS.

Status: Contract complete. TASK-156 adds the first service-layer report catalog
helper for `campaign_performance`; TASK-157 adds the first read-only product
route wrapper; TASK-158 adds bounded identity-derived tenant scope for that
route; TASK-159 adds `referral_funnel` as the second bounded report type with
partial-source coverage warnings; TASK-160 adds `progress_event_health` over
tenant-scoped progress event and failure evidence; TASK-161 adds
`attribution_quality` as a derived aggregate report over tenant-scoped
referral, campaign-link, and route-link evidence. Export jobs, frontend, full
SaaS account membership resolution, permission changes, and storage remain
unimplemented.

## Boundary

This contract defines tenant-safe Referral SaaS reporting and export behavior
for campaign, referral, link/code, progress, attribution, safe-status, and
operational conversion evidence.

Required boundary docs checked:

- `docs/product/README.md`
- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/README.md`
- `docs/roadmap/referral-saas/ROADMAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_ATTRIBUTION_TRACE_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_SAFE_STATUS_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_E2E_LIVE_VERIFICATION_PLAN.md`
- `docs/sa/TENANT_SAFE_ANALYTICS_REPORTING_CONTRACT.md`

Source files inspected:

- `services/tenant_safe_analytics_service.py`
- `apps/api/routers/admin_analytics.py`
- `services/distribution/reporting_service.py`
- `apps/api/routers/distribution/admin_reporting.py`
- `test/test_tenant_safe_analytics_service.py`
- `test/api/test_admin_analytics_api.py`
- `test/api/distribution/test_admin_reporting_api.py`

## Purpose

Referral SaaS needs reports that answer:

1. Which campaigns, referral links/codes, progress events, and attribution
   outcomes are performing?
2. Which referrals are validated, in progress, completed, missing evidence, or
   blocked?
3. What can a tenant safely export without leaking raw UCNs, provider payloads,
   audit payloads, operator-only trace internals, or broader DLaaS money state?

The repository already has tenant-safe analytics and distribution reporting
foundations. TASK-142 defines the focused Referral SaaS report/export contract
that should use those foundations without creating a parallel analytics stack.

## Current Implementation Facts

Current tenant-safe analytics service:

- `services.tenant_safe_analytics_service.get_tenant_safe_analytics_report`
- supports `distribution_overview`
- supports `reconciliation_summary`
- validates report type, dimensions, filters, tenant code, and data windows
- redacts sensitive filter names such as UCN, raw, token, secret, provider
  payload, and audit payload
- returns a reporting envelope with report type, tenant scope, filters,
  dimensions, metric class, metrics, data window, generated timestamp,
  freshness, source warnings, redactions, and reconciliation status
- classifies `distribution_overview` as `OPERATIONAL`
- classifies `reconciliation_summary` as `LEDGER_BACKED`

Current admin analytics route:

- `GET /admin/analytics/reports/{report_type}`
- implemented in `apps/api/routers/admin_analytics.py`
- requires admin-style analytics roles
- returns a read-only guardrail
- does not create exports, invoices, billing events, or mutate funding,
  settlement, fulfilment, reward, commission, audit, tenant, or analytics
  records

Current distribution reporting service:

- `services.distribution.reporting_service`
- provides marketplace overview, opportunity performance, distributor
  performance, attribution exceptions, governance reporting, and producer
  conversion journeys
- includes useful Referral SaaS evidence such as campaign code, referral counts,
  linked/completed conversions, attribution rate, progress fields, and
  attribution exceptions
- also includes broader DLaaS fields such as distributor commissions, wallets,
  governance, opportunities, budgets, and disputes

Current distribution reporting routes:

- `GET /admin/distribution/reporting/overview`
- `GET /admin/distribution/reporting/opportunities`
- `GET /admin/distribution/reporting/distributors`
- `GET /admin/distribution/reporting/attribution-exceptions`
- `GET /admin/distribution/reporting/governance`

These are admin distribution reports, not a focused Referral SaaS tenant report
or export API.

## First-Launch Report Types

Referral SaaS should start with operational, tenant-safe reports:

| Report type | Purpose | Metric class |
|---|---|---|
| `campaign_performance` | Campaign referral volume, validation, progress, completion, attribution, and safe status by campaign. | `OPERATIONAL` |
| `referral_funnel` | Referral journey counts from code issued/validated through progress milestones and completion. | `OPERATIONAL` |
| `link_code_performance` | Referral code/link issued/resolved/linked/expired/invalid states by source type and campaign. | `OPERATIONAL` |
| `progress_event_health` | Progress event received/deduped/rejected/failed counts and freshness by event family. | `OPERATIONAL` |
| `attribution_quality` | Complete, partial, missing, inconsistent, unavailable, and unattributed outcome counts. | `DERIVED_STATUS` |
| `safe_status_distribution` | Referrer/customer safe status counts and action-required categories. | `DERIVED_STATUS` |
| `reward_visibility_summary` | Optional visible reward summary counts where already supported. | `OPERATIONAL` unless money totals are later ledger-backed |

First launch should not include:

- distributor commission settlement
- wallet balances
- funding account operations
- fulfilment provider routing internals
- settlement batches
- sponsor billing
- invoices
- payout status
- raw operator trace exports

## Required Report Envelope

Referral SaaS reporting should reuse the tenant-safe analytics envelope:

```json
{
  "reportType": "campaign_performance",
  "tenantScope": "internal-or-derived-scope",
  "externalTenantRef": "safe-account-ref",
  "filters": {
    "campaignRef": "campaign-safe-ref",
    "dataWindowStart": "ISO-8601",
    "dataWindowEnd": "ISO-8601"
  },
  "dimensions": ["campaign_ref", "safe_status", "metric_name"],
  "metricClass": "OPERATIONAL",
  "metrics": [],
  "generatedAt": "ISO-8601",
  "freshness": {},
  "sourceWarnings": [],
  "redactions": [],
  "reconciliationStatus": "NOT_APPLICABLE"
}
```

API wrappers may use camelCase. Service-layer contracts may use snake_case.
The meaning must remain the same.

## Approved Dimensions

First-launch Referral SaaS dimensions:

| Dimension family | Approved dimensions |
|---|---|
| Account/campaign | `external_tenant_ref`, `campaign_ref`, `campaign_code` for operator/internal reports, `campaign_status`, `product`, `sub_product`, `journey_code`, `journey_version` |
| Referral | `safe_referral_ref`, `safe_status`, `progress_band`, `next_milestone`, `validation_state`, `completion_state` |
| Link/code | `source_type`, `link_code_status`, `issued_period`, `resolved_period`, `campaign_ref` |
| Progress | `event_family`, `event_type`, `ingestion_state`, `dedupe_state`, `source_system`, `freshness_bucket` |
| Attribution | `trace_status`, `source_confidence`, `attribution_source`, `missing_evidence_code`, `warning_code` |
| Safe status | `viewer_role`, `safe_status`, `action_category`, `terminal` |
| Export | `export_format`, `redaction_profile`, `freshness_status` |

Restricted or operator-only dimensions:

- internal `tenant_code`
- raw `referral_track_id`
- raw `campaign_track_id`
- raw source table names
- raw audit correlation IDs
- operator-only missing-evidence source details

Forbidden dimensions:

- raw UCNs
- raw customer identifiers
- provider payloads
- secrets, tokens, signing material, API keys
- raw audit payloads
- DLQ payloads
- settlement internals
- funding account identifiers

## Core Metrics

Recommended first-launch operational metrics:

- `campaigns.active_count`
- `campaigns.ready_count`
- `referrals.code_issued_count`
- `referrals.validated_count`
- `referrals.recovery_required_count`
- `referrals.in_progress_count`
- `referrals.completed_count`
- `referrals.cancelled_count`
- `progress.events_recorded_count`
- `progress.events_deduped_count`
- `progress.events_rejected_count`
- `progress.events_failed_count`
- `attribution.traced_count`
- `attribution.complete_count`
- `attribution.partial_count`
- `attribution.missing_evidence_count`
- `attribution.inconsistent_count`
- `attribution.unavailable_count`
- `status.action_required_count`
- `status.unavailable_count`
- `conversion.validation_rate`
- `conversion.completion_rate`
- `conversion.attribution_rate`

Metric rules:

- every metric must declare `metric_class`
- operational conversion rates must not be presented as ledger-backed money
  totals
- missing joins must produce `sourceWarnings` or missing-evidence metrics, not
  quiet zeroes
- reward visibility counts may appear, but reward money totals need a later
  money-flow contract if they are treated as ledger-backed

## Freshness Rules

Every report and export must include freshness evidence:

- generated time
- data window start and end
- source-as-of timestamp when known
- source family freshness
- lag seconds when calculable
- `FRESH`, `STALE`, `PARTIAL`, `BACKFILLING`, or `UNAVAILABLE`

Referral SaaS source families should include:

- `campaign`
- `referral`
- `link_code`
- `progress`
- `attribution`
- `safe_status`
- `reward_summary` when included

If progress or attribution sources are stale or unavailable, the report must
show `PARTIAL` or `UNAVAILABLE` rather than hiding the issue.

## Export Contract

Exports are read-only report outputs. First-launch export formats:

- JSON
- CSV

Export rules:

- apply the same tenant, participant, filter, dimension, date-window, row-limit,
  redaction, and freshness rules as API reports
- include report type, generated timestamp, data window, freshness, source
  warnings, redactions, and metric class
- export only safe identifiers and derived statuses for tenant-facing exports
- do not export operator trace evidence unless the export is explicitly
  operator-only and covered by a later support workflow contract
- do not export raw UCNs, tenant internals for public views, provider payloads,
  raw audit payloads, DLQ payloads, secrets, tokens, funding account internals,
  settlement internals, wallet internals, invoices, or payout details
- persisted, scheduled, or externally delivered exports require audit,
  retention, expiry, and access-control behavior in a later implementation task

TASK-142 does not implement export APIs or storage.

## Candidate API Direction

Future product route family:

```text
GET /referral-saas/reports/{report_type}
POST /referral-saas/reports/{report_type}/exports
GET /referral-saas/exports/{export_id}
```

Current admin route foundation:

```text
GET /admin/analytics/reports/{report_type}
```

Required future behavior:

- tenant/account scope must derive from authenticated SaaS account context
- operator/admin reports may use explicit tenant filters
- partner/customer/referrer reports must apply role and participant scope before
  returning data
- export requests must be validated before any data is produced
- reads must be side-effect free
- persisted exports must be audited

## Current Surface Gaps

Current code gives useful reporting foundations, but not the complete Referral
SaaS reporting product:

- TASK-156 defines the first Referral SaaS report catalog helper for
  `campaign_performance`; TASK-159 adds `referral_funnel` using current
  tenant-safe distribution overview evidence. Deeper stage metrics for
  code-issued, validation-state, and progress milestones still need dedicated
  report sources. TASK-160 adds `progress_event_health` using
  `referral_progress_events` and tenant-scoped `referral_event_failures` rows,
  with partial coverage for deduped/rejected states. TASK-161 adds
  `attribution_quality` as an aggregate derived-status report. It does not
  expose raw outcome trace payloads. `safe_status_distribution` remains
  unimplemented.
- `admin_analytics` is admin/internal and requires explicit `tenant_code`; it is
  not a SaaS account-facing report API.
- distribution reporting includes useful attribution and conversion metrics, but
  it also includes broader DLaaS distributor, commission, wallet, governance,
  budget, dispute, and opportunity fields that are outside first-launch Referral
  SaaS reporting.
- export APIs, export storage, audit, retention, and scheduled delivery are not
  implemented by the current reporting foundation.

These are product packaging and report-catalog gaps, not evidence that the
underlying referral/campaign/progress/attribution data is missing.

## Future Tests

When this contract becomes implementation work, add or preserve tests for:

- supported Referral SaaS report types
- rejected unsupported report types
- approved and rejected dimensions
- tenant/account scope derived from identity
- cross-tenant rejection and safe 403/404 behavior
- date-window validation and row limits
- freshness blocks for fresh, stale, partial, and unavailable sources
- redaction of raw UCNs, provider payloads, audit payloads, secrets, tokens,
  DLQ payloads, funding account fields, and settlement internals
- export format validation, export redaction, and export row limits
- attribution/source-warning counts do not disappear as zeroes
- operational metrics remain separate from ledger-backed money totals

## Explicit Non-Goals

- no schema, migration, service, route, export, frontend, permission, or test
  implementation
- no materialized view or rollup job implementation
- no live DB access
- no billing, invoice, payout, settlement, funding, fulfilment, commission, or
  sponsor billing reporting implementation
- no public export storage, retention, scheduling, or delivery implementation
- no exposure of raw operator attribution trace or link/code inspect evidence
  to tenant/customer-facing reports
- no mutation, repair, retry, replay, fulfilment, settlement, payout, invoice,
  webhook dispatch, or notification action

## Readiness Decision

Referral SaaS has reporting foundations in tenant-safe analytics and
distribution reporting, but first-launch SaaS reporting still needs a focused
report catalog, product route/API wrapper, export validation, and redaction
tests. TASK-142 defines that contract while preserving the shared analytics
foundation and keeping broader DLaaS money/reporting scope separate.

TASK-156 implementation update: `services/referral_saas_reporting_service.py`
now defines the first report catalog helper and supports
`campaign_performance` by adapting the existing `distribution_overview`
tenant-safe analytics source into product-safe operational metrics.

TASK-157 implementation update: `GET /v1/referral-saas/reports/{report_type}`
now exposes the report helper through a read-only product wrapper. It currently
requires an approved report-reader/admin role.

TASK-158 implementation update: the report wrapper can derive tenant scope from
the authenticated identity when the identity is already tenant-scoped. Internal
report-reader/admin identities still require explicit `tenant_code` until full
SaaS account membership scope exists.

TASK-159 implementation update: `referral_funnel` is now available through the
same report helper and read-only route. It maps the current tenant-safe
distribution overview source to safe funnel metrics and returns a
`PARTIAL_SOURCE_COVERAGE` warning until dedicated code-issued,
validation-state, and progress-milestone stage sources are implemented.

TASK-160 implementation update: `progress_event_health` is now available
through the same report helper and read-only route. It reads tenant-scoped
`referral_progress_events` and `referral_event_failures`, reports recorded,
failed, retry-attempt, open-failure, and resolved-failure counts, excludes
failure rows that cannot be tenant-scoped, and returns partial-source warnings
for deduped/rejected counts until those states are persisted in reportable
form.

TASK-161 implementation update: `attribution_quality` is now available through
the same report helper and read-only route. It derives aggregate
`COMPLETE`, `PARTIAL`, `MISSING_EVIDENCE`, `INCONSISTENT`, and `UNATTRIBUTED`
trace-status counts from tenant-scoped `referral_instances`,
`campaign_referral_links`, `campaign_attributions`, and
`distribution_route_referral_links` evidence. Raw outcome trace payloads,
operator-only evidence, exports, retention, scheduling, storage, and frontend
screens remain explicit follow-up work.
