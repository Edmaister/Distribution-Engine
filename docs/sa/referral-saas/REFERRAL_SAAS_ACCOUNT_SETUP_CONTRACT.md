# Referral SaaS Account Setup Contract

TASK ID: TASK-134

Product boundary: Referral SaaS.

Required boundary docs checked:

- `docs/product/README.md`
- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/README.md`
- `docs/roadmap/referral-saas/ROADMAP.md`

Supporting SA docs checked:

- `docs/sa/TENANT_IDENTIFIER_BOUNDARY_DECISION.md`
- `docs/sa/TENANT_ACCOUNT_BOUNDARY_MAP.md`
- `docs/sa/TENANT_ACCOUNT_LIFECYCLE_MEMBERSHIP_MODEL.md`
- `docs/sa/LIVE_CRITICAL_STATE_INVENTORY.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`

Current implementation files inspected:

- `dp/migrations/031_tenent.sql`
- `services/tenant_service.py`
- `apps/api/routers/admin_tenants.py`
- `apps/api/routers/session.py`
- `utils/security.py`
- `utils/permissions.py`
- `test/test_tenant_service.py`
- `test/test_admin_tenant.py`

## Purpose

Define the account setup contract needed to package the existing referral,
campaign, progress, link/code, and attribution capabilities as a SaaS product.

This is a contract and readiness document only. It does not authorize schema,
service, route, frontend, auth, permission, migration, billing, or live database
changes.

## Boundary Decision

Referral SaaS account setup must be an additive product wrapper around the
current internal tenant model.

Rules:

- Keep `tenant_code` as the internal runtime tenant identifier.
- Do not expose `tenant_code` as the primary public SaaS account identifier for
  new productized APIs.
- Resolve external SaaS-facing account references into internal `tenant_code`
  before calling existing services.
- Do not copy, fork, or duplicate referral, campaign, progress, attribution, or
  tenant service code for the product boundary.
- Keep full DLaaS account, seat, billing, white-label, funding, fulfilment, and
  settlement scope out of this first contract unless separately tasked.

## Current Facts

The current tenant schema is small:

- `tenants.tenant_code` is the primary key.
- `tenants` stores `tenant_name`, `industry`, `currency`, `locale`,
  `is_active`, and `created_at`.
- `referral_instances.tenant_code` is non-null and indexed with
  `referral_track_id`.

The current service boundary is `services/tenant_service.py`:

- `create_tenant(tenant_code, tenant_name, industry)` inserts or updates a
  tenant row.
- `get_tenant(tenant_code)` returns tenant display and active-state fields.

The current admin route boundary is `apps/api/routers/admin_tenants.py`:

- `POST /admin/tenants/` normalizes and creates an internal tenant.
- `GET /admin/tenants/{tenant_code}` fetches an internal tenant.
- The route requires admin authentication.

The current auth/session boundary:

- `utils/security.py` resolves identities with `role`, `tenant_code`, `tenant`,
  and role-specific claims.
- `utils/permissions.py` enforces tenant scope by comparing the caller identity
  tenant claim with the requested tenant.
- `GET /auth/session` returns public session identity and workspace access.

Current gap:

- No first-class Referral SaaS account setup contract exists.
- No product-facing account reference exists above `tenant_code`.
- No account setup checklist exists for the Referral SaaS wedge.
- No user membership/seat model is implemented.
- No plan/limit gate is implemented for Referral SaaS.
- No live DB verification has confirmed runtime tenant/account assumptions.

Implementation note:

- `services/tenant_service.py` is async, while `apps/api/routers/admin_tenants.py`
  currently calls its functions from sync route functions. Existing tests
  monkeypatch route-level functions. A future implementation task must verify
  the route/service async boundary before reusing or extending these routes.

## Referral SaaS Account Concepts

This contract narrows the broader TASK-005 account model to the first SaaS
launch wedge.

### Account

The commercial customer of the Referral Management and Campaign Attribution SaaS
product.

Minimum product-facing fields for a future implementation:

| Field | Purpose |
| --- | --- |
| `account_ref` | External SaaS-facing stable identifier. Must not be `tenant_code`. |
| `account_name` | Customer display name. |
| `account_status` | Setup and access lifecycle. |
| `primary_contact_ref` | Optional external reference to setup owner or account admin. |
| `plan_code` | Basic plan or product entitlement code. |
| `created_at`, `updated_at` | Audit timestamps. |

### Tenant Link

The compatibility bridge from account setup into existing runtime data.

Minimum future fields:

| Field | Purpose |
| --- | --- |
| `account_ref` | Product-facing account reference. |
| `tenant_code` | Existing internal tenant partition. |
| `tenant_link_status` | Whether the account can resolve into this tenant. |
| `is_primary` | Default tenant for Referral SaaS operations. |

### External Reference

The product-facing reference accepted by future Referral SaaS APIs or derived
from credentials.

Minimum future fields:

| Field | Purpose |
| --- | --- |
| `external_tenant_ref` | Public or integration-safe tenant/account reference. |
| `account_ref` | Owning account reference. |
| `tenant_code` | Resolved internal tenant partition. |
| `status` | Active, suspended, disabled, archived, or rotated. |

### Membership

The user or actor relationship to the Referral SaaS account.

Minimum future fields:

| Field | Purpose |
| --- | --- |
| `member_ref` | External user/member reference. |
| `account_ref` | Account scope. |
| `tenant_code` | Optional resolved tenant scope. |
| `role_family` | Account owner, campaign manager, analyst, support operator, or integration actor. |
| `status` | Invited, active, suspended, disabled, archived. |

### Setup Checklist

The product readiness view that tells a SaaS customer or operator what remains
before referral/campaign attribution can be used.

Minimum checklist items:

| Checklist item | Required for first launch | Source or future owner |
| --- | --- | --- |
| Account profile captured | Yes | Future account setup service |
| Internal tenant linked | Yes | Existing `tenants` plus future tenant link |
| External tenant reference active | Yes | Future resolver/mapping layer |
| Admin/member access active | Yes | Future membership layer |
| Default campaign settings ready | Yes | Campaign setup/readiness tasks |
| Referral terms copy configured | Yes | Referral code/validation tasks |
| Progress event contract selected | Yes | Progress event contract task |
| Attribution reporting baseline ready | Yes | Attribution/reporting tasks |
| Billing plan selected | Basic gate only | Future plan/limit gate |
| Funding/fulfilment/settlement configured | No | Explicitly deferred |

## Account Setup States

Use a product-facing setup state independent from current `tenants.is_active`.

Recommended future setup states:

| State | Meaning | Allowed SaaS behavior |
| --- | --- | --- |
| `DRAFT` | Account setup has started but required fields are incomplete. | No public campaign/referral activity. |
| `PENDING_REVIEW` | Setup is complete enough for operator review. | Read-only preview and validation only. |
| `READY_FOR_CAMPAIGN_SETUP` | Account and tenant mapping are active. | Campaign draft/setup can begin. |
| `ACTIVE` | Account can operate Referral SaaS campaigns. | Campaign, referral, progress, and attribution flows allowed by role. |
| `SUSPENDED` | Temporary block on external writes. | Authorized operators may inspect; external writes rejected. |
| `DISABLED` | Account cannot operate. | Normal access blocked. |
| `ARCHIVED` | Retained for history. | No new activity. |

State rules:

- `DRAFT -> PENDING_REVIEW` requires account profile, tenant link, and external
  reference draft evidence.
- `PENDING_REVIEW -> READY_FOR_CAMPAIGN_SETUP` requires operator approval or a
  future automated readiness gate.
- `READY_FOR_CAMPAIGN_SETUP -> ACTIVE` requires at least one ready campaign
  setup path.
- `ACTIVE -> SUSPENDED` and `SUSPENDED -> ACTIVE` require explicit actor,
  reason, and audit evidence.
- `DISABLED` and `ARCHIVED` must not authorize new external referral,
  campaign, progress, or attribution writes.

## Minimum API Contract Direction

Future Referral SaaS account setup APIs should be versioned or product-scoped
wrappers. They should not mutate existing tenant service behavior invisibly.

Candidate future route family:

| Route | Purpose | Auth |
| --- | --- | --- |
| `POST /referral-saas/accounts` | Create account setup draft. | Admin/operator initially. |
| `GET /referral-saas/accounts/{account_ref}` | Read account setup projection. | Account member or admin/operator. |
| `POST /referral-saas/accounts/{account_ref}/tenant-link` | Link account to existing or newly created internal tenant. | Admin/operator. |
| `POST /referral-saas/accounts/{account_ref}/external-refs` | Register external tenant reference. | Admin/operator. |
| `POST /referral-saas/accounts/{account_ref}/memberships` | Invite or activate setup member. | Admin/operator initially. |
| `GET /referral-saas/accounts/{account_ref}/setup-readiness` | Read checklist and blockers. | Account member or admin/operator. |
| `POST /referral-saas/accounts/{account_ref}/submit-for-review` | Submit setup for review. | Account owner/admin or operator. |
| `POST /referral-saas/accounts/{account_ref}/activate` | Activate account for campaign setup. | Admin/operator. |

These are contract candidates only. A later implementation task must decide
whether the route prefix belongs under `/admin`, `/v1`, or a product-specific
namespace.

## Required Response Shape

Future account setup read responses should separate public/account-facing data
from internal runtime evidence.

Recommended shape:

```json
{
  "account_ref": "acct_...",
  "account_name": "Example Co",
  "account_status": "READY_FOR_CAMPAIGN_SETUP",
  "setup_checklist": [
    {
      "code": "TENANT_LINK_ACTIVE",
      "status": "READY",
      "severity": "BLOCKER",
      "message": "Internal tenant link is active."
    }
  ],
  "external_refs": [
    {
      "ref_type": "external_tenant_ref",
      "external_ref": "org_...",
      "status": "ACTIVE"
    }
  ],
  "permissions": {
    "can_configure_campaigns": true,
    "can_issue_referral_codes": true,
    "can_ingest_progress_events": true,
    "can_view_attribution": true
  },
  "internal": {
    "tenant_code": "REDACT_OR_OMIT_FOR_NON_OPERATOR"
  }
}
```

Rules:

- Non-operator responses should omit or redact internal `tenant_code`.
- Operator responses may include `tenant_code` only when permission allows it.
- Safe errors should avoid exposing whether another tenant owns an external
  reference unless caller has admin/operator scope.
- Responses must distinguish setup blockers from warnings.

## Idempotency And Audit Expectations

Future write commands must define idempotency behavior before implementation.

Required idempotent commands:

- account setup draft create
- tenant link create
- external reference register
- external reference rotate
- membership invite/activate
- submit for review
- activate/suspend/disable/archive

Audit evidence must capture:

- actor identity and role
- account reference
- resolved tenant code where available
- external reference where supplied
- command name
- idempotency key or hashed idempotency reference
- previous state and next state
- reason where state changes affect access
- correlation ID
- timestamp

No account setup command may create referral, campaign, reward, funding,
fulfilment, settlement, webhook, or money movement side effects.

## Permission Expectations

Initial implementation should be admin/operator controlled.

Future account-member permissions may be introduced after membership model
implementation. Until then:

- Admin/operator can create and inspect account setup records.
- Tenant/account users cannot self-authorize access by supplying
  `external_tenant_ref`.
- Partner/producer/distributor/consumer keys must not gain access to account
  setup routes without explicit membership and route authorization.
- Existing tenant-scoped referral, progress, campaign, and attribution services
  continue to receive internal `tenant_code` only after boundary resolution.

TASK-166 implementation note: report and export-validation account-scope
envelopes can now carry trusted `account_ref` and `external_tenant_ref` values
from authenticated identity/JWT claims. This is a bridge only. It does not add
account setup tables, tenant-link persistence, membership authorization,
disabled/suspended reference behavior, or caller-supplied account-reference
lookup.

## Validation And Test Expectations

Future implementation tasks should add tests in this order:

1. Contract tests for account setup response shape and safe redaction.
2. External reference uniqueness and disabled/suspended behavior.
3. Tenant link active/suspended/disabled behavior.
4. Membership authorization and adjacent-role rejection.
5. Setup checklist blocker/warning/readiness tests.
6. Idempotency replay and conflict tests for each write command.
7. Audit evidence tests for state transitions.
8. Regression tests proving existing tenant-code referral/campaign/progress
   flows still work.
9. Live DB/state checklist for `tenants`, future account tables, external refs,
   memberships, and route smoke tests.

## Implementation Slices

Recommended future task slices:

1. Schema contract final review for Referral SaaS account setup.
2. Add additive account setup tables and migration replay tests.
3. Add account setup repository/service primitives.
4. Add external reference resolver primitives.
5. Add setup readiness projection service.
6. Add guarded admin/operator account setup APIs.
7. Extend session/account context only after membership rules are tested.
8. Add frontend setup checklist workflow.

Do not combine these with campaign setup implementation. Campaign setup starts
after the account setup contract is stable enough to supply account and tenant
context.

## Explicit Non-Goals

This contract does not implement:

- database schema
- account service
- membership service
- external reference resolver
- route handlers
- frontend setup UI
- SaaS billing
- usage metering beyond basic future plan/limit gates
- funding, fulfilment, settlement, wallets, commissions, or sponsor billing
- white-label/embed
- live onboarding automation
- campaign creation changes
- referral code changes
- progress API changes
- attribution trace changes

## Readiness Decision

Referral SaaS account setup can proceed to implementation planning after this
contract, but the first implementation task should remain additive and narrow:
schema/repository/service foundations only, with no changes to current
referral, campaign, progress, or attribution behavior.

