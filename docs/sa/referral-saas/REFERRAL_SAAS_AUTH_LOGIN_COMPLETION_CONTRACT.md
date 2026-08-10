# Referral SaaS Governed Auth And Login Completion Contract

TASK ID: TASK-345

Product boundary: Shared Platform with Referral SaaS impact.

Status: Contract plus implemented safe API boundaries. TASK-346 implements
membership-level login completion readiness/intent recording. TASK-365 adds a
read-only account-level identity/login reconciliation projection. Neither task
performs identity-provider calls, credential creation, invite delivery, seat
assignment from reconciliation, auth/session claim mutation, campaign
activation, go-live, billing, money movement, DLaaS expansion, or source fork.

## Boundary

People and Access now lets an operator name the people responsible for a
selected customer, record accepted customer access, and optionally reserve a
platform seat through the governed provisioning boundary. TASK-345 defines the
next boundary: when the platform may say that a person is ready to sign in.

These states must stay separate:

1. Named person: the customer has identified who should manage the account.
2. Confirmed for customer work: the person has accepted responsibility for the
   selected customer.
3. Platform seat assigned: commercial or operational capacity has been reserved
   for that accepted membership.
4. Login completion: identity-provider and permission evidence is complete
   enough to allow sign-in.

A platform seat is not a password, invite, login session, or permission claim.
Login completion is the governed identity boundary that comes after customer
access is confirmed and after a seat is assigned when the account policy needs
one.

Required boundary docs checked:

- `AGENTS.md`
- `docs/product/README.md`
- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/README.md`
- `docs/roadmap/referral-saas/ROADMAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_MEMBERSHIP_ACTIVATION_DELIVERY_BOUNDARY.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_ACCESS_PROVISIONING_COMMAND_CONTRACT.md`
- `docs/roadmap/ORDERED_TASK_LIST.md`

## Current Source Facts

Current platform behavior supports:

- customer account foundation creation and activation
- external-reference and tenant-link account resolution
- invited membership intent
- invited membership edit and removal intent
- manual accepted-access evidence for Amplifi Admin
- person-level membership activation to active customer access
- guarded platform seat assignment for active memberships
- read models that expose accepted access, seat state, and missing setup
  evidence without exposing internal tenant identifiers

Current platform behavior does not support:

- live identity-provider provisioning
- password, magic-link, or credential creation
- email invite delivery as part of login setup
- auth/session claim propagation
- permission claim mutation from the People and Access page
- raw identity-provider payload persistence through product routes

## Product Meaning

The product should use these plain-language meanings:

| Product phrase | Platform meaning |
| --- | --- |
| Named | A person has been recorded for a customer responsibility. |
| Confirmed for customer work | The person has accepted the responsibility for this customer. |
| Platform seat assigned | The platform has reserved an access slot for this membership. |
| Login ready | The identity-provider and permission evidence required for sign-in is complete. |
| Login managed externally | The customer does not need Amplifi platform login for this person. |

The UI must avoid saying a person can sign in merely because the membership is
active or a seat exists. A person can be ready for customer referral work before
they have platform login.

## Candidate Product Routes

TASK-346 introduces an account-scoped and membership-scoped route family:

| Route | Method | Purpose |
| --- | --- | --- |
| `/v1/referral-saas/accounts/{accountRef}/memberships/{membershipRef}/login-completion-readiness` | `GET` | Read safe login completion posture for one accepted customer membership. |
| `/v1/referral-saas/accounts/{accountRef}/memberships/{membershipRef}/login-completion-intents` | `POST` | Record governed login completion intent/evidence for one membership. |
| `/v1/referral-saas/accounts/{accountRef}/identity-login-reconciliation` | `GET` | Read account-level reconciliation across customer access, platform seat, identity-provider evidence, revocation posture, and auth-claim readiness. |

Implementation note: TASK-346 implements these routes as a safe API boundary.
They inspect and record login completion intent/evidence through membership
metadata and platform account audit events only. They do not create credentials,
send invites, assign seats, mutate auth/session claims, activate campaigns,
trigger go-live, bill, move money, expose tenant codes, add DLaaS behavior, or
fork source code. TASK-347 remains the People and Access UI wiring.

The route path is never sufficient authorization. The service must resolve the
selected customer account, membership, actor role, account status, tenant link,
external reference, accepted access, seat policy, provider approval, audit
evidence, idempotency, and redactions before returning a ready or completed
state.

## Candidate Readiness Statuses

| Status | Meaning |
| --- | --- |
| `LOGIN_COMPLETION_NOT_REQUIRED` | The person is confirmed for customer work but does not need platform login. |
| `LOGIN_COMPLETION_BLOCKED_ACCOUNT_NOT_ACTIVE` | The selected customer foundation is not active. |
| `LOGIN_COMPLETION_BLOCKED_MEMBERSHIP_NOT_ACTIVE` | The person has not accepted customer access. |
| `LOGIN_COMPLETION_BLOCKED_SEAT_NOT_ASSIGNED` | Account policy requires a platform seat before login completion. |
| `LOGIN_COMPLETION_BLOCKED_AUTH_PROVIDER_NOT_APPROVED` | The identity-provider or SSO setup is not approved for this customer. |
| `LOGIN_COMPLETION_BLOCKED_PERMISSION_PROFILE_MISSING` | Responsibility cannot map to a governed permission profile. |
| `LOGIN_COMPLETION_READY` | Required evidence is present and a completion intent can be recorded. |
| `LOGIN_COMPLETION_RECORDED` | The platform has recorded completion evidence. |
| `LOGIN_COMPLETION_REPLAYED` | The same idempotency key and payload returned the same safe result. |
| `LOGIN_COMPLETION_REJECTED_UNSAFE_PAYLOAD` | The request attempted raw secrets, tokens, arbitrary claims, campaign, billing, money, or DLaaS behavior. |
| `IDEMPOTENCY_CONFLICT` | The same idempotency key was reused with different login completion content. |

## Candidate Request Shape

```json
{
  "accountScope": {
    "refType": "external_tenant_ref",
    "externalRef": "customer-reference",
    "context": "setup"
  },
  "loginCompletion": {
    "intent": "PLATFORM_LOGIN_REQUIRED",
    "identitySubjectRef": "safe-identity-subject-reference",
    "authProviderRef": "approved-auth-provider-reference",
    "seatEvidenceRef": "safe-seat-assignment-reference",
    "permissionProfile": "REFERRAL_SAAS_ACCOUNT_ADMIN",
    "operatorReason": "Person needs Amplifi login for customer operations."
  },
  "correlationId": "client-correlation-id",
  "idempotencyKey": "client-generated-key"
}
```

Allowed `intent` values:

- `PLATFORM_LOGIN_REQUIRED`
- `LOGIN_NOT_REQUIRED`
- `EXTERNAL_IDP_MANAGED`

Allowed `permissionProfile` values must be policy-owned and derived from the
person's customer responsibility. The browser must not send arbitrary auth
claims. Initial Referral SaaS mappings should be:

| Customer responsibility | Permission profile |
| --- | --- |
| Account owner | `REFERRAL_SAAS_ACCOUNT_ADMIN` |
| Campaign manager | `REFERRAL_SAAS_CAMPAIGN_MANAGER` |
| Support contact | `REFERRAL_SAAS_SUPPORT` |
| Reporting contact | `REFERRAL_SAAS_ANALYST` |

## Required Gates

The command may record login completion only when:

- Actor is Amplifi Admin or a future customer admin with explicit login setup
  permission.
- Account context resolves to the selected customer.
- Account status is `ACTIVE`.
- Tenant link is `ACTIVE`.
- External reference is `ACTIVE`.
- Membership belongs to the resolved account.
- Membership status is `ACTIVE`.
- Responsibility maps to a governed permission profile.
- Seat assignment exists when account policy requires platform login seats.
- Identity-provider or external-login evidence is approved.
- No raw password, token, MFA secret, provider payload, arbitrary claim map,
  internal tenant code, session cookie, invite link, client secret, or API key
  is accepted from the browser.
- Idempotency key, payload hash, actor, reason, correlation ID, and redactions
  are recorded.

## Safe Response Shape

```json
{
  "loginCompletionStatus": "LOGIN_COMPLETION_RECORDED",
  "accountRef": "ACCT_SAFE_REF",
  "membershipRef": "safe-membership-ref",
  "person": {
    "displayName": "Jane Doe",
    "responsibilities": ["ACCOUNT_OWNER"]
  },
  "seat": {
    "seatAssignmentStatus": "ASSIGNED"
  },
  "identity": {
    "identityProviderStatus": "APPROVED",
    "authClaimStatus": "CLAIM_PROPAGATION_RECORDED"
  },
  "plainLanguageSummary": "Jane Doe is ready for platform login. No password was created and no campaign, billing, or money action was taken.",
  "nextActions": [],
  "guardrails": [
    "NO_RAW_CREDENTIAL_STORAGE",
    "NO_TOKEN_EXPOSURE",
    "NO_INVITE_DELIVERY",
    "NO_CAMPAIGN_ACTIVATION",
    "NO_BILLING_OR_MONEY_MOVEMENT"
  ],
  "redactions": [
    "tenant_code",
    "raw_auth_claims",
    "provider_payload",
    "provider_secret"
  ],
  "correlationId": "client-correlation-id",
  "auditRef": "safe-audit-reference"
}
```

Until a live identity-provider adapter is explicitly implemented, the command
may record readiness/completion evidence only. It must not create credentials
or mutate active auth/session claims.

## UI Contract

People and Access should remain the person/responsibility workspace. TASK-347
should show login completion as a person-level follow-on action only after the
person is confirmed for customer work.

Recommended lifecycle language:

| Stage | UI label | Plain-language copy |
| --- | --- | --- |
| 1 | Added | Person is named for this customer. |
| 2 | Confirmed for customer work | Person can manage the customer responsibility. |
| 3 | Platform seat assigned | A seat is reserved if this person must sign in. |
| 4 | Login ready | Identity and permission evidence is complete. |

The screen should explain:

- "Confirmed for customer work" lets campaign work continue.
- "Platform login setup" is optional unless the person must sign in.
- A seat reserves capacity; it does not create a password.
- Login permissions are completed through governed identity setup.
- If the customer manages login externally, mark the person as
  `LOGIN_NOT_REQUIRED` or `EXTERNAL_IDP_MANAGED`.

## Audit, Idempotency, And Redactions

The future API must:

- require `idempotencyKey`
- require `correlationId`
- hash idempotency keys before persistence
- return replay for the same key and payload
- return conflict for the same key with different payload
- record account, membership, actor, reason, permission profile, provider
  evidence reference, seat evidence reference, and no-adjacent-action
  confirmations
- redact raw secrets, tokens, auth provider payloads, raw claim maps, internal
  tenant identifiers, invite links, credential material, and session artifacts

## Explicit Non-Goals

TASK-345 does not add:

- runtime routes
- backend service writes
- database migrations
- frontend controls
- identity-provider integration
- credential creation
- password, magic-link, or invite delivery
- auth/session claim mutation
- campaign activation
- go-live enablement
- billing or money movement
- DLaaS expansion
- source-code duplication

