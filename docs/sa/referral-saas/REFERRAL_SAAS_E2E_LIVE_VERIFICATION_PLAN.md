# Referral SaaS E2E And Live Verification Plan

TASK ID: TASK-147

Product boundary: Referral Management and Campaign Attribution SaaS.

Status: Contract/plan only. No runtime tests, schema changes, live database
queries, or route smoke tests are executed by this task.

## Purpose

Referral SaaS already has meaningful backend primitives for referral code
creation, validation, progress ingestion, campaign attribution, link/code
inspection, and outcome trace. The remaining production-confidence gap is not
greenfield feature creation. It is proof that the focused product can run as one
tenant-safe journey:

```text
account context -> campaign -> referral code/link -> validation ->
progress event -> attribution trace -> safe status/reporting evidence
```

This plan defines the E2E suite, route smoke checks, and live DB/state
verification needed to prove that journey before calling the focused SaaS wedge
production-ready.

## Boundary Rules

- Use existing platform primitives instead of creating a parallel Referral SaaS
  implementation.
- Keep live checks read-only unless a local or staging environment has isolated
  seeded test data and explicit approval for mutating smoke routes.
- Do not include DLaaS money flows in this plan. Rewards, funding, fulfilment,
  settlement, commissions, sponsor billing, and marketplace depth remain
  separate DLaaS expansion work.
- Do not invent statuses, fields, routes, or product promises. Validate against
  database migrations, service code, router code, and existing tests.
- Treat production verification as evidence gathering only. No production
  repair, replay, retry, write, update, delete, approval, settlement, or
  fulfilment action belongs in this task.

## Current Source-Backed Facts

The focused product already has test and implementation coverage in these
areas:

| Area | Current evidence |
|---|---|
| Referral code issue/reuse | `services/referral_code.py`, `apps/api/routers/referrals.py`, `test/test_referral_code.py`, `test/test_referrals_api.py` |
| Referral validation and UCN capture | `apps/api/routers/referrals.py`, `apps/api/schemas/referrals.py`, `dp/migrations/001_init.sql`, `dp/migrations/006_qr_scans.sql`, `test/test_referrals_api.py` |
| Progress event ingestion | `apps/api/routers/progress.py`, `services/progress_service.py`, `services/journey_orchestrator.py`, `dp/migrations/013_progress_events.sql`, `test/test_progress_service.py`, `test/test_progress_api.py` |
| Campaign setup/readiness | `services/campaign_service.py`, `services/campaign_readiness_service.py`, `services/campaign_policy_service.py`, `test/test_campaign_service.py`, `test/api/test_campaign_readiness_api.py` |
| Attribution and journey evidence | `services/outcome_trace_service.py`, `apps/api/routers/admin_outcomes.py`, `test/test_outcome_trace_service.py`, `test/test_distribution_attribution_journey_contract.py` |
| Link/code inspection | `services/link_code_service.py`, `test/test_link_code_service.py`, `test/api/test_admin_links_api.py` |
| Enterprise/event diagnostics | `dp/migrations/061_enterprise_event_inbox.sql`, `test/test_enterprise_events_api.py`, `test/test_enterprise_event_inbox_admin.py` |
| Tenant-safe reporting foundation | distribution reporting and tenant analytics tests, including `test/api/distribution/test_admin_reporting_api.py` and `test/test_tenant_safe_analytics_service.py` when present in the active test tree |

This plan does not replace those tests. It turns them into one launch-readiness
verification path.

## E2E Test Plan

### E2E-001: Account Context And Tenant Isolation

Goal: prove a SaaS account context can drive the existing tenant-scoped
referral and campaign behavior.

Required assertions:

- request context maps to one tenant without exposing raw internal tenant
  identifiers in customer-facing responses
- partner/referrer identity is redacted or hashed according to the relevant
  route contract
- cross-tenant campaign, code, progress, and trace access is rejected or empty
- product wrapper gaps are documented until TASK-134 implementation work exists

Environment: local and CI first; staging after product wrapper routes exist.

### E2E-002: Campaign Setup And Readiness

Goal: prove a tenant can create or select a campaign, inspect readiness, and
resolve readiness blockers before referral traffic is launched.

Required assertions:

- campaign identity and campaign track identity stay distinct
- readiness returns deterministic checks for required campaign data
- policy presence/version evidence is visible where the contract requires it
- invalid or inactive campaign states do not accept attribution as launch-ready
- no marketplace, commission, funding, fulfilment, or settlement behavior is
  implied by campaign readiness

Candidate current tests:

- `test/test_campaigns.py`
- `test/test_campaign_service.py`
- `test/test_campaign_policy_service.py`
- `test/test_campaign_readiness_service.py`
- `test/api/test_campaign_readiness_api.py`

### E2E-003: Referral Code Issue And Reuse

Goal: prove referral code issue/reuse works as a tenant-safe product command.

Required assertions:

- accepted terms are required before issue
- repeated issue for the same source identity reuses the correct existing code
  according to the current source-of-truth behavior
- preferred handle conflicts fail safely
- raw UCN/customer identifiers are not returned
- global uniqueness constraints on `referrer_codes` are either accepted as a
  launch constraint or resolved by a later implementation task before claiming
  tenant-local code reuse

Candidate current tests:

- `test/test_referral_code.py`
- `test/test_referrals_api.py`

### E2E-004: Public Validation And Recovery

Goal: prove a referred customer can validate a code/link and receive a safe
recovery state when validation cannot complete.

Required assertions:

- valid code creates or returns referral-instance evidence
- terms, alias, campaign, and source validation failures are safe and stable
- QR scan evidence is written when the current route/service path says it is
- `REFERRAL_LOG_FAILED` style recovery states are mapped to product-safe
  messages without leaking internal fraud, audit, or provider details
- duplicate validation behavior is documented before it is presented as
  idempotent

Candidate current tests:

- `test/test_referrals_api.py`
- `test/test_link_code_service.py`

### E2E-005: Progress Event Ingestion

Goal: prove product progress events can be recorded, deduped, queued, and traced
without forking the shared `/v1/progress` primitive.

Required assertions:

- valid progress event inserts `referral_progress_events` evidence
- duplicate source event or dedupe key returns the documented dedupe outcome
- invalid journey, product, sub-product, self-referral, or identifier payload is
  rejected safely
- payload hash and source event identity can support audit/replay diagnosis
- downstream queueing emits only the expected platform event boundary
- non-banking event-name requirements are checked against the live DB
  `chk_rpe_event_type` constraint before broader SaaS event catalogs are
  promised

Candidate current tests:

- `test/test_progress_service.py`
- `test/test_progress_api.py`
- `test/test_journey_orchestrator.py`

### E2E-006: Attribution Trace

Goal: prove the operator/admin trace can explain how campaign, referral, link,
route, validation, and progress evidence did or did not produce attribution.

Required assertions:

- trace resolves from `referral_track_id`
- trace includes outcome, participant, attribution, source-link, route-link, and
  progress-event evidence where present
- missing evidence is classified instead of hidden
- cross-tenant trace access is rejected or empty
- trace responses are redacted for customer identifiers and raw payloads
- conflicting link/code/route evidence is visible enough for operator workflow
  tasks to handle later

Candidate current tests:

- `test/test_outcome_trace_service.py`
- `test/api/test_admin_outcomes_api.py`
- `test/test_distribution_attribution_journey_contract.py`

### E2E-007: Reporting And Safe Status Handoff

Goal: define what the E2E suite must prove once TASK-141 and TASK-142 contracts
exist.

Required assertions after those tasks:

- customer/referrer status uses safe product language rather than raw internal
  states
- reporting totals reconcile to referral, campaign, progress, and attribution
  source evidence
- tenant filters are mandatory for SaaS reporting views
- export freshness and redaction rules are enforced

This is a handoff placeholder, not a reporting implementation requirement for
TASK-147.

### E2E-008: Negative And Cross-Tenant Suite

Goal: prove failures are safe, explainable, and tenant-isolated.

Required assertions:

- unknown referral code
- expired or inactive campaign
- missing accepted terms
- duplicate source event
- mismatched product/sub-product/journey
- self-referral
- cross-tenant code/campaign/trace/report access
- malformed payload
- missing attribution evidence
- unexpected live state value

Each failure must have a stable product outcome, a support/operator diagnostic
path, or an explicit follow-up task.

## Live DB/State Verification Plan

Live verification must follow `docs/sa/LIVE_DB_STATE_VERIFICATION_CHECKLIST.md`.
For the Referral SaaS wedge, the minimum read-only checks are:

| Area | Tables or evidence to verify |
|---|---|
| Account/tenant context | `tenants` and any product wrapper tables introduced by later implementation work |
| Referral code issue | `referrer_codes`, uniqueness constraints, handle/terms columns, tenant indexes |
| Validation | `referral_instances`, `referral_qr_scans`, status constraints, referral track identifiers |
| Progress | `referral_progress_events`, dedupe/source-event indexes, payload hash, event-type constraint |
| Recovery/failure | `referral_event_failures`, retry/failure status fields, dedupe constraints |
| Audit | `referral_processing_audit`, `admin_audit_log` where operator/admin routes are used |
| Campaign | `marketing_campaigns`, `marketing_campaign_policies`, campaign status and policy evidence |
| Attribution | `campaign_attributions`, `campaign_track_events`, campaign/referral track identifiers |
| Link/code trace | `campaign_referral_links`, `distribution_route_referral_links` |
| Enterprise/event diagnostics | `enterprise_event_inbox`, dedupe key, processing status, source event indexes |

Minimum state checks:

- `referral_instances.status` actual values and DB/service allowed values
- `referral_progress_events.event_type` actual values and DB/service allowed
  values
- `referral_event_failures.status` actual values and retry posture
- `referral_qr_scans.status` actual values and constraint
- `campaign_attributions.status` actual values and constraint
- `enterprise_event_inbox.processing_status` actual values and constraint
- `distribution_route_referral_links.link_status` actual values and constraint

Minimum index/constraint checks:

- `referrer_codes` referral code, referrer hash, gaming handle, and tenant lookup
  posture
- `referral_progress_events` dedupe/source-event uniqueness
- `referral_event_failures` source event and dedupe uniqueness
- `campaign_referral_links.referral_track_id` uniqueness
- `distribution_route_referral_links.referral_track_id` uniqueness
- `enterprise_event_inbox.dedupe_key` uniqueness
- tenant/campaign/referral track lookup indexes used by smoke routes

## Route Smoke Selection

Do not invent routes. Select mounted routes from the active application before
execution.

Candidate Referral SaaS smoke routes:

| Route family | Method | Safe environments | Expected write? |
|---|---|---|---|
| `/referrals/codes` | POST | local/staging seeded tenant only | Yes |
| `/public/referrals/validate` | POST | local/staging seeded tenant only | Yes |
| `/referrals/referees/ucn` | POST | local/staging seeded tenant only | Yes |
| `/v1/progress` | POST | local/staging seeded tenant only | Yes |
| `/campaigns` route family | POST/GET as mounted | local/staging seeded tenant only for writes; read-only GET can be broader | Depends on route |
| `/admin/campaigns/{campaign_code}/readiness` | GET | local/staging/production read-only where auth permits | No |
| `/admin/outcomes/{referral_track_id}/trace` | GET | local/staging/production read-only with redacted evidence | No |
| `/admin/links` or equivalent mounted link/code inspection route | GET | local/staging/production read-only with redacted evidence | No |
| reporting routes from TASK-142 | GET | after contract exists | No |

Production smoke tests are read-only only. Mutating smoke routes are local or
staging only and must use seeded test data with explicit correlation IDs.

## Launch Confidence Exit Criteria

Referral SaaS should not be rated as production-ready until all of the following
are true:

- focused E2E golden path passes from account context through attribution trace
- focused negative suite proves safe failure handling and tenant isolation
- clean DB migration replay passes
- live or staging schema verification confirms required tables, columns,
  statuses, constraints, and indexes
- route smoke checks are selected from mounted routers and classified by safety
- progress event-name constraints are compatible with the SaaS event catalog
- attribution trace redaction is verified
- reporting and safe-status E2E checks are added after TASK-141 and TASK-142
- unresolved source/schema mismatches are recorded as ordered follow-up tasks

## Implementation Slices

1. Create seeded local/CI fixtures for the Referral SaaS golden path.
2. Add a focused E2E test for campaign readiness -> code issue -> validation.
3. Extend the E2E test through progress ingestion and attribution trace.
4. Add negative/cross-tenant/redaction E2E cases.
5. Add a read-only schema/status/index verification script or checklist runner
   for staging/live evidence.
6. Add route smoke documentation generated from mounted routers.
7. Add reporting and safe-status assertions after TASK-141 and TASK-142.

## Explicit Non-Goals

- no schema, migration, service, API, frontend, or test implementation in this
  task
- no live DB access or credential discovery
- no production writes or repair actions
- no reward, funding, fulfilment, settlement, commission, sponsor billing, or
  marketplace-depth verification
- no replacement of existing referral, progress, campaign, or attribution
  primitives

## Readiness Decision

TASK-147 completes the plan for proving the focused Referral SaaS product
journey. It does not make the product production-ready by itself. It moves the
roadmap from "we have strong components" to "we know exactly what evidence is
required to call the wedge production-ready."
