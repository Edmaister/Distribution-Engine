# API Surface Map

## Current API Groups

Current APIs are broad and operational. This map separates current facts from target DLaaS API recommendations.

| Group | Current routes | Auth pattern | Current purpose |
| --- | --- | --- | --- |
| Tenants | `/admin/tenants` | Admin key | Create/fetch tenant records. |
| Campaigns | `/campaigns`, campaign policy endpoints | Admin/partner patterns vary by route | Campaign creation, validation, track update, policy read/write. |
| Referrals | `/referrals/*`, `/public/referrals/validate` | Partner/public depending route | Issue referrer codes, bootstrap, accept terms, validate referrals, capture referee UCN. |
| Progress/events | `/v1/progress`, `/enterprise/events`, `/admin/enterprise-events`, `/worker/referral-events` | Partner/system/admin/worker | Ingest journey progress and enterprise events, queue/replay/inspect processing. |
| Rewards | `/rewards/apply`, `/v1/rewards/summary/*` | Admin/partner | Apply rewards and expose reward summaries. |
| Funding | `/admin/funding/*`, `/admin/marketplace-funding/sponsor-wallets`, `/admin/funding/contracts`, `/admin/funding/budget-governance` | Finance admin | Funding accounts, rules, reservations, limits, alerts, reconciliation, wallets, contracts, budgets. |
| Sponsor billing/portal | `/admin/funding/sponsor-billing/*`, `/v1/tenants/{tenant_code}/sponsors/{sponsor_code}/billing/*` | Finance admin/admin or partner | Sponsor utilisation invoices, payments, statements, wallet, contracts, forecasts. |
| Fulfilment/settlement | `/admin/fulfilment/*`, `/admin/settlements`, `/admin/settlement/*` | Finance admin | Fulfilment ops, settlement batches, approvals, exceptions, periods, certifications, reversals. |
| Distribution admin | `/admin/distribution/*` | Distribution admin | Distributors, wallets, commissions, opportunities, routing, governance, reporting. |
| Distribution portal | `/distribution/portal/*` | Admin/partner/distributor | Distributor profile, offers, accept/decline, wallets, ledger, conversions, performance. |
| Partner seam | `/oauth/token`, `/partner/*`, `/admin/partners/*` | Partner identity/admin | Client credentials, tokens, webhooks, delivery health, exceptions, retries, exports, readiness. |
| Admin operations | `/admin/audit`, `/admin/failures`, `/admin/dlq`, `/admin/reconciliation`, command centre routes | Admin/system/finance/distribution admin | Audit, failures, DLQ replay, reconciliation, command-centre aggregation. |
| Experience APIs | `/v1/experience/admin-command-centre`, `/v1/experience/sponsor`, distributor/consumer experience routes | Role-scoped keys/JWT | Backend-for-frontend aggregate views by role/workspace. |
| Session/auth | `/auth/session` | Session key/JWT/API key | Backend-confirmed role/workspace access metadata. |

## Target DLaaS API Surface

These are target-state recommendations. They are not current implementation facts unless matched above.

| API area | Target recommendation | Current wrap/reuse candidate | Trace |
| --- | --- | --- | --- |
| Accounts/tenants | Create account, tenant, environment, onboarding, lifecycle, membership context. | `tenants`, `tenant_service.py`, `/admin/tenants`. | GAP-01 |
| Campaigns | Stable campaign CRUD, lifecycle, readiness, config versioning, limits, policies. | `campaign_service.py`, campaign policy service/routes. | GAP-02 |
| Participants | Unified APIs for partners/referrers/distributors/sponsors/customers with role-specific views. | referral, distribution, sponsor, partner seam services. | GAP-03 |
| Links/codes | Issue, list, void, resolve, and inspect distribution links/codes. | referral codes, campaign referral links, route referral links. | GAP-04 |
| Attribution events | Public event ingestion and attribution diagnostics with idempotency. | progress/enterprise event APIs and inbox. | GAP-05, GAP-06 |
| Qualification | Evaluate and inspect qualification decisions from backend events. | journey/progress/campaign policy services. | GAP-07 |
| Rewards/commissions | Calculate, approve, fulfil, reverse, summarize; keep customer reward and distributor commission boundaries clear. | reward service, commission service, reward summary. | GAP-08 |
| Funding/budgets | Reserve, release, settle, forecast, alert, reconcile, expose liability and readiness. | funding and marketplace funding services. | GAP-09 |
| Fulfilment/settlement | Create/inspect fulfilment and settlement lifecycle records, batches, approvals, exceptions, reversals. | fulfilment and settlement services/routes. | GAP-10 |
| Webhooks | Subscribe to DLaaS event catalog, inspect delivery, retry, export dead letters. | partner seam. | GAP-13 |
| Analytics/reporting | Tenant-safe reports across campaigns, participants, attribution, reward, funding, settlement, webhook health. | distribution reporting, finance metrics, materialized views. | GAP-16 |
| Audit/support | Trace outcome, export audit, investigate stuck states, capture repair actions. | admin audit, failure, DLQ, outcome-money map. | GAP-11, GAP-14 |
| SaaS packaging | API keys, plans, usage, quotas, billing hooks. | partner clients are reusable only for integration credentials, not full SaaS packaging. | GAP-17 |

## API Design Rules

- Do not expose internal admin routes as public DLaaS APIs without a stable contract.
- Public APIs must define tenant scope, auth, idempotency, validation, events emitted, and error shape.
- Money-affecting APIs must emit audit evidence and reject duplicate commands.
- Partner/customer APIs must return safe derived statuses.
- Existing endpoints should be wrapped or versioned rather than renamed in-place unless a migration plan exists.

## Tenant Identifier Boundary

TASK-048 accepts `docs/sa/TENANT_IDENTIFIER_BOUNDARY_DECISION.md` as the API identifier boundary.

Current routes that expose `tenant_code` remain current implementation facts and backward-compatible surfaces. They are not the preferred target-state public contract.

Target DLaaS public APIs, partner APIs, webhooks, QR/distribution links, onboarding, SaaS setup, and white-label/embed surfaces should use credential-derived tenant scope, `external_tenant_ref`, or role-specific aliases such as `organisation_ref`, `producer_ref`, `partner_ref`, and `distributor_ref`.

Internal/admin/operator APIs and backend services may continue using resolved `tenant_code` for data isolation, audit, funding, fulfilment, settlement, and reporting.
