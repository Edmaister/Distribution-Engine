# Outcome Trace Response Contract

Status: Accepted for TASK-010 on 2026-06-22.

## Purpose

TASK-010 defines the backend response contract for tracing one distribution outcome across attribution, reward, commission, funding, fulfilment, settlement, audit, and webhook evidence.

This is a contract document only. It does not implement the aggregation service, add an API route, change migrations, add indexes, mutate money state, create repair actions, or verify live database joins.

## Source Documents And Code

- `docs/product/DLAAS_TARGET_STATE.md`
- `docs/sa/LIVE_CRITICAL_STATE_INVENTORY.md`
- `docs/sa/LINK_CODE_CONTRACT.md`
- `docs/sa/PARTICIPANT_TAXONOMY_PERMISSION_MAP.md`
- `docs/API_PERMISSION_MATRIX.md`
- `docs/sa/API_SURFACE_MAP.md`
- `docs/sa/CURRENT_STATE_MAP.md`
- `docs/sa/CAPABILITY_GAP_MATRIX.md`
- `docs/sa/STATE_MACHINE_MAP.md`
- `services/outcome_money_reconciliation_service.py`
- `services/progress_service.py`
- `services/reward_service.py`
- `services/distribution/commission_service.py`
- `services/funding/*`
- `services/marketplace_funding/*`
- `services/fulfilment/*`
- `services/partner_seam_service.py`
- `services/admin_audit_service.py`
- `dp/migrations/001_init.sql`
- `dp/migrations/002_campaigns.sql`
- `dp/migrations/013_progress_events.sql`
- `dp/migrations/014_campaign_referral_links.sql`
- `dp/migrations/035_add_fulfilment_audit.sql`
- `dp/migrations/037_phase_7_1_fulfilment_settlement_ledger.sql`
- `dp/migrations/041_funding_accounts_and_transactions.sql` through `dp/migrations/063_budget_governance.sql`
- `dp/migrations/066_distribution_commissions.sql`
- `dp/migrations/070_distribution_route_referral_links.sql`
- `dp/migrations/071_admin_audit_log.sql`
- `dp/migrations/077_partner_seam.sql`

## Contract Summary

Recommended future service name: `outcome_trace_service`.

Recommended first read-only service contract:

```text
get_outcome_trace(
  *,
  tenant_code: str,
  referral_track_id: str,
  identity: dict,
  include_sections: list[str] | None = None,
) -> OutcomeTrace
```

The first implementation should be lookup-by-`referral_track_id` because current schema and services use it as the referral outcome golden thread. Later implementations may add lookup by `campaign_track_id`, route link, external participant reference, or webhook/event correlation after those joins are validated.

## Current Golden Thread

| Evidence area | Current source truth | Current join candidate | Confidence |
| --- | --- | --- | --- |
| Outcome | `referral_instances` | `referral_track_id`, `tenant_code` | High |
| Campaign attribution | `campaign_referral_links`, `campaign_attributions`, `campaign_track_events` | `referral_track_id` to `campaign_track_id` | Medium |
| Link/code | `referrer_codes`, `campaign_referral_links`, `distribution_route_referral_links` | `referral_track_id`, `referrer_code_id`, `route_id` | Medium |
| Progress events | `referral_progress_events`, `enterprise_event_inbox` | `referral_track_id`, `tenant_code`, event keys | High for referral progress; medium for enterprise inbox |
| Reward | `referral_rewards`, `rewards` | `referral_track_id`, `reward_id`, `tenant_code` | Medium; two reward tables exist |
| Commission | `distribution_commission_events` | `source_event_id` or `correlation_id` matching `referral_track_id` | Medium |
| Funding | `funding_reservations`, `marketplace_funding_allocations`, sponsor wallet/ledger, funding contracts | `reward_id`, wallet/allocation correlation, tenant/sponsor | Low to medium |
| Fulfilment | `fulfilment_audit`, fulfilment services | `reward_id`, `referral_track_id`, `idempotency_key`, `correlation_id` | Medium |
| Settlement | `fulfilment_settlement_ledger`, settlement batches/exceptions/reversals/periods/certifications | `reward_id`, `settlement_id`, correlation fields | Medium |
| Audit | `admin_audit_log`, `referral_processing_audit`, fulfilment/funding/distribution audit tables | `tenant_code`, `target_id`, `correlation_id`, `referral_track_id` where present | Low to medium |
| Webhooks | `partner_webhook_deliveries`, `partner_webhook_subscriptions` | `tenant_code`, `event_type`, payload/correlation evidence | Low until event catalog is defined |

The response contract must keep these confidence levels visible. It must not hide a weak join by returning a normal-looking empty section without a missing-evidence reason.

## Required Response Envelope

Recommended service response:

```json
{
  "trace_id": "outcome:referral_track_id:11111111-1111-4111-8111-111111111111",
  "trace_type": "OUTCOME",
  "lookup": {
    "type": "REFERRAL_TRACK_ID",
    "value": "11111111-1111-4111-8111-111111111111"
  },
  "tenant_code": "FNB",
  "trace_completeness": "PARTIAL",
  "sections": {
    "outcome": {},
    "attribution": {},
    "participants": {},
    "events": {},
    "reward": {},
    "commission": {},
    "funding": {},
    "fulfilment": {},
    "settlement": {},
    "audit": {},
    "webhooks": {}
  },
  "missing_evidence": [],
  "source_warnings": [],
  "redactions": [],
  "generated_at": "ISO-8601 timestamp"
}
```

The API layer may use camelCase if the route family requires it. Service-level contracts should preserve current source field names in `evidence` blocks.

## Trace Completeness Values

These values describe the completeness of the trace response, not the business status of the outcome.

| Value | Meaning |
| --- | --- |
| `COMPLETE` | All requested sections have source evidence or a proven not-applicable reason. |
| `PARTIAL` | The outcome was found and at least one requested downstream section is missing or ambiguous. |
| `MISSING_EVIDENCE` | The outcome was found but core evidence required by the requested section is missing. |
| `INCONSISTENT` | Source evidence conflicts across tenant, identifier, amount, status, or ownership boundaries. |
| `UNAVAILABLE` | A section cannot be evaluated because the current implementation has no safe source or verified join. |

Business statuses must remain inside their source sections as current source values, such as referral status, reward status, commission status, fulfilment status, settlement status, or webhook delivery status.

## Required Sections

### Outcome

Source: `referral_instances`.

Required fields:

- `referral_track_id`
- `tenant_code`
- `status`
- `is_complete`
- `product`
- `sub_product`
- `journey_code`
- `created_at`
- `updated_at`
- `completed_at`
- safe source evidence

Do not expose raw referrer or referee UCN in public or partner/customer responses. Operator-only traces may include internal-sensitive fields only if the future route explicitly authorizes them.

### Attribution

Sources:

- `campaign_referral_links`
- `campaign_attributions`
- `campaign_track_events`
- `distribution_route_referral_links`
- `distribution_opportunities`
- `distribution_offer_routes`

Required fields where available:

- `campaign_code`
- `campaign_track_id`
- `route_id`
- `opportunity_id`
- `opportunity_code`
- `link_status`
- `source_type`
- `source_confidence`
- source timestamps

The response must distinguish no campaign attribution from unavailable campaign attribution. A missing `campaign_track_id` is not enough by itself to prove the outcome was unattributed.

### Participants

Sources:

- `referrer_codes`
- `referral_instances`
- `distribution_distributors`
- `distribution_opportunities`
- partner and sponsor/funding records where joined safely

Required fields where available:

- `participant_type`
- `source`
- `source_id`
- `safe_display_ref`
- `tenant_code`
- `sponsor_code`
- `distributor_code`
- `client_id` where webhook/client evidence is included

Raw UCN values, secret material, provider payloads, and token values must be redacted.

### Events

Sources:

- `referral_progress_events`
- `enterprise_event_inbox`
- `referral_processing_audit`
- campaign track events

Required fields where available:

- `event_type`
- `event_status`
- `source_system`
- `source_event_id`
- `dedupe_key` or idempotency evidence
- `occurred_at`
- `processed_at`
- `processing_status`
- `correlation_id`

Progress event dedupe and enterprise inbox idempotency should be shown as evidence, not as a new canonical event state in TASK-010.

### Reward

Sources:

- `referral_rewards`
- `rewards`
- `services/reward_service.py`

Required fields where available:

- `reward_id`
- `reward_type`
- `reward_source`
- `beneficiary_type`
- `beneficiary_ref`
- `amount`
- `currency`
- `status`
- `mission_code`
- `fulfilment event correlation`

The trace must not collapse `referral_rewards` and `rewards` into one table-shaped truth. It should list which source supplied each reward row.

### Commission

Sources:

- `distribution_commission_events`
- `distribution_commission_rules`
- distributor wallet records

Required fields where available:

- `commission_event_id`
- `distributor_id`
- `distributor_code`
- `rule_id`
- `source_event_id`
- `activity_type`
- `sale_amount`
- `commission_amount`
- `currency`
- `commission_status`
- `credited_at`
- `correlation_id`

Current joins use `source_event_id` or `correlation_id` matching the referral track ID. The contract must mark this as ambiguous unless a later implementation verifies the source event taxonomy.

### Funding

Sources:

- `funding_reservations`
- `funding_accounts`
- `funding_account_rules`
- `marketplace_funding_allocations`
- `sponsor_wallets`
- `sponsor_wallet_ledger`
- `funding_contracts`
- `funding_contract_ledger`

Required fields where available:

- `reservation_id` or allocation ID
- `account_id`
- `wallet_id`
- `contract_id`
- `sponsor_code`
- `reward_id`
- `amount`
- `currency`
- `status`
- `correlation_id`
- `source`

Funding is not always directly keyed by `referral_track_id`. The response must show whether evidence was joined through reward ID, wallet/allocation correlation, contract ledger, or was unavailable.

### Fulfilment

Sources:

- `fulfilment_audit`
- fulfilment idempotency/retry services
- provider status services

Required fields where available:

- `audit_id`
- `reward_id`
- `referral_track_id`
- `fulfilment_provider`
- `status`
- `idempotency_key`
- `provider_reference`
- `retry_count` or retry status where current source provides it
- `correlation_id`
- redacted provider metadata

Provider payloads and internal errors should be operator-only and redacted by default.

### Settlement

Sources:

- `fulfilment_settlement_ledger`
- `settlement_batches`
- `settlement_items`
- `settlement_approvals`
- `settlement_exceptions`
- `settlement_reversals`
- `settlement_periods`
- `settlement_certifications`
- `cross_border_settlements`

Required fields where available:

- `settlement_id`
- `batch_id`
- `reward_id`
- `audit_id`
- `status`
- `amount`
- `currency`
- `settlement_date`
- `exception_count`
- `reversal_count`
- `period_id`
- `certification_id`

Settlement evidence should preserve raw source status inside the section and use missing-evidence records for absent joins.

### Audit

Sources:

- `admin_audit_log`
- `referral_processing_audit`
- `fulfilment_audit`
- `funding_resolution_audit`
- `distribution_governance_audit`

Required fields where available:

- `audit_id`
- `action_domain`
- `action_type`
- `actor_role`
- `actor_tenant_code`
- `tenant_code`
- `target_type`
- `target_id`
- `correlation_id`
- `created_at`

The trace should show audit references and high-level action metadata. It should not expose full before/after payloads or sensitive metadata outside an operator-only route.

### Webhooks

Sources:

- `partner_webhook_subscriptions`
- `partner_webhook_deliveries`
- `partner_webhook_alert_notifications`

Required fields where available:

- `delivery_id`
- `webhook_id`
- `client_id`
- `event_type`
- `delivery_status`
- `attempt_count`
- `next_attempt_at`
- `delivered_at`
- `last_error` only in operator-safe form

TASK-010 does not define the DLaaS webhook event catalog. Until that catalog exists, webhook evidence should be matched only where event type and payload/correlation evidence are safe and explicit; otherwise return `JOIN_AMBIGUOUS`.

## Missing Evidence Contract

Each missing or ambiguous section must return structured evidence:

```json
{
  "section": "funding",
  "code": "JOIN_AMBIGUOUS",
  "severity": "WARNING",
  "message": "Funding evidence exists by reward/allocation, but no verified referral-track join is available.",
  "source": "marketplace_funding_allocations",
  "next_verification": "Verify reward_id to referral_track_id join in TASK-011 before implementation."
}
```

Canonical missing-evidence codes:

| Code | Use |
| --- | --- |
| `OUTCOME_NOT_FOUND` | No accessible `referral_instances` row exists for the lookup and tenant scope. |
| `TENANT_MISMATCH` | Source evidence exists but does not match the requested or identity-derived tenant. |
| `SECTION_NOT_REQUESTED` | Caller excluded an optional section. |
| `NO_SOURCE_EVIDENCE` | Source table was checked and no rows were found. |
| `JOIN_AMBIGUOUS` | Static code shows a possible join, but live/schema verification or taxonomy is still required. |
| `SOURCE_CONFLICT` | Two source rows disagree on tenant, amount, status, or ownership. |
| `SOURCE_UNAVAILABLE` | The repo does not currently expose a safe source for the requested section. |
| `REDACTED` | Evidence exists but is hidden by role, privacy, or security policy. |
| `NOT_APPLICABLE` | The section is proven irrelevant for the outcome type. |

## API And Auth Direction

Future read API direction:

```text
GET /admin/outcomes/{referral_track_id}/trace?tenant_code=FNB
```

This endpoint is not implemented by TASK-010.

Required future route rules:

- Read-only.
- Require an admin/operator helper appropriate to the route family.
- Validate tenant access before returning any source evidence.
- Return 400 for malformed identifiers or unsupported include sections.
- Return 401 for missing/invalid credentials.
- Return 403 for authenticated callers without tenant or route scope.
- Return 404 when the outcome is not found or inaccessible.
- Return 200 with `trace_completeness` and `missing_evidence` when the outcome exists but sections are incomplete.
- Do not require idempotency keys for reads.
- Do not expose raw UCNs, secrets, provider payloads, webhook signing material, or unrestricted audit metadata.

Partner/customer-safe traces must be separate contracts after safe status work. TASK-010 is an operator/backend trace contract.

## Idempotency, Retry, And Audit

The trace response is read-only and does not create idempotency records. It must display existing idempotency and retry evidence where available:

- progress dedupe keys
- enterprise inbox source event keys
- reward business keys where current service exposes them
- commission unique source event evidence
- fulfilment idempotency keys
- webhook delivery attempt counts and next attempt timestamps
- audit correlation IDs

Repair actions, retry commands, replay commands, fulfilment retries, settlement reversals, and payout changes are out of scope for TASK-010.

## Non-Goals

TASK-010 does not implement `outcome_trace_service`.

TASK-010 does not add an outcome trace API route.

TASK-010 does not start TASK-011 or any aggregation query implementation.

TASK-010 does not create a canonical outcome table, money table, webhook event catalog, participant table, or link/code table.

TASK-010 does not change reward, commission, funding, fulfilment, settlement, audit, webhook, auth, tenant, or data-isolation behavior.

TASK-010 does not add, rename, or remove schema fields.

TASK-010 does not verify live database joins or production data.

## Follow-Up Implementation Tasks

TASK-011 should:

- implement a read-only `outcome_trace_service`
- add contract fixture tests
- add broken-trail and missing-evidence tests
- add cross-tenant access tests
- verify each join against migrated test schema
- keep weak joins as `JOIN_AMBIGUOUS` until proven
- preserve all source statuses in their own sections

Later tasks should:

- define the webhook event catalog before broad webhook trace matching
- define partner/customer-safe outcome status contracts
- add liability projection over this trace contract
- add operator BFF/API contracts once trace and liability are implemented

## Validation Notes

This contract is based on static repository inspection only. No live database, production data, runtime credentials, schema drift check, or data verification was used.

Current source truth is sufficient to define a response contract and missing-evidence taxonomy. It is not sufficient to implement all joins without TASK-011 verification.

