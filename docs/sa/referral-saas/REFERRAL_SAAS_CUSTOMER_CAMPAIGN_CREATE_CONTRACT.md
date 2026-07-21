# Referral SaaS Customer-Scoped Campaign Create Contract

TASK ID: TASK-255

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
- `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`

Current implementation files inspected:

- `dp/migrations/002_campaigns.sql`
- `services/campaign_service.py`
- `services/campaign_policy_service.py`
- `services/campaign_readiness_service.py`
- `services/referral_saas_campaign_service.py`
- `apps/api/routers/campaigns.py`
- `apps/api/routers/referral_saas_accounts.py`
- `apps/api/schemas/campaigns.py`
- `test/test_campaign_service.py`
- `test/api/test_referral_saas_accounts_api.py`

## Purpose

Define the next Referral SaaS campaign command boundary before customer-facing
campaign write routes are implemented.

TASK-253 and TASK-254 made campaign readiness, list, and read work inside the
selected customer profile. The next step is campaign creation, but the current
generic campaign create primitive inserts directly into `marketing_campaigns`
and leaves `is_active` at its database default of `TRUE`. That behavior is
acceptable for the existing admin primitive, but it is too sharp for a
productized SaaS setup flow.

This contract defines the customer-scoped create/draft command that must exist
before the UI exposes `Create campaign` as a real product action.

## Boundary Decision

Referral SaaS campaign creation must be a selected-customer setup command, not
a tenant-code form and not a campaign activation path.

Rules:

- Use `POST /v1/referral-saas/accounts/{accountRef}/campaigns` as the product
  command route.
- Resolve `tenant_code` internally from the selected account and its active
  tenant link. Operators must not type or see tenant identifiers in this flow.
- Create only a safe campaign setup artifact or an inactive campaign definition
  until readiness, policy, review, and activation command boundaries exist.
- Treat campaign activation as a separate future command.
- Keep policy write, link generation, validation-track creation, webhook
  delivery, billing, rewards, funding, fulfilment, settlement, commissions, and
  DLaaS marketplace behavior outside this command.
- Do not copy or fork campaign services into product-specific folders.

## Current Facts

Current schema facts:

- `marketing_campaigns.campaign_code` is the stable campaign definition
  identity and primary key.
- `marketing_campaigns.campaign_id` is a UUID surrogate.
- `marketing_campaigns.tenant_code` stores internal tenant/brand scope.
- `marketing_campaigns.is_active` is `BOOLEAN NOT NULL DEFAULT TRUE`.
- `marketing_campaigns.starts_at`, `ends_at`, `max_uses`, `uses_count`, and
  `attributes` model campaign availability and metadata.
- `marketing_campaign_policies` stores versioned policy rows keyed by
  `(campaign_code, tenant_code, version)`.
- `campaign_attributions.campaign_track_id` is created only after campaign
  validation, not during campaign setup.

Current service/API facts:

- `services/campaign_service.py:create_campaign` validates `segment`, `name`,
  and the date window, generates `campaign_code` when omitted, and inserts a
  campaign definition.
- The generic `POST /campaigns` route accepts admin-created campaign input and
  still accepts `tenant_code`.
- TASK-253 added selected-account readiness checks without campaign mutation.
- TASK-254 added selected-account campaign list/read wrappers without campaign
  mutation.

## Product Command Contract

Route:

`POST /v1/referral-saas/accounts/{accountRef}/campaigns`

Minimum request shape:

```json
{
  "accountScope": {
    "externalTenantRef": "customer-visible-ref",
    "organisationRef": "customer-visible-org-ref"
  },
  "campaign": {
    "name": "Summer Referral 2026",
    "segment": "Retail banking",
    "startsAt": "2026-08-01T00:00:00Z",
    "endsAt": "2026-09-30T23:59:59Z",
    "maxUses": 1000
  },
  "setupIntent": {
    "requestedStatus": "DRAFT",
    "reason": "Initial customer campaign setup"
  },
  "correlationId": "operator-session-or-request-id",
  "idempotencyKey": "stable-create-command-key"
}
```

Required command behavior:

- Validate that `accountRef`, `externalTenantRef`, and `organisationRef` match
  the selected customer account.
- Resolve internal tenant scope server-side.
- Validate campaign name, segment, date window, and max-use limits using the
  existing campaign rules.
- Record idempotency evidence before any write effect.
- Return replay for the same idempotency key and same payload hash.
- Return conflict for the same idempotency key and a different payload hash.
- Return duplicate/conflict if the selected customer already has an equivalent
  campaign setup artifact or campaign code.
- Record audit evidence with actor, selected account, resolved campaign
  identity, command status, payload hash, correlation ID, and previous/next
  setup state.
- Return redactions and guardrails in the response.

Allowed product setup statuses:

| Status | Meaning | Allowed next action |
| --- | --- | --- |
| `DRAFT` | Campaign setup has been captured but is not ready. | Edit setup, add policy intent, run readiness. |
| `NEEDS_POLICY` | Campaign definition exists but attribution/policy evidence is incomplete. | Complete policy/settings. |
| `READY_FOR_REVIEW` | Required campaign setup evidence is present for review. | Submit/review in a future command. |
| `READY_TO_ACTIVATE` | Setup passes readiness and review gates. | Activation can be considered by a later command. |
| `ACTIVE` | Campaign can support validation and attribution. | Only a future activation command may enter this state. |

TASK-255 does not implement these statuses. It defines the vocabulary and
guardrails future implementation tasks must use.

## Response Contract

Successful first capture:

```json
{
  "status": "CAMPAIGN_SETUP_DRAFT_RECORDED",
  "accountRef": "ACC-1234",
  "campaign": {
    "campaignRef": "customer-visible-campaign-ref",
    "campaignCode": "redacted-or-safe-code",
    "name": "Summer Referral 2026",
    "segment": "Retail banking",
    "setupStatus": "DRAFT",
    "isActive": false
  },
  "nextActions": [
    "Complete policy and attribution settings",
    "Run campaign readiness",
    "Review before activation"
  ],
  "guardrails": [
    "NO_TENANT_CODE_EXPOSURE",
    "NO_CAMPAIGN_ACTIVATION",
    "NO_LINK_GENERATION",
    "NO_VALIDATION_TRACK_CREATED",
    "NO_POLICY_WRITE",
    "NO_WEBHOOK_DELIVERY",
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

- `CAMPAIGN_SETUP_DRAFT_REPLAYED`
- Same visible campaign result as the original accepted command.
- Same no-adjacent-action guardrails.

Conflict response:

- `IDEMPOTENCY_CONFLICT` when the same idempotency key is reused with a
  different payload.
- `CAMPAIGN_SETUP_ALREADY_EXISTS` when the selected customer already has a
  matching campaign setup artifact.
- `ACCOUNT_SCOPE_MISMATCH` when account references do not match.
- `ACCOUNT_NOT_READY_FOR_CAMPAIGN_SETUP` when customer/account gates are not
  sufficient to start campaign setup.

## Frontend Implications

Selected Customer Profile > Campaigns should expose campaign creation as a
standalone customer-scoped page, not as stacked content on the customer home.

Expected UX:

- Open from the selected customer Campaigns page.
- Display the customer name and operating jurisdiction.
- Do not ask for `tenant_code`.
- Capture campaign basics only: name, segment/audience, dates, optional max
  uses, and setup reason.
- Save as draft or safe inactive setup only.
- After save, show the campaign profile with next best actions:
  1. Complete policy and attribution settings.
  2. Run campaign readiness.
  3. Review before activation.
- Keep activation, go-live, link generation, and validation outside the create
  screen.

## Audit And Idempotency Requirements

Future implementation must store enough evidence to prove:

- who requested the campaign setup
- which selected customer account was used
- which internal tenant scope was resolved
- what payload hash was accepted
- whether this was a new request or replay
- which campaign setup state resulted
- which guardrails prevented adjacent behavior

The idempotency key must not be stored or returned raw. Store and expose only a
hash or safe reference.

## Explicit Non-Goals

This task does not add:

- runtime route behavior
- schema migration
- campaign write implementation
- policy write implementation
- campaign activation
- go-live
- link/code generation
- campaign validation or `campaign_track_id` creation
- webhooks
- live invite delivery
- account lifecycle commands
- seat assignment
- auth/session claim changes
- reporting export mutation
- billing
- rewards
- funding
- fulfilment
- settlement
- commissions
- wallet, invoice, payout, sponsor billing, or treasury behavior
- broad DLaaS marketplace behavior
- source-code forks

## Implementation Sequence

Recommended next tasks:

1. Add an audited/idempotent customer-scoped campaign setup service that creates
   either a campaign setup draft or an inactive campaign definition.
2. Add the product route and route smoke inventory entry.
3. Add the selected-customer campaign create page.
4. Add campaign policy/settings maintenance as a separate customer-scoped page.
5. Add review/activation command boundaries only after readiness, audit,
   idempotency, and physical tests pass.

