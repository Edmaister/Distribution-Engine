# Referral SaaS Safe Status Contract

TASK ID: TASK-141

Product boundary: Referral Management and Campaign Attribution SaaS.

Status: Contract only. No runtime behavior, schema, route, frontend, permission,
or test changes are made by this task.

## Boundary

This contract defines how Referral SaaS should present referrer/customer-safe
status and next action without exposing raw referral, progress, reward,
provider, audit, tenant, or money-operation internals.

Required boundary docs checked:

- `docs/product/README.md`
- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/README.md`
- `docs/roadmap/referral-saas/ROADMAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_VALIDATION_RECOVERY_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_PROGRESS_EVENT_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_ATTRIBUTION_TRACE_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_LINK_CODE_INVESTIGATION_CONTRACT.md`
- `docs/sa/PARTNER_CUSTOMER_SAFE_STATUS_CONTRACT.md`

Source files inspected:

- `services/partner_customer_safe_status_service.py`
- `services/reward_summary_service.py`
- `services/progress_service.py`
- `apps/api/routers/consumer_experience.py`
- `apps/api/routers/reward_summary.py`
- `test/test_partner_customer_safe_status_service.py`
- `test/test_consumer_experience_api.py`
- `test/test_reward_summary_api.py`
- `test/test_progress_service.py`
- `test/test_progress_api.py`

## Purpose

Referral SaaS needs a safe answer for referrers and referred customers:

```text
Where is this referral, what happened, what happens next, and do I need to do
anything?
```

That answer must not expose:

- raw UCNs or private identifiers
- raw fraud/risk, provider, retry, DLQ, audit, or worker details
- internal tenant codes on public/customer surfaces
- raw progress-event failure internals
- funding, fulfilment, settlement, commission, or sponsor billing details

The repository already has a broad role-safe projection helper in
`services.partner_customer_safe_status_service`. TASK-141 defines the focused
Referral SaaS status contract that should use that helper rather than inventing
a separate status system.

## Current Implementation Facts

Current broad safe-status helper:

- `project_partner_customer_safe_status`
- `project_safe_statuses`
- supports viewer roles `partner`, `distributor`, `sponsor`, `producer`,
  `referrer`, and `customer`
- maps source families including `outcome`, `campaign`, `reward`,
  `fulfilment`, `settlement`, `webhook`, `funding`, and related families
- rejects unsafe keys such as `tenant_code`, `raw_ucn`, `provider_payload`,
  secrets, tokens, audit payloads, and settlement internals
- returns safe status, label, summary, what happened, what happens next, action
  category, terminal flag, source families, confidence, missing evidence, and
  redactions

Current safe status vocabulary:

- `NOT_STARTED`
- `PENDING`
- `IN_PROGRESS`
- `QUALIFIED`
- `APPROVED`
- `FULFILLED`
- `SETTLED`
- `ADJUSTED`
- `DECLINED`
- `EXPIRED`
- `ACTION_REQUIRED`
- `UNAVAILABLE`

Current action categories:

- `NONE`
- `WAITING_FOR_EVENT`
- `RETRY_LATER`
- `CONTACT_SUPPORT`
- `NOT_AVAILABLE`
- plus broader DLaaS categories such as `VERIFY_PAYMENT_DETAILS`,
  `REVIEW_DISPUTE`, and `ACCEPT_OFFER`

Current consumer/referrer surfaces:

- `GET /v1/experience/consumer`
- aggregates profile/referrals, rewards, missions, leaderboard, and optional
  insurance proof sections
- enforces tenant scope through `require_consumer_scope`
- returns partial/degraded section states when sections fail or time out
- currently exposes `tenantCode` and `referrerUcn` in the response shape

Current reward summary surfaces:

- `GET /v1/rewards/summary/referrers/{referrer_ucn}`
- `GET /v1/rewards/summary/{referral_track_id}`
- reads reward rows and referral counts
- returns reward item source statuses such as `APPLIED` and `PENDING`
- includes compliance/disclosure metadata

Current progress foundation:

- `POST /v1/progress` records valid progress events and dedupes duplicate
  source events
- `referral_instances` stores journey snapshot fields such as status,
  milestone timestamps, progress, and next milestone in the broader flow
- progress failures and invalid events are not customer-safe by default

## First-Launch Referral SaaS Safe Status Scope

First launch safe status should cover these source families:

| Source family | Safe for referrer | Safe for customer | Notes |
|---|---|---|---|
| `outcome` | Yes | Yes | Referral journey state and progress. |
| `campaign` | Bounded | Bounded | Only safe campaign availability/window messages, not internal readiness. |
| `reward` | Yes for own visible rewards | Yes only for own visible benefit where applicable | Reward summaries may remain visible if already supported. |
| `fulfilment` | Optional bounded status | Optional bounded status | Use existing external-safe fulfilment mapping only. |
| `attribution` | Bounded summary only | Bounded summary only | Do not expose operator trace evidence. |
| `link_code` | Bounded validation/source status only | Bounded validation/source status only | Do not expose operator evidence shape. |
| `progress` | Yes as safe milestones | Yes as safe milestones | Do not expose raw event/retry/error details. |

First launch should not expose:

- funding account operations
- settlement batches
- distributor commissions
- sponsor billing
- fulfilment provider routing internals
- raw outcome trace sections
- operator link/code evidence
- raw campaign readiness blockers

## Referral SaaS Safe Status Vocabulary

Referral SaaS should use the broad safe-status vocabulary, but the first-launch
customer/referrer copy should stay focused:

| Product status | Maps to broad safe status | Product meaning |
|---|---|---|
| `NOT_STARTED` | `NOT_STARTED` | The referral journey has not started or no safe evidence exists yet. |
| `WAITING` | `PENDING` | The platform is waiting for validation, identity capture, or progress evidence. |
| `IN_PROGRESS` | `IN_PROGRESS` | The referral has started and qualifying events are still being processed. |
| `QUALIFIED` | `QUALIFIED` | The referral has met a qualification milestone, but final visible completion may still be pending. |
| `COMPLETED` | `FULFILLED` | The referral journey or visible benefit is complete for this viewer. |
| `EXPIRED` | `EXPIRED` | The campaign, link, or opportunity window is no longer valid. |
| `ACTION_NEEDED` | `ACTION_REQUIRED` | Support or the viewer must take safe next action. |
| `UNAVAILABLE` | `UNAVAILABLE` | Current source truth cannot safely show status. |

The API/service layer may continue returning broad safe statuses. UI/product
copy may map them to the product labels above, but must not invent new backend
states.

## Source Status Mapping

### Referral Outcome

Use `source_family=outcome` through the broad safe-status helper.

| Current source state/evidence | Referrer/customer safe status | Safe next action |
|---|---|---|
| no referral instance or inaccessible subject | `UNAVAILABLE` | Check again later or contact support if expected. |
| validation not completed | `PENDING` | Accept terms or complete validation if prompted. |
| `VALIDATED` | `PENDING` | Wait for identity/progress evidence. |
| `UCN_CAPTURED` | `IN_PROGRESS` | No action unless identity evidence is incomplete. |
| `ACCOUNT_OPENED`, `ACCOUNT_ACTIVATED`, `FUNDED` | `IN_PROGRESS` or `QUALIFIED` depending product milestone | Wait for next milestone. |
| `COMPLETED` | `FULFILLED` | No action required. |
| `CANCELLED` | `ACTION_REQUIRED` or `UNAVAILABLE` depending visibility | Contact support; do not expose raw reason. |

### Validation And Recovery

Use TASK-137 product validation states as input to safe copy.

| Validation product state | Safe status | Safe action |
|---|---|---|
| `VALIDATED` | `PENDING` | Continue journey or wait for next event. |
| `REJECTED_TERMS_REQUIRED` | `ACTION_REQUIRED` | Accept terms to continue. |
| `REJECTED_ALIAS` | `ACTION_REQUIRED` | Choose a different alias. |
| `REJECTED_CODE_NOT_FOUND` | `UNAVAILABLE` | Check the code or contact support. |
| `RECOVERY_REQUIRED_LOGGING` | `ACTION_REQUIRED` | Contact support; durable journey evidence is incomplete. |
| `RECOVERY_REQUIRED_IDENTITY_CAPTURE` | `ACTION_REQUIRED` | Complete identity step if prompted. |
| `FAILED` | `UNAVAILABLE` | Contact support without exposing internals. |

### Progress Events

Use TASK-138 product event outcomes as input to status projection.

| Progress product state | Safe status | Safe action |
|---|---|---|
| `RECORDED` | `IN_PROGRESS` | No action required. |
| `DEDUPED` | `IN_PROGRESS` | No action required; do not expose duplicate internals. |
| `QUEUED` | `IN_PROGRESS` | Wait for status update. |
| rejected due to unsupported event, journey mismatch, identity mismatch, or product mismatch | `ACTION_REQUIRED` or `UNAVAILABLE` | Contact support; do not expose raw validation details. |
| `FAILED_TO_QUEUE` or `FAILED` | `UNAVAILABLE` | Try again later or contact support. |

### Campaign, Link, And Attribution

Use campaign/link/attribution evidence only as bounded context:

| Evidence | Safe status | Safe action |
|---|---|---|
| active campaign/link exists | `APPROVED` or product `WAITING` | Continue or wait for referral progress. |
| campaign/link expired | `EXPIRED` | Use a current link/code if available. |
| attribution trace complete for the viewer's outcome | `QUALIFIED` or `COMPLETED` depending outcome status | No action unless reward/benefit remains pending. |
| trace partial or missing evidence | `UNAVAILABLE` or `ACTION_REQUIRED` | Contact support if status appears stuck. |

Do not expose operator-only trace sections, missing-evidence source tables, or
link/code inspect evidence on referrer/customer surfaces.

### Reward Summary

Reward summary may remain visible when already supported, but it must be safe:

| Reward source state | Safe status | Safe action |
|---|---|---|
| `APPLIED` | `APPROVED` | No action required. |
| `EARNED` | `QUALIFIED` | No action required. |
| `PENDING` or `PENDING_FULFILMENT` | `IN_PROGRESS` | Wait for processing. |
| `FULFILLED` | `FULFILLED` | No action required. |
| `FAILED` | `ACTION_REQUIRED` | Contact support. |
| missing reward evidence | `PENDING` or `UNAVAILABLE` | Wait for evidence or contact support. |

Reward amount/disclosure behavior remains governed by reward summary services
and compliance metadata. This contract does not authorize deeper money movement
or settlement visibility.

## Recommended Response Shape

Future Referral SaaS safe-status APIs or BFF sections should return:

```json
{
  "status": "ok",
  "viewerRole": "referrer",
  "subject": {
    "type": "referral",
    "safeRef": "referral:track:11111111-1111-4111-8111-111111111111"
  },
  "safeStatus": {
    "status": "IN_PROGRESS",
    "productStatus": "IN_PROGRESS",
    "label": "In progress",
    "summary": "Your referral is in progress.",
    "whatHappened": "The referral was validated and progress evidence was received.",
    "whatHappensNext": "The platform will update this status when the next milestone is confirmed.",
    "actionRequired": false,
    "actionCategory": "NONE",
    "terminal": false,
    "sourceFamilies": ["outcome", "progress"],
    "sourceConfidence": "MEDIUM",
    "missingEvidence": [],
    "redactions": ["private_identifier", "raw_status"]
  },
  "sections": {
    "referral": {},
    "campaign": {},
    "reward": {}
  }
}
```

Field requirements:

- use `safeRef` instead of raw UCNs or raw customer identifiers
- keep raw backend state names out of customer/referrer copy
- include `missingEvidence` only as safe codes, not raw source tables or joins
- include `redactions` when data was intentionally hidden
- do not include `tenantCode` on public/customer views unless the route is
  explicitly internal/operator scoped

## Current Surface Gaps

Current code provides useful building blocks, but these are not yet a complete
Referral SaaS safe-status product surface:

- `consumer_experience` currently returns `tenantCode` and `referrerUcn`, so it
  needs a safe product wrapper before being treated as public customer/referrer
  status.
- reward summary routes return reward item source statuses such as `APPLIED` and
  `PENDING`; a product wrapper should project them through the safe-status
  helper for customer/referrer views.
- operator attribution trace and link/code inspection are intentionally too
  detailed for referrer/customer surfaces.
- progress event rejection reasons are support diagnostics, not direct
  customer/referrer copy.

These gaps are packaging and projection gaps, not proof that the core referral
or progress foundations are missing.

## Current Product Wrapper Fact

TASK-182 implements
`GET /v1/referral-saas/operator/referrals/{referral_track_id}/progress-status`
as an operator-scoped product wrapper that reuses the Referral SaaS
safe-status projection helper over existing progress evidence.

The route returns `safeStatus`, `missingEvidence`, `redactions`, safe progress
fields, and bounded `nextDiagnostics` without exposing raw UCN values or
adding customer/referrer-safe public status behavior. It remains read-only and
does not add progress mutation, support-case writes, repair/replay/retry,
reward, funding, fulfilment, settlement, commission, wallet, invoice, payout,
or broad DLaaS behavior.

## Future Tests

When this contract becomes implementation work, add or preserve tests for:

- referrer and customer role projections from `outcome`, `progress`, `campaign`,
  `link_code`, `attribution`, and `reward` evidence
- no raw UCN, tenant code, provider payload, audit payload, DLQ, secret, token,
  or raw status leakage
- validation recovery states map to safe status and next action
- progress rejected/failed states map to safe status without raw internals
- reward summary source statuses map to safe statuses
- cross-tenant or adjacent-role access returns safe 403/404 behavior
- frontend renders product labels and next action without internal state names
- degraded/partial sections remain bounded and do not expose exception text

## Explicit Non-Goals

- no schema, migration, service, route, permission, frontend, or test changes
- no public API wrapper implementation
- no reward, funding, fulfilment, settlement, commission, sponsor billing, or
  marketplace-depth implementation
- no exposure of operator attribution trace or link/code inspect evidence to
  customers/referrers
- no raw state, tenant, UCN, provider, audit, DLQ, token, or secret exposure
- no mutation, repair, retry, replay, fulfilment, settlement, payout, invoice,
  webhook dispatch, or notification action

## Readiness Decision

Referral SaaS has the core safe-status foundation through the shared
partner/customer safe-status helper and existing consumer/reward/progress
surfaces. TASK-141 defines the focused referrer/customer contract needed to
turn those foundations into a product-safe status experience without mixing in
operator diagnostics or broader DLaaS money workflows.
