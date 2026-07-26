# Referral SaaS Support Case Persistence Contract

TASK ID: TASK-295

Product boundary: Referral Management and Campaign Attribution SaaS.

Status: Contract only. No runtime behavior, schema, route, permission,
frontend, repair/replay action, audit write, or test implementation is added by
this task.

## Boundary

This contract defines how Referral SaaS should persist selected-customer support
cases after the read-only support hub and diagnostic surfaces already exist.

Required boundary docs checked:

- `AGENTS.md`
- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/referral-saas/ROADMAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`
- `docs/roadmap/ORDERED_TASK_LIST.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_SUPPORT_WORKFLOW.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_AUDIT_IDEMPOTENCY_POSTURE.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`

Source files inspected:

- `frontend/src/pages/admin/ReferralSaasSupportHubPage.tsx`
- `services/referral_saas_account_scope_service.py`
- `services/referral_saas_account_foundation_service.py`
- `services/referral_saas_reporting_service.py`
- `apps/api/routers/referral_saas_accounts.py`
- `apps/api/routers/referral_saas_links.py`
- `apps/api/routers/referral_saas_reports.py`

## Purpose

The current Referral SaaS support hub routes operators to read-only evidence.
That is useful for diagnosis, but it does not yet give the product a durable
case trail for:

- who raised a customer issue
- which selected customer/account the issue belongs to
- which safe evidence was reviewed
- what the operator decided next
- whether the case was resolved without exposing raw payloads or mutating
  referral, campaign, progress, attribution, reward, billing, or money state

Support-case persistence closes that product gap without turning support into a
repair console.

## Product Rule

Persisted support cases are customer-scoped investigation records.

They may:

- store a safe summary
- store a case category, priority, status, and assignee/owner reference
- link to safe diagnostic evidence
- record operator notes and status changes
- preserve idempotency and audit evidence

They must not:

- repair, replay, retry, reprocess, requeue, or override anything
- mutate referral, campaign, progress, attribution, report, export, access,
  account, reward, funding, fulfilment, settlement, wallet, invoice, payout, or
  billing state
- expose raw UCNs, provider payloads, audit payloads, DLQ payloads, secrets,
  tokens, credentials, SQL errors, stack traces, or cross-tenant evidence

## Case Scope

Every case must resolve scope from the selected customer account.

Required scope inputs:

| Field | Rule |
|---|---|
| `account_ref` | Opaque selected-customer account reference in the route path. |
| `external_tenant_ref` | Safe customer reference used for selected-customer context. |
| `organisation_ref` | Safe organisation reference when available. |
| `context` | Must be a product context such as `support` or selected-customer maintenance. |
| `actor_ref` | Operator/admin/member identity reference from auth context. |

Caller-supplied internal `tenant_code` is not accepted on product support-case
commands.

## Case Categories

Use the TASK-145 support categories as product categories, not raw database
failure names:

| Category | Use when |
|---|---|
| `VALIDATION_RECOVERY` | A code, link, alias, terms, or validation flow needs support. |
| `PROGRESS_DIAGNOSTIC` | A progress event is missing, rejected, deduped, delayed, or failed. |
| `ATTRIBUTION_REVIEW` | Attribution is missing, partial, conflicting, or needs explanation. |
| `READINESS_BLOCKER` | Account, campaign, access, technical setup, or integration readiness blocks testing. |
| `REPORTING_FRESHNESS` | Report counts, freshness, export requests, or source warnings need review. |
| `INTEGRATION_HEALTH` | API, webhook, event intake, channel, or provider readiness needs review. |
| `ACCESS_SCOPE` | The issue is about roles, account access, or customer scope. |
| `MANUAL_REVIEW_REQUIRED` | Evidence is conflicting or a future governed repair/replay workflow may be needed. |

## Case Statuses

First implementation should keep statuses small and operator-readable:

| Status | Meaning |
|---|---|
| `OPEN` | Case has been created and needs operator review. |
| `INVESTIGATING` | Operator is actively reviewing evidence. |
| `WAITING` | Waiting for customer, source system, provider, or another governed workflow. |
| `RESOLVED` | Operator has recorded the safe resolution outcome. |
| `CLOSED` | Case is closed after resolution or cancellation. |

Status changes must be audit-backed and append-only in history.

## Evidence Links

Support cases should link to evidence by safe reference, not copy raw evidence
payloads.

Allowed evidence link types:

| Evidence type | Safe reference examples |
|---|---|
| `LINK_CODE_INSPECTION` | source type, code/link safe ref, redaction list |
| `ATTRIBUTION_TRACE` | referral track safe ref, trace section, correlation reference |
| `PROGRESS_STATUS` | referral track safe ref, source event ID, dedupe reference |
| `CAMPAIGN_READINESS` | selected account ref, campaign code, readiness evaluation ref |
| `REPORTING_EVIDENCE` | report type, selected account ref, date window, export request ref |
| `TECHNICAL_SETUP` | provider/channel readiness ref, no secret material |
| `PEOPLE_ACCESS` | membership/access posture ref, no credential or auth-claim payload |
| `OPERATOR_NOTE` | safe note text and actor reference |

Evidence links may include safe status, warning, missing-evidence, and redaction
codes. They must not embed raw diagnostic JSON unless a later redaction review
explicitly allows a bounded snapshot.

## Target API Shape

The next implementation tasks should prefer selected-customer routes:

| Route | Method | Purpose |
|---|---|---|
| `/v1/referral-saas/accounts/{account_ref}/support-cases` | `POST` | Create a support case for the selected customer. |
| `/v1/referral-saas/accounts/{account_ref}/support-cases` | `GET` | List support cases for the selected customer. |
| `/v1/referral-saas/accounts/{account_ref}/support-cases/{case_ref}` | `GET` | Read one support case and its safe evidence links. |
| `/v1/referral-saas/accounts/{account_ref}/support-cases/{case_ref}/notes` | `POST` | Add a safe operator note. |
| `/v1/referral-saas/accounts/{account_ref}/support-cases/{case_ref}/status-changes` | `POST` | Move a case through the bounded status lifecycle. |

Future operator-only aggregate routes may exist, but customer-scoped product
work should start from selected-customer account routes.

## Create Command

Request fields:

| Field | Rule |
|---|---|
| `idempotency_key` | Required for create. Same key plus same payload replays; same key plus different payload conflicts. |
| `category` | Must be one of the support categories above. |
| `priority` | `LOW`, `MEDIUM`, `HIGH`, or `CRITICAL`. |
| `title` | Plain-language title, bounded length. |
| `summary` | Safe operator summary, bounded length. |
| `source_surface` | Optional surface that opened the case, such as `support_hub`, `link_inspection`, `attribution_trace`, `progress_status`, `reports`, or `customer_home`. |
| `evidence_links` | Optional list of safe evidence references. |

Response fields:

| Field | Rule |
|---|---|
| `case_ref` | Opaque case reference. |
| `status` | Starts as `OPEN` unless replay returns existing current status. |
| `idempotency_status` | `NEW_REQUEST`, `REPLAY_SAME_PAYLOAD`, or conflict error. |
| `guardrails` | Confirms no repair, replay, retry, campaign activation, invite delivery, credential creation, auth-claim change, export file creation, billing, or money movement. |

## Audit And Idempotency

Every case command must record:

- actor reference
- selected customer account reference
- operation name
- request hash
- idempotency key hash when applicable
- before/after status for status changes
- safe evidence link references
- redaction list
- correlation ID

Same-payload replay must return the original case result without duplicating
case rows, notes, evidence links, or audit records beyond allowed replay
evidence.

Conflicting idempotency reuse must fail safely with no mutation.

## Frontend Product Contract

The selected-customer Support page should eventually show:

1. open support cases for this customer
2. a clear `Create support case` action
3. the source evidence that can be attached
4. the current case status and next action
5. read-only links back to Link Inspection, Attribution Trace, Progress Status,
   Technical Setup, Reports, Campaigns, People and Access, or Account Health

It should not show a generic global helpdesk, raw diagnostic dumps, DB queries,
repair/replay buttons, money actions, or DLaaS marketplace operations.

## Acceptance Criteria For Implementation

Future implementation tasks must prove:

- selected-customer scope is resolved server-side
- cross-tenant account access is rejected or hidden safely
- case create is idempotent
- conflicting idempotency reuse is rejected
- evidence links are redacted and safe
- notes and status changes are audit-backed
- list/read routes return only customer-scoped cases
- support-case creation does not mutate referral, campaign, progress,
  attribution, report, export, access, account lifecycle, reward, billing, or
  money state

## Explicit Non-Goals

- no schema, migration, repository, service, route, frontend, permission, or
  runtime implementation in this task
- no repair, replay, retry, reprocess, requeue, resolve-failure, attribution
  override, code reissue/revoke/rotate, campaign activation, export file
  creation, live invite delivery, credential creation, auth/session claim
  propagation, billing, or money movement
- no DLaaS marketplace, funding, fulfilment, settlement, commission, wallet,
  invoice, payout, sponsor billing, white-label/embed, or SaaS billing work
- no source-code fork

## Next Task

TASK-297 implemented the schema/repository/API foundation for selected-customer
support-case create/list/read with idempotency, audit, and redaction tests.

The next support task should add the selected-customer Support UI for listing
and creating cases against the current customer. Notes, status-change UI,
repair/replay guardrails, and customer-facing support views should remain
separate tasks unless the UI task stays small enough to review safely.
