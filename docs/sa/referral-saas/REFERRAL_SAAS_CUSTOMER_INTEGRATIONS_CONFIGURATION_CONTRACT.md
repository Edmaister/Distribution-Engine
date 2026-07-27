# Referral SaaS Customer Integrations Configuration Contract

TASK ID: TASK-301

Product boundary: Referral SaaS.

Status: Configuration command-boundary contract only. No runtime route, service
write, frontend control, schema migration, credential creation, secret storage,
webhook dispatch, invite delivery, auth/session claim propagation, campaign
activation, go-live, billing, money movement, or DLaaS expansion is made by
this task.

## Boundary

TASK-300 made the selected-customer `Integrations` workspace the product place
for API, webhook, invite-delivery, and referral-message readiness. TASK-301
defines the future configuration boundary behind that workspace.

The Integrations workspace should manage customer-scoped setup evidence for:

- API environment intent
- webhook callback intent
- webhook event category subscription intent
- invite-delivery provider approval intent
- referral-message channel provider readiness intent
- safe test-mode posture

It must not silently create credentials, register live webhooks, send test
messages, deliver invites, activate campaigns, rotate secrets, change login
permissions, bill, or move money.

Required boundary docs checked:

- `AGENTS.md`
- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/referral-saas/ROADMAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`
- `docs/roadmap/ORDERED_TASK_LIST.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`

## Current Source Facts

The current product already has:

- selected-customer account context and account-scoped route wrappers
- a read-only technical setup readiness API used by the Integrations page
- provider approval readiness checks for invite delivery
- recipient/contact readiness checks for People and Access
- guarded invite-delivery check UI that does not send email
- webhook event catalog source material for discovery use cases
- account audit and idempotency patterns used by customer-scoped commands

The current product does not yet have:

- customer-scoped persisted integration configuration
- API key or credential lifecycle
- raw secret storage or rotation
- customer-owned webhook callback registration
- provider-backed invite or message delivery
- live webhook test dispatch
- auth/session claim propagation

## Candidate Product Routes

Future routes should stay selected-customer scoped:

| Route | Method | Purpose |
| --- | --- | --- |
| `/v1/referral-saas/accounts/{accountRef}/integrations/configuration` | `GET` | Read safe integration configuration and readiness for the selected customer. |
| `/v1/referral-saas/accounts/{accountRef}/integrations/configuration` | `PUT` | Save bounded integration setup intent and non-secret configuration evidence. |
| `/v1/referral-saas/accounts/{accountRef}/integrations/configuration/validate` | `POST` | Validate configuration evidence without persisting or dispatching anything. |
| `/v1/referral-saas/accounts/{accountRef}/integrations/webhook-catalog` | `GET` | Read safe webhook event categories and payload preview metadata. |

Credential lifecycle should be a later governed route family, not a hidden side
effect of this configuration command.

## Candidate Request Shape

```json
{
  "accountScope": {
    "refType": "external_tenant_ref",
    "externalRef": "customer-reference",
    "context": "setup"
  },
  "apiEnvironment": {
    "environment": "sandbox",
    "integrationOwnerRef": "safe-contact-ref",
    "intendedAuthMethod": "api_key",
    "allowedUse": ["campaign_read", "referral_code_issue", "progress_event_ingest"]
  },
  "webhookIntent": {
    "callbackUrl": "https://customer.example/webhooks/referral-saas",
    "eventCategories": ["campaign", "referral", "progress", "attribution"],
    "payloadVersion": "v1",
    "signingMode": "planned"
  },
  "messageProviders": {
    "inviteDelivery": {
      "channel": "email",
      "providerApprovalRef": "safe-provider-approval-ref",
      "deliveryMode": "disabled_until_approved"
    },
    "referralMessages": {
      "channels": ["email", "sms"],
      "providerApprovalRefs": ["safe-provider-approval-ref"]
    }
  },
  "reasonCode": "CUSTOMER_INTEGRATION_SETUP",
  "correlationId": "client-correlation-id",
  "idempotencyKey": "client-generated-key"
}
```

The first runtime implementation may support a smaller subset, but it must
return explicit `unsupportedField` feedback rather than ignoring unknown live
behavior.

## Required Gates

Configuration save may proceed only when:

- actor is authorized as Amplifi Admin or future customer integration admin
- selected account exists and belongs to the resolved customer context
- account foundation is active enough for integration setup, or the response
  clearly states that only draft intent was saved
- external reference is active
- no raw `tenant_code` is accepted from the browser
- no raw secret, token, signing key, private key, credential, auth claim,
  provider payload, UCN, or DLQ payload is accepted
- callback URL is HTTPS except for explicitly labelled local development
  evidence
- event categories are in the approved Referral SaaS webhook catalog
- message channels are in the approved provider-readiness catalog
- idempotency key and payload hash are recorded for replay/conflict behavior
- account audit evidence records actor, reason, correlation ID, safe setup
  summary, redactions, and no-adjacent-action confirmations

## Candidate Response Statuses

| Status | Meaning |
| --- | --- |
| `INTEGRATION_CONFIGURATION_SAVED` | Safe setup evidence was persisted for the selected customer. |
| `INTEGRATION_CONFIGURATION_VALIDATED` | Setup evidence passed validation but was not saved. |
| `INTEGRATION_CONFIGURATION_REPLAYED` | Same idempotency key and payload returned the same result. |
| `INTEGRATION_CONFIGURATION_DRAFT_ONLY` | Account state allows setup intent only, not provider approval or live behavior. |
| `INTEGRATION_CONFIGURATION_BLOCKED_ACCOUNT_NOT_ACTIVE` | Account/link posture is not active enough for configuration save. |
| `INTEGRATION_CONFIGURATION_BLOCKED_PROVIDER_NOT_APPROVED` | Selected provider/channel is not approved for this customer. |
| `INTEGRATION_CONFIGURATION_BLOCKED_UNSAFE_PAYLOAD` | Payload attempted secrets, credentials, raw tenant identifiers, provider payloads, live dispatch, billing, or money movement. |
| `IDEMPOTENCY_CONFLICT` | Same key was reused with different configuration content. |

## UX Contract

The selected-customer Integrations page should eventually show three simple
areas:

1. API access: what the customer wants to connect to.
2. Webhooks: where product events should be sent once approved.
3. Message providers: which channels are approved for invites and referral
   messages.

Each area should show:

- setup state in plain language
- one next action
- what the action will save
- what the action will not do
- current blocker and recovery path

The page should avoid exposing implementation names such as internal tenant
codes, raw provider payloads, signing secrets, or queue internals.

## Explicit Non-Goals

TASK-301 does not add:

- schema or migrations
- backend routes or service writes
- frontend controls
- API key creation
- secret creation, storage, rotation, or reveal
- webhook subscription activation
- webhook dispatch or delivery retry
- invite or referral-message delivery
- identity-provider integration
- auth/session claim changes
- campaign activation or go-live
- support-case writes
- export persistence
- billing, invoicing, payout, wallet, funding, fulfilment, settlement,
  commission, treasury, or money movement
- DLaaS marketplace expansion
- source-code forks

## Definition Of Done

A runtime Integrations implementation may start only after it references this
contract and proves selected-customer scope, permission gates, safe payload
validation, idempotency, audit, redaction, provider/catalog validation, and
no adjacent credential, webhook dispatch, invite delivery, auth, campaign,
billing, or money side effects.
