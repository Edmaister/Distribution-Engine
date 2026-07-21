# Referral SaaS Membership Activation And Delivery Boundary

TASK ID: TASK-214

Product boundary: Referral SaaS.

Status: Command-boundary contract only. No runtime route, service write,
frontend control, invitation provider integration, identity-provider
integration, auth/session claim change, seat assignment, migration, live DB
mutation, campaign activation, go-live, money movement, or DLaaS expansion is
made by this task.

## Boundary

TASK-211 records bounded membership invitation intent and TASK-213 physically
proved that intent through the local API and database. The remaining account
setup risk is confusing invited setup evidence with real access.

This contract separates three different capabilities:

1. Invitation intent: already implemented; records invited membership evidence.
2. Invitation delivery: future command that asks an approved delivery provider
   to send an invite message.
3. Membership activation: future command that marks a membership usable after
   identity acceptance and account readiness are proven.

These capabilities must remain separate because delivery is a communication side effect,
activation is an authorization side effect, and neither should implicitly assign
seats, update auth claims, launch campaigns, enable go-live, or move money.

Required boundary docs checked:

- `AGENTS.md`
- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/referral-saas/ROADMAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_MEMBERSHIP_INVITATION_BOUNDARY.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_MEMBERSHIP_INTENT_PHYSICAL_VERIFICATION.md`
- `docs/sa/TENANT_ACCOUNT_LIFECYCLE_MEMBERSHIP_MODEL.md`
- `docs/roadmap/ORDERED_TASK_LIST.md`

Implementation/source files inspected:

- `dp/migrations/082_referral_saas_account_foundation.sql`
- `services/referral_saas_account_membership_service.py`
- `apps/api/routers/referral_saas_accounts.py`
- `scripts/referral_saas_account_membership_intent_physical_check.py`
- `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`

## Future Route Contract

Candidate product route family:

| Route | Method | Purpose |
| --- | --- | --- |
| `/v1/referral-saas/accounts/{accountRef}/membership-invitations/{membershipRef}/delivery` | `POST` | Request approved invitation delivery for an existing invited membership. |
| `/v1/referral-saas/accounts/{accountRef}/memberships/{membershipRef}/activation` | `POST` | Activate a previously invited membership after identity acceptance and readiness checks pass. |
| `/v1/referral-saas/accounts/{accountRef}/memberships/{membershipRef}` | `GET` | Read safe membership lifecycle state. |

The route path alone must never authorize delivery or activation. Each command
must resolve account context, membership context, actor permissions, tenant
link status, external reference status, and audit/idempotency evidence.

## Invitation Delivery Command

TASK-246 implementation note: Referral SaaS now has a readiness gate that
distinguishes Email channel URL/secret configuration from an approved provider
reference scoped for Referral SaaS invitation delivery. This does not send
email or activate memberships; it only makes the provider approval requirement
visible in Technical Setup.

TASK-247 implementation note: People and Access activation readiness now exposes
safe recipient contact readiness from existing hashed contact evidence. Product
responses show statuses such as `CONTACT_REFERENCE_PRESENT` or
`CONTACT_REFERENCE_MISSING`, but they do not expose the email hash, raw email,
provider secrets, user identifiers, or internal tenant identifiers.

TASK-248 implementation note: People and Access can now request the guarded
delivery boundary from the selected customer profile when a membership is
invited, recipient contact evidence exists, and an approved invite-provider
reference is visible from Technical Setup. The request does not send email. The
service derives recipient readiness from backend contact evidence instead of
requiring the browser to supply a recipient hash.
`recipientHash` is intentionally not accepted from the browser in the current
guarded UI path; it remains a redacted backend/audit concept for delivery
boundary evidence.

Current guarded request shape:

```json
{
  "accountScope": {
    "refType": "external_tenant_ref",
    "externalRef": "customer-safe-account-ref",
    "context": "setup"
  },
  "delivery": {
    "providerRef": "approved-provider-reference",
    "channel": "EMAIL",
    "templateRef": "referral-saas-account-invite-v1"
  },
  "reasonCode": "ACCOUNT_SETUP_INVITE_DELIVERY",
  "correlationId": "client-correlation-id",
  "idempotencyKey": "client-generated-key"
}
```

Required delivery gates:

- Membership exists, belongs to the resolved account, and has status `INVITED`.
- Account status is `PENDING_ONBOARDING` or `ACTIVE`, not suspended, disabled,
  or archived.
- Tenant link is `PENDING_SETUP` or `ACTIVE`, not suspended, disabled, or
  archived.
- External reference is `ACTIVE`.
- Delivery provider is configured, approved, and scoped for Referral SaaS.
- Recipient contact evidence exists as a safe reference; raw email is not
  persisted or returned by product responses.
- Recipient data is hashed/redacted in product responses.
- Idempotency key and payload hash are stored for replay/conflict detection.
- Audit evidence records provider reference, channel, template reference,
  actor, reason, correlation ID, idempotency hash, and no-auth/no-seat/no-money
  confirmations.

Allowed delivery statuses:

| Status | Meaning |
| --- | --- |
| `INVITATION_DELIVERY_REQUESTED` | Delivery request accepted by the platform and queued or handed to an approved provider. |
| `INVITATION_DELIVERY_REPLAYED` | Same idempotency key and payload returned the same safe result. |
| `DELIVERY_PROVIDER_NOT_CONFIGURED` | Provider is missing, disabled, or not approved for Referral SaaS. |
| `DELIVERY_REJECTED_MEMBERSHIP_NOT_INVITED` | Membership is not in an invited state. |
| `DELIVERY_REJECTED_UNSAFE_PAYLOAD` | Payload attempted raw secrets, auth changes, seats, activation, campaign/go-live, or money behavior. |
| `IDEMPOTENCY_CONFLICT` | Same key was reused with different delivery content. |

## Membership Activation Command

Future request shape:

```json
{
  "accountScope": {
    "refType": "external_tenant_ref",
    "externalRef": "customer-safe-account-ref",
    "context": "runtime"
  },
  "identityAcceptance": {
    "acceptedSubject": "identity-provider-subject",
    "acceptedAt": "2026-07-18T00:00:00Z",
    "acceptanceEvidenceRef": "safe-audit-reference"
  },
  "reasonCode": "ACCOUNT_SETUP_MEMBERSHIP_ACTIVATION",
  "correlationId": "client-correlation-id",
  "idempotencyKey": "client-generated-key"
}
```

Required activation gates:

- Membership exists, belongs to the resolved account, and has status `INVITED`.
- Accepted identity subject matches the invited user subject or an approved
  identity-link record.
- Account status is `ACTIVE` before membership can operate runtime product
  routes. `PENDING_ONBOARDING` may allow setup-only activation only if a later
  task explicitly defines that narrower permission.
- Tenant link status is `ACTIVE` for runtime access.
- External reference status is `ACTIVE`.
- Role family and permission set are recognized policy references.
- Actor has account-owner, platform-admin, or reviewed setup-owner permission.
- No suspended, disabled, archived, or duplicate active membership exists for
  the same actor, account, tenant scope, and role family.
- Idempotency key and payload hash are stored for replay/conflict detection.
- Account audit evidence captures previous status, next status, actor,
  accepted subject reference, reason, correlation ID, idempotency hash, and
  redactions.

Allowed activation statuses:

| Status | Meaning |
| --- | --- |
| `MEMBERSHIP_ACTIVATED` | Membership moved from `INVITED` to `ACTIVE`. |
| `MEMBERSHIP_ACTIVATION_REPLAYED` | Same idempotency key and payload returned the same safe result. |
| `ACTIVATION_REJECTED_IDENTITY_NOT_ACCEPTED` | Acceptance evidence is missing or does not match the invitation. |
| `ACTIVATION_REJECTED_ACCOUNT_NOT_ACTIVE` | Account is not active enough for the requested access mode. |
| `ACTIVATION_REJECTED_TENANT_LINK_NOT_ACTIVE` | Tenant link cannot authorize runtime access. |
| `ACTIVATION_REJECTED_EXTERNAL_REFERENCE_NOT_ACTIVE` | External reference cannot authorize runtime access. |
| `ACTIVATION_REJECTED_DUPLICATE_ACTIVE_MEMBERSHIP` | Activation would create duplicate active access. |
| `ACTIVATION_REJECTED_UNSAFE_PAYLOAD` | Payload attempted seats, auth claims, go-live, campaigns, credentials, webhooks, rewards, or money behavior. |
| `IDEMPOTENCY_CONFLICT` | Same key was reused with different activation content. |

## Seat And Auth Claim Boundary

Activation must not assign seats or mutate auth/session claims in the first
implementation. These are separate future capabilities:

- Seat assignment: commercial entitlement command against `platform_seats`.
- Auth/session claim update: identity/session integration that reads active
  membership and tenant/account context.

Activation may expose `canOperateSetup` or `canOperateRuntime` in a safe
response, but it must not persist auth claims, issue credentials, refresh JWTs,
create API keys, or change partner/client credentials.

## Audit And Idempotency

Both delivery and activation commands must:

- require `idempotencyKey`
- require `correlationId`
- hash idempotency keys before persistence
- hash effective payloads before replay comparison
- return replay for same key and payload
- return conflict for same key and changed payload
- record account audit events
- redact internal tenant identifiers, user identifiers, client identifiers,
  email hashes, recipient hashes, idempotency hashes, and provider secrets from
  product responses

## Guardrails

Required guardrails:

- `NO_RAW_EMAIL_STORAGE`
- `NO_PROVIDER_SECRET_EXPOSURE`
- `NO_AUTH_CLAIM_CHANGE`
- `NO_SEAT_ASSIGNMENT`
- `NO_TENANT_CODE_EXPOSURE`
- `NO_CAMPAIGN_ACTIVATION`
- `NO_GO_LIVE_CHANGE`
- `NO_MONEY_MOVEMENT`
- `NO_DLAAS_MARKETPLACE_EXPANSION`

Required redactions:

- `internal_tenant_identifier`
- `user_identifier`
- `client_identifier`
- `email_hash`
- `recipient_hash`
- `idempotency_key_hash`
- `provider_secret`

## UX Boundary

Account Setup should show delivery and activation as future locked steps until
their runtime tasks exist.

Required UX posture:

- Step 2 can show "Role intent recorded" for invited membership evidence.
- "Send invite" must remain disabled until an approved delivery provider is
  configured and the delivery command exists.
- "Activate access" must remain disabled until identity acceptance, active
  account, active tenant link, active external reference, and activation command
  support exist.
- Campaign setup may continue to readiness/testing only according to the
  current product guardrails; membership activation does not automatically launch campaigns or enable go-live.

## Explicit Non-Goals

TASK-214 does not add:

- backend routes
- backend service writes
- frontend controls
- schema or migrations
- invitation provider integration
- email or messaging delivery
- identity-provider integration
- auth/session claim changes
- seat assignment
- account lifecycle commands
- account maintenance commands
- tenant creation
- campaign activation
- go-live
- credential lifecycle
- webhook delivery
- support-case writes
- repair, replay, or retry commands
- reward, funding, fulfilment, settlement, commission, wallet, invoice, payout,
  sponsor billing, treasury, or money behavior
- broad DLaaS marketplace behavior
- source-code forks

## Definition Of Done

Membership delivery and activation implementation may begin only after a narrow
runtime task references this boundary and proves idempotency, audit, permission,
account status, tenant link status, external reference status, identity
acceptance, duplicate prevention, redaction, and no adjacent seat/auth/campaign/
go-live/money side effects.
