# Roadmap Documentation Boundaries

This folder contains the global ordered task list and product-specific roadmap
views.

## Product Roadmap Folders

- `referral-saas/` - roadmap for Referral Management and Campaign Attribution
  SaaS.
- `dlaas/` - roadmap for broader DLaaS expansion.

## Source Of Truth

`docs/roadmap/ORDERED_TASK_LIST.md` remains the ordered task source of truth
until the project explicitly adopts separate task queues.

Product roadmap files should classify and package work; they should not invent
implemented fields, statuses, schemas, APIs, or task completion.

## Task Boundary Gate

Every roadmap task must identify its product boundary before implementation:

- `Referral SaaS`
- `DLaaS`
- `Shared Platform`

Use `docs/roadmap/TASK_TEMPLATE.md` for new tasks.

## Routing Rules

Classify as `Referral SaaS` first when the work is primarily about:

- referral code issue, validation, terms, alias, QR scan, or lifecycle
- referral progress and journey checks
- campaign setup, campaign readiness, campaign policy, or campaign track
- campaign attribution, attribution trace, link/code inspection, or referral
  SaaS reporting
- referrer/customer-safe SaaS UX

Classify as `DLaaS` when the work is primarily about:

- distributor marketplace expansion
- commissions
- funding accounts, reservations, exposure, or budget governance
- fulfilment providers
- settlement batches, exceptions, reversals, or certifications
- sponsor billing
- platform SaaS billing and advanced usage metering
- white-label/embed
- broad DLaaS public API expansion beyond the referral SaaS wedge

Classify as `Shared Platform` when the work changes primitives used by both:

- tenant/account boundaries
- auth, RBAC, permissions, API credentials
- audit taxonomy
- idempotency and retry standards
- event contracts and observability
- live DB/state verification
- shared frontend components or API client infrastructure

Source duplication is not allowed as a task strategy. If product-specific
behavior is needed, add a product layer, adapter, route, UI surface, test suite,
or documentation boundary around shared primitives.
