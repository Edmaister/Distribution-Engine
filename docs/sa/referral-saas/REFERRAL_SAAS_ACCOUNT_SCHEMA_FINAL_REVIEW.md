# Referral SaaS Account Schema Final Review

Status: Accepted for TASK-197 on 2026-07-15.

Product boundary: Referral SaaS.

Required boundary docs checked:

- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/referral-saas/ROADMAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_MAINTENANCE_WORKFLOW_ARCHITECTURE.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_WRAPPER_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_MAINTENANCE_READ_MODEL_CONTRACT.md`
- `docs/sa/TENANT_ACCOUNT_BOUNDARY_MAP.md`
- `docs/sa/TENANT_ACCOUNT_LIFECYCLE_MEMBERSHIP_MODEL.md`
- `docs/sa/TENANT_IDENTIFIER_BOUNDARY_DECISION.md`

## Purpose

TASK-197 is the final review gate before adding durable account primitives for
Referral SaaS account setup and account maintenance.

The review confirms what exists, what remains missing, and what the next
additive schema task may implement. It does not create schema, routes, services,
frontend behavior, account lifecycle commands, membership writes, invitations,
reference rotation, credential lifecycle, campaign activation, go-live actions,
money movement, or broad DLaaS behavior.

## Current Facts

`tenant_code` is the current internal platform tenant identifier. It is created
by `dp/migrations/031_tenent.sql` through the `tenants` table and is already
used by referral, campaign, reward, funding, fulfilment, settlement, audit,
reporting, permissions, and background-processing paths.

`tenant_code` remains an internal partition key. It must not become the primary
external product identifier for Referral SaaS setup, maintenance, public APIs,
partner integrations, webhooks, links, or tenant-facing reports.

The current admin tenant route and service are internal platform primitives:

- `services/tenant_service.py`
- `apps/api/routers/admin_tenants.py`

Onboarding draft persistence exists through
`dp/migrations/080_onboarding_draft_persistence.sql`. It stores safe setup
intent and validation evidence using external references such as
`external_tenant_ref`, `organisation_ref`, `producer_ref`, `sponsor_ref`,
`distributor_ref`, `campaign_code`, and `opportunity_ref`.

Onboarding drafts are not durable SaaS accounts. They are setup evidence until
the account, tenant-link, external-reference, membership, lifecycle, and audit
primitives exist.

Account Setup and Account Maintenance are now separate Referral SaaS workflows:

- Account Setup captures and validates setup evidence.
- Account Setup Readiness is a checkpoint inside setup.
- Account Maintenance is currently read-only and uses safe onboarding/readiness
  evidence until durable account primitives exist.

## Missing Durable Primitives

The current system still lacks these launch-critical primitives:

- durable account record
- account-to-tenant link
- external-reference mapping and resolver persistence
- account membership and role assignment persistence
- invitation and activation lifecycle
- account lifecycle and maintenance command audit timeline
- product account API wrappers that hide internal tenant identifiers
- account maintenance commands for safe, scoped changes

These gaps block a real 10/10 Account Setup and Account Maintenance workflow.
They should be solved before promising production-grade account maintenance,
membership management, reference rotation, credential lifecycle, go-live, or
campaign activation from the Referral SaaS workspace.

## Approved Additive Schema Direction

The next schema task may add an account foundation above the existing tenant
layer. It must be additive and must preserve current tenant-scoped behavior.

Approved table families for the next implementation slice:

1. Account and organisation ownership records.
2. Account-to-tenant links that reference existing `tenants(tenant_code)`.
3. External-reference mappings that resolve active external references to an
   account and internal tenant scope.
4. Account membership records for user or actor access to accounts and linked
   tenant scope.
5. Lifecycle or audit records for account, link, reference, and membership
   changes.

The next task may choose exact table and column names, but it must stay aligned
with the existing account boundary docs and must not introduce broad DLaaS
marketplace, billing, funding, fulfilment, settlement, wallet, commission, or
invoice behavior.

## Required Schema Guardrails

The account foundation migration must:

- be additive and clean-DB replay safe
- avoid renaming, dropping, or replacing existing `tenant_code` columns
- reference `tenants(tenant_code)` from tenant-link and external-reference
  tables where tenant scope is needed
- keep `tenant_code` internal to platform/service execution
- expose external references as the product-facing account and organisation
  selectors
- support active, suspended, disabled, archived, and pending-style states where
  lifecycle behavior is needed
- include uniqueness rules for active external references
- prevent duplicate active account-to-tenant links for the same tenant scope
- keep onboarding drafts as setup evidence, not account records
- avoid backfills unless implementation tests prove they are necessary
- avoid route, service, and frontend behavior in the same migration task unless
  a later task explicitly approves a narrow wrapper

## Required Test Gates For The Next Implementation Slice

Before product behavior depends on the account foundation, tests must prove:

- clean DB migration replay succeeds
- existing `tenant_code` routes and services remain compatible
- external references cannot resolve to multiple active tenant scopes
- disabled, suspended, archived, and missing references are rejected safely
- account-to-tenant link uniqueness is enforced
- membership status and role checks can be represented without caller-supplied
  internal tenant identifiers
- no product response leaks raw `tenant_code`, secrets, raw payloads, or money
  evidence
- Account Setup and Account Maintenance remain bounded to Referral SaaS scope

## Non-Goals For TASK-197

TASK-197 does not add schema, migrations, routes, services, frontend changes,
OpenAPI output, permission changes, durable account creation, tenant creation,
tenant-link persistence, external-reference resolver persistence, membership
writes, invitations, account lifecycle commands, account maintenance commands,
reference rotation, credential lifecycle, campaign activation, go-live actions,
repair, replay, retry, support-case writes, reward application, reward
fulfilment, funding, settlement, commissions, wallet behavior, invoice behavior,
sponsor billing, marketplace expansion, white-label/embed, SaaS billing, source
forks, or broad DLaaS behavior.

## Decision

Proceed to the next task as an additive account foundation migration and
contract-test slice. That task should implement only the durable account,
tenant-link, external-reference, membership, and lifecycle/audit schema needed
to stop relying on onboarding drafts as the account selector.

Routes, account creation commands, maintenance commands, membership write flows,
reference rotation, credential lifecycle, campaign activation, go-live actions,
and frontend command UX must remain separate follow-up tasks.
