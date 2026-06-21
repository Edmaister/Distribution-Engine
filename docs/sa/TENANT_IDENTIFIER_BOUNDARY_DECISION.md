# Tenant Identifier Boundary Decision

Status: Accepted for TASK-048 (2026-06-21)

## Problem Statement

The current platform uses `tenant_code` across schema, services, routes, tests, audit, funding, fulfilment, settlement, reporting, and permissions. That makes it a reliable internal partition and data-isolation identifier today.

DLaaS target state also needs stable external identifiers for organisations, producers, partners, distributors, sponsors, campaigns, onboarding, webhooks, links, and public APIs. If external parties depend directly on `tenant_code`, the platform loses the ability to change tenant packaging, introduce account hierarchy, rotate partner-facing identifiers, support white-label distribution, or separate SaaS account identity from internal runtime partitioning.

TASK-004 was blocked until the platform decided whether `tenant_code` is an external identifier or an internal one.

## Decision

`tenant_code` remains the internal platform tenant identifier.

External parties must not depend on `tenant_code` as the primary integration identifier. DLaaS will introduce an explicit external identifier boundary for SaaS accounts, organisations, producers, partners, distributors, sponsors, and other participant roles.

The generic external SaaS-facing identifier is `external_tenant_ref`. Role-specific aliases can be used where they make API or domain intent clearer:

- `organisation_ref`
- `producer_ref`
- `partner_ref`
- `distributor_ref`

These external references map to internal `tenant_code`. Internal services continue to use `tenant_code` for partitioning, joins, audit scope, funding, fulfilment, settlement, reporting, and data isolation.

## Internal Identifier

`tenant_code` is the internal platform tenant identifier.

It remains valid for:

- database partitioning and tenant-scoped table columns
- internal service calls
- admin/operator routes
- audit evidence
- funding accounts, limits, reservations, exposure, reconciliation, wallets, and contracts
- reward, fulfilment, settlement, and settlement evidence
- internal reporting and reconciliation
- background workers and internal event routing
- internal permission checks and tenant isolation

`tenant_code` is not the preferred external product identifier for new public APIs, partner integrations, onboarding flows, white-label embeds, QR links, or webhook contracts.

## External Identifier Options

Option 1: expose `tenant_code` externally.

This is rejected. It couples public contracts to internal partitioning and makes future account hierarchy, tenant rename, tenant consolidation, or white-label product packaging risky.

Option 2: replace `tenant_code` everywhere with a public account identifier.

This is rejected for now. The current schema and services already use `tenant_code` heavily across money, audit, fulfilment, settlement, permissions, and reporting. Renaming or replacing it would be high risk and unnecessary for this phase.

Option 3: keep `tenant_code` internal and add an external identifier boundary.

This is selected. It preserves current backend truth while giving DLaaS stable public identifiers and role-specific references.

## Mapping Model

External references map into internal `tenant_code` through a future account/tenant identity layer.

Conceptual mapping:

```text
external_tenant_ref
  -> organisation_ref or producer_ref or partner_ref or distributor_ref
  -> internal tenant_code
```

Rules:

- Each external reference must resolve to exactly one active internal tenant scope at request time.
- Mapping must be tenant-safe, auditable, and permission-checked.
- Mapping must support lifecycle states such as pending onboarding, active, suspended, disabled, and archived when TASK-005 designs tenant lifecycle schema.
- Mapping must support role-specific references without collapsing producers, partners, distributors, sponsors, referrers, and organisations into one premature table.
- Public APIs should accept external references or derive tenant scope from credentials; they should not require callers to know internal `tenant_code`.
- Internal services should receive resolved `tenant_code` plus actor/credential context after authentication and authorization.

## Where External Identifiers Must Be Used

Use `external_tenant_ref` or a role-specific alias in:

- partner/public APIs
- webhook subscription and delivery contracts
- campaign attribution inputs from external systems
- QR links and distribution links that leave the platform boundary
- onboarding and SaaS setup flows
- public credential registration and API-key productization
- white-label or embedded distribution surfaces
- partner, producer, distributor, sponsor, and organisation portals
- tenant-facing analytics/reporting exports where the recipient should not learn internal partition keys

## Where `tenant_code` Must Remain Internal

Continue using `tenant_code` inside:

- current database tables and migrations
- service-layer joins and filters
- internal/admin/operator APIs unless a route is explicitly productized later
- funding, fulfilment, settlement, reward, and audit services
- background workers and event processing
- internal logs, metrics, reconciliation, and support workflows
- tenant isolation checks after external reference resolution

## API And Webhook Implications

New public DLaaS APIs should not expose internal `tenant_code` as the primary path or payload identifier. They should either:

- derive tenant scope from authenticated credentials, or
- accept `external_tenant_ref` or a role-specific reference where the caller must disambiguate scope.

Existing routes that currently expose `tenant_code` remain backward compatible until versioned replacements or wrappers exist. They should be treated as current implementation facts, not the preferred target-state public contract.

Webhook subscription, event payload, and delivery contracts should include external references where the receiver needs tenant or participant context. Internal delivery workers may continue resolving to `tenant_code` before writing inbox, audit, retry, or delivery state.

## Funding, Fulfilment, Settlement, Audit, And Reporting Implications

Money and audit domains keep `tenant_code` as the internal source of tenant isolation.

Funding, fulfilment, settlement, audit, and reporting services must not be refactored away from `tenant_code` as part of the identifier-boundary decision. Future APIs may translate external identifiers to `tenant_code` before calling these services.

Audit records should capture both:

- the resolved internal `tenant_code` used for enforcement and traceability
- the external reference and actor/credential context when the action originated outside the platform boundary

Tenant-facing reporting exports should prefer external references. Internal finance, reconciliation, and support reports may include `tenant_code` where access is operator-scoped.

## Backward Compatibility

Existing `tenant_code` columns, services, tests, routes, seeds, and migrations remain unchanged.

No schema migration is authorized by this decision. No route rename is authorized by this decision. Existing API clients that currently call tenant-code routes continue to work until a future versioned API migration plan exists.

TASK-004 can now map current `tenant_code` usage and design the account-to-tenant boundary using this decision:

- preserve `tenant_code` internally
- introduce external references at the platform boundary
- map external references to `tenant_code` before service execution

## Follow-Up Implementation Tasks

Follow-up work should be split into small reviewable tasks:

- TASK-004: Map all current `tenant_code` dependencies and define the account-to-tenant boundary using this decision.
- TASK-005: Design tenant lifecycle, account/org, membership, seat, and external-reference mapping schema.
- Future task: define the external-reference resolver service contract, including auth, lifecycle, collision, rotation, and audit behavior.
- Future task: update public API design rules and permission matrix to prefer external references or credential-derived scope.
- Future task: design webhook payload tenant-context fields using `external_tenant_ref` and role-specific aliases.
- Future task: define migration/backward-compatibility strategy for current public-ish routes that expose `tenant_code`.
- Future task: add tests for external-reference resolution, tenant isolation, duplicate external refs, disabled mapping behavior, and audit capture.
