# TASK-101 Onboarding Draft Migration Final Review

Date: 2026-06-30

Status: Accepted for TASK-101.

This review is documentation only. It does not add migrations, edit migrations, add backend code, add frontend code, add services, add routes, add tests, access live databases, inspect secrets, enable writes, persist drafts, write audit rows, persist events, generate credentials, deliver webhooks, activate go-live, fund, fulfil, settle, retry, create wallets, or move money.

## Purpose

TASK-101 performs the final review before TASK-102 may add onboarding draft persistence tables. The purpose is to confirm that the schema design, rollback posture, clean DB replay plan, idempotency model, audit linkage, privacy boundaries, and no-live-action guardrails are explicit enough for a narrow migration-only implementation task.

The decision in this review is not approval for onboarding writes. It is approval for a future additive migration that creates draft persistence tables only.

## Source Review

The review used these source documents and repository facts:

- `docs/sa/ONBOARDING_DRAFT_PERSISTENCE_SCHEMA_DESIGN.md`
- `docs/sa/ONBOARDING_DRAFT_SAVE_API_BOUNDARY.md`
- `docs/sa/ONBOARDING_AUDIT_EVENT_CAPTURE_DESIGN.md`
- `docs/sa/ONBOARDING_DRY_RUN_VALIDATION_ENDPOINT_CONTRACT.md`
- `docs/sa/ONBOARDING_DATA_CONTRACT.md`
- `docs/roadmap/ONBOARDING_PRE_WRITE_READINESS_CHECKPOINT_TASK_100.md`
- `docs/API_PERMISSION_MATRIX.md`
- existing migration naming under `dp/migrations/`
- `AGENTS.md`

The current migration folder uses ordered numeric prefixes, with the latest normal numbered migration at `079_partner_webhook_alert_notifications.sql` and a terminal `999_indexes.sql`. TASK-102 should follow the same ordered migration pattern and must not modify `999_indexes.sql` unless a later reviewed task explicitly requires it.

## Proposed Future Migration Scope

TASK-102 may consider only the contract tables already approved by TASK-098:

| Future table | Approved purpose |
| --- | --- |
| `onboarding_drafts` | Draft aggregate header, external scope, lifecycle state, version, and safe summary. |
| `onboarding_draft_sections` | Section-level draft payloads for company, producer/sponsor, distributor, member/role, campaign/opportunity, and webhook/API setup. |
| `onboarding_draft_validation_results` | Safe validation, blocker, missing-evidence, and readiness snapshots. |
| `onboarding_draft_idempotency_keys` | Duplicate-safe command evidence for future draft create, update, validate, submit-for-review, and discard behavior. |
| `onboarding_draft_audit_links` | References linking draft changes to audit, event, idempotency, and correlation evidence without storing raw sensitive payloads. |

The future migration should create tables, constraints, indexes, and foreign keys needed for draft persistence readiness. It must not add write routes, write services, frontend integration, feature enablement, seed data, live activation semantics, or backfills.

## Explicitly Not Approved

TASK-101 does not approve:

- tenant, account, company, or organisation creation;
- producer, sponsor, distributor, partner, member, user, seat, role, or identity-provider creation;
- invite delivery;
- campaign or opportunity creation, publication, launch, pause, close, or activation;
- link/code issuance or route activation;
- credential generation, rotation, reveal, storage, or lifecycle;
- webhook subscription, signing, queueing, retry, replay, or delivery;
- go-live activation;
- funding, wallet, reservation, invoice, fulfilment, settlement, payout, reversal, repair, retry, reconciliation, or money movement;
- audit writes or event persistence;
- dry-run validation route implementation;
- draft-save route implementation.

Any future implementation of these capabilities requires separate task scope, permission review, idempotency review, audit review, redaction tests, and no-money/no-go-live tests.

## Additive Migration Principles

TASK-102 must follow these principles:

1. Create tables only.
2. Use additive schema changes.
3. Do not change existing onboarding read-only behavior.
4. Do not enable writes.
5. Do not add routes, services, frontend code, tests unrelated to migration verification, or seed data.
6. Do not require backfill initially.
7. Do not depend on production data.
8. Do not access live databases.
9. Keep `tenant_code` internal-only and nullable where resolution is unavailable.
10. Preserve external references as the user-facing onboarding boundary.
11. Keep draft lifecycle states separate from live platform lifecycle states.
12. Represent redaction and missing evidence with safe categories.

## Clean DB Replay Plan

TASK-102 validation must prove the migration can replay from an empty database in local/CI context:

- run migration hygiene checks;
- run full clean DB migration replay;
- verify the migration order is stable;
- verify dependencies and extensions already exist before the migration uses them;
- verify all referenced tables exist before foreign keys or references are added;
- verify the migration has no production data dependency;
- verify no live DB access is required;
- verify no seed file is required for the draft tables to exist;
- verify migration replay still reaches the terminal migration/index stage.

Recommended commands for TASK-102 validation, subject to that task's instructions:

- `python scripts/check_migrations.py`
- `python scripts/init_db.py`

If TASK-102 discovers a later migration or clean replay blocker, it should report the new blocker separately and keep fixes minimal.

## Rollback Plan

Rollback must be operationally conservative:

1. Disable any future draft write paths before considering schema rollback.
2. Preserve read-only access to existing draft evidence where support needs it.
3. Preserve idempotency, audit-link, correlation, and validation evidence where retention requires it.
4. Avoid destructive table drops by default.
5. Do not treat rollback as permission to delete live data or audit evidence.
6. If schema rollback is unavoidable, require operator approval, retention review, and export/anonymisation decisions first.
7. Keep existing onboarding read-only projection and frontend fallback usable.

Because draft persistence may later carry audit-linked evidence, rollback must not assume the data is disposable.

## Idempotency Readiness

The future migration should support idempotency evidence without implementing idempotency behavior in TASK-102:

- store hashed idempotency keys, not raw keys;
- scope keys by actor, action, external references, route, and draft reference where available;
- store payload hash and safe result hash/status;
- support same-key/same-payload replay;
- support same-key/different-payload conflict detection;
- avoid duplicate draft creation;
- avoid duplicate audit/event evidence that implies a second mutation.

TASK-102 should create only the storage foundation. TASK-105 remains the implementation task for idempotency helper behavior.

## Audit And Event Readiness

TASK-102 may create audit-link storage only. It must not write audit rows or persist events.

Approved migration-level readiness:

- draft reference;
- action type and status columns;
- actor reference and actor role columns;
- correlation ID;
- idempotency reference;
- audit reference;
- event reference;
- before and after state hashes;
- changed section names;
- redaction categories.

Not approved in TASK-102:

- audit writer implementation;
- event store implementation;
- webhook dispatch;
- event delivery;
- repair, replay, retry, or DLQ behavior.

## Redaction And Privacy Readiness

TASK-102 must preserve these non-exposure rules:

- no raw secrets;
- no API keys;
- no tokens;
- no passwords;
- no certificates;
- no signing material;
- no webhook credential material;
- no raw UCNs or private identifiers;
- no provider internals;
- no raw audit payloads;
- no webhook delivery internals;
- no funding, wallet, fulfilment, settlement, retry, reconciliation, payout, reversal, or money movement internals;
- no SQL errors, stack traces, database DSNs, or environment secret names.

Redaction must be represented through safe categories and hashes where needed, not leaked values.

## Permission Posture

The current onboarding read route remains read-only and admin/operator scoped. TASK-102 must not change auth helpers, permission behavior, role mappings, route dependencies, or frontend access.

Future write routes will require separate RBAC and permission contract tests. Those future tests must cover allowed roles, adjacent-role rejection, unauthenticated rejection, cross-scope rejection, external-reference scope, idempotency, redaction, safe errors, no live actions, and no money movement.

## TASK-027 And TASK-028 Posture

TASK-027 remains blocked because safe read-only runtime database access has not been approved. TASK-028 remains blocked because TASK-027 has not produced verified live/schema drift evidence.

TASK-102 may proceed only as a local/CI clean DB migration task. It must not claim live DB readiness, production drift resolution, release readiness, or production onboarding readiness.

If a future migration needs live DB verification, TASK-102 must stop and record the blocker instead of attempting DB access.

## TASK-102 Readiness Decision

Decision: TASK-102 may proceed as a narrow migration-only implementation task.

TASK-102 must:

- create only the approved draft persistence tables;
- remain additive;
- avoid write routes and route wiring;
- avoid services and frontend integration;
- avoid seed data and production data;
- avoid live DB access;
- preserve `tenant_code` as internal-only;
- preserve external references as the user-facing boundary;
- include constraints and indexes needed for duplicate prevention, idempotency evidence, lookup, retention, correlation, and audit links;
- pass migration hygiene and clean DB replay validation;
- stop if it needs broader implementation scope.

TASK-102 must not implement draft save, dry-run validation, audit writes, event persistence, credential lifecycle, webhook delivery, go-live, funding, wallet, fulfilment, settlement, retry, or money movement.

## Readback Checklist

- Schema design is documented in TASK-098 and reviewed here.
- Approved future tables are limited to onboarding draft persistence foundations.
- Migration approach is additive and migration-only.
- Clean DB replay is the immediate validation path.
- No production data or live DB access is required.
- Rollback disables future write paths before destructive schema action.
- Idempotency storage is approved only as storage foundation.
- Audit links are approved only as references, not writes.
- Redaction and privacy guardrails are explicit.
- Permission posture remains unchanged for TASK-102.
- `tenant_code` remains internal-only.
- External references remain user-facing.
- TASK-027 and TASK-028 remain blocked.
- No live onboarding, credential lifecycle, webhook delivery, go-live activation, funding, fulfilment, settlement, retry, wallet, or money movement is approved.
- TASK-102 can proceed only as a narrow migration-only task.
