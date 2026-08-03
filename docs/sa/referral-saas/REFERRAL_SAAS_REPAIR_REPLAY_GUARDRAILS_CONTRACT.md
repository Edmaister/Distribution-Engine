# Referral SaaS Repair And Replay Guardrails Contract

TASK ID: TASK-336

Product boundary: Referral Management and Campaign Attribution SaaS.

Status: Contract only. No runtime behavior, schema, route, permission,
frontend, repair, replay, retry, provider execution, credential/auth behavior,
campaign activation, billing, money movement, or DLaaS expansion is made by
this task.

## Boundary

This contract defines the governed repair and replay posture for selected
customer support cases and operator diagnostics. It turns the existing support
case, support queue, link/code inspection, progress/status, attribution trace,
report/export, audit, and idempotency material into a reviewed decision model
before any runtime repair/replay API or UI is built.

Required boundary docs checked:

- `AGENTS.md`
- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/referral-saas/ROADMAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_SUPPORT_WORKFLOW.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_AUDIT_IDEMPOTENCY_POSTURE.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_SUPPORT_CASE_PERSISTENCE_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_SUPPORT_QUEUE_CONTRACT.md`
- `docs/roadmap/ORDERED_TASK_LIST.md`

## Purpose

Referral SaaS operators need a safe answer to this question:

```text
Can this issue be retried, replayed, repaired, or only investigated?
```

The answer must be visible before any button exists. Repair/replay actions can
affect customer journeys, attribution evidence, reporting, integrations, and
support audit trails. They must therefore be scoped, reasoned, idempotent, and
reviewable rather than exposed as a generic admin console.

## Action Classes

| Class | Meaning | Launch posture |
| --- | --- | --- |
| `READ_ONLY_DIAGNOSTIC` | Inspect evidence and explain the current state. | Allowed now through existing diagnostics. |
| `READINESS_ONLY` | Return whether a support case is eligible for a future action. | Next runtime task. No mutation. |
| `DRY_RUN_EVIDENCE` | Simulate what a repair/replay would evaluate without mutating state. | Allowed only after explicit route contract and audit readback. |
| `GOVERNED_REPAIR` | Correct a bounded bad state with before/after evidence. | Future command only; requires approval, reason, idempotency, and audit. |
| `GOVERNED_REPLAY` | Reprocess a bounded event or failure from existing stored evidence. | Future command only; requires approval, reason, idempotency, and audit. |
| `HARD_EXCLUDED` | Action is outside Referral SaaS launch scope. | Must not be shown as a support action. |

## Case-To-Action Matrix

| Support category | Readiness allowed | Future repair/replay posture | Hard exclusions |
| --- | --- | --- | --- |
| `VALIDATION_RECOVERY` | Yes. Check whether the issue is user-correctable, duplicate, or evidence-missing. | Repair may only reconcile missing validation evidence after source evidence is present. Replay validation must not create a new referral journey silently. | Reward, money, campaign activation, auth changes, code generation unless a specific lifecycle contract permits it. |
| `PROGRESS_DIAGNOSTIC` | Yes. Check dedupe, payload-hash, queue, failure, and journey compatibility. | Replay may only use stored failure/event evidence and must preserve dedupe behavior. Repair may only correct bounded processing state, not rewrite customer identity. | Raw payload editing, raw UCN exposure, queue flood, unsupported event names, provider dispatch. |
| `ATTRIBUTION_REVIEW` | Yes. Check missing source evidence, conflicts, and trace completeness. | Repair may only record a governed attribution review outcome after trace evidence and reason are present. Replay cannot override attribution without an approved attribution-specific command. | Reward payout, commission, settlement, manual winner override without contract. |
| `REPORTING_FRESHNESS` | Yes. Check export/report freshness, source warnings, retention, and storage state. | Repair may only refresh metadata or mark safe stale/expired states when source evidence supports it. Replay may only replay idempotent export file creation when the original request is still eligible. | Scheduled provider dispatch, invoice/billing, money, download of expired content. |
| `INTEGRATION_HEALTH` | Yes. Check saved configuration, credential request posture, and execution-readiness evidence. | Repair/replay remains blocked until provider/vault execution contracts exist. | Live webhook dispatch, provider calls, credential creation/reveal/rotation, auth/session change. |
| `ACCESS_SCOPE` | Yes. Check account, membership, accepted access, and provisioning posture. | Repair may only route to governed people/access or auth/login workflows. | Silent seat assignment, login credential creation, auth-claim propagation from support. |
| `READINESS_BLOCKER` | Yes. Show blocker and owning workflow. | Repair is not a support shortcut; route to Account, People and Access, Integrations, Campaigns, Reports, or Support owner workflow. | Go-live bypass, campaign activation, money movement. |
| `MANUAL_REVIEW_REQUIRED` | Yes. Must show why review is required. | Future command requires operator approval, reason, support-case link, idempotency key, and audit evidence. | Any action without before/after evidence and approval. |

## Readiness Response Contract

Future TASK-337 readiness APIs should return a safe support-case-scoped
envelope:

```json
{
  "caseRef": "case_123",
  "accountRef": "ACCT_SAFE",
  "category": "PROGRESS_DIAGNOSTIC",
  "overallStatus": "REVIEW_REQUIRED",
  "allowedActions": [
    {
      "action": "READ_ONLY_DIAGNOSTIC",
      "status": "AVAILABLE",
      "label": "Review evidence"
    },
    {
      "action": "GOVERNED_REPLAY",
      "status": "BLOCKED",
      "reasonCode": "APPROVAL_REQUIRED",
      "label": "Replay stored progress event"
    }
  ],
  "requiredEvidence": [
    "support_case_link",
    "actor",
    "reason",
    "correlation_id",
    "idempotency_key",
    "before_state_hash"
  ],
  "redactions": [
    "raw_ucn",
    "provider_payload"
  ],
  "guardrails": [
    "NO_PROVIDER_DISPATCH",
    "NO_CREDENTIAL_CHANGE",
    "NO_CAMPAIGN_ACTIVATION",
    "NO_BILLING",
    "NO_MONEY_MOVEMENT"
  ]
}
```

Readiness is not permission to execute. It is only the plain-language decision
record that tells the operator which workflow owns the next action.

## Required Gates Before A Future Command

Every future governed repair/replay command must require:

- selected-customer account scope from `accountRef`
- support case link or operator queue item link
- actor identity and role
- explicit reason
- correlation ID
- idempotency key
- target reference and target type
- before-state hash or stable read-model evidence
- approved action class
- expected side-effect boundary
- redaction list
- audit event with outcome and after-state hash where state changes

Same idempotency key with the same payload must replay the same safe result.
Same idempotency key with different payload must return conflict. Reads and
readiness checks must stay side-effect free.

## Explicitly Blocked Actions

Repair/replay guardrails must not permit:

- editing raw database rows from the UI
- replaying arbitrary DLQ payloads from a customer support screen
- exposing raw UCNs, provider payloads, audit payloads, worker stack traces,
  secrets, tokens, signing material, API keys, or credential values
- creating, revealing, rotating, revoking, or downloading credentials
- calling providers or dispatching webhooks/messages unless a later provider
  execution task explicitly permits it
- creating login credentials or propagating auth claims
- silently assigning seats outside the governed People and Access workflow
- activating campaigns or triggering go-live
- creating rewards, funding, fulfilment, settlement, commission, invoice,
  payout, wallet, sponsor billing, or any money movement
- expanding into broader DLaaS marketplace, fulfilment, settlement, funding,
  sponsor billing, white-label, or embedded distribution workflows

## Frontend Expectations

Future UI should show:

- read-only evidence first
- a simple answer: `No action needed`, `Fix in another workflow`,
  `Review required`, or `Ready for governed action`
- the owning workflow for the next action
- required evidence before a governed button can be enabled
- disabled or absent repair/replay controls until readiness says the action is
  eligible
- plain-language labels rather than internal queue or worker vocabulary

The support queue and selected-customer support page must not become a mutation
console. They should explain, route, and record review posture first.

## Test Expectations

Future implementation tasks should add tests for:

- read-only readiness does not mutate support cases or source objects
- unsupported categories return `ACTION_NOT_SUPPORTED`
- missing support-case link blocks governed actions
- missing actor, reason, correlation ID, idempotency key, or before-state
  evidence blocks governed actions
- same-payload idempotency replay returns the original result
- different-payload idempotency conflict is rejected
- redactions remove raw UCN, provider payload, audit payload, DLQ payload,
  secrets, tokens, and signing material
- no repair/replay action triggers provider dispatch, credential/auth changes,
  campaign activation, billing, money movement, or DLaaS side effects

## Explicit Non-Goals

- no schema or migration
- no backend route or service implementation
- no frontend controls
- no repair, replay, retry, reprocess, requeue, resolve, override, revoke,
  expire, reissue, rotate, provider dispatch, credential execution, auth,
  campaign activation, export delivery, billing, money, or DLaaS action
- no public customer/referrer exposure of operator diagnostics

## Readiness Decision

Referral SaaS now has a reviewed repair/replay guardrail contract. The next
tasks can add read-only support-case readiness and then UI visibility without
creating unsafe repair buttons or duplicating platform primitives.
