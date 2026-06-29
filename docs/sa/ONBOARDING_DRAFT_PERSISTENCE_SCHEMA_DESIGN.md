# Onboarding Draft Persistence Schema Design

Status: Accepted for TASK-098 on 2026-06-30.

## Purpose And Scope

This document designs the future persistence schema for DLaaS onboarding drafts. It covers proposed tables, indexes, uniqueness rules, retention, idempotency references, audit and event linkage, rollback, and migration safety.

This is design only. It does not add database tables, migrations, routes, services, frontend code, tests, persistence, live DB access, audit writes, event persistence, credential lifecycle, webhook delivery, funding, wallet, fulfilment, settlement, retry, go-live activation, or money movement.

The design supports the safe onboarding path defined by:

- `docs/sa/ONBOARDING_DATA_CONTRACT.md`
- `docs/sa/ONBOARDING_DRAFT_SAVE_API_BOUNDARY.md`
- `docs/sa/ONBOARDING_AUDIT_EVENT_CAPTURE_DESIGN.md`
- `docs/sa/AUDIT_RETRY_POLICY_STANDARD.md`
- `docs/roadmap/ONBOARDING_READ_MODEL_WAVE_CHECKPOINT_TASK_090.md`

## Design Principles

Future onboarding draft persistence must follow these principles:

1. Additive-only first migration.
2. No live activation semantics.
3. No account, tenant, organisation, producer, sponsor, distributor, member, user, campaign, opportunity, credential, webhook, wallet, funding, fulfilment, settlement, retry, or money records are created by draft persistence.
4. No secrets, API keys, tokens, passwords, certificates, signing material, callback secrets, or raw credential material are stored.
5. `tenant_code` remains internal and may appear only in internal/operator-only columns or audit references after authorized resolution.
6. External references remain the user-facing onboarding boundary.
7. Draft payloads are sectioned, bounded, redacted, and versioned.
8. Validation results use safe error codes and missing-evidence markers.
9. Idempotency is required for future write-like draft commands.
10. Rollback disables write paths before any database rollback is considered.

## Proposed Future Tables

These tables are proposed contract names only. TASK-098 does not create them.

| Table | Purpose |
| --- | --- |
| `onboarding_drafts` | Draft aggregate header, external scope, lifecycle state, version, and safe summary. |
| `onboarding_draft_sections` | Section-level draft payloads for company, producer/sponsor, distributor, member/role, campaign/opportunity, and webhook/API setup. |
| `onboarding_draft_validation_results` | Safe validation, blocker, missing-evidence, and readiness snapshots. |
| `onboarding_draft_idempotency_keys` | Duplicate-safe command evidence for draft create, update, validate, submit-for-review, and discard. |
| `onboarding_draft_audit_links` | References linking draft changes to audit/event/correlation evidence without storing raw sensitive payloads. |

The first implementation migration should create these structures in a disabled/no-write posture. Route and service write enablement should happen in later tasks behind explicit feature gates.

## Table: `onboarding_drafts`

Purpose: Store the draft aggregate record and current lifecycle state.

Key columns:

| Column | Intent |
| --- | --- |
| `draft_id` | Internal UUID primary key. |
| `draft_ref` | Stable external/support-safe draft reference. |
| `contract_version` | Onboarding contract version, for example `onboarding.v1`. |
| `status` | Draft lifecycle state. |
| `version` | Monotonic integer or equivalent stale-update guard. |
| `external_tenant_ref` | User-facing tenant/account reference. |
| `organisation_ref` | User-facing organisation reference. |
| `producer_ref` | User-facing producer reference, nullable. |
| `sponsor_ref` | User-facing sponsor reference, nullable. |
| `distributor_ref` | User-facing distributor reference, nullable. |
| `campaign_code` | User-facing campaign setup/diagnostic code, nullable. |
| `opportunity_ref` | User-facing opportunity reference, nullable. |
| `tenant_code` | Internal-only resolved tenant scope, nullable until resolution exists. |
| `created_by_actor_ref` | Safe actor reference for creator. |
| `updated_by_actor_ref` | Safe actor reference for last updater. |
| `source` | UI, admin API, integration client, or system source. |
| `correlation_id` | Support trace reference. |
| `safe_summary` | JSON summary with no secrets or raw sensitive values. |
| `redactions` | JSON array of applied redaction categories. |
| `created_at` | UTC creation timestamp. |
| `updated_at` | UTC update timestamp. |
| `expires_at` | Optional retention expiry timestamp. |
| `discarded_at` | Optional discard timestamp. |

External references: `external_tenant_ref`, `organisation_ref`, `producer_ref`, `sponsor_ref`, `distributor_ref`, `campaign_code`, and `opportunity_ref`.

Internal references: `draft_id`, `tenant_code`, actor references, and correlation ID. `tenant_code` must not be exposed as the primary user-facing identifier.

JSON payload boundaries: `safe_summary` may include section names, readiness counts, missing evidence counts, and safe display labels. It must not include raw section payloads, secrets, credentials, UCNs, provider payloads, audit internals, wallet/funding/settlement/fulfilment/retry internals, or money movement details.

Indexes:

- Unique index on `draft_ref`.
- Index on `external_tenant_ref`.
- Index on `organisation_ref`.
- Index on `producer_ref`.
- Index on `sponsor_ref`.
- Index on `distributor_ref`.
- Index on `campaign_code`.
- Index on `opportunity_ref`.
- Index on `status`.
- Index on `created_at`.
- Index on `updated_at`.
- Index on `correlation_id`.
- Optional partial unique index for one active draft per external scope where `status` is not `DISCARDED`.

Uniqueness constraints:

- `draft_ref` must be globally unique.
- Active draft uniqueness should be scoped to the external references that identify the onboarding aggregate. If external reference resolution is incomplete, the implementation should prefer a conservative duplicate conflict over creating ambiguous active drafts.

Retention:

- Active drafts retain until completed, discarded, expired, or archived by policy.
- Discarded drafts retain long enough for support and audit review, then may be privacy-safely anonymised.
- Audit-linked drafts must not be hard-deleted while audit retention requires the reference.

Non-goals:

- Does not create live tenants, organisations, producers, sponsors, distributors, campaigns, users, credentials, wallets, or money records.
- Does not store raw secrets, live credential material, or provider internals.

## Table: `onboarding_draft_sections`

Purpose: Store bounded section payloads and per-section state.

Key columns:

| Column | Intent |
| --- | --- |
| `section_id` | Internal UUID primary key. |
| `draft_id` | Foreign key to `onboarding_drafts`. |
| `section_key` | One of the canonical onboarding section names. |
| `section_status` | Safe section status such as `DRAFT`, `IN_PROGRESS`, `BLOCKED`, or `READY`. |
| `section_version` | Section-level stale update guard. |
| `payload` | JSON payload using TASK-081 field names only. |
| `payload_hash` | Stable hash for idempotency, audit, and stale detection. |
| `redacted_fields` | JSON array of redacted field names or categories. |
| `missing_evidence` | JSON array using bounded missing-evidence shape. |
| `source_warnings` | JSON array of safe warnings. |
| `created_at` | UTC creation timestamp. |
| `updated_at` | UTC update timestamp. |

Allowed `section_key` values:

- `company`
- `producer_sponsor`
- `distributor`
- `member_role`
- `campaign_opportunity`
- `webhook_api`

External references: section payloads may repeat external references from the draft header when needed for local validation, but header scope remains authoritative.

Internal references: section rows use `draft_id`; they should not carry `tenant_code` unless a later implementation proves it is required and internal-only.

JSON payload boundaries:

- Payload keys must match `ONBOARDING_DATA_CONTRACT.md`.
- Unknown keys should be rejected or stored only after redaction, according to future route policy.
- Unsafe key categories must be rejected/redacted: `tenant_code` as user input, UCNs, secrets, tokens, certificates, provider internals, audit internals, webhook delivery internals, funding/wallet/settlement/fulfilment/retry internals, and money details.

Indexes:

- Unique index on `(draft_id, section_key)`.
- Index on `(draft_id, section_status)`.
- Index on `payload_hash`.
- Index on `updated_at`.

Retention:

- Retain with parent draft.
- Redacted fields should remain categories only.
- Anonymise or delete section payloads when privacy policy allows and audit retention no longer requires content.

Non-goals:

- Does not store live entity payloads.
- Does not store credentials or webhook signing details.
- Does not validate or deliver invites, webhooks, fulfilment, settlement, or money movement.

## Table: `onboarding_draft_validation_results`

Purpose: Store safe validation and readiness snapshots for drafts.

Key columns:

| Column | Intent |
| --- | --- |
| `validation_id` | Internal UUID primary key. |
| `draft_id` | Foreign key to `onboarding_drafts`. |
| `draft_version` | Draft version validated. |
| `validation_type` | `FIELD`, `CROSS_SECTION`, `PERMISSION`, `READINESS`, or `SAFETY`. |
| `status` | `PASSED`, `FAILED`, `BLOCKED`, or `WARNING`. |
| `safe_error_code` | Bounded error code where applicable. |
| `section_key` | Optional affected section. |
| `field_name` | Optional safe field name. |
| `message` | Safe operator/client message. |
| `details` | JSON array/object with bounded safe details. |
| `readiness_snapshot` | JSON readiness summary compatible with TASK-083. |
| `correlation_id` | Support trace reference. |
| `created_at` | UTC creation timestamp. |

Validation categories:

- Field validation.
- Cross-section validation.
- Permission validation.
- Reference validation.
- Readiness validation.
- Safety validation.

Safe error codes should align to TASK-086, including:

- `VALIDATION_FAILED`
- `DUPLICATE_DRAFT`
- `IDEMPOTENCY_CONFLICT`
- `STALE_DRAFT`
- `UNKNOWN_REFERENCE`
- `PERMISSION_DENIED`
- `READINESS_BLOCKED`
- `UNSAFE_OPERATION_ATTEMPTED`
- `LIVE_DB_VERIFICATION_BLOCKED`
- `DRIFT_VERIFICATION_BLOCKED`

Indexes:

- Index on `draft_id`.
- Index on `(draft_id, draft_version)`.
- Index on `validation_type`.
- Index on `status`.
- Index on `safe_error_code`.
- Index on `created_at`.
- Index on `correlation_id`.

Retention:

- Retain recent validation history for support.
- Long-term retention may keep only summary, error code, section, field name, and hash references.

Non-goals:

- Does not perform validation by itself.
- Does not activate go-live when validation passes.
- Does not persist raw invalid sensitive values.

## Table: `onboarding_draft_idempotency_keys`

Purpose: Store duplicate-safe command evidence for future draft commands.

Key columns:

| Column | Intent |
| --- | --- |
| `idempotency_id` | Internal UUID primary key. |
| `idempotency_key_hash` | Hash of caller-supplied idempotency key. |
| `scope_hash` | Hash of action, actor, external refs, and draft ref where available. |
| `action_type` | Future command type such as create, update, validate, submit, or discard. |
| `draft_id` | Optional draft reference once known. |
| `draft_ref` | Safe draft reference where useful. |
| `actor_ref` | Safe actor reference. |
| `external_tenant_ref` | User-facing tenant reference when supplied. |
| `payload_hash` | Hash of canonicalized request payload. |
| `result_hash` | Hash of safe response/result. |
| `result_status` | Success, duplicate, conflict, validation failed, blocked, or denied. |
| `correlation_id` | Support trace reference. |
| `first_seen_at` | UTC first request timestamp. |
| `last_seen_at` | UTC most recent replay timestamp. |
| `expires_at` | Expiry timestamp for key retention. |

Behavior:

- Same key, same scope, same payload returns the prior result.
- Same key, same scope, different payload returns `409 IDEMPOTENCY_CONFLICT`.
- Same payload with a different key may still conflict with active-draft uniqueness.
- Replays must not create duplicate drafts, duplicate audit rows that imply a second mutation, credentials, webhooks, funding, fulfilment, settlement, retry, or money movement.

Indexes:

- Unique index on `(idempotency_key_hash, scope_hash)`.
- Index on `draft_id`.
- Index on `draft_ref`.
- Index on `actor_ref`.
- Index on `external_tenant_ref`.
- Index on `payload_hash`.
- Index on `correlation_id`.
- Index on `expires_at`.

Retention:

- Retain keys long enough for client retries and support investigation.
- Expired keys may be pruned after audit/support windows.
- Hashes may be retained longer than raw request/result summaries.

Non-goals:

- Does not store raw idempotency keys.
- Does not authorize commands without permission checks.
- Does not make non-idempotent live actions safe.

## Table: `onboarding_draft_audit_links`

Purpose: Link drafts to audit/event/correlation evidence without duplicating raw audit payloads.

Key columns:

| Column | Intent |
| --- | --- |
| `link_id` | Internal UUID primary key. |
| `draft_id` | Foreign key to `onboarding_drafts`. |
| `draft_ref` | Safe draft reference. |
| `draft_version` | Draft version associated with the evidence. |
| `action_type` | Onboarding action type. |
| `action_status` | Success, validation failed, duplicate, stale, blocked, denied, unsafe, or discarded. |
| `actor_ref` | Safe actor reference. |
| `actor_role` | Actor role family. |
| `audit_ref` | Reference to audit evidence, if written by future implementation. |
| `event_ref` | Reference to event evidence, if emitted or persisted by future implementation. |
| `idempotency_id` | Optional link to idempotency evidence. |
| `correlation_id` | Support trace reference. |
| `before_state_hash` | Hash/version of prior safe state. |
| `after_state_hash` | Hash/version of accepted safe state. |
| `changed_sections` | JSON array of section names. |
| `redactions` | JSON array of redaction categories. |
| `created_at` | UTC timestamp. |

Indexes:

- Index on `draft_id`.
- Index on `draft_ref`.
- Index on `action_type`.
- Index on `action_status`.
- Index on `actor_ref`.
- Index on `audit_ref`.
- Index on `event_ref`.
- Index on `idempotency_id`.
- Index on `correlation_id`.
- Index on `created_at`.

Retention:

- Preserve while audit/event retention requires it.
- Do not delete links that are necessary for support trace reconstruction.
- Redaction categories may be kept after sensitive payloads are removed.

Non-goals:

- Does not write audit rows.
- Does not persist events.
- Does not store raw before/after sensitive payloads.

## Draft Lifecycle States

Future schema should support these states from TASK-086:

| State | Meaning | Live action semantics |
| --- | --- | --- |
| `DRAFT_CREATED` | Draft aggregate accepted for future persistence. | None |
| `DRAFT_UPDATED` | Draft changed safely. | None |
| `VALIDATION_FAILED` | Validation failed or blockers remain. | None |
| `READY_FOR_REVIEW` | Complete enough for operator review. | Not go-live |
| `BLOCKED` | Known blocker prevents review or progress. | None |
| `DISCARDED` | Draft is inactive. | None |

`READY_FOR_REVIEW` must never imply tenant creation, campaign publication, credential activation, webhook delivery, funding, fulfilment, settlement, retry, or money movement.

## External Reference Handling

Future draft persistence should store external references as the primary onboarding scope:

- `external_tenant_ref`
- `organisation_ref`
- `producer_ref`
- `sponsor_ref`
- `distributor_ref`
- `campaign_code`
- `opportunity_ref`

Rules:

1. External references are visible to onboarding users and support workflows.
2. `tenant_code` is internal-only and nullable until an approved resolver exists.
3. Drafts without resolved tenant context must be marked unresolved or missing evidence.
4. Ambiguous, archived, disabled, suspended, or cross-tenant references must not authorize writes.
5. Future partner/distributor/producer/customer views must not expose `tenant_code`.

## Idempotency Model

Future commands that create, update, validate, submit for review, or discard drafts must require idempotency evidence.

Required model:

- Hash the caller-supplied idempotency key.
- Scope the key by actor, action type, external references, route, and draft reference where available.
- Canonicalize and hash the payload.
- Store safe result status and result hash.
- Return the existing result for same key/scope/payload.
- Return `IDEMPOTENCY_CONFLICT` for same key/scope/different payload.
- Keep idempotency rows long enough for retries and support.

This model is replay-safe only for draft state. It does not authorize duplicate-sensitive live actions.

## Audit And Event Linkage

Future audit/event evidence should link through references rather than raw payload copies.

Minimum linkage:

- correlation ID;
- draft reference;
- draft version;
- action type;
- action status;
- actor reference and role;
- idempotency reference;
- audit reference, if future audit writes exist;
- event reference, if future event persistence exists;
- before/after state hash;
- changed sections;
- redaction categories.

Sensitive state should be represented by hashes, versions, safe summaries, or redaction categories. No raw secrets, credential material, private identifiers, provider payloads, audit internals, webhook delivery internals, funding/wallet/settlement/fulfilment/retry internals, SQL, stack traces, or money movement details should be stored in draft audit links.

## Validation Result Model

Future validation results should be able to represent:

- field validation;
- cross-section validation;
- permission validation;
- reference validation;
- readiness validation;
- safety validation.

Each result should include a safe code, safe message, section, field name where safe, severity/status, and correlation ID. Readiness snapshots should reuse TASK-083 categories and must keep go-live disabled until a later reviewed implementation explicitly enables it.

## Redaction And Non-Exposure Boundaries

Draft persistence must not store or expose:

- secrets;
- API keys;
- client secrets;
- signing material;
- access or refresh tokens;
- passwords;
- certificates;
- raw webhook credentials;
- webhook delivery internals;
- raw UCNs or private identifiers;
- raw provider payloads;
- raw audit payloads;
- internal tenant identifiers as user-facing scope;
- funding, wallet, settlement, fulfilment, retry, reconciliation, payout, reversal, or money movement internals;
- SQL errors;
- stack traces;
- environment secret names;
- database DSNs.

Redaction must be observable through safe redaction categories, not through leaked values.

## Index Strategy Summary

Future migration review should include indexes for:

- `draft_ref`;
- `external_tenant_ref`;
- `organisation_ref`;
- `producer_ref`;
- `sponsor_ref`;
- `distributor_ref`;
- `campaign_code`;
- `opportunity_ref`;
- `status`;
- `created_at`;
- `updated_at`;
- idempotency key hash and scope hash;
- payload hash;
- correlation ID;
- audit reference;
- event reference.

Indexes should support operator lookup, duplicate prevention, retry/replay support, and retention cleanup without requiring table scans.

## Retention Strategy

Retention should distinguish:

| Draft type | Retention direction |
| --- | --- |
| Active drafts | Retain until submitted, discarded, expired, or archived. |
| Ready-for-review drafts | Retain through review and support window. |
| Blocked drafts | Retain until blocker is resolved, discarded, expired, or archived. |
| Discarded drafts | Retain for support/audit window, then anonymise or prune payloads. |
| Expired drafts | Prune or anonymise according to policy and audit linkage. |
| Audit-linked drafts | Keep references while audit retention requires traceability. |

Privacy-safe deletion may remove section payloads while preserving draft references, hashes, timestamps, redaction categories, and audit/event links required for support.

## Additive Migration Strategy

The first future implementation should use an additive migration:

1. Create tables only; do not enable writes in the same task unless explicitly scoped.
2. Add constraints and indexes needed for safe duplicate prevention.
3. Do not require backfill initially.
4. Keep existing read-only onboarding endpoint behavior unchanged.
5. Add read-only verification of empty tables and clean DB replay.
6. Feature-flag future draft writes separately.
7. Enable write paths only after route, permission, idempotency, audit, redaction, rollback, and no-live-action tests exist.

Migration naming should follow the existing numeric prefix pattern under `dp/migrations/`, but TASK-098 does not choose or create a migration file.

## Rollback Plan

Rollback should be operationally conservative:

1. Disable draft write feature flags first.
2. Keep read-only access to existing draft evidence for support.
3. Stop background jobs or processors if later tasks add any.
4. Preserve audit, idempotency, and event references.
5. Avoid destructive table drops in an emergency rollback.
6. If a schema rollback is unavoidable, perform it only after export/retention decisions and operator approval.
7. Existing onboarding read-only projection and frontend fallback must remain usable.

Because draft persistence may carry audit-linked evidence, migration rollback should not assume data can be discarded safely.

## Migration Safety Checklist

Before any future migration is added:

- Clean DB replay succeeds.
- Migration order does not reference tables before creation.
- Tables are additive and nullable where resolver evidence is unavailable.
- `tenant_code` stays internal-only.
- External reference indexes exist.
- Active-draft uniqueness is explicit.
- Idempotency uniqueness is explicit.
- Correlation ID lookup is indexed.
- Audit/event reference lookup is indexed.
- Retention cleanup paths have indexes.
- Redaction categories are represented.
- No secrets or credential storage exists.
- No-money/no-go-live tests exist for future write routes before enablement.
- Permission tests cover allowed roles, adjacent-role rejection, and cross-scope rejection.
- TASK-027/TASK-028 are either completed or explicitly deferred by reviewed decision.

## Explicitly Excluded

This design does not authorize:

- tenant creation;
- organisation/account creation;
- producer, sponsor, distributor, partner, member, user, seat, role, or identity-provider creation;
- invite delivery;
- campaign or opportunity publication;
- link/code issuance;
- credential generation, rotation, reveal, storage, or lifecycle;
- webhook subscription, signing, queueing, retry, replay, or delivery;
- go-live activation;
- funding, wallet, reservation, invoice, fulfilment, settlement, payout, reversal, repair, retry, reconciliation, or money movement.

## Mapping Back To Prior Tasks

| Source | Mapping |
| --- | --- |
| TASK-081 onboarding data contract | Defines section names, field names, external references, safe statuses, missing evidence, and redaction boundaries. |
| TASK-086 draft/save API boundary | Defines draft lifecycle, idempotency, duplicate/conflict behavior, safe errors, permissions, and disabled live actions. |
| TASK-087 audit/event capture design | Defines actor, action, before/after, idempotency, correlation, audit, event, and redaction evidence. |
| TASK-090 checkpoint | Confirms current state is read-only and recommends schema design before write implementation. |
| TASK-027/TASK-028 | Remain blocked and must not be silently bypassed for live DB or drift confidence. |

## Readback Checklist

Before starting any future schema or write implementation task, confirm:

- schema work is additive first;
- no migration is bundled with unrelated route or UI behavior;
- active draft uniqueness is defined;
- idempotency key storage uses hashes and scoped uniqueness;
- duplicate same-payload and duplicate different-payload behavior is explicit;
- stale draft/version handling is explicit;
- audit/event links use references, not raw sensitive payloads;
- correlation ID support is present;
- validation results use bounded safe errors;
- retention and anonymisation policy is defined;
- `tenant_code` is internal-only;
- external references are the user-facing boundary;
- redaction covers secrets, credentials, private identifiers, provider internals, audit internals, webhook internals, funding/wallet/settlement/fulfilment/retry internals, SQL, stack traces, and DSNs;
- rollback disables write paths before destructive schema action;
- no tenant creation, user creation, invite delivery, campaign publication, credential lifecycle, webhook delivery, go-live activation, funding, fulfilment, settlement, retry, audit mutation, or money movement is introduced;
- TASK-027 and TASK-028 remain blocked unless separately completed or explicitly deferred.
