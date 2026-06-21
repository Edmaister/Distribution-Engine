# Tenant Account Boundary Map

Status: Accepted for TASK-004 on 2026-06-21.

## Purpose

TASK-004 maps the current `tenant_code` dependencies and defines the account-to-tenant boundary needed before account, membership, lifecycle, and SaaS packaging work begins.

This document does not introduce schema, API, migration, or service changes. It records the target boundary that future implementation tasks must preserve.

## Source Documents

- `docs/sa/TENANT_IDENTIFIER_BOUNDARY_DECISION.md`
- `docs/product/DLAAS_TARGET_STATE.md`
- `docs/sa/API_SURFACE_MAP.md`
- `docs/sa/CURRENT_STATE_MAP.md`
- `docs/sa/CAPABILITY_GAP_MATRIX.md`
- `docs/roadmap/ORDERED_TASK_LIST.md`
- `dp/migrations/031_tenent.sql`
- `services/tenant_service.py`
- `apps/api/routers/admin_tenants.py`
- `utils/security.py`
- `utils/permissions.py`
- `utils/tenant_guard.py`

## Current Facts

`tenant_code` is the current internal platform tenant identifier.

The current schema has a `tenants` table created by `dp/migrations/031_tenent.sql` with `tenant_code` as the primary key. The same migration adds `tenant_code` to `referral_instances`, backfills legacy rows to `FNB`, makes the column non-null, and adds a `(tenant_code, referral_track_id)` index.

`services/tenant_service.py` provides tenant create/read behavior around the current `tenants` table. `apps/api/routers/admin_tenants.py` exposes internal admin tenant create/read operations using `tenant_code`.

`utils/security.py` includes `tenant_code` in authenticated identity claims and supports claim resolution from `tenant_code` or `tenant`. `utils/permissions.py` enforces tenant-scoped access by comparing identity tenant claims with requested tenant scope. `utils/tenant_guard.py` validates tenant existence and activity before scoped execution.

Static source search found `tenant_code` in migrations, services, routers, utilities, and tests across referrals, campaign policy, rewards, missions, badges, leaderboards, funding, fulfilment, settlement, distribution, partner seam, privacy, reporting, audit, and role-specific experience APIs. That makes `tenant_code` a platform isolation key, not an external integration contract.

No first-class SaaS account, organisation account, user membership, seat ownership, tenant lifecycle, subscription, or external-reference mapping schema is currently implemented.

## Boundary Decision

TASK-048 decides that `tenant_code` remains internal. External parties must not depend on it as the primary integration identifier.

External-facing identifiers map into internal `tenant_code` before service execution:

```text
external_tenant_ref
organisation_ref / producer_ref / partner_ref / distributor_ref
  -> account and tenant identity layer
  -> internal tenant_code
  -> existing services, schema, audit, funding, fulfilment, settlement, and reporting
```

Existing routes, tests, and services that expose or accept `tenant_code` remain current implementation facts and backward-compatible surfaces. Future public DLaaS APIs should prefer credential-derived tenant scope or external references.

## Target Boundary Terms

Account: The commercial SaaS owner relationship. An account may own or administer one or more tenants. Account is the future boundary for subscription, billing plan, seats, lifecycle, commercial ownership, and SaaS setup.

Tenant: The internal runtime partition represented by `tenant_code`. A tenant scopes referrals, campaigns, policies, rewards, funding, fulfilment, settlement, reporting, audit, workers, and operator controls.

Membership: The future relationship between a user or actor and an account or tenant. Membership must carry role, permission, status, lifecycle, and audit context.

External tenant reference: The external integration identifier, generically `external_tenant_ref`, with role-specific aliases such as `organisation_ref`, `producer_ref`, `partner_ref`, and `distributor_ref`.

Tenant lifecycle: The future controlled state model for tenant setup and operation, including states such as pending onboarding, active, suspended, disabled, and archived. TASK-005 must define the exact schema and state transitions.

## Current Tenant Reference Inventory

Tenant core and auth:

- `tenants` is the current internal tenant registry.
- `tenant_service.py` is the current tenant service boundary.
- `/admin/tenants` is an internal admin-facing current route.
- Auth identity includes `tenant_code`; permission checks enforce tenant scope from identity claims.

Referrals, attribution, and events:

- `referral_instances` is tenant-scoped by `tenant_code`.
- Progress, worker, bootstrap, referral, and enterprise event flows use tenant scope before writing or reading referral state.
- Future public event APIs should resolve external tenant references or credential-derived scope to `tenant_code` before calling current services.

Campaigns and policies:

- Campaign and policy services/routes use tenant scope as an internal partition.
- Campaign attribution, QR/link flows, onboarding, and partner-facing campaign APIs should use external references or resolved scope at the edge, then use `tenant_code` internally.

Rewards, missions, badges, and leaderboards:

- Reward, mission, badge, leaderboard, and summary paths use tenant scope directly or indirectly through referral and campaign state.
- Future account or organisation packaging must not change reward semantics by replacing internal `tenant_code` filters.

Funding, budget, and reconciliation:

- Funding accounts, rules, transactions, reservations, limits, exposure, alerts, reconciliation, sponsor wallets, allocations, contracts, and budget governance use tenant scope.
- These money domains must continue receiving resolved `tenant_code` plus actor context for isolation, auditability, idempotency, and reconciliation.

Fulfilment and settlement:

- Fulfilment audit, fulfilment policies, settlement ledger, batches, items, approvals, exceptions, reversals, periods, and certifications use tenant scope.
- Account membership work must preserve tenant-safe settlement and fulfilment filtering.

Distribution marketplace:

- Distributor, wallet, commission, opportunity, offer route, governance, reporting, and route referral link flows use tenant context.
- Distributor-facing APIs should use `distributor_ref` or credential-derived scope externally, then resolve to internal tenant and distributor records.

Partner seam and webhooks:

- Partner clients, access tokens, webhook subscriptions, deliveries, alert notifications, retries, and dead-letter handling require tenant context.
- Webhook payloads should expose external references where receivers need tenant or participant context; internal delivery workers can continue writing resolved `tenant_code`.

Privacy, reporting, and audit:

- Privacy flows, reporting APIs, dashboards, finance metrics, admin audit, processing audit, fulfilment audit, and governance audit depend on tenant isolation.
- Tenant-facing exports should prefer external references; operator-scoped reports may include `tenant_code`.

## Account-To-Tenant Boundary

Future account work should add an account layer above the current tenant layer. The account layer owns commercial relationship, membership, lifecycle, plan, subscription, onboarding, and external references. The tenant layer continues to own runtime partitioning and operational execution.

Recommended future model:

```text
account
  has many memberships
  has many tenant links
  has lifecycle and SaaS packaging state

tenant
  remains represented internally by tenant_code
  has operational configuration and runtime data scope

external tenant reference mapping
  maps external_tenant_ref or role-specific refs to account and tenant_code
  supports status, rotation, uniqueness, audit timestamps, and source system metadata
```

The account model must not require renaming existing `tenant_code` columns. It should add an explicit mapping layer around them.

## API And Webhook Implications

New public APIs should avoid `tenant_code` as the primary path, query, or payload identifier. They should derive tenant scope from credentials where possible. Where a caller must send tenant context, use `external_tenant_ref` or a role-specific alias.

Internal/admin/operator APIs may continue to use `tenant_code` when the caller is authorised to operate on internal tenant scope.

Service-layer calls should continue receiving resolved `tenant_code`. The boundary translation belongs at authentication, authorization, partner API, webhook, onboarding, QR/link, and external integration edges.

Audit records should capture the resolved internal `tenant_code` and, when present, the external reference used by the caller.

## Funding, Fulfilment, Settlement, Audit, And Reporting Implications

Funding, fulfilment, settlement, audit, and reporting must continue using `tenant_code` for internal isolation and joins. Account and external-reference implementation must be additive and must not remove existing tenant filters.

Money and audit flows should receive:

- authenticated actor identity
- resolved internal `tenant_code`
- external reference context when supplied
- request or idempotency metadata where applicable

## Compatibility

Existing schema, migrations, services, routes, and tests that use `tenant_code` remain compatible.

Existing public-ish or partner-facing routes that currently expose `tenant_code` should be treated as current implementation facts. Future tasks should add versioned wrappers or explicit migration plans instead of renaming current contracts in place.

## Follow-Up Implementation Tasks

TASK-005 should design the schema and service contract for accounts, organisations, tenant lifecycle, memberships, seats, and external-reference mappings.

Future implementation tasks should define:

- external-reference resolver service behavior
- uniqueness and collision rules for external references
- disabled, suspended, archived, and rotated reference handling
- account-member permission checks
- audit evidence for external-to-internal tenant resolution
- API and webhook payload conventions using `external_tenant_ref` and role-specific aliases
- backward-compatible wrappers for routes that currently expose `tenant_code`
- tenant isolation tests for account, membership, and external-reference resolution

TASK-004 does not implement TASK-005 or TASK-006.
