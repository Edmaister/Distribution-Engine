# Liability State Model And Source Mapping

Status: Accepted for TASK-015 on 2026-06-22.

## Purpose

TASK-015 defines liability states and maps them to current reward, commission, funding, wallet, fulfilment, settlement, invoice, and missing-evidence sources.

This is a contract document only. It does not implement a liability projection service, add routes, add migrations, rename fields, create rollup tables, change reward or commission behavior, mutate funding, alter fulfilment or settlement behavior, or create repair actions.

## Source Documents And Code

- `docs/product/DLAAS_TARGET_STATE.md`
- `docs/sa/OUTCOME_TRACE_RESPONSE_CONTRACT.md`
- `docs/sa/QUALIFICATION_DECISION_CONTRACT.md`
- `docs/sa/REWARD_COMMISSION_POLICY_BOUNDARY.md`
- `docs/sa/API_SURFACE_MAP.md`
- `docs/sa/CURRENT_STATE_MAP.md`
- `docs/sa/CAPABILITY_GAP_MATRIX.md`
- `docs/sa/STATE_MACHINE_MAP.md`
- `services/outcome_trace_service.py`
- `services/outcome_money_reconciliation_service.py`
- `services/reward_service.py`
- `services/reward_policy_service.py`
- `services/distribution/commission_service.py`
- `services/funding/*`
- `services/marketplace_funding/*`
- `services/fulfilment/*`
- `services/fulfilment/settlement/*`

## Problem Statement

DLaaS needs a liability model that can explain money obligations without double-counting source evidence. Current systems already record reward rows, distributor commission rows, funding reservations, marketplace funding allocations, wallet movements, fulfilment audit, sponsor invoices, settlement ledger rows, settlement exceptions, and reversals.

Those rows are not the same thing. A reward, an invoice line, a funding reservation, and a settlement ledger row can all point to the same underlying obligation. Liability projection must preserve the phase and source family of each row so future funding dashboards and operator views do not add the same obligation multiple times.

## Current Source Truth

| Evidence family | Current source truth | Current role in liability |
| --- | --- | --- |
| Qualification | `referral_instances`, progress/enterprise events, TASK-013 contract | Explains why money work may start. Not a liability row. |
| Reward decision | `rewards`, legacy `referral_rewards`, `services/reward_service.py` | Customer/referrer obligation evidence. |
| Distributor commission decision | `distribution_commission_events`, `distribution_commission_rules`, `services/distribution/commission_service.py` | Distributor obligation evidence. |
| Funding reservation | `funding_reservations`, marketplace funding allocations, sponsor wallets/contracts | Reservation or release of budget against an obligation. |
| Distributor wallet movement | `distribution_distributor_wallet_ledger` through distribution wallet services | Distributor-side fulfilment or credit evidence for commission flows. |
| Fulfilment | `fulfilment_audit` and fulfilment services | Provider/action evidence for reward fulfilment. |
| Sponsor invoice | `sponsor_invoices`, `sponsor_invoice_lines` | Producer/sponsor billing evidence. Not a new customer reward obligation. |
| Settlement | `fulfilment_settlement_ledger`, settlement batches/items/approvals/exceptions/reversals | Settlement and exception evidence over prior obligations and fulfilment. |
| Audit | admin, referral-processing, funding, fulfilment, and distribution audit rows | Investigation evidence. Not a liability amount source by itself. |

## Liability Categories

Liability projection must preserve the TASK-014 money decision categories:

- `CUSTOMER_REWARD`
- `REFERRER_REWARD`
- `DISTRIBUTOR_COMMISSION`

Funding, fulfilment, settlement, invoice, wallet, and audit evidence are phases or evidence over those categories. They must not be promoted into new liability categories unless a future contract defines a separate obligation type.

## Liability State Model

These are derived liability states for future read models. They are not current database enum values.

| Derived state | Meaning | Current source mapping |
| --- | --- | --- |
| `CALCULATED` | A reward or commission obligation has been calculated or recorded, but downstream funding/fulfilment/settlement may not be complete. | `rewards.status` such as `APPLIED`, `EARNED`, or `PENDING_FULFILMENT`; `referral_rewards`; `distribution_commission_events.commission_status = CALCULATED`. |
| `RESERVED` | Budget or wallet funding has been reserved for the obligation. | `funding_reservations.status = RESERVED`; marketplace funding allocation `status = RESERVED`. |
| `RELEASED` | Previously reserved budget was released and should not be counted as active reserved liability. | `funding_reservations.status = RELEASED`; marketplace funding allocation `status = RELEASED`. |
| `FULFILLED` | The obligation has provider, wallet, or domain evidence that value was delivered or credited. | `rewards.status = FULFILLED`; fulfilment audit `status = SUCCESS`; `distribution_commission_events.commission_status = CREDITED`; related wallet ledger credit evidence. |
| `SETTLED` | The fulfilled obligation has settlement evidence. | `funding_reservations.status = SETTLED`; `fulfilment_settlement_ledger.status = SETTLED`; settled settlement batch/item evidence. |
| `REVERSED` | The obligation or a downstream funding/settlement movement has been reversed. | `rewards.status = REVERSED`; marketplace funding allocation `status = REVERSED`; settlement reversal rows; reversed ledger evidence where present. |
| `FAILED` | A downstream attempt failed and needs retry, repair, or final failure handling. | `rewards.status = FAILED`; fulfilment statuses such as `FAILED_RETRYABLE`, `FAILED_FINAL`, or `DLQ`; settlement `status = FAILED`; failed invoice generation evidence where present. |
| `DISPUTED` | Settlement or exception evidence indicates the obligation is disputed or blocked by an open exception. | settlement `status = DISPUTED`; open settlement exceptions; unresolved funding or budget governance exceptions where applicable. |
| `PENDING` | Work has started or evidence exists, but the relevant downstream phase is still in progress. | fulfilment `PENDING` or `PROCESSING`; settlement `PENDING` or `PROCESSING`; settlement batches before `SETTLED`; pending approvals. |
| `MISSING_EVIDENCE` | Required source evidence is absent, ambiguous, or unavailable for the requested view. | TASK-010 missing evidence such as `NO_SOURCE_EVIDENCE`, `JOIN_AMBIGUOUS`, `SOURCE_UNAVAILABLE`, `SOURCE_CONFLICT`, `REDACTED`, or `NOT_APPLICABLE`. |

Current source statuses must remain visible in the evidence section of any future liability response. The derived state is a read-model interpretation, not a replacement for source status.

## Source Mapping Rules

### Reward Sources

Reward liability starts with `CUSTOMER_REWARD` or `REFERRER_REWARD` decision evidence.

Use:

- `rewards` as the current reward-service source;
- `referral_rewards` as legacy/current trace evidence where it exists;
- reward service business-key and unique-index behavior as duplicate evidence;
- `reward_id`, `referral_track_id`, `tenant_code`, beneficiary type, reward type, amount, reward source, mission code, and source status as safe operator evidence.

Do not count both `rewards` and `referral_rewards` as separate obligations unless a future implementation proves they represent distinct liabilities. Until then, a liability projection must expose the source rows and mark ambiguous duplicates rather than silently sum them.

### Distributor Commission Sources

Distributor commission liability starts with `DISTRIBUTOR_COMMISSION` decision evidence.

Use:

- `distribution_commission_events` as the commission event source;
- `distribution_commission_rules` as the rule source;
- `(tenant_code, source_event_id)` as current duplicate protection where `source_event_id` is present;
- `commission_event_id`, distributor, sponsor, campaign, activity type, sale amount, commission amount, currency, commission status, source event, and correlation fields as source evidence.

Do not treat wallet crediting as a second commission. Wallet movement is downstream fulfilment/credit evidence.

### Funding Sources

Funding evidence describes reservation, release, debit, or settlement movement against prior obligations.

Use:

- `funding_reservations` for reservation/release/settle evidence;
- marketplace funding allocations for sponsor funding allocation states such as `RESERVED`, `RELEASED`, `DEBITED`, and `REVERSED`;
- funding accounts, funding account rules, sponsor wallets, funding contracts, and funding contract ledger as context when joined safely.

Funding rows may support `RESERVED`, `RELEASED`, `SETTLED`, `REVERSED`, or `MISSING_EVIDENCE`. They must not create a new obligation amount separate from the reward or commission decision.

### Fulfilment Sources

Fulfilment evidence describes delivery attempts and outcomes.

Use:

- `fulfilment_audit`;
- fulfilment idempotency keys and provider references;
- source statuses such as `PENDING`, `PROCESSING`, `SUCCESS`, `FAILED_RETRYABLE`, `FAILED_FINAL`, `DLQ`, and `SKIPPED_DUPLICATE`.

Fulfilment success supports `FULFILLED`. Retryable or final failure supports `FAILED`. Duplicate skipped evidence should remain visible as duplicate/no-op evidence and must not create a second fulfilled obligation.

### Settlement Sources

Settlement evidence describes financial closeout, exceptions, disputes, and reversals over previous money decisions.

Use:

- `fulfilment_settlement_ledger`;
- settlement batches, items, approvals, periods, certifications, exceptions, and reversals;
- source statuses such as `PENDING`, `PROCESSING`, `SETTLED`, `FAILED`, `REVERSED`, and `DISPUTED`;
- open settlement exceptions as dispute or attention evidence.

Settlement rows support `SETTLED`, `FAILED`, `REVERSED`, `DISPUTED`, `PENDING`, or `MISSING_EVIDENCE`. They must not be summed as new reward or commission obligations.

### Invoice And Billing Sources

Sponsor invoice evidence describes billing readiness and producer/sponsor recovery for a prior obligation.

Use:

- `sponsor_invoices`;
- `sponsor_invoice_lines`;
- invoice and payment statuses where current services expose them;
- `reward_id` and contract/sponsor references where joined safely.

Invoice lines are billing evidence. They are not separate reward liabilities and should not be added to reward obligation totals.

## Aggregation And Double-Counting Rules

Future liability projection should expose separate totals by phase:

- `obligation_total`: sum of distinct reward and commission decision obligations by liability category.
- `reserved_total`: sum of distinct active funding reservations or allocations.
- `released_total`: sum of distinct released reservations or allocations.
- `fulfilled_total`: sum of distinct fulfilled reward/provider or commission wallet-credit evidence.
- `settled_total`: sum of distinct settled ledger evidence.
- `reversed_total`: sum of distinct reversed obligation, funding, or settlement evidence.
- `failed_total`: sum of distinct failed fulfilment/settlement evidence where an amount can be safely attributed.
- `disputed_total`: sum of distinct disputed/open-exception evidence where an amount can be safely attributed.

Rules:

- The same source row may contribute to only one phase total at a time.
- A downstream phase must point back to a source obligation or return missing evidence.
- Invoices, wallet movements, funding reservations, and settlement rows must not inflate `obligation_total`.
- Reward and distributor commission categories must remain separate in totals and item lists.
- Weak joins must produce `MISSING_EVIDENCE` or `JOIN_AMBIGUOUS`, not quiet zeroes.
- Tenant scope must be applied before any source evidence is returned.

## Missing Evidence And Conflicts

Use the TASK-010 missing-evidence vocabulary:

- `OUTCOME_NOT_FOUND`
- `TENANT_MISMATCH`
- `JOIN_AMBIGUOUS`
- `NO_SOURCE_EVIDENCE`
- `SOURCE_UNAVAILABLE`
- `SOURCE_CONFLICT`
- `REDACTED`
- `NOT_APPLICABLE`
- `SECTION_NOT_REQUESTED`

Liability-specific missing evidence should identify the phase and source family:

- `reward`
- `commission`
- `funding`
- `wallet`
- `fulfilment`
- `invoice`
- `settlement`
- `audit`

Conflicts must be explicit when two source rows disagree on tenant, participant, amount, category, status, reward ID, commission event ID, or settlement ownership.

## API Direction

TASK-015 does not add an API. Future liability APIs should be read-only first:

```text
GET /admin/outcomes/{referral_track_id}/liability?tenant_code=...
GET /admin/campaigns/{campaign_ref}/liability?tenant_code=...
```

Contract rules:

- reads must be tenant and role scoped;
- reads must not require idempotency keys;
- responses must include derived state, raw source status, source family, source ID, amount, currency, category, join confidence, and missing evidence;
- responses must return safe errors and must not expose raw UCNs, provider payloads, secrets, or unredacted internal metadata;
- repair, retry, reversal, settlement approval, payout, and funding mutation commands are separate tasks and require audit plus idempotency.

## Backward Compatibility

Current tables, source statuses, and services remain unchanged. This model is additive and derived.

Existing `tenant_code` columns remain internal source truth for backend isolation and joins. External/public contracts must continue using the identifier boundary from TASK-048 where applicable.

Existing outcome trace behavior remains the diagnostic source for partial and missing evidence. Future liability projection should consume that discipline rather than hiding incomplete joins.

## Non-Goals

TASK-015 does not implement the liability projection read service.

TASK-015 does not start TASK-016.

TASK-015 does not create a canonical liability table, source rollup table, materialized view, migration, index, route, frontend surface, settlement workflow, funding workflow, fulfilment workflow, or repair command.

TASK-015 does not change reward, commission, funding, fulfilment, settlement, audit, auth, tenant, privacy, or data-isolation behavior.

## Follow-Up Implementation Tasks

- Implement a read-only liability projection service using this model.
- Add liability rollup tests for reward and commission category separation.
- Add double-count prevention tests across reward, funding, invoice, wallet, fulfilment, and settlement evidence.
- Add missing-evidence and ambiguous-join tests.
- Add tenant-scope tests before any operator or partner API exposes liability data.
- Add schema or index work only if the read-service implementation proves a current source join is unavailable or too slow.

## Validation Notes

Current source truth is sufficient to define a derived liability state model and source mapping. It is not sufficient to guarantee every runtime join without TASK-016 implementation tests and clean DB/state verification.

Readback validation for TASK-015 should confirm the model distinguishes calculated, reserved, released, fulfilled, settled, reversed, failed, disputed, pending, and missing-evidence states; preserves reward and commission category separation; and prevents funding, wallet, invoice, fulfilment, and settlement evidence from being double-counted as new obligations.
