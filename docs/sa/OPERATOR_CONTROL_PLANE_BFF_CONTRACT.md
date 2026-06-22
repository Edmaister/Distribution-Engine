# Operator Control-Plane BFF Contract

Status: Accepted for TASK-021.

This document defines the backend-for-frontend contract for DLaaS operator control-plane surfaces. It is a contract only: it does not add routes, schema, migrations, frontend screens, or mutating workflows.

## Problem Statement

Operators need one control-plane view that can explain campaign readiness, outcome state, money exposure, fulfilment, settlement, integrations, audit evidence, and failures without the frontend inventing state or reading raw internal tables directly.

Current backend routes already expose many pieces of this information through admin experience, finance, funding, fulfilment, settlement, partner seam, audit, failure, and DLQ APIs. The missing contract is the aggregate BFF shape: which sections exist, how tenant and permission boundaries apply, how partial data is represented, and which backend source owns each field family.

## Decision

Define role-scoped, read-only operator BFF contracts over existing backend services and future internal APIs. BFF responses must be explicit about source truth, missing evidence, unavailable sections, redactions, and permission-denied sections.

The BFF must not execute repair, replay, fulfilment, settlement, funding, reward, commission, or webhook mutation commands. It may expose safe next-action metadata that points operators to separately authorized command routes.

## Non-Goals

- No application code, API route, schema, migration, seed, or frontend implementation is added by TASK-021.
- No raw provider payload, secret, signing material, private participant identifier, or unrestricted settlement internal should be exposed to external or general operator surfaces.
- No money movement or lifecycle mutation is part of the BFF read contract.

## Contract Principles

- **Admin auth required:** Operator BFF routes must use admin/system/finance/distribution permission helpers that match the section being read.
- **Tenant scoped:** Requests must include or derive tenant scope. Cross-tenant visibility is reserved for explicitly authorized platform/system operators.
- **Read idempotent:** GET/read BFF endpoints are side-effect free and do not require idempotency keys.
- **Partial by design:** A failed section must not hide the rest of the response. The response must list unavailable, timed-out, permission-denied, and missing-evidence sections.
- **Source owned:** Every field family must map to a backend service, route, or accepted SA contract.
- **Safe errors:** Client-visible errors must use safe categories and correlation references without exposing secrets, provider internals, SQL details, or raw payloads.
- **Audit visible:** Read responses should show audit/support references where available, and missing audit evidence where it is material.

## Response Envelope

Operator BFF implementations should use this envelope shape unless a narrower route contract documents a smaller subset.

```json
{
  "status": "ok",
  "tenant_code": "TENANT",
  "generated_at": "2026-06-22T00:00:00Z",
  "requested_sections": ["campaign_readiness", "outcome_trace"],
  "sections": {
    "campaign_readiness": {
      "status": "ok",
      "data": {},
      "missing_evidence": [],
      "source_warnings": [],
      "redactions": [],
      "backend_sources": [],
      "safe_next_actions": []
    }
  },
  "unavailable_sections": [],
  "permission_denied_sections": [],
  "redactions": [],
  "guardrail": "Read-only aggregate. Command workflows require separately authorized routes."
}
```

Top-level `status` values:

| Status | Meaning |
| --- | --- |
| `ok` | All requested sections loaded and no material evidence is missing. |
| `partial` | One or more requested sections are unavailable, timed out, permission denied, or missing evidence. |
| `unavailable` | No requested section could be loaded. |

Section `status` values:

| Status | Meaning |
| --- | --- |
| `ok` | Section loaded from backend source truth. |
| `missing_evidence` | Section loaded, but source evidence is incomplete or inconsistent. |
| `permission_denied` | The actor is authenticated but not authorized for this section. |
| `timeout` | Section exceeded the BFF time budget. |
| `unavailable` | Section source failed or is not currently reachable. |
| `not_implemented` | Contracted section has no backend implementation yet. |

## Section Contracts

| Section | Purpose | Required source truth | Minimum safe fields |
| --- | --- | --- | --- |
| `campaign_readiness` | Show whether a campaign or opportunity can be launched, activated, paused, or repaired. | `docs/sa/CAMPAIGN_READINESS_SERVICE_CONTRACT.md`, campaign services, campaign policy services, distribution opportunity services. | Readiness state, blockers, missing configuration, lifecycle state, activation guard, source warnings. |
| `outcome_trace` | Explain an outcome or referral track across attribution, participants, event evidence, reward, commission, funding, fulfilment, settlement, audit, and webhooks. | `docs/sa/OUTCOME_TRACE_RESPONSE_CONTRACT.md`, `services/outcome_trace_service.py`. | Trace completeness, safe section summaries, missing evidence, support trace references, redactions. |
| `funding_liability` | Show derived liability and funding exposure without creating or moving money. | `docs/sa/LIABILITY_STATE_MODEL.md`, `services/liability_projection_service.py`, funding and finance services. | Liability totals by category, derived state counts, missing money evidence, no-double-count warnings, source families. |
| `fulfilment` | Show fulfilment progress, failed states, retry posture, and operator-safe status categories. | Fulfilment admin routes and services, `services/fulfilment_safe_status.py`. | Safe status counts, pending/processing/success/failure counts, retry posture, provider health category, action-required flags. |
| `settlement` | Show settlement batches, approvals, exceptions, reversals, certifications, and settlement-safe status categories. | Admin settlement routes and settlement services, `services/fulfilment_safe_status.py`. | Batch state counts, approval state, exception counts, reversal/dispute indicators, safe status counts. |
| `integration_health` | Show partner/API/webhook delivery health without exposing credentials or secrets. | `docs/sa/WEBHOOK_EVENT_CATALOG.md`, partner seam service/routes, webhook delivery worker evidence. | Client readiness, subscription health, delivery success/failure counts, retry/dead-letter counts, signing readiness without secret values. |
| `audit` | Show operator evidence, actor/action references, correlation references, and missing audit evidence. | `docs/sa/AUDIT_RETRY_POLICY_STANDARD.md`, admin audit service, support trace evidence. | Audit record references, actor/action categories, correlation/idempotency references, missing audit evidence. |
| `failures` | Show stuck events, DLQ items, replayable failures, and repair-safe categories. | Admin failure routes, DLQ replay routes, enterprise event inbox evidence. | Failure counts, DLQ counts, replayable categories, last failure category, safe next actions. |

## Permission Rules

The aggregate BFF may be system-admin scoped, but each section must preserve the stricter domain boundary when applicable.

| Section family | Minimum permission expectation |
| --- | --- |
| Cross-domain aggregate | System admin/operator permission. |
| Funding, liability, finance, fulfilment, settlement | Finance admin or stronger system-admin permission. |
| Distribution lifecycle and distributor finance | Distribution admin or stronger system-admin permission. |
| Partner seam and webhook health | Partner admin/system-admin for admin views; partner identity only for tenant/client-scoped partner views. |
| Audit, failure, DLQ | System/admin permission with safe redaction. |

If the actor can read the aggregate but not a section, the section must return `permission_denied`; the BFF must not silently omit it.

## Tenant And Identifier Rules

- Internal operator surfaces may use resolved `tenant_code`.
- Public, partner, webhook, onboarding, and SaaS-facing surfaces should use the external identifier boundary defined in `docs/sa/TENANT_IDENTIFIER_BOUNDARY_DECISION.md`.
- BFF implementations must not combine tenant data unless the route is explicitly platform-scoped and authorized.
- Section filters must be passed through to source services rather than applied only in the frontend.

## Safe Error Shape

Section errors should follow this shape:

```json
{
  "code": "section_unavailable",
  "message": "Section is temporarily unavailable.",
  "correlation_id": "optional-correlation-reference",
  "retryable": true
}
```

Allowed safe error categories include `validation_error`, `permission_denied`, `not_found`, `missing_evidence`, `section_timeout`, `section_unavailable`, and `not_implemented`.

## Redaction Rules

BFF responses must redact or omit:

- raw UCNs, private participant identifiers, secrets, API keys, signing secrets, tokens, and credential material;
- raw provider payloads and stack traces;
- raw SQL/database errors;
- settlement provider internals that are not needed for operator action;
- webhook signing material and full request/response bodies unless a separately authorized audit export permits them.

Operator-safe details may include source family, source row reference, derived status, evidence count, retry category, and safe failure category.

## Current Route Alignment

| Current route family | Alignment |
| --- | --- |
| `/v1/experience/admin-command-centre` | Existing aggregate pattern with section status, unavailable sections, and read-only guardrail. Future BFF work can extend this pattern or add a narrower route. |
| `/admin/finance/*` | Candidate source for finance, outcome-money, wallet, and reconciliation sections. |
| `/admin/funding/*` | Candidate source for funding readiness, exposure, alerts, reconciliation, and rule sections. |
| `/admin/fulfilment/*` | Candidate source for fulfilment health and retry posture. |
| `/admin/settlement*` | Candidate source for settlement batches, approvals, exceptions, periods, reversals, and certifications. |
| `/admin/partners/*` and partner seam services | Candidate source for integration readiness, webhook delivery health, retry, and dead-letter evidence. |
| `/admin/audit`, `/admin/failures`, `/admin/dlq/*` | Candidate source for audit, stuck-state, failure, and replay visibility. |

## Validation Expectations For Implementation Tasks

Future implementation tasks should add tests for:

- authenticated section loading;
- unauthenticated and unauthorized access;
- tenant filter enforcement and cross-tenant rejection;
- partial-section behavior;
- missing-evidence behavior;
- permission-denied section behavior;
- read-only behavior with no mutation side effects;
- redaction of raw provider, settlement, webhook, credential, and private participant data;
- source truth coverage for every response field.

## Follow-Up Implementation Tasks

- Implement the internal outcome trace API after this contract, using TASK-022 scope.
- Add operator BFF aggregation only in a later task that cites this contract and preserves section-level permissions.
- Add frontend control-plane screens only after the backend BFF route contracts and tests exist.
- Add command/repair workflows separately with explicit authorization, idempotency, audit reason, and retry behavior.
