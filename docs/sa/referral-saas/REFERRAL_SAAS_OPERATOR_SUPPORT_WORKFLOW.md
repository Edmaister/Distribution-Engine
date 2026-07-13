# Referral SaaS Operator Support Workflow

TASK ID: TASK-145

Product boundary: Referral Management and Campaign Attribution SaaS.

Status: Contract only. No runtime behavior, schema, route, permission,
frontend, repair/replay action, audit behavior, or test changes are made by
this task.

## Boundary

This contract defines the first-launch Referral SaaS operator support workflow
for investigating validation, link/code, progress, status, attribution,
reporting, integration, and readiness issues from safe evidence.

Required boundary docs checked:

- `docs/product/README.md`
- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/README.md`
- `docs/roadmap/referral-saas/ROADMAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_LINK_CODE_INVESTIGATION_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_ATTRIBUTION_TRACE_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_PROGRESS_EVENT_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_SAFE_STATUS_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`
- `docs/sa/AUDIT_RETRY_POLICY_STANDARD.md`
- `docs/sa/API_SURFACE_MAP.md`

Source files inspected:

- `apps/api/routers/admin_links.py`
- `apps/api/routers/admin_outcomes.py`
- `apps/api/routers/admin_campaign_readiness.py`
- `apps/api/routers/progress.py`
- `apps/api/routers/admin_audit.py`
- `apps/api/routers/admin_analytics.py`
- `apps/api/routers/admin_failure.py`
- `apps/api/routers/admin_dlq_replay.py`
- `apps/api/routers/internal_replay.py`
- `apps/api/routers/enterprise_events.py`
- `services/link_code_service.py`
- `services/outcome_trace_service.py`
- `services/failure_admin_service.py`
- `services/dlq_replay_service.py`
- `services/replay_service.py`
- `services/admin_audit_service.py`
- `frontend/src/pages/admin/OperatorDemoHomePage.tsx`

## Purpose

Referral SaaS operators need a bounded way to answer:

```text
Why is this referral, code, campaign, progress event, attribution trace, or
report not behaving as expected, and what safe next step should we take?
```

The repository already has several support primitives:

- read-only link/code inspection
- read-only outcome trace
- read-only campaign readiness
- progress event ingestion and referrer progress reads
- tenant-safe analytics reads
- admin audit reads
- admin failure listing, resolving, and reprocessing
- DLQ and referral replay routes
- event ingestion and health/readiness surfaces
- an operator demo home that marks several diagnostics as frontend pending

This contract assembles those into a Referral SaaS support workflow. It does
not authorize new repair, replay, retry, mutation, or customer-visible
diagnostic behavior.

## Current Implementation Facts

Current read-only or diagnostic foundations:

| Capability | Current route/service | Current guardrail |
|---|---|---|
| Link/code inspection | `GET /admin/links/inspect`; `GET /v1/referral-saas/operator/links/inspect`; `inspect_link_code` | Read-only; product wrapper preserves redactions, missing evidence, source warnings, evidence toggling, safe validation errors, and next diagnostics; does not issue, resolve, void, rotate, mutate, retry, replay, repair, reward, fund, fulfil, settle, or generate codes. |
| Outcome trace | `GET /admin/outcomes/{referral_track_id}/trace`; `get_outcome_trace` | Read-only; does not mutate reward, funding, fulfilment, settlement, audit, or webhook state. |
| Campaign readiness | `GET /admin/campaigns/{campaign_code}/readiness`; `get_campaign_readiness` | Read-only; does not mutate campaigns, policies, referrals, attribution, funding, fulfilment, settlement, audit, or rewards. |
| Progress ingestion | `POST /v1/progress`; `handle_progress_event` | Partner-authenticated; dedupe and queue behavior are source truth. |
| Referrer progress read | `GET /v1/referrers/{referrerUcn}` | Admin/partner scoped progress summary. |
| Tenant-safe analytics | `GET /admin/analytics/reports/{report_type}` | Read-only; no export, invoice, billing, funding, settlement, fulfilment, reward, commission, audit, tenant, or analytics mutation. |
| Admin audit | `GET /admin/audit`; `GET /admin/audit/summary` | System-admin audit visibility. |
| Failure list/summary | `GET /admin/failures`; `GET /admin/failures/summary` | Admin failure visibility over `referral_event_failures`. |
| Enterprise event ingest | `POST /enterprise/events` | Admin/partner authenticated event ingestion. |

Current mutation/repair-capable foundations that require caution:

| Capability | Current route/service | Support workflow posture |
|---|---|---|
| Failure resolve | `POST /admin/failures/{failure_id}/resolve`; `resolve_failure` | Existing admin mutation; product support must require actor/reason/audit posture before surfacing. |
| Failure reprocess | `POST /admin/failures/{failure_id}/reprocess`; `reprocess_failure` | Existing admin mutation; only supports `REFERRAL_PROGRESS_RECORDED` payloads. |
| DLQ replay | `POST /admin/dlq/replay`; `replay_dlq_event` | Existing system-admin mutation/replay path; not a first-launch product self-service action. |
| Referral replay | `POST /internal/replay/referrals/{referral_track_id}`; `rebuild_referral_instance` | Existing system-admin/internal replay; `dry_run=true` is safer, non-dry-run mutates referral projection. |

## First-Launch Support Cases

Referral SaaS should start with these support case types:

| Support case | Primary lookup | First diagnostic | Related diagnostics |
|---|---|---|---|
| Code or link not recognized | code/ref/link ID/source type | Link/code inspection | Campaign readiness, validation recovery, attribution trace |
| Validation failed or customer cannot continue | referral code, tenant/account, alias/terms context | Link/code inspection plus validation contract state | Safe status, audit, campaign readiness |
| Progress event rejected or missing | referral track ID, source system/event ID, event type | Progress evidence and failure list | Outcome trace, failure detail, event ingestion health |
| Status stuck or unsafe to show | safe referral ref/referral track ID | Safe-status projection contract | Progress, outcome trace, missing evidence |
| Attribution missing, partial, or conflicting | referral track ID, campaign code, link/code | Outcome trace | Link/code inspect, campaign readiness, reports |
| Report count mismatch | report type, campaign/date filters | Tenant-safe analytics freshness/warnings | Attribution trace sample, progress health, missing evidence |
| Integration event/payload failure | source system/event ID/correlation ID | Progress/event failure list | Enterprise event intake, audit, health |
| Campaign not ready | campaign code | Campaign readiness | Link/code status, integration readiness, report freshness |

## Operator Workflow

### 1. Start From A Safe Lookup

Allowed support lookup inputs:

- safe account reference or tenant scope for operator-only routes
- campaign code
- referral code or link/code ID
- referral track ID for operator-only trace and progress diagnostics
- source system and source event ID
- failure ID
- audit target type and target ID
- report type and date window

Rules:

- public/customer support should not ask for raw UCNs as the first lookup
- operator-only routes may require `tenant_code` until product wrappers exist
- tenant mismatch results must not reveal the other tenant
- missing evidence must stay a support diagnostic, not a customer-facing reason

### 2. Classify The Issue

Support should classify cases into product categories:

| Category | Meaning | Default action |
|---|---|---|
| `VALIDATION_RECOVERY` | Terms, alias, code-not-found, or validation evidence gap. | Give safe recovery guidance; inspect code/link if needed. |
| `PROGRESS_DIAGNOSTIC` | Event recorded, deduped, rejected, failed, or missing. | Review progress evidence and failure list. |
| `ATTRIBUTION_REVIEW` | Trace is partial, missing evidence, inconsistent, or unavailable. | Review trace and linked source evidence. |
| `READINESS_BLOCKER` | Campaign/account/integration is not ready. | Show blocker and next action; no activation from support. |
| `REPORTING_FRESHNESS` | Report is stale, partial, unavailable, or has source warnings. | Show freshness/source warning; do not silently zero metrics. |
| `INTEGRATION_HEALTH` | Source system, webhook/API, queue, or event intake issue. | Review event/audit/health evidence. |
| `ACCESS_SCOPE` | Role, tenant, or credential does not permit action/view. | Return safe permission guidance. |
| `MANUAL_REVIEW_REQUIRED` | Evidence is unsafe, conflicting, or mutation might be needed. | Escalate with actor/reason requirement. |

These are product support categories, not new database enum values.

### 3. Gather Read-Only Evidence First

Required read-only evidence sequence:

1. link/code inspection when a code, link, campaign track, route link, or
   composite reference is involved
2. campaign readiness when campaign availability or setup is in question
3. progress/failure evidence when events are missing, rejected, or delayed
4. outcome trace when attribution or status is unclear
5. tenant-safe analytics when report totals are disputed
6. audit and health evidence when integration or platform behavior is in
   question

The support UI should prefer read-only routes before any repair/retry/replay
path is shown.

### 4. Decide Safe Next Action

| Evidence result | Safe next action |
|---|---|
| Source not found | Ask caller to confirm code/link; do not disclose other tenant evidence. |
| Tenant mismatch | Treat as inaccessible/mismatched evidence; do not reveal tenant owner. |
| Terms required | Direct user to accept terms through public flow. |
| Alias rejected | Direct user to choose a valid alias. |
| Progress deduped | Explain that the event was already received; no replay needed. |
| Progress validation rejected | Correct payload/journey/identifier before retry. |
| Progress queue or processing failed | Review `referral_event_failures`; mutation requires controlled repair workflow. |
| Attribution partial/missing | Show missing evidence category and linked source; do not count as attributed. |
| Report stale/partial | Show freshness and source warning; do not create an export from stale assumptions. |
| Access denied | Explain permission boundary without leaking existence of inaccessible data. |
| Replay/repair might be required | Escalate to manual review with actor, reason, correlation, before/after, and idempotency requirements. |

## Support Case Response Shape

Future support APIs or BFF sections should return a safe support envelope:

```json
{
  "caseType": "PROGRESS_DIAGNOSTIC",
  "caseStatus": "MANUAL_REVIEW_REQUIRED",
  "subject": {
    "type": "referral",
    "safeRef": "referral:track:11111111-1111-4111-8111-111111111111"
  },
  "summary": "Progress event was recorded but downstream processing needs review.",
  "evidence": {
    "linkCode": null,
    "campaignReadiness": null,
    "progress": {},
    "attributionTrace": {},
    "reportFreshness": null,
    "audit": {}
  },
  "missingEvidence": [],
  "sourceWarnings": [],
  "redactions": [],
  "recommendedNextAction": {
    "action": "ESCALATE_MANUAL_REVIEW",
    "mutationRequired": false,
    "reasonRequiredBeforeMutation": true
  }
}
```

This is a target product shape only. TASK-145 does not implement it.

## Mutation Boundary

First-launch support workflow is read-only by default.

Do not expose these as ordinary support actions until a later implementation
task adds role, audit, idempotency, retry, and tests:

- resolve failure
- reprocess failure
- replay DLQ
- rebuild referral instance with `dry_run=false`
- requeue event
- edit progress/referral/campaign state
- override attribution
- revoke, expire, reissue, void, or rotate code/link
- publish/activate campaign
- deliver webhook
- create export
- perform funding, fulfilment, settlement, commission, wallet, invoice, payout,
  or sponsor billing actions

Dry-run/referral replay evidence may be useful for support diagnosis, but a
non-dry-run replay remains a mutation and must follow the audit/retry policy.

## Permissions

Minimum first-launch permission posture:

| Surface | Current role posture | Product support rule |
|---|---|---|
| Link/code inspect | Distribution/platform admin style key | Operator/support only. |
| Outcome trace | Operator/admin session roles | Operator/support only; account-safe wrapper later. |
| Campaign readiness | Distribution admin style key | Operator/support and later account admin safe view. |
| Analytics report | Admin analytics roles | Operator/account admin only after product wrapper. |
| Audit | System admin | Internal operator only. |
| Failure resolve/reprocess | Admin key | Internal admin only until repair contract exists. |
| DLQ/replay | System admin | Internal only; not first-launch SaaS self-service. |

Cross-tenant access must be rejected or hidden with safe 403/404 behavior.

## Redaction Rules

Support workflow must not expose:

- raw UCNs
- raw customer identifiers
- raw account numbers
- raw provider payloads
- raw audit payloads to account users
- DLQ payloads outside internal operator views
- secrets, tokens, signing material, API keys, certificates, or private keys
- raw SQL errors, stack traces, or worker errors
- funding, fulfilment, settlement, commission, wallet, invoice, payout, or
  sponsor billing internals for first-launch Referral SaaS

Allowed support evidence:

- safe refs
- tenant/account scope for operator-only views
- campaign code where permitted
- referral track ID for operator-only diagnostics
- source system and source event ID
- dedupe key
- safe missing-evidence code
- safe warning code
- redaction list
- correlation reference where it does not leak restricted payloads

## Relationship To Frontend IA

TASK-144 identifies support as a top-level product area, but the current
frontend does not have a dedicated Referral SaaS support screen.

Current frontend facts:

- `OperatorDemoHomePage` links existing setup, readiness, monitoring, events,
  health, and distributor/status surfaces.
- It explicitly marks outcome trace, campaign readiness, link/code diagnostics,
  tenant-safe analytics, and webhook/payload diagnostics as dedicated UI
  pending.
- `/admin/referral-saas/operator-links` now gives operators a focused TASK-179
  link/code inspection surface over the TASK-178 product wrapper. It renders
  safe source summary, connected campaign/participant/attribution identifiers,
  missing evidence, source warnings, redactions, and next diagnostics while
  keeping raw source evidence, support-case writes, repair, retry, replay,
  lifecycle commands, reward, money, and DLaaS controls absent.

Implementation should therefore add support UI as a focused workflow, not as a
generic admin dashboard.

## Future Tests

When support workflow implementation starts, add or preserve tests for:

- support case type classification
- link/code to attribution trace navigation
- validation recovery evidence maps to safe next action
- progress failure/dedupe/rejection states map to safe support actions
- report freshness/source warnings remain visible
- operator-only evidence is hidden from account/referrer/customer users
- cross-tenant lookup is rejected or hidden safely
- mutation actions are absent or disabled unless explicitly authorized
- repair/replay commands require actor, reason, correlation, idempotency, and
  audit evidence before execution
- no raw UCN, provider payload, audit payload, DLQ payload, secret, token,
  funding, settlement, commission, wallet, invoice, or payout leakage

## Explicit Non-Goals

- no schema, migration, service, route, permission, frontend, BFF, or test
  implementation
- no support-case table or queue
- no repair, replay, retry, requeue, resolve, override, revoke, expire, reissue,
  void, rotate, publish, activate, export, webhook delivery, notification, or
  mutation implementation
- no customer/referrer exposure of operator diagnostics
- no public API wrapper implementation
- no funding, fulfilment, settlement, commission, wallet, invoice, payout,
  sponsor billing, marketplace-depth, white-label/embed, or SaaS billing work
- no live DB access or production-state verification

## Readiness Decision

Referral SaaS has enough operator primitives to define a production-grade
support workflow, but the workflow is not yet packaged as a product support
surface. TASK-145 defines the case taxonomy, evidence sequence, safe next
actions, permission/redaction boundaries, and mutation guardrails needed before
implementation adds dedicated support UI or BFF behavior.
