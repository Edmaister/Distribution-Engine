# DLaaS Product Brief

## Purpose

Distribution Layer as a Service is the broader target platform direction. It
extends beyond referral management into a reusable multi-tenant platform for
configuring, launching, tracking, rewarding, funding, fulfilling, settling, and
analyzing distribution, referral, and partner campaigns.

The canonical target-state source remains:

- `docs/product/DLAAS_TARGET_STATE.md`

## Product Boundary

DLaaS includes the complete platform surface:

- account and tenant model
- campaign model
- participant model across referrers, distributors, partners, sponsors, and
  customers
- distribution links/codes
- attribution tracking
- event ingestion
- qualification rules
- reward and commission rules
- funding and budget tracking
- fulfilment and settlement
- audit trail
- public/internal APIs
- webhooks
- operator control plane
- partner/customer portal
- analytics/reporting
- SaaS packaging
- white-label/embed readiness

## Current Relationship To Referral SaaS

Referral Management and Campaign Attribution SaaS is the first productized
wedge. It should supply hardened primitives that DLaaS can reuse later, but it
must not be forced to carry all DLaaS scope before launch.

Shared implementation primitives should remain single-source. DLaaS expansion
should reuse and extend them rather than copying referral SaaS code.

## DLaaS Readiness Constraints

DLaaS should not be called production-complete until the gap matrix blockers are
closed, especially:

- full SaaS account/user/membership/seat model
- canonical distribution outcome spine
- platform-wide audit taxonomy
- platform-wide idempotency/retry behavior
- stable public DLaaS APIs
- SaaS usage metering and billing boundaries
- live DB/state verification
- full end-to-end DLaaS golden paths

