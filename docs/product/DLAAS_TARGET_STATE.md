# Distribution Layer as a Service Target State

## Purpose

Distribution Layer as a Service (DLaaS) is the target platform state for this repository. It is a reusable, multi-tenant platform that lets businesses configure, launch, track, reward, fund, fulfil, settle, and analyze distribution, referral, and partner campaigns through APIs, webhooks, an operator control plane, and partner/customer-facing UX.

This repository must not be treated as a simple referral app. Referral is one distribution pattern inside the larger platform.

## Target-State Capabilities

| ID | Capability | Target outcome |
| --- | --- | --- |
| TS-01 | Tenant/account model | Multiple business clients can be onboarded, isolated, configured, billed, and operated independently. |
| TS-02 | Campaign model | Tenants can define multiple distribution campaigns with lifecycle, limits, attribution, qualification, reward, funding, and reporting context. |
| TS-03 | Partner/referrer/distributor model | The platform can represent people or organizations that distribute offers, refer customers, or route demand. |
| TS-04 | Distribution links/codes | The platform can issue traceable links/codes tied to tenant, campaign, distributor/referrer, and attribution context. |
| TS-05 | Attribution tracking | The platform can connect link/code activity and ingested events to a customer or distribution outcome. |
| TS-06 | Event ingestion | External systems can submit backend events with dedupe, validation, queueing, replay, and failure visibility. |
| TS-07 | Qualification rules | Campaign outcomes can be qualified from backend events and configured journey logic. |
| TS-08 | Reward/commission rules | Customer/referrer rewards and distributor commissions can be calculated from configured policies. |
| TS-09 | Funding/budget tracking | Reward and commission obligations can be reserved, funded, limited, forecast, reconciled, and exposed to operators. |
| TS-10 | Fulfilment/settlement | Rewards, commissions, payouts, settlement batches, approvals, reversals, and exceptions are traceable and auditable. |
| TS-11 | Audit trail | Sensitive actions and state transitions produce durable audit evidence. |
| TS-12 | Public/internal APIs | External clients and internal surfaces use stable, tenant-scoped APIs with explicit auth and idempotency behavior. |
| TS-13 | Webhooks | External systems can subscribe to lifecycle events with signed delivery, retries, failures, and dead-letter export. |
| TS-14 | Operator control plane | Operators can configure, monitor, investigate, repair, and audit distribution flows. |
| TS-15 | Partner/customer portal | Partners, distributors, referrers, sponsors, and customers can see safe status and required actions. |
| TS-16 | Analytics/reporting | Tenants and operators can analyze campaign, partner, customer, reward, funding, settlement, and operational performance. |
| TS-17 | SaaS packaging | The platform supports account setup, plans, seats, usage tracking, quota enforcement, billing hooks, and support operations. |
| TS-18 | White-label/embed | Tenant-branded or embeddable partner/customer UX can be supported after isolation and status APIs are mature. |

## Operating Principles

- Database schema and service-layer code are the source of truth for current capability.
- Current facts and target-state recommendations must be separated.
- Do not invent current fields, statuses, endpoints, or API responses.
- Every gap must trace to a target capability.
- Every enhancement must trace to a gap.
- Every task must trace to an enhancement.
- Money, reward, funding, fulfilment, settlement, and audit work must prioritize correctness, idempotency, retry behavior, failure states, and traceability before visual polish.

## Current Architecture Interpretation

The current repository already contains strong platform material:

- Referral and campaign journeys.
- Enterprise event ingestion and queueing.
- Reward policy and reward records.
- Fulfilment, provider routing, retry, audit, and settlement operations.
- Funding accounts, reservations, limits, exposure, sponsor wallets, sponsor billing, budget governance, forecasting, reconciliation, and multi-currency foundations.
- Distribution marketplace entities: distributors, wallets, commissions, opportunities, offer routes, route referral links, governance, and reporting.
- Partner integration surface: client credentials, access tokens, webhook subscriptions, delivery queue, retries, alerts, and dead-letter export.
- Operator surfaces for funding, settlement, audit, failures, DLQ, enterprise events, distribution, reporting, and command-center aggregation.

The main transformation need is not to add a generic dashboard. It is to consolidate these capabilities into reusable DLaaS platform primitives with canonical state machines, tenant/account isolation, stable APIs, customer/partner-safe status, and SaaS packaging.

## Target Platform Spine

The canonical DLaaS spine should converge around:

```text
Account/Tenant
  -> Campaign
  -> Participant (partner/referrer/distributor/sponsor/customer)
  -> Distribution Link/Code
  -> Attribution Event
  -> Qualified Outcome
  -> Reward or Commission
  -> Funding Obligation/Reservation
  -> Fulfilment
  -> Settlement
  -> Audit/Webhook/Report/Usage Event
```

## Non-Goals For Early Transformation

- Do not build visual polish before backend truth and traceability.
- Do not create a generic referral dashboard.
- Do not add white-label or embedded UX before tenant isolation, status APIs, and permission boundaries are hardened.
- Do not combine sponsor utilisation billing with SaaS platform billing without an explicit model boundary.
