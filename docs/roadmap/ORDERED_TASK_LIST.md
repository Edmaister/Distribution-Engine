# Ordered DLaaS Task List

This task list is ordered by dependency, not ease of build. Every task links to an enhancement in `docs/roadmap/ENHANCEMENT_BACKLOG.md`.

## TASK-001: Inventory live-critical states, identifiers, and idempotency keys

Status: Complete (2026-06-20). Output: `docs/sa/LIVE_CRITICAL_STATE_INVENTORY.md`.
Linked enhancement: DLaaS-002: Platform state, idempotency, and live verification guardrails
Linked platform capability: 14. Audit trail; 28. Idempotency/retry handling; 30. Live DB/state verification
Goal: Produce a source-of-truth inventory of existing state fields, identifiers, idempotency keys, retry fields, and audit tables used by DLaaS-critical flows.
Why now: Later tasks depend on knowing which current fields can safely anchor outcome, money, API, and UX contracts.
Files likely involved: `dp/migrations/*`; `services/*`; `apps/api/routers/*`; `docs/sa/STATE_MACHINE_MAP.md`
Database/schema impact: Documentation only unless the inventory finds unverifiable schema assumptions.
Backend impact: None yet; maps existing implementation.
Frontend impact: None.
API impact: None.
Tests to add/update: No implementation tests yet; add a doc-check or static inventory check only if practical.
Validation method: Cross-check migration constraints, service constants, and router query/status usage.
Acceptance criteria: Inventory identifies current source-of-truth fields for referral, campaign track, reward, funding, fulfilment, settlement, webhook delivery, audit, and retry/idempotency.
Dependencies: None.
Blocked by: None.
Risk level: Low.
Rollback notes: Revert documentation/check only.
Definition of done: The state/idempotency inventory is complete enough to unblock outcome trace and audit taxonomy work. Priority: P0.

## TASK-002: Define platform audit and retry policy standards

Linked enhancement: DLaaS-002; DLaaS-012: Audit taxonomy and observable support trace
Linked platform capability: 14. Audit trail; 27. Observability; 28. Idempotency/retry handling
Goal: Define required audit fields, retry classes, idempotency expectations, and failure categories for DLaaS-critical actions.
Why now: Money, event, fulfilment, settlement, webhook, and repair work must share guardrails before new APIs are built.
Files likely involved: `docs/sa/STATE_MACHINE_MAP.md`; `docs/roadmap/ENHANCEMENT_BACKLOG.md`; `services/admin_audit_service.py`; `services/fulfilment_retry_*`; `services/partner_seam_service.py`
Database/schema impact: None initially; later schema changes must reference this standard.
Backend impact: Establishes rules future services must follow.
Frontend impact: Defines status/action language future UI can consume.
API impact: Future APIs must include auth, validation, idempotency, retry/error, and audit behavior consistent with this standard.
Tests to add/update: Audit write tests; duplicate request tests; retry exhaustion tests once implementations start.
Validation method: Confirm standard covers event ingestion, rewards, funding, fulfilment, settlement, webhooks, and repair actions.
Acceptance criteria: Standard states which actions require idempotency keys, bounded retry, actor/reason capture, before/after state, and audit records.
Dependencies: TASK-001.
Blocked by: None.
Risk level: Medium.
Rollback notes: Revert doc-only standard if it conflicts with implementation reality.
Definition of done: Future backend and API tasks can cite the standard without making new policy decisions. Priority: P0.

## TASK-003: Create live DB/state verification checklist

Status: Complete (2026-06-20). Output: `docs/sa/LIVE_DB_STATE_VERIFICATION_CHECKLIST.md`.
Linked enhancement: DLaaS-002
Linked platform capability: 30. Live DB/state verification
Goal: Define repeatable verification for migration replay, live schema drift, seed data, status constraints, and critical route smoke tests.
Why now: The capability matrix marks live DB/state verification as Unknown; implementation must not rely only on static files.
Files likely involved: `docs/RUNTIME_SMOKE_TEST.md`; `docs/HELM_MIGRATIONS.md`; `scripts/`; `dp/migrations/*`
Database/schema impact: None directly; validates schema reality.
Backend impact: Defines smoke expectations for backend-critical flows.
Frontend impact: None.
API impact: Smoke checks should cover representative internal/public routes with auth expectations.
Tests to add/update: Migration replay tests; live schema diff check; seed verification; smoke tests.
Validation method: Run static migration replay where available; document live checks that require environment access.
Acceptance criteria: Checklist identifies what to verify locally, in CI, and against a live environment before money/API work ships.
Dependencies: TASK-001.
Blocked by: Runtime DB access for actual live execution.
Risk level: Medium.
Rollback notes: Revert checklist only; no runtime state changed.
Definition of done: Live verification is no longer ambiguous and can be executed when environment credentials exist. Priority: P0.

## TASK-027: Run live DB verification for TASK-001 inventory

Linked enhancement: DLaaS-002: Platform state, idempotency, and live verification guardrails
Linked platform capability: 14. Audit trail; 28. Idempotency/retry handling; 30. Live DB/state verification
Goal: Compare `docs/sa/LIVE_CRITICAL_STATE_INVENTORY.md` against a real migrated database, including status constraints, unique indexes, columns, and critical table presence.
Why now: TASK-001 was static inspection only; money, webhook, settlement, and API work must not rely on unverified deployed schema assumptions.
Files likely involved: `docs/sa/LIVE_CRITICAL_STATE_INVENTORY.md`; `docs/sa/LIVE_DB_STATE_VERIFICATION_CHECKLIST.md`; `docs/RUNTIME_SMOKE_TEST.md`; `docs/HELM_MIGRATIONS.md`; `scripts/`; `dp/migrations/*`
Database/schema impact: Read-only verification; no schema changes in this task.
Backend impact: None unless drift is discovered and converted into a later implementation task.
Frontend impact: None.
API impact: Smoke checks may call representative admin/internal routes with proper auth, but no API changes.
Tests to add/update: Migration replay check; live schema diff/checklist; table/column/status/index verification; route smoke checks where environment credentials are available.
Validation method: Use information schema/catalog queries or existing migration tooling to confirm each live-critical table, state field, check constraint, unique index, and idempotency key from TASK-001.
Acceptance criteria: Every TASK-001 confirmed fact is marked verified, drifted, or environment-unavailable; all drift becomes explicit follow-up work.
Dependencies: TASK-001; TASK-003.
Blocked by: Runtime database access and safe read-only credentials.
Risk level: Medium.
Rollback notes: Documentation/checklist only; no data is changed.
Definition of done: Live DB verification results are recorded and schema uncertainty is reduced to named follow-up tasks. Priority: P0.

## TASK-030: Classify untracked repository baseline before agent execution

Status: Complete (2026-06-21). Output: `docs/agent/DLAAS_AGENT_RUNBOOK.md`.
Linked enhancement: DLaaS Agent Runner Framework
Linked platform capability: Agent execution, traceability, clean diffs, branch/PR workflow, rollback safety
Goal: Classify all currently untracked files and folders so the project can establish a safe baseline before autonomous agent execution begins.
Why now: The DLaaS agent runner requires clean Git diffs. The repo currently has many untracked files, including core product folders such as `apps`, `services`, `frontend`, `dp`, `scripts`, and `test`. Product tasks should not run until the baseline is tracked or deliberately ignored.
Files likely involved: `docs/agent/*`; `.gitignore`; `docs/roadmap/ORDERED_TASK_LIST.md`; Git status output; untracked workspace files and folders for classification only.
Database/schema impact: None. Do not modify database schema.
Backend impact: None. Do not modify backend product code or business logic.
Frontend impact: None. Do not build or modify frontend UI.
API impact: None. Do not modify APIs.
Tests to add/update: No product tests required. Validate by reading Git status output and reviewing `.gitignore` coverage for unsafe local files.
Validation method: Run `git status --short` or equivalent repository status inspection, list every untracked file/folder, classify each item, and confirm unsafe local files are excluded from the recommended baseline.
Acceptance criteria: Every untracked file/folder from Git status is listed and classified as `commit to baseline`, `ignore`, `inspect before deciding`, or `delete/archive outside repo`; no secrets, virtual environments, runtime logs, coverage files, or local outputs are recommended for commit; `.gitignore` excludes unsafe local files; a recommended safe commit sequence is produced; no `git add` or `git commit` is run.
Dependencies: DLaaS Agent Runner Framework files exist.
Blocked by: A Git repository/status command must be available from the correct repository root.
Risk level: High.
Rollback notes: Revert documentation/classification output only. Do not delete, add, stage, or commit files in this task.
Definition of done: There is a clear baseline classification and commit plan that allows the repo to become safe for branch/PR-based DLaaS agent execution. Priority: P0.

## TASK-031: Verify GitHub remote and autonomous agent readiness after baseline push

Status: Complete (2026-06-21). Output: `docs/agent/DLAAS_AGENT_RUNBOOK.md`.
Linked enhancement: DLaaS Agent Runner Framework
Linked platform capability: Agent execution, traceability, clean diffs, branch/PR workflow, rollback safety
Goal: Verify GitHub remote configuration, branch tracking, pushed baseline commits, unsafe ignored files, and remaining untracked items before autonomous agent execution.
Why now: TASK-030 classified the baseline before push. After the baseline push, the runner needs a final readiness gate that confirms remote tracking is healthy and remaining untracked files do not invalidate clean diffs for DLaaS task work.
Files likely involved: `docs/agent/DLAAS_AGENT_RUNBOOK.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; Git status/remote/log output.
Database/schema impact: None. Do not modify database schema or run live DB checks.
Backend impact: None. Do not modify product code or business logic.
Frontend impact: None. Do not build or modify frontend UI.
API impact: None.
Tests to add/update: No product tests required. Validate with Git status, branch tracking, remote URL, recent commit history, unsafe tracked-file checks, and untracked-file classification.
Validation method: Run read-only Git inspection commands and document whether remote, branch tracking, baseline push, ignored unsafe files, and remaining untracked files are acceptable for autonomous agent execution.
Acceptance criteria: GitHub remote is confirmed; current branch tracks `origin/main`; recent baseline commits are present; unsafe local files are not tracked; remaining untracked files are listed and classified; readiness for autonomous branch/PR execution is explicitly stated.
Dependencies: TASK-030; baseline commits pushed to GitHub.
Blocked by: Missing remote, branch not tracking `origin/main`, unsafe files tracked, or unclassified untracked files that affect the next agent task.
Risk level: Medium.
Rollback notes: Revert documentation/readiness updates only. Do not add, commit, delete, or modify product files.
Definition of done: The repo has an explicit post-push readiness decision for DLaaS agent runner execution. Priority: P0.

## TASK-032: Review remaining untracked config, infra, and legacy docs before broad agent execution

Status: Complete (2026-06-21). Output: `docs/agent/DLAAS_AGENT_RUNBOOK.md`.
Linked enhancement: DLaaS Agent Runner Framework
Linked platform capability: Agent execution, traceability, clean diffs, branch/PR workflow, rollback safety
Goal: Inspect and classify remaining untracked config, CI/CD, Helm, monitoring, sample, and legacy documentation items after the baseline push.
Why now: TASK-031 confirmed restricted readiness only. Broad autonomous execution remains unsafe until remaining untracked config/infra and accidental files are explicitly classified.
Files likely involved: `docs/agent/DLAAS_AGENT_RUNBOOK.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; untracked config/infra/legacy files for inspection only.
Database/schema impact: None. Do not modify database schema or run live DB checks.
Backend impact: None. Do not modify product code or business logic.
Frontend impact: None. Do not build or modify frontend UI.
API impact: None.
Tests to add/update: No product tests required. Validate by inspecting untracked files, checking for secrets/sensitive values, comparing `github/` with `.github/`, and documenting cleanup recommendations.
Validation method: Use read-only file and Git inspection to classify every remaining untracked item as commit, ignore, archive, delete after human confirmation, or keep untracked temporarily.
Acceptance criteria: Remaining untracked items are classified; config/CI/CD/Helm/monitoring sensitive values are identified; accidental files are identified; final cleanup/commit plan is documented; blockers for backend/docs, frontend, CI/CD, deployment, monitoring, and broad autonomous execution are explicit.
Dependencies: TASK-031.
Blocked by: Human decision on whether to commit, migrate, ignore, archive, or delete the remaining untracked items.
Risk level: Medium.
Rollback notes: Revert documentation/readiness updates only. Do not add, commit, delete, or modify product files.
Definition of done: The repo has a clear policy for remaining untracked files and a readiness decision for broad autonomous DLaaS agent execution. Priority: P0.

## TASK-033: Clean accidental local artifacts after GitHub baseline push

Status: Complete (2026-06-21). Output: `docs/agent/DLAAS_AGENT_RUNBOOK.md`.
Linked enhancement: DLaaS Agent Runner Framework
Linked platform capability: Agent execution, traceability, clean diffs, branch/PR workflow, rollback safety
Goal: Inspect accidental local artifacts after the GitHub baseline push and produce human-approved cleanup commands.
Why now: TASK-032 identified empty and accidental untracked files that do not belong in the product baseline but still keep the workspace noisy for broad autonomous execution.
Files likely involved: `body`; `docker`; `eline readiness` artifact; `run_tests.ps1`; `docs/agent/DLAAS_AGENT_RUNBOOK.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Database/schema impact: None. Do not modify database schema or run live DB checks.
Backend impact: None. Do not modify product code or business logic.
Frontend impact: None. Do not build or modify frontend UI.
API impact: None.
Tests to add/update: No product tests required. Validate by inspecting target file size/content and documenting cleanup recommendations.
Validation method: Confirm whether each target file is empty, accidental, duplicate, or useful; document whether it should be deleted, archived outside repo, kept untracked, or committed later.
Acceptance criteria: Each target file is inspected and classified; no product code is changed; no Git staging or commit is performed; exact human-approved cleanup commands are documented.
Dependencies: TASK-032.
Blocked by: Human confirmation before deletion or archive operations.
Risk level: Low.
Rollback notes: Revert documentation/readiness updates only. Do not delete files unless explicitly approved.
Definition of done: Accidental local artifacts have clear cleanup recommendations and no longer create ambiguity for DLaaS agent runner readiness. Priority: P0.

## TASK-036: Template and migrate safe config/infra assets for safe baseline commit

Status: Complete (2026-06-21). Output: `docs/agent/DLAAS_AGENT_RUNBOOK.md`.
Linked enhancement: DLaaS Agent Runner Framework
Linked platform capability: Agent execution, traceability, clean diffs, branch/PR workflow, rollback safety
Goal: Template credential-looking config/infra values and copy reviewed CI/CD assets into canonical locations for a safe baseline commit.
Why now: TASK-035 identified safe config/infra assets and files requiring templating. Broad autonomous execution needs CI/CD, deployment, Helm, and monitoring assets to be safe to stage or explicitly ignored.
Files likely involved: `config/*`; `.github/workflows/*`; `docs/CI_CD.md`; `helm/referrals/*`; `monitoring/infra/*`; `.gitignore`; `docs/agent/DLAAS_AGENT_RUNBOOK.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Database/schema impact: None. Do not modify database schema or run live DB checks.
Backend impact: None. Do not modify product business logic.
Frontend impact: None. Do not build or modify frontend UI.
API impact: None.
Tests to add/update: No product tests required. Validate with diff review and secret-pattern scan.
Validation method: Confirm credential-looking values are placeholders or env references, workflows are copied into `.github/workflows/`, unsafe local files are ignored, and no staging or commit was performed.
Acceptance criteria: Config DSNs are safe placeholders/env references; deploy workflows exist under `.github/workflows/`; CI/CD docs exist under `docs/`; Helm README no longer contains credential-looking DSN examples; monitoring example infra avoids literal local credentials where edited; unsafe local secret file remains ignored; files safe to stage are listed.
Dependencies: TASK-035.
Blocked by: Human review and staging/commit decision for the cleaned assets.
Risk level: Medium.
Rollback notes: Revert templating/docs/workflow-copy changes only. Do not delete legacy folders in this task.
Definition of done: Safe config/infra assets are templated or migrated enough for a reviewed baseline commit plan. Priority: P0.

## TASK-037: Archive or ignore remaining legacy docs and sample artifacts after config/infra cleanup

Status: Complete (2026-06-21). Output: `docs/agent/DLAAS_AGENT_RUNBOOK.md`.
Linked enhancement: DLaaS Agent Runner Framework
Linked platform capability: Agent execution, traceability, clean diffs, branch/PR workflow, rollback safety
Goal: Inspect remaining legacy docs, duplicate GitHub workflow source, support SQL, and sample Docker app artifacts after config/infra cleanup.
Why now: TASK-036 made config/infra assets safer for a baseline commit, but broad autonomous execution remains noisy while legacy and duplicate untracked artifacts remain in the workspace.
Files likely involved: `Core Domain Features.txt`; `Front-end Blueprint.txt`; `Support Queries.txt`; `folder strucuture.txt`; `github/`; `welcome-to-docker/`; `docs/agent/DLAAS_AGENT_RUNBOOK.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Database/schema impact: None. Do not modify database schema or run live DB checks.
Backend impact: None. Do not modify product business logic.
Frontend impact: None. Do not build or modify frontend UI.
API impact: None.
Tests to add/update: No product tests required. Validate by inspecting target legacy files and documenting sensitive, stale, duplicate, or conflicting content.
Validation method: Confirm whether each target should be archived outside repo, ignored, committed after review, deleted after human confirmation, or kept untracked temporarily; check for SQL with real-looking IDs and duplicate migrated content.
Acceptance criteria: Each target item is inspected and classified; `github/` migration status is confirmed; `welcome-to-docker/` sample/nested Git status is confirmed; `Support Queries.txt` sensitivity is documented; exact cleanup commands are provided; no staging, committing, deleting, moving, or archiving is performed.
Dependencies: TASK-036.
Blocked by: Human confirmation before archive/delete operations.
Risk level: Low.
Rollback notes: Revert documentation/readiness updates only. Do not delete or archive files in this task.
Definition of done: Remaining legacy artifacts have clear archive/delete/retain recommendations and broad autonomous execution blockers are explicit. Priority: P0.

## TASK-038: Review remaining monitoring Terraform assets before baseline commit

Status: Complete (2026-06-21). Output: `docs/agent/DLAAS_AGENT_RUNBOOK.md`.
Linked enhancement: DLaaS Agent Runner Framework
Linked platform capability: Agent execution, traceability, clean diffs, branch/PR workflow, rollback safety
Goal: Inspect remaining monitoring Terraform assets for secrets, credentials, backend state, provider details, and production-risk values before baseline commit.
Why now: TASK-036 cleaned config/infra assets, but monitoring Terraform skeletons need explicit classification before monitoring/deployment work is unblocked.
Files likely involved: `monitoring/infra/Infra_Read_Me.md`; `monitoring/infra/Terraform/*`; `docs/agent/DLAAS_AGENT_RUNBOOK.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Database/schema impact: None. Do not modify database schema or run live DB checks.
Backend impact: None. Do not modify product code or business logic.
Frontend impact: None. Do not build or modify frontend UI.
API impact: None.
Tests to add/update: No product tests required. Validate by inspecting Terraform/infra docs and scanning for sensitive values.
Validation method: Confirm each target file is safe to commit, needs templating, should be ignored, archived, or deleted after human confirmation.
Acceptance criteria: Terraform/infra files are inspected; sensitive findings are documented; safe-to-commit and blocked files are listed; exact staging or redaction commands are recommended; no staging, committing, deleting, or product changes are performed.
Dependencies: TASK-036.
Blocked by: Human review and baseline staging/commit decision.
Risk level: Low.
Rollback notes: Revert documentation/readiness updates only.
Definition of done: Monitoring Terraform assets have a clear safety classification and deployment/monitoring blockers are explicit. Priority: P0.

## TASK-039: Fix clean DB migration replay readiness

Status: Complete (2026-06-21). Branch: `task-039-fix-referral-track-id-migration`.
Linked enhancement: DLaaS-002: Platform state, idempotency, and live verification guardrails
Linked platform capability: 30. Live DB/state verification
Goal: Keep the clean database migration chain replayable from zero without touching live data or making unrelated schema changes.
Why now: CI clean DB readiness found sequential replay failures that block proof that a new environment can provision safely.
Files involved: `dp/migrations/024_mission_and_reward_summary.sql`; `dp/migrations/041_funding_accounts_and_transactions.sql`; `dp/migrations/044_create_funding_exposure.sql`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Database/schema impact: Migration-chain correction only. No live DB access, no production data, and no business-data migration.
Backend impact: None. Services and tests are used as source of truth for expected schema.
Frontend impact: None.
API impact: None.
Tests to add/update: No new tests unless validation reveals a missing migration hygiene assertion. Use existing migration and targeted funding tests.
Validation method: Run `python scripts/check_migrations.py`, `python scripts/init_db.py`, and targeted funding tests.
Findings:
- Migration 024 previously referenced `referral_track_id` incorrectly and was fixed under this task; CI progressed beyond migration 024 afterward.
- Migration 041 then failed on a clean replay because it altered `funding_account_rules` before that table existed.
- `funding_account_rules` is first created by migration 044 and repeated idempotently by migration 045; services and tests reference the same canonical table with `funding_model` and `sponsor_wallet_id`.
- The minimal fix is to remove the premature 041 `funding_account_rules` ALTER/INDEX block and apply the same columns/indexes after the table is first created in migration 044.
- Migration 061 then failed on clean replay because its backfill used `ON CONFLICT (dedupe_key)` before the unique index on `enterprise_event_inbox(dedupe_key)` existed.
- `dedupe_key` is the canonical enterprise inbox idempotency key used by migration 061 and `apps/Workers/ids_consumer.py`; the minimal fix is to create `ux_enterprise_event_inbox_dedupe_key` immediately after the inbox table is created and before the backfill runs.
- After migration replay reached 999, CI failed in the clean DB seed step because direct execution of `scripts/seed_db.py` could not import project-root modules such as `utils.db`.
- `scripts/init_db.py` already adds the repository root to `sys.path`; the minimal readiness fix is to apply the same direct-script import bootstrap to `scripts/seed_db.py` instead of changing seed semantics or hiding seed failures.
- Validation passed with `.venv_codex\Scripts\python.exe scripts\check_migrations.py` after the migration 061 ordering fix.
- Validation passed with `.venv_codex\Scripts\python.exe scripts\init_db.py`; local replay progressed past migrations 041 and 061 and completed through migration 999.
- Validation with `.venv_codex\Scripts\python.exe scripts\seed_db.py` progressed beyond the prior `ModuleNotFoundError: No module named 'utils'` import failure and began applying seed files.
- The next seed readiness failure is a real seed/schema mismatch in `dp/seeds/seed_data_for_mission_definitions.sql`: `asyncpg.exceptions.UndefinedColumnError: column "title" of relation "mission_definitions" does not exist`.
- `mission_definitions` canonical columns are `mission_name`, `mission_description`, `event_type`, and `goal_count`; `title`, `description`, `trigger_type`, `goal`, `badge_code`, and `bonus_reward_type` are not mission definition columns in the migration/service source of truth.
- The minimal seed alignment fix maps the old seed to canonical mission columns, preserves the two mission rows, removes noncanonical mission-definition fields from the insert, and adds `ON CONFLICT (mission_code) DO NOTHING` for idempotent seed replay.
- Validation with `.venv_codex\Scripts\python.exe scripts\seed_db.py` progressed past `seed_data_for_mission_definitions.sql`.
- The next seed readiness failure is in `dp/seeds/seed_leaderboard_scoring_rules.sql`: `asyncpg.exceptions.UniqueViolationError` on `uq_leaderboard_scoring_rule_expr`, meaning the leaderboard scoring rule seed needs its own idempotency alignment.
- `leaderboard_scoring_rules` uses a canonical uniqueness expression over leaderboard, journey, product scope, milestone, and score type; the minimal seed replay fix is to add `ON CONFLICT` against that same expression without changing scoring values or table schema.
- Validation with `.venv_codex\Scripts\python.exe scripts\seed_db.py` progressed past `seed_leaderboard_scoring_rules.sql`.
- The next seed readiness failure is in `dp/seeds/seed_mission_definition_core.sql`: `asyncpg.exceptions.UniqueViolationError` on `mission_definitions_mission_code_key` for `mission_code=ACCOUNT_OPENED_CORE`, meaning the core mission seed needs its own idempotency alignment.
- `seed_mission_definition_core.sql` contains canonical additive mission definitions and should not override existing mission content; the minimal seed replay fix is `ON CONFLICT (mission_code) DO NOTHING`.
- Validation with `.venv_codex\Scripts\python.exe scripts\seed_db.py` progressed past `seed_mission_definition_core.sql`.
- The next seed readiness failure is in `dp/seeds/seed_mission_definition_milestone.sql`: `asyncpg.exceptions.UniqueViolationError` on `mission_definitions_mission_code_key` for `mission_code=COMPLETE_1_REFERRAL`, meaning the milestone mission seed needs its own idempotency alignment.
- `seed_mission_definition_milestone.sql` contains canonical additive mission definitions and should not override existing mission content; the minimal seed replay fix is `ON CONFLICT (mission_code) DO NOTHING`.
- Validation with `.venv_codex\Scripts\python.exe scripts\seed_db.py` progressed past `seed_mission_definition_milestone.sql`.
- The next seed readiness failure is in `dp/seeds/seed_policies_and_campaigns (1).sql`: `asyncpg.exceptions.UndefinedColumnError` because `marketing_campaigns.sticker` does not exist in the canonical schema.
- Migration 002 documents `segment` as the campaign targeting dimension that replaced campaign-level `sticker`; the minimal seed alignment fix maps the sample campaign seed from `sticker` to `segment` without changing campaign behavior or policy data.
- Validation with `.venv_codex\Scripts\python.exe scripts\seed_db.py` completed successfully after the campaign seed alignment fix.
- Targeted funding validation passed: `test\services\funding\test_account_rules.py`, `test\services\funding\test_account_resolution.py`, `test\services\funding\test_funding_orchestrator.py`, and `test\api\test_admin_funding_rules.py`.
- Targeted enterprise inbox validation passed: `test\test_enterprise_event_inbox_admin.py` and `test\test_worker_ids_consumer.py`.
- Targeted mission validation passed: `test\test_mission_service.py`, `test\test_missions_api.py`, and `test\test_mission_service_badges.py`.
- Targeted leaderboard validation passed: `test\test_leaderboard_service.py`, `test\test_leaderboard_api.py`, `test\test_leaderboard_events.py`, and `test\test_worker_leaderboard_rebuild_event.py`.
- Targeted campaign/policy validation passed: `test\test_campaign_service.py`, `test\test_campaigns.py`, and `test\test_campaign_policy_service.py`.
Acceptance criteria: `scripts/init_db.py` progresses beyond migration 041 on a clean database, and any later replay failure is reported as a new clean DB replay-chain finding.
Dependencies: TASK-003.
Blocked by: None.
Risk level: Medium.
Rollback notes: Revert only the TASK-039 migration-order/doc changes; do not touch live DB.
Definition of done: Clean DB replay either completes or advances to a clearly documented later migration failure with minimal source-of-truth-aligned fixes. Priority: P0.

## TASK-028: Resolve schema uncertainty from TASK-001 inventory

Linked enhancement: DLaaS-002: Platform state, idempotency, and live verification guardrails
Linked platform capability: 14. Audit trail; 28. Idempotency/retry handling; 30. Live DB/state verification
Goal: Convert TASK-001 unknowns and TASK-027 drift findings into confirmed documentation updates or separate implementation tasks.
Why now: Canonical state machines, audit taxonomy, public APIs, and money UX must not inherit unresolved state/schema ambiguity.
Files likely involved: `docs/sa/LIVE_CRITICAL_STATE_INVENTORY.md`; `docs/sa/STATE_MACHINE_MAP.md`; `docs/roadmap/ENHANCEMENT_BACKLOG.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; relevant migrations/services only if a later implementation task is created.
Database/schema impact: Documentation-first. Any actual schema correction must be split into a separate reviewed implementation task.
Backend impact: None in this task unless new implementation tasks are proposed.
Frontend impact: None.
API impact: None.
Tests to add/update: Add or update verification tests only for documented drift/uncertainty; implementation tests belong to later tasks.
Validation method: Trace each unknown from TASK-001 to a resolved fact, a live DB verification result, or a named follow-up implementation task.
Acceptance criteria: Reward ID type ambiguity, reward status/schema mismatch, funding reconciliation `correlation_id` uncertainty, unconstrained status fields, and audit coverage unknowns are each explicitly resolved or assigned to task IDs.
Dependencies: TASK-027.
Blocked by: Live DB verification results or explicit decision to defer an unknown.
Risk level: Medium.
Rollback notes: Revert documentation/task updates only.
Definition of done: No TASK-001 unknown remains implicit; every uncertainty is either confirmed, intentionally deferred, or represented as a reviewable follow-up task. Priority: P1.

## TASK-004: Map tenant references and account boundary

Linked enhancement: DLaaS-003: SaaS account and tenant lifecycle foundation
Linked platform capability: 1. Tenant/account model; 26. Security/permissions
Goal: Map every current `tenant_code` dependency and define the account-to-tenant boundary without changing schema yet.
Why now: Tenant/account scope is foundational for campaign, participant, API, portal, SaaS, and reporting work.
Files likely involved: `dp/migrations/031_tenent.sql`; `services/tenant_service.py`; `apps/api/routers/admin_tenants.py`; `utils/security.py`; `utils/permissions.py`
Database/schema impact: Design-only; identifies future account, membership, lifecycle, and relationship schema.
Backend impact: Documents how existing tenant behavior must be preserved.
Frontend impact: None yet; later account setup depends on this.
API impact: No new API yet; future APIs must derive tenant scope from auth except explicit admin operations.
Tests to add/update: Tenant isolation tests; account-member permission tests when model is implemented.
Validation method: Search tenant usage in routers, services, migrations, tests, and docs.
Acceptance criteria: A design note defines account, tenant, membership, lifecycle, and how current `tenant_code` remains compatible.
Dependencies: TASK-001.
Blocked by: Decision on preserving `tenant_code` as external identifier.
Risk level: High.
Rollback notes: Revert design only.
Definition of done: Implementers can add account/tenant schema without deciding tenant semantics from scratch. Priority: P0.

## TASK-005: Design tenant lifecycle and membership schema

Linked enhancement: DLaaS-003
Linked platform capability: 1. Tenant/account model; 26. Security/permissions
Goal: Specify schema and service changes for account/org, tenant lifecycle, users, memberships, and seat ownership.
Why now: Campaign and SaaS packaging depend on account ownership and membership boundaries.
Files likely involved: `dp/migrations`; `services/tenant_service.py`; `utils/security.py`; `utils/permissions.py`; `apps/api/routers/session.py`
Database/schema impact: New schema design for accounts, users/memberships, tenant-account link, and lifecycle fields; no implementation in this task unless split into a later build task.
Backend impact: Defines service boundaries and permission checks.
Frontend impact: Enables future account setup and user management screens, but no frontend build yet.
API impact: Future tenant/account APIs must include auth, validation, idempotency for create operations, and clear 400/401/403/409/404 errors.
Tests to add/update: Migration replay tests; tenant lifecycle tests; membership permission tests.
Validation method: Review against current auth helpers and API permission matrix.
Acceptance criteria: Schema/service/API design is reviewable and compatible with existing tenant-scoped data.
Dependencies: TASK-004.
Blocked by: Account boundary decision.
Risk level: High.
Rollback notes: If later implemented, rollback must preserve existing `tenants` and `tenant_code` references.
Definition of done: Account/tenant implementation can proceed as small schema/service/API changes. Priority: P0.

## TASK-006: Map campaign and opportunity lifecycle sources

Linked enhancement: DLaaS-004: Canonical campaign lifecycle and readiness
Linked platform capability: 2. Campaign model
Goal: Map marketing campaign, campaign policy, campaign track, and distribution opportunity concepts into one canonical campaign lifecycle proposal.
Why now: Campaign readiness depends on knowing which existing entity owns lifecycle, policy, routing, and funding context.
Files likely involved: `dp/migrations/002_campaigns.sql`; `dp/migrations/003_policies.sql`; `services/campaign_service.py`; `services/campaign_policy_service.py`; `services/distribution/opportunity_service.py`
Database/schema impact: None yet; identifies whether lifecycle/config version fields are needed later.
Backend impact: Defines service/readiness boundaries.
Frontend impact: Prevents campaign builder UI from assuming states that do not exist.
API impact: No API changes yet.
Tests to add/update: None until readiness service is implemented.
Validation method: Compare schema constraints, campaign routes, opportunity routes, and service status handling.
Acceptance criteria: Current campaign/opportunity lifecycle facts and target canonical mapping are documented.
Dependencies: TASK-004.
Blocked by: None.
Risk level: Medium.
Rollback notes: Revert mapping document.
Definition of done: Readiness service can be designed without guessing campaign semantics. Priority: P0.

## TASK-007: Define campaign readiness service contract

Linked enhancement: DLaaS-004
Linked platform capability: 2. Campaign model; 10. Funding/budget allocation
Goal: Define a backend contract that evaluates whether a campaign is ready for activation based on policy, link/code, event, funding, and audit prerequisites.
Why now: Campaign activation and control-plane UX must be backend-driven.
Files likely involved: `services/campaign_service.py`; `services/campaign_policy_service.py`; `services/funding/*`; `services/distribution/opportunity_service.py`
Database/schema impact: None initially; may identify missing config/version fields.
Backend impact: Adds readiness decision contract before implementation.
Frontend impact: Future campaign builder will consume readiness reasons.
API impact: Readiness API must include auth, tenant validation, deterministic response, idempotent read behavior, and 400/401/403/404 errors.
Tests to add/update: Readiness guard tests; activation blocker tests; tenant permission tests.
Validation method: Review against current campaign policy and funding readiness sources.
Acceptance criteria: Readiness contract lists required checks and missing-setup reason categories.
Dependencies: TASK-006; TASK-005.
Blocked by: Tenant lifecycle design.
Risk level: High.
Rollback notes: Revert contract only.
Definition of done: Backend implementation task can add readiness service without deciding checks. Priority: P0.

## TASK-008: Define participant taxonomy and permission mapping

Linked enhancement: DLaaS-005: Participant taxonomy and role mapping
Linked platform capability: 3. Partner/referrer/distributor model; 4. Customer/referred user model; 26. Security/permissions
Goal: Map referrer, distributor, partner, sponsor/producer, customer/consumer, and operator roles to current tables and auth claims.
Why now: Link/code, attribution, portal, and API work need consistent participant language and access rules.
Files likely involved: `referrer_codes`; `distribution_distributors`; `partner_clients`; `utils/security.py`; `utils/permissions.py`; `apps/api/routers/session.py`
Database/schema impact: None initially; identifies whether participant read models are needed.
Backend impact: Defines role mapping and participant source lookup.
Frontend impact: Prevents role-specific UI from inventing participant fields.
API impact: Future participant APIs must include auth, tenant/role validation, pagination/filter validation, idempotency only for mutating operations, and clear 403/404 semantics.
Tests to add/update: Role mapping tests; participant isolation tests; customer privacy tests.
Validation method: Compare auth claims, portal route scope checks, and domain tables.
Acceptance criteria: Taxonomy maps current participant sources and states where no canonical entity exists.
Dependencies: TASK-004; TASK-006.
Blocked by: Tenant/account model decisions.
Risk level: Medium.
Rollback notes: Revert mapping.
Definition of done: Participant-dependent tasks can cite a single taxonomy. Priority: P1.

## TASK-009: Define canonical link/code contract

Linked enhancement: DLaaS-006: Canonical link/code and attribution contract
Linked platform capability: 5. Distribution link/code generation
Goal: Define a canonical contract for issuing, resolving, inspecting, and voiding current referral codes, campaign links, and route referral links.
Why now: Attribution and public API work require one link/code abstraction.
Files likely involved: `services/referral_code.py`; `services/composite_code_service.py`; `services/distribution/distributor_portal_service.py`; `dp/migrations/014_campaign_referral_links.sql`; `dp/migrations/070_distribution_route_referral_links.sql`
Database/schema impact: None initially; identify metadata gaps.
Backend impact: Defines wrapper service behavior over existing code/link sources.
Frontend impact: Future link manager and partner portal can use one contract.
API impact: Link/code APIs must include auth, validation, idempotency for issue/void commands, duplicate handling, and 400/401/403/404/409 errors.
Tests to add/update: Link issue/resolve tests; void/expired tests; duplicate code tests; tenant isolation tests.
Validation method: Compare current link/code schema and service behavior.
Acceptance criteria: Contract represents source, tenant, campaign, participant, status, and attribution metadata for all current link/code sources.
Dependencies: TASK-008; TASK-007.
Blocked by: Participant and campaign mappings.
Risk level: Medium.
Rollback notes: Revert contract.
Definition of done: Link/code wrapper implementation can proceed as a separate task. Priority: P1.

## TASK-010: Define outcome trace response contract

Linked enhancement: DLaaS-001: Canonical distribution outcome spine
Linked platform capability: 6. Attribution tracking; 11. Reward liability tracking; 27. Observability
Goal: Define the backend response contract for tracing one outcome across attribution, reward/commission, funding, fulfilment, settlement, audit, and webhook evidence.
Why now: Multiple later services, APIs, dashboards, and reports depend on a stable outcome trace.
Files likely involved: `services/outcome_money_reconciliation_service.py`; `services/progress_service.py`; `services/reward_service.py`; `services/distribution/commission_service.py`; `services/funding/*`; `services/fulfilment/*`
Database/schema impact: None initially; identifies missing joins/correlation data.
Backend impact: Defines aggregation service interface and missing-evidence categories.
Frontend impact: Future control-plane outcome trace depends on this.
API impact: Future read API must enforce auth, tenant validation, input validation, no mutation/idempotency not applicable, and 400/401/403/404 errors.
Tests to add/update: Contract fixture tests; broken-trail tests; cross-tenant access tests.
Validation method: Dry-map contract fields to current tables/services.
Acceptance criteria: Contract distinguishes current facts from missing evidence and avoids invented statuses.
Dependencies: TASK-001; TASK-009.
Blocked by: Ambiguous identifier joins requiring live schema/data verification.
Risk level: High.
Rollback notes: Revert contract.
Definition of done: Implementation can build the aggregation service without choosing response structure. Priority: P0.

## TASK-011: Implement outcome trace aggregation service

Linked enhancement: DLaaS-001
Linked platform capability: 6. Attribution tracking; 11. Reward liability tracking; 27. Observability
Goal: Add a backend aggregation service over existing tables/services for outcome trace lookups.
Why now: It is the core platform spine and unblocks money, audit, API, control-plane, reporting, and portal work.
Files likely involved: `services/outcome_money_reconciliation_service.py`; `services/reward_summary_service.py`; `services/distribution/reporting_service.py`; `services/funding/*`; `services/fulfilment/settlement/*`
Database/schema impact: Read-only queries first; no schema change unless current identifiers cannot support traceability.
Backend impact: New or extended service returning the agreed outcome trace contract.
Frontend impact: None yet.
API impact: No public API yet unless added separately; internal service should validate tenant and input at call boundary.
Tests to add/update: Golden-path outcome trace tests; missing reward/commission/funding/settlement evidence tests; cross-tenant tests.
Validation method: Run targeted service tests and compare against seeded test data.
Acceptance criteria: Service returns completed and broken outcome traces with explicit missing-evidence categories.
Dependencies: TASK-010.
Blocked by: Live DB/schema ambiguity if existing keys do not join.
Risk level: High.
Rollback notes: Remove service/read queries; no data migration expected.
Definition of done: Outcome trace service passes golden and broken-trail tests. Priority: P0.

## TASK-012: Define event ingestion public contract

Linked enhancement: DLaaS-007: Productized event ingestion contract
Linked platform capability: 7. Event ingestion; 28. Idempotency/retry handling
Goal: Document the stable event ingestion contract over existing progress and enterprise-event routes.
Why now: Attribution, qualification, reward, and fulfilment must not be driven by ambiguous external events.
Files likely involved: `apps/api/routers/progress.py`; `apps/api/routers/enterprise_events.py`; `services/enterprise_event_inbox_service.py`; `services/progress_service.py`
Database/schema impact: None initially.
Backend impact: Defines validation, idempotency, queueing, duplicate, failed, ignored, and replay behavior.
Frontend impact: Future integration monitor uses diagnostics from this contract.
API impact: Must include auth source, tenant derivation, payload validation, idempotency key behavior, error shape, retry/replay semantics, and 400/401/403/409/422/500 behavior.
Tests to add/update: Ingestion contract tests; duplicate event tests; invalid payload tests; tenant auth tests.
Validation method: Compare route models, service behavior, migration idempotency columns, and existing tests.
Acceptance criteria: Contract describes accepted, invalid, duplicate, queued, failed, ignored, and replayed outcomes.
Dependencies: TASK-002; TASK-010.
Blocked by: Outcome trace contract for downstream diagnostics.
Risk level: High.
Rollback notes: Revert contract.
Definition of done: API implementation and tests can align to one event contract. Priority: P1.

## TASK-013: Define qualification decision contract

Linked enhancement: DLaaS-008: Qualification and campaign rules boundary
Linked platform capability: 8. Qualification rules
Goal: Define how backend events, journey/progress definitions, campaign policies, and limits produce a qualification decision.
Why now: Reward and funding obligations must only start from explainable qualification.
Files likely involved: `services/journey_definitions.py`; `services/progress_definitions.py`; `services/journey_orchestrator.py`; `services/campaign_policy_service.py`
Database/schema impact: None initially; may identify need for rule version/evidence storage later.
Backend impact: Establishes rules engine boundary and decision output.
Frontend impact: Future campaign builder and investigation views can show qualification reasons.
API impact: Future qualification APIs must include auth, validation, idempotent read/evaluation behavior, deterministic errors, and audit for persisted decisions.
Tests to add/update: Rule evaluation tests; negative qualification tests; rule version/audit tests.
Validation method: Map current journey/progress completion behavior to decision categories.
Acceptance criteria: Contract explains qualified, not qualified, pending, blocked, and invalid cases using current backend evidence where possible.
Dependencies: TASK-007; TASK-012.
Blocked by: Campaign readiness and event contract.
Risk level: Medium.
Rollback notes: Revert contract.
Definition of done: Reward policy work can depend on explicit qualification decisions. Priority: P1.

## TASK-014: Define reward and commission policy boundary

Linked enhancement: DLaaS-009: Reward and commission policy boundary
Linked platform capability: 9. Reward rules; 11. Reward liability tracking
Goal: Define how reward policies and distributor commission rules map to outcome money decisions without combining distinct money types incorrectly.
Why now: Liability and funding views need a reliable source of calculated obligations.
Files likely involved: `services/reward_service.py`; `services/reward_policy_service.py`; `services/distribution/commission_service.py`; `dp/migrations/022_reward.sql`; `dp/migrations/066_distribution_commissions.sql`
Database/schema impact: None initially; identify whether rule version/evidence fields are missing.
Backend impact: Defines policy taxonomy and decision evidence.
Frontend impact: Future reward/commission operation views use this boundary.
API impact: Future reward/commission APIs must include auth, validation, idempotency for calculation/apply commands, duplicate protection, and money-safe errors.
Tests to add/update: Reward calculation tests; commission calculation tests; no-double-pay tests; precedence tests.
Validation method: Compare current reward and commission services and tests.
Acceptance criteria: Reward and commission decisions can be traced to rule source, outcome, participant, amount, and status.
Dependencies: TASK-013.
Blocked by: Qualification decision contract.
Risk level: High.
Rollback notes: Revert design; no data changes.
Definition of done: Liability projection can consume reward/commission decisions safely. Priority: P1.

## TASK-015: Define liability state model and source mapping

Linked enhancement: DLaaS-010: Campaign funding readiness and liability projection
Linked platform capability: 10. Funding/budget allocation; 11. Reward liability tracking
Goal: Define liability states and map them to rewards, commissions, funding reservations, wallets, fulfilment, settlement, and invoice evidence.
Why now: Money views and campaign readiness require non-ambiguous liability state.
Files likely involved: `services/funding/*`; `services/marketplace_funding/*`; `services/reward_service.py`; `services/distribution/commission_service.py`; `services/fulfilment/settlement/*`
Database/schema impact: None initially; identifies rollup/read model needs.
Backend impact: Defines source mapping for liability projection service.
Frontend impact: Future funding dashboard depends on these states.
API impact: Future liability APIs must be read-only, tenant/role scoped, validate filters, and return safe errors.
Tests to add/update: Liability state mapping tests; double-count prevention tests; missing evidence tests.
Validation method: Trace sample reward/commission/funding/settlement records through current services.
Acceptance criteria: Model distinguishes calculated, reserved, released, fulfilled, settled, reversed, failed, disputed, and missing-evidence states where current backend supports them.
Dependencies: TASK-011; TASK-014.
Blocked by: Outcome trace and reward/commission boundary.
Risk level: High.
Rollback notes: Revert model.
Definition of done: Backend liability projection can be implemented without inventing money states. Priority: P0.

## TASK-016: Implement liability projection read service

Linked enhancement: DLaaS-010
Linked platform capability: 10. Funding/budget allocation; 11. Reward liability tracking
Goal: Build a backend read service that computes campaign/outcome liability from existing reward, commission, funding, fulfilment, settlement, and invoice evidence.
Why now: It unblocks funding readiness, settlement observability, control-plane money views, and reporting.
Files likely involved: `services/outcome_money_reconciliation_service.py`; `services/funding/dashboard.py`; `services/funding/reservations.py`; `services/marketplace_funding/*`; `services/fulfilment/settlement/*`
Database/schema impact: Read-only first; add indexes/rollups only if tests expose performance issues.
Backend impact: Adds liability projection service with tenant and role scope.
Frontend impact: None yet.
API impact: No public API in this task; service must expose clear validation errors to callers.
Tests to add/update: Reservation/release/settle tests; liability rollup tests; double-count tests; reconciliation tests; tenant filter tests.
Validation method: Run service tests over seeded current-domain data.
Acceptance criteria: Service returns liability totals and missing-evidence flags without double-counting reward, commission, wallet, invoice, or settlement evidence.
Dependencies: TASK-015.
Blocked by: DB/state verification if source tables differ from migrations.
Risk level: High.
Rollback notes: Remove read service; no data mutation expected.
Definition of done: Liability projection passes money-focused tests and is audit/source traceable. Priority: P0.

## TASK-017: Map fulfilment and settlement statuses to outcome-safe statuses

Linked enhancement: DLaaS-011: Fulfilment and settlement status integration
Linked platform capability: 12. Fulfilment lifecycle; 13. Settlement lifecycle
Goal: Map current fulfilment and settlement states into operator-safe and partner/customer-safe status categories.
Why now: Portal and control-plane status must not expose raw provider or settlement internals.
Files likely involved: `services/fulfilment_status.py`; `services/fulfilment/*`; `services/fulfilment/settlement/status.py`; `services/fulfilment/settlement/*`
Database/schema impact: None.
Backend impact: Defines mapping helper or contract for later services.
Frontend impact: Future UI consumes safe statuses instead of raw states.
API impact: Future APIs must include auth, validation, read idempotency, and error handling for status lookup.
Tests to add/update: Safe status mapping tests; internal detail leakage tests.
Validation method: Compare status enums, admin routes, settlement services, and failure handling.
Acceptance criteria: Every current fulfilment/settlement status maps to operator and external visibility category.
Dependencies: TASK-015.
Blocked by: Liability state model.
Risk level: Medium.
Rollback notes: Revert mapping.
Definition of done: Outcome trace can include safe fulfilment/settlement status. Priority: P1.

## TASK-018: Add audit/correlation references to outcome and money traces

Linked enhancement: DLaaS-012: Audit taxonomy and observable support trace
Linked platform capability: 14. Audit trail; 27. Observability
Goal: Extend outcome/liability trace contracts to include available audit and correlation evidence.
Why now: Operators need proof and support traces before repair workflows or public APIs.
Files likely involved: `services/admin_audit_service.py`; `services/fulfilment_audit_service.py`; `services/outcome_money_reconciliation_service.py`; `utils/metrics.py`
Database/schema impact: Read existing audit tables first; schema only if critical references are missing.
Backend impact: Adds audit/correlation lookup into trace services.
Frontend impact: Future audit viewer/support console depends on this.
API impact: Any later API exposing audit references must enforce role scope and safe error handling.
Tests to add/update: Audit reference tests; role-scoped audit access tests; trace ID propagation tests.
Validation method: Verify audit references against existing audit tables and seeded traces.
Acceptance criteria: Outcome trace identifies available audit records and missing audit evidence without leaking restricted payloads.
Dependencies: TASK-011; TASK-016; TASK-002.
Blocked by: Audit taxonomy.
Risk level: High.
Rollback notes: Remove audit enrichment from trace.
Definition of done: Outcome/money trace contains audit/correlation evidence where current repo supports it. Priority: P0.

## TASK-019: Define DLaaS public/internal API families and permission matrix updates

Linked enhancement: DLaaS-013: Versioned public/internal API and webhook event catalog
Linked platform capability: 17. Public API; 18. Internal API; 20. API keys/integration credentials; 26. Security/permissions
Goal: Define API families, auth helpers, tenant scope, validation, idempotency, and error handling for target DLaaS routes before implementing endpoints.
Why now: Public API work must not expose internal route shapes accidentally.
Files likely involved: `docs/API_PERMISSION_MATRIX.md`; `apps/api/routers/*`; `utils/security.py`; `utils/permissions.py`; `services/partner_seam_service.py`
Database/schema impact: None.
Backend impact: Defines route grouping and service ownership.
Frontend impact: Integration centre and control-plane contracts can align to stable APIs later.
API impact: Must explicitly include auth, validation, idempotency, error shape, tenant scope, and emitted events for each family.
Tests to add/update: Contract tests; auth/scope tests; error shape tests; OpenAPI/schema tests.
Validation method: Compare current route families and permission docs.
Acceptance criteria: API matrix update covers campaigns, participants, links/codes, events, outcomes, rewards, funding, fulfilment, settlement, analytics, audit, credentials, and webhooks.
Dependencies: TASK-012; TASK-018.
Blocked by: Outcome/state/event contracts.
Risk level: High.
Rollback notes: Revert docs only.
Definition of done: Endpoint implementation tasks can cite exact API guardrails. Priority: P1.

## TASK-020: Define webhook lifecycle event catalog

Linked enhancement: DLaaS-013
Linked platform capability: 19. Webhooks
Goal: Define DLaaS lifecycle webhook event types and map them to current partner seam delivery mechanics.
Why now: Partners need stable events tied to canonical outcome/campaign states.
Files likely involved: `services/partner_seam_service.py`; `apps/api/routers/partner_seam.py`; `apps/Workers/partner_webhook_worker.py`; `dp/migrations/077_partner_seam.sql`
Database/schema impact: Existing webhook tables likely reusable; schema changes only if event catalog needs metadata not currently stored.
Backend impact: Defines event names, payload sources, and delivery rules.
Frontend impact: Future integration centre can show event catalog and subscription status.
API impact: Webhook APIs must include auth, validation, idempotency for subscription mutations, target URL validation, errors, signing, retry, and dead-letter behavior.
Tests to add/update: Webhook catalog tests; signing tests; retry/backoff tests; dead-letter export tests.
Validation method: Compare partner seam subscription/delivery statuses and current lifecycle events.
Acceptance criteria: Catalog covers initial campaign/outcome/reward/funding/fulfilment/settlement/integration events that are backed by current source truth.
Dependencies: TASK-019.
Blocked by: API family and outcome state contracts.
Risk level: Medium.
Rollback notes: Revert catalog only.
Definition of done: Webhook implementation can add event emission without inventing names ad hoc. Priority: P1.

## TASK-021: Define operator control-plane BFF contracts

Linked enhancement: DLaaS-014: Operator control-plane information architecture and BFF contracts
Linked platform capability: 15. Admin/operator workflow
Goal: Define BFF contracts for campaign readiness, outcome trace, funding/liability, fulfilment, settlement, integration health, audit, and failures.
Why now: Frontend control-plane work must wait for backend-backed states and contracts.
Files likely involved: `apps/api/routers/admin_experience.py`; `apps/api/routers/admin_finance.py`; `apps/api/routers/admin_funding*.py`; `apps/api/routers/admin_settlement*.py`; `apps/api/routers/admin_fulfilment.py`; `apps/api/routers/partner_seam.py`
Database/schema impact: None initially.
Backend impact: Defines aggregate endpoints over existing services and new outcome/liability services.
Frontend impact: Establishes safe frontend dependencies; no frontend implementation yet.
API impact: BFF APIs must include admin auth, validation, tenant filters, read idempotency, partial-section errors, and permission-denied behavior.
Tests to add/update: BFF aggregation tests; partial-section tests; permission tests; audit tests.
Validation method: Check each BFF field has backend source truth.
Acceptance criteria: BFF contracts do not require frontend-invented state and identify unavailable/missing sections explicitly.
Dependencies: TASK-018; TASK-019.
Blocked by: Outcome trace, liability, audit contracts.
Risk level: Medium.
Rollback notes: Revert BFF contract docs.
Definition of done: Backend BFF implementation can proceed before frontend screens. Priority: P1.

## TASK-022: Implement internal outcome trace API

Linked enhancement: DLaaS-014; DLaaS-013
Linked platform capability: 15. Admin/operator workflow; 18. Internal API
Goal: Expose the outcome trace service through an internal/admin API for operators.
Why now: It is the first usable control-plane backend surface and supports validation of the canonical spine.
Files likely involved: `apps/api/routers/admin_finance.py` or new admin router; `services/outcome_money_reconciliation_service.py`; `utils/security.py`; `utils/permissions.py`
Database/schema impact: Read-only.
Backend impact: Adds route with tenant/role validation and safe error shape.
Frontend impact: None yet.
API impact: Must include admin/system/finance/distribution auth decision, input validation, read idempotency, 400/401/403/404/422/500 handling, and no mutation.
Tests to add/update: API contract tests; permission tests; cross-tenant tests; not-found/missing-evidence tests.
Validation method: Run API tests against seeded traces.
Acceptance criteria: Authorized operator can fetch outcome trace; unauthorized/cross-tenant requests are rejected; missing evidence is explicit.
Dependencies: TASK-011; TASK-018; TASK-021.
Blocked by: Outcome trace service.
Risk level: High.
Rollback notes: Remove route; service can remain internal.
Definition of done: Internal outcome trace API passes contract and permission tests. Priority: P1.

## TASK-023: Define partner/customer safe status contract

Linked enhancement: DLaaS-015: Partner/customer safe status and action-required APIs
Linked platform capability: 16. Partner/customer portal; 21. Notifications
Goal: Define safe statuses and action-required categories for partners, distributors, sponsors, referrers, and customers.
Why now: Portal/frontend tasks must not consume raw internal states.
Files likely involved: `apps/api/routers/distribution/distributor_portal.py`; `apps/api/routers/sponsor_portal_billing.py`; `apps/api/routers/consumer_experience.py`; `apps/api/routers/reward_summary.py`
Database/schema impact: None initially.
Backend impact: Defines derived status mapping over outcome, fulfilment, settlement, reward, commission, wallet, and webhook states.
Frontend impact: Enables future portal copy and components.
API impact: Future portal APIs must include role auth, tenant/participant validation, read idempotency, and safe 403/404 behavior.
Tests to add/update: Safe status tests; internal detail leakage tests; action-required tests; role-scoped portal tests.
Validation method: Map each current status to safe role-specific status.
Acceptance criteria: Contract answers what happened, what happens next, whether action is required, and what backend state family supports it.
Dependencies: TASK-017; TASK-019.
Blocked by: Canonical state mapping and permissions.
Risk level: Medium.
Rollback notes: Revert contract.
Definition of done: Portal API tasks can proceed without exposing raw internals. Priority: P2.

## TASK-024: Define tenant-safe analytics dimensions and freshness rules

Linked enhancement: DLaaS-016: Tenant-safe analytics and ledger-aware reporting
Linked platform capability: 22. Analytics/reporting
Goal: Define reporting dimensions, tenant filters, freshness indicators, exports, and ledger reconciliation rules.
Why now: Reporting must reconcile with outcome/liability truth before UI charts are built.
Files likely involved: `services/distribution/reporting_service.py`; `services/finance_metrics_service.py`; `utils/metrics.py`; `dp/migrations/011_materialized_views.sql`
Database/schema impact: Identify future materialized views/rollups only if needed.
Backend impact: Defines reporting contract and source ownership.
Frontend impact: Future reporting screens use backend freshness and dimensions.
API impact: Reporting APIs must include auth, tenant filter validation, pagination/export validation, read idempotency, and safe errors.
Tests to add/update: Reporting accuracy tests; tenant filter tests; export tests; freshness tests; ledger reconciliation tests.
Validation method: Map current reporting services to proposed dimensions.
Acceptance criteria: Reporting contract distinguishes operational metrics from ledger-backed money totals.
Dependencies: TASK-016; TASK-018.
Blocked by: Outcome/liability spine.
Risk level: Medium.
Rollback notes: Revert reporting contract.
Definition of done: Analytics implementation can proceed without inventing dimensions. Priority: P2.

## TASK-025: Define SaaS usage and billing separation model

Linked enhancement: DLaaS-017: SaaS usage, plan, quota, and billing boundary
Linked platform capability: 20. API keys/integration credentials; 23. SaaS usage tracking; 24. Billing/monetization hooks
Goal: Define billable usage events, rollups, quotas, plans, subscriptions, billing hooks, and explicit separation from sponsor billing.
Why now: SaaS packaging must wait for account/API boundaries but should be designed before implementation.
Files likely involved: `apps/api/middleware/rate_limit.py`; `utils/metrics.py`; `services/partner_seam_service.py`; `services/marketplace_funding/sponsor_billing_service.py`; `dp/migrations/062_sponsor_billing.sql`
Database/schema impact: New SaaS packaging schema design; sponsor billing tables remain separate.
Backend impact: Defines metering and quota service boundaries.
Frontend impact: Enables future account usage, plan, billing, and credential management.
API impact: Usage/billing APIs must include account auth, validation, idempotency for usage writes, quota errors, and clear billing error handling.
Tests to add/update: Usage event tests; quota tests; plan entitlement tests; sponsor-vs-SaaS separation tests; credential usage attribution tests.
Validation method: Confirm each proposed billable event maps to matrix capabilities and current service hooks.
Acceptance criteria: Design defines SaaS usage and billing without reusing sponsor utilisation billing as platform billing.
Dependencies: TASK-005; TASK-019.
Blocked by: Account/tenant model and API credential productization.
Risk level: High.
Rollback notes: Revert design; do not touch sponsor billing.
Definition of done: SaaS schema/API implementation can proceed as separate reviewable changes. Priority: P2.

## TASK-026: Define white-label/embed security and dependency plan

Linked enhancement: DLaaS-018: White-label, embed, and SDK foundation
Linked platform capability: 25. White-label/embeddable UX
Goal: Define future tenant branding, custom domains, allowed origins, embed clients, SDK candidates, and security guardrails.
Why now: This is Later work and should be explicitly blocked until safe status, tenant isolation, and API contracts are mature.
Files likely involved: `docs/AMPLIFI_FRONTEND_BRAND_NOTES.md`; future tenant branding/domain/embed docs; `utils/security.py`
Database/schema impact: Future schema only; no implementation now.
Backend impact: Defines future backend primitives and security constraints.
Frontend impact: Defines future UX dependencies; no frontend task yet.
API impact: Future embed APIs must include origin validation, scoped tokens, tenant validation, rate limits, safe errors, and idempotency for config writes.
Tests to add/update: Branding config tests; domain verification tests; CORS/origin tests; embed token tests; cross-tenant leak tests.
Validation method: Review against tenant isolation, public API, and safe status contracts.
Acceptance criteria: White-label/embed plan clearly lists blockers and does not authorize implementation before dependencies exist.
Dependencies: TASK-005; TASK-019; TASK-023.
Blocked by: Tenant isolation, public API contracts, partner/customer safe statuses.
Risk level: High.
Rollback notes: Revert plan only.
Definition of done: Later implementation scope is bounded and dependency-gated. Priority: Later.

## TASK-039: Fix clean DB migration failure for referral_track_id

Status: Complete (2026-06-21). Output: `dp/migrations/024_mission_and_reward_summary.sql`.
Linked enhancement: DLaaS-002: Platform state, idempotency, and live verification guardrails
Linked platform capability: 30. Live DB/state verification
Goal: Fix clean DB initialization failure in `024_mission_and_reward_summary.sql` where legacy gamification tables from migration 005 did not yet have canonical `referral_track_id` columns.
Why now: GitHub backend and clean-db-readiness checks failed before documentation-only PR validation could pass.
Files likely involved: `scripts/init_db.py`; `dp/migrations/005_gamification.sql`; `dp/migrations/024_mission_and_reward_summary.sql`; mission and badge services/tests.
Database/schema impact: Compatibility-safe migration replay fix only; no live DB changes.
Backend impact: Keeps canonical mission/badge services aligned to referral-track columns.
Frontend impact: None.
API impact: None.
Tests to add/update: Migration hygiene check; clean DB init; targeted mission and badge tests.
Validation method: Run `scripts/check_migrations.py`, `scripts/init_db.py`, and targeted mission/badge tests using the repo Codex virtualenv.
Acceptance criteria: Clean DB init succeeds; no production/live DB touched; no unrelated schema changes; schema decision is documented.
Dependencies: TASK-001; TASK-003.
Blocked by: None.
Risk level: Medium.
Rollback notes: Revert migration compatibility changes and this roadmap entry.
Definition of done: Backend and clean-db-readiness CI can replay migrations past 024 without `referral_track_id` undefined-column failure. Priority: P0.
