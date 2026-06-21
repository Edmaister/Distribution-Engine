# Tenant Account Lifecycle Membership Model

Status: Accepted for TASK-005 on 2026-06-21.

## Purpose

TASK-005 defines the reviewable account, organisation, tenant lifecycle, membership, seat, and external-reference mapping model needed before implementation.

This is a design document only. It does not authorize schema migrations, service changes, route changes, permission changes, or tenant-code renames.

## Source Documents

- `docs/sa/TENANT_IDENTIFIER_BOUNDARY_DECISION.md`
- `docs/sa/TENANT_ACCOUNT_BOUNDARY_MAP.md`
- `docs/product/DLAAS_TARGET_STATE.md`
- `docs/sa/API_SURFACE_MAP.md`
- `docs/sa/CURRENT_STATE_MAP.md`
- `docs/sa/CAPABILITY_GAP_MATRIX.md`
- `docs/API_PERMISSION_MATRIX.md`
- `dp/migrations/031_tenent.sql`
- `services/tenant_service.py`
- `apps/api/routers/admin_tenants.py`
- `utils/security.py`
- `utils/permissions.py`
- `apps/api/routers/session.py`

## Current Facts

The current platform has a `tenants` table keyed by `tenant_code`. That value is the internal runtime tenant identifier and must remain compatible with existing migrations, services, routes, tests, audit, funding, fulfilment, settlement, reporting, and data-isolation behavior.

The current auth layer resolves identities with `role`, `tenant_code`, and role-specific claims such as producer or distributor codes. `utils/permissions.py` enforces tenant scope by comparing identity claims to requested tenant scope. `docs/API_PERMISSION_MATRIX.md` describes current role families and requires tenant scope to come from resolved identity unless a route is explicitly admin/operator scoped.

No first-class SaaS account, organisation account, user, account membership, tenant membership, seat, tenant lifecycle, subscription, or external-reference mapping table exists today.

## Design Principles

- Add account and membership primitives around current tenant scope; do not replace `tenant_code`.
- Keep `tenant_code` as the internal service and database partition key.
- Resolve external references and account membership before service calls receive `tenant_code`.
- Preserve role-scoped helpers and tenant isolation while adding durable membership evidence.
- Make lifecycle transitions explicit, auditable, and idempotent.
- Keep sponsor billing and SaaS account billing separate.
- Split implementation into small migrations, services, route contracts, and tests.

## Target Entities

### Account

An account is the commercial SaaS owner relationship. It owns lifecycle, onboarding, billing-plan readiness, seats, memberships, support context, and one or more tenant links.

Recommended future table: `platform_accounts`.

Key fields:

| Field | Purpose |
| --- | --- |
| `account_id` | UUID primary key. |
| `account_code` | Internal stable account code for operator use. |
| `account_name` | Display name. |
| `account_type` | Organisation, producer, partner, distributor, sponsor, operator, or mixed account classification. |
| `status` | Account lifecycle status. |
| `onboarding_status` | Setup progress independent from runtime tenant status. |
| `primary_external_tenant_ref` | Optional external SaaS-facing reference. |
| `created_at`, `updated_at` | Audit timestamps. |
| `created_by`, `updated_by` | Actor references where available. |

### Organisation

An organisation represents a legal or operating entity attached to an account. It lets the platform distinguish commercial account ownership from role-specific participants.

Recommended future table: `platform_organisations`.

Key fields:

| Field | Purpose |
| --- | --- |
| `organisation_id` | UUID primary key. |
| `account_id` | Owning account. |
| `organisation_ref` | External organisation reference. |
| `organisation_name` | Display/legal name. |
| `organisation_type` | Producer, partner, distributor, sponsor, customer-organisation, or platform operator. |
| `status` | Active, suspended, disabled, archived. |
| `created_at`, `updated_at` | Audit timestamps. |

### Tenant Link

The tenant link connects a SaaS account to the existing internal `tenants.tenant_code` row. This is the additive compatibility bridge.

Recommended future table: `platform_account_tenants`.

Key fields:

| Field | Purpose |
| --- | --- |
| `account_tenant_id` | UUID primary key. |
| `account_id` | Owning account. |
| `tenant_code` | Existing internal tenant identifier; references `tenants(tenant_code)`. |
| `relationship_type` | Owner, operator, reseller, sponsor, integration, or support. |
| `is_primary` | Marks default tenant for account-scoped operations. |
| `status` | Pending, active, suspended, disabled, archived. |
| `created_at`, `updated_at` | Audit timestamps. |

Uniqueness requirements:

- Unique `tenant_code` for primary owner relationship.
- Unique `(account_id, tenant_code, relationship_type)` for repeat-safe linking.
- At most one primary tenant per account unless a later multi-environment design explicitly allows more.

### External Reference Mapping

External references map partner/public identifiers into account and tenant context before service execution.

Recommended future table: `platform_external_tenant_refs`.

Key fields:

| Field | Purpose |
| --- | --- |
| `external_ref_id` | UUID primary key. |
| `account_id` | Owning account. |
| `tenant_code` | Resolved internal tenant scope. |
| `ref_type` | `external_tenant_ref`, `organisation_ref`, `producer_ref`, `partner_ref`, `distributor_ref`, or future role alias. |
| `external_ref` | External value. |
| `status` | Pending, active, suspended, disabled, archived, rotated. |
| `source_system` | Optional issuer/source context. |
| `valid_from`, `valid_until` | Reference lifetime for rotation and migration. |
| `created_at`, `updated_at`, `rotated_at` | Audit timestamps. |

Uniqueness requirements:

- Active references must be unique by `(ref_type, external_ref)`.
- A reference must resolve to exactly one active `tenant_code` at request time.
- Rotated or archived references may remain for audit but must not authorize new requests.

### User

A platform user represents a human actor independently from a tenant-scoped role claim.

Recommended future table: `platform_users`.

Key fields:

| Field | Purpose |
| --- | --- |
| `user_id` | UUID primary key. |
| `subject` | Stable identity-provider subject or internal user subject. |
| `email_hash` | Optional privacy-safe lookup value. |
| `display_name` | Display name where allowed. |
| `status` | Invited, active, suspended, disabled, archived. |
| `created_at`, `updated_at`, `last_seen_at` | Audit timestamps. |

Do not store unnecessary personal data in this table. Any email or identity metadata must follow existing privacy and audit rules.

### Membership

Membership binds a user or integration actor to an account and optionally to a tenant.

Recommended future table: `platform_memberships`.

Key fields:

| Field | Purpose |
| --- | --- |
| `membership_id` | UUID primary key. |
| `account_id` | Account scope. |
| `tenant_code` | Optional internal tenant scope for tenant-specific membership. |
| `user_id` | Optional user actor. |
| `client_id` | Optional integration actor for partner/client credentials. |
| `role_family` | Platform Admin, System Admin, Finance Admin, Distribution Admin, Partner, Producer, Distributor, Consumer, or future role. |
| `permission_set` | Named permission bundle or policy reference. |
| `status` | Invited, active, suspended, disabled, archived. |
| `seat_id` | Optional assigned seat. |
| `created_at`, `updated_at`, `invited_at`, `accepted_at`, `disabled_at` | Lifecycle timestamps. |

Uniqueness requirements:

- Prevent duplicate active membership for the same actor, account, tenant, and role family.
- A suspended or disabled membership must not authorize tenant-scoped access.
- Admin/operator memberships must still respect the API permission matrix and route-specific helper rules.

### Seat

Seats represent SaaS packaging entitlement, not runtime tenant isolation.

Recommended future table: `platform_seats`.

Key fields:

| Field | Purpose |
| --- | --- |
| `seat_id` | UUID primary key. |
| `account_id` | Owning account. |
| `seat_type` | Admin, operator, partner, producer, distributor, consumer, or support. |
| `status` | Available, assigned, suspended, disabled, archived. |
| `assigned_membership_id` | Optional membership assignment. |
| `created_at`, `updated_at` | Audit timestamps. |

Seats should not be reused as permission checks. Permission checks should evaluate membership and role policy; seats only prove commercial entitlement.

## Lifecycle States

Account status:

- `PENDING_ONBOARDING`: account created but setup not complete.
- `ACTIVE`: account can operate according to memberships and entitlements.
- `SUSPENDED`: temporary block; existing data remains readable by authorized operators, but external write operations should be rejected.
- `DISABLED`: account is blocked from normal access and external resolution.
- `ARCHIVED`: retained for audit/history; no new activity.

Tenant link status:

- `PENDING_SETUP`: tenant link exists but runtime setup is incomplete.
- `ACTIVE`: tenant can be resolved and used internally.
- `SUSPENDED`: tenant is temporarily blocked for external writes.
- `DISABLED`: tenant is not available for normal access.
- `ARCHIVED`: retained for audit/history.

External reference status:

- `PENDING`: reserved but not yet usable.
- `ACTIVE`: can resolve to internal tenant scope.
- `SUSPENDED`: temporarily blocked.
- `DISABLED`: cannot authorize or resolve new requests.
- `ROTATED`: preserved for audit or migration but not active.
- `ARCHIVED`: retained only for history.

Membership status:

- `INVITED`: pending acceptance or activation.
- `ACTIVE`: can authorize according to role and tenant scope.
- `SUSPENDED`: temporarily blocked.
- `DISABLED`: cannot authorize.
- `ARCHIVED`: retained only for history.

Seat status:

- `AVAILABLE`: unassigned entitlement.
- `ASSIGNED`: bound to an active or pending membership.
- `SUSPENDED`: temporarily unusable.
- `DISABLED`: unusable.
- `ARCHIVED`: retained only for history.

## Lifecycle Transition Rules

Account and tenant lifecycle changes must be explicit commands, not implicit updates hidden inside unrelated business flows.

Required command behavior:

- Require an authorized admin/operator actor.
- Validate current state before transition.
- Reject invalid transitions with 409 conflict.
- Use idempotency keys for create, invite, link, external-ref registration, rotation, suspension, and activation commands.
- Write audit evidence with actor, account, tenant, previous state, next state, reason, and correlation/idempotency context.
- Never cascade-destruct tenant operational data.

Suggested transition constraints:

| From | Allowed to | Notes |
| --- | --- | --- |
| Pending/invited/setup | Active, disabled, archived | Activation requires required setup fields. |
| Active | Suspended, disabled, archived | Archive should require no active externally visible operations. |
| Suspended | Active, disabled, archived | Resume must be explicit and audited. |
| Disabled | Archived | Re-enable should require a separate reviewed policy if allowed later. |
| Rotated external ref | Archived | Rotated refs cannot become active again without a new record. |

## Service Boundaries

Future service changes should be split into small implementation tasks.

Recommended services:

| Service | Responsibility |
| --- | --- |
| `account_service` | Create/read/update accounts, account lifecycle commands, account audit context. |
| `tenant_lifecycle_service` | Link accounts to `tenant_code`, manage tenant link lifecycle, validate setup readiness. |
| `external_tenant_ref_service` | Register, resolve, rotate, suspend, disable, and audit external references. |
| `membership_service` | Invite, activate, suspend, disable, and list account or tenant memberships. |
| `seat_service` | Track seat availability and assignment without enforcing permissions directly. |
| `tenant_identity_resolver` | Resolve credential or external reference to account, tenant, membership, and internal `tenant_code`. |

Existing `tenant_service.py` should remain the compatibility service for current `tenants` records until implementation tasks deliberately extend or wrap it.

## API Contract Direction

Future account/tenant APIs must be admin/operator controlled until public onboarding is explicitly designed.

Recommended route families:

| Route family | Purpose | Auth expectation |
| --- | --- | --- |
| `/admin/accounts` | Account create/read/lifecycle operations. | Platform/System admin initially; narrower roles may be designed later. |
| `/admin/accounts/{account_id}/tenants` | Link accounts to internal tenants and inspect setup state. | Platform/System admin; audit required. |
| `/admin/accounts/{account_id}/memberships` | Invite/list/update memberships. | Platform/System admin or future account owner role. |
| `/admin/accounts/{account_id}/external-refs` | Register, rotate, suspend, and disable external references. | Platform/System admin; audit and idempotency required. |
| `/auth/session` extension | Include resolved account/membership/tenant context after implementation. | Existing session auth helpers; no unauthenticated account data. |

Required response and error behavior:

- `400` for malformed input.
- `401` for missing/invalid credential.
- `403` for valid credential without required role or membership.
- `404` for inaccessible or absent account, tenant, membership, or reference.
- `409` for duplicate active references, invalid lifecycle transitions, or seat conflicts.
- `422` for schema validation errors where framework validation applies.

## Permission Model

The current API permission matrix remains valid until implementation expands it.

Future authorization should evaluate:

```text
credential/JWT/API key
  -> identity role and claims
  -> account membership status
  -> tenant link status
  -> external reference status where applicable
  -> route-specific role helper and permission set
  -> resolved internal tenant_code
```

Rules:

- A valid credential is not enough if membership is suspended, disabled, or archived.
- A valid external reference is not enough if the account or tenant link is suspended, disabled, or archived.
- Cross-tenant admin/operator actions must remain explicit and audited.
- Tenant-bound partner, producer, distributor, and consumer access must continue rejecting cross-tenant reads and writes.
- Finance, fulfilment, settlement, funding, and audit routes must not infer tenant scope from caller input unless the route is explicitly admin-scoped and audited.

## Migration Plan For Later Implementation

The first implementation migration should be additive:

1. Create account, organisation, tenant-link, external-reference, user, membership, and seat tables with indexes and constraints.
2. Reference existing `tenants(tenant_code)` from tenant-link and external-reference tables.
3. Do not rename or drop existing `tenant_code` columns.
4. Backfill a minimal internal account and tenant link for existing tenants only if required by implementation tests.
5. Keep migration replay idempotent and clean-DB safe.
6. Add migration tests before adding route behavior.

Implementation should be split if it cannot remain reviewable:

- schema-only migration and replay tests
- service create/read/lifecycle tests
- external-reference resolver tests
- membership and permission tests
- admin API contract tests
- session payload extension tests

## Test Plan For Implementation Tasks

Required future tests:

- clean DB migration replay
- account create/idempotency/duplicate tests
- tenant link create/duplicate/status tests
- external reference uniqueness, rotation, disabled, suspended, archived tests
- membership invite/activate/suspend/disable tests
- seat assign/release/conflict tests
- account-member permission tests
- tenant isolation and cross-tenant denial tests
- session context tests
- audit evidence tests for lifecycle and membership changes
- regression tests proving existing `tenant_code` routes continue to work

## Non-Goals

TASK-005 does not implement schema, services, routes, or tests.

TASK-005 does not start TASK-006 campaign lifecycle work.

TASK-005 does not design SaaS usage metering, platform billing, white-label, or public onboarding beyond the account/membership primitives needed to support them later.

TASK-005 does not rename existing `tenant_code` columns or replace existing auth helpers.

## Readiness For Next Tasks

TASK-005 gives implementation tasks a bounded model for account lifecycle, memberships, seats, external references, and compatibility with `tenant_code`.

TASK-006 remains a separate campaign/opportunity lifecycle mapping task and must not be combined with account lifecycle implementation.
