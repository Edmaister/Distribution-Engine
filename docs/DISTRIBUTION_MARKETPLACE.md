# Distribution Marketplace

Distribution marketplace capability starts after the funding platform can
reliably govern sponsor-funded commercial exposure.

## Current Capability

The platform now supports the first distribution slice:

- Distributor creation
- Distributor listing and filtering
- Distributor profile retrieval
- Distributor profile updates
- Distributor activation
- Distributor suspension
- Distributor termination
- Distributor segmentation, regional coverage, channel support, eligibility,
  capabilities, and operating limits
- Distributor wallet creation
- Distributor wallet listing and retrieval
- Distributor earning credits
- Distributor fund holds
- Distributor hold releases
- Distributor payouts
- Distributor earning reversals
- Distributor wallet ledger entries
- Commission rule creation and listing
- Commission calculation by tenant, sponsor, campaign, distributor type, and sale amount
- Commission event recording
- Optional commission crediting into distributor wallets
- Opportunity creation, listing, retrieval, and updates
- Opportunity publish, close, and reopen lifecycle actions
- Distributor-ready opportunity filters by segment, region, channel, and distributor type
- Opportunity-to-distributor match previews
- Persisted offer routing to matched distributors
- Route acceptance and decline lifecycle actions
- Distributor-facing profile retrieval
- Distributor-facing offer inbox with opportunity details
- Distributor-facing wallet, ledger, and performance views
- Distributor compliance review creation, listing, and completion
- Marketplace dispute creation, listing, resolution, and rejection
- Distributor governance actions for suspension, reinstatement, termination,
  and operating-limit updates
- Governance audit trail for compliance, dispute, and distributor control actions
- Marketplace overview reporting
- Opportunity performance reporting
- Distributor performance reporting
- Governance reporting

## Data Model

Primary table:

- `distribution_distributors`
- `distribution_distributor_wallets`
- `distribution_distributor_wallet_ledger`
- `distribution_commission_rules`
- `distribution_commission_events`
- `distribution_opportunities`
- `distribution_offer_routes`
- `distribution_compliance_reviews`
- `distribution_disputes`
- `distribution_governance_audit`

The distributor model records who can distribute sponsor-funded opportunities,
where they operate, which segments they serve, what channels they support, and
what limits apply before routing or commission logic is introduced.

The distributor wallet model tracks distributor earnings and cash movement
states. Current balance records unpaid earned value, available balance records
earnings that can still be held or reversed, held balance records earnings being
prepared for payout, paid-out balance records completed payouts, and reversed
balance records cancelled earnings.

The commission model separates distributor commission from customer or referrer
rewards. Commission rules decide how a distributor is paid for an activity, and
commission events store the calculated result before or after wallet crediting.

The opportunity model records sponsor-funded demand that can later be shown to,
matched with, or routed to distributors. It links sponsor, campaign, product,
funding contract, targeting, budget, allocation limit, and lifecycle status in
one marketplace-ready record.

The routing model records which distributors were matched or routed to an
opportunity. Route scores explain fit across distributor type, segment, region,
and channel, while route status tracks whether the offer is routed, accepted, or
declined.

The governance model records operational controls around the marketplace.
Compliance reviews capture distributor checks, disputes capture disagreements or
exceptions on routed offers, and governance audit records preserve who changed
what, why, and what the before/after state was.

## Admin API

Create a distributor:

```text
POST /admin/distribution/distributors
```

List distributors:

```text
GET /admin/distribution/distributors
```

Get a distributor:

```text
GET /admin/distribution/distributors/{distributor_id}
```

Update distributor profile:

```text
PATCH /admin/distribution/distributors/{distributor_id}/profile
```

Activate a distributor:

```text
POST /admin/distribution/distributors/{distributor_id}/activate
```

Suspend a distributor:

```text
POST /admin/distribution/distributors/{distributor_id}/suspend
```

Terminate a distributor:

```text
POST /admin/distribution/distributors/{distributor_id}/terminate
```

Create a distributor wallet:

```text
POST /admin/distribution/distributor-wallets
```

List distributor wallets:

```text
GET /admin/distribution/distributor-wallets
```

Get a distributor wallet:

```text
GET /admin/distribution/distributor-wallets/{wallet_id}
```

Credit distributor earnings:

```text
POST /admin/distribution/distributor-wallets/{wallet_id}/credit
```

Hold distributor earnings:

```text
POST /admin/distribution/distributor-wallets/{wallet_id}/hold
```

Release held earnings:

```text
POST /admin/distribution/distributor-wallets/{wallet_id}/release-hold
```

Pay out held earnings:

```text
POST /admin/distribution/distributor-wallets/{wallet_id}/payout
```

Reverse available earnings:

```text
POST /admin/distribution/distributor-wallets/{wallet_id}/reverse
```

List wallet ledger entries:

```text
GET /admin/distribution/distributor-wallets/{wallet_id}/ledger
```

Create a commission rule:

```text
POST /admin/distribution/commissions/rules
```

List commission rules:

```text
GET /admin/distribution/commissions/rules
```

Calculate commission:

```text
POST /admin/distribution/commissions/calculate
```

List commission events:

```text
GET /admin/distribution/commissions/events
```

Create an opportunity:

```text
POST /admin/distribution/opportunities
```

List opportunities:

```text
GET /admin/distribution/opportunities
```

Get an opportunity:

```text
GET /admin/distribution/opportunities/{opportunity_id}
```

Update an opportunity:

```text
PATCH /admin/distribution/opportunities/{opportunity_id}
```

Publish an opportunity:

```text
POST /admin/distribution/opportunities/{opportunity_id}/publish
```

Close an opportunity:

```text
POST /admin/distribution/opportunities/{opportunity_id}/close
```

Reopen an opportunity:

```text
POST /admin/distribution/opportunities/{opportunity_id}/reopen
```

Preview distributor matches for an opportunity:

```text
POST /admin/distribution/routing/opportunities/{opportunity_id}/matches
```

Route an opportunity to matched distributors:

```text
POST /admin/distribution/routing/opportunities/{opportunity_id}/routes
```

List offer routes:

```text
GET /admin/distribution/routing/routes
```

Accept an offer route:

```text
POST /admin/distribution/routing/routes/{route_id}/accept
```

Decline an offer route:

```text
POST /admin/distribution/routing/routes/{route_id}/decline
```

Get distributor portal profile:

```text
GET /distribution/portal/profile
```

List distributor portal offers:

```text
GET /distribution/portal/offers
```

Accept a distributor portal offer:

```text
POST /distribution/portal/offers/{route_id}/accept
```

Decline a distributor portal offer:

```text
POST /distribution/portal/offers/{route_id}/decline
```

List distributor portal wallets:

```text
GET /distribution/portal/wallets
```

List distributor portal wallet ledger:

```text
GET /distribution/portal/wallets/{wallet_id}/ledger
```

Get distributor portal performance:

```text
GET /distribution/portal/performance
```

Create a distributor compliance review:

```text
POST /admin/distribution/governance/compliance-reviews
```

List distributor compliance reviews:

```text
GET /admin/distribution/governance/compliance-reviews
```

Complete a distributor compliance review:

```text
POST /admin/distribution/governance/compliance-reviews/{review_id}/complete
```

Create a marketplace dispute:

```text
POST /admin/distribution/governance/disputes
```

List marketplace disputes:

```text
GET /admin/distribution/governance/disputes
```

Resolve or reject a marketplace dispute:

```text
POST /admin/distribution/governance/disputes/{dispute_id}/resolve
```

Apply a distributor governance action:

```text
POST /admin/distribution/governance/distributors/{distributor_id}/actions
```

List governance audit records:

```text
GET /admin/distribution/governance/audit
```

Get marketplace overview reporting:

```text
GET /admin/distribution/reporting/overview
```

List opportunity performance reporting:

```text
GET /admin/distribution/reporting/opportunities
```

List distributor performance reporting:

```text
GET /admin/distribution/reporting/distributors
```

Get governance reporting:

```text
GET /admin/distribution/reporting/governance
```

## Distributor Lifecycle

```text
Distributor created
  -> Status is ONBOARDING
  -> Profile, eligibility, capabilities, and limits are captured
  -> Admin activates distributor
  -> Distributor becomes eligible for future opportunity routing
  -> Admin can suspend or terminate distributor when needed
```

## Distributor Wallet Flow

```text
Commission or earning is credited
  -> Current and available balances increase
  -> Earnings can be placed on hold for payout review
  -> Hold can be released back to available balance
  -> Held earnings can be paid out
  -> Available earnings can be reversed
  -> Every movement writes a wallet ledger entry
```

## Commission Flow

```text
Distributor activity is supplied
  -> Active commission rule is matched
  -> Commission amount is calculated
  -> Commission event is stored as CALCULATED
  -> Optional wallet credit records earnings
  -> Commission event is marked CREDITED
```

## Opportunity Flow

```text
Sponsor-funded demand is captured
  -> Campaign, product, funding, budget, and targeting context are recorded
  -> Opportunity is created as DRAFT
  -> Admin publishes the opportunity when ready
  -> Distributors can list opportunities using eligibility-style filters
  -> Admin closes or reopens the opportunity as commercial availability changes
```

## Offer Routing Flow

```text
Published opportunity is selected
  -> Active distributors in the same tenant are evaluated
  -> Distributor type, segment, region, and channel fit are scored
  -> Admin can preview ranked matches
  -> Admin routes the opportunity to matched distributors
  -> Distributor route can be accepted or declined
```

## Distributor Portal Flow

```text
Distributor identifies by tenant and distributor code
  -> Distributor profile is retrieved
  -> Routed offers are listed with sponsor and product context
  -> Distributor accepts or declines an offer
  -> Wallet and ledger views show earnings movement
  -> Performance view summarizes routed, accepted, declined, commission, and wallet totals
```

## Marketplace Governance Flow

```text
Distributor or route needs operational control
  -> Admin opens or completes compliance review
  -> Admin opens or resolves route dispute
  -> Admin can suspend, reinstate, terminate, or update distributor limits
  -> Governance audit records before and after state
  -> Reporting can show control history by tenant, distributor, and action type
```

## Marketplace Reporting Flow

```text
Marketplace reporting request is made
  -> Platform aggregates distributors, opportunities, routes, commissions, wallets, and governance data
  -> Admin can view platform, sponsor/campaign, opportunity, distributor, and governance summaries
  -> Reporting supports target-state visibility across commercial performance and operational control
```

## Remaining Work

No planned distribution marketplace phases remain in this roadmap slice.
