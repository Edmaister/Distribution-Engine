# Operator Demo Readiness Smoke Checklist

Status: Accepted for TASK-067 on 2026-06-27.

This checklist covers the local/CI-safe read-only operator demo path added across the recent DLaaS implementation wave. It is documentation only. Do not use it to run live database checks, inspect secrets, mutate records, dispatch webhooks, create money movement, or unblock TASK-027/TASK-028.

## Scope

Use this checklist to validate that the read-only operator/admin platform surfaces are ready for a controlled demo:

- operator control-plane BFF;
- admin outcome trace endpoint;
- admin liability projection endpoint;
- admin campaign readiness endpoint;
- admin link/code inspect endpoint;
- admin tenant-safe analytics endpoint;
- admin webhook event catalog endpoint;
- admin webhook payload preview endpoint.

## Demo Prerequisites

- Run only against local, test, or CI environments with test credentials.
- Use seeded or synthetic demo data only.
- Do not use production data, live DB credentials, write credentials, or secrets.
- Confirm all requests are read-only GET requests.
- Confirm `tenant_code` values are internal operator/admin test scopes, not public SaaS-facing tenant references.
- For webhook payload preview, use `external_tenant_ref` only; do not send `tenant_code`, UCNs, tokens, client secrets, signing secrets, raw provider payloads, raw audit payloads, or settlement internals.
- Treat TASK-027 and TASK-028 as blocked until approved safe read-only runtime database access is available.

## CI-Safe Smoke Commands

Run these from the repository root with the project test environment:

```powershell
.\.venv_codex\Scripts\python.exe -m pytest test/api/test_operator_control_plane_bff_api.py test/api/test_admin_outcomes_api.py --no-cov
.\.venv_codex\Scripts\python.exe -m pytest test/api/test_campaign_readiness_api.py test/api/test_admin_links_api.py --no-cov
.\.venv_codex\Scripts\python.exe -m pytest test/api/test_admin_analytics_api.py test/api/test_admin_webhook_catalog_api.py --no-cov
.\.venv_codex\Scripts\python.exe -m pytest test/test_outcome_trace_service.py test/test_liability_projection_service.py test/test_campaign_readiness_service.py test/test_link_code_service.py test/test_tenant_safe_analytics_service.py test/test_webhook_event_catalog.py test/test_webhook_payload_builder.py --no-cov
.\.venv_codex\Scripts\python.exe -m pytest test/test_partner_customer_safe_status_service.py test/test_fulfilment_safe_status.py --no-cov
```

Expected result: all selected tests pass without DB writes, live DB access, webhook dispatch, settlement, fulfilment, funding, reward, commission, invoice, export, or audit mutation.

## Endpoint Smoke Checklist

| Surface | Example path | Auth expectation | Tenant/input expectation | Expected guardrail |
| --- | --- | --- | --- | --- |
| Operator control-plane BFF | `GET /v1/experience/operator-control-plane/outcomes/{referral_track_id}?tenant_code=FNB&sections=campaign_readiness&sections=outcome_trace&sections=funding_liability&campaign_code=CAMP001` | Admin/system/finance/distribution/platform operator identity; section-specific permission denial is explicit. | `tenant_code` required; `campaign_code` required when `campaign_readiness` is requested. | Read-only aggregate; command workflows require separate authorized routes. |
| Admin outcome trace | `GET /admin/outcomes/{referral_track_id}/trace?tenant_code=FNB` | Admin/operator identity accepted by the admin outcomes route. | Explicit tenant scope and outcome/referral track lookup. | Outcome trace is diagnostic and must not mutate source state. |
| Admin liability projection | `GET /admin/outcomes/{referral_track_id}/liability?tenant_code=FNB` | Finance/system/platform-style admin permission where required. | Explicit tenant scope and outcome/referral track lookup. | Liability projection is derived and must not create money movement. |
| Admin campaign readiness | `GET /admin/campaigns/{campaign_code}/readiness?tenant_code=FNB&operation=CONTROL_PLANE_VIEW` | Distribution admin or platform admin; adjacent finance-only identity is rejected. | Explicit tenant scope, operation, optional opportunity/evidence controls. | Read-only readiness; no campaign, policy, referral, attribution, funding, fulfilment, settlement, audit, or reward mutation. |
| Admin link/code inspect | `GET /admin/links/inspect?tenant_code=FNB&source_type=CAMPAIGN_CODE&code_or_ref=CAMP001` | Distribution admin or platform admin; adjacent finance-only identity is rejected. | Explicit tenant scope, source type, and link/code identifier. | Read-only inspect; does not issue, resolve, void, rotate, mutate, or generate codes. |
| Admin analytics report | `GET /admin/analytics/reports/distribution_overview?tenant_code=FNB&dimensions=tenant_code&dimensions=metric_name` | Platform/admin, distribution, finance, or system admin identity depending report use. | Explicit tenant scope; approved dimensions, filters, and date windows only. | Read-only analytics; no exports, billing events, invoices, ledger writes, or money movement. |
| Admin webhook event catalog | `GET /admin/webhooks/event-catalog?family=outcome` | Admin/system/platform admin identity; partner identity is rejected. | Optional family filter must be one of the accepted catalog families. | Read-only catalog; no subscription validation, dispatch, queue, signing, retry, replay, delivery, persistence, or payload building. |
| Admin webhook payload preview | `GET /admin/webhooks/payload-preview?event_type=OUTCOME_COMPLETED&external_tenant_ref=partner-fnb&subject_id=outcome-safe-1` | Admin/system/platform admin identity; partner identity is rejected. | Campaign and outcome catalog events only; external tenant reference and safe subject ID required. | Preview-only; no dispatch, queue, signing, retry, replay, delivery, persistence, or partner delivery creation. |

## Safe Redaction Expectations

Every demo response should be checked for these properties:

- no raw UCNs, private customer identifiers, access tokens, client secrets, signing secrets, API keys, passwords, or credential material;
- no raw provider payloads, raw audit payloads, raw DLQ payloads, SQL errors, stack traces, or unrestricted settlement internals;
- evidence fields either use safe source references or explicit redaction markers such as `[REDACTED]`;
- webhook payload previews use `external_tenant_ref`, never internal `tenant_code`;
- outcome, liability, link/code, analytics, and webhook responses preserve `redactions`, `missing_evidence`, `source_warnings`, or safe error envelopes where evidence is incomplete.

## No-Mutation Guardrails

During demo readiness, do not call routes that:

- create, update, activate, publish, pause, close, route, issue, resolve, void, rotate, retry, replay, repair, export, approve, reverse, fulfil, settle, reserve, release, invoice, or notify;
- enqueue webhook deliveries or process webhook deliveries;
- write audit rows as part of a command flow;
- require idempotency keys because duplicate execution could change state.

For this checklist, valid requests are read-only diagnostics only.

## Curl-Style Local Examples

These examples use placeholder local test keys. Do not use real secrets in documentation, terminals, screenshots, or demos.

```powershell
curl -H "x-api-key: test-system-admin-key" "http://localhost:8000/v1/experience/operator-control-plane/outcomes/11111111-1111-4111-8111-111111111111?tenant_code=FNB&sections=outcome_trace&sections=funding_liability"
curl -H "x-api-key: test-distribution-admin-key" "http://localhost:8000/admin/campaigns/CAMP001/readiness?tenant_code=FNB&operation=CONTROL_PLANE_VIEW"
curl -H "x-api-key: test-distribution-admin-key" "http://localhost:8000/admin/links/inspect?tenant_code=FNB&source_type=CAMPAIGN_CODE&code_or_ref=CAMP001"
curl -H "x-api-key: test-admin-key" "http://localhost:8000/admin/analytics/reports/distribution_overview?tenant_code=FNB&dimensions=tenant_code&dimensions=metric_name"
curl -H "x-api-key: test-system-admin-key" "http://localhost:8000/admin/webhooks/event-catalog?family=outcome"
curl -H "x-api-key: test-system-admin-key" "http://localhost:8000/admin/webhooks/payload-preview?event_type=OUTCOME_COMPLETED&external_tenant_ref=partner-fnb&subject_id=outcome-safe-1"
```

Expected response posture:

- HTTP 200 for authorized read-only requests with valid inputs and available evidence;
- HTTP 400 for safe validation errors;
- HTTP 401 for missing credentials;
- HTTP 403 for authenticated identities outside the route's permission boundary;
- HTTP 404 only where a diagnostic source is intentionally hidden or inaccessible, such as missing/inaccessible campaign readiness evidence.

## Known Blockers

- TASK-027 is blocked until approved safe read-only runtime DB access is available. No DB connection should be attempted without environment name, read-only credentials, write-protection confirmation, and explicit approval.
- TASK-028 is blocked until TASK-027 produces verified live/schema drift evidence or a formal decision defers specific unknowns.
- This checklist does not prove live DB state, production readiness, partner delivery behavior, event emission, white-label readiness, SaaS billing readiness, or money movement correctness.

## Readback Validation

Before a demo, read this checklist back and confirm:

- all eight read-only surfaces are covered;
- auth and tenant expectations are explicit;
- redaction and safe error expectations are explicit;
- no-mutation and no-money-movement guardrails are explicit;
- TASK-027/TASK-028 remain blocked;
- the provided commands are local/CI-safe and use no real secrets.
