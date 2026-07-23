# Referral SaaS Customer-Scoped Campaign Activation Contract

TASK ID: TASK-264

Product boundary: Referral SaaS.

Status: Command-boundary contract only.

Required boundary docs checked:

- `AGENTS.md`
- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/referral-saas/ROADMAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`
- `docs/roadmap/ORDERED_TASK_LIST.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_CUSTOMER_CAMPAIGN_SUBMIT_REVIEW_CONTRACT.md`

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
- `test/test_referral_saas_campaign_service.py`
- `test/api/test_referral_saas_accounts_api.py`

## Purpose

Define the selected-customer campaign activation/go-live boundary that follows
approved campaign review.

TASK-256 through TASK-263 now let the Referral SaaS product create an inactive
campaign setup draft, capture policy/settings evidence, submit campaign setup
for review, record approval or block decisions, and show that review workflow in
the selected customer Campaigns module. The next dangerous product gap is
activation: approval must not be treated as launch, and launch must not
quietly create links, validation tracks, webhooks, credentials, access changes,
billing, or money movement.

This contract defines the product command and UX boundary only. It does not add
runtime behavior, schema, migrations, frontend implementation, campaign
activation, link generation, validation-track creation, webhook delivery,
credentials, billing, rewards, funding, fulfilment, settlement, commissions, or
money movement.

## Boundary Decision

Referral SaaS activation must be a separate selected-customer campaign command,
not a side effect of review approval, policy save, campaign creation, link/code
setup, or technical setup.

Rules:

- Use selected customer account scope from
  `/v1/referral-saas/accounts/{accountRef}`.
- Use selected campaign identity from
  `/v1/referral-saas/accounts/{accountRef}/campaigns/{campaignRef}`.
- Resolve `tenant_code` internally from the selected account and active tenant
  link. Operators must not enter or see tenant identifiers in this flow.
- Require approved campaign-review evidence before activation can be requested.
- Require readiness evidence that is not blocked for activation/go-live.
- Mutate only the campaign activation/lifecycle posture in the implementation
  task.
- Keep link/code generation, validation-track creation, webhook delivery,
  credentials, invite delivery, membership activation, seat/auth provisioning,
  billing, reward funding, fulfilment, settlement, commissions, and broad DLaaS
  marketplace behavior outside this command.
- Reuse existing campaign, policy, readiness, review, account-audit, and
  idempotency primitives; do not fork source code.

## Current Facts

Current schema facts:

- `marketing_campaigns` is the existing campaign definition table.
- `marketing_campaigns.campaign_code` is the stable campaign identifier.
- `marketing_campaigns.tenant_code` is the internal tenant scope key and must
  remain hidden from product UI/API payloads.
- `marketing_campaigns.is_active` is the current campaign activation flag used
  by validation and readiness behavior.
- `marketing_campaigns.attributes` currently stores Referral SaaS setup and
  review metadata such as `referral_saas_review`.
- `marketing_campaign_policies` stores the policy/settings evidence captured
  before review and activation.
- `platform_account_audit_events` exists for account-scoped audit evidence and
  includes `event_type`, `event_status`, `previous_status`, `next_status`,
  `reason_code`, `correlation_id`, `idempotency_key_hash`, and `payload_hash`.

Current service/API facts:

- `services/referral_saas_campaign_service.py` already creates inactive
  selected-customer campaign setup drafts and records policy/settings evidence.
- `services/referral_saas_campaign_service.py` already records campaign review
  submission and review decision evidence.
- Approved review currently returns `REVIEW_APPROVED`,
  `ELIGIBLE_FOR_FUTURE_ACTIVATION`, and `NOT_ACTIVATED`.
- `services/campaign_readiness_service.py` checks campaign definition,
  active-state, date-window, usage-cap, policy, and track-operation readiness.
- No customer-scoped campaign activation/go-live product route exists yet.

## Product Command Contract

Activation route:

`POST /v1/referral-saas/accounts/{accountRef}/campaigns/{campaignRef}/activation-requests`

Minimum request shape:

```json
{
  "accountScope": {
    "refType": "external_tenant_ref",
    "externalRef": "customer-visible-ref",
    "context": "campaign_activation"
  },
  "activationRequest": {
    "requestedLifecycleStatus": "ACTIVE",
    "reviewStatus": "REVIEW_APPROVED",
    "goLiveReason": "Campaign setup, policy, readiness, and review evidence approved.",
    "activationWindow": {
      "startsAt": "2026-08-01T00:00:00Z",
      "endsAt": "2026-09-30T23:59:59Z"
    },
    "operatorNotes": "Optional safe notes for the activation decision."
  },
  "correlationId": "operator-session-or-request-id",
  "idempotencyKey": "stable-campaign-activation-key"
}
```

Required command behavior:

- Validate that `accountRef`, `campaignRef`, and `accountScope.externalRef`
  resolve to the same selected customer context.
- Resolve `tenant_code` internally from the selected account.
- Validate the selected campaign exists for the selected customer.
- Validate campaign policy/settings evidence exists.
- Validate campaign review evidence exists and is `REVIEW_APPROVED`.
- Validate campaign activation eligibility is
  `ELIGIBLE_FOR_FUTURE_ACTIVATION`.
- Validate readiness evidence is sufficient for activation and is not blocked.
- Reject activation when the selected campaign is already active unless the
  same accepted command is replayed by idempotency.
- Reject caller-supplied `tenant_code`, `tenantCode`, `campaign_code`,
  `campaignCode`, `is_active`, `isActive`, `active`, `activate`, `goLive`,
  `link`, `track`, `campaign_track_id`, `webhook`, `credential`, `invite`,
  `seat`, `authClaim`, `billing`, `funding`, `settlement`, `payout`, or
  money-movement fields.
- Record idempotency evidence before any write effect in the implementation
  task.
- Return replay for the same idempotency key and same payload hash.
- Return conflict for the same idempotency key and different payload hash.
- Record account/campaign audit evidence with actor, selected account,
  selected campaign, command status, payload hash, correlation ID, previous
  lifecycle state, and next lifecycle state.
- Mutate only the selected campaign activation/lifecycle posture.

Allowed activation statuses:

| Status | Meaning | Allowed next action |
| --- | --- | --- |
| `NOT_ACTIVATED` | Campaign setup/review may exist but activation has not run. | Request activation only after approved review and readiness. |
| `ACTIVATION_BLOCKED` | Activation request failed a precondition. | Return to the named setup, policy, review, readiness, or customer module. |
| `READY_TO_ACTIVATE` | Review and readiness gates are satisfied. | Run the activation command. |
| `ACTIVATION_REQUEST_ACCEPTED` | The activation command accepted the lifecycle change. | Open customer campaign operations. |
| `ACTIVE` | Campaign can support validation and attribution. | Continue to link/code setup and live monitoring as separate modules. |

TASK-264 does not implement these statuses. It defines the vocabulary and
guardrails future implementation tasks must use.

## Response Contract

Successful activation response:

```json
{
  "status": "CAMPAIGN_ACTIVATION_ACCEPTED",
  "accountRef": "ACC-1234",
  "campaignRef": "customer-visible-campaign-ref",
  "campaignActivation": {
    "previousLifecycle": "READY_TO_ACTIVATE",
    "lifecycle": "ACTIVE",
    "reviewStatus": "REVIEW_APPROVED",
    "activationEligibility": "ELIGIBLE_FOR_FUTURE_ACTIVATION",
    "activationStatus": "ACTIVATION_REQUEST_ACCEPTED"
  },
  "nextActions": [
    "Open customer campaign operations",
    "Create or issue links and codes through the customer-scoped Links module",
    "Monitor readiness, attribution, progress, and reporting separately"
  ],
  "guardrails": [
    "NO_TENANT_CODE_EXPOSURE",
    "NO_LINK_GENERATION",
    "NO_VALIDATION_TRACK_CREATED",
    "NO_WEBHOOK_DELIVERY",
    "NO_INVITE_OR_SEAT_CHANGE",
    "NO_CREDENTIAL_CREATION",
    "NO_BILLING_OR_MONEY_MOVEMENT"
  ],
  "redactions": [
    "internal_tenant_identifier",
    "idempotency_key_hash",
    "payload_hash"
  ]
}
```

Replay response:

- `CAMPAIGN_ACTIVATION_REPLAYED`
- Same visible campaign activation result as the original accepted command.
- Same no-adjacent-action guardrails.

Conflict/error responses:

- `IDEMPOTENCY_CONFLICT` when the same idempotency key is reused with a
  different payload.
- `CAMPAIGN_SCOPE_MISMATCH` when the campaign does not belong to the selected
  customer account.
- `CAMPAIGN_POLICY_EVIDENCE_MISSING` when policy/settings evidence is absent.
- `CAMPAIGN_REVIEW_NOT_APPROVED` when approved review evidence is missing.
- `CAMPAIGN_READINESS_BLOCKED` when readiness evidence blocks activation.
- `CAMPAIGN_ALREADY_ACTIVE` when a different command already activated the
  campaign.
- `UNSAFE_CAMPAIGN_ACTIVATION_PAYLOAD` when the caller attempts tenant-code
  exposure, link generation, validation-track creation, credentials, webhooks,
  invite delivery, seat/auth changes, billing, funding, settlement, payout, or
  money movement.

## Frontend Implications

Selected Customer Profile > Campaigns should expose activation only after the
selected campaign has policy evidence, review approval, and readiness evidence
that allows activation.

Expected UX:

- Open from the selected customer Campaigns page or campaign review success
  state.
- Display customer name, operating jurisdiction, campaign name, review status,
  readiness summary, and activation guardrails.
- Do not ask for `tenant_code`.
- Use one primary action: request activation/go-live.
- Show blocked activation as a clear return-to-specific-step state.
- After activation succeeds, route to the selected customer Campaigns module or
  customer home with next best actions.
- Keep link/code creation, validation-track creation, technical webhooks,
  credentials, reporting, billing, and money out of the activation page.

## Explicit Non-Goals

This task does not implement:

- backend routes
- schema or migrations
- runtime campaign activation writes
- frontend screens
- link/code generation
- campaign validation or `campaign_track_id` creation
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

TASK-265 should implement the guarded backend wrapper:

`POST /v1/referral-saas/accounts/{accountRef}/campaigns/{campaignRef}/activation-requests`

That task should reuse selected-account scope resolution, campaign ownership
checks, policy/readiness/review evidence, account audit events, and idempotency
patterns. It must mutate only the campaign activation posture and keep links,
validation tracks, webhooks, credentials, access changes, billing, and money as
separate future workflows.
