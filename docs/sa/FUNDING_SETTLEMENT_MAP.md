# Funding And Settlement Map

## Current Money Domains

| Domain | Current evidence | Current role |
| --- | --- | --- |
| Rewards | `rewards`, reward policies, reward service, reward summary APIs | Customer/referrer reward calculation and status. |
| Distributor commissions | `distribution_commission_rules`, `distribution_commission_events`, commission service | Distributor payment calculation separate from customer/referrer rewards. |
| Distributor wallets | `distribution_distributor_wallets`, wallet ledger, wallet service | Distributor earning balance, holds, payouts, reversals. |
| Funding accounts/reservations | funding accounts, funding rules, reservations, limits, exposure, alerts | Determine and reserve funding obligations for reward outcomes. |
| Sponsor wallets/contracts | sponsor wallets, funding allocations, funding contracts, contract ledger | Sponsor-funded commercial exposure and utilisation. |
| Budget governance | budget governance migration/services/routes | Budget requests, approvals, transfers, exceptions. |
| Fulfilment | fulfilment service, provider routing, audit, retries, DLQ | Execute reward fulfilment through configured providers. |
| Settlement | settlement ledger, batches, items, approvals, exceptions, reversals, periods, certifications | Move approved obligations through settlement controls. |
| Sponsor billing | sponsor invoice/payment tables and services | Bill sponsors for utilisation; separate from future SaaS platform billing. |
| Reconciliation | funding reconciliation, fulfilment/settlement reconciliation, outcome money map | Find gaps, exceptions, and broken money trails. |

## Current Flow

```text
Customer or distribution outcome
  -> Reward and/or commission calculation
  -> Funding resolution/reservation or wallet allocation
  -> Fulfilment request/provider processing
  -> Settlement ledger/batch/approval/exception
  -> Sponsor invoice/utilisation evidence where applicable
  -> Reconciliation, audit, dashboard/reporting visibility
```

## Current Strengths

- Funding and settlement are materially more mature than the tenant/account/SaaS packaging layer.
- Sponsor billing, wallets, contracts, allocations, forecasting, reconciliation, and budget governance already exist.
- Settlement batches, approvals, exceptions, reversals, periods, and certifications exist.
- Outcome-to-money visibility exists in current roadmap docs and finance/admin surfaces.
- Fulfilment status, retry, DLQ, and audit services exist.

## Gaps For DLaaS

| Gap | Description | Trace |
| --- | --- | --- |
| Money-GAP-01 | No single canonical outcome-to-liability state that spans reward, commission, funding, fulfilment, settlement, and billing evidence. | GAP-05, GAP-08, GAP-09, GAP-10 |
| Money-GAP-02 | Sponsor billing exists, but SaaS platform billing does not. | GAP-17 |
| Money-GAP-03 | Customer/partner-safe money status needs mapping from internal reward/funding/settlement states. | GAP-15 |
| Money-GAP-04 | Campaign-level funding readiness/liability projection should be first-class in the control plane. | GAP-09, GAP-14 |
| Money-GAP-05 | Audit taxonomy across reward, funding, fulfilment, settlement, reversal, and repair actions should be canonical. | GAP-11 |

## Target Operating Views

| View | User | Required backend truth |
| --- | --- | --- |
| Liability dashboard | Finance/operator | Calculated rewards/commissions, reserved funding, fulfilled amounts, settled amounts, reversed/disputed amounts. |
| Campaign funding readiness | Operator/tenant admin | Campaign budget, available funds, pending obligations, settlement readiness, alerts. |
| Outcome money trace | Operator/support | Outcome ID, reward, commission, wallet movement, funding reservation, fulfilment, settlement, invoice evidence, audit. |
| Sponsor billing | Sponsor/finance | Sponsor invoices, statements, receipts, utilisation, contracts, wallet and forecast. |
| Partner/distributor earnings | Distributor/partner | Safe commission/wallet/settlement statuses and action-required states. |
| Customer reward status | Customer/referrer | Safe pending/approved/fulfilled/failed/action-required reward status without internal ledger detail. |

## Implementation Guardrails

- Do not merge sponsor utilisation billing and SaaS platform billing into one table/model without an explicit boundary.
- Do not calculate displayed money from frontend assumptions.
- Do not allow user-editable fields to modify reward, commission, funding, fulfilment, settlement, invoice, or audit values without backend validation and audit.
- Every money-affecting repair action needs reason capture, actor identity, before/after state, idempotency, and tests.
