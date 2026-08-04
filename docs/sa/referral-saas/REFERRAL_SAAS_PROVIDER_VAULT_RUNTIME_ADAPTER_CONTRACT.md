# Referral SaaS Provider/Vault Runtime Adapter Contract

Task: TASK-342
Status: Complete
Product boundary: Shared Platform with Referral SaaS impact

## Boundary

This contract defines the shared provider/vault runtime adapter boundary that
Referral SaaS Integrations will consume first, while keeping the primitive
portable for later DLaaS surfaces.

Required boundary docs checked:

- `AGENTS.md`
- `docs/product/README.md`
- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/README.md`
- `docs/roadmap/referral-saas/ROADMAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_CUSTOMER_INTEGRATIONS_CONFIGURATION_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_CUSTOMER_INTEGRATIONS_LIVE_EXECUTION_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_CUSTOMER_INTEGRATIONS_CREDENTIAL_LIFECYCLE_CONTRACT.md`
- `docs/roadmap/ORDERED_TASK_LIST.md`

Source duplication: No.

## Purpose

Referral SaaS Integrations can now save non-secret setup evidence, record safe
verification checks, request credentials, approve or block credential requests,
and record execution-check evidence. The remaining gap is the governed runtime
adapter that turns an approved credential request into opaque execution
references without exposing secrets or letting setup screens call providers.

This contract answers:

1. When is a credential request eligible for provider/vault execution?
2. What references may the runtime adapter return?
3. Which facts are safe for the Referral SaaS UI and APIs to render?
4. What must be audited and idempotent?
5. Which adjacent actions remain explicitly outside this boundary?

## Current Source Facts

The current implementation already includes:

- selected-customer account scope and account maintenance pages
- persisted Integrations configuration evidence
- Integrations execution-readiness read models
- governed API-access verification, webhook test-dispatch evidence, and
  message-provider test-check evidence commands
- persisted credential request create/list/read routes
- credential request review-decision routes
- credential execution-check evidence routes
- account audit and idempotency patterns
- redaction checks for internal identifiers, provider payloads, and secrets

The current implementation does not yet include:

- a vault write adapter
- API key or signing secret generation
- customer secret reveal or download
- live provider dispatch from approved credential requests
- provider-specific adapter implementations
- auth/session claim propagation
- automatic campaign activation, report delivery, invite delivery, billing, or
  money movement

## Adapter Ownership

The runtime adapter is a shared platform primitive. Referral SaaS owns the
selected-customer product workflow and safe UI language. The adapter owns the
execution boundary.

| Layer | Owns | Must not own |
| --- | --- | --- |
| Referral SaaS Integrations | Setup plan, saved non-secret evidence, credential request/review, readiness display, selected-customer navigation. | Raw secret entry, vault storage, provider execution internals, live provider dispatch. |
| Provider/vault adapter | Approved request execution, vault/provider reference creation, execution-state evidence, adapter audit. | Product setup workflow decisions, campaign activation, auth claims, billing, money movement. |
| Vault provider | Secret material and secure storage under platform policy. | Browser-rendered secret values or product UI state. |
| Provider adapter | Provider-specific reference validation and optional future runtime calls. | Unapproved setup-screen calls or raw provider payload rendering. |

## Lifecycle

| Stage | Meaning | Safe product visibility |
| --- | --- | --- |
| `REQUEST_RECORDED` | Credential capability was requested for a selected customer. | Request type, capability, environment, requester, status. |
| `REQUEST_APPROVED` | Human/governed review approved later execution. | Approval status, safe reason, approver reference. |
| `EXECUTION_READY` | Required account, request, provider, vault, and policy gates are satisfied. | Plain readiness result and next action. |
| `VAULT_REFERENCE_RECORDED` | Vault has stored or accepted secret material and returned an opaque reference. | Opaque `vaultSecretRef`, fingerprint, created timestamp, redactions. |
| `PROVIDER_REFERENCE_RECORDED` | Provider adapter has accepted safe setup/reference evidence. | Opaque `providerConnectionRef`, provider key, environment, status. |
| `EXECUTION_BLOCKED` | A required gate failed without unsafe side effects. | Safe blocked reason and recovery path. |
| `EXECUTION_REPLAYED` | Same idempotency key and payload returned the prior result. | Prior safe response and audit reference. |

The first runtime implementation may stop at `EXECUTION_READY` or a blocked
state. It must not fake provider/vault success.

## Candidate Route Family

The first Referral SaaS consumer should stay selected-customer scoped:

| Route | Method | Purpose |
| --- | --- | --- |
| `/v1/referral-saas/accounts/{accountRef}/integrations/provider-vault/readiness` | `GET` | Read whether approved credential requests are ready for provider/vault execution. |
| `/v1/referral-saas/accounts/{accountRef}/integrations/credential-requests/{requestRef}/provider-vault-executions` | `POST` | Execute an approved credential request through the governed adapter when implementation exists. |
| `/v1/referral-saas/accounts/{accountRef}/integrations/provider-vault/executions/{executionRef}` | `GET` | Read safe execution metadata and references without revealing secrets. |

TASK-343 should implement the read-only readiness route first. The mutation
route must remain unavailable until a separate provider/vault runtime task
implements it with full audit and adapter tests.

## TASK-343 Readiness API Implementation

TASK-343 implements the first route in this family:

`GET /v1/referral-saas/accounts/{account_ref}/integrations/provider-vault/readiness`

The response returns `providerVaultReadiness` for the selected customer. It
checks active account posture, saved Integrations configuration, provider
approval, approved credential requests, and request/configuration version
alignment. It can return ready, missing, unapproved, provider-blocked,
configuration-blocked, stale-version, or inactive-account states.

This route is a classifier only. It does not create credentials, store or
reveal secrets, write vault references, call providers, dispatch webhooks or
messages, send invites, activate memberships, assign seats, change auth claims,
activate campaigns, bill, move money, add DLaaS scope, or fork source code.

`PROVIDER_VAULT_EXECUTION_READY` means the visible customer setup evidence is
aligned for a future governed executor. It does not mean a provider connection
or vault secret exists yet.

## Candidate Execution Request

```json
{
  "accountScope": {
    "refType": "external_tenant_ref",
    "externalRef": "customer-reference",
    "context": "setup"
  },
  "credentialRequestRef": "credreq_safe_reference",
  "approvedRequestVersion": 3,
  "executionIntent": "CREATE_PROVIDER_AND_VAULT_REFERENCES",
  "environment": "sandbox",
  "providerKey": "approved-provider-key",
  "capability": "REFERRAL_SAAS_INVITE_DELIVERY",
  "reasonCode": "APPROVED_CREDENTIAL_EXECUTION",
  "reason": "Approved setup for customer invite delivery provider.",
  "correlationId": "client-correlation-id",
  "idempotencyKey": "client-generated-key",
  "confirmations": {
    "noRawSecretSubmitted": true,
    "noSecretRevealRequested": true,
    "noSetupScreenProviderDispatch": true,
    "noInviteDeliveryRequested": true,
    "noWebhookDispatchRequested": true,
    "noAuthClaimChangeRequested": true,
    "noCampaignActivationRequested": true,
    "noBillingOrMoneyMovementRequested": true
  }
}
```

If future secure secret entry is needed, that capture must happen in a
vault-owned or vault-mediated flow. Referral SaaS product screens must never
accept raw token, API key, signing secret, private key, password, or provider
secret values.

## Candidate Response

```json
{
  "status": "EXECUTION_READY",
  "executionRef": "pvexec_safe_reference",
  "accountRef": "ACCT_SAFE_REFERENCE",
  "credentialRequestRef": "credreq_safe_reference",
  "providerKey": "approved-provider-key",
  "environment": "sandbox",
  "capability": "REFERRAL_SAAS_INVITE_DELIVERY",
  "vaultSecretRef": null,
  "providerConnectionRef": null,
  "credentialFingerprint": null,
  "nextAction": {
    "label": "Run governed provider/vault execution",
    "target": "integrations"
  },
  "redactions": [
    "NO_RAW_SECRET_STORAGE",
    "NO_SECRET_REVEAL",
    "NO_PROVIDER_PAYLOAD_RENDERING"
  ],
  "guardrails": [
    "NO_SETUP_SCREEN_PROVIDER_DISPATCH",
    "NO_INVITE_DELIVERY",
    "NO_WEBHOOK_DISPATCH",
    "NO_AUTH_CLAIM_CHANGE",
    "NO_CAMPAIGN_ACTIVATION",
    "NO_BILLING_OR_MONEY_MOVEMENT"
  ]
}
```

Opaque references may be returned only when the corresponding adapter has
actually completed that step. A response must not invent a vault or provider
reference.

## Required Gates

Provider/vault execution readiness may be `READY` only when:

- selected account exists and matches the requested customer context
- account foundation, tenant link, and external reference are active
- actor is authorized as Amplifi Admin or future customer integration admin
- credential request exists under the selected account
- credential request is approved and not blocked/cancelled/superseded
- approved request version matches the request being executed
- saved Integrations configuration still matches the requested capability
- provider key is approved for the product capability, channel, environment,
  and selected customer
- vault adapter is configured for the environment
- no raw secret, token, signing key, private key, credential value, provider
  payload, internal tenant code, UCN, auth claim, invite recipient payload,
  billing instruction, or money instruction appears in the product payload
- idempotency key and payload hash can be recorded and replayed safely
- account audit can record actor, request, approval, execution intent,
  redactions, blocked/ready state, and no-adjacent-action confirmations

## Failure Taxonomy

| Failure state | Meaning |
| --- | --- |
| `PROVIDER_VAULT_BLOCKED_ACCOUNT_NOT_ACTIVE` | Account, tenant link, or external reference is not active. |
| `PROVIDER_VAULT_BLOCKED_REQUEST_NOT_APPROVED` | Credential request is missing, not approved, blocked, cancelled, or superseded. |
| `PROVIDER_VAULT_BLOCKED_REQUEST_VERSION_MISMATCH` | Execution targeted an older request version. |
| `PROVIDER_VAULT_BLOCKED_CONFIGURATION_MISSING` | Saved Integrations evidence is absent or no longer matches the request. |
| `PROVIDER_VAULT_BLOCKED_PROVIDER_NOT_APPROVED` | Provider is not approved for this customer/product/environment. |
| `PROVIDER_VAULT_BLOCKED_VAULT_NOT_CONFIGURED` | Vault adapter is not configured for the environment. |
| `PROVIDER_VAULT_BLOCKED_ADAPTER_NOT_CONFIGURED` | Provider adapter is not configured for this provider/environment/capability. |
| `PROVIDER_VAULT_REJECTED_UNSAFE_PAYLOAD` | Payload attempted raw secret, provider payload, internal identifier, auth, campaign, billing, or money behavior. |
| `PROVIDER_VAULT_PROVIDER_EXECUTION_BLOCKED` | Provider adapter could not safely record or validate the provider reference. |
| `PROVIDER_VAULT_VAULT_WRITE_BLOCKED` | Vault adapter could not safely record the secret reference. |
| `IDEMPOTENCY_CONFLICT` | Same idempotency key was reused with different content. |

All failures must be safe to render. They must not include raw provider
responses, stack traces, secret names that reveal values, tenant codes, or
cross-customer details.

## Audit And Idempotency

Every readiness or future execution action must record or return:

- selected account reference
- external customer reference posture
- credential request reference and approved request version
- actor and role family
- reason code and safe reason
- correlation ID
- idempotency key hash and payload hash
- execution state before and after
- opaque provider/vault references where actually produced
- redactions applied
- no-adjacent-action confirmations

Replay with the same idempotency key and same payload must return the same safe
result. Reuse with different content must fail as `IDEMPOTENCY_CONFLICT`.

## UI Contract

Selected-customer Integrations should explain the provider/vault gap in plain
language:

- "Credentials requested" means the customer asked for a governed setup.
- "Approved" means a human/operator approved the request for secure execution.
- "Ready for secure setup" means provider/vault gates are satisfied.
- "Reference recorded" means the runtime adapter returned an opaque reference.
- "Blocked" means a specific prerequisite must be fixed before execution.

The UI must not show:

- raw API keys
- raw signing secrets
- raw provider payloads
- vault object paths
- internal tenant codes
- provider stack traces
- download/reveal controls unless a later reviewed task explicitly adds a
  secure reveal/download workflow

## Explicit Non-Goals

TASK-342 does not add:

- schema or migrations
- backend routes or service writes
- frontend controls
- provider calls
- vault integration or vault writes
- credential creation, storage, rotation, reveal, browser submission, or
  download
- webhook dispatch, live invite delivery, or referral-message delivery
- identity-provider integration
- auth/session claim changes
- campaign activation or go-live
- repair/replay/retry execution
- export delivery execution
- billing, invoicing, payout, wallet, funding, fulfilment, settlement,
  commission, treasury, or money movement
- DLaaS marketplace expansion
- source-code forks

## Definition Of Done

TASK-343 may start when it references this contract and implements read-only
provider/vault execution readiness over selected-customer Integrations without
exposing secrets, calling providers, writing vault entries, dispatching
messages/webhooks, changing auth, activating campaigns, billing, moving money,
or expanding into DLaaS implementation scope.
