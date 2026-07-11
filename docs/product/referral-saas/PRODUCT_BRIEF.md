# Referral Management and Campaign Attribution SaaS Product Brief

## Purpose

Referral Management and Campaign Attribution SaaS is the first productized
commercial wedge. It packages existing referral, campaign, progress, link/code,
and attribution capabilities into a focused SaaS product without forking the
codebase away from future DLaaS expansion.

## Current Code Assessment

The product is not greenfield. The repo already includes:

- Referral code creation, existing-code reuse, preferred handle handling, and
  accepted-terms enforcement in `services/referral_code.py`.
- Referral code validation, alias validation, referral instance creation, QR
  scan evidence, and tenant-scoped validation responses.
- Referee UCN capture with progress-event emission.
- Progress and journey checks in `services/progress_service.py`, including
  required identifiers, product/sub-product binding, journey compatibility,
  self-referral rejection, payload hashing, dedupe keys, and queue emission.
- Campaign create, validation, track update, policy read/write, campaign
  attribution records, and campaign track events.
- Campaign readiness checks in `services/campaign_readiness_service.py`.
- Canonical link/code inspection in `services/link_code_service.py` for
  referral codes, campaign codes, campaign referral links, route referral links,
  and composite-code compatibility.
- Tests covering referral code, progress service, campaign readiness,
  link/code inspection, and attribution-related journeys.

## Product Boundary

This SaaS product should expose only the capabilities needed to sell and operate
referral management and campaign attribution:

- tenant/account setup for referral SaaS customers
- campaign setup and readiness
- referral code/link issue, validation, trace, and lifecycle management
- progress/event ingestion for referral journeys
- campaign attribution evidence and explainable attribution trace
- referrer/customer-safe status
- tenant-safe reporting and exports
- operator support workflows for failed validation, missing evidence, and
  attribution investigation

## Explicit Non-Goals For First SaaS Launch

The following should not block a 10/10 referral and attribution SaaS launch:

- full DLaaS marketplace distribution
- distributor commission settlement
- funding account operations
- fulfilment provider routing
- settlement batches and certifications
- sponsor billing
- white-label/embed infrastructure
- full SaaS usage billing beyond basic plan/limit gates

Reward summaries may remain visible if already supported, but deep money
movement must stay outside this product boundary unless a separate task scopes
it with money-flow guardrails.

## 10/10 Product Criteria

The product reaches 10/10 when:

- every product API is tenant-scoped, documented, and contract-tested
- campaign setup and readiness are coherent in backend and frontend
- referral code/link lifecycle is auditable and operator-investigable
- progress/event ingestion has clear idempotency, dedupe, retry, and safe-error
  behavior
- campaign attribution has an explainable trace from link/code/event to outcome
- referrer and customer surfaces show safe status without internal leakage
- reporting is tenant-safe and exportable
- full SaaS golden-path and failure-path E2E tests pass
- live DB/state verification confirms schema, constraints, statuses, and smoke
  routes

## Relationship To DLaaS

This product should remain compatible with DLaaS by using portable platform
language: account, campaign, participant, link/code, event, attribution trace,
status, audit evidence, and report.

Compatibility does not mean DLaaS expansion work is required for first launch.

