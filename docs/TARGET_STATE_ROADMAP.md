# Target-State Roadmap

Date: 2026-06-10

This roadmap separates the current platform maturity into two milestones:

1. Funding Platform Complete
2. Distribution Marketplace Complete

These are related, but they are not the same target. Funding proves that rewards,
sponsors, contracts, wallets, allocations, and settlement can be governed. The
distribution marketplace is the next layer: it turns that governed funding base
into a scalable ecosystem of distributors, offers, commissions, and commercial
opportunity routing.

## Current Position

The platform now has a strong enterprise backbone:

- Referral and campaign journeys
- IDS/Hogan enterprise event inbox
- Event normalization, dedupe, replay, and dashboard visibility
- Reward policy and fulfilment flow
- Funding rules and funding resolution
- Sponsor wallets
- Funding allocations
- Funding contracts
- Settlement, approvals, reversals, certifications, and exceptions
- Admin security coverage
- Operational docs and tests

The current maturity is strongest in referral orchestration, event intake,
reward lifecycle, fulfilment operations, settlement operations, and funding
foundation.

## Milestone 1: Funding Platform Complete

Funding is complete when the platform can answer four questions with audit-grade
evidence:

- Who funds the reward?
- Which contract or wallet owns the obligation?
- Has the amount been reserved, settled, billed, and paid?
- Can sponsors see and govern their commercial exposure?

### Already In Place

| Capability | Status |
| --- | --- |
| Funding rules | In place |
| Funding resolution | In place |
| Sponsor wallets | In place |
| Wallet balances and ledger | In place |
| Funding allocations | In place |
| Funding contracts | In place |
| Settlement operations | In place |
| Sponsor invoice and utilisation billing foundation | In place |
| Forecasting foundation | In progress |

### Remaining Funding Work

| Phase | Capability | Priority | Purpose |
| --- | --- | --- | --- |
| 11.4 | Sponsor billing and invoicing | Application-complete | Invoice, invoice-line, payment, payment allocation, payment reversal, contract-utilisation generation, scheduled generation, statement, billing dashboard, VAT reporting, and sponsor-facing billing, contract, and utilisation views exist; remaining work is live migration rollout and optional dedicated sponsor identity hardening. |
| 11.5 | Forecasting | Application-complete | Funding account, sponsor wallet, sponsor contract, settlement exposure, sponsor portal forecast views, and forecast risk evaluation exist; remaining work is optional schema hardening for first-class sponsor and settlement alert workflows. |
| 11.6 | Budget governance | Application-complete | Budget increase requests, budget transfer requests, approval policy rules, approvals, rejections, exception workflows, approved contract increases/transfers, and ledger audit entries exist; remaining work is optional budget decrease requests and sponsor-facing request submission. |
| 11.7 | Multi-currency | Application-complete foundation | FX rates, conversion quotes, existing multi-currency wallet records, and cross-border settlement instructions exist; remaining work is external FX provider ingestion, FX gain/loss accounting, and provider-specific payment execution. |
| 11.8 | Sponsor portal | Application-complete | Sponsor-facing read APIs now expose dashboard, invoices, statements, payment receipts, wallet, contracts, utilisation ledger activity, and forecasts; remaining work is frontend experience and optional dedicated sponsor identity hardening. |

### Recommended Funding Sequence

The recommended sequence before moving deeply into distribution is:

1. Sponsor billing and invoicing
2. Forecasting
3. Sponsor portal

After those three, the funding layer can support a credible commercial sponsor
ecosystem:

```text
Contract
  -> Wallet
  -> Allocation
  -> Settlement
  -> Invoice
  -> Payment
  -> Forecast
  -> Sponsor visibility
```

## Milestone 2: Distribution Marketplace Complete

Distribution marketplace capability starts once the platform can reliably fund,
settle, bill, and expose sponsor-funded campaigns.

The marketplace target is:

```text
Sponsor demand
  -> Funded opportunity
  -> Distributor eligibility
  -> Offer routing
  -> Referral or sale activity
  -> Commission/reward calculation
  -> Fulfilment and settlement
  -> Sponsor and distributor reporting
```

### Distribution Capabilities To Build

| Phase | Capability | Purpose |
| --- | --- | --- |
| 12.1 | Distributor model | Application-complete: distributor entities, profiles, segments, eligibility, lifecycle status, channels, regions, capabilities, and operating limits exist. |
| 12.2 | Distributor wallets | Application-complete: distributor earning credits, holds, hold releases, payouts, reversals, balances, and ledger entries exist. |
| 12.3 | Commission engine | Application-complete: commission rules, commission calculation, commission event recording, and optional distributor wallet crediting exist separately from customer/referrer rewards. |
| 12.4 | Opportunity marketplace | Application-complete: sponsor-funded opportunities, campaign/product/funding context, targeting filters, lifecycle publish/close/reopen, and distributor-ready listing exist. |
| 12.5 | Offer routing | Application-complete: published opportunities can be matched to active distributors, scored by distributor type, segment, region, and channel fit, persisted as offer routes, and accepted or declined. |
| 12.6 | Distributor portal/API | Application-complete: distributors can retrieve profile, view routed offers with opportunity details, accept/decline offers, view wallets and ledger activity, and see basic performance and earnings totals. |
| 12.7 | Marketplace governance | Application-complete: compliance reviews, route disputes, distributor suspension/reinstatement/termination/limit actions, and governance audit records exist. |
| 12.8 | Marketplace reporting | Application-complete: marketplace overview, opportunity performance, distributor performance, and governance reporting APIs exist across routes, opportunities, commissions, wallets, disputes, and compliance controls. |

## Roadmap Interpretation

The current platform is not missing the idea of distribution; it has been
building the foundation that distribution needs. The correct interpretation is:

```text
Referral Engine
  -> Enterprise Event Backbone
  -> Reward and Fulfilment Engine
  -> Funding and Settlement Platform
  -> Sponsor Billing and Visibility
  -> Distribution Marketplace
```

That means the next work should not jump straight to a full marketplace before
funding operations are commercially complete. The practical target-state path is
to complete sponsor billing, forecasting, and sponsor visibility first, then use
that as the base for distributor wallets, commission rules, and opportunity
marketplace features.
