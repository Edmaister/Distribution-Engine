# Live-Critical State, Identifier, And Idempotency Inventory

TASK ID: TASK-001

Linked enhancement: DLaaS-002: Platform state, idempotency, and live verification guardrails

Linked capabilities: 14. Audit trail; 28. Idempotency/retry handling; 30. Live DB/state verification

Scope: documentation-only inventory. No business logic, API, database schema, or frontend code was changed.

## Source Review

Confirmed source folders inspected:

- `dp/migrations/`
- `services/`
- `apps/api/routers/`
- `test/`
- `docs/sa/`
- `docs/roadmap/`

Confirmed path correction: migration files live under `dp/migrations/`; no `db/migrations` path was used.

Static inspection only: no live database connection was used for TASK-001.
TASK-027/TASK-028 later added local read-only verification evidence; staging and
production schema drift remain unknown until those environments are approved.

Local verification update, 2026-07-12:

- Local database `referrals` was inspected with strict read-only role
  `referral_readonly_verifier`.
- Local public base table count was 106 after applying migration 080 for
  onboarding draft persistence.
- Local protected read-only API smoke checks passed for health, OpenAPI, admin
  audit summary, admin failure summary, and admin funding dashboard.
- `funding_reconciliation_runs.correlation_id` was confirmed absent in the
  pre-081 local schema even though the funding reconciliation service reads/writes
  it. TASK-148 adds guarded additive migration 081 to resolve this on clean or
  updated schemas; pre-081 environments remain drifted until that migration is
  applied.
- Staging and production were not accessed.

## 1. State Fields Inventory

| Entity/table | Field | Confirmed states/defaults | Source of truth | Notes |
|---|---|---|---|---|
| `referral_instances` | `status` | `VALIDATED`, `UCN_CAPTURED`, `ACCOUNT_OPENED`, `ACCOUNT_ACTIVATED`, `FUNDED`, `COMPLETED`, `CANCELLED`; default originally `VALIDATED` | `dp/migrations/001_init.sql`; `dp/migrations/016_fix_referral_instances_status_constraint.sql`; `services/progress_service.py` | Migration history expands initial constraint. Current live constraint must be verified. |
| `referral_instances` | `is_complete` | boolean default `FALSE` | `dp/migrations/001_init.sql`; `services/progress_service.py` | Customer-safe completion view is derived from this plus timestamps/status. |
| `referral_progress_events` | `event_type` | `VALIDATED`, `UCN_CAPTURED`, `ACCOUNT_OPENED`, `ACCOUNT_ACTIVATED`, `FUNDED`, `DEBIT_ORDER_SWITCHED`, `SALARY_SWITCHED`, `FIRST_TRANSACTION_COMPLETED` | `dp/migrations/013_progress_events.sql`; `dp/migrations/017_fix_referral_progress_event_type_constraint.sql`; `services/progress_service.py` | Used as event history and idempotency source for progress ingestion. |
| `referral_event_failures` | `status` | default `OPEN`; service writes `RESOLVED`, `REPROCESSED` | `dp/migrations/020_referral_event_failures.sql`; `services/failure_admin_service.py`; `apps/api/routers/admin_failure.py`; TASK-027 local verification | No status check constraint found. Local values observed: `REPROCESSED`, `RESOLVED`. |
| `referral_processing_audit` | `processing_status` | comment says `PROCESSED`, `IGNORED`, `FAILED` | `dp/migrations/018_add_referral_processing_audit.sql`; TASK-027 local verification | Comment-only states; no check constraint found. Local values observed: `FAILED`, `IGNORED`, `PROCESSED`. |
| `marketing_campaigns` | `is_active` | boolean default `TRUE` | `dp/migrations/002_campaigns.sql`; `services/campaign_service.py` | Not a full campaign lifecycle state. |
| `marketing_campaign_policies` | `is_active` | boolean default `TRUE` | `dp/migrations/002_campaigns.sql`; `services/campaign_policy_service.py` | Policy lifecycle is boolean, not canonical version-state workflow. |
| `campaign_attributions` | `status` | `SCANNED`, `VALIDATED`, `ATTRIBUTED`, `COMPLETED`, `BLOCKED`, `EXPIRED`, `INVALID`; default `SCANNED` | `dp/migrations/002_campaigns.sql` | Attribution state source for campaign track. |
| `campaign_track_events` | `event_type` | unconstrained text observed | `dp/migrations/002_campaigns.sql` | Event stream exists, but event catalog is not constrained in schema. |
| `referral_qr_scans` | `status` | `SCANNED`, `VALIDATED`, `COMPLETED`, `BLOCKED`, `INVALID`, `EXPIRED`; default `SCANNED` | `dp/migrations/006_qr_scans.sql` | Telemetry/audit table. |
| `campaign_qr_scans` | `status` | `SCANNED`, `VALIDATED`, `ATTRIBUTED`, `COMPLETED`, `BLOCKED`, `INVALID`, `EXPIRED`; default `SCANNED` | `dp/migrations/008_campaign_qr_scans.sql` | Campaign scan telemetry. |
| `composite_scan_attempts` | `status` | `SCANNED`, `VALIDATED`, `INVALID`, `EXPIRED`, `BLOCKED`; default `SCANNED` | `dp/migrations/012_composit_scan_attempts.sql` | Filename spelling is `composit`; keep exact path until renamed intentionally. |
| `rewards` | `status` | local default `APPLIED`; service allows `APPLIED`, `EARNED`, `PENDING_FULFILMENT`, `FULFILLED`, `FAILED`, `REVERSED` | `dp/migrations/022_reward.sql`; `dp/migrations/034_reward_update.sql`; `services/reward_service.py`; TASK-027/TASK-028 local verification | Local DB has no status check constraint and current rows are `APPLIED`. Reward status remains service-governed. |
| `fulfilment_audit` | `status` | local default `PENDING`; service enum: `PENDING`, `PROCESSING`, `SUCCESS`, `FAILED_RETRYABLE`, `FAILED_FINAL`, `DLQ`, `SKIPPED_DUPLICATE` | `dp/migrations/035_add_fulfilment_audit.sql`; `services/fulfilment_status.py`; `services/fulfilment_audit_service.py`; `services/fulfilment/service.py`; TASK-027 local verification | No status check constraint found. Local value observed: `SUCCESS`. Admin dashboard counts all enum values. |
| `fulfilment_settlement_ledger` | `status` | `PENDING`, `PROCESSING`, `SETTLED`, `FAILED`, `REVERSED`, `DISPUTED`; default `PENDING` | `dp/migrations/037_phase_7_1_fulfilment_settlement_ledger.sql`; `services/fulfilment/settlement/status.py` | Has DB check constraint. |
| `settlement_batches` | `status` | service constants: `DRAFT`, `READY_FOR_APPROVAL`, `APPROVED`, `PROCESSING`, `SETTLED` | `dp/migrations/050_settlement_batches.sql`; `services/fulfilment/settlement/batches.py` | No DB check constraint found. |
| `settlement_batch_items` | `status` | service constants: `ADDED`, `SETTLED` | `dp/migrations/051_settlement_batch_items.sql`; `services/fulfilment/settlement/batches.py` | No DB check constraint found. |
| `settlement_approvals` | `approval_status` | `PENDING`, `APPROVED`, `REJECTED`; default `PENDING` | `dp/migrations/052_settlement_approvals.sql`; `services/fulfilment/settlement/approvals.py` | No DB check constraint found. |
| `settlement_exceptions` | `status` | `OPEN`, `RESOLVED`; default `OPEN` | `dp/migrations/053_settlement_exceptions.sql`; `services/fulfilment/settlement/exceptions.py` | No DB check constraint found. |
| `settlement_reversals` | `status` | `REQUESTED`, `APPROVED`, `EXECUTED`; default `REQUESTED` | `dp/migrations/054_settlement_reversals.sql`; `services/fulfilment/settlement/reversals.py` | No DB check constraint found. |
| `settlement_periods` | `status` | `OPEN`, `CLOSED`; default `OPEN` | `dp/migrations/055_settlement_period.sql`; `services/fulfilment/settlement/periods.py`; `services/fulfilment/settlement/lock_enforcement.py` | Closed periods block modifications in service logic. |
| `settlement_certifications` | `status` | default `PENDING`; service writes `CERTIFIED` | `dp/migrations/056_settlement_certification.sql`; `services/fulfilment/settlement/certifications.py` | No DB check constraint found. |
| `funding_accounts` | `status` | default `ACTIVE` | `dp/migrations/041_funding_accounts_and_transactions.sql`; `services/funding_service.py` | No DB check constraint found. |
| `funding_account_rules` | `is_active` | boolean default `TRUE` | `dp/migrations/043_create_funding_limits.sql`; `dp/migrations/045_funding_accounts.sql`; `services/funding/account_rules.py` | Rule activity is boolean. |
| `funding_limits` | `is_active` | boolean default `TRUE` | `dp/migrations/043_create_funding_limits.sql`; `services/funding/limits.py` | Limit activity is boolean. |
| `funding_reservations` | `status` | `RESERVED`, `RELEASED`, `SETTLED` | `dp/migrations/042_funding_reservations.sql`; `services/funding/reservations.py` | Has DB check constraint; release/settle updates only apply from `RESERVED`. |
| `funding_alerts` | `status` | service constants: `OPEN`, `ACKNOWLEDGED`, `RESOLVED`; default `OPEN` | `dp/migrations/047_funding_alerts.sql`; `services/funding/alerts.py` | No DB check constraint found. |
| `funding_reconciliation_runs` | `status` | service writes `MATCHED`, `EXCEPTION` | `dp/migrations/048_funding_reconciliation_runs.sql`; `dp/migrations/081_funding_reconciliation_run_correlation.sql`; `services/funding/reconciliation.py`; TASK-027/TASK-028/TASK-148 verification | Pre-081 local table had `status` but no rows and no `correlation_id`; TASK-148 adds the missing correlation evidence column and index for clean/updated schemas. |
| `funding_reconciliation_exceptions` | `status` | `OPEN`, `RESOLVED`; default `OPEN` | `dp/migrations/049_funding_reconciliation_exceptions.sql`; `services/funding/reconciliation.py` | No DB check constraint found. |
| `marketplace_funding_allocations` | `status` | `RESERVED`, `RELEASED`, `DEBITED`, `REVERSED`; default `RESERVED` | `dp/migrations/058_marketplace_funding_allocations.sql`; `services/marketplace_funding/sponsor_funding_service.py` | Has DB check constraint and unique `reward_id`. |
| `funding_contracts` | `status` | default `ACTIVE`; service/docs reference `ACTIVE`, `SUSPENDED`, `CANCELLED` | `dp/migrations/059_funding_contracts.sql`; `services/marketplace_funding/funding_contract_service.py` | No DB check constraint found. |
| `sponsor_wallets` | `status` | default `ACTIVE` | `dp/migrations/057_sponsor_wallets.sql`; `services/marketplace_funding/sponsor_wallet_service.py` | No DB check constraint found. |
| `sponsor_invoices` | `status` | default `DRAFT`; service issues and payment updates modify invoice state | `dp/migrations/062_sponsor_billing.sql`; `services/marketplace_funding/sponsor_billing_service.py` | Exact service state set needs deeper billing-specific task before money UX/API exposure. |
| `sponsor_payment_receipts` | `status` | default `UNAPPLIED` | `dp/migrations/062_sponsor_billing.sql`; `services/marketplace_funding/sponsor_billing_service.py` | No DB check constraint found. |
| `funding_budget_adjustment_requests` | `request_status` | `PENDING`, `APPROVED`, `REJECTED`; default `PENDING` | `dp/migrations/063_budget_governance.sql`; `services/marketplace_funding/budget_governance_service.py` | No DB check constraint found. |
| `funding_budget_transfer_requests` | `request_status` | `PENDING`, `APPROVED`, `REJECTED`; default `PENDING` | `dp/migrations/063_budget_governance.sql`; `services/marketplace_funding/budget_governance_service.py` | No DB check constraint found. |
| `funding_budget_exceptions` | `exception_status` | `OPEN`, `RESOLVED`, `WAIVED`; default `OPEN` | `dp/migrations/063_budget_governance.sql`; `services/marketplace_funding/budget_governance_service.py` | No DB check constraint found. |
| `funding_budget_approval_policies` | `policy_status` | `ACTIVE`; default `ACTIVE` | `dp/migrations/063_budget_governance.sql`; `services/marketplace_funding/budget_governance_service.py` | No DB check constraint found. |
| `enterprise_event_inbox` | `processing_status` | `RECEIVED`, `QUEUED`, `IGNORED`, `FAILED`, `DUPLICATE`; default `RECEIVED` | `dp/migrations/061_enterprise_event_inbox.sql`; `services/enterprise_event_inbox_service.py` | Has DB check constraint and unique `dedupe_key`. |
| `distribution_distributors` | `status` | `ONBOARDING`, `ACTIVE`, `SUSPENDED`, `TERMINATED`; default `ONBOARDING` | `dp/migrations/064_distribution_distributors.sql`; `services/distribution/distributor_service.py` | No DB check constraint found. |
| `distribution_distributor_wallets` | `status` | default `ACTIVE` | `dp/migrations/065_distribution_distributor_wallets.sql`; wallet services | No DB check constraint found. |
| `distribution_commission_rules` | `rule_status` | default `ACTIVE` | `dp/migrations/066_distribution_commissions.sql`; `services/distribution/commission_service.py` | No DB check constraint found. |
| `distribution_commission_events` | `commission_status` | `CALCULATED`, `CREDITED`; default `CALCULATED` | `dp/migrations/066_distribution_commissions.sql`; `services/distribution/commission_service.py` | No DB check constraint found; unique `(tenant_code, source_event_id)`. |
| `distribution_opportunities` | `opportunity_status` | `DRAFT`, `PUBLISHED`, `CLOSED`; default `DRAFT` | `dp/migrations/067_distribution_opportunities.sql`; `services/distribution/opportunity_service.py` | No DB check constraint found. |
| `distribution_offer_routes` | `route_status` | `ROUTED`, `ACCEPTED`, `DECLINED`; default `ROUTED` | `dp/migrations/068_distribution_offer_routes.sql`; `services/distribution/routing_service.py` | No DB check constraint found. |
| `distribution_compliance_reviews` | `review_status` | default `OPEN`; service likely resolves/updates | `dp/migrations/069_distribution_governance.sql`; distribution governance services | Exact closed statuses need focused governance pass. |
| `distribution_disputes` | `dispute_status` | default `OPEN`; service likely resolves/updates | `dp/migrations/069_distribution_governance.sql`; distribution governance services | Exact closed statuses need focused governance pass. |
| `distribution_route_referral_links` | `link_status` | `ACTIVE`, `VOIDED`; default `ACTIVE` | `dp/migrations/070_distribution_route_referral_links.sql` | Has DB check constraint. |
| `partner_clients` | `status` | `ACTIVE`, `SUSPENDED`, `REVOKED`; default `ACTIVE` | `dp/migrations/077_partner_seam.sql`; `services/partner_seam_service.py` | Has DB check constraint. |
| `partner_webhook_subscriptions` | `status` | `ACTIVE`, `PAUSED`, `REVOKED`; default `ACTIVE` | `dp/migrations/077_partner_seam.sql`; `services/partner_seam_service.py` | Has DB check constraint and HTTPS URL check. |
| `partner_webhook_deliveries` | `delivery_status` | `PENDING`, `SENT`, `FAILED`, `CANCELLED`; default `PENDING` | `dp/migrations/077_partner_seam.sql`; `services/partner_seam_service.py` | Has DB check constraint and retry fields. |
| `partner_webhook_alert_notifications` | `notification_status` | `QUEUED`, `SENT`, `FAILED`; default `SENT` | `dp/migrations/079_partner_webhook_alert_notifications.sql`; `services/partner_seam_service.py` | Has DB check constraint. |
| `admin_audit_log` | `action_status` | default `SUCCESS`; tests use `SUCCESS` | `dp/migrations/071_admin_audit_log.sql`; `services/admin_audit_service.py`; `test/test_admin_audit_service.py`; TASK-027 local verification | No DB check constraint found. Local values observed: `FAILED`, `SUCCESS`. |
| `privacy_erasure_audit` | `status` | `erased`, `not_found`, `blocked`, `failed` | `dp/migrations/032_privacy_tables.sql`; `services/privacy_service.py` | Has DB check constraint. |

## 2. Identifier Inventory

| Identifier | Type assumption from schema/code | Used by | Source |
|---|---|---|---|
| `tenant_code` | text internal platform tenant identifier | Most domain tables, auth, routes, funding, partner seam | `dp/migrations/*`; `utils/security.py`; services; TASK-048 decision keeps `tenant_code` internal and maps external references into it |
| `referrer_code_id` | UUID PK | `referrer_codes`, `referral_instances` FK | `dp/migrations/001_init.sql` |
| `referrer_ucn_hash` | text unique deterministic lookup | Referrer registry | `dp/migrations/001_init.sql` |
| `referral_code` | text unique share token | Referrer/customer validation | `dp/migrations/001_init.sql`; `services/referral_code.py` |
| `gaming_handle` | text unique public identity | Referrer display/leaderboards | `dp/migrations/001_init.sql` |
| `referral_track_id` | UUID PK/golden thread | Referral instances, progress, rewards, route referral links, fulfilment metadata | `dp/migrations/001_init.sql`; `dp/migrations/013_progress_events.sql`; `services/progress_service.py` |
| `campaign_code` | text PK/stable campaign identity | Marketing campaigns, policies, distribution opportunity link | `dp/migrations/002_campaigns.sql`; `services/campaign_service.py` |
| `campaign_id` | UUID unique surrogate | Marketing campaigns | `dp/migrations/002_campaigns.sql` |
| `campaign_track_id` | UUID PK/golden thread after campaign validation | Campaign attribution/event stream | `dp/migrations/002_campaigns.sql` |
| `reward_id` | mixed: UUID in `referral_rewards`; BIGSERIAL `id` in `rewards`; text in `funding_reservations.reward_id`; UUID in `fulfilment_settlement_ledger.reward_id` | Reward, fulfilment, funding, settlement | `dp/migrations/001_init.sql`; `dp/migrations/022_reward.sql`; `dp/migrations/042_funding_reservations.sql`; `dp/migrations/037_phase_7_1_fulfilment_settlement_ledger.sql`; `services/reward_service.py`; TASK-028 local verification |
| `rewards.id` | BIGSERIAL PK | Current reward service returns `id` | `dp/migrations/022_reward.sql`; `services/reward_service.py` |
| `business_key` | deterministic UUIDv5 string, not persisted directly by inspected reward insert | Reward event payload/idempotency evidence | `services/reward_service.py` |
| `audit_id` | UUID PK | Fulfilment audit, funding resolution audit, admin audit, distribution governance audit | `dp/migrations/035_add_fulfilment_audit.sql`; `046_funding_resolution_audit.sql`; `071_admin_audit_log.sql`; `069_distribution_governance.sql` |
| `settlement_id` | UUID PK | `fulfilment_settlement_ledger`, batch items, invoice lines | `dp/migrations/037_phase_7_1_fulfilment_settlement_ledger.sql`; `051_settlement_batch_items.sql`; `062_sponsor_billing.sql` |
| `batch_id`, `batch_item_id`, `approval_id`, `exception_id`, `reversal_id`, `period_id`, `certification_id` | UUID PKs | Settlement lifecycle | `dp/migrations/050_*` through `056_*` |
| `account_id`, `transaction_id`, `reservation_id`, `limit_id`, `audit_id`, `alert_id`, `run_id`, `exception_id` | UUID PKs | Funding engine | `dp/migrations/041_*` through `049_*` |
| `wallet_id`, `allocation_id`, `contract_id`, `ledger_id`, `invoice_id`, `line_id`, `payment_id`, `receipt_id` | UUID PKs | Marketplace funding/sponsor billing | `dp/migrations/057_*` through `063_*` |
| `sponsor_code` | text external sponsor identifier | Marketplace funding, opportunities, invoices | `dp/migrations/057_*`; `058_*`; `062_*`; `067_*` |
| `distributor_id` | UUID PK | Distribution distributor, routes, wallets, commissions, governance | `dp/migrations/064_distribution_distributors.sql` |
| `distributor_code` | text unique per tenant | Distribution distributor and wallet display | `dp/migrations/064_distribution_distributors.sql`; `065_distribution_distributor_wallets.sql` |
| `opportunity_id` | UUID PK | Distribution opportunity/routing/linking | `dp/migrations/067_distribution_opportunities.sql` |
| `opportunity_code` | text unique per tenant | Distribution opportunity external code | `dp/migrations/067_distribution_opportunities.sql` |
| `route_id` | UUID PK | Distribution offer route and route referral link | `dp/migrations/068_distribution_offer_routes.sql`; `070_distribution_route_referral_links.sql` |
| `commission_event_id`, `rule_id` | UUID PKs | Distribution commission event/rule | `dp/migrations/066_distribution_commissions.sql` |
| `source_event_id` | text source identifier | Progress, enterprise inbox, commission events, failures | `dp/migrations/013_progress_events.sql`; `020_referral_event_failures.sql`; `061_enterprise_event_inbox.sql`; `066_distribution_commissions.sql` |
| `dedupe_key` | text/hash unique key | Progress events, referral failures, enterprise event inbox | `dp/migrations/013_progress_events.sql`; `020_referral_event_failures.sql`; `061_enterprise_event_inbox.sql`; `services/progress_service.py` |
| `client_id` | text PK | Partner client credentials and webhooks | `dp/migrations/077_partner_seam.sql`; `services/partner_seam_service.py` |
| `token_id`, `webhook_id`, `delivery_id`, `notification_id` | UUID PKs | Partner access token, webhook subscription, delivery, alert notification | `dp/migrations/077_partner_seam.sql`; `079_partner_webhook_alert_notifications.sql` |
| `correlation_id` | text correlation/reference | Funding, fulfilment, settlement exceptions/reversals, enterprise inbox, webhooks, audit | Multiple migrations/services | Inconsistent type/semantics; needs platform standard. |

## 3. UUID/Text/Numeric ID Assumptions

Confirmed:

- Most new platform-domain primary keys are UUIDs generated by PostgreSQL `gen_random_uuid()` or Python `uuid4()`.
- Legacy/current reward service table `rewards` uses `id BIGSERIAL PRIMARY KEY`, while older `referral_rewards.reward_id` is UUID.
- `tenant_code`, `campaign_code`, `referral_code`, `distributor_code`, `opportunity_code`, `sponsor_code`, and `client_id` are text identifiers.
- Money fields are generally `NUMERIC(18,2)`; FX rates use `NUMERIC(20,8)`.

Assumptions requiring verification:

- Local runtime database may contain additional constraints or columns not
  represented by static migrations; staging and production remain unverified.
- `reward_id` is confirmed locally as not a single canonical type across all
  reward/money flows.
- `correlation_id` is not a guaranteed UUID; services use text and sometimes store reward IDs, audit IDs, or referral track IDs as correlation evidence.

## 4. Idempotency Key Inventory

| Flow | Key/source | Enforcement | Source | Notes |
|---|---|---|---|---|
| Progress ingestion | `dedupe_key` built from `source_system + source_event_id`, or fallback from `source_system + referral_track_id + event_type + occurred_at` | unique index `ux_progress_events_dedupe_key`; `ON CONFLICT DO NOTHING` | `dp/migrations/013_progress_events.sql`; `services/progress_service.py` | Also has unique `(source_system, source_event_id)` where source ID exists. |
| Progress event per referral/event type | `(referral_track_id, event_type)` | unique constraint `uq_rpe_track_event` | `dp/migrations/013_progress_events.sql` | Coexists with later dedupe key; live DB behavior needs verification if both constraints are present. |
| Referral failure capture | `(source_system, source_event_id)` and `dedupe_key` | unique constraints | `dp/migrations/020_referral_event_failures.sql` | Status lifecycle handled by admin failure service. |
| Enterprise event ingestion | `dedupe_key` | unique index `ux_enterprise_event_inbox_dedupe_key` | `dp/migrations/061_enterprise_event_inbox.sql`; `services/enterprise_event_inbox_service.py` | Inbox statuses include `DUPLICATE`. |
| Reward application | DB conflict on reward unique indexes; service derives `business_key` UUIDv5 | unique indexes in `dp/migrations/022_reward.sql`; `ON CONFLICT DO NOTHING` in service | `dp/migrations/022_reward.sql`; `services/reward_service.py` | Derived `business_key` is emitted in payload but not confirmed as persisted. |
| Fulfilment | `idempotency_key = tenant_code:referral_track_id:reward_type:beneficiary_ucn:journey_stage` | unique column on `fulfilment_audit.idempotency_key`; existing audit causes `SKIPPED_DUPLICATE` result | `dp/migrations/035_add_fulfilment_audit.sql`; `services/fulfilment_idempotency.py`; `services/fulfilment/service.py` | Critical no-double-fulfilment guard. |
| Funding reservation | `reward_id` | unique index `idx_funding_reservations_reward`; state-guarded release/settle | `dp/migrations/042_funding_reservations.sql`; `services/funding/reservations.py` | Prevents duplicate reservation per reward. |
| Marketplace funding allocation | `reward_id` | unique index `ux_marketplace_funding_allocations_reward` | `dp/migrations/058_marketplace_funding_allocations.sql` | Prevents duplicate sponsor allocation per reward. |
| Sponsor invoice line | `source_ledger_id` | unique partial index where source ledger exists | `dp/migrations/062_sponsor_billing.sql` | Prevents duplicate invoice lines from the same funding contract ledger row. |
| Distribution commission | `(tenant_code, source_event_id)` | unique constraint | `dp/migrations/066_distribution_commissions.sql`; `services/distribution/commission_service.py` | Protects duplicate commission for same source event when source ID exists. |
| Route referral link | `referral_track_id` | unique constraint `uq_distribution_route_referral` | `dp/migrations/070_distribution_route_referral_links.sql` | Prevents one referral track being linked to multiple routes. |
| Partner access token | `access_token_hash` | unique column | `dp/migrations/077_partner_seam.sql` | Credential uniqueness, not event idempotency. |
| Partner webhook delivery | `delivery_id` | UUID PK; retry updates existing delivery row | `dp/migrations/077_partner_seam.sql`; `services/partner_seam_service.py` | No content-level unique delivery idempotency found for repeated queueing of same event payload. |

## 5. Retry/Failure Fields

| Flow/table | Retry/failure fields | Confirmed behavior |
|---|---|---|
| `referral_event_failures` | `failure_category`, `failure_reason`, `status`, `retry_count`, `first_failed_at`, `last_failed_at`, `resolved_at`, `resolution_note`, `payload_json` | Admin can resolve or reprocess failures. Reprocessing only supports `REFERRAL_PROGRESS_RECORDED` payloads. |
| `enterprise_event_inbox` | `processing_status`, `processed_at`, `error_message`, `dedupe_key`, `normalized_payload` | Admin/service can replay if normalized payload exists; replay sets `processing_status = 'QUEUED'`. |
| `fulfilment_audit` | `attempt_no`, `max_attempts`, `failure_reason`, `error_code`, `provider_status`, `provider_response`, timestamps, `previous_status` | Fulfilment increments attempts, schedules retry when policy allows, writes failed status, and publishes to DLQ when retry exhausted. |
| Fulfilment retry metadata | `retry`, `source_audit_id`, `idempotency_key`, `attempt_no`, `max_attempts`, `next_retry_at`, `failure_reason` | Retry event metadata is built by `services/fulfilment_retry_scheduler_service.py`. |
| Fulfilment replay | replayable statuses `FAILED_RETRYABLE`, `FAILED_FINAL`, `DLQ` | Replay resets `fulfilment_audit.status` to `PENDING` and republishes fulfilment request. |
| `partner_webhook_deliveries` | `delivery_status`, `attempt_count`, `last_error`, `next_attempt_at`, `delivered_at` | Worker retries `PENDING`; max attempts `3`; backoff base `60` seconds; failure becomes `FAILED`. Admin/partner can requeue `FAILED`/`CANCELLED`. |
| `partner_webhook_alert_notifications` | `severity`, `channel`, `notification_status`, `metadata` | Alerts persist evidence for repeated failed/cancelled webhook delivery rows. |
| `funding_alerts` | `status`, `acknowledged_at`, `resolved_at`, `correlation_id` | Service constants confirm `OPEN`, `ACKNOWLEDGED`, `RESOLVED`. |
| `funding_reconciliation_exceptions` | `status`, `resolved_at`, `correlation_id`, expected/actual/variance amounts | Service resolves `OPEN` to `RESOLVED`. |
| `settlement_exceptions` | `status`, `severity`, `exception_message`, `correlation_id`, `resolved_at`, `resolved_by` | Service resolves `OPEN` to `RESOLVED`. |
| `settlement_reversals` | `status`, `reversal_reason`, `approved_at`, `executed_at`, `correlation_id` | Service moves `REQUESTED` to `APPROVED` to `EXECUTED`. |

## 6. Audit-Critical Tables/Events

Confirmed audit/evidence stores:

- `referral_processing_audit`: referral event processing evidence with previous/new status.
- `referral_event_failures`: event failure, reprocess, and resolution evidence.
- `referral_progress_events`: immutable-ish progress event evidence with dedupe keys.
- `campaign_track_events`: campaign attribution event stream.
- `fulfilment_audit`: fulfilment state, idempotency, provider, retry, failure, and replay anchor.
- `fulfilment_settlement_ledger`: settlement state and money evidence linked to reward and fulfilment audit.
- `funding_resolution_audit`: funding account/rule resolution evidence per reward.
- `funding_transactions`: money movement evidence for funding accounts.
- `funding_reservations`: reserved/released/settled funding obligation evidence.
- `funding_reconciliation_runs` and `funding_reconciliation_exceptions`: finance reconciliation evidence.
- `funding_alerts`: operational funding alert evidence.
- `sponsor_wallet_ledger`, `funding_contract_ledger`, `sponsor_invoice_*`: sponsor funding and billing evidence.
- `distribution_distributor_wallet_ledger`: distributor wallet movement evidence.
- `distribution_commission_events`: distributor commission liability/credit evidence.
- `distribution_governance_audit`: distributor governance/compliance/dispute action evidence.
- `enterprise_event_inbox`: external event ingestion, dedupe, replay, and error evidence.
- `partner_webhook_deliveries`: outbound webhook delivery evidence.
- `partner_webhook_alert_notifications`: webhook alert notification evidence.
- `admin_audit_log`: admin/operator action evidence.
- `privacy_erasure_audit`: privacy erasure action evidence.

Audit gaps confirmed from static inspection:

- There is no single canonical audit taxonomy across these tables.
- Several state fields are service-defined without DB check constraints.
- Some manual/retry actions write admin audit (`partner_webhook_delivery_retry`), but uniform audit coverage across all money/manual transitions is not yet confirmed.

## 7. Funding/Reward/Fulfilment/Settlement State Fields

| Area | Primary source fields | Money-safety notes |
|---|---|---|
| Reward | `rewards.status`, `reward_source`, `beneficiary_type`, `amount`, `reward_type`, `mission_code` | Service status set is wider than schema default. Reward ID type is inconsistent across old/new reward tables and funding references. |
| Funding account | `funding_accounts.status`, balances, `funding_transactions.transaction_type` | Balance integrity checks exist for current/reserved/available balances. Transaction type is unconstrained text. |
| Funding reservation | `funding_reservations.status`, `reward_id`, `amount`, `funding_transaction_id`, `correlation_id` | Reservation state is constrained and state-guarded. |
| Marketplace allocation | `marketplace_funding_allocations.status`, `reward_id`, `wallet_id`, timestamps | Allocation state is constrained and unique per reward. |
| Fulfilment | `fulfilment_audit.status`, `previous_status`, `attempt_no`, `max_attempts`, provider fields, `idempotency_key` | Strong idempotency and retry tracking, but schema has no check constraint on fulfilment status. |
| Settlement ledger | `fulfilment_settlement_ledger.status`, `reward_id`, `audit_id`, provider reference, timestamps, failure/reversal reason | Ledger status is constrained and tied to fulfilment audit. |
| Settlement batch | `settlement_batches.status`; `settlement_batch_items.status`; `settlement_approvals.approval_status` | Workflow states are service constants, not DB-enforced in inspected migrations. |
| Settlement exception/reversal/period/certification | exception `status`, reversal `status`, period `status`, certification `status` | Operational states exist; check constraints not found except ledger. |
| Sponsor billing | `sponsor_invoices.status`, `sponsor_payment_receipts.status`, invoice/payment/reversal/allocation tables | Sponsor billing is not SaaS platform billing; exact invoice state set needs focused verification before UI/API commitment. |
| Distribution commission | `distribution_commission_events.commission_status`, wallet ledger transaction type | Commission events have duplicate protection via `(tenant_code, source_event_id)` but no status constraint found. |

## 8. Backend Source-Of-Truth Files

Schema and migrations:

- `dp/migrations/001_init.sql`
- `dp/migrations/002_campaigns.sql`
- `dp/migrations/006_qr_scans.sql`
- `dp/migrations/008_campaign_qr_scans.sql`
- `dp/migrations/012_composit_scan_attempts.sql`
- `dp/migrations/013_progress_events.sql`
- `dp/migrations/016_fix_referral_instances_status_constraint.sql`
- `dp/migrations/017_fix_referral_progress_event_type_constraint.sql`
- `dp/migrations/018_add_referral_processing_audit.sql`
- `dp/migrations/020_referral_event_failures.sql`
- `dp/migrations/022_reward.sql`
- `dp/migrations/034_reward_update.sql`
- `dp/migrations/035_add_fulfilment_audit.sql`
- `dp/migrations/037_phase_7_1_fulfilment_settlement_ledger.sql`
- `dp/migrations/041_funding_accounts_and_transactions.sql`
- `dp/migrations/042_funding_reservations.sql`
- `dp/migrations/046_funding_resolution_audit.sql`
- `dp/migrations/047_funding_alerts.sql`
- `dp/migrations/048_funding_reconciliation_runs.sql`
- `dp/migrations/049_funding_reconciliation_exceptions.sql`
- `dp/migrations/050_settlement_batches.sql` through `dp/migrations/056_settlement_certification.sql`
- `dp/migrations/057_sponsor_wallets.sql` through `dp/migrations/063_budget_governance.sql`
- `dp/migrations/064_distribution_distributors.sql` through `dp/migrations/070_distribution_route_referral_links.sql`
- `dp/migrations/071_admin_audit_log.sql`
- `dp/migrations/077_partner_seam.sql`
- `dp/migrations/078_partner_webhook_signing_secret.sql`
- `dp/migrations/079_partner_webhook_alert_notifications.sql`

Services:

- `services/progress_service.py`
- `services/failure_admin_service.py`
- `services/reward_service.py`
- `services/fulfilment_status.py`
- `services/fulfilment_idempotency.py`
- `services/fulfilment/service.py`
- `services/fulfilment_audit_service.py`
- `services/fulfilment_retry_scheduler_service.py`
- `services/fulfilment_replay_service.py`
- `services/fulfilment/settlement/*.py`
- `services/funding/*.py`
- `services/marketplace_funding/*.py`
- `services/distribution/*.py`
- `services/enterprise_event_inbox_service.py`
- `services/partner_seam_service.py`
- `services/admin_audit_service.py`

Routers/tests:

- `apps/api/routers/progress.py`
- `apps/api/routers/enterprise_events.py`
- `apps/api/routers/admin_failure.py`
- `apps/api/routers/admin_fulfilment.py`
- `apps/api/routers/admin_finance.py`
- `apps/api/routers/admin_settlement*.py`
- `apps/api/routers/partner_seam.py`
- `apps/api/routers/distribution/*`
- `test/test_progress_api.py`
- `test/test_enterprise_events_api.py`
- `test/test_admin_failure.py`
- `test/test_admin_fulfilment.py`
- `test/test_reward_service.py`
- `test/test_fulfilment_*`
- `test/test_admin_settlement.py`
- `test/test_partner_seam_service.py`
- `test/test_distribution_attribution_journey_contract.py`
- `test/test_outcome_money_reconciliation_*`

## 9. Risks And Unknowns

Confirmed risks:

- Static migrations, services, and local runtime schema do not always agree.
  Example: local `rewards.status` defaults to `APPLIED` and has no status check
  constraint, while service accepts `APPLIED`, `EARNED`,
  `PENDING_FULFILMENT`, `FULFILLED`, `FAILED`, and `REVERSED`.
- Some migration files define state columns without DB check constraints, leaving actual allowed statuses service-governed.
- `funding_reconciliation_runs` service reads/writes `correlation_id`. Migration
  048 and the pre-081 local runtime schema did not define that column; TASK-148
  adds migration 081 to resolve the drift once applied.
- `reward_id` is not a single consistent type across `referral_rewards`,
  `rewards`, `funding_reservations`, and settlement references.
- `correlation_id` is important but not semantically standardized across event, reward, funding, fulfilment, settlement, webhook, and audit paths.
- Partner webhook retry has delivery-row idempotency, but no payload/event-level uniqueness was found for duplicate queueing.
- Sponsor billing state vocabulary needs a focused pass before exposing billing-grade SaaS or finance UX.
- Distribution governance status vocabulary needs a focused pass before exposing admin/customer safe status copy.

Unknowns requiring follow-up:

- Local live DB schema and constraints were inspected under TASK-027/TASK-028;
  staging and production remain uninspected.
- Whether all migrations replay cleanly in order was not verified in this task.
- Whether staging/production include additional columns/check constraints/indexes
  beyond static migrations is unknown.
- Whether `fulfilment_audit.status` can contain values outside service enum is
  not DB-enforced locally because no DB check constraint was found; staging and
  production remain unverified.
- Whether old `referral_rewards` is still actively used alongside `rewards` needs confirmation before canonical reward/liability work.
- Whether all manual repair/retry actions consistently write `admin_audit_log` needs an audit coverage task.

## 10. Follow-Up Tasks

Added to `docs/roadmap/ORDERED_TASK_LIST.md`:

- `TASK-027: Run live DB verification for TASK-001 inventory`
- `TASK-028: Resolve schema uncertainty from TASK-001 inventory`

These follow-ups exist because TASK-001 was intentionally static/doc-only and because live DB verification is required before money, settlement, webhook, or public API contracts rely on this inventory.
