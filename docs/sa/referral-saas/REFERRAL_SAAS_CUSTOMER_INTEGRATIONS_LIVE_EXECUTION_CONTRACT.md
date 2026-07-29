# Referral SaaS Customer Integrations Live Execution Contract

TASK ID: TASK-304

Product boundary: Referral SaaS.

Status: Live execution command-boundary contract only. No runtime route,
service write, frontend control, schema migration, credential creation, secret
storage, webhook dispatch, invite delivery, referral-message delivery,
auth/session claim propagation, campaign activation, go-live, billing, money
movement, or DLaaS expansion is made by this task.

## Boundary

TASK-300 made selected-customer Integrations the product place for API,
webhook, invite-delivery, and referral-message readiness. TASK-301 defined the
safe configuration contract. TASK-302 added the persisted non-secret
configuration API foundation. TASK-303 wired the selected-customer UI to read,
validate, and save that safe setup evidence.

TASK-304 defines what must happen before that configuration can become any
kind of live provider execution.

The live execution layer covers four future actions:

- verify API access readiness without creating or revealing credentials
- verify webhook callback readiness without dispatching business events
- verify message-provider readiness without sending live invites or referral
  messages
- request governed credential lifecycle operations without accepting raw
  secrets from the browser

These actions must stay separate from setup evidence. Saving configuration is
not the same thing as creating credentials, registering live webhooks, sending
messages, or granting login access.

Required boundary docs checked:

- `AGENTS.md`
- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/referral-saas/ROADMAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`
- `docs/roadmap/ORDERED_TASK_LIST.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_CUSTOMER_INTEGRATIONS_CONFIGURATION_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`

## Current Source Facts

The current product already has:

- selected-customer account context and customer-profile routing
- selected-customer Integrations configuration read, validate, and save APIs
- safe non-secret integration setup evidence persistence
- account audit and idempotency patterns
- webhook catalog source material
- invite-provider approval readiness checks
- People and Access invitation-delivery and platform-login boundaries

The current product does not yet have:

- approved live provider execution adapters
- customer credential create, rotate, revoke, or reveal workflow
- webhook callback registration or signed test dispatch
- provider-backed invite or referral-message delivery
- auth/session claim propagation
- external customer-facing integration credential scopes

## Future Route Family

Future routes should stay selected-customer scoped:

| Route | Method | Purpose |
| --- | --- | --- |
| `/v1/referral-saas/accounts/{accountRef}/integrations/execution-readiness` | `GET` | Read whether saved configuration can move into live verification or provider execution. |
| `/v1/referral-saas/accounts/{accountRef}/integrations/api-access/verification` | `POST` | Record a safe API-access verification attempt without creating or revealing credentials. |
| `/v1/referral-saas/accounts/{accountRef}/integrations/webhooks/test-dispatch` | `POST` | Record a signed test-dispatch attempt only after callback, catalog, signing, and provider gates pass. |
| `/v1/referral-saas/accounts/{accountRef}/integrations/message-providers/test-delivery-check` | `POST` | Record readiness for invite/referral-message provider testing without live delivery unless an approved provider path exists. |
| `/v1/referral-saas/accounts/{accountRef}/integrations/credential-requests` | `POST` | Request governed credential create/rotate/revoke activity without accepting raw secrets from the browser. |

TASK-305 exposes execution readiness. TASK-307 implements the first governed
execution command: `POST
/v1/referral-saas/accounts/{accountRef}/integrations/api-access/verification`.
That command records API-access verification evidence only after saved
configuration and active account/link/reference gates pass. It is audited and
idempotent, rejects unsafe secret-like payloads, and does not create,
reveal, rotate, or accept credentials; call providers; dispatch webhooks; send
invites or messages; activate memberships; assign seats; change auth claims;
activate campaigns; trigger go-live; bill; or move money.

TASK-309 implements the second governed execution command: `POST
/v1/referral-saas/accounts/{accountRef}/integrations/webhooks/test-dispatch`.
That command records webhook test-dispatch evidence only after saved webhook
setup and active account/link/reference gates pass. It is audited and
idempotent, rejects unsafe secret-like payloads, and does not dispatch a
webhook, activate a subscription, create/reveal signing material, call a
provider, send invites or messages, activate memberships, assign seats, change
auth claims, activate campaigns, trigger go-live, bill, or move money.

Message-provider checks and credential lifecycle commands should not be added
until their readiness gates and failure states are implemented with the same
selected-customer, audit, idempotency, and redaction boundaries.

## Required Gates

Any future live execution action must prove:

- selected account exists and is the customer currently in context
- account foundation, tenant link, and external reference are active
- actor is authorized as Amplifi Admin or future customer integration admin
- saved Integrations configuration exists and validates cleanly
- event categories are in the safe Referral SaaS webhook catalog
- callback URL, message channel, provider reference, and environment are
  approved for this customer
- credential actions use governed provider references, never raw secrets
- idempotency key and payload hash are recorded for replay/conflict behavior
- account audit evidence records actor, reason, correlation ID, provider
  posture, redactions, and no-adjacent-action confirmations
- responses redact tokens, signing material, raw provider payloads, raw webhook
  payloads, raw recipients, tenant internals, UCNs, SQL errors, and stack
  traces

## Candidate Response Statuses

| Status | Meaning |
| --- | --- |
| `INTEGRATION_EXECUTION_READY` | Saved setup evidence and provider gates allow the next bounded execution action. |
| `INTEGRATION_EXECUTION_BLOCKED_CONFIGURATION_MISSING` | Required setup evidence has not been saved. |
| `INTEGRATION_EXECUTION_BLOCKED_ACCOUNT_NOT_ACTIVE` | Account, tenant link, or external reference is not active. |
| `INTEGRATION_EXECUTION_BLOCKED_PROVIDER_NOT_APPROVED` | Provider/channel/callback is not approved for this customer. |
| `INTEGRATION_EXECUTION_BLOCKED_UNSAFE_PAYLOAD` | Payload attempted secrets, raw tenant identifiers, raw provider payloads, live delivery, auth changes, billing, or money behavior. |
| `API_ACCESS_VERIFICATION_RECORDED` | API access verification evidence was recorded without credential creation. |
| `WEBHOOK_TEST_DISPATCH_RECORDED` | A safe test-dispatch attempt was recorded after all gates passed. |
| `WEBHOOK_TEST_DISPATCH_BLOCKED` | Test dispatch was blocked with a safe recovery reason. |
| `MESSAGE_PROVIDER_TEST_RECORDED` | Provider test readiness evidence was recorded without live invite or referral-message delivery. |
| `CREDENTIAL_REQUEST_RECORDED` | A governed credential lifecycle request was recorded without raw secret handling. |
| `IDEMPOTENCY_REPLAYED` | Same key and payload returned the same result. |
| `IDEMPOTENCY_CONFLICT` | Same key was reused with different execution content. |

## UX Contract

The selected-customer Integrations page should eventually separate setup from
live execution in plain language:

1. Setup evidence: what the customer wants to connect.
2. Readiness check: what is missing before live testing.
3. Live verification: safe API, webhook, and provider checks.
4. Credential requests: governed actions for credentials and rotation.

Each action should show:

- what will happen
- what will not happen
- who can run it
- what prerequisite is missing
- where to fix the blocker
- whether the result was recorded, replayed, blocked, or rejected

Operators should never have to interpret terms such as raw payload, tenant
code, queue replay, provider adapter, or credential material to know what to do
next.

## Explicit Non-Goals

TASK-304 does not add:

- schema or migrations
- backend routes or service writes
- frontend controls
- API key creation
- secret creation, storage, rotation, reveal, or browser submission
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

A runtime live Integrations implementation may start only after it references
this contract and proves selected-customer scope, permission gates, safe
payload validation, idempotency, audit, redaction, provider/catalog validation,
clear recovery states, and no adjacent credential, webhook dispatch, invite
delivery, auth, campaign, billing, or money side effects.
