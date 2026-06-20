# Live DB/State Verification Checklist

TASK ID: TASK-003

Linked enhancement: DLaaS-002: Platform state, idempotency, and live verification guardrails

Linked capability: 30. Live DB/state verification

Status: Checklist/procedure only. Do not run live verification from this task.

## 1. Purpose

Live DB/state verification exists because static migrations, service code, tests, and deployed databases can drift. DLaaS depends on backend truth for rewards, funding, fulfilment, settlement, webhooks, audit, and user-visible status. A frontend, public API, operator repair action, or money report must not rely on unverified assumptions.

This checklist defines a repeatable, read-only process for verifying live-critical state in local, staging, and production-like environments. It supports DLaaS correctness by proving that deployed schema, state fields, identifiers, idempotency keys, retry fields, and audit evidence match the source-of-truth inventory in `docs/sa/LIVE_CRITICAL_STATE_INVENTORY.md`.

This checklist unblocks `TASK-027: Run live DB verification for TASK-001 inventory`. `TASK-027` should execute this checklist and record evidence. `TASK-028` should resolve confirmed mismatches.

## 2. Scope

Verify these live-critical areas:

- Referral states: `referral_instances`, `referral_progress_events`, `referral_event_failures`, referral audit evidence.
- Campaign tracking states: `marketing_campaigns`, `campaign_attributions`, `campaign_track_events`, QR/composite scan tables.
- Reward states: `rewards`, `referral_rewards` if present, reward policies, reward summary evidence.
- Funding states: funding accounts, rules, reservations, exposure, alerts, reconciliation, sponsor wallets, allocations, contracts, budget governance.
- Fulfilment states: `fulfilment_audit`, fulfilment policies, provider health, retry/replay fields.
- Settlement states: settlement ledger, batches, items, approvals, exceptions, reversals, periods, certifications.
- Webhook delivery states: partner clients, access tokens, webhook subscriptions, deliveries, alert notifications.
- Audit events: admin audit, referral processing audit, fulfilment audit, funding resolution audit, governance audit, privacy audit.
- Idempotency keys: dedupe keys, source event IDs, fulfilment idempotency keys, reward/funding uniqueness, webhook delivery IDs.
- Retry/failure fields: attempt counts, retry counts, failure reasons, error codes, next attempt timestamps, DLQ/replay evidence.
- Identifier types: UUID, text, numeric, BIGSERIAL, correlation IDs, external codes.

## 3. Environment Gates

| Environment | Allowed purpose | Access requirement | Data rule | Approval requirement |
|---|---|---|---|---|
| Local | Migration replay, schema inspection, seeded smoke tests, checklist dry run | Local dev DB or disposable container only | Seed/test data only | No production approval required |
| Staging | Read-only verification against deployed-like schema and seeded/synthetic tenant data | Read-only DB role and non-production API keys | Use seeded test tenant/correlation IDs only | Team approval required before running mutating smoke routes |
| Production | Emergency/read-only drift verification only | Read-only DB role, explicit scoped credentials, audited session | Redacted metadata only; no customer identifiers or secrets in evidence | Written human approval required before any access |

Required environment variables or credentials must be discovered from repo docs or deployment configuration before TASK-027 runs. Do not invent connection names. Record only variable names, never secret values.

Minimum access rules:

- DB role must be read-only for schema and data checks.
- API keys must be the narrowest role required for the smoke route.
- Production access must be approved before connection.
- Production smoke tests must be read-only routes only.
- Staging/local mutating smoke tests require isolated seeded test data and explicit correlation IDs.

Data redaction rules:

- Redact UCNs, account numbers, customer identifiers, access tokens, webhook signing secrets, client secrets, raw payloads, and provider responses.
- Keep only table names, column names, counts, statuses, timestamps, correlation IDs generated for the test, and truncated IDs where needed.
- Evidence must not include full customer payloads, secrets, or raw production records.

## 4. Safety Rules

- Use read-only queries by default.
- Do not write, update, delete, truncate, repair, reprocess, replay, settle, approve, reverse, fulfil, or retry anything during schema verification.
- Do not run destructive commands.
- Do not run manual data repair.
- Do not make production changes.
- Do not make schema changes.
- Do not expose secrets or customer data.
- Redact all captured evidence.
- Stop immediately if the current database user can write in production.
- Stop immediately if the query result contains unredacted sensitive data.
- Any mutating smoke route is local/staging only and must use seeded test data.

## 5. Schema Verification Checklist

For each table named in `docs/sa/LIVE_CRITICAL_STATE_INVENTORY.md`:

- Confirm the actual table exists in the target schema.
- Confirm actual column names.
- Confirm column types.
- Confirm nullable versus non-nullable fields.
- Confirm default values.
- Confirm enum/check constraints where present.
- Confirm indexes.
- Confirm unique constraints.
- Confirm foreign keys.
- Confirm UUID/text/numeric/BIGSERIAL identifier types.
- Confirm timestamp/time zone types for event, audit, retry, and settlement fields.
- Compare live schema to `dp/migrations/*`.
- Record any migration drift.
- Record whether drift affects money, audit, idempotency, retry, or customer-visible state.

Minimum schema areas:

- Referral: `referrer_codes`, `referral_instances`, `referral_progress_events`, `referral_event_failures`, `referral_processing_audit`.
- Campaign: `marketing_campaigns`, `marketing_campaign_policies`, `campaign_attributions`, `campaign_track_events`, scan tables.
- Reward: `rewards`, `referral_rewards`, reward policy tables if present.
- Funding: `funding_accounts`, `funding_transactions`, `funding_reservations`, `funding_resolution_audit`, `funding_alerts`, reconciliation tables, sponsor wallet/contract/billing/budget tables.
- Fulfilment/settlement: `fulfilment_audit`, `fulfilment_settlement_ledger`, settlement lifecycle tables.
- Distribution: distributor, opportunity, route, link, commission, wallet, governance tables.
- Webhooks: `partner_clients`, `partner_access_tokens`, `partner_webhook_subscriptions`, `partner_webhook_deliveries`, `partner_webhook_alert_notifications`.
- Audit: `admin_audit_log`, domain audit tables, privacy audit tables.

## 6. State Verification Checklist

For each state field in the TASK-001 inventory:

- Confirm the state field exists.
- Confirm current distinct values in the environment using only redacted/count output.
- Confirm whether allowed values are DB-constrained or service-governed.
- Confirm service-governed states against the service constants listed in TASK-001.
- Confirm reward/funding/fulfilment/settlement logic uses the same fields.
- Confirm states exposed to users/operators through read APIs.
- Confirm states requiring audit events.
- Confirm states requiring retries or idempotency.
- Confirm unknown/unexpected values are absent or documented.

Important state families:

- Referral: `referral_instances.status`, `referral_progress_events.event_type`, `referral_event_failures.status`.
- Campaign: `campaign_attributions.status`, scan statuses, campaign/event stream types.
- Reward: `rewards.status`; compare schema default to service-allowed states.
- Funding: reservation, allocation, alert, reconciliation, budget governance, contract, wallet, invoice/receipt statuses.
- Fulfilment: `fulfilment_audit.status`, attempts, failures, replayable statuses.
- Settlement: settlement ledger, batch, item, approval, exception, reversal, period, certification statuses.
- Webhooks: client/subscription/delivery/notification statuses.
- Audit: `admin_audit_log.action_status` and domain audit action/state fields.

## 7. Idempotency And Retry Verification Checklist

Verify:

- Idempotency key fields exist.
- Uniqueness constraints or indexes exist.
- Duplicate event behavior is known for progress, enterprise inbox, reward, fulfilment, funding, commission, route links, and webhooks.
- Replay-safe operations are documented before being exercised.
- Retry counters exist where expected.
- Failure reasons and error codes exist where expected.
- Webhook retry behavior uses `delivery_status`, `attempt_count`, `next_attempt_at`, `last_error`, and `delivered_at`.
- Fulfilment retry behavior uses `fulfilment_audit.idempotency_key`, `attempt_no`, `max_attempts`, `failure_reason`, `error_code`, and replay metadata.
- Settlement retry/repair behavior is represented by exceptions/reversals/approval state rather than hidden retries unless code says otherwise.
- Funding reservation uniqueness is enforced by reward-level uniqueness and state-guarded transitions.

Do not execute retry/replay actions in production. In staging/local, retries must use seeded test records and explicit correlation IDs.

## 8. Audit Verification Checklist

Verify:

- Audit tables exist.
- Audit event/action fields exist.
- Money-impacting transitions write audit evidence where code claims they do.
- Manual repair events are auditable.
- Admin/operator actions are auditable.
- Before/after state capture exists where present in schema or services.
- Correlation IDs or trace IDs exist and can link event, reward, funding, fulfilment, settlement, webhook, and audit records.
- Audit queries can be filtered by tenant, target type, target ID, action domain, action type, or correlation ID where supported.
- Audit evidence can be exported/redacted safely.

Audit-critical examples from current code:

- `/admin/audit` and `/admin/audit/summary` read `admin_audit_log`.
- Enterprise event replay writes admin audit in `apps/api/routers/admin_enterprise_events.py`.
- Partner webhook retry writes admin audit in `services/partner_seam_service.py`.
- Distribution distributor/opportunity lifecycle routes write admin audit in distribution admin routers.

## 9. Smoke-Test Route Selection Method

Do not invent routes. Select smoke-test routes from actual router files and classify each route before execution.

Selection rules:

- Prefer read-only `GET` routes for production.
- Use `POST`, `PUT`, `PATCH`, `DELETE`, replay, retry, approve, resolve, repair, issue, fulfil, settle, reverse, or process routes only in local/staging with seeded test data.
- For production, any route expected to write audit evidence or change state is not a smoke route unless separately approved as an incident procedure.
- Every selected route must declare auth, safe environment, expected DB/state change, expected audit event, and seeded-data requirement.

Candidate route matrix from current router files:

| Route/path | Method | Purpose | Auth requirement | Safe environment | Expected DB/state change | Expected audit event | Seeded test data needed |
|---|---|---|---|---|---|---|---|
| `/admin/audit/summary` | GET | Read admin audit summary | system admin key | local/staging/production read-only | None | None | No |
| `/admin/audit` | GET | Read admin audit rows | system admin key | local/staging/production read-only | None | None | No, but use filters |
| `/admin/enterprise-events/summary` | GET | Read enterprise inbox status counts | system admin key | local/staging/production read-only | None | None | No |
| `/admin/enterprise-events/dashboard` | GET | Read inbox dashboard and problem events | system admin key | local/staging/production read-only | None | None | No |
| `/admin/enterprise-events` | GET | List enterprise inbox records | system admin key | local/staging/production read-only | None | None | Optional test correlation/filter |
| `/admin/enterprise-events/{inbox_event_id}/replay?dryRun=true` | POST | Dry-run replayability check | system admin key | local/staging only by default; production only with explicit approval | No queue write if `dryRun=true`; route may write admin audit | `ENTERPRISE_EVENT_REPLAY` admin audit | Yes |
| `/admin/failures/summary` | GET | Read referral failure summary | admin key | local/staging/production read-only | None | None | No |
| `/admin/failures` | GET | List referral event failures | admin key | local/staging/production read-only | None | None | Optional test filter |
| `/admin/fulfilment/dashboard` | GET | Read fulfilment status counts | admin key | local/staging/production read-only | None | None | No |
| `/admin/fulfilment/failures` | GET | List failed fulfilment audit rows | admin key | local/staging/production read-only | None | None | Optional tenant filter |
| `/admin/fulfilment/audit/{audit_id}` | GET | Read one fulfilment audit row | admin key | local/staging/production read-only | None | None | Yes |
| `/admin/fulfilment/replay/{audit_id}` | POST | Replay failed fulfilment | admin key | local/staging only | Changes fulfilment audit/event queue | Fulfilment replay evidence; audit coverage must be verified | Yes |
| `/admin/funding/dashboard` | GET | Read funding summary | finance admin key | local/staging/production read-only | None | None | No |
| `/admin/funding/exposure` | GET | Read funding exposure | finance admin key | local/staging/production read-only | None | None | Optional filters |
| `/admin/funding/limits` | GET | Read funding limits | finance admin key | local/staging/production read-only | None | None | Optional filters |
| `/admin/funding/reconciliation` | GET | Read funding reconciliation runs | finance admin key | local/staging/production read-only | None | None | Optional filters |
| `/admin/funding/reconciliation/exceptions` | GET | Read funding reconciliation exceptions | finance admin key | local/staging/production read-only | None | None | Optional filters |
| `/admin/funding/reconciliation/run` | POST | Run funding reconciliation | finance admin key | local/staging only | Creates run and maybe exception rows | Audit coverage must be verified | Yes |
| `/admin/finance/outcome-money-map` | GET | Read outcome-money evidence map | finance admin key | local/staging/production read-only | None | None | Optional tenant/filter |
| `/admin/finance/reconciliation/metrics` | GET | Read finance reconciliation metrics | finance admin key | local/staging/production read-only | None | None | No |
| `/admin/settlements` | GET | List settlement ledger records | finance admin key | local/staging/production read-only | None | None | Optional filters |
| `/admin/settlements/exposure` | GET | Read settlement exposure | finance admin key | local/staging/production read-only | None | None | Optional filters |
| `/admin/settlement/batches` | GET | List settlement batches | finance admin key | local/staging/production read-only | None | None | Optional filters |
| `/admin/settlement/exceptions` | GET | List settlement exceptions | finance admin key | local/staging/production read-only | None | None | Optional filters |
| `/admin/partners/readiness` | GET | Read partner seam readiness | system admin key | local/staging/production read-only | None | None | No |
| `/admin/partners/webhook-deliveries` | GET | List webhook deliveries | system admin key | local/staging/production read-only | None | None | Optional filters |
| `/admin/partners/webhook-deliveries/summary` | GET | Read webhook delivery summary | system admin key | local/staging/production read-only | None | None | No |
| `/admin/partners/webhook-deliveries/{delivery_id}/retry` | POST | Requeue failed/cancelled webhook delivery | system admin key | local/staging only | Sets delivery to `PENDING`, clears error/next attempt | `PARTNER_WEBHOOK_DELIVERY_RETRY` admin audit | Yes |
| `/v1/progress` | POST | Ingest progress event | partner key | local/staging only | Inserts progress event or dedupes; may enqueue event | Event/audit path must be verified | Yes |
| `/enterprise/events` | POST | Ingest enterprise event | admin or partner key | local/staging only | Writes enterprise inbox/queue path | Event/audit path must be verified | Yes |
| `/admin/distribution/reporting/overview` | GET | Read distribution marketplace overview | distribution admin key | local/staging/production read-only | None | None | Tenant filter required |
| `/admin/distribution/distributors` | GET | List distributors | distribution admin key | local/staging/production read-only | None | None | Tenant filter required |
| `/admin/distribution/opportunities` | GET | List opportunities | distribution admin key | local/staging/production read-only | None | None | Tenant filter required |

TASK-027 may add more route candidates after inspecting the active router registration in `apps/api/main.py`. It must not execute routes that are not mounted in the running app.

## 10. Event-By-Event Verification Template

Use this template during TASK-027:

```text
Event:
Trigger/action:
Environment:
Correlation ID:
Tenant/test scope:
Expected API response:
Expected DB table changes:
Expected state transition:
Expected audit event:
Expected idempotency behavior:
Expected retry behavior:
Evidence captured:
Pass/Fail:
Notes:
```

## 11. Query Templates

Use placeholders only. Do not include real secrets or customer data. Adjust schema names if the environment uses a non-default schema.

Inspect table structure:

```sql
SELECT
  table_schema,
  table_name,
  column_name,
  data_type,
  udt_name,
  is_nullable,
  column_default
FROM information_schema.columns
WHERE table_schema = '<schema>'
  AND table_name = '<table_name>'
ORDER BY ordinal_position;
```

Check constraints:

```sql
SELECT
  conname,
  contype,
  pg_get_constraintdef(oid) AS definition
FROM pg_constraint
WHERE conrelid = '<schema>.<table_name>'::regclass
ORDER BY conname;
```

Check indexes:

```sql
SELECT
  schemaname,
  tablename,
  indexname,
  indexdef
FROM pg_indexes
WHERE schemaname = '<schema>'
  AND tablename = '<table_name>'
ORDER BY indexname;
```

Check state field values with counts:

```sql
SELECT
  <state_field>,
  COUNT(*) AS row_count
FROM <schema>.<table_name>
GROUP BY <state_field>
ORDER BY <state_field>;
```

Check identifier column types:

```sql
SELECT
  column_name,
  data_type,
  udt_name,
  is_nullable
FROM information_schema.columns
WHERE table_schema = '<schema>'
  AND table_name = '<table_name>'
  AND column_name IN ('<id_column_1>', '<id_column_2>', '<correlation_id_column>');
```

Check recent records by test correlation ID:

```sql
SELECT
  '<table_name>' AS source_table,
  created_at,
  updated_at,
  correlation_id,
  <state_field>
FROM <schema>.<table_name>
WHERE correlation_id = '<test_correlation_id>'
ORDER BY COALESCE(updated_at, created_at) DESC
LIMIT 20;
```

Check admin audit events:

```sql
SELECT
  created_at,
  tenant_code,
  action_domain,
  action_type,
  action_status,
  target_type,
  target_id
FROM <schema>.admin_audit_log
WHERE created_at >= '<test_started_at>'
  AND (
    target_id = '<test_correlation_id>'
    OR request_payload::text LIKE '%' || '<test_correlation_id>' || '%'
    OR result_payload::text LIKE '%' || '<test_correlation_id>' || '%'
  )
ORDER BY created_at DESC
LIMIT 20;
```

Check webhook delivery records:

```sql
SELECT
  delivery_id,
  tenant_code,
  client_id,
  event_type,
  delivery_status,
  attempt_count,
  next_attempt_at,
  delivered_at,
  created_at,
  updated_at
FROM <schema>.partner_webhook_deliveries
WHERE tenant_code = '<test_tenant_code>'
  AND created_at >= '<test_started_at>'
ORDER BY created_at DESC
LIMIT 20;
```

Check reward/funding/fulfilment/settlement records:

```sql
SELECT
  'rewards' AS source_table,
  id::text AS record_id,
  tenant_code,
  referral_track_id::text,
  status,
  created_at
FROM <schema>.rewards
WHERE referral_track_id::text = '<test_referral_track_id>'
UNION ALL
SELECT
  'funding_reservations',
  reservation_id::text,
  tenant_code,
  reward_id::text,
  status,
  created_at
FROM <schema>.funding_reservations
WHERE correlation_id = '<test_correlation_id>'
UNION ALL
SELECT
  'fulfilment_audit',
  audit_id::text,
  tenant_code,
  referral_track_id::text,
  status,
  created_at
FROM <schema>.fulfilment_audit
WHERE correlation_id = '<test_correlation_id>'
UNION ALL
SELECT
  'fulfilment_settlement_ledger',
  settlement_id::text,
  tenant_code,
  reward_id::text,
  status,
  created_at
FROM <schema>.fulfilment_settlement_ledger
WHERE audit_id::text = '<test_audit_id>';
```

If a table or column is absent, record drift. Do not edit schema during verification.

## 12. Evidence Requirements

TASK-027 must capture:

- Environment name.
- Timestamp and timezone.
- Operator/agent performing verification.
- Read-only credential confirmation.
- Route/action executed, if any.
- Correlation ID or seeded test ID.
- Redacted query output.
- Before/after state for any local/staging mutating smoke test.
- Pass/fail result per check.
- Schema drift findings.
- State value drift findings.
- Idempotency/retry/audit findings.
- Follow-up task IDs for unresolved drift.

Evidence format should be compact and redacted. Prefer counts, constraints, and structural metadata over row contents.

## 13. Pass/Fail Criteria

Pass when:

- Required tables, columns, constraints, indexes, and identifier types match the TASK-001 inventory or documented migrations.
- State fields contain only expected values or explicitly documented service-governed values.
- Idempotency keys and uniqueness constraints exist where expected.
- Retry/failure fields exist for fulfilment, webhook, event failure, settlement exception, and funding exception paths.
- Audit evidence exists for money-impacting and manual repair actions where code claims it exists.
- Smoke-test route behavior is read-only in production and isolated in local/staging.
- Evidence is complete and redacted.

Fail when:

- Live schema differs from migrations in a way that affects state, money, audit, idempotency, retry, auth, or identifiers.
- State values exist that are not in migration constraints, service constants, or documented unknowns.
- Identifier types conflict with service/test assumptions.
- Idempotency or uniqueness guarantees are missing for money/event/fulfilment flows.
- Audit evidence is missing for money-impacting or manual repair transitions.
- Smoke-test route behavior changes unexpected state.
- Evidence cannot be safely redacted.

Stop and escalate when:

- Production access is needed without approval.
- DB access is not read-only.
- Any verification step risks exposing secrets or customer data.
- Test data cannot be isolated.
- Money-impacting state is unclear.
- Schema drift is detected in a money, settlement, fulfilment, webhook, or audit table.

Human approval is required before:

- Any production database connection.
- Any production API smoke test beyond read-only GET routes.
- Any staging mutating smoke test involving rewards, funding, fulfilment, settlement, webhooks, or audit.
- Any attempt to inspect raw payloads or provider responses.

## 14. Stop Conditions

Stop TASK-027 immediately if:

- DB access is not read-only.
- Production access is required without approval.
- Schema differs from migrations.
- Identifier types conflict with services/tests.
- Money-impacting state is unclear.
- Audit trail is missing for money/manual transitions.
- Test data cannot be isolated.
- Secrets or customer data may be exposed.
- A route expected to be read-only writes state.
- A replay/retry/repair action is accidentally selected for production.

## 15. Follow-Up Routing

This checklist unblocks `TASK-027` by defining the safe execution process, query templates, evidence requirements, pass/fail rules, and stop conditions.

`TASK-027` should:

- Run this checklist using read-only access.
- Record redacted evidence.
- Mark each TASK-001 inventory item as verified, drifted, or environment-unavailable.
- Create or update follow-up tasks for drift.

`TASK-028` should:

- Resolve confirmed mismatches from TASK-027.
- Update `docs/sa/LIVE_CRITICAL_STATE_INVENTORY.md`, `docs/sa/STATE_MACHINE_MAP.md`, and roadmap tasks as needed.
- Split any real schema/service fixes into separate implementation tasks with tests.

Do not use this checklist to justify frontend/control-plane work, public API work, or money-flow implementation until the relevant verification and schema uncertainty tasks are complete.
