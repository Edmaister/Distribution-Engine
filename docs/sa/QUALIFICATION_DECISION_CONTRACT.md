# Qualification Decision Contract

Status: Accepted for TASK-013 on 2026-06-22.

## Purpose

TASK-013 defines how backend events, journey/progress definitions, campaign policies, and current source evidence produce a qualification decision.

This is a contract document only. It does not implement a qualification service, add an API route, change migrations, create rule-version storage, change reward issuance, mutate funding, alter fulfilment or settlement behavior, or rename current journey/campaign fields.

## Source Documents And Code

- `docs/product/DLAAS_TARGET_STATE.md`
- `docs/sa/CAMPAIGN_READINESS_SERVICE_CONTRACT.md`
- `docs/sa/EVENT_INGESTION_PUBLIC_CONTRACT.md`
- `docs/sa/OUTCOME_TRACE_RESPONSE_CONTRACT.md`
- `docs/sa/API_SURFACE_MAP.md`
- `docs/sa/CURRENT_STATE_MAP.md`
- `docs/sa/CAPABILITY_GAP_MATRIX.md`
- `docs/sa/STATE_MACHINE_MAP.md`
- `services/journey_definitions.py`
- `services/progress_definitions.py`
- `services/journey_orchestrator.py`
- `services/vertical_identifier_service.py`
- `services/campaign_policy_service.py`
- `services/reward_policy_service.py`
- `services/reward_service.py`
- `services/outcome_trace_service.py`
- `test/test_journey_orchestrator.py`
- `test/test_progress_service.py`
- `test/test_worker_ids_consumer.py`
- `test/test_lifecycle_e2e.py`

## Current Source Truth

| Area | Current source truth | Contract role |
| --- | --- | --- |
| Event acceptance | `referral_progress_events`, `enterprise_event_inbox`, TASK-012 | Confirms whether an event was accepted, ignored, duplicate, failed, or queued. |
| Journey rules | `services/journey_definitions.py` | Defines supported milestones, allowed transitions, completion events, and completion minimums. |
| Progress display | `services/progress_definitions.py` | Defines progress percent, progress band, display status, and next milestone. |
| Identifier requirements | `services/vertical_identifier_service.py` | Defines required customer/account/policy/order evidence by journey/event. |
| Referral state | `referral_instances` through `services/journey_orchestrator.py` | Holds current milestone, timestamps, completion flag, product, sub-product, and tenant scope. |
| Campaign readiness | TASK-007 and campaign services | Determines whether campaign/opportunity/link/funding context is ready enough for qualification. |
| Campaign policy | `services/campaign_policy_service.py` | Resolves effective policy/rules where campaign-scoped checks apply. |
| Reward policy | `services/reward_policy_service.py` and `services/reward_service.py` | Consumes completed outcomes later; not the qualification source itself. |
| Outcome trace | TASK-010/TASK-011 | Exposes qualification evidence and missing evidence to operators. |

Qualification must be treated as a derived decision over current evidence. It must not be inferred from a reward row alone.

## Contract Summary

Recommended future service name: `qualification_decision_service`.

Recommended first read/evaluate contract:

```text
evaluate_qualification(
  *,
  tenant_code: str,
  referral_track_id: str,
  event: dict | None = None,
  campaign_code: str | None = None,
  identity: dict | None = None,
  include_evidence: bool = True,
) -> QualificationDecision
```

The first implementation should be read/evaluate only. Persisted qualification decisions, rule-version snapshots, command idempotency, and audit writes should be separate implementation tasks.

## Decision Values

| Decision | Meaning | Current evidence |
| --- | --- | --- |
| `QUALIFIED` | The outcome has met journey completion requirements and campaign/policy checks required for this qualification scope. | `referral_instances.is_complete = true`, completion timestamps, valid processed event audit, campaign/readiness evidence where required. |
| `NOT_QUALIFIED` | The outcome exists but has not met required milestones or policy conditions. | Incomplete journey state, missing completion event, missing minimum milestone, inactive/expired campaign, or failed required policy check. |
| `PENDING` | The outcome is valid so far but waiting for more source events or evidence. | Current milestone is in progress, expected next milestone exists, no blocking invalid evidence. |
| `BLOCKED` | The outcome cannot qualify until a blocker is repaired or external state changes. | Tenant mismatch, campaign not ready, self-referral, exhausted campaign cap, missing required policy, missing source truth, or data inconsistency. |
| `INVALID` | The event or state transition is not valid for the journey/ruleset. | Unsupported event, invalid transition, out-of-order event that cannot be applied, backward event, malformed required identifiers. |

These are qualification decisions, not reward statuses, fulfilment statuses, settlement statuses, or webhook delivery statuses.

## Required Response Shape

Recommended service response:

```json
{
  "tenant_code": "FNB",
  "referral_track_id": "11111111-1111-4111-8111-111111111111",
  "campaign_code": "FNB-GOLD-SUMMER",
  "journey_code": "BANKING_TRANSACTIONAL",
  "journey_version": "v1",
  "decision": "PENDING",
  "can_start_reward": false,
  "current_milestone": "ACCOUNT_OPENED",
  "next_milestone": "ACCOUNT_ACTIVATED",
  "progress_percent": 40,
  "reasons": [],
  "blockers": [],
  "warnings": [],
  "evidence": {
    "referral": {},
    "events": {},
    "journey": {},
    "campaign": {},
    "policy": {},
    "audit": {}
  },
  "missing_evidence": [],
  "redactions": [],
  "evaluated_at": "ISO-8601 timestamp"
}
```

API responses may use camelCase if route conventions require it. Service-level contracts should preserve source field names in evidence blocks.

## Decision Rules

### `QUALIFIED`

The decision may be `QUALIFIED` only when all applicable checks pass:

- tenant scope matches the referral/outcome;
- journey code and version are supported;
- required identifier evidence exists for the qualifying event type;
- the current state satisfies the journey definition's completion rule;
- `referral_instances.is_complete` is true or can be derived true from current timestamps;
- the qualifying transition was processed, not ignored, duplicate-only, or failed;
- campaign readiness checks pass when the qualification is campaign-scoped;
- required campaign policy/rule checks pass where current source truth supports them.

For the current banking journey, completion requires the configured minimum milestone and at least one completion event from the journey definition. Current code uses `FUNDED` as the minimum for `BANKING_TRANSACTIONAL:v1` and treats `DEBIT_ORDER_SWITCHED`, `SALARY_SWITCHED`, or `FIRST_TRANSACTION_COMPLETED` as completion events.

### `NOT_QUALIFIED`

Use `NOT_QUALIFIED` when the outcome is accessible and valid but does not meet qualification criteria yet:

- journey has not reached required completion evidence;
- required completion event is absent;
- campaign is inactive, not started, expired, or cap-exhausted where that is a qualifying rule;
- effective campaign policy or product rule says the event does not qualify;
- reward policy is absent for the product, where the caller is asking whether the outcome can start reward work.

`NOT_QUALIFIED` should not be used for malformed events or unsafe state conflicts. Use `INVALID` or `BLOCKED` instead.

### `PENDING`

Use `PENDING` when the trail is valid and incomplete:

- current milestone has advanced but completion has not been reached;
- expected next milestone is known from `progress_definitions`;
- an accepted enterprise event is queued but not yet processed;
- an event is valid but asynchronous downstream evidence has not arrived;
- campaign/readiness evidence is sufficient to continue but optional evidence is still missing.

Pending outcomes must include next expected evidence when current source truth can provide it.

### `BLOCKED`

Use `BLOCKED` when qualification cannot proceed safely without repair, configuration, or an external state change:

- tenant mismatch or inaccessible referral;
- campaign/opportunity readiness blocker from TASK-007;
- self-referral;
- missing active campaign policy where policy is required;
- source rows disagree on tenant, campaign, journey, product, or ownership;
- required source table/evidence is unavailable;
- manual review, fraud, risk, or governance condition is present in current source truth.

Blocking decisions should include operator-safe remediation guidance, not raw internal payloads.

### `INVALID`

Use `INVALID` when the event/state input cannot be accepted as a valid qualification signal:

- unsupported event type for the journey;
- unsupported journey code/version;
- out-of-order transition that cannot be applied;
- backward transition;
- duplicate-only event when the caller asks whether this event newly qualifies the outcome;
- missing required identifiers for the event type;
- malformed referral track ID or required input.

The current orchestrator records invalid, duplicate, backward, out-of-order, and self-referral handling through processing audit and logs. Future qualification APIs should expose these safely.

## Reason Codes

| Code | Decision | Source | Meaning |
| --- | --- | --- | --- |
| `OUTCOME_NOT_FOUND` | `BLOCKED` or not-found API error | `referral_instances` | No accessible outcome exists for tenant/referral. |
| `TENANT_MISMATCH` | `BLOCKED` | Referral/campaign source | Source evidence is outside caller tenant scope. |
| `UNSUPPORTED_JOURNEY` | `INVALID` | Journey definitions | Journey code/version is not supported. |
| `UNSUPPORTED_EVENT` | `INVALID` | Journey definitions | Event is not valid for the journey. |
| `MISSING_IDENTIFIER` | `INVALID` | Identifier requirements | Required customer/account/policy/order evidence is missing. |
| `INVALID_TRANSITION` | `INVALID` | Journey orchestrator | Transition is invalid for the current milestone. |
| `OUT_OF_ORDER_EVENT` | `INVALID` | Journey orchestrator | Event arrived before prerequisite milestone. |
| `BACKWARD_EVENT` | `INVALID` | Journey orchestrator | Event tries to move state backwards. |
| `DUPLICATE_EVENT` | `PENDING` or `INVALID` | Dedupe/audit | Event was already recorded; no new qualification side effect. |
| `SELF_REFERRAL_NOT_ALLOWED` | `BLOCKED` | Progress/orchestrator | Referrer and referee identity conflict. |
| `JOURNEY_INCOMPLETE` | `NOT_QUALIFIED` or `PENDING` | Referral progress | Required completion evidence has not arrived. |
| `COMPLETION_EVIDENCE_PRESENT` | `QUALIFIED` | Referral progress | Completion event and minimum milestone are present. |
| `CAMPAIGN_NOT_READY` | `BLOCKED` or `NOT_QUALIFIED` | Campaign readiness | Required campaign/opportunity/link/funding readiness failed. |
| `POLICY_NOT_MATCHED` | `NOT_QUALIFIED` | Campaign policy | Effective policy exists but does not qualify this event/outcome. |
| `POLICY_UNAVAILABLE` | `BLOCKED` | Campaign policy | Required policy could not be resolved. |
| `REWARD_POLICY_MISSING` | `NOT_QUALIFIED` | Reward policy | Outcome may be complete, but no active reward policy can start reward work. |
| `SOURCE_CONFLICT` | `BLOCKED` | Any | Source rows disagree on tenant, identifier, product, journey, or ownership. |
| `SOURCE_UNAVAILABLE` | `BLOCKED` | Any | Current implementation cannot evaluate the required source safely. |

## Evidence Requirements

Qualification evidence should include source references, not raw sensitive payloads:

| Evidence family | Required safe fields |
| --- | --- |
| Referral | `referral_track_id`, `tenant_code`, `status`, `is_complete`, `journey_code`, `journey_version`, `product`, `sub_product`, timestamp presence flags. |
| Events | `event_type`, `source_system`, `source_event_id`, `dedupe_key`, `processing_status`, `occurred_at`, `processed_at`, `correlation_id`. |
| Journey | `current_milestone`, `next_milestone`, `completion_minimum_milestone`, `completion_events`, transition result. |
| Campaign | `campaign_code`, campaign readiness state, lifecycle/status, campaign track status where safely joined. |
| Policy | campaign policy version/rule summary where available; reward policy presence only when checking reward readiness. |
| Audit | processing audit references and safe reasons, not raw metadata payloads. |

Raw UCNs, raw account numbers, unrestricted `raw_payload`, provider payloads, secrets, tokens, and internal stack traces must be redacted.

## Relationship To Event Ingestion

TASK-012 defines whether an event was accepted, ignored, duplicate, failed, or queued. Qualification consumes that evidence:

- accepted/queued events may produce `PENDING`;
- processed valid events may produce `PENDING`, `NOT_QUALIFIED`, or `QUALIFIED`;
- ignored invalid transitions produce `INVALID`;
- ignored self-referral produces `BLOCKED`;
- duplicates are no-op evidence and must not create new rewards;
- failed events cannot be treated as qualification evidence until repaired/replayed.

## Relationship To Outcome Trace

Outcome trace should show qualification evidence in the `events`, `outcome`, `reward`, and `audit` sections. Missing or ambiguous qualification evidence should reuse the missing-evidence vocabulary from TASK-010 where possible:

- `NO_SOURCE_EVIDENCE`
- `JOIN_AMBIGUOUS`
- `SOURCE_CONFLICT`
- `SOURCE_UNAVAILABLE`
- `REDACTED`

Qualification should not require a new canonical outcome table before the read/evaluate service can be implemented.

## Relationship To Rewards And Funding

Rewards, commissions, funding reservations, fulfilment, and settlement must start from explainable qualification evidence.

Current reward behavior starts base reward issuance when a referral newly becomes complete. Future reward-policy work should depend on this contract rather than treating reward application as the qualification decision itself.

Funding and fulfilment should consume reward/liability evidence after qualification and reward decisions have been made. They should not independently infer qualification from event payloads.

## API Direction

Future internal/operator route direction:

```text
GET /admin/outcomes/{referral_track_id}/qualification?tenant_code=...
POST /admin/outcomes/{referral_track_id}/qualification/evaluate
```

Future public/partner diagnostics, if allowed, must be a reduced safe view.

API requirements:

- read/evaluate operations must be tenant-scoped and authorized;
- reads are idempotent and do not require idempotency keys;
- persisted decisions or manual overrides require audit and idempotency before implementation;
- return 400 for invalid filters or unsupported operations;
- return 401/403 for missing or insufficient auth;
- return 404 for missing or inaccessible outcomes;
- return 200 with decision details for accessible outcomes, including `PENDING`, `NOT_QUALIFIED`, `BLOCKED`, or `INVALID`;
- do not expose raw identifiers, raw payloads, provider responses, or secrets.

## Non-Goals

TASK-013 does not implement `qualification_decision_service`.

TASK-013 does not add qualification API routes.

TASK-013 does not add schema for persisted decisions, rule versions, evidence snapshots, or audit rows.

TASK-013 does not change journey definitions, campaign policy behavior, reward policy behavior, reward issuance, funding, fulfilment, settlement, webhooks, auth, tenant scope, or data isolation.

TASK-013 does not start TASK-014 reward/commission policy boundary work.

## Follow-Up Implementation Tasks

- Implement a read-only qualification decision service over current referral, event, journey, campaign, and policy evidence.
- Add tests for `QUALIFIED`, `NOT_QUALIFIED`, `PENDING`, `BLOCKED`, and `INVALID`.
- Add tenant-scope and privacy tests.
- Add rule-version/evidence snapshot design only if persisted decisions become required.
- Align TASK-014 reward/commission policy boundary to require qualification evidence before money decisions.
- Add operator API/BFF contracts after permission matrix work defines the route family.

## Validation Notes

This contract is based on static repository inspection only. No live database, production data, runtime credentials, schema drift check, or data verification was used.

Current source truth is sufficient to define qualification decision values, reason codes, and evidence boundaries. It is not sufficient to implement persisted rule-version evidence without a later schema task.
