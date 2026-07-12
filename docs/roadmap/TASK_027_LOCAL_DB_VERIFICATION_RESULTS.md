# TASK-027 Local DB Verification Results

Date: 2026-07-11

Status: Partial local verification recorded. Local migration alignment and
protected local API smoke checks are now verified. TASK-027 remains blocked for
full completion until strict read-only credentials or an explicit local
exception are available, and until any required non-local environment
verification is approved.

## Scope

This run verified the locally running database and locally running API only. It
did not access staging or production. No write, update, delete, repair, replay,
retry, fulfilment, settlement, funding, wallet, go-live, or money movement
operation was attempted.

The DB session was forced into read-only mode with
`default_transaction_read_only = on` before metadata and state queries were run.

## Environment Evidence

| Item | Result |
| --- | --- |
| Database connection | Connected |
| Database name | `referrals` |
| PostgreSQL family | PostgreSQL 18.3 |
| Public base table count | 106 |
| Verification transaction mode | `default_transaction_read_only = on` |
| DB role write posture | Current role can create in `public`; this is not a strict read-only DB role |
| Migration tracking table | Not found |
| App health route | `GET /health` returned 200 |
| OpenAPI route | `GET /openapi.json` returned 200 |

## Live-Critical Table Verification Summary

The initial broad local metadata pass checked 58 live-critical tables from the
TASK-001 inventory and adjacent onboarding work.

| Result | Count |
| --- | ---: |
| Checked tables | 58 |
| Present tables | 55 |
| Missing tables | 3 |

Initially missing local tables:

- `onboarding_drafts`
- `onboarding_draft_idempotency_keys`
- `onboarding_draft_audit_links`

These tables are expected by the onboarding draft persistence work. The local
database was brought forward by applying
`dp/migrations/080_onboarding_draft_persistence.sql`, then re-checked in a
read-only verification session.

Follow-up local verification confirmed all five onboarding draft persistence
tables now exist:

- `onboarding_drafts`
- `onboarding_draft_sections`
- `onboarding_draft_validation_results`
- `onboarding_draft_idempotency_keys`
- `onboarding_draft_audit_links`

Each onboarding draft persistence table had zero rows locally at verification
time. The expected state fields, check constraints, uniqueness constraints, and
lookup/idempotency/audit indexes were present.

| Table | State field | Local rows | Constraint/index evidence |
| --- | --- | ---: | --- |
| `onboarding_drafts` | `status` | 0 | `onboarding_drafts_status_chk`, `onboarding_drafts_draft_ref_key`, 9 indexes |
| `onboarding_draft_sections` | `section_status` | 0 | `onboarding_draft_sections_status_chk`, `onboarding_draft_sections_section_key_chk`, `onboarding_draft_sections_draft_section_key`, 6 indexes |
| `onboarding_draft_validation_results` | `validation_status` | 0 | `onboarding_draft_validation_results_status_chk`, `onboarding_draft_validation_results_type_chk`, 8 indexes |
| `onboarding_draft_idempotency_keys` | `result_status` | 0 | `onboarding_draft_idempotency_keys_status_chk`, `onboarding_draft_idempotency_keys_scope_key`, 9 indexes |
| `onboarding_draft_audit_links` | `action_status` | 0 | `onboarding_draft_audit_links_status_chk`, 11 indexes |

## Focused State And Constraint Evidence

| Table | State field | Live values observed | Constraint/idempotency evidence |
| --- | --- | --- | --- |
| `referral_instances` | `status` | `ACCOUNT_ACTIVATED`, `ACCOUNT_OPENED`, `COMPLETED`, `FUNDED`, `UCN_CAPTURED`, `VALIDATED` | `referral_instances_status_chk` present |
| `referral_progress_events` | `event_type` | `ACCOUNT_ACTIVATED`, `ACCOUNT_OPENED`, `DEBIT_ORDER_SWITCHED`, `FIRST_TRANSACTION_COMPLETED`, `FUNDED`, `SALARY_SWITCHED`, `UCN_CAPTURED` | `chk_rpe_event_type`, `ux_progress_events_source_event`, and `ux_progress_events_dedupe_key` present |
| `referral_event_failures` | `status` | `REPROCESSED`, `RESOLVED` | `uq_referral_event_failures_dedupe_key` and `uq_referral_event_failures_source_event` present; no status check constraint observed |
| `referral_processing_audit` | `processing_status` | `FAILED`, `IGNORED`, `PROCESSED` | No status check constraint observed |
| `marketing_campaigns` | `is_active` | `true` | Campaign date/count check constraints present |
| `campaign_attributions` | `status` | No rows observed | `campaign_attr_status_chk` present |
| `campaign_track_events` | `event_type` | No rows observed | Event type is service-governed; no check constraint observed |
| `rewards` | `status` | `APPLIED` | No status check constraint observed |
| `referral_rewards` | `status` | Field not present | Unique `(referral_track_id, reward_type)` evidence present |
| `fulfilment_audit` | `status` | `SUCCESS` | Unique `idempotency_key` evidence present; no status check constraint observed |
| `fulfilment_settlement_ledger` | `status` | `DISPUTED`, `FAILED`, `PENDING`, `PROCESSING`, `REVERSED`, `SETTLED` | `chk_fulfilment_settlement_status` present |
| `funding_reconciliation_runs` | `status` | No rows observed | `correlation_id` exists in local DB despite earlier static uncertainty |
| `enterprise_event_inbox` | `processing_status` | `IGNORED`, `QUEUED` | `enterprise_event_inbox_status_chk` and `ux_enterprise_event_inbox_dedupe_key` present |
| `partner_webhook_deliveries` | `delivery_status` | No rows observed | `partner_webhook_deliveries_status_chk` present |
| `admin_audit_log` | `action_status` | `FAILED`, `SUCCESS` | No action-status check constraint observed |

## Read-Only API Smoke Evidence

| Route | Result |
| --- | --- |
| `GET /health` | 200 |
| `GET /openapi.json` | 200 |
| `GET /admin/audit/summary` | 200 with local system-admin test key |
| `GET /admin/failures/summary` | Initially 500 after successful admin authentication; fixed by awaiting the async failure admin service in `apps/api/routers/admin_failure.py`; retest returned 200 with local admin test key |
| `GET /admin/failures/summary` without key | 401 |
| `GET /admin/funding/dashboard` | 200 with local finance-admin test key |

No mutating route was called.

The protected smoke pass used local built-in test keys only. No real secrets
were recorded.

## Drift And Blockers

1. Local DB role is not a strict read-only role. The session was forced
   read-only, but full TASK-027 completion should use a true read-only DB user
   or an explicitly approved local exception.
2. Local onboarding draft persistence migration alignment is resolved after
   applying `dp/migrations/080_onboarding_draft_persistence.sql`; staging and
   production still need environment-specific verification before this can be
   treated as broadly verified.
3. Protected local API smoke checks now pass for health, OpenAPI, audit summary,
   failure summary, and funding dashboard. The failure summary route required a
   narrow TASK-028 code fix because it was calling async service functions from
   a sync route handler.
4. No migration tracking table was found, so applied migration completeness must
   be inferred from table/column evidence unless the migration process records
   versions elsewhere.

## TASK-028 Routing

The local results create these TASK-028 follow-up decisions:

- Decide whether the local DB should be brought up to the latest migration chain
  before continuing onboarding review workflow verification. Locally, the
  onboarding draft persistence gap was resolved by applying migration 080 and
  verifying the five expected tables.
- Confirm whether `funding_reconciliation_runs.correlation_id` is now resolved
  as present for the local environment and update source documentation if this
  is accepted as verified local evidence.
- Keep service-governed status fields explicit where no DB check constraint
  exists, especially `rewards.status`, `fulfilment_audit.status`,
  `admin_audit_log.action_status`, `referral_event_failures.status`, and
  `referral_processing_audit.processing_status`.
- Treat the local protected API smoke gap as resolved after the TASK-028 route
  fix; repeat the same read-only smoke set in staging/production only with
  approved credentials and access.

## What Is Needed Next

To complete TASK-027 rather than partial local verification, provide or approve:

1. A strict read-only DB user/DSN for the local database, or explicit permission
   to treat the current local DB user as acceptable while forcing each session
   into read-only mode.
2. Confirmation that the local migration-alignment evidence is enough for the
   local environment, plus separate staging/production verification when those
   environments are in scope.
3. Approval to repeat the same read-only protected smoke routes outside local
   only when the target environment and credentials are approved.
