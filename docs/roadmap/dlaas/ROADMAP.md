# DLaaS Roadmap

## Objective

Continue the broader Distribution Layer as a Service transformation after the
referral management and campaign attribution SaaS wedge is productized.

## Roadmap Relationship

DLaaS should reuse the SaaS wedge primitives instead of copying them:

- account/tenant
- campaign
- participant
- link/code
- event
- attribution trace
- audit evidence
- tenant-safe status/reporting

## Major Platform Waves

### 1. Platform Account And Entitlement Layer

- account/org model
- user memberships and seats
- role and permission enforcement
- API credentials and scopes
- usage limits and quota attribution

### 2. Canonical Outcome Spine

- connect campaign, participant, link/code, event, attribution, qualification,
  reward, funding, fulfilment, settlement, audit, webhook, and reporting
  evidence
- define missing-evidence and trace-completeness behavior
- expose operator-safe and partner/customer-safe projections

### 3. Platform Audit And Idempotency

- canonical audit taxonomy
- idempotency policy by command/event type
- retry classes and exhaustion behavior
- repair/replay audit evidence

### 4. Money And Liability Expansion

- reward and commission decision boundaries
- funding obligation and reservation projections
- fulfilment status mapping
- settlement status mapping
- no-double-count and reconciliation controls

### 5. Public DLaaS API Product

- versioned API surface
- campaign, participant, link/code, event, status, webhook, reporting, and
  credential contracts
- tenant-safe errors and schema tests
- webhook event catalog alignment

### 6. SaaS Billing And White-Label Readiness

- usage metering
- plan/subscription boundaries
- platform billing separated from sponsor billing
- branding/custom domain/embed only after security gates are mature

## Production Gates

DLaaS should not be considered world-class production-ready until:

- live DB/state verification is complete
- full DLaaS E2E paths pass
- public APIs and webhooks are contract-tested
- money flows have idempotency, retry, failure, audit, and reconciliation tests
- tenant/account isolation is verified
- operator and portal surfaces use safe derived states

