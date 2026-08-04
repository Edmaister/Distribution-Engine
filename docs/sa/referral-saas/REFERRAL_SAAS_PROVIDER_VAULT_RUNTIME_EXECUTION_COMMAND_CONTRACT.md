# Referral SaaS Provider/Vault Runtime Execution Command Contract

Task: TASK-349
Status: Complete
Product boundary: Shared Platform with Referral SaaS impact

## Boundary

This contract defines the first governed command boundary for provider/vault
runtime execution after Integrations setup evidence, credential request review,
and provider/vault readiness are already visible.

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
- `docs/sa/referral-saas/REFERRAL_SAAS_PROVIDER_VAULT_RUNTIME_ADAPTER_CONTRACT.md`
- `docs/roadmap/ORDERED_TASK_LIST.md`

Source duplication: No.

## Purpose

TASK-342 to TASK-344 made provider/vault readiness understandable, but they did
not define the exact write command that will eventually turn an approved
credential request into safe provider/vault execution evidence.

This contract closes that design gap before runtime code is added. It defines
what a future execution command may accept, which gates must pass, which states
are safe to return, and which side effects remain explicitly forbidden.

## Current Source Facts

The current implementation already supports:

- selected-customer Integrations configuration evidence
- credential request create/list/read
- credential request review decisions
- execution-check evidence without provider/vault side effects
- read-only provider/vault readiness
- selected-customer Integrations UI visibility for readiness and blockers
- account scope, active account/link/reference posture, audit, idempotency,
  route smoke checks, redactions, and no-adjacent-action language

The current implementation does not yet support:

- provider/vault mutation commands
- vault writes
- provider connection creation
- credential material generation, capture, reveal, or download
- live provider dispatch
- webhook, invite, or referral-message delivery
- auth/session claim propagation
- campaign activation, billing, money movement, or DLaaS expansion

## Command Family

The first command family should remain selected-customer scoped:

| Route | Method | Purpose |
| --- | --- | --- |
| `/v1/referral-saas/accounts/{accountRef}/integrations/credential-requests/{requestRef}/provider-vault-executions` | `POST` | Record a governed provider/vault execution attempt for an approved credential request. |
| `/v1/referral-saas/accounts/{accountRef}/integrations/provider-vault/executions/{executionRef}` | `GET` | Read safe execution metadata without exposing secrets or provider payloads. |

The first runtime task may return a controlled `PROVIDER_VAULT_EXECUTION_NOT_IMPLEMENTED`
or `PROVIDER_VAULT_EXECUTION_BLOCKED` state while proving scope, gate, audit, and
idempotency behavior. It must not pretend that provider or vault references
exist unless an adapter actually created them.

## Allowed Request Shape

```json
{
  "accountScope": {
    "refType": "external_tenant_ref",
    "externalRef": "customer-reference",
    "context": "setup"
  },
  "credentialRequestRef": "credreq_safe_reference",
  "approvedRequestVersion": 3,
  "executionIntent": "RECORD_PROVIDER_VAULT_EXECUTION",
  "executionMode": "guarded",
  "providerKey": "approved-provider-key",
  "environment": "sandbox",
  "capability": "REFERRAL_SAAS_INVITE_DELIVERY",
  "reasonCode": "APPROVED_CREDENTIAL_EXECUTION",
  "reason": "Approved provider/vault execution for customer integrations.",
  "correlationId": "client-correlation-id",
  "idempotencyKey": "client-generated-key",
  "confirmations": {
    "noRawSecretSubmitted": true,
    "noSecretRevealRequested": true,
    "noSetupScreenProviderDispatch": true,
    "noInviteDeliveryRequested": true,
    "noWebhookDispatchRequested": true,
    "noReferralMessageDeliveryRequested": true,
    "noAuthClaimChangeRequested": true,
    "noCampaignActivationRequested": true,
    "noBillingOrMoneyMovementRequested": true
  }
}
```

The product API must reject any payload containing raw secret material,
provider payloads, internal tenant identifiers, UCNs, auth claims, invite
recipient payloads, billing instructions, or money instructions.

## Safe Response Shape

```json
{
  "status": "PROVIDER_VAULT_EXECUTION_BLOCKED",
  "executionRef": "pvexec_safe_reference",
  "accountRef": "ACCT_SAFE_REFERENCE",
  "credentialRequestRef": "credreq_safe_reference",
  "providerKey": "approved-provider-key",
  "environment": "sandbox",
  "capability": "REFERRAL_SAAS_INVITE_DELIVERY",
  "vaultSecretRef": null,
  "providerConnectionRef": null,
  "credentialFingerprint": null,
  "blockedReason": "PROVIDER_VAULT_BLOCKED_VAULT_NOT_CONFIGURED",
  "nextAction": {
    "label": "Configure the approved vault adapter",
    "target": "integrations"
  },
  "auditRef": "audit_safe_reference",
  "redactions": [
    "NO_RAW_SECRET_STORAGE",
    "NO_SECRET_REVEAL",
    "NO_PROVIDER_PAYLOAD_RENDERING"
  ],
  "guardrails": [
    "NO_PROVIDER_DISPATCH",
    "NO_INVITE_DELIVERY",
    "NO_WEBHOOK_DISPATCH",
    "NO_REFERRAL_MESSAGE_DELIVERY",
    "NO_AUTH_CLAIM_CHANGE",
    "NO_CAMPAIGN_ACTIVATION",
    "NO_BILLING_OR_MONEY_MOVEMENT"
  ]
}
```

`vaultSecretRef`, `providerConnectionRef`, and `credentialFingerprint` may be
non-null only when the corresponding governed adapter actually completed that
step and returned opaque safe metadata.

## Required Gates

The command may execute only when:

- selected account exists and matches the path account
- external reference resolves to the same selected account
- account foundation, tenant link, and external reference are active
- actor is authorized as Amplifi Admin or a future customer integration admin
- credential request belongs to the selected account
- credential request is approved and not blocked, cancelled, or superseded
- approved request version matches the request being executed
- saved Integrations configuration still matches request capability,
  environment, provider, and channel
- provider is approved for the selected customer, product capability, channel,
  and environment
- vault adapter is configured for the environment before any vault reference is
  returned
- no unsafe payload material is present
- idempotency and payload hash can be recorded or replayed
- account audit can record actor, request, command, state, redactions, and
  no-adjacent-action confirmations

## Execution States

| State | Meaning |
| --- | --- |
| `PROVIDER_VAULT_EXECUTION_READY` | All gates pass and the adapter can proceed, but no provider/vault reference is implied. |
| `PROVIDER_VAULT_EXECUTION_BLOCKED` | A prerequisite failed safely. |
| `PROVIDER_VAULT_EXECUTION_NOT_IMPLEMENTED` | The command boundary exists but no runtime adapter is available. |
| `VAULT_REFERENCE_RECORDED` | A vault adapter returned an opaque secret reference. |
| `PROVIDER_REFERENCE_RECORDED` | A provider adapter returned an opaque connection reference. |
| `PROVIDER_VAULT_EXECUTION_REPLAYED` | Same idempotency key and same payload returned the prior safe result. |
| `PROVIDER_VAULT_EXECUTION_REJECTED` | Payload or actor requested forbidden behavior. |

## Failure Taxonomy

| Failure state | Meaning |
| --- | --- |
| `PROVIDER_VAULT_BLOCKED_ACCOUNT_NOT_ACTIVE` | Account, tenant link, or external reference is not active. |
| `PROVIDER_VAULT_BLOCKED_REQUEST_NOT_APPROVED` | Credential request is missing, not approved, blocked, cancelled, or superseded. |
| `PROVIDER_VAULT_BLOCKED_REQUEST_VERSION_MISMATCH` | Execution targeted an older request version. |
| `PROVIDER_VAULT_BLOCKED_CONFIGURATION_MISSING` | Saved Integrations evidence is missing or no longer matches the request. |
| `PROVIDER_VAULT_BLOCKED_PROVIDER_NOT_APPROVED` | Provider is not approved for this customer/product/environment. |
| `PROVIDER_VAULT_BLOCKED_VAULT_NOT_CONFIGURED` | Vault adapter is not configured for the environment. |
| `PROVIDER_VAULT_BLOCKED_ADAPTER_NOT_CONFIGURED` | Provider adapter is not configured for the capability. |
| `PROVIDER_VAULT_REJECTED_UNSAFE_PAYLOAD` | Payload attempted raw secret, provider payload, internal identifier, auth, campaign, billing, or money behavior. |
| `PROVIDER_VAULT_EXECUTION_NOT_IMPLEMENTED` | Runtime adapter is not yet available. |
| `IDEMPOTENCY_CONFLICT` | Same idempotency key was reused with different content. |

Failures must be safe to render. They must not include raw provider responses,
stack traces, secret values, vault object paths, internal tenant codes, UCNs,
auth claims, or cross-customer details.

## Audit And Idempotency

Every command attempt must record:

- selected account reference
- external customer reference posture
- credential request reference and approved request version
- actor and role family
- reason code and safe reason
- correlation ID
- idempotency key hash and payload hash
- command state before and after
- blocked/ready/result status
- opaque provider/vault references where actually produced
- redactions applied
- no-adjacent-action confirmations

Same idempotency key and same payload must replay the same safe response. Same
idempotency key and different payload must fail as `IDEMPOTENCY_CONFLICT`.

## UI Implications

Selected-customer Integrations should present this command as a future guarded
setup action only after the customer has:

- saved Integration setup evidence
- requested credential setup
- received approval for the credential request
- cleared provider/vault readiness gates

Plain-language copy should separate these meanings:

- "Request approved" means the setup request passed review.
- "Ready for secure setup" means the command gates are clear.
- "Provider/vault execution recorded" means a governed runtime command ran.
- "Reference recorded" means an opaque vault or provider reference exists.

The UI must not show secret fields, reveal/download controls, provider payloads,
provider stack traces, internal tenant identifiers, or live delivery controls
until separate reviewed tasks implement those capabilities.

## Explicit Non-Goals

TASK-349 does not add:

- schema or migrations
- backend route implementation
- frontend controls
- provider calls
- vault writes
- credential creation, capture, reveal, rotation, download, or browser entry
- webhook dispatch
- invite delivery
- referral-message delivery
- identity-provider integration
- auth/session claim changes
- campaign activation or go-live
- repair/replay/retry execution
- export delivery execution
- billing, invoice, payout, wallet, funding, fulfilment, settlement,
  commission, treasury, or money movement
- DLaaS marketplace expansion
- source-code forks

## Definition Of Done

The next runtime task can reference this contract to implement the first
provider/vault execution command foundation with selected-customer scope,
idempotency, audit, redaction, approved-request gates, and controlled blocked
states before any provider-specific or vault-specific adapter is allowed to
produce opaque execution references.
