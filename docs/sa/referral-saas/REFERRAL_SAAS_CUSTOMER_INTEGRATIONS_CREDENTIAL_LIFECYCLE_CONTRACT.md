# Referral SaaS Customer Integrations Credential Lifecycle Contract

TASK ID: TASK-314

Product boundary: Referral SaaS.

Status: Credential lifecycle request contract only. No runtime route, service
write, frontend control, schema migration, API key creation, secret storage,
secret rotation, secret reveal, provider call, webhook dispatch, invite
delivery, referral-message delivery, auth/session claim propagation, campaign
activation, go-live, billing, money movement, or DLaaS expansion is made by
this task.

## Boundary

Selected-customer Integrations now lets an operator plan API, webhook, and
message-provider setup, save non-secret configuration evidence, and record safe
verification evidence. Credential lifecycle is the next boundary because the
product will eventually need customer-owned API credentials, webhook signing
material, and provider references.

Credential lifecycle must not be hidden inside configuration save, validation,
or test-check commands. It is a governed request workflow with its own approval,
audit, redaction, and recovery states.

Required boundary docs checked:

- `AGENTS.md`
- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/referral-saas/ROADMAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`
- `docs/roadmap/ORDERED_TASK_LIST.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_CUSTOMER_INTEGRATIONS_CONFIGURATION_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_CUSTOMER_INTEGRATIONS_LIVE_EXECUTION_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`

## Current Source Facts

The current product already has:

- selected-customer account context and account-scoped route wrappers
- persisted non-secret Integrations configuration evidence
- execution-readiness checks for API access, webhooks, and message providers
- governed API-access verification, webhook test-dispatch, and
  message-provider test-check evidence commands
- account audit and idempotency patterns
- unsafe-payload rejection and redaction expectations

The current product does not yet have:

- credential request persistence
- credential approval lifecycle
- API key generation or customer credential issuance
- webhook signing material creation or rotation
- provider-backed secret storage or vault integration
- secret reveal/download
- customer-facing credential scopes
- auth/session claim propagation

## Product Intent

The credential lifecycle request flow should answer five operator questions in
plain language:

1. Which selected customer needs credentials?
2. What credential capability is being requested?
3. Who approved the request and why?
4. What happened to the request?
5. What is the next safe action?

It should not ask the operator to paste secrets into the browser. The browser
may request a governed credential action, but the platform must own secret
creation, storage, rotation, redaction, and audit.

## Route Family

The route family should stay selected-customer scoped:

| Route | Method | Purpose |
| --- | --- | --- |
| `/v1/referral-saas/accounts/{accountRef}/integrations/credential-requests` | `POST` | Request a governed credential lifecycle action for the selected customer. |
| `/v1/referral-saas/accounts/{accountRef}/integrations/credential-requests` | `GET` | List safe credential request summaries for the selected customer. |
| `/v1/referral-saas/accounts/{accountRef}/integrations/credential-requests/{requestRef}` | `GET` | Read one safe credential request summary and audit posture. |
| `/v1/referral-saas/accounts/{accountRef}/integrations/credential-requests/{requestRef}/review-decisions` | `POST` | Approve or block a credential request before provider/vault execution. |
| `/v1/referral-saas/accounts/{accountRef}/integrations/credential-requests/{requestRef}/execution-checks` | `POST` | Record safe execution readiness after approval without revealing secrets. |

The first implementation may start with the create/read request boundary only.
Actual credential issuance, vault writes, secret reveal/download, rotation,
revocation, and provider execution must remain separate reviewed tasks.

## Candidate Request Shape

```json
{
  "accountScope": {
    "refType": "external_tenant_ref",
    "externalRef": "customer-reference",
    "context": "setup"
  },
  "requestType": "API_KEY_CREATE",
  "capability": "REFERRAL_SAAS_API_ACCESS",
  "environment": "sandbox",
  "intendedUse": [
    "campaign_read",
    "referral_code_issue",
    "progress_event_ingest"
  ],
  "requestedFor": {
    "integrationOwnerRef": "safe-contact-ref",
    "displayName": "Customer integration owner"
  },
  "reasonCode": "CUSTOMER_INTEGRATION_CREDENTIAL_REQUEST",
  "reason": "Customer needs sandbox API access for referral testing.",
  "correlationId": "client-correlation-id",
  "idempotencyKey": "client-generated-key",
  "confirmations": {
    "noRawSecretSubmitted": true,
    "noSecretRevealRequested": true,
    "noProviderExecutionRequested": true,
    "noWebhookDispatchRequested": true,
    "noInviteDeliveryRequested": true,
    "noAuthClaimChangeRequested": true,
    "noCampaignActivationRequested": true,
    "noMoneyMovementRequested": true
  }
}
```

## Supported Request Types

| Request type | Meaning |
| --- | --- |
| `API_KEY_CREATE` | Request a new customer-scoped API credential. |
| `API_KEY_ROTATE` | Request rotation of an existing customer-scoped API credential. |
| `API_KEY_REVOKE` | Request revocation of an existing customer-scoped API credential. |
| `WEBHOOK_SIGNING_KEY_CREATE` | Request signing material for customer webhook verification. |
| `WEBHOOK_SIGNING_KEY_ROTATE` | Request rotation of webhook signing material. |
| `PROVIDER_CREDENTIAL_REFERENCE_CREATE` | Request a provider credential reference without browser-held secrets. |

Unsupported request types must be rejected explicitly. They must not be stored
as generic text that later becomes ambiguous.

## Required Gates

Credential request creation may proceed only when:

- selected account exists and matches the current customer context
- account foundation, tenant link, and external reference are active
- actor is authorized as Amplifi Admin or future customer integration admin
- saved Integrations configuration exists for the relevant capability
- environment is `sandbox`, `staging`, or `production` and is allowed for this
  account
- requested capability maps to the Referral SaaS product boundary
- request contains reason, correlation ID, idempotency key, and confirmations
- payload contains no raw secret, token, signing key, private key, credential
  material, raw provider payload, internal tenant code, UCN, SQL error, stack
  trace, invite recipient payload, billing instruction, or money instruction
- account audit records actor, account, request type, capability, environment,
  approval posture, payload hash, redactions, and no-adjacent-action
  confirmations

## Candidate Statuses

| Status | Meaning |
| --- | --- |
| `CREDENTIAL_REQUEST_RECORDED` | Safe request was recorded; no credential was created. |
| `CREDENTIAL_REQUEST_REPLAYED` | Same idempotency key and payload returned the existing request. |
| `CREDENTIAL_REQUEST_BLOCKED_ACCOUNT_NOT_ACTIVE` | Account/link/reference posture is not active. |
| `CREDENTIAL_REQUEST_BLOCKED_CONFIGURATION_MISSING` | Saved Integrations setup evidence is missing. |
| `CREDENTIAL_REQUEST_BLOCKED_UNSUPPORTED_TYPE` | Requested credential action is outside the approved vocabulary. |
| `CREDENTIAL_REQUEST_REJECTED_UNSAFE_PAYLOAD` | Payload attempted raw secrets, provider payloads, auth, campaign, billing, or money behavior. |
| `CREDENTIAL_REQUEST_READY_FOR_REVIEW` | Request is safe and waiting for a human/governed review decision. |
| `CREDENTIAL_REQUEST_APPROVED` | Review approved later provider/vault execution. No secret was revealed. |
| `CREDENTIAL_REQUEST_BLOCKED_BY_REVIEW` | Review blocked the request with a safe reason. |
| `CREDENTIAL_EXECUTION_NOT_IMPLEMENTED` | Request is approved but provider/vault execution is not implemented yet. |
| `IDEMPOTENCY_CONFLICT` | Same idempotency key was reused with different request content. |

## Response Shape

Responses must be safe to render in the selected-customer UI:

```json
{
  "status": "CREDENTIAL_REQUEST_RECORDED",
  "requestRef": "credreq_safe_reference",
  "accountRef": "ACCT_SAFE_REFERENCE",
  "requestType": "API_KEY_CREATE",
  "capability": "REFERRAL_SAAS_API_ACCESS",
  "environment": "sandbox",
  "reviewStatus": "READY_FOR_REVIEW",
  "nextAction": {
    "label": "Review credential request",
    "target": "integrations"
  },
  "redactions": [
    "NO_RAW_SECRET_STORAGE",
    "NO_SECRET_REVEAL",
    "NO_PROVIDER_PAYLOAD_RENDERING"
  ],
  "guardrails": [
    "NO_PROVIDER_EXECUTION",
    "NO_WEBHOOK_DISPATCH",
    "NO_INVITE_DELIVERY",
    "NO_AUTH_CLAIM_CHANGE",
    "NO_CAMPAIGN_ACTIVATION",
    "NO_MONEY_MOVEMENT"
  ]
}
```

## UX Contract

Integrations should treat credential lifecycle as a separate stage:

1. Plan connection.
2. Save non-secret setup.
3. Verify safe readiness.
4. Request credentials.
5. Review and execute through a governed provider/vault workflow later.

Plain-language copy should say:

- what credential capability is being requested
- why it is needed
- who requested it
- whether it is waiting for review, approved, blocked, or not implemented
- that no secret was pasted, revealed, emailed, downloaded, or stored in the
  browser
- that provider/vault execution is a later governed workflow

## Explicit Non-Goals

TASK-314 does not add:

- schema or migrations
- backend routes or service writes
- frontend controls
- API key creation
- secret creation, storage, rotation, reveal, browser submission, or download
- vault integration
- provider API calls
- webhook subscription activation
- webhook dispatch, retry, replay, queueing, or signing
- invite or referral-message delivery
- identity-provider integration
- auth/session claim changes
- campaign activation or go-live
- support-case writes
- export persistence or downloads
- billing, invoicing, payout, wallet, funding, fulfilment, settlement,
  commission, treasury, or money movement
- DLaaS marketplace expansion
- source-code forks

## Definition Of Done

A runtime credential lifecycle implementation may start only after it references
this contract and proves selected-customer scope, permission gates, supported
request vocabulary, unsafe-payload rejection, idempotency, audit, redaction,
clear review states, and no adjacent provider, webhook, invite/message, auth,
campaign, billing, money, or DLaaS side effects.
