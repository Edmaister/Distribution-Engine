# Referral SaaS Membership Invitation Boundary

TASK ID: TASK-210

Product boundary: Referral SaaS.

Status: Command-boundary contract only. No runtime route, service write,
frontend action, permission helper, identity-provider integration, email
delivery, seat assignment, auth-claim change, migration, or live DB mutation is
made by this task.

## Boundary

Referral SaaS Account Setup can now create and resolve durable account
foundation records, and TASK-209 can read membership posture. The next gap is a
reviewed write boundary for inviting or activating account members without
turning setup into fake user provisioning.

This contract defines the future membership invitation command surface against
the existing account foundation schema:

- `platform_accounts`
- `platform_account_tenants`
- `platform_external_tenant_refs`
- `platform_users`
- `platform_memberships`
- `platform_seats`
- `platform_account_audit_events`

Required boundary docs checked:

- `AGENTS.md`
- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/referral-saas/ROADMAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_WRAPPER_CONTRACT.md`
- `docs/sa/TENANT_ACCOUNT_LIFECYCLE_MEMBERSHIP_MODEL.md`
- `docs/roadmap/ORDERED_TASK_LIST.md`

Implementation/source files inspected:

- `dp/migrations/082_referral_saas_account_foundation.sql`
- `services/referral_saas_account_membership_service.py`
- `services/referral_saas_account_setup_service.py`
- `services/referral_saas_account_foundation_service.py`
- `apps/api/routers/referral_saas_accounts.py`
- `frontend/src/pages/admin/MemberRoleOnboardingPage.tsx`
- `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`

## Purpose

Define the first production-grade membership write contract for Account Setup:

1. Resolve a durable Referral SaaS account from trusted account context.
2. Record a membership invitation intent for a human or integration actor.
3. Preserve idempotency and audit evidence.
4. Keep identity delivery, auth claims, seat assignment, activation, and money
   actions outside the first command until separately implemented.

This means Account Setup can become coherent:

- Company profile creates durable account foundation.
- Users and roles records membership invitation intent.
- Readiness checks whether membership evidence is usable.
- Campaign setup remains blocked until account and membership posture are safe.

## Future Route Contract

Candidate product route family:

| Route | Method | Purpose |
| --- | --- | --- |
| `/v1/referral-saas/accounts/{accountRef}/membership-invitations` | `POST` | Record a bounded account membership invitation intent. |
| `/v1/referral-saas/accounts/{accountRef}/membership-invitations/{membershipRef}` | `GET` | Read safe invitation/membership command result. |

Initial implementation may derive `accountRef` from a resolved account query
instead of accepting path-only authorization. Caller-supplied `accountRef` must
never be enough to authorize the command.

## Request Shape

Future command request:

```json
{
  "actor": {
    "actorType": "USER",
    "subject": "identity-provider-subject-or-future-placeholder",
    "emailHash": "optional-privacy-safe-email-hash",
    "displayName": "optional-display-name"
  },
  "membership": {
    "roleFamily": "DISTRIBUTION_ADMIN",
    "permissionSet": "REFERRAL_SAAS_ACCOUNT_ADMIN",
    "tenantScope": "PRIMARY_ACCOUNT_TENANT"
  },
  "reasonCode": "ACCOUNT_SETUP_USER_ROLE",
  "correlationId": "client-correlation-id",
  "idempotencyKey": "client-generated-key"
}
```

Required rules:

- `idempotencyKey` is mandatory for every write.
- `correlationId` is mandatory for audit traceability.
- `roleFamily` must match the schema-approved membership role families.
- `permissionSet` must be a named policy reference, not an arbitrary inline
  permission list.
- `tenantScope` may request primary account tenant scope, but the service must
  resolve the internal `tenant_code`; it must not accept caller-supplied
  `tenant_code`.
- Email addresses must not be stored raw in the account foundation tables.
  Future implementations may accept raw email only long enough to hash or hand
  it to an approved delivery provider, then redact it from persisted evidence.

## Response Shape

Future command response:

```json
{
  "commandStatus": "INVITATION_INTENT_RECORDED",
  "membership": {
    "membershipRef": "membership-safe-reference",
    "status": "INVITED",
    "roleFamily": "DISTRIBUTION_ADMIN",
    "permissionSet": "REFERRAL_SAAS_ACCOUNT_ADMIN",
    "canOperateSetup": false
  },
  "delivery": {
    "status": "DELIVERY_NOT_CONFIGURED",
    "nextAction": "Configure approved invitation delivery provider"
  },
  "idempotency": {
    "status": "RECORDED"
  },
  "guardrails": [
    "NO_RAW_EMAIL_STORAGE",
    "NO_EMAIL_DELIVERY_WITHOUT_PROVIDER",
    "NO_AUTH_CLAIM_CHANGE",
    "NO_SEAT_ASSIGNMENT",
    "NO_TENANT_CODE_EXPOSURE",
    "NO_MONEY_MOVEMENT"
  ],
  "redactions": [
    "internal_tenant_identifier",
    "user_identifier",
    "client_identifier",
    "email_hash",
    "idempotency_key_hash"
  ]
}
```

Allowed command statuses:

| Status | Meaning |
| --- | --- |
| `INVITATION_INTENT_RECORDED` | Membership invitation intent was recorded as `INVITED`. |
| `INVITATION_INTENT_REPLAYED` | Same idempotency key and payload returned the same result. |
| `IDEMPOTENCY_CONFLICT` | Same key was reused with different command content. |
| `ACCOUNT_NOT_READY` | Account, tenant link, or external reference is not usable for invitation intent. |
| `MEMBERSHIP_ALREADY_EXISTS` | A non-archived membership already exists for actor, account, tenant scope, and role. |
| `REJECTED_UNSAFE_SCOPE` | Caller supplied internal tenant identifiers or untrusted account scope. |
| `REJECTED_UNSAFE_PAYLOAD` | Payload attempted delivery, credentials, auth claims, seats, live launch, campaign activation, or money movement. |

## State Model

The first write implementation may create or reuse:

- `platform_users.status = 'INVITED'`
- `platform_memberships.status = 'INVITED'`
- `platform_account_audit_events.event_type = 'REFERRAL_SAAS_MEMBERSHIP_INVITATION_INTENT'`
- `platform_account_audit_events.event_status = 'RECORDED'` or `DUPLICATE`

It must not set:

- `platform_users.status = 'ACTIVE'`
- `platform_memberships.status = 'ACTIVE'`
- `platform_seats.status = 'ASSIGNED'`
- auth/session account claims
- invitation delivery status outside a future approved delivery table/provider

Membership activation is a separate future command. Activation must prove
accepted identity, active membership status, account status, tenant-link status,
external-reference status, audit evidence, and route authorization before it can
change access posture.

## Idempotency And Audit

The future command must hash the effective command payload and the idempotency
key before storing replay evidence. Replay must return the same safe response
when the key and payload hash match, and must return conflict when the key is
reused with different content.

Audit evidence must include:

- account ID
- resolved account tenant ID where available
- resolved external reference ID where available
- membership ID when recorded
- resolved internal tenant code in audit only, never in product response
- actor reference and actor role
- command name
- previous status and next status
- reason code
- correlation ID
- idempotency key hash
- evidence summary
- redactions

## Permission Boundary

Initial implementation should remain admin/operator or reviewed Account Setup
owner controlled until membership-aware authorization is implemented.

Required rejection cases:

- unauthenticated caller
- adjacent product role without account setup permission
- caller-supplied internal `tenant_code`
- disabled, suspended, archived, or unresolved account
- disabled, suspended, archived, rotated, or unresolved external reference
- duplicate active/invited/suspended membership for the same actor, account,
  tenant scope, and role family
- raw credential material, invite delivery instructions, auth-claim mutation,
  seat assignment, go-live, campaign activation, webhook delivery, reward,
  funding, fulfilment, settlement, commission, wallet, invoice, payout, or
  sponsor billing keys

## UX Boundary

Account Setup should present this future command as the Step 2 Users and Roles
action. It should not be hidden in readiness or maintenance.

Required UX posture:

- Show the command as "Invite setup member" or "Record member invite" only after
  durable account foundation exists.
- Explain that the first implementation records invitation intent and does not
  send email until delivery provider setup exists.
- Show membership posture after recording intent.
- Keep account maintenance for fixing existing account drift, not first-time
  setup.

## Explicit Non-Goals

TASK-210 does not add:

- backend routes
- backend service writes
- frontend controls
- schema or migrations
- user creation command implementation
- email or messaging invitation delivery
- identity-provider integration
- auth/session claim changes
- membership activation
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

The membership/invitation write implementation can begin when this contract is
used to create a narrow service/API task that records invitation intent with
idempotency, audit, redaction, duplicate prevention, and no delivery, seat,
activation, auth-claim, campaign, go-live, or money side effects.
