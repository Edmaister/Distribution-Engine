# Frontend API Contract Map

This document maps the first frontend surfaces to the existing API. It is a
product/API bridge, not a visual design specification. Branding, layout,
navigation styling, and component design remain open.

See `docs/FRONTEND_BUILD_PLAN.md` for the implementation route, folder
structure, shared components, and phased build plan.

## Frontend Surfaces

| Surface | Primary users | Auth expected today | Status |
| --- | --- | --- | --- |
| Admin Console | Platform operations, finance, distribution, system admins | Platform/scoped admin API keys | Backend-ready |
| Sponsor Portal | Sponsor users and tenant partners | Partner/admin API key with tenant scoping | Backend-ready for read-only billing/funding views |
| Distributor Portal | Distributor users or partner-side distributor reps | Partner/admin API key plus tenant/distributor query params | Backend-ready for current portal flows |

## Shared Frontend Requirements

Every frontend shell should provide:

- Environment health indicator from `GET /health` and `GET /readyz`.
- Session role handling for platform admin, finance admin, distribution admin,
  system admin, partner, and tenant-scoped access.
- Standard API error handling for `401`, `403`, `404`, and validation errors.
- Tenant selector for admin users.
- Date range, status, tenant, sponsor, distributor, and limit filters where
  supported by the API.
- Audit-friendly correlation display where backend responses include IDs.

Current auth is API-key based. A production frontend should later sit behind
OAuth2/OIDC or another user identity layer and exchange user identity for the
appropriate backend access model.

## Admin Console

### Operations Home

Purpose: show whether the platform is alive and whether required schemas are
ready.

| UI area | Endpoint | Inputs | Uses |
| --- | --- | --- | --- |
| Service status | `GET /health` | none | Overall status and dependency health |
| Readiness detail | `GET /readyz` | none | Schema groups: foundation, funding, distribution, multi-currency, admin audit |
| Metrics link | `GET /metrics` | none | Prometheus scrape output; usually linked, not rendered directly |

Gap: user-friendly uptime/SLO dashboard is not yet a dedicated JSON API. Metrics
exist, but a UI would either query Prometheus/Grafana or need a backend summary
endpoint.

### Enterprise Events

Purpose: operate IDS/Hogan event ingestion, problem review, and replay.

| UI area | Endpoint | Inputs | Uses |
| --- | --- | --- | --- |
| Event summary cards | `GET /admin/enterprise-events/summary` | optional filters | Counts by processing status |
| Event dashboard | `GET /admin/enterprise-events/dashboard` | `days`, `problemLimit` | Source/event/status breakdown and recent problem events |
| Event list | `GET /admin/enterprise-events` | status/source/event filters, `limit` | Inbox table |
| Replay action | `POST /admin/enterprise-events/{inbox_event_id}/replay` | `dryRun` | Dry-run or queue a normalized event |

Gap: no frontend-friendly bulk replay endpoint yet. Current replay is one event
at a time, which is safer for the first UI.

### Admin Audit

Purpose: show sensitive admin activity and audit health.

| UI area | Endpoint | Inputs | Uses |
| --- | --- | --- | --- |
| Audit summary | `GET /admin/audit/summary` | `hours`, `action_domain`, `tenant_code` | Totals by domain, status, top action types |
| Audit log | `GET /admin/audit` | domain/type/tenant/target filters, `limit` | Searchable activity table |
| Audit health | `GET /metrics` | none | `admin_audit_writes_total` success/failure trends |

Gap: no CSV/export endpoint yet. The list API is sufficient for UI browsing.

### Funding And Sponsor Finance

Purpose: manage sponsor funding, billing, forecasts, VAT, payments, and
governance.

| UI area | Endpoint | Inputs | Uses |
| --- | --- | --- | --- |
| Funding dashboard | `GET /admin/funding/dashboard` | optional filters | Portfolio funding overview |
| Tenant funding dashboard | `GET /admin/funding/dashboard/{tenant_code}` | tenant | Tenant funding overview |
| Account funding detail | `GET /admin/funding/dashboard/{tenant_code}/{account_id}` | tenant/account | Account-level funding state |
| Funding exposure | `GET /admin/funding/exposure` | filters | Exposure summary |
| Funding limits | `GET /admin/funding/limits` | filters | Limit table |
| Create/update limits | `POST /admin/funding/limits`, `PUT /admin/funding/limits/{limit_id}` | limit payload | Limit administration |
| Funding rules | `GET /admin/funding/rules`, `POST /admin/funding/rules`, `PUT /admin/funding/rules/{rule_id}` | rule payload | Funding rule management |
| Funding audit | `GET /admin/funding/audit` | filters | Funding-specific audit trail |
| Reconciliation | `POST /admin/funding/reconciliation/run`, `GET /admin/funding/reconciliation` | run/filter params | Funding reconciliation |
| Reconciliation exceptions | `GET /admin/funding/reconciliation/exceptions`, `POST /admin/funding/reconciliation/exceptions/{exception_id}/resolve` | status/resolution | Exception work queue |
| Forecasts | `GET /admin/funding/forecast`, `GET /admin/funding/sponsor-forecast`, `GET /admin/funding/settlement-exposure-forecast` | tenant/sponsor/currency/date filters | Forecast widgets |
| Alerts | `GET /admin/funding/alerts`, `POST /admin/funding/alerts/run`, `POST /admin/funding/alerts/{alert_id}/acknowledge`, `POST /admin/funding/alerts/{alert_id}/resolve` | filters/action payloads | Alert queue |
| Sponsor wallets | `GET /admin/marketplace-funding/sponsor-wallets`, `POST /admin/marketplace-funding/sponsor-wallets`, `POST /admin/marketplace-funding/sponsor-wallets/{wallet_id}/topup` | sponsor/wallet payloads | Sponsor wallet ops |
| Wallet ledger | `GET /admin/marketplace-funding/sponsor-wallets/{wallet_id}/ledger` | wallet ID | Ledger drawer |
| Funding contracts | `GET /admin/funding/contracts`, `POST /admin/funding/contracts`, lifecycle endpoints | contract payloads | Contract management |

### Sponsor Billing

Purpose: create, issue, collect, reverse, report, and monitor invoices.

| UI area | Endpoint | Inputs | Uses |
| --- | --- | --- | --- |
| Invoice list | `GET /admin/funding/sponsor-billing/invoices` | tenant/sponsor/status/limit | Invoice table |
| Invoice detail | `GET /admin/funding/sponsor-billing/invoices/{invoice_id}` | invoice ID | Invoice detail view |
| Create invoice | `POST /admin/funding/sponsor-billing/invoices` | invoice + line payload | Manual invoice |
| Generate invoice | `POST /admin/funding/sponsor-billing/invoices/generate-from-utilisation` | tenant/sponsor/period | Utilisation billing |
| Scheduled generation | `POST /admin/funding/sponsor-billing/scheduled-generation` | dry-run/issue flags | Batch preview/execution |
| Issue invoice | `POST /admin/funding/sponsor-billing/invoices/{invoice_id}/issue` | invoice ID | Status action |
| Record payment | `POST /admin/funding/sponsor-billing/invoices/{invoice_id}/payments` | payment payload | Invoice payment |
| Payment receipts | `POST /admin/funding/sponsor-billing/payment-receipts`, `GET /admin/funding/sponsor-billing/payment-receipts/{receipt_id}` | receipt payload/ID | Receipt allocation |
| Reversals | `POST /admin/funding/sponsor-billing/payments/{payment_id}/reversals`, `POST /admin/funding/sponsor-billing/payment-allocations/{allocation_id}/reversals` | reversal payload | Correction flow |
| Statements | `GET /admin/funding/sponsor-billing/statements` | tenant/sponsor/period/currency | Statement view |
| Dashboard | `GET /admin/funding/sponsor-billing/dashboard` | tenant/sponsor/period/currency | Billing KPI cards |
| VAT report | `GET /admin/funding/sponsor-billing/vat-report` | tenant/period/currency | VAT reporting |

Gap: invoice PDF/download is not yet a dedicated endpoint. UI can render invoice
detail first; export can be added later.

### Distribution Marketplace Admin

Purpose: manage distributors, opportunities, routing, commissions, wallets,
governance, and reporting.

| UI area | Endpoint | Inputs | Uses |
| --- | --- | --- | --- |
| Distributor list | `GET /admin/distribution/distributors` | tenant/status/type filters | Distributor table |
| Distributor create/detail | `POST /admin/distribution/distributors`, `GET /admin/distribution/distributors/{distributor_id}` | profile payload/ID | Onboarding and detail |
| Distributor lifecycle | `POST /admin/distribution/distributors/{distributor_id}/activate`, `/suspend`, `/terminate` | reason/action payloads | Status actions |
| Distributor wallets | `GET /admin/distribution/distributor-wallets`, `GET /admin/distribution/distributor-wallets/{wallet_id}` | filters/ID | Wallet table/detail |
| Wallet movements | `/credit`, `/hold`, `/release-hold`, `/payout`, `/reverse` under `/admin/distribution/distributor-wallets/{wallet_id}` | movement payloads | Wallet operations |
| Wallet ledger | `GET /admin/distribution/distributor-wallets/{wallet_id}/ledger` | wallet ID | Ledger drawer |
| Commission rules | `GET /admin/distribution/commissions/rules`, `POST /admin/distribution/commissions/rules` | filters/rule payload | Rule management |
| Commission calculation | `POST /admin/distribution/commissions/calculate` | activity payload | Calculate and optionally credit wallet |
| Commission events | `GET /admin/distribution/commissions/events` | filters | Commission event list |
| Opportunities | `GET /admin/distribution/opportunities`, `POST /admin/distribution/opportunities`, `GET /admin/distribution/opportunities/{opportunity_id}`, `PATCH /admin/distribution/opportunities/{opportunity_id}` | filters/payload/ID | Opportunity management |
| Opportunity lifecycle | `POST /admin/distribution/opportunities/{opportunity_id}/publish`, `/close`, `/reopen` | action payloads | Status actions |
| Match preview | `POST /admin/distribution/routing/opportunities/{opportunity_id}/matches` | score/limit payload | Candidate preview |
| Route creation | `POST /admin/distribution/routing/opportunities/{opportunity_id}/routes` | score/limit payload | Offer routing |
| Route list/actions | `GET /admin/distribution/routing/routes`, `POST /admin/distribution/routing/routes/{route_id}/accept`, `/decline` | filters/action payload | Route management |
| Governance | Compliance, dispute, distributor action, and audit endpoints under `/admin/distribution/governance/*` | review/dispute/action payloads | Operational controls |
| Reporting | `/admin/distribution/reporting/overview`, `/opportunities`, `/distributors`, `/governance` | tenant/date/status filters | Marketplace reporting |

Gap: route/action ownership for a true distributor user is still represented by
tenant/distributor query params. Production UI should add user-to-distributor
identity mapping.

### Multi-Currency

Purpose: manage FX rates, quote conversion, and cross-border settlements.

| UI area | Endpoint | Inputs | Uses |
| --- | --- | --- | --- |
| FX rates | `GET /admin/multi-currency/fx-rates`, `POST /admin/multi-currency/fx-rates` | tenant/currency/date/source | Rate table and upload/manual entry |
| Conversion quote | `POST /admin/multi-currency/quotes` | source/target currency, amount, date | Quote tool |
| Cross-border settlements | `GET /admin/multi-currency/cross-border-settlements`, `POST /admin/multi-currency/cross-border-settlements` | tenant/currency/status/provider | Settlement instruction table |

Gap: no FX bulk upload endpoint yet.

### Settlement, Fulfilment, Failures

Purpose: operate fulfilment and finance controls.

| UI area | Endpoint | Inputs | Uses |
| --- | --- | --- | --- |
| Fulfilment dashboard | `GET /admin/fulfilment/dashboard` | filters | Fulfilment overview |
| Fulfilment failures | `GET /admin/fulfilment/failures` | filters | Failure queue |
| Fulfilment audit | `GET /admin/fulfilment/audit/{audit_id}` | ID | Attempt detail |
| Fulfilment replay | `POST /admin/fulfilment/replay/{audit_id}` | ID | Replay action |
| Provider health | `GET /admin/fulfilment/providers/health`, `GET /admin/fulfilment/providers/{provider_key}/health` | optional provider | Provider status |
| Settlements | `GET /admin/settlements`, `GET /admin/settlements/{settlement_id}`, `GET /admin/settlements/exposure` | filters/ID | Settlement views |
| Settlement batches | `/admin/settlement-batches/*` | batch/action payloads | Batch lifecycle |
| Settlement approvals | `/admin/settlement-approvals/*` | approval payloads | Approval workflow |
| Settlement exceptions | `/admin/settlement-exceptions/*` | filters/resolution | Exception workflow |
| Settlement reversals | `/admin/settlement-reversals/*` | reversal/action payloads | Reversal workflow |
| Settlement periods | `/admin/settlement-periods/*` | period/action payloads | Period control |
| Certifications | `/admin/settlement-certifications/*` | certification payloads | Closeout evidence |
| DLQ replay | `POST /admin/dlq/replay` | DLQ payload | Technical recovery |
| Processing failures | `GET /admin/failures`, `POST /admin/failures/{failure_id}/resolve`, `POST /admin/failures/{failure_id}/reprocess`, `GET /admin/failures/summary` | filters/action payloads | Failure operations |

Gap: some operational areas need UI-specific aggregation endpoints if the first
admin console aims for a compact command centre rather than many separate
tables.

### Privacy And Tenant Admin

| UI area | Endpoint | Inputs | Uses |
| --- | --- | --- | --- |
| Tenant create/detail | `POST /admin/tenants/`, `GET /admin/tenants/{tenant_code}` | tenant payload/code | Tenant admin |
| Privacy erasure | `DELETE /v1/privacy/referrers/{ucn}` | UCN + tenant context | Erasure request |
| Privacy audit | `GET /v1/privacy/audit`, `GET /v1/privacy/audit/{correlation_id}` | filters/correlation ID | Privacy audit trail |
| Manual purge | `POST /v1/privacy/purge/run` | tenant/jurisdiction options | Manual purge run |

Gap: no full tenant configuration UI contract yet for theme/branding, locales,
journey templates, or channel configuration.

## Sponsor Portal

The Sponsor Portal is currently read-only and billing/funding focused.

Base path:

```text
/v1/tenants/{tenant_code}/sponsors/{sponsor_code}/billing
```

| Screen | Endpoint | Required inputs | Expected use |
| --- | --- | --- | --- |
| Sponsor dashboard | `GET /dashboard` | tenant, sponsor, optional period/currency/as-of date | KPI cards, outstanding amounts, recent status |
| Invoices | `GET /invoices` | optional status, limit | Invoice table |
| Invoice detail | `GET /invoices/{invoice_id}` | invoice ID | Invoice lines and status |
| Statements | `GET /statements` | `period_start`, `period_end`, optional currency/limit | Statement page |
| Payment receipts | `GET /payment-receipts`, `GET /payment-receipts/{receipt_id}` | optional status/limit or receipt ID | Receipt list/detail |
| Wallet | `GET /wallet` | tenant, sponsor | Sponsor wallet balance |
| Contracts | `GET /contracts`, `GET /contracts/{contract_id}` | optional status/limit or contract ID | Contract list/detail |
| Contract ledger | `GET /contracts/{contract_id}/ledger` | contract ID, optional limit | Utilisation ledger |
| Forecast | `GET /forecast` | optional currency, burn window, buffer days | Runway/top-up forecast |

Sponsor Portal gaps:

- No sponsor self-service write actions yet, such as invoice dispute,
  payment upload, top-up request, or contact/admin user management.
- No sponsor-specific opportunity creation flow yet. Opportunities currently
  exist in the admin distribution API.
- No document export/download endpoint yet for invoice PDF, statement PDF, or
  CSV.
- Sponsor identity is currently partner/admin key scoped, not a dedicated
  sponsor user model.

## Distributor Portal

Base path:

```text
/distribution/portal
```

| Screen | Endpoint | Required inputs | Expected use |
| --- | --- | --- | --- |
| Profile | `GET /profile` | `tenant_code`, `distributor_code` | Profile and lifecycle status |
| Offer inbox | `GET /offers` | `tenant_code`, `distributor_code`, optional status/limit | Available and historical offers |
| Accept offer | `POST /offers/{route_id}/accept` | route ID, tenant, distributor | Accept action |
| Decline offer | `POST /offers/{route_id}/decline` | route ID, tenant, distributor | Decline action |
| Wallets | `GET /wallets` | tenant, distributor, optional limit | Wallet summary |
| Wallet ledger | `GET /wallets/{wallet_id}/ledger` | wallet ID, tenant, distributor, optional limit | Ledger detail |
| Performance | `GET /performance` | tenant, distributor | Performance KPIs |

Distributor Portal gaps:

- No dedicated distributor login/session model yet.
- No distributor profile self-edit endpoint in the portal; profile changes are
  admin-side today.
- No payout request endpoint from the distributor portal; payouts are admin
  wallet operations today.
- No attachments/documents endpoint for compliance evidence.

## Recommended Frontend Build Order

1. Build an API client layer generated or typed from OpenAPI.
2. Build shared app shell, auth placeholder, error handling, tenant selector,
   and health banner.
3. Build Admin Console read-only operations views first: health, enterprise
   events, audit, distribution reporting, billing dashboard.
4. Add Admin Console write actions with confirmation modals: replay, issue
   invoice, approve/reject, route offers, wallet movement actions.
5. Build Sponsor Portal read-only billing/funding views.
6. Build Distributor Portal offer inbox, wallet, ledger, and performance.
7. Add production identity model, then replace query-param identity assumptions
   in the portals.

## Backend Gaps To Resolve Before A Production UI

| Gap | Priority | Reason |
| --- | --- | --- |
| OAuth2/OIDC or equivalent user identity | High | API keys are not a user-facing session model |
| User-to-tenant, sponsor, and distributor mapping | High | Prevents relying on query params for portal identity |
| UI-specific command centre summaries | Medium | Reduces frontend over-fetching across many admin endpoints |
| Invoice/statement export endpoints | Medium | Common sponsor operational need |
| Sponsor self-service actions | Medium | Needed once sponsors can operate without platform admins |
| Distributor self-service profile/payout actions | Medium | Needed for a full distributor portal |
| Bulk operations for replay, FX upload, reporting export | Low/Medium | Useful after first operational UI is stable |
