# Referral SaaS Support Queue Contract

TASK ID: TASK-324

Product boundary: Referral Management and Campaign Attribution SaaS.

Status: Contract defined. Runtime aggregate queue API, UI, assignment workflow,
repair/replay actions, export file delivery, provider execution, credential/auth
actions, billing, and money movement remain separate governed tasks.

## Boundary

This contract defines the operator aggregate support queue that sits above the
selected-customer support cases implemented through TASK-297, TASK-321,
TASK-322, and TASK-323.

Required boundary docs checked:

- `AGENTS.md`
- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/referral-saas/ROADMAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_SUPPORT_CASE_PERSISTENCE_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`
- `docs/roadmap/ORDERED_TASK_LIST.md`

Source files inspected:

- `services/referral_saas_support_case_service.py`
- `apps/api/routers/referral_saas_accounts.py`
- `docs/sa/referral-saas/REFERRAL_SAAS_SUPPORT_CASE_PERSISTENCE_CONTRACT.md`

## Purpose

Selected-customer Support now lets an operator create, list, read, note, and
change status on a single customer's cases. That is useful inside a customer
profile, but it does not answer the operator's queue question:

Which customer issues need attention across the Referral SaaS portfolio?

The aggregate queue provides a safe triage view across customer-scoped support
cases. It must remain a read-only queue/read model until a later task adds a
reviewed assignment or work-allocation command.

## Product Rule

The operator support queue is a cross-customer triage read model.

It may:

- list safe case metadata across selected Referral SaaS customers
- filter by case status, priority, category, account reference, source surface,
  assignee reference, and updated/created date windows
- sort the queue by urgency and recent activity
- show safe customer identifiers needed to route the operator into the selected
  customer profile
- link back to the selected-customer Support page for the actual case lifecycle

It must not:

- create, update, assign, resolve, close, repair, replay, retry, reprocess, or
  override a case
- mutate referral, campaign, progress, attribution, report, export, access,
  account lifecycle, reward, funding, fulfilment, settlement, wallet, invoice,
  payout, billing, or money state
- expose raw UCNs, provider payloads, audit payloads, DLQ payloads, secrets,
  tokens, credentials, SQL errors, stack traces, or cross-tenant raw evidence

## Target API Shape

The target route is operator-scoped because it crosses selected-customer pages.

| Route | Method | Purpose |
|---|---|---|
| `/v1/referral-saas/operator/support-cases` | `GET` | Read a safe aggregate queue of customer-scoped support cases. |

Selected-customer case work remains on:

- `GET /v1/referral-saas/accounts/{account_ref}/support-cases`
- `GET /v1/referral-saas/accounts/{account_ref}/support-cases/{case_ref}`
- `POST /v1/referral-saas/accounts/{account_ref}/support-cases/{case_ref}/notes`
- `POST /v1/referral-saas/accounts/{account_ref}/support-cases/{case_ref}/status`

## Query Contract

The first implementation should support only fields backed by the current
support-case service and account context.

| Query field | Rule |
|---|---|
| `status` | Optional bounded case status: `OPEN`, `INVESTIGATING`, `WAITING`, `RESOLVED`, or `CLOSED`. Multiple statuses may be added later. |
| `priority` | Optional bounded priority: `LOW`, `MEDIUM`, `HIGH`, or `CRITICAL`. |
| `category` | Optional bounded support category from the support-case persistence contract. |
| `account_ref` | Optional opaque account reference. Internal tenant codes are not accepted. |
| `source_surface` | Optional safe source surface from the support-case contract. |
| `assignee_ref` | Optional safe operator/member reference when present on the case. |
| `created_from` / `created_to` | Optional date-time window for queue creation date. |
| `updated_from` / `updated_to` | Optional date-time window for recent activity. |
| `limit` | Optional bounded page size; must not exceed the service maximum. |
| `cursor` | Optional opaque cursor for later pagination. First implementation may use offset-free keyset pagination. |

Unsupported filters must fail with a safe validation error rather than silently
leaking internal schema details.

## Queue Item Contract

Each queue item should be enough to choose the next case, not enough to expose
raw diagnostics.

| Field | Rule |
|---|---|
| `case_ref` | Opaque support case reference. |
| `account_ref` | Opaque selected-customer account reference. |
| `customer_label` | Safe display label derived from account/customer references when available. |
| `external_tenant_ref` | Safe customer reference when already exposed in selected-customer context. |
| `organisation_ref` | Safe organisation reference when already exposed in selected-customer context. |
| `category` | Bounded support category. |
| `priority` | Bounded priority. |
| `status` | Bounded current status. |
| `title` | Plain-language safe title. |
| `source_surface` | Safe source surface that opened the case. |
| `assignee_ref` | Safe assignee/operator reference when present. |
| `created_at` / `updated_at` | Case timestamps. |
| `evidence_link_count` | Count only. Raw evidence is not embedded. |
| `note_count` | Count only. Notes remain on the selected-customer case read page unless explicitly expanded by a later task. |
| `latest_activity` | Safe activity summary such as last status, note type, or update time. |
| `redactions` | Redaction codes applied to the queue item. |
| `next_action` | Plain-language route hint such as `Open customer support case`. |

## Ordering

Default ordering should be deterministic:

1. unresolved cases before resolved/closed cases
2. `CRITICAL`, `HIGH`, `MEDIUM`, then `LOW`
3. recently updated cases before older cases
4. stable case reference tie-breaker

The queue should not use random ordering, hidden priority overrides, or raw
database error order.

## Frontend Product Contract

The future operator queue UI should be a separate Support Queue page, not a
stacked panel inside a selected customer profile.

It should show:

- a compact queue header with open, investigating, waiting, and critical counts
- filters for status, priority, category, customer, and source surface
- case rows with customer label, category, priority, status, safe title, latest
  activity, and `Open case`
- clear empty states such as `No open support cases`
- direct routing into the selected-customer Support case page

It should not show raw diagnostic payloads, all case notes by default, repair
buttons, replay buttons, retry buttons, export creation, provider execution,
credential/auth actions, billing, money, or DLaaS marketplace controls.

## Audit, Idempotency, And Redaction

The queue route is read-only. It does not require a command idempotency key.

It must still preserve:

- operator/support/admin auth scope
- tenant/account-safe filtering
- correlation ID propagation where available
- safe validation errors
- redactions for internal tenant identifiers, raw UCNs, provider payloads,
  audit payloads, DLQ payloads, secrets, tokens, credentials, SQL errors, stack
  traces, idempotency-key hashes, and payload hashes
- no-adjacent-action guardrails in the response metadata

## Acceptance Criteria For Implementation

Future implementation tasks must prove:

- the queue reads from persisted support cases rather than a UI-only cache
- operator scope is enforced server-side
- internal tenant code is never accepted as a product query parameter
- account/customer labels are safe and customer-scoped
- filters are bounded and reject unsupported values safely
- queue items exclude raw evidence and secret/provider/auth payloads
- opening a queue item routes back to the selected-customer Support context
- the route is read-only and cannot mutate cases or adjacent product state

## Explicit Non-Goals

- no schema, migration, repository, service, route, frontend, permission, or
  runtime implementation in this task
- no support assignment workflow
- no case create/note/status mutation from the aggregate queue
- no repair, replay, retry, reprocess, requeue, failure resolution, attribution
  override, code reissue/revoke/rotate, campaign activation, export file
  creation, live invite delivery, credential creation, auth/session claim
  propagation, billing, or money movement
- no DLaaS marketplace, funding, fulfilment, settlement, commission, wallet,
  invoice, payout, sponsor billing, white-label/embed, or SaaS billing work
- no source-code fork

## Next Task

After this contract, the next support task should implement the read-only
operator aggregate queue API over the existing support-case persistence model,
with route inventory and API tests. The queue UI should follow only after the
backend read model is proven.
