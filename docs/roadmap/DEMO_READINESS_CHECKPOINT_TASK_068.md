# Demo Readiness Checkpoint

Status: Accepted for TASK-068 on 2026-06-27.

This checkpoint records demo readiness after the TASK-061 through TASK-067 wave. It is documentation only. No database access was attempted, no secrets were inspected, and no application code, tests, schema, migrations, or runtime behavior were changed by this checkpoint.

## Completed Demo-Readiness Wave

| Task | Capability added | Demo impact |
| --- | --- | --- |
| TASK-061 | Distributor portal safe status | Distributor-facing conversion rows can include role-safe status/action categories without exposing raw provider, settlement, tenant, UCN, or secret-like evidence. |
| TASK-062 | Campaign readiness in operator BFF | Operators can request campaign readiness inside the read-only control-plane aggregate. |
| TASK-063 | Tenant-safe analytics admin endpoint | Operators can query tenant-safe operational analytics through an authenticated read-only admin endpoint. |
| TASK-064 | Webhook event catalog endpoint | Operators and integration teams can inspect supported webhook event families and types without delivery side effects. |
| TASK-065 | Webhook payload preview endpoint | Operators can preview safe campaign/outcome webhook envelopes without dispatching, signing, queueing, or persisting deliveries. |
| TASK-066 | Public/API diagnostic contract tests | Campaign readiness and link/code diagnostics have locked read-only response, auth, tenant, safe error, and redaction behavior. |
| TASK-067 | Operator demo readiness smoke checklist | The team has a local/CI-safe checklist for the read-only operator demo path. |

## What Is Demo-Ready

- Read-only operator investigation for outcome trace and liability projection.
- Read-only operator control-plane aggregation with outcome trace, funding liability, and campaign readiness sections.
- Read-only campaign readiness diagnostics for distribution/platform operators.
- Read-only link/code inspect diagnostics for campaign and link/code evidence.
- Read-only tenant-safe analytics reports for approved dimensions and filters.
- Read-only webhook event catalog discovery.
- Non-delivering webhook payload preview for campaign and outcome events.
- Distributor-safe status projection for a role-scoped portal path.
- CI/local smoke-test selections documented in `docs/roadmap/OPERATOR_DEMO_READINESS_SMOKE_CHECKLIST.md`.

These surfaces are demo-ready only for controlled local, CI, or test environments with seeded or synthetic data. They do not prove live production state.

## Read-Only Operator/Admin Endpoints

| Surface | Route family | Demo use |
| --- | --- | --- |
| Operator control-plane BFF | `GET /v1/experience/operator-control-plane/outcomes/{referral_track_id}` | Show one aggregate operator view with section-level status, permission handling, missing evidence, and guardrails. |
| Admin outcome trace | `GET /admin/outcomes/{referral_track_id}/trace` | Explain attribution, outcome, support trace, evidence completeness, and redactions. |
| Admin liability projection | `GET /admin/outcomes/{referral_track_id}/liability` | Show derived liability and funding exposure without creating money movement. |
| Admin campaign readiness | `GET /admin/campaigns/{campaign_code}/readiness` | Show readiness blockers, warnings, operation context, and source evidence. |
| Admin link/code inspect | `GET /admin/links/inspect` | Inspect campaign/referral/route code evidence without issuing, resolving, voiding, rotating, or generating codes. |
| Admin analytics | `GET /admin/analytics/reports/{report_type}` | Show tenant-safe operational reporting with metric class, freshness, warnings, and redactions. |
| Admin webhook event catalog | `GET /admin/webhooks/event-catalog` | List safe webhook event families and event types. |
| Admin webhook payload preview | `GET /admin/webhooks/payload-preview` | Render safe campaign/outcome webhook envelope examples without delivery behavior. |

All of these are read-only diagnostic or preview surfaces. They must not be described as command workflows.

## Distributor, Partner, And Customer-Safe Surfaces

- Distributor portal conversion rows can expose `distributor_safe_status` using the partner/customer-safe status helper.
- Partner/customer-safe status projection helper exists for partner, distributor, sponsor/producer, referrer, and customer perspectives.
- Fulfilment and settlement safe status helpers exist for operator-facing and external-facing mappings.
- Webhook payload preview uses `external_tenant_ref` rather than internal `tenant_code`.

Partner/customer-safe adoption is still partial. The distributor path has adopted the helper, but broader partner, sponsor, customer, referrer, and public APIs still need role-specific integration work before an external demo.

## Available Services And Helpers

- `services/outcome_trace_service.py`
- `services/liability_projection_service.py`
- `services/fulfilment_safe_status.py`
- `services/partner_customer_safe_status_service.py`
- `services/campaign_readiness_service.py`
- `services/link_code_service.py`
- `services/tenant_safe_analytics_service.py`
- `services/webhook_event_catalog.py`
- `services/webhook_payload_builder.py`

These services and helpers provide the reusable read-only platform layer for the current demo wave.

## Safe Demo Flows Without Money Movement

The following flows can be shown safely in local/test/CI conditions with synthetic data:

1. Operator investigates an outcome through the control-plane BFF, including outcome trace and liability projection sections.
2. Operator inspects campaign readiness before launch or operational review.
3. Operator inspects a campaign or link/code diagnostic without changing the code.
4. Operator reviews tenant-safe operational analytics with freshness and source warnings.
5. Operator previews accepted webhook events and renders a non-delivering campaign/outcome payload.
6. Distributor portal shows a role-safe conversion status without raw internal state.
7. Team runs the TASK-067 smoke checklist and targeted tests to demonstrate read-only readiness.

Do not demo fulfilment, settlement, funding reservation, release, payout, invoice generation, webhook delivery, retry, replay, repair, export, or lifecycle command execution as complete unless a later task explicitly implements and validates those command paths.

## Backend-Only Capabilities Needing UI Work

- Operator control-plane BFF has backend/API shape but needs a deliberate operator UI surface.
- Campaign readiness diagnostics need frontend presentation for blockers, warnings, source evidence, and safe next actions.
- Link/code inspect needs an operator UI pattern for safe status, evidence, and validation errors.
- Tenant-safe analytics has an admin endpoint but no demo-focused reporting UI.
- Webhook catalog and payload preview are API-ready but need an integration/operator UI.
- Distributor safe status exists in backend output, but frontend adoption should be confirmed or implemented in a focused task.
- Smoke checklist is manual/docs-driven, not an automated demo script or UI test suite.

## Remaining Risks Before External Demo

- TASK-027 live DB verification remains blocked, so live schema/state drift is unknown.
- TASK-028 remains blocked because there are no verified live drift results to resolve.
- Partner/customer-safe status adoption is not complete across all external roles.
- Public partner API packaging remains incomplete; several surfaces are admin/internal diagnostics only.
- Webhook event delivery is not implemented by this wave; catalog and preview do not mean emission, subscription enforcement, signing, queueing, or delivery.
- SaaS account, membership, plan, quota, billing, credential lifecycle, and white-label/embed readiness remain immature.
- Demo data must be synthetic or seeded; no production data should be used.
- External demos need careful wording to avoid implying money movement, settlement, fulfilment, webhook delivery, or live DB verification is complete.

## Blocked Work

TASK-027 is still blocked by missing approved safe read-only runtime database access. No DB connection was attempted.

TASK-028 is still blocked because TASK-027 has not produced verified live/schema drift evidence. TASK-028 should only resolve confirmed live/schema mismatches or explicitly deferred unknowns.

Required unblockers remain:

- environment name;
- read-only DB credentials;
- write-protection confirmation;
- approval for runtime/API smoke checks;
- or an explicit decision to defer named TASK-001 unknowns without live DB verification.

## Recommended Next Implementation Wave

1. Build a focused frontend/operator demo UI over the existing read-only BFF and admin diagnostics.
2. Add API hardening around read-only diagnostic routes where contract tests reveal gaps: pagination, safe errors, OpenAPI examples, response envelope consistency, and permission matrix alignment.
3. Package a small public partner API slice around safe status and link/code inspection only after tenant/external identifier boundaries are enforced.
4. Add webhook subscription validation and delivery hardening only after catalog and payload preview are stable, with idempotency, audit, signing, retry, and dead-letter behavior tested.
5. Complete TASK-027 live DB verification as soon as safe read-only access is approved.

Do not prioritize money movement, settlement commands, fulfilment commands, SaaS billing, or white-label/embed work until live verification, tenant/account packaging, and role-safe external APIs are stronger.

## Recommended Priority

Priority should be:

1. Frontend/demo UI for the read-only operator/admin surfaces, because the backend platform primitives are now ready to show safely.
2. API hardening for the diagnostic routes, especially response envelope consistency, OpenAPI examples, and permission matrix coverage.
3. Live DB verification as soon as approved read-only access exists, because release confidence still depends on deployed state.
4. Public partner API packaging for safe status and diagnostics after tenant/external identifier boundaries are enforceable in implementation.
5. Webhook delivery implementation after catalog, payload preview, subscription validation, idempotency, audit, and retry contracts are fully tested.

## Readiness Summary

The platform is ready for a controlled internal demo of read-only operator/admin diagnostics and one distributor-safe status path. It is not yet ready for an external production-style demo that depends on live DB verification, partner-facing API packaging, webhook delivery, command workflows, money movement, SaaS billing, or white-label/embed behavior.
