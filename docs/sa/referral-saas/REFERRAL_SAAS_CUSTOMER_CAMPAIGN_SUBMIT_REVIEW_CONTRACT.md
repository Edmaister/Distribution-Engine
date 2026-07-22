# Referral SaaS Customer-Scoped Campaign Submit/Review Contract

TASK ID: TASK-261

Product boundary: Referral SaaS.

Status: Command-boundary contract only.

Required boundary docs checked:

- `AGENTS.md`
- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/referral-saas/ROADMAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`
- `docs/roadmap/ORDERED_TASK_LIST.md`

Supporting SA docs checked:

- `docs/sa/referral-saas/REFERRAL_SAAS_CAMPAIGN_SETUP_READINESS_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_CUSTOMER_CAMPAIGN_CREATE_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_CUSTOMER_CAMPAIGN_POLICY_SETTINGS_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`

Current implementation files inspected:

- `dp/migrations/002_campaigns.sql`
- `dp/migrations/082_referral_saas_account_foundation.sql`
- `services/campaign_service.py`
- `services/campaign_policy_service.py`
- `services/campaign_readiness_service.py`
- `services/referral_saas_campaign_service.py`
- `apps/api/routers/campaigns.py`
- `apps/api/routers/referral_saas_accounts.py`
- `apps/api/schemas/campaigns.py`
- `services/onboarding/onboarding_submit_for_review_service.py`
- `services/onboarding/onboarding_review_decision_service.py`

## Purpose

Define the selected-customer campaign submit/review boundary that follows
campaign setup draft creation and campaign policy/settings capture.

TASK-256 created inactive campaign setup drafts, TASK-257 added the selected
customer create UX, TASK-258 defined the policy/settings command, TASK-259
implemented the guarded policy/settings API, and TASK-260 added the standalone
policy/settings UX. The next campaign gap is review: the product needs a clear
operator/human checkpoint before activation is even eligible.

This contract defines the product command and UX boundary only. It does not add
runtime behavior, schema, migrations, frontend implementation, campaign
activation, link generation, validation-track creation, webhook delivery,
billing, rewards, funding, fulfilment, settlement, commissions, or money
movement.

## Boundary Decision

Referral SaaS campaign review must be a selected-customer campaign governance
step, not a launch command and not a duplicate of Account Setup review.

Rules:

- Use selected customer account scope from
  `/v1/referral-saas/accounts/{accountRef}`.
- Use selected campaign identity from
  `/v1/referral-saas/accounts/{accountRef}/campaigns/{campaignRef}`.
- Resolve `tenant_code` internally from the selected account and active tenant
  link. Operators must not enter or see tenant identifiers in this flow.
- Submit only campaign setup evidence for human/internal review.
- Record review approval or block decision as campaign-governance evidence.
- Approval makes the campaign eligible for a later activation command; it does
  not activate the campaign.
- Keep link/code generation, validation-track creation, webhook delivery,
  credentials, invite delivery, seat/auth provisioning, billing, reward
  funding, fulfilment, settlement, commissions, and broad DLaaS marketplace
  behavior outside this command.
- Reuse existing campaign, policy, readiness, account-audit, and idempotency
  primitives; do not fork source code.

## Current Facts

Current schema facts:

- `marketing_campaigns` is the existing campaign definition table.
- `marketing_campaigns.campaign_code` is the stable campaign identifier.
- `marketing_campaigns.tenant_code` is the internal tenant scope key and must
  remain hidden from the product UI/API payload.
- `marketing_campaigns.is_active` is the current activation flag used by
  runtime validation and readiness behavior.
- `marketing_campaign_policies` stores the policy/settings evidence captured
  before review.
- `platform_account_audit_events` exists for account-scoped audit evidence and
  includes `event_type`, `event_status`, `previous_status`, `next_status`,
  `reason_code`, `correlation_id`, `idempotency_key_hash`, and `payload_hash`.

Current service/API facts:

- `services/referral_saas_campaign_service.py` already creates inactive
  selected-customer campaign setup drafts and records policy/settings evidence.
- `services/campaign_readiness_service.py` checks campaign definition,
  active-state, date-window, usage-cap, policy, and track-operation readiness.
- `services/campaign_policy_service.py` reads active tenant-specific policy,
  then active global policy, then defaults.
- `services/onboarding/onboarding_submit_for_review_service.py` and
  `services/onboarding/onboarding_review_decision_service.py` provide proven
  idempotency, state-transition, and audit patterns for review flows, but they
  are account-onboarding services, not campaign-review services.
- No customer-scoped campaign submit/review product route exists yet.

## Product Command Contract

Submit route:

`POST /v1/referral-saas/accounts/{accountRef}/campaigns/{campaignRef}/review-submissions`

Review-decision route:

`POST /v1/referral-saas/accounts/{accountRef}/campaigns/{campaignRef}/review-decisions`

Minimum submit request shape:

```json
{
  "accountScope": {
    "refType": "external_tenant_ref",
    "externalRef": "customer-visible-ref",
    "context": "campaign_setup"
  },
  "reviewSubmission": {
    "setupSummary": "Campaign setup and policy settings are ready for review.",
    "requestedReviewStatus": "READY_FOR_REVIEW",
    "operatorNotes": "Optional safe notes for the reviewer."
  },
  "correlationId": "operator-session-or-request-id",
  "idempotencyKey": "stable-campaign-review-submit-key"
}
```

Minimum review-decision request shape:

```json
{
  "accountScope": {
    "refType": "external_tenant_ref",
    "externalRef": "customer-visible-ref",
    "context": "campaign_review"
  },
  "reviewDecision": {
    "decision": "APPROVED",
    "reason": "Campaign setup, policy settings, and readiness evidence reviewed.",
    "reviewerRef": "operator-visible-reviewer-ref"
  },
  "correlationId": "operator-session-or-request-id",
  "idempotencyKey": "stable-campaign-review-decision-key"
}
```

Required command behavior:

- Validate that `accountRef`, `campaignRef`, and `accountScope.externalRef`
  resolve to the same selected customer context.
- Resolve `tenant_code` internally from the selected account.
- Validate the selected campaign exists for the selected customer.
- Validate campaign policy/settings evidence exists before submission.
- Run or read campaign readiness evidence before accepting review submission.
- Allow review decisions only after a successful review submission.
- Reject caller-supplied `tenant_code`, `tenantCode`, `campaign_code`,
  `campaignCode`, `is_active`, `isActive`, `activate`, `goLive`, `link`,
  `track`, `webhook`, `credential`, `invite`, `seat`, `authClaim`, `billing`,
  `funding`, `settlement`, `payout`, or money-movement fields.
- Record idempotency evidence before any write effect in the implementation
  task.
- Return replay for the same idempotency key and same payload hash.
- Return conflict for the same idempotency key and different payload hash.
- Record account/campaign audit evidence with actor, selected account,
  selected campaign, command status, payload hash, correlation ID, and
  previous/next campaign review state.
- Keep the campaign inactive unless a later activation command runs.

Allowed campaign review statuses:

| Status | Meaning | Allowed next action |
| --- | --- | --- |
| `NEEDS_REVIEW_SUBMISSION` | Campaign setup exists but has not been submitted for review. | Submit for review after policy/settings are saved. |
| `READY_FOR_REVIEW` | Setup evidence is submitted for human/internal review. | Record review decision. |
| `REVIEW_APPROVED` | Review passed. | Consider activation in a future command. |
| `REVIEW_BLOCKED` | Review failed or needs more setup work. | Return to campaign setup/policy settings. |
| `READY_TO_ACTIVATE` | Review and readiness gates are satisfied. | Future activation command only. |
| `ACTIVE` | Campaign can support validation and attribution. | Only a future activation command may enter this state. |

TASK-261 does not implement these statuses. It defines the vocabulary and
guardrails future implementation tasks must use.

## Response Contract

Successful submit response:

```json
{
  "status": "CAMPAIGN_REVIEW_SUBMITTED",
  "accountRef": "ACC-1234",
  "campaignRef": "customer-visible-campaign-ref",
  "campaignReview": {
    "reviewStatus": "READY_FOR_REVIEW",
    "setupStatus": "POLICY_SETTINGS_RECORDED",
    "readinessStatus": "NEEDS_REVIEW",
    "reviewerAction": "Record approval or block decision"
  },
  "nextActions": [
    "Review campaign setup evidence",
    "Record campaign review decision",
    "Activate only through a later activation command"
  ],
  "guardrails": [
    "NO_TENANT_CODE_EXPOSURE",
    "NO_CAMPAIGN_ACTIVATION",
    "NO_LINK_GENERATION",
    "NO_VALIDATION_TRACK_CREATED",
    "NO_WEBHOOK_DELIVERY",
    "NO_INVITE_OR_SEAT_CHANGE",
    "NO_MONEY_MOVEMENT"
  ],
  "redactions": [
    "internal_tenant_identifier",
    "idempotency_key_hash",
    "payload_hash"
  ]
}
```

Successful review-decision response:

```json
{
  "status": "CAMPAIGN_REVIEW_APPROVED",
  "accountRef": "ACC-1234",
  "campaignRef": "customer-visible-campaign-ref",
  "campaignReview": {
    "reviewStatus": "REVIEW_APPROVED",
    "activationEligibility": "ELIGIBLE_FOR_FUTURE_ACTIVATION",
    "activationStatus": "NOT_ACTIVATED"
  },
  "nextActions": [
    "Open activation checklist",
    "Confirm links and delivery setup after activation",
    "Keep campaign inactive until activation is approved"
  ],
  "guardrails": [
    "NO_TENANT_CODE_EXPOSURE",
    "NO_CAMPAIGN_ACTIVATION",
    "NO_LINK_GENERATION",
    "NO_VALIDATION_TRACK_CREATED",
    "NO_WEBHOOK_DELIVERY",
    "NO_INVITE_OR_SEAT_CHANGE",
    "NO_MONEY_MOVEMENT"
  ],
  "redactions": [
    "internal_tenant_identifier",
    "idempotency_key_hash",
    "payload_hash"
  ]
}
```

Replay response:

- `CAMPAIGN_REVIEW_SUBMISSION_REPLAYED` for submit replay.
- `CAMPAIGN_REVIEW_DECISION_REPLAYED` for decision replay.
- Same visible campaign-review result as the original accepted command.
- Same no-adjacent-action guardrails.

Conflict/error responses:

- `IDEMPOTENCY_CONFLICT` when the same idempotency key is reused with a
  different payload.
- `CAMPAIGN_SCOPE_MISMATCH` when the campaign does not belong to the selected
  customer account.
- `CAMPAIGN_REVIEW_NOT_READY` when policy/settings or readiness evidence is
  missing.
- `CAMPAIGN_REVIEW_INVALID_STATE` when a decision is attempted before
  submission or after a terminal decision.
- `CAMPAIGN_REVIEW_BLOCKED` when the reviewer blocks launch eligibility.
- `UNSAFE_CAMPAIGN_REVIEW_PAYLOAD` when the caller attempts activation, links,
  validation tracks, credentials, webhooks, invites, seats, auth claims,
  billing, money, or tenant-code exposure.

## Frontend Implications

Selected Customer Profile > Campaigns should expose review as a standalone
customer-scoped campaign page after policy/settings are saved.

Expected UX:

- Open from the selected customer Campaigns page or campaign policy/settings
  success state.
- Display customer name, operating jurisdiction, campaign name, campaign setup
  state, policy/settings state, and readiness summary.
- Do not ask for `tenant_code`.
- Use one primary action at a time:
  - Submit for review when setup evidence is complete.
  - Record review decision after submission.
  - Route to activation only after review approval.
- Show blocked review as a return-to-setup state, not a go-live failure.
- Keep activation and go-live out of the page.

## Explicit Non-Goals

This task does not implement:

- backend routes
- schema or migrations
- runtime campaign review writes
- frontend screens
- campaign activation
- campaign validation or `campaign_track_id` creation
- link/code generation
- webhook delivery
- credential creation
- invite delivery
- membership activation
- seat assignment
- auth/session claim changes
- report/export creation
- billing
- rewards payment
- funding
- fulfilment
- settlement
- commissions
- wallet
- invoice
- payout
- sponsor billing
- treasury
- broad DLaaS marketplace behavior
- source-code forks

## Recommended Next Implementation Slice

TASK-262 should implement the guarded backend wrapper:

- `POST /v1/referral-saas/accounts/{accountRef}/campaigns/{campaignRef}/review-submissions`
- `POST /v1/referral-saas/accounts/{accountRef}/campaigns/{campaignRef}/review-decisions`

That task should reuse selected-account scope resolution, campaign ownership
checks, existing readiness/policy evidence, account audit events, and
idempotency patterns. It must keep campaign activation as a separate future
command.
