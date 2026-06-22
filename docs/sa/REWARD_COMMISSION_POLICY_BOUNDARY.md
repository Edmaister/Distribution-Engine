# Reward And Commission Policy Boundary

Status: Accepted for TASK-014 on 2026-06-22.

## Purpose

TASK-014 defines how reward policies and distributor commission rules map to outcome money decisions without combining distinct money types incorrectly.

This is a contract document only. It does not implement a reward/commission decision service, add API routes, change migrations, rename current fields, change reward issuance, change commission calculation, mutate funding, alter fulfilment or settlement behavior, or add a canonical liability table.

## Source Documents And Code

- `docs/product/DLAAS_TARGET_STATE.md`
- `docs/sa/QUALIFICATION_DECISION_CONTRACT.md`
- `docs/sa/EVENT_INGESTION_PUBLIC_CONTRACT.md`
- `docs/sa/OUTCOME_TRACE_RESPONSE_CONTRACT.md`
- `docs/sa/API_SURFACE_MAP.md`
- `docs/sa/CURRENT_STATE_MAP.md`
- `docs/sa/CAPABILITY_GAP_MATRIX.md`
- `docs/sa/STATE_MACHINE_MAP.md`
- `services/reward_service.py`
- `services/reward_policy_service.py`
- `services/distribution/commission_service.py`
- `services/outcome_money_reconciliation_service.py`
- `dp/migrations/022_reward.sql`
- `dp/migrations/066_distribution_commissions.sql`

## Problem Statement

DLaaS needs a reliable way to explain why money is owed after an outcome qualifies. The current platform already records customer/referrer rewards and distributor commissions, but those are different money-decision families:

- rewards are owed to referrers or referees/customers from reward policy decisions;
- distributor commissions are owed to distributors from distribution commission rules;
- funding, fulfilment, settlement, wallet, invoice, and reporting work must consume these decisions without double-counting them.

TASK-013 establishes that money work starts from explainable qualification evidence. TASK-014 defines the next boundary: how qualified outcome evidence becomes reward or commission decisions.

## Current Source Truth

| Decision family | Current source truth | Current duplicate guard | Current status source |
| --- | --- | --- | --- |
| Reward policy | `reward_policies` and `services/reward_policy_service.py` | Active policy selected by product and optional sub-product; no rule-version snapshot yet. | Policy active flag and selected reward fields. |
| Reward decision/evidence | `rewards` and `services/reward_service.py`; legacy `referral_rewards` remains trace evidence. | `uq_rewards_base`, `uq_rewards_mission_bonus`, and reward service business key. | `rewards.status` values such as `APPLIED`, `EARNED`, `PENDING_FULFILMENT`, `FULFILLED`, `FAILED`, `REVERSED`. |
| Distributor commission rule | `distribution_commission_rules` and `services/distribution/commission_service.py` | Highest-priority active matching rule by tenant, sponsor, campaign, distributor type, and rule priority. | `rule_status`, currently active-rule driven. |
| Distributor commission decision/evidence | `distribution_commission_events` and `services/distribution/commission_service.py` | Unique `(tenant_code, source_event_id)` and `CommissionDuplicateEvent`. | `commission_status` values such as `CALCULATED` and `CREDITED`. |
| Outcome money trace | `services/outcome_trace_service.py` and `services/outcome_money_reconciliation_service.py` | Read-only aggregation and repair helpers; not a canonical money-decision table. | Separate reward, commission, funding, fulfilment, settlement, audit, and webhook evidence sections. |

## Decision

Reward and commission decisions must remain separate source families.

Future liability, funding, fulfilment, settlement, reporting, and operator views may aggregate them, but must preserve a typed boundary:

- `CUSTOMER_REWARD`: a reward decision for a referred customer/referee.
- `REFERRER_REWARD`: a reward decision for a referrer.
- `DISTRIBUTOR_COMMISSION`: a commission decision for a distributor.

These are money decision categories, not current database enum values. Current source statuses must remain inside their source sections until a later liability/state model maps them safely.

## Qualification Boundary

A reward or commission decision may be calculated or applied only after the caller can identify qualification evidence for the outcome scope.

Required qualification inputs:

- `tenant_code` resolved from trusted internal scope or credential-derived tenant scope;
- `referral_track_id` or a future canonical outcome reference;
- qualification decision evidence from the TASK-013 contract;
- event or campaign evidence sufficient for the requested money decision;
- product, sub-product, campaign, sponsor, participant, and distributor evidence where the policy/rule requires it.

Money decisions must not treat an existing reward row or commission event as proof that an outcome qualified. Those rows are downstream evidence.

## Reward Decision Boundary

Reward policy decisions are for referrer/customer rewards.

Canonical current inputs:

- `reward_policies.product`
- `reward_policies.sub_product`
- `reward_policies.reward_type`
- `reward_policies.referrer_reward_amount`
- `reward_policies.referee_reward_amount`
- `reward_policies.allow_referee_reward`
- referral outcome evidence such as `tenant_code`, `referral_track_id`, `product`, `sub_product`, `referrer_ucn`, and `referee_ucn`

Current output evidence:

- `rewards.tenant_code`
- `rewards.referral_track_id`
- `rewards.beneficiary_type`
- `rewards.beneficiary_ref`
- `rewards.product`
- `rewards.sub_product`
- `rewards.reward_type`
- `rewards.amount`
- `rewards.status`
- `rewards.reward_source`
- `rewards.mission_code`
- reward service `business_key`
- inserted or duplicate/no-op result

Rules:

- `REFERRER_REWARD` maps to `beneficiary_type = REFERRER`.
- `CUSTOMER_REWARD` maps to `beneficiary_type = REFEREE`.
- Reward issuance must preserve the current duplicate guards and service business-key behavior.
- A duplicate/no-op reward must remain observable and must not publish duplicate fulfilment side effects.
- Reward policy absence may block reward work even when the outcome is otherwise qualified.

## Distributor Commission Boundary

Distributor commission decisions are for distributor earnings. They are not customer/referrer rewards.

Canonical current inputs:

- `distribution_commission_rules.tenant_code`
- optional `sponsor_code`
- optional `campaign_code`
- optional `distributor_type`
- `commission_type`
- `rate`
- `fixed_amount`
- `min_commission`
- `max_commission`
- `currency`
- `priority`
- activity evidence such as `activity_type`, `sale_amount`, `source_event_id`, `correlation_id`, distributor, campaign, sponsor, and route/opportunity context

Current output evidence:

- `distribution_commission_events.commission_event_id`
- `tenant_code`
- `distributor_id`
- `distributor_code`
- `wallet_id`
- `rule_id`
- `sponsor_code`
- `campaign_code`
- `source_event_id`
- `activity_type`
- `sale_amount`
- `commission_amount`
- `currency`
- `commission_status`
- `credited_at`
- `correlation_id`
- metadata

Rules:

- `DISTRIBUTOR_COMMISSION` maps to `distribution_commission_events`.
- Commission calculation must preserve current active-rule matching and min/max/fixed/percentage/hybrid amount handling.
- Duplicate source events must not create duplicate commission events or wallet movements.
- Wallet crediting is a downstream effect of a commission decision, not the commission decision itself.

## Required Money Decision Shape

Future read/evaluate services should return money decisions with the following fields where source truth exists:

```json
{
  "decision_type": "REFERRER_REWARD",
  "tenant_code": "FNB",
  "outcome_ref": {
    "type": "REFERRAL_TRACK_ID",
    "value": "11111111-1111-4111-8111-111111111111"
  },
  "qualification": {
    "decision": "QUALIFIED",
    "reason_codes": ["COMPLETION_EVIDENCE_PRESENT"]
  },
  "policy_source": {
    "source": "reward_policies",
    "policy_ref": "42",
    "rule_version": null
  },
  "participant": {
    "type": "REFERRER",
    "safe_ref": "hash-or-internal-reference"
  },
  "amount": "100.00",
  "currency": "ZAR",
  "source_status": "APPLIED",
  "idempotency": {
    "business_key": "stable-reward-business-key",
    "source_event_id": null,
    "duplicate": false
  },
  "evidence": [],
  "missing_evidence": []
}
```

Service-level responses may use current snake_case source fields. Public or partner-facing APIs must use safe identifiers and must not expose raw UCNs, provider payloads, secrets, or unredacted metadata.

## Idempotency And Duplicate Protection

Money-affecting commands must be duplicate-safe before they mutate state:

- event ingestion dedupe must prevent duplicate downstream money side effects;
- reward application must use the current unique indexes and business-key behavior;
- commission calculation must use `(tenant_code, source_event_id)` or a future equivalent source identity;
- wallet, funding, fulfilment, settlement, and invoice side effects must preserve their own idempotency or state guards;
- duplicate/no-op outcomes should be explicit in service evidence and audit, not hidden as a normal new success.

## Funding, Fulfilment, Settlement, Audit, And Reporting Implications

Funding consumes reward and commission decisions as obligations. It must not infer qualification directly from event payloads.

Fulfilment consumes eligible reward or commission evidence according to the relevant source family. It must not collapse reward fulfilment and distributor wallet crediting into the same lifecycle.

Settlement consumes fulfilment, wallet, ledger, invoice, and exception evidence. It must preserve the original money decision category so reporting can distinguish customer/referrer reward cost from distributor commission cost.

Audit for future money commands must include tenant, actor/system source, target decision category, policy/rule source, amount, currency, idempotency or dedupe key, outcome reference, status, and safe reason codes.

Reporting and liability projection may total across categories only when the response preserves category-level subtotals and source evidence.

## Missing Evidence

Use the TASK-010 missing-evidence vocabulary where possible:

- `NO_SOURCE_EVIDENCE` when no reward, policy, commission, or rule source row exists.
- `JOIN_AMBIGUOUS` when commission, funding, fulfilment, or settlement evidence cannot be safely joined to the outcome.
- `SOURCE_CONFLICT` when source rows disagree on tenant, amount, status, participant, rule, or ownership.
- `REDACTED` when evidence exists but is hidden by role, privacy, or security policy.
- `NOT_APPLICABLE` when a decision category is proven irrelevant to the outcome type.

Reward policy absence may surface as `REWARD_POLICY_MISSING` from the TASK-013 qualification contract when the caller asks whether reward work can start.

## API Direction

Future reward/commission APIs should be explicit about whether they are reads or money-affecting commands.

Read/evaluate candidates:

```text
GET /admin/outcomes/{referral_track_id}/money-decisions?tenant_code=...
POST /admin/outcomes/{referral_track_id}/money-decisions/evaluate
```

Command candidates:

```text
POST /admin/outcomes/{referral_track_id}/rewards/apply
POST /admin/distribution/commissions/calculate
POST /admin/distribution/commissions/{commission_event_id}/credit-wallet
```

Contract rules:

- validate tenant access before returning source evidence;
- return `401` for missing or invalid credentials;
- return `403` for authenticated callers without tenant, route, or action scope;
- return `404` when the outcome, policy, rule, participant, or distributor is not found or inaccessible;
- return `409` for unsafe duplicate/conflict cases;
- return `200` or `201` with explicit duplicate/no-op metadata for safe idempotent outcomes;
- do not require idempotency keys for read-only trace/evaluate operations;
- require deterministic idempotency or source event identity for money-affecting commands.

## Backward Compatibility

Current tables, routes, statuses, and service behavior remain unchanged:

- `tenant_code` remains the internal tenant identifier.
- Existing reward and commission tables remain separate source truth.
- Existing outcome trace behavior continues to expose reward and commission sections separately.
- Existing public/partner surfaces must not be expanded with raw internal money evidence without a later safe-status contract.

## Non-Goals

TASK-014 does not implement a new policy engine, liability projection service, route, migration, rule-version table, persisted money decision table, fulfilment provider change, settlement change, wallet change, or reporting endpoint.

TASK-014 does not start TASK-015 liability state modeling or TASK-016 liability projection implementation.

## Follow-Up Implementation Tasks

- Implement reward/commission decision read/evaluate service over current source evidence.
- Add reward policy mapping tests for qualified, not qualified, missing policy, duplicate/no-op, and no-double-pay cases.
- Add commission rule mapping tests for active rule selection, precedence, duplicate source events, wallet credit separation, and no-double-pay cases.
- Add rule-version/evidence snapshot design only if later implementation requires persisted decisions.
- Use this boundary in TASK-015 liability state modeling before building liability projections.

## Validation Notes

Current schema and services are sufficient to define this boundary. They are not sufficient to provide persisted policy/rule version snapshots without a later schema task.

Readback validation for TASK-014 should confirm that rewards and commissions remain separate decision families, both require qualification evidence, duplicate protection is preserved, and funding/fulfilment/settlement/reporting implications do not collapse distinct money types.
