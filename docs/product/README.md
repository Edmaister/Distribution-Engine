# Product Documentation Boundaries

This folder separates product documentation by product surface while keeping the
implementation source of truth shared.

## Product Folders

- `referral-saas/` - Referral Management and Campaign Attribution SaaS.
- `dlaas/` - broader Distribution Layer as a Service platform direction.

## Boundary Rule

Do not duplicate backend or frontend source code by product. Shared platform
primitives such as referral codes, progress events, campaign attribution,
campaign readiness, link/code inspection, tenant scope, audit, and idempotency
must remain single-source implementation capabilities.

Product-specific docs should describe packaging, workflows, API contracts,
frontend surfaces, tests, and launch criteria for each product boundary.

## Required Boundary Check

Every task must classify itself before implementation:

- `Referral SaaS` for referral management and campaign attribution SaaS work.
- `DLaaS` for broader distribution-platform expansion.
- `Shared Platform` for primitives used by both.

Boundary docs to read:

- Referral SaaS: `docs/product/referral-saas/PRODUCT_BRIEF.md`
- DLaaS: `docs/product/dlaas/PRODUCT_BRIEF.md` and
  `docs/product/DLAAS_TARGET_STATE.md`
- Shared Platform: this file plus the affected product brief(s)

If a task touches shared referral, campaign, attribution, event, tenant, audit,
or idempotency behavior, it must preserve single-source implementation unless a
specific reviewed task creates a new abstraction.
