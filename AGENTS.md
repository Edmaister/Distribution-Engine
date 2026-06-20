# AGENTS.md

## Project Direction

This repository is targeting **Distribution Layer as a Service (DLaaS)**.

Do not treat it as a simple referral app, and do not build generic dashboards. DLaaS is a reusable multi-tenant platform for configuring, launching, tracking, rewarding, funding, fulfilling, settling, and analyzing distribution/referral/partner campaigns through APIs, webhooks, operator tooling, and partner/customer UX.

## Source Documents

- Target state: `docs/product/DLAAS_TARGET_STATE.md`
- SA outputs: `docs/sa/`
- Roadmap and tasks: `docs/roadmap/`
- Ordered implementation tasks: `docs/roadmap/ORDERED_TASK_LIST.md`

No major coding task may start without checking the relevant SA and roadmap docs.

## Required Workflow

Follow this chain:

```text
Target State -> SA Docs -> Gap Matrix -> Enhancement Backlog -> Ordered Task List -> Implementation -> Tests -> Docs Update
```

Every implementation task must reference a `TASK-XXX` ID from `docs/roadmap/ORDERED_TASK_LIST.md`, and the task status/docs must be updated when implementation work changes scope or completion state.

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
