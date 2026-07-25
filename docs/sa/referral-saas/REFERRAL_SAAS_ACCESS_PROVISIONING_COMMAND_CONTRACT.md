# Referral SaaS Access Provisioning Command Contract

TASK ID: TASK-284

Product boundary: Referral SaaS.

Status: Command-boundary contract only. No runtime route, service write,
frontend action enablement, schema migration, live DB mutation, seat assignment,
identity-provider integration, auth/session claim change, credential creation,
invitation delivery, campaign activation, go-live, billing, money movement, or
DLaaS expansion is made by this task.

## Boundary

People and Access now distinguishes three separate states:

1. Named person intent: who should manage a selected customer.
2. Accepted access: evidence that the named person accepted responsibility for
   that customer.
3. Login and seat provisioning: the governed operational step that assigns a
   platform seat and prepares identity/login claims.

TASK-284 defines the third step. It must not be collapsed into invitation
intent or accepted-access evidence because a person can be known and accepted
without being able to log in, consume a seat, or receive auth claims.

Required boundary docs checked:

- `AGENTS.md`
- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/referral-saas/ROADMAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`
- `docs/roadmap/ORDERED_TASK_LIST.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_MEMBERSHIP_INVITATION_BOUNDARY.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_MEMBERSHIP_ACTIVATION_DELIVERY_BOUNDARY.md`

Source-of-truth code/schema checked:

- `dp/migrations/082_referral_saas_account_foundation.sql`
- `services/referral_saas_account_membership_service.py`
- `frontend/src/api/endpoints/referralSaasAccounts.ts`

## Current Source Facts

Current schema supports:

- `platform_users.status` values: `INVITED`, `ACTIVE`, `SUSPENDED`,
  `DISABLED`, `ARCHIVED`
- `platform_memberships.status` values: `INVITED`, `ACTIVE`, `SUSPENDED`,
  `DISABLED`, `ARCHIVED`
- `platform_seats.status` values: `AVAILABLE`, `ASSIGNED`, `SUSPENDED`,
  `DISABLED`, `ARCHIVED`
- `platform_seats.assigned_membership_id`
- `platform_memberships.seat_id`
- `platform_account_audit_events` with account, membership, tenant, event,
  actor, reason, correlation, idempotency, evidence, and redaction fields

Current service/read-model behavior supports:

- invited membership intent
- invited membership edit/cancel
- manual accepted-access activation to `ACTIVE` membership status
- activation readiness response fields for seat assignment and auth claim
  posture
- explicit no-seat and no-auth-claim confirmations on current activation
  commands

Current service/read-model behavior does not support:

- assigning or reserving a seat through People and Access
- provisioning login credentials
- mutating auth/session claims
- calling an identity provider
- assigning product seats as a side effect of accepted access

## Candidate Product Route

The future product route family should be account-scoped and membership-scoped:

| Route | Method | Purpose |
| --- | --- | --- |
| `/v1/referral-saas/accounts/{accountRef}/memberships/{membershipRef}/access-provisioning` | `POST` | Request governed login and seat provisioning for an accepted customer membership. |
| `/v1/referral-saas/accounts/{accountRef}/memberships/{membershipRef}/access-provisioning` | `GET` | Read safe provisioning posture for a selected customer membership. |

The path does not authorize the operation by itself. The service must resolve
selected account context, membership context, actor permissions, tenant link,
external reference, accepted membership, seat availability, identity provider
readiness, audit evidence, and idempotency before any state change.

## Candidate Request Shape

```json
{
  "accountScope": {
    "refType": "external_tenant_ref",
    "externalRef": "customer-reference",
    "context": "setup"
  },
  "provisioning": {
    "seatType": "ADMIN",
    "seatAssignmentEvidenceRef": "safe-seat-evidence-ref",
    "authProviderRef": "approved-auth-provider-ref",
    "authClaimEvidenceRef": "safe-auth-evidence-ref",
    "operatorNotes": "Reason for provisioning this customer access."
  },
  "reasonCode": "CUSTOMER_ACCESS_PROVISIONING",
  "correlationId": "client-correlation-id",
  "idempotencyKey": "client-generated-key"
}
```

Allowed `seatType` values must come from the schema-backed
`platform_seats.seat_type` values. The first Referral SaaS implementation
should normally map:

| Access responsibility | Seat type |
| --- | --- |
| Account owner | `ADMIN` |
| Campaign manager | `OPERATOR` |

Auth provider and auth claim fields are evidence references only until an
identity-provider adapter exists. The first implementation must not accept raw
credentials, tokens, secrets, or arbitrary claim payloads from the browser.

## Required Gates

The command may proceed only when all required gates pass:

- Actor is authorized as Amplifi Admin or a future account-admin role with
  explicit provisioning permission.
- Account exists in the selected customer context.
- Account status is `ACTIVE`; `PENDING_ONBOARDING` may show accepted-access
  evidence but must not create runtime login/seat access.
- Tenant link is `ACTIVE`.
- External reference is `ACTIVE`.
- Membership belongs to the resolved account.
- Membership status is `ACTIVE`.
- The role family and permission set are recognized.
- No duplicate active seat assignment exists for the same membership.
- A compatible `platform_seats` row is available or can be created by the
  dedicated provisioning implementation.
- Auth provider readiness is approved before any login/auth-claim propagation
  is attempted.
- Idempotency key and payload hash are recorded for replay/conflict behavior.
- Audit evidence records actor, reason, correlation ID, idempotency hash, seat
  evidence, auth evidence, and all no-adjacent-action confirmations.

## Candidate Response Statuses

| Status | Meaning |
| --- | --- |
| `PROVISIONING_REQUEST_RECORDED` | Provisioning request accepted; implementation may assign a seat only if seat and identity gates pass. |
| `PROVISIONING_REPLAYED` | Same idempotency key and payload returned the same safe result. |
| `PROVISIONING_REJECTED_ACCOUNT_NOT_ACTIVE` | Account is not active enough for runtime access. |
| `PROVISIONING_REJECTED_TENANT_LINK_NOT_ACTIVE` | Tenant link cannot authorize runtime access. |
| `PROVISIONING_REJECTED_EXTERNAL_REFERENCE_NOT_ACTIVE` | External reference cannot authorize runtime access. |
| `PROVISIONING_REJECTED_MEMBERSHIP_NOT_ACTIVE` | Membership has not reached accepted access. |
| `PROVISIONING_REJECTED_SEAT_UNAVAILABLE` | No compatible seat is available or creatable under current policy. |
| `PROVISIONING_REJECTED_AUTH_PROVIDER_NOT_READY` | Login/auth-claim provider is not configured and approved. |
| `PROVISIONING_REJECTED_UNSAFE_PAYLOAD` | Payload attempted raw credentials, tokens, arbitrary auth claims, campaign/go-live, billing, or money behavior. |
| `IDEMPOTENCY_CONFLICT` | Same key was reused with different provisioning content. |

## Safe Response Shape

```json
{
  "provisioningStatus": "PROVISIONING_REQUEST_RECORDED",
  "accountRef": "ACCT_SAFE_REF",
  "membershipRef": "safe-membership-ref",
  "seat": {
    "seatType": "ADMIN",
    "seatAssignmentStatus": "ASSIGNED"
  },
  "authClaims": {
    "authClaimStatus": "AUTH_PROVIDER_SYNC_PENDING"
  },
  "guardrails": [
    "NO_RAW_CREDENTIAL_STORAGE",
    "NO_TOKEN_EXPOSURE",
    "NO_CAMPAIGN_ACTIVATION",
    "NO_GO_LIVE_CHANGE",
    "NO_MONEY_MOVEMENT"
  ],
  "redactions": [
    "tenant_code",
    "raw_auth_claims",
    "provider_secret"
  ],
  "correlationId": "client-correlation-id"
}
```

The exact persisted auth-claim status must be implemented only after an
identity-provider integration primitive exists. Until then, auth-claim posture
may be returned as a safe read-model label but must not imply that live login
claims changed.

## UX Contract

People and Access should keep the current Login and Seat Provisioning section,
but the `Provision login & seat` action must remain disabled until the runtime
API and tests exist.

The UI should explain the next steps in plain product language:

- Accepted access means the person is approved to manage this customer.
- Seat assignment is the commercial/platform access slot.
- Login permissions are handled by a separate identity provider workflow.
- Nothing on this page sends an invite, changes auth claims, creates
  credentials, assigns seats, bills, or moves money until the governed command
  exists.

## Explicit Non-Goals

TASK-284 does not add:

- backend routes
- backend service writes
- schema or migration changes
- frontend action enablement
- seat assignment
- auth/session claim propagation
- identity-provider integration
- credential lifecycle
- invitation delivery
- campaign activation
- go-live
- billing, invoicing, payout, wallet, funding, fulfilment, settlement, or
  money behavior
- DLaaS marketplace expansion
- source-code forks

## Definition Of Done

The access provisioning command may be implemented only after a narrow runtime
task references this contract and proves permission, account status, tenant
link status, external reference status, accepted membership, seat availability,
auth-provider readiness, idempotency, audit, redaction, duplicate prevention,
and no adjacent campaign/go-live/billing/money side effects.
