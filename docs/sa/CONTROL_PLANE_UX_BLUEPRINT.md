# Control Plane UX Blueprint

## Principle

The DLaaS control plane is an operator and tenant tool for configuring, monitoring, investigating, and repairing distribution campaigns. It is not a generic referral dashboard.

Every screen must answer:

- What happened?
- What happens next?
- Is action required?
- What backend state is this in?
- Can the user trust the status?
- Can an operator investigate it?

## Operator Control Plane Screens

| Screen | Purpose | Backend data/API candidates | State represented | Primary CTA |
| --- | --- | --- | --- | --- |
| Tenant/account command centre | Provision and inspect tenant/account readiness. | `/admin/tenants`, target SaaS account APIs, `/auth/session` | Tenant lifecycle/readiness | Continue setup |
| Campaign builder/readiness | Configure campaign, policy, qualification, reward, funding readiness. | campaign routes/services, campaign policy service, funding readiness APIs | Campaign draft/active/paused/completed target state | Activate campaign |
| Participant management | Manage partners, referrers, distributors, sponsors. | referral routes, distribution distributor routes, partner seam, sponsor routes | Participant onboarding/active/suspended/terminated | Invite/activate participant |
| Link/code manager | Generate, inspect, void, and troubleshoot links/codes. | referral codes, campaign referral links, route referral links | Active/voided/expired target mapping | Generate link/code |
| Event and attribution monitor | Inspect event intake, attribution, dedupe, failures, replay. | `/v1/progress`, `/enterprise/events`, `/admin/enterprise-events`, failures/DLQ | Received/queued/duplicate/failed/completed | Replay or inspect |
| Outcome trace | Trace one distribution outcome end to end. | outcome-money map, reward, commission, funding, fulfilment, settlement, audit services | Canonical outcome target state | Investigate next break |
| Reward/commission operations | Review calculated, pending, fulfilled, failed, reversed rewards and commissions. | reward routes, commission routes, reward summary | Reward/commission lifecycle | Approve/repair where allowed |
| Funding dashboard | Monitor budgets, wallets, reservations, limits, exposure, alerts. | `/admin/funding/*`, sponsor wallets, budget governance, forecast | Reserved/released/settled/exposure/alert states | Resolve funding risk |
| Fulfilment dashboard | Monitor providers, retries, failed fulfilments, DLQ. | fulfilment routes/services | Pending/processing/success/failed/DLQ | Retry/replay |
| Settlement dashboard | Manage batches, approvals, exceptions, reversals, certifications. | settlement routes/services | Draft/approval/processing/settled/failed/disputed | Submit/approve/resolve |
| Webhook/integration centre | Manage clients, tokens, subscriptions, delivery health, dead letters. | partner seam routes/services | Active/paused/revoked and pending/sent/failed/cancelled | Retry/export/fix |
| Audit viewer | Search sensitive actions and state transitions. | `/admin/audit`, domain audit services | Audit event records | Export evidence |
| Analytics/reporting | Understand campaign, partner, attribution, reward, funding, settlement performance. | distribution reporting, finance metrics, materialized views | Reporting periods and freshness states | Export report |
| Support/debug console | Search by tenant, campaign, referral track, customer, reward, funding, settlement, webhook delivery. | admin failure, DLQ, audit, outcome trace APIs | Stuck/failure states | Open investigation |

## Partner/Customer Experience Screens

| Screen | Purpose | Backend data/API candidates | State represented | Primary CTA |
| --- | --- | --- | --- | --- |
| Partner integration home | Show credentials, webhooks, delivery health, readiness. | partner seam | Client/webhook/delivery states | Create webhook |
| Distributor portal home | Show profile, offers, performance, wallets. | `/distribution/portal/*` | Distributor/route/wallet states | Accept offer |
| Sponsor portal | Show billing, contracts, wallet, forecast, utilisation. | sponsor portal billing routes | Invoice/contract/wallet/forecast states | Review statement |
| Referrer/customer status | Show safe referral/reward status and action required. | reward summary, consumer experience, referral validation | Customer-safe derived status | Continue required action |
| Link/code sharing | Provide active campaign link/code and share context. | referral/code/link APIs | Active/voided/expired target mapping | Share link |

## UX States Required Everywhere

- Loading: show which backend section is being loaded.
- Empty: explain whether no data exists, filters are too narrow, or setup is incomplete.
- Success: show what changed and the new backend state.
- Failure: show safe error, trace ID/correlation ID if available, and next action.
- Pending/manual review: show owner, reason category, and expected next step.
- Permission denied: show required workspace/role from `/auth/session` where possible.
- Delayed: explain retry, queue, webhook, or settlement delay without implying payment is complete.

## Copy Rules

- Use backend-owned status names for operator views.
- Use safe, plain-language derived statuses for partner/customer views.
- Never imply money is paid when the backend state is only calculated, reserved, pending fulfilment, processing, or unsettled.
- Every trust-building message should reference the evidence type: event received, reward approved, funds reserved, fulfilment processing, settlement completed, audit recorded.

## Build Order

1. Operator outcome trace and funding/settlement observability.
2. Campaign builder/readiness and participant management.
3. Integration/webhook centre.
4. Partner/distributor/sponsor portal status views.
5. Customer/referrer safe status views.
6. Analytics/reporting.
7. SaaS account/usage/billing UX.
8. White-label/embed UX.
