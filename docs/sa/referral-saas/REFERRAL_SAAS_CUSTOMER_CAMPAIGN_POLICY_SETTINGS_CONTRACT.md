# Referral SaaS Customer-Scoped Campaign Policy Settings Contract

TASK ID: TASK-258

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
- `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`

Current implementation files inspected:

- `dp/migrations/002_campaigns.sql`
- `services/campaign_policy_service.py`
- `services/campaign_readiness_service.py`
- `services/referral_saas_campaign_service.py`
- `apps/api/routers/campaigns.py`
- `apps/api/routers/referral_saas_accounts.py`
- `apps/api/schemas/campaigns.py`
- `test/test_campaign_policy_service.py`
- `test/test_campaign_readiness_service.py`
- `test/test_campaigns.py`
- `test/api/test_referral_saas_accounts_api.py`

## Purpose

Define the customer-scoped Referral SaaS policy/settings boundary that follows
campaign setup draft creation.

TASK-256 created the guarded backend route for inactive campaign setup drafts.
TASK-257 added the selected-customer create UX. The next capability gap is
policy/settings: attribution window, eligibility rules, product windows, reward
visibility, and setup completeness. Those settings must be captured without
falling back to the generic tenant-code policy API and without implying that a
campaign is active or launch-ready.

This contract defines the product command and UX boundary. It does not add
runtime behavior, schema, policy writes, frontend implementation, activation,
link generation, webhook delivery, billing, rewards, funding, fulfilment,
settlement, or money movement.

## Boundary Decision

Referral SaaS policy/settings must be a selected-customer campaign setup step,
not a generic `tenant_code` policy editor and not a launch command.

Rules:

- Use selected customer account scope from
  `/v1/referral-saas/accounts/{accountRef}`.
- Use selected campaign identity from
  `/v1/referral-saas/accounts/{accountRef}/campaigns/{campaignRef}`.
- Resolve `tenant_code` internally from the selected account and active tenant
  link. Operators must not enter or see tenant identifiers in this flow.
- Persist only policy/settings evidence needed for campaign readiness.
- Keep campaign activation as a separate future command.
- Keep link/code generation, validation-track creation, webhook delivery,
  billing, reward funding, fulfilment, settlement, commissions, and broad DLaaS
  marketplace behavior outside this command.
- Reuse existing campaign policy/readiness primitives; do not fork source code.

## Current Facts

Current schema facts:

- `marketing_campaign_policies` is the existing policy table.
- The policy primary key is `(campaign_code, tenant_code, version)`.
- `tenant_code` is the internal scope key and must remain hidden from the
  product UI/API payload.
- `is_active` currently controls which policy versions can be used by
  `get_effective_policy`.
- `rolling_window_days` can represent the attribution/cooldown window.
- `rules_json` stores general policy rules.
- `product_windows_json` stores product-specific timing/window rules.
- `reward_amounts_json` stores reward amount configuration and is money-adjacent.
- `product_rules_json` stores product-specific eligibility/rule configuration.

Current service/API facts:

- `services/campaign_policy_service.py:get_effective_policy` reads the active
  tenant-specific policy first, then active global policy, then defaults.
- `PUT /campaigns/{campaign_code}/policy` is the current generic admin route.
  It accepts `tenant_code`, writes active policy rows by default, and returns
  the raw policy shape.
- `services/campaign_readiness_service.py` treats missing active policy as a
  readiness warning for create-track style operations and a blocker for publish
  or activation style operations.
- TASK-256 and TASK-257 created selected-customer campaign setup without policy
  writes.

## Product Command Contract

Route:

`PUT /v1/referral-saas/accounts/{accountRef}/campaigns/{campaignRef}/policy-settings`

Minimum request shape:

```json
{
  "accountScope": {
    "refType": "external_tenant_ref",
    "externalRef": "customer-visible-ref",
    "context": "setup"
  },
  "policySettings": {
    "version": 1,
    "attributionWindowDays": 30,
    "eligibilityRules": [
      {
        "rule": "NEW_CUSTOMER_ONLY",
        "enabled": true
      }
    ],
    "productWindows": {
      "default": {
        "days": 30
      }
    },
    "productRules": {
      "default": {
        "requiresAcceptedTerms": true
      }
    },
    "rewardVisibility": {
      "mode": "configured_without_payment",
      "notes": "Reward amounts are configured for display/readiness only."
    }
  },
  "setupIntent": {
    "requestedStatus": "NEEDS_REVIEW",
    "reason": "Complete policy and attribution settings"
  },
  "correlationId": "operator-session-or-request-id",
  "idempotencyKey": "stable-policy-settings-command-key"
}
```

Required command behavior:

- Validate that `accountRef`, `campaignRef`, and `accountScope.externalRef`
  resolve to the same selected customer context.
- Resolve `tenant_code` internally from the selected account.
- Reject caller-supplied `tenant_code`, `tenantCode`, `campaign_code`,
  `campaignCode`, `is_active`, `isActive`, `activate`, `goLive`, `webhook`,
  `credential`, `funding`, `settlement`, `payout`, or money-movement fields.
- Validate the selected campaign exists for the selected customer.
- Validate policy settings against the existing policy columns:
  `version`, `rolling_window_days`, `rules_json`, `product_windows_json`,
  `reward_amounts_json`, and `product_rules_json`.
- Record idempotency evidence before any write effect in the implementation
  task.
- Return replay for the same idempotency key and same payload hash.
- Return conflict for the same idempotency key and different payload hash.
- Record audit evidence with actor, selected account, selected campaign,
  command status, payload hash, correlation ID, and previous/next setup state.
- Keep the campaign inactive unless a later activation command runs.

Allowed product setup statuses:

| Status | Meaning | Allowed next action |
| --- | --- | --- |
| `NEEDS_POLICY` | Campaign exists but policy/settings are incomplete. | Save policy/settings. |
| `POLICY_SETTINGS_RECORDED` | Policy/settings evidence is captured. | Run campaign readiness. |
| `READY_FOR_REVIEW` | Policy/settings and setup evidence are ready for review. | Submit/review in a future command. |
| `READY_TO_ACTIVATE` | Readiness and review gates are satisfied. | Activation can be considered by a later command. |
| `ACTIVE` | Campaign can support validation and attribution. | Only a future activation command may enter this state. |

TASK-258 does not implement these statuses. It defines the vocabulary and
guardrails future implementation tasks must use.

## Response Contract

Successful first capture:

```json
{
  "status": "POLICY_SETTINGS_RECORDED",
  "accountRef": "ACC-1234",
  "campaignRef": "customer-visible-campaign-ref",
  "policySettings": {
    "version": 1,
    "setupStatus": "POLICY_SETTINGS_RECORDED",
    "attributionWindowDays": 30,
    "eligibilityRuleCount": 1,
    "productWindowCount": 1,
    "productRuleCount": 1,
    "rewardVisibilityStatus": "CONFIGURED_WITHOUT_PAYMENT"
  },
  "nextActions": [
    "Run campaign readiness",
    "Review before activation",
    "Generate links only after activation is approved"
  ],
  "guardrails": [
    "NO_TENANT_CODE_EXPOSURE",
    "NO_CAMPAIGN_ACTIVATION",
    "NO_LINK_GENERATION",
    "NO_VALIDATION_TRACK_CREATED",
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

- `POLICY_SETTINGS_REPLAYED`
- Same visible policy/settings result as the original accepted command.
- Same no-adjacent-action guardrails.

Conflict response:

- `IDEMPOTENCY_CONFLICT` when the same idempotency key is reused with a
  different payload.
- `CAMPAIGN_SCOPE_MISMATCH` when the campaign does not belong to the selected
  customer account.
- `CAMPAIGN_NOT_READY_FOR_POLICY_SETTINGS` when the campaign setup draft is not
  ready for policy/settings.
- `UNSAFE_POLICY_SETTINGS_PAYLOAD` when the caller attempts activation, links,
  credentials, webhooks, billing, money, or tenant-code exposure.

## Frontend Implications

Selected Customer Profile > Campaigns should expose policy/settings as a
standalone customer-scoped page after a campaign exists.

Expected UX:

- Open from the selected customer Campaigns page or campaign detail page.
- Display customer name, operating jurisdiction, campaign name, and setup state.
- Do not ask for `tenant_code`.
- Treat attribution window and eligibility rules as setup inputs.
- Treat reward visibility as configuration evidence only; do not imply payment,
  payout, wallet funding, settlement, sponsor billing, or fulfilment.
- Show clear next actions: run readiness, review before activation, and later
  link generation.
- Keep activation and go-live out of the page.

## Explicit Non-Goals

This task does not implement:

- backend routes
- schema or migrations
- policy writes
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

TASK-259 should implement the guarded backend wrapper:

`PUT /v1/referral-saas/accounts/{accountRef}/campaigns/{campaignRef}/policy-settings`

That task should reuse existing `marketing_campaign_policies`, resolve tenant
scope through the selected account, add idempotency/audit evidence, reject
unsafe payloads, and keep the campaign inactive.
