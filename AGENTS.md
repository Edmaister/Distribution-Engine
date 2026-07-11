# AGENTS.md

## Project Direction

This repository is targeting **Distribution Layer as a Service (DLaaS)**.

Do not treat it as a simple referral app, and do not build generic dashboards. DLaaS is a reusable multi-tenant platform for configuring, launching, tracking, rewarding, funding, fulfilling, settling, and analyzing distribution/referral/partner campaigns through APIs, webhooks, operator tooling, and partner/customer UX.

## Source Documents

- Target state: `docs/product/DLAAS_TARGET_STATE.md`
- Product boundaries: `docs/product/README.md`
- Referral SaaS product brief: `docs/product/referral-saas/PRODUCT_BRIEF.md`
- DLaaS product brief: `docs/product/dlaas/PRODUCT_BRIEF.md`
- SA outputs: `docs/sa/`
- Roadmap and tasks: `docs/roadmap/`
- Roadmap boundaries: `docs/roadmap/README.md`
- Ordered implementation tasks: `docs/roadmap/ORDERED_TASK_LIST.md`

No major coding task may start without checking the relevant SA and roadmap docs.

## Product Boundary Gate

Before starting any implementation task, classify the work as one of:

- **Referral SaaS**: Referral Management and Campaign Attribution SaaS. This includes referral code creation/validation, accepted terms, referral progress, journey checks, campaign setup, campaign readiness, campaign attribution, link/code inspection, referrer/customer-safe status, tenant-safe referral reporting, and referral SaaS frontend workflows.
- **DLaaS**: Broader Distribution Layer as a Service expansion. This includes distributor marketplace depth, commissions, funding, fulfilment, settlement, sponsor billing, platform SaaS billing, white-label/embed, broad partner distribution, and full DLaaS public API expansion.
- **Shared Platform**: Cross-product primitives used by both product surfaces. This includes tenant/account boundaries, auth/RBAC, audit, idempotency/retry standards, event contracts, observability, live DB verification, shared API client code, and shared UI components.

Required boundary read before implementation:

- Referral SaaS work must read `docs/product/referral-saas/PRODUCT_BRIEF.md` and `docs/roadmap/referral-saas/ROADMAP.md`.
- DLaaS work must read `docs/product/dlaas/PRODUCT_BRIEF.md`, `docs/product/DLAAS_TARGET_STATE.md`, and `docs/roadmap/dlaas/ROADMAP.md`.
- Shared Platform work must read `docs/product/README.md`, `docs/roadmap/README.md`, and whichever product brief(s) are affected.

Do not copy or fork source code into separate product folders. Product boundaries live in docs, roadmap, routes, UX surfaces, tests, and packaging. Shared backend and frontend primitives remain single-source unless a task explicitly introduces a reviewed abstraction boundary.

## Required Workflow

Follow this chain:

```text
Product Boundary Gate -> Target State/Product Brief -> SA Docs -> Gap Matrix -> Enhancement Backlog -> Ordered Task List -> Implementation -> Tests -> Docs Update
```

Every implementation task must reference a `TASK-XXX` ID from `docs/roadmap/ORDERED_TASK_LIST.md`, and the task status/docs must be updated when implementation work changes scope or completion state.

Every new or updated task should include:

- Product boundary: Referral SaaS, DLaaS, or Shared Platform.
- Required boundary docs checked.
- Shared primitive impact.
- Source duplication: must be `No`.
- Tests and docs update expectations.

## Engineering Rules

- Do not invent backend fields, statuses, schemas, or APIs.
- Treat database schema and service-layer code as the source of truth.
- Separate current facts from target-state recommendations.
- Build in small, reviewable, capability-driven changes.
- Prefer platform primitives over page-specific or one-off referral behavior.

## Money And Audit Rules

Reward, funding, fulfilment, settlement, and audit flows require extra care:

- inspect the actual database schema
- inspect the relevant service-layer logic
- include idempotency and retry behavior
- include failure and delayed states
- include auditability
- add or update tests
- perform DB/state validation where relevant

Visual polish must not come before correctness, traceability, and platform reuse.
