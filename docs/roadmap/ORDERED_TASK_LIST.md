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

Status: Complete (2026-06-21). Output: `docs/sa/AUDIT_RETRY_POLICY_STANDARD.md`.
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

Status: Blocked.

Finding:
TASK-027 is ready in scope but cannot execute without approved safe read-only runtime database access. No database connection was attempted.

Blocked by:
Environment name, read-only DB credentials, write-protection confirmation, and approval for any runtime/API smoke checks.

Validation:
Readiness inspection only; no files changed beyond this roadmap update and no DB access attempted.

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
- CI later reported `dp/seeds/seed_data_for_insurance.sql` failing because `progress_definitions` does not exist in the canonical clean DB schema; `progress_definitions` exists only in legacy migrations, while current progress configuration is sourced from `services/progress_definitions.py`.
- The minimal seed replay fix is to guard the obsolete insurance and transactional `progress_definitions` seed inserts so canonical clean DB replay skips them, while preserving idempotent inserts if a legacy local schema still has that table.
- Validation with `.venv_codex\Scripts\python.exe scripts\seed_db.py` completed successfully after the progress seed guards.
- CI then reported `dp/seeds/seed_data_for_reward_policies.sql` failing because `reward_policies` did not exist in the canonical clean DB schema; unlike `progress_definitions`, current reward services and reconciliation code read `reward_policies` directly, and the existing legacy migration provides the table shape.
- The minimal migration-chain fix is to create `reward_policies` and its product/sub-product lookup index in migration 022 using the existing legacy schema, then make the reward policy seed additive/idempotent with `WHERE NOT EXISTS` checks for the natural policy rows.
- Validation with `.venv_codex\Scripts\python.exe scripts\seed_db.py` completed successfully after the reward policy migration/seed alignment fix.
- Backend CI then failed during pytest collection because `utils.crypto` intentionally raises `RuntimeError: REFERRAL_CODE_SECRET must be set` when the referral-code signing secret is absent.
- `utils.crypto` requires a non-empty secret value and does not impose an additional format or length check; the minimal CI-readiness fix is to set the deterministic test-only `REFERRAL_CODE_SECRET: ci-referral-code-secret` in the backend CI job, matching the existing clean-db-readiness job value without changing crypto behavior or committing a real secret.
- Validation passed with `.venv_codex\Scripts\python.exe scripts\check_migrations.py`, `.venv_codex\Scripts\python.exe scripts\init_db.py`, and `.venv_codex\Scripts\python.exe scripts\seed_db.py` after the CI environment update.
- Validation with `REFERRAL_CODE_SECRET=ci-referral-code-secret .venv_codex\Scripts\python.exe -m pytest --collect-only` collected 1688 tests, including `test/test_admin_audit_api.py`, without the prior crypto import failure.
- Full backend validation with `REFERRAL_CODE_SECRET=ci-referral-code-secret .venv_codex\Scripts\python.exe -m pytest` progressed beyond collection and then stopped at the next real test failure: `test/api/test_partner_seam_api.py::test_system_admin_can_retry_failed_webhook_delivery`, where the test fake expects only `delivery_id` but the router passes both `delivery_id` and an authenticated `identity` payload.
- Targeted funding validation passed: `test\services\funding\test_account_rules.py`, `test\services\funding\test_account_resolution.py`, `test\services\funding\test_funding_orchestrator.py`, and `test\api\test_admin_funding_rules.py`.
- Targeted enterprise inbox validation passed: `test\test_enterprise_event_inbox_admin.py` and `test\test_worker_ids_consumer.py`.
- Targeted mission validation passed: `test\test_mission_service.py`, `test\test_missions_api.py`, and `test\test_mission_service_badges.py`.
- Targeted leaderboard validation passed: `test\test_leaderboard_service.py`, `test\test_leaderboard_api.py`, `test\test_leaderboard_events.py`, and `test\test_worker_leaderboard_rebuild_event.py`.
- Targeted campaign/policy validation passed: `test\test_campaign_service.py`, `test\test_campaigns.py`, and `test\test_campaign_policy_service.py`.
- Targeted insurance/progress validation passed: `test\test_second_vertical_agnosticism.py`, `test\test_progress_service.py`, `test\test_progress_api.py`, and `test\test_insurance_journey_proof_service.py`.
- Targeted reward/policy validation passed: `test\test_reward_policy_service.py`, `test\test_reward_service.py`, `test\test_rewards.py`, and `test\test_rewards_router.py`.
Acceptance criteria: `scripts/init_db.py` progresses beyond migration 041 on a clean database, and any later replay failure is reported as a new clean DB replay-chain finding.
Dependencies: TASK-003.
Blocked by: None.
Risk level: Medium.
Rollback notes: Revert only the TASK-039 migration-order/doc changes; do not touch live DB.
Definition of done: Clean DB replay either completes or advances to a clearly documented later migration failure with minimal source-of-truth-aligned fixes. Priority: P0.

## TASK-040: Align badges API missing-referral test with auth contract

Status: Complete (2026-06-21). Branch: `task-039-fix-referral-track-id-migration`.
Linked enhancement: DLaaS-002: Platform state, idempotency, and live verification guardrails
Linked platform capability: 17. Public API; 26. Security/permissions
Goal: Keep badges API tests aligned with the route auth contract without weakening authentication or changing production behavior.
Why now: Backend pytest progressed past TASK-039 readiness work and exposed a badges API test that expected missing-referral handling but received `401 Unauthorized` first.
Files involved: `test/test_badges_api.py`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Database/schema impact: None.
Backend impact: Test-only. No router, auth helper, or business logic changes.
Frontend impact: None.
API impact: No production API behavior change; unauthenticated badges requests still return 401, and authenticated missing-referral requests return 404.
Tests to add/update: Update badges API tests to use an isolated test app with a mocked authenticated identity; add a focused unauthenticated 401 assertion for the referral badges route.
Validation method: Run targeted badges API tests and full backend pytest if practical.
Findings:
- `apps/api/routers/badges.py` correctly requires `require_admin_or_partner_key` at the router and route levels before reaching missing-referral logic.
- The failing missing-referral test used a module-level dependency override on the shared app; other tests can clear shared dependency overrides during full-suite execution, causing the request to hit real auth and return 401 before the mocked missing-referral path.
- The minimal test-focused fix is to build an isolated badges-only FastAPI app per test, apply a valid mocked identity for authenticated badges assertions, and keep an explicit unauthenticated test to preserve the 401 contract.
- Validation passed with `REFERRAL_CODE_SECRET=ci-referral-code-secret .venv_codex\Scripts\python.exe -m pytest test\test_badges_api.py -q`; 4 badges API tests passed.
- Full backend validation with `REFERRAL_CODE_SECRET=ci-referral-code-secret .venv_codex\Scripts\python.exe -m pytest` progressed beyond the badges API failure and then stopped at the next existing blocker: `test/api/test_partner_seam_api.py::test_system_admin_can_retry_failed_webhook_delivery`.
Acceptance criteria: Authenticated missing-referral badges API test returns 404; unauthenticated badges API access remains 401; related badges API tests pass.
Dependencies: TASK-039.
Blocked by: None.
Risk level: Low.
Rollback notes: Revert the TASK-040 test/doc changes only.
Definition of done: Badges API auth and missing-referral tests are deterministic in full-suite execution without production auth changes. Priority: P0.

## TASK-041: Align partner webhook retry test with authenticated identity contract

Status: Complete (2026-06-21). Branch: `task-039-fix-referral-track-id-migration`.
Linked enhancement: DLaaS-002: Platform state, idempotency, and live verification guardrails
Linked platform capability: 14. Audit trail; 20. API keys/integration credentials; 26. Security/permissions
Goal: Keep partner webhook retry API tests aligned with the authenticated system-admin retry contract without weakening authorization or audit traceability.
Why now: Backend pytest progressed past TASK-040 and exposed a partner webhook retry test fake that expected only `delivery_id` while the router correctly passed authenticated identity metadata.
Files involved: `test/api/test_partner_seam_api.py`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Database/schema impact: None.
Backend impact: Test-only. No router, service, auth helper, or business logic changes.
Frontend impact: None.
API impact: No production API behavior change; system-admin retry still requires `require_system_admin_key` and passes identity to the service.
Tests to add/update: Update the system-admin webhook retry test fake to assert `delivery_id` plus authenticated `SYSTEM_ADMIN` identity metadata.
Validation method: Run targeted partner seam API tests and full backend pytest.
Findings:
- `apps/api/routers/partner_seam.py` passes `identity=Depends(require_system_admin_key)` into `partner_seam_service.mark_webhook_delivery_for_retry`.
- `services/partner_seam_service.py` defines `mark_webhook_delivery_for_retry(delivery_id, identity=None)` and writes `PARTNER_WEBHOOK_DELIVERY_RETRY` admin audit evidence with the provided identity, so the router's identity handoff is the correct audit/security contract.
- The minimal fix is to align the test fake with that contract by asserting `delivery_id`, `identity.role == SYSTEM_ADMIN`, and `identity.tenant_code == INTERNAL`.
- Validation passed with `REFERRAL_CODE_SECRET=ci-referral-code-secret .venv_codex\Scripts\python.exe -m pytest test\api\test_partner_seam_api.py -q`; 24 partner seam API tests passed.
- Full backend validation passed with `REFERRAL_CODE_SECRET=ci-referral-code-secret .venv_codex\Scripts\python.exe -m pytest`; 1689 tests passed.
Acceptance criteria: `test_system_admin_can_retry_failed_webhook_delivery` passes; related partner seam API tests pass; backend pytest passes.
Dependencies: TASK-040.
Blocked by: None.
Risk level: Low.
Rollback notes: Revert the TASK-041 test/doc changes only.
Definition of done: Partner webhook retry tests preserve the authenticated audit actor contract and backend pytest is green. Priority: P0.

## TASK-042: Align DLQ replay admin test with admin authentication contract

Status: Complete (2026-06-21). Branch: `task-039-fix-referral-track-id-migration`.
Linked enhancement: DLaaS-002: Platform state, idempotency, and live verification guardrails
Linked platform capability: 14. Audit trail; 18. Internal API; 26. Security/permissions
Goal: Keep DLQ replay admin endpoint tests aligned with the system-admin authentication contract without weakening replay authorization.
Why now: Backend pytest progressed past TASK-041 and exposed a DLQ replay endpoint test overriding the wrong admin dependency, causing the success path to receive `401 Unauthorized`.
Files involved: `test/test_dlq_replay.py`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Database/schema impact: None.
Backend impact: Test-only. No router, replay service, auth helper, or business logic changes.
Frontend impact: None.
API impact: No production API behavior change; `/admin/dlq/replay` remains protected by the router's system-admin dependency.
Tests to add/update: Override the DLQ router's actual `require_admin_key` alias in the test app and add an unauthenticated 401 assertion for `/admin/dlq/replay`.
Validation method: Run targeted DLQ replay tests and full backend pytest.
Findings:
- `apps/api/routers/admin_dlq_replay.py` aliases `require_system_admin_key` as `require_admin_key` and applies that alias as a router-level dependency.
- The failing test imported and overrode `utils.security.require_admin_key`, which is not the same dependency object used by the DLQ replay router.
- The minimal fix is to override `router_mod.require_admin_key` in the isolated test app with a system-admin identity and keep unauthenticated access covered with a 401 regression test.
- Validation passed with `REFERRAL_CODE_SECRET=ci-referral-code-secret .venv_codex\Scripts\python.exe -m pytest test\test_dlq_replay.py -q`; 9 DLQ replay tests passed.
- Full backend validation passed with `REFERRAL_CODE_SECRET=ci-referral-code-secret .venv_codex\Scripts\python.exe -m pytest`; 1690 tests passed.
Acceptance criteria: `test_admin_dlq_replay_endpoint_success` passes; unauthenticated replay requests still return 401; related DLQ replay tests pass; backend pytest passes.
Dependencies: TASK-041.
Blocked by: None.
Risk level: Low.
Rollback notes: Revert the TASK-042 test/doc changes only.
Definition of done: DLQ replay admin tests use the route's system-admin auth contract and backend pytest remains green. Priority: P0.

## TASK-043: Fix HVE badge award referrer_hash contract

Status: Complete (2026-06-21). Branch: `task-039-fix-referral-track-id-migration`.
Linked enhancement: DLaaS-002: Platform state, idempotency, and live verification guardrails
Linked platform capability: 6. Progress/status tracking; 14. Audit trail; 26. Security/permissions
Goal: Ensure HVE badge awards preserve the `user_badges.referrer_hash` identity contract while keeping the canonical beneficiary fields intact.
Why now: Backend pytest progressed past TASK-042 and exposed an HVE badge award insert that populated `beneficiary_ref` but not the legacy `referrer_hash` column, causing a `NOT NULL` violation where that schema column exists.
Files involved: `services/badge_service.py`; `test/test_badge_service.py`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Database/schema impact: None. The existing `user_badges.referrer_hash` constraint is preserved.
Backend impact: Badge award service now carries the stored referrer hash from `referrer_codes.referrer_ucn_hash` through the award insert, with canonical crypto lookup as a fallback when the stored hash is unavailable.
Frontend impact: None.
API impact: None.
Tests to add/update: Align badge service unit fakes with the additional `referrer_hash` service argument; run HVE mission badge and badge service tests.
Validation method: Run targeted mission badge tests, badge service tests, and full backend pytest.
Findings:
- Migrations preserve an older `user_badges.referrer_hash` identity column while later badge services write newer `beneficiary_type` and `beneficiary_ref` fields.
- `services/badge_service.py` previously selected only `referral_instances.referrer_ucn`, so `_award_badge` had no stored hash available and inserted without `referrer_hash`.
- The canonical source for the stored referrer identity is `referrer_codes.referrer_ucn_hash`, joined via `referral_instances.referrer_code_id`; if a referral row lacks that stored source, the existing `utils.crypto.ucn_lookup_key` helper derives the canonical lookup hash from the referrer UCN.
- The minimal service fix is to fetch `referrer_hash` with the referral row, pass it through `_evaluate_and_award_badges`, and populate `user_badges.referrer_hash` whenever that column exists.
- Validation passed with `REFERRAL_CODE_SECRET=ci-referral-code-secret .venv_codex\Scripts\python.exe -m pytest test\test_mission_service_badges.py -q`; the HVE badge idempotency test passed.
- Validation passed with `REFERRAL_CODE_SECRET=ci-referral-code-secret .venv_codex\Scripts\python.exe -m pytest test\test_badge_service.py -q`; 20 badge service tests passed.
- Full backend validation passed with `REFERRAL_CODE_SECRET=ci-referral-code-secret .venv_codex\Scripts\python.exe -m pytest`; 1690 tests passed.
Acceptance criteria: `test_hve_event_awards_badge_once` passes; mission badge tests pass; backend pytest passes.
Dependencies: TASK-042.
Blocked by: None.
Risk level: Medium.
Rollback notes: Revert the TASK-043 service/test/doc changes only.
Definition of done: HVE badge awards use the same referrer identity contract as other badge award paths and backend pytest remains green. Priority: P0.

## TASK-044: Align HVE badge award with canonical badge definition

Status: Complete (2026-06-21). Branch: `task-039-fix-referral-track-id-migration`.
Linked enhancement: DLaaS-002: Platform state, idempotency, and live verification guardrails
Linked platform capability: 6. Progress/status tracking; 14. Audit trail
Goal: Align the HVE badge award regression fixture with the canonical badge definition while preserving the `user_badges.badge_code` foreign key contract.
Why now: Backend pytest progressed past TASK-043 and exposed that the HVE badge fixture inserted `VALUE_ESTABLISHED` into `badge_definitions` without a matching canonical `badges` row, causing a foreign key violation when awarding `user_badges`.
Files involved: `test/test_mission_service_badges.py`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Database/schema impact: None. The existing `user_badges_badge_code_fkey` constraint is preserved.
Backend impact: Test/reference alignment only. No badge service, HVE threshold, reward, fulfilment, or scoring logic changed.
Frontend impact: None.
API impact: None.
Tests to add/update: Update the HVE mission badge fixture to seed the canonical first-HVE badge in both `badges` and `badge_definitions`; run mission badge, badge service, and backend pytest.
Validation method: Run targeted mission badge tests, badge service tests, and full backend pytest.
Findings:
- `services/badge_service.py` does not hard-code `VALUE_ESTABLISHED`; it awards active `badge_definitions` rows matching the HVE trigger.
- Migration 030 seeds the canonical first HVE badge as `VALUE_DRIVER` with trigger `HVE_COUNT`, value `1`, and display name `Value Driver`.
- `VALUE_ESTABLISHED` was test-local legacy data and did not have a matching row in the legacy `badges` table required by the preserved `user_badges.badge_code` foreign key.
- The minimal fix is to update the HVE fixture to seed `VALUE_DRIVER` into both `badges` and `badge_definitions`, then assert the canonical awarded badge code.
- Validation passed with `REFERRAL_CODE_SECRET=ci-referral-code-secret .venv_codex\Scripts\python.exe -m pytest test\test_mission_service_badges.py -q`; the HVE badge idempotency test passed.
- Validation passed with `REFERRAL_CODE_SECRET=ci-referral-code-secret .venv_codex\Scripts\python.exe -m pytest test\test_badge_service.py -q`; 20 badge service tests passed.
- Full backend validation passed with `REFERRAL_CODE_SECRET=ci-referral-code-secret .venv_codex\Scripts\python.exe -m pytest`; 1690 tests passed.
Acceptance criteria: `test_hve_event_awards_badge_once` passes; all mission badge tests pass; backend pytest passes.
Dependencies: TASK-043.
Blocked by: None.
Risk level: Low.
Rollback notes: Revert the TASK-044 test/doc changes only.
Definition of done: HVE badge award tests use the canonical `VALUE_DRIVER` badge reference data and backend pytest remains green. Priority: P0.

## TASK-045: Align worker missing-secret error handling with security contract

Status: Complete (2026-06-21). Branch: `task-039-fix-referral-track-id-migration`.
Linked enhancement: DLaaS-002: Platform state, idempotency, and live verification guardrails
Linked platform capability: 26. Security/permissions; 28. Idempotency/retry handling
Goal: Ensure worker referral-event authentication fails closed with a controlled unauthorized response when `WORKER_SECRET` is not configured.
Why now: Backend pytest progressed past TASK-044 and exposed that `/worker/referral-events` returned `500 Internal Server Error` for missing worker secret configuration, even though this is an authentication failure path.
Files involved: `apps/api/routers/worker.py`; `test/test_worker.py`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Database/schema impact: None.
Backend impact: Worker auth now returns `401 Unauthorized` when server-side worker secret configuration is missing, matching existing missing/wrong credential behavior while retaining server-side error logging.
Frontend impact: None.
API impact: Worker endpoint no longer exposes a 500 for missing worker auth configuration; client response remains generic and does not reveal secret/config details.
Tests to add/update: Align the worker auth unit expectation for missing configured secret with the endpoint security contract; run security/error handling and worker router tests.
Validation method: Run targeted security/error handling tests, worker router tests, and full backend pytest.
Findings:
- `apps/api/routers/worker.py` already returns `401 Unauthorized` for missing or wrong request worker credentials.
- The missing server-side `WORKER_SECRET` branch logged the configuration error but raised `500 Worker not configured`, causing the public endpoint to expose an internal server error for an auth failure.
- The minimal fix is to preserve the server-side log and return `401 Unauthorized` with the same generic detail used by other worker auth failures.
- Validation passed with `REFERRAL_CODE_SECRET=ci-referral-code-secret .venv_codex\Scripts\python.exe -m pytest test\test_security_and_error_handling.py -q`; 4 tests passed.
- Validation passed with `REFERRAL_CODE_SECRET=ci-referral-code-secret .venv_codex\Scripts\python.exe -m pytest test\test_worker.py test\test_worker_leaderboard_rebuild_event.py -q`; 39 worker tests passed.
- Full backend validation passed with `REFERRAL_CODE_SECRET=ci-referral-code-secret .venv_codex\Scripts\python.exe -m pytest`; 1690 tests passed.
Acceptance criteria: `test_worker_rejects_missing_secret` passes; related worker/security tests pass; backend pytest passes.
Dependencies: TASK-044.
Blocked by: None.
Risk level: Low.
Rollback notes: Revert the TASK-045 worker/test/doc changes only.
Definition of done: Missing worker secret configuration fails closed with generic unauthorized response and backend pytest remains green. Priority: P0.

## TASK-046: Fix funding exposure table clean-DB readiness

Status: Complete (2026-06-21). Branch: `task-039-fix-referral-track-id-migration`.
Linked enhancement: DLaaS-010: Campaign funding readiness and liability projection
Linked platform capability: 10. Funding/budget allocation; 14. Audit trail; 30. Live DB/state verification
Goal: Ensure the canonical `funding_exposure` table exists during clean DB migration replay so `/admin/funding/exposure` and funding dashboard services can run without test-only schema setup.
Why now: Backend pytest progressed past TASK-045 and exposed that `GET /admin/funding/exposure` queried `funding_exposure`, but clean DB schema did not create that table.
Files involved: `dp/migrations/044_create_funding_exposure.sql`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Database/schema impact: Adds the missing idempotent `funding_exposure` table definition to migration 044, including the service-required uniqueness key on `(tenant_code, account_id, exposure_date)` and non-negative amount checks.
Backend impact: No service or route behavior change. Existing funding exposure, dashboard, and exposure-limit services now have their canonical table after migration replay.
Frontend impact: None.
API impact: No response contract change for `/admin/funding/exposure`; the endpoint now works on clean DBs instead of failing with `UndefinedTableError`.
Tests to add/update: No new tests required; existing admin funding and funding exposure/dashboard tests cover the table contract.
Validation method: Run migration hygiene, clean DB migration replay, targeted funding API/service tests, and full backend pytest.
Findings:
- SA docs and roadmap inventory already describe funding exposure as an existing funding/budget primitive.
- `services/funding/exposure.py` consistently reads and writes `funding_exposure` with `tenant_code`, `account_id`, `exposure_date`, `reserved_amount`, `settled_amount`, `released_amount`, and `updated_at`.
- `dp/migrations/044_create_funding_exposure.sql` existed but only created `funding_account_rules`; it did not create the `funding_exposure` table needed by the service and API.
- The minimal migration-safe fix is to add the missing idempotent table and indexes to migration 044 without changing endpoint or business logic.
- Validation passed with `.venv_codex\Scripts\python.exe scripts\check_migrations.py`.
- Validation passed with `.venv_codex\Scripts\python.exe scripts\init_db.py`; migration replay completed through 999.
- Validation passed with `REFERRAL_CODE_SECRET=ci-referral-code-secret .venv_codex\Scripts\python.exe -m pytest test\api\test_admin_funding.py test\services\funding\test_exposure.py test\services\funding\test_dashboard.py test\services\funding\test_exposure_limits.py -q`; 31 targeted funding tests passed.
- Full backend validation passed with `REFERRAL_CODE_SECRET=ci-referral-code-secret .venv_codex\Scripts\python.exe -m pytest`; 1690 tests passed.
Acceptance criteria: `test_get_funding_exposure_empty` passes; related admin funding tests pass; clean DB migration replay passes; backend pytest passes.
Dependencies: TASK-045.
Blocked by: None.
Risk level: Medium.
Rollback notes: Revert the TASK-046 migration/doc changes only.
Definition of done: Clean DBs create `funding_exposure` before funding exposure APIs/services run, and backend pytest remains green. Priority: P0.

## TASK-047: Select next DLaaS priority and record readiness stop

Status: Complete (2026-06-21). Branch: `task-047-next-dlaas-priority`.
Linked enhancement: DLaaS Agent Runner Framework
Linked platform capability: Agent execution, traceability, clean diffs, branch/PR workflow, rollback safety
Goal: Select the next highest-priority unblocked task from this ordered list and execute only that task, or stop safely if the next work is blocked or unsafe.
Why now: TASK-039 through TASK-046 restored clean DB, seed, and backend pytest readiness; the next runner cycle must return to ordered DLaaS roadmap selection without skipping dependency gates.
Files involved: `docs/roadmap/ORDERED_TASK_LIST.md`.
Database/schema impact: None.
Backend impact: None.
Frontend impact: None.
API impact: None.
Tests to add/update: None. This was a selection/readiness check only.
Validation method: Read `AGENTS.md`, `docs/agent/DLAAS_AGENT_RUNBOOK.md`, `docs/agent/DLAAS_AGENT_STOP_CONDITIONS.md`, `docs/product/DLAAS_TARGET_STATE.md`, SA/roadmap context, and inspect Git status.
Findings:
- The first incomplete task by ordered dependency is TASK-027, but it remains blocked by runtime database access and safe read-only credentials.
- TASK-028 depends on TASK-027 and remains blocked until live DB verification results exist or an explicit deferral decision is made.
- TASK-004 is the next P0 roadmap task after the live-verification chain, but it is explicitly blocked by the decision on preserving `tenant_code` as the external identifier.
- TASK-006 lists `Blocked by: None`, but it depends on TASK-004, so it is not ready while TASK-004 is blocked.
- No later task should be selected until the live-verification chain is deliberately deferred or the tenant/account boundary decision unblocks TASK-004.
- Validation confirmed the current branch is `task-047-next-dlaas-priority` and the working tree was clean before this documentation update.
Acceptance criteria: Next task selection is documented; no blocked task is implemented; no unrelated product code is changed.
Dependencies: TASK-046.
Blocked by: None.
Risk level: Low.
Rollback notes: Revert the TASK-047 documentation update only.
Definition of done: The runner stops safely with the next-roadmap blocker recorded and no product implementation performed. Priority: P0.

## TASK-048: Decide tenant-code external identifier boundary

Status: Complete (2026-06-21). Branch: `task-048-tenant-identifier-boundary-decision`.
Linked enhancement: DLaaS-003: SaaS account and tenant lifecycle foundation
Linked platform capability: 1. Tenant/account model; 26. Security/permissions
Goal: Make and document the tenant-code/external identifier boundary decision required to unblock TASK-004.
Why now: TASK-047 confirmed TASK-004 was the next P0 design task after the live-verification chain, but it was blocked by whether `tenant_code` should be preserved as an external identifier.
Files involved: `docs/sa/TENANT_IDENTIFIER_BOUNDARY_DECISION.md`; `docs/sa/API_SURFACE_MAP.md`; `docs/sa/CURRENT_STATE_MAP.md`; `docs/sa/CAPABILITY_GAP_MATRIX.md`; `docs/sa/LIVE_CRITICAL_STATE_INVENTORY.md`; `docs/roadmap/ENHANCEMENT_BACKLOG.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Database/schema impact: None. No migrations, schema changes, or tenant-code column renames were made.
Backend impact: None. No application code changed.
Frontend impact: None.
API impact: Documentation-only. Target public APIs should use credential-derived scope, `external_tenant_ref`, or role-specific aliases, while existing tenant-code routes remain backward-compatible current implementation facts.
Tests to add/update: None for this documentation-only task.
Validation method: Read required source docs; perform documentation readback; confirm no non-doc files changed; confirm `git diff --stat`.
Findings:
- `tenant_code` remains the internal platform tenant identifier for partitioning, service joins, tenant isolation, audit, funding, fulfilment, settlement, reporting, workers, and internal/admin routes.
- External parties must not depend on `tenant_code` as the primary integration identifier in target DLaaS contracts.
- The generic external SaaS-facing identifier is `external_tenant_ref`; role-specific aliases may include `organisation_ref`, `producer_ref`, `partner_ref`, and `distributor_ref`.
- External references map to internal `tenant_code` through a future account/tenant identity layer.
- Existing tenant-code routes, columns, services, tests, seeds, and migrations remain unchanged until future versioned wrappers or migration plans exist.
- TASK-004 is unblocked by this decision and can now map current `tenant_code` dependencies and define the account-to-tenant boundary.
Acceptance criteria: Tenant identifier boundary is documented; relevant SA/roadmap docs point to the decision; TASK-004 blocker is removed; no code or schema changed.
Dependencies: TASK-047.
Blocked by: None.
Risk level: Low.
Rollback notes: Revert the TASK-048 documentation changes only.
Definition of done: TASK-004 can proceed without deciding tenant identifier semantics from scratch. Priority: P0.

## TASK-028: Resolve schema uncertainty from TASK-001 inventory

Status: Blocked.

Finding:
TASK-028 cannot execute because TASK-027 live DB verification is blocked and no verified drift results exist. TASK-028 should only resolve confirmed live/schema mismatches or explicitly deferred unknowns.

Blocked by:
TASK-027 completion, or an explicit decision to defer specific TASK-001 unknowns without live DB verification.

Validation:
Readiness inspection only; no files changed beyond this roadmap update, no DB access attempted, no secrets inspected, and no downstream tasks started.

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

Status: Complete on 2026-06-21. TASK-004 produced `docs/sa/TENANT_ACCOUNT_BOUNDARY_MAP.md` and did not change application code, migrations, or schema.
Linked enhancement: DLaaS-003: SaaS account and tenant lifecycle foundation
Linked platform capability: 1. Tenant/account model; 26. Security/permissions
Goal: Map every current `tenant_code` dependency and define the account-to-tenant boundary without changing schema yet.
Why now: Tenant/account scope is foundational for campaign, participant, API, portal, SaaS, and reporting work.
Files involved: `docs/sa/TENANT_ACCOUNT_BOUNDARY_MAP.md`; `docs/sa/API_SURFACE_MAP.md`; `docs/sa/CURRENT_STATE_MAP.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Source files inspected: `dp/migrations/031_tenent.sql`; `services/tenant_service.py`; `apps/api/routers/admin_tenants.py`; `utils/security.py`; `utils/permissions.py`; `utils/tenant_guard.py`; tenant references across migrations, services, routers, utilities, tests, and docs.
Database/schema impact: Design-only; identifies future account, membership, lifecycle, and relationship schema.
Backend impact: Documents how existing tenant behavior must be preserved.
Frontend impact: None yet; later account setup depends on this.
API impact: No new API yet; future APIs must derive tenant scope from auth except explicit admin operations.
Tests to add/update: Tenant isolation tests; account-member permission tests when model is implemented.
Validation method: Searched tenant usage in routers, services, migrations, tests, and docs; read back the new SA note for `tenant_code`, `external_tenant_ref`, account, membership, lifecycle, API/webhook, money-flow, audit, and compatibility coverage.
Validation completed: Documentation-only validation on 2026-06-21. Static search found `tenant_code` broadly used across schema, services, routers, utilities, and tests, confirming it is an internal platform isolation key. No backend tests were run because TASK-004 changed docs only.
Findings: `tenant_code` is already the internal tenant partition used by auth, permissions, referrals, campaign policy, reward, funding, fulfilment, settlement, distribution, partner seam, privacy, reporting, and audit flows. No first-class SaaS account, membership, seat, tenant lifecycle, subscription, or external-reference mapping schema is currently implemented. TASK-048's external identifier boundary is now mapped into the account-to-tenant model for TASK-005.
Acceptance criteria: Complete. `docs/sa/TENANT_ACCOUNT_BOUNDARY_MAP.md` defines account, tenant, membership, lifecycle, external references, and how current `tenant_code` remains compatible.
Dependencies: TASK-001.
Blocked by: None. Tenant identifier boundary accepted in `docs/sa/TENANT_IDENTIFIER_BOUNDARY_DECISION.md` by TASK-048.
Risk level: High.
Rollback notes: Revert design only.
Definition of done: Complete. Implementers can add account/tenant schema without deciding tenant semantics from scratch. Priority: P0.

## TASK-005: Design tenant lifecycle and membership schema

Status: Complete on 2026-06-21. TASK-005 produced `docs/sa/TENANT_ACCOUNT_LIFECYCLE_MEMBERSHIP_MODEL.md` and did not change application code, migrations, schema, auth helpers, or tenant-scoped business logic.
Linked enhancement: DLaaS-003
Linked platform capability: 1. Tenant/account model; 26. Security/permissions
Goal: Specify schema and service changes for account/org, tenant lifecycle, users, memberships, and seat ownership.
Why now: Campaign and SaaS packaging depend on account ownership and membership boundaries.
Files involved: `docs/sa/TENANT_ACCOUNT_LIFECYCLE_MEMBERSHIP_MODEL.md`; `docs/sa/API_SURFACE_MAP.md`; `docs/sa/CAPABILITY_GAP_MATRIX.md`; `docs/API_PERMISSION_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Source files inspected: `dp/migrations/031_tenent.sql`; `services/tenant_service.py`; `apps/api/routers/admin_tenants.py`; `utils/security.py`; `utils/permissions.py`; `apps/api/routers/session.py`; `docs/API_PERMISSION_MATRIX.md`.
Database/schema impact: New schema design for accounts, users/memberships, tenant-account link, and lifecycle fields; no implementation in this task unless split into a later build task.
Backend impact: Defines service boundaries and permission checks.
Frontend impact: Enables future account setup and user management screens, but no frontend build yet.
API impact: Future tenant/account APIs must include auth, validation, idempotency for create operations, and clear 400/401/403/409/404 errors.
Tests to add/update: Migration replay tests; tenant lifecycle tests; membership permission tests.
Validation method: Reviewed against current auth helpers, `docs/API_PERMISSION_MATRIX.md`, TASK-048 identifier decision, and TASK-004 account-to-tenant boundary. Read back the new design for account, organisation, tenant links, external references, users, memberships, seats, lifecycle states, transition rules, service boundaries, API direction, permission model, migration plan, and implementation tests.
Validation completed: Documentation-only validation on 2026-06-21. No backend tests were run because TASK-005 changed docs only.
Findings: Current auth and permission helpers resolve identity through role and `tenant_code`; there is no durable account, organisation, user membership, tenant link, seat, or external-reference mapping schema. The accepted model is additive: account/membership services resolve or validate account context before existing services continue receiving internal `tenant_code`.
Acceptance criteria: Complete. Schema/service/API design is reviewable, additive, and compatible with existing tenant-scoped data.
Dependencies: TASK-004.
Blocked by: None. TASK-004 completed the account boundary map.
Risk level: High.
Rollback notes: If later implemented, rollback must preserve existing `tenants` and `tenant_code` references.
Definition of done: Complete. Account/tenant implementation can proceed as small schema/service/API changes. Priority: P0.

## TASK-006: Map campaign and opportunity lifecycle sources

Status: Complete on 2026-06-21. TASK-006 produced `docs/sa/CAMPAIGN_OPPORTUNITY_LIFECYCLE_MAP.md` and did not change application code, migrations, schema, auth, audit, funding, fulfilment, settlement, or data-isolation behavior.
Linked enhancement: DLaaS-004: Canonical campaign lifecycle and readiness
Linked platform capability: 2. Campaign model
Goal: Map marketing campaign, campaign policy, campaign track, and distribution opportunity concepts into one canonical campaign lifecycle proposal.
Why now: Campaign readiness depends on knowing which existing entity owns lifecycle, policy, routing, and funding context.
Files involved: `docs/sa/CAMPAIGN_OPPORTUNITY_LIFECYCLE_MAP.md`; `docs/sa/API_SURFACE_MAP.md`; `docs/sa/CURRENT_STATE_MAP.md`; `docs/sa/CAPABILITY_GAP_MATRIX.md`; `docs/sa/STATE_MACHINE_MAP.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Source files inspected: `dp/migrations/002_campaigns.sql`; `dp/migrations/003_policies.sql`; `dp/migrations/067_distribution_opportunities.sql`; `dp/migrations/068_distribution_offer_routes.sql`; `services/campaign_service.py`; `services/campaign_policy_service.py`; `services/distribution/opportunity_service.py`; `services/distribution/routing_service.py`; `apps/api/routers/campaigns.py`; `apps/api/routers/distribution/admin_opportunities.py`; `apps/api/routers/distribution/admin_routing.py`.
Database/schema impact: None yet; identifies whether lifecycle/config version fields are needed later.
Backend impact: Defines service/readiness boundaries.
Frontend impact: Prevents campaign builder UI from assuming states that do not exist.
API impact: No API changes yet.
Tests to add/update: None until readiness service is implemented.
Validation method: Compared schema constraints, campaign routes, opportunity routes, routing routes, service constants, status handling, state inventory, and state-machine docs. Read back the new map for current source facts, canonical lifecycle, current-to-canonical mapping, readiness ownership, API implications, implementation guidance, and non-goals.
Validation completed: Documentation-only validation on 2026-06-21. No backend tests were run because TASK-006 changed docs only.
Findings: Campaign definition lifecycle is currently boolean/window-based on `marketing_campaigns`, policy lifecycle is active/version-based on `marketing_campaign_policies`, interaction lifecycle lives on `campaign_attributions.status`, marketplace lifecycle lives on `distribution_opportunities.opportunity_status`, and distributor-specific offer state lives on `distribution_offer_routes.route_status`. The canonical campaign lifecycle should be derived/read-model first and must keep interaction states separate from campaign configuration states.
Acceptance criteria: Complete. Current campaign/opportunity lifecycle facts and target canonical mapping are documented.
Dependencies: TASK-004.
Blocked by: None.
Risk level: Medium.
Rollback notes: Revert mapping document.
Definition of done: Complete. Readiness service can be designed without guessing campaign semantics. Priority: P0.

## TASK-007: Define campaign readiness service contract

Status: Complete on 2026-06-21. TASK-007 produced the documentation-only campaign readiness service contract in `docs/sa/CAMPAIGN_READINESS_SERVICE_CONTRACT.md`; no application code, migrations, schema, auth, audit, retry, funding, fulfilment, settlement, or data-isolation behavior changed.
Linked enhancement: DLaaS-004
Linked platform capability: 2. Campaign model; 10. Funding/budget allocation
Goal: Define a backend contract that evaluates whether a campaign is ready for activation based on policy, link/code, event, funding, and audit prerequisites.
Why now: Campaign activation and control-plane UX must be backend-driven.
Files involved: `docs/sa/CAMPAIGN_READINESS_SERVICE_CONTRACT.md`; `docs/sa/API_SURFACE_MAP.md`; `docs/sa/CAPABILITY_GAP_MATRIX.md`; `docs/sa/STATE_MACHINE_MAP.md`.
Source files inspected: `services/campaign_service.py`; `services/campaign_policy_service.py`; `services/funding/*`; `services/marketplace_funding/funding_contract_service.py`; `services/distribution/opportunity_service.py`; `services/distribution/distributor_portal_service.py`; `apps/api/routers/distribution/admin_opportunities.py`; `apps/api/routers/distribution/admin_routing.py`; `apps/api/routers/distribution/producer_supply.py`.
Database/schema impact: None initially; may identify missing config/version fields.
Backend impact: Adds readiness decision contract before implementation.
Frontend impact: Future campaign builder will consume readiness reasons.
API impact: Readiness API must include auth, tenant validation, deterministic response, idempotent read behavior, and 400/401/403/404 errors.
Tests to add/update: Readiness guard tests; activation blocker tests; tenant permission tests.
Validation method: Documentation readback against current campaign policy, distribution opportunity/routing, link, funding, and audit sources.
Validation completed: Readback confirmed the contract defines inputs, output shape, readiness states, operation-specific checks, blocker/warning/unknown categories, source ownership, API implications, audit/idempotency expectations, non-goals, and future tests. Backend tests were not run because TASK-007 changed documentation only.
Findings: Current campaign readiness must be a read-only derived decision over existing campaign, policy, opportunity, route/link, commission, funding, and audit evidence. The contract deliberately does not publish opportunities, activate campaigns, reserve funding, mutate policies, or create links.
Acceptance criteria: Complete; readiness contract lists required checks and missing-setup reason categories and can guide a later implementation without frontend-invented blocker states.
Dependencies: TASK-006; TASK-005.
Blocked by: None. TASK-005 and TASK-006 are complete.
Risk level: High.
Rollback notes: Revert contract only.
Definition of done: Complete; backend implementation task can add readiness service without deciding checks. Priority: P0.

## TASK-008: Define participant taxonomy and permission mapping

Status: Complete on 2026-06-22. TASK-008 produced the documentation-only participant taxonomy and permission map in `docs/sa/PARTICIPANT_TAXONOMY_PERMISSION_MAP.md`; no application code, migrations, schema, auth helpers, role behavior, funding, fulfilment, settlement, audit, or data-isolation behavior changed.
Linked enhancement: DLaaS-005: Participant taxonomy and role mapping
Linked platform capability: 3. Partner/referrer/distributor model; 4. Customer/referred user model; 26. Security/permissions
Goal: Map referrer, distributor, partner, sponsor/producer, customer/consumer, and operator roles to current tables and auth claims.
Why now: Link/code, attribution, portal, and API work need consistent participant language and access rules.
Files involved: `docs/sa/PARTICIPANT_TAXONOMY_PERMISSION_MAP.md`; `docs/sa/API_SURFACE_MAP.md`; `docs/sa/CAPABILITY_GAP_MATRIX.md`; `docs/sa/STATE_MACHINE_MAP.md`; `docs/API_PERMISSION_MATRIX.md`.
Source files inspected: `referrer_codes`; `referral_instances`; `distribution_distributors`; `distribution_opportunities`; `sponsor_wallets`; `partner_clients`; `utils/security.py`; `utils/permissions.py`; `apps/api/routers/session.py`; `apps/api/routers/referrals.py`; `apps/api/routers/consumer_experience.py`; `apps/api/routers/sponsor_experience.py`; `apps/api/routers/sponsor_portal_billing.py`; `apps/api/routers/distribution/distributor_portal.py`; `apps/api/routers/partner_seam.py`.
Database/schema impact: None initially; identifies whether participant read models are needed.
Backend impact: Defines role mapping and participant source lookup.
Frontend impact: Prevents role-specific UI from inventing participant fields.
API impact: Future participant APIs must include auth, tenant/role validation, pagination/filter validation, idempotency only for mutating operations, and clear 403/404 semantics.
Tests to add/update: Role mapping tests; participant isolation tests; customer privacy tests.
Validation method: Documentation readback against auth claims, permission helpers, session workspace exposure, portal route scope checks, and domain tables.
Validation completed: Readback confirmed the map covers operator, partner, producer/sponsor, distributor, referrer, customer/consumer, public, and worker boundaries; current source tables/claims; route-family helpers; role-specific scope checks; missing canonical entities; non-goals; and follow-up implementation tasks. Backend tests were not run because TASK-008 changed documentation only.
Findings: `distribution_distributors` and `partner_clients` are first-class current participant sources. Producers/sponsors are currently represented by `sponsor_code` in opportunity, funding, wallet, billing, and reporting records while auth uses `producer_code`. Referrers and referred customers are referral/progress-source concepts, with raw UCN values treated as internal-sensitive. Operators are auth/session roles, not domain rows. No canonical `participants`, `customers`, `producers`, `sponsors`, or `operators` table exists today.
Acceptance criteria: Complete; taxonomy maps current participant sources, current role/auth claims, permission boundaries, and places where no canonical entity exists.
Dependencies: TASK-004; TASK-006.
Blocked by: None. Tenant/account and campaign lifecycle decisions are documented by TASK-004 through TASK-007.
Risk level: Medium.
Rollback notes: Revert mapping.
Definition of done: Complete; participant-dependent tasks can cite a single taxonomy. Priority: P1.

## TASK-009: Define canonical link/code contract

Status: Complete on 2026-06-22. TASK-009 produced the documentation-only canonical link/code contract in `docs/sa/LINK_CODE_CONTRACT.md`; no application code, migrations, schema, auth helpers, role behavior, attribution, funding, fulfilment, settlement, audit, tenant, or data-isolation behavior changed.
Linked enhancement: DLaaS-006: Canonical link/code and attribution contract
Linked platform capability: 5. Distribution link/code generation
Goal: Define a canonical contract for issuing, resolving, inspecting, and voiding current referral codes, campaign links, and route referral links.
Why now: Attribution and public API work require one link/code abstraction.
Files involved: `docs/sa/LINK_CODE_CONTRACT.md`; `docs/sa/API_SURFACE_MAP.md`; `docs/sa/CAPABILITY_GAP_MATRIX.md`; `docs/sa/STATE_MACHINE_MAP.md`.
Source files inspected: `services/referral_code.py`; `services/composite_code_service.py`; `services/campaign_service.py`; `services/distribution/distributor_portal_service.py`; `apps/api/routers/referrals.py`; `apps/api/routers/campaigns.py`; `apps/api/routers/composite_codes.py`; `apps/api/routers/distribution/distributor_portal.py`; `dp/migrations/001_init.sql`; `dp/migrations/002_campaigns.sql`; `dp/migrations/006_qr_scans.sql`; `dp/migrations/014_campaign_referral_links.sql`; `dp/migrations/070_distribution_route_referral_links.sql`.
Database/schema impact: None initially; identify metadata gaps.
Backend impact: Defines wrapper service behavior over existing code/link sources.
Frontend impact: Future link manager and partner portal can use one contract.
API impact: Link/code APIs must include auth, validation, idempotency for issue/void commands, duplicate handling, and 400/401/403/404/409 errors.
Tests to add/update: Link issue/resolve tests; void/expired tests; duplicate code tests; tenant isolation tests.
Validation method: Documentation readback against current link/code schema, service behavior, route auth, duplicate handling, status sources, and privacy constraints.
Validation completed: Readback confirmed the contract covers referral codes, campaign codes, campaign/referral bridge links, route referral links, and current composite-code compatibility; canonical status mapping; issue/resolve/inspect/void operation expectations; source-specific idempotency and duplicate behavior; auth and tenant rules; privacy/redaction; non-goals; and future test cases. Backend tests were not run because TASK-009 changed documentation only.
Findings: `referrer_codes.referral_code` is the current shareable referral code source. `marketing_campaigns.campaign_code` resolves into `campaign_attributions.campaign_track_id`. `campaign_referral_links` bridges campaign and referral tracks but has no tenant/status/metadata/void fields. `distribution_route_referral_links` binds accepted distributor routes to referral tracks and supports `ACTIVE`/`VOIDED`, but no current void route/service was identified. `validate_composite_code` is explicitly interim and validates the same code through both campaign and referral validators.
Acceptance criteria: Complete; the contract represents source, tenant, campaign, participant, status, and attribution metadata for all current link/code sources and identifies unsupported or future-only operations.
Dependencies: TASK-008; TASK-007.
Blocked by: None. Participant and campaign mappings are documented by TASK-006 through TASK-008.
Risk level: Medium.
Rollback notes: Revert contract.
Definition of done: Complete; link/code wrapper implementation can proceed as a separate task. Priority: P1.

## TASK-010: Define outcome trace response contract

Status: Complete (2026-06-22). Output: `docs/sa/OUTCOME_TRACE_RESPONSE_CONTRACT.md`.
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
Blocked by: None for the documentation-only contract. Implementation in TASK-011 remains gated by migrated-schema/live-state verification for ambiguous joins.
Risk level: High.
Rollback notes: Revert contract.
Definition of done: Implementation can build the aggregation service without choosing response structure. Validation: static source inspection, readback checks, and documentation diff only; no code, migration, live DB, or backend test execution was needed. Priority: P0.

## TASK-011: Implement outcome trace aggregation service

Status: Complete (2026-06-22). Output: `services/outcome_trace_service.py`; `test/test_outcome_trace_service.py`.
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
Blocked by: None for the first read-only service slice. Weak commission, funding, and webhook joins remain explicitly marked as `JOIN_AMBIGUOUS` until follow-up verification/event-catalog work.
Risk level: High.
Rollback notes: Remove service/read queries; no data migration expected.
Definition of done: Outcome trace service passes golden and broken-trail tests. Validation: targeted outcome trace tests passed; nearby outcome-money reconciliation service tests passed; full backend pytest passed with coverage disabled after a parallel coverage data-file error; no schema/API changes. Priority: P0.

## TASK-012: Define event ingestion public contract

Status: Complete (2026-06-22). Output: `docs/sa/EVENT_INGESTION_PUBLIC_CONTRACT.md`.
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
Blocked by: None. TASK-010 and TASK-011 provide the outcome trace contract/service used for downstream diagnostics.
Risk level: High.
Rollback notes: Revert contract.
Definition of done: API implementation and tests can align to one event contract. Validation: readback checks passed for the contract and SA cross-references; no code, schema, auth, money, fulfilment, settlement, or audit behavior changed. Priority: P1.

## TASK-013: Define qualification decision contract

Status: Complete (2026-06-22). Output: `docs/sa/QUALIFICATION_DECISION_CONTRACT.md`.
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
Blocked by: None. TASK-007 and TASK-012 provide the campaign readiness and event ingestion contracts.
Risk level: Medium.
Rollback notes: Revert contract.
Definition of done: Reward policy work can depend on explicit qualification decisions. Validation: readback checks passed for the contract and SA cross-references; no code, schema, auth, reward, funding, fulfilment, settlement, audit, tenant, or data-isolation behavior changed. Priority: P1.

## TASK-014: Define reward and commission policy boundary

Status: Complete (2026-06-22). Output: `docs/sa/REWARD_COMMISSION_POLICY_BOUNDARY.md`.
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
Blocked by: None. TASK-013 provides the qualification decision contract.
Risk level: High.
Rollback notes: Revert design; no data changes.
Definition of done: Liability projection can consume reward/commission decisions safely. Validation: readback confirmed reward and commission decisions remain separate source families, both require qualification evidence, duplicate guards are preserved, and funding/fulfilment/settlement/reporting implications keep category-level evidence for later liability work. No code, schema, auth, reward, funding, fulfilment, settlement, audit, tenant, or data-isolation behavior changed. Priority: P1.

## TASK-015: Define liability state model and source mapping

Status: Complete (2026-06-22). Output: `docs/sa/LIABILITY_STATE_MODEL.md`.
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
Blocked by: None. TASK-011 provides outcome trace source discipline and TASK-014 provides reward/commission money-decision boundaries.
Risk level: High.
Rollback notes: Revert model.
Definition of done: Backend liability projection can be implemented without inventing money states. Validation: readback confirmed the model maps calculated, reserved, released, fulfilled, settled, reversed, failed, disputed, pending, and missing-evidence states to current reward, commission, funding, wallet, fulfilment, invoice, settlement, and audit sources; preserves reward/commission category separation; and prevents downstream evidence from inflating obligation totals. No code, schema, auth, reward, funding, fulfilment, settlement, audit, tenant, privacy, or data-isolation behavior changed. Priority: P0.

## TASK-016: Implement liability projection read service

Status: Complete (2026-06-22). Implemented a read-only outcome liability projection service backed by canonical outcome trace evidence.
Linked enhancement: DLaaS-010
Linked platform capability: 10. Funding/budget allocation; 11. Reward liability tracking
Goal: Build a backend read service that computes campaign/outcome liability from existing reward, commission, funding, fulfilment, settlement, and invoice evidence.
Why now: It unblocks funding readiness, settlement observability, control-plane money views, and reporting.
Files likely involved: `services/outcome_money_reconciliation_service.py`; `services/funding/dashboard.py`; `services/funding/reservations.py`; `services/marketplace_funding/*`; `services/fulfilment/settlement/*`
Files changed: `services/liability_projection_service.py`; `test/test_liability_projection_service.py`; `docs/sa/CAPABILITY_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`
Database/schema impact: Read-only first; add indexes/rollups only if tests expose performance issues.
Backend impact: Adds liability projection service with tenant and role scope.
Frontend impact: None yet.
API impact: No public API in this task; service must expose clear validation errors to callers.
Tests to add/update: Reservation/release/settle tests; liability rollup tests; double-count tests; reconciliation tests; tenant filter tests.
Validation method: Run service tests over current-domain trace evidence.
Acceptance criteria: Service returns liability totals and missing-evidence flags without double-counting reward, commission, wallet, invoice, or settlement evidence.
Dependencies: TASK-015.
Blocked by: None for the read-only trace-derived service slice. Direct DB/source-table expansion remains gated by DB/state verification if source tables differ from migrations.
Risk level: High.
Rollback notes: Remove read service; no data mutation expected.
Definition of done: Liability projection passes money-focused tests and is audit/source traceable. Validation: targeted liability projection and outcome trace regression tests passed with 8 tests total. The service preserves reward/commission separation, treats funding/fulfilment/settlement as phase evidence rather than new obligations, dedupes repeated reward evidence, and surfaces money-section missing evidence. No schema, route, auth, reward, funding, fulfilment, settlement, audit, tenant, privacy, or data-isolation behavior changed. Priority: P0.

## TASK-017: Map fulfilment and settlement statuses to outcome-safe statuses

Status: Complete (2026-06-22). Implemented read-only safe status mappings for fulfilment and settlement source statuses.
Linked enhancement: DLaaS-011: Fulfilment and settlement status integration
Linked platform capability: 12. Fulfilment lifecycle; 13. Settlement lifecycle
Goal: Map current fulfilment and settlement states into operator-safe and partner/customer-safe status categories.
Why now: Portal and control-plane status must not expose raw provider or settlement internals.
Files likely involved: `services/fulfilment_status.py`; `services/fulfilment/*`; `services/fulfilment/settlement/status.py`; `services/fulfilment/settlement/*`
Files changed: `services/fulfilment_safe_status.py`; `services/outcome_trace_service.py`; `test/test_fulfilment_safe_status.py`; `test/test_outcome_trace_service.py`; `docs/roadmap/ORDERED_TASK_LIST.md`
Database/schema impact: None.
Backend impact: Defines a mapping helper for operator and external safe statuses, and annotates outcome trace fulfilment/settlement rows without changing raw source statuses.
Frontend impact: Future UI consumes safe statuses instead of raw states.
API impact: Future APIs must include auth, validation, read idempotency, and error handling for status lookup.
Tests to add/update: Safe status mapping tests; internal detail leakage tests.
Validation method: Compare status enums, admin routes, settlement services, and failure handling. Validation run: targeted safe-status and outcome trace tests passed with 24 tests total; Black check passed; Ruff check passed with only the existing pyproject deprecation warning.
Acceptance criteria: Every current fulfilment/settlement status maps to operator and external visibility category.
Dependencies: TASK-015.
Blocked by: None for the read-only mapping helper slice.
Risk level: Medium.
Rollback notes: Revert mapping.
Definition of done: Outcome trace includes safe fulfilment/settlement status alongside raw source status. External-safe mappings omit raw provider/settlement status detail; operator-safe mappings preserve source status and detail code. No schema, migration, API route, frontend, money movement, or TASK-018 audit/correlation work was added. Priority: P1.

## TASK-018: Add audit/correlation references to outcome and money traces

Status: Complete (2026-06-22). Implemented read-only support trace references for outcome trace and liability projection responses.
Linked enhancement: DLaaS-012: Audit taxonomy and observable support trace
Linked platform capability: 14. Audit trail; 27. Observability
Goal: Extend outcome/liability trace contracts to include available audit and correlation evidence.
Why now: Operators need proof and support traces before repair workflows or public APIs.
Files likely involved: `services/admin_audit_service.py`; `services/fulfilment_audit_service.py`; `services/outcome_money_reconciliation_service.py`; `utils/metrics.py`
Files changed: `services/outcome_trace_service.py`; `services/liability_projection_service.py`; `test/test_outcome_trace_service.py`; `test/test_liability_projection_service.py`; `docs/roadmap/ORDERED_TASK_LIST.md`
Database/schema impact: Read existing audit tables first; schema only if critical references are missing.
Backend impact: Adds derived `support_trace` evidence from existing outcome trace sections, including audit references, correlation/idempotency references, and missing audit evidence. Liability projection carries the same support trace through without new queries.
Frontend impact: Future audit viewer/support console depends on this.
API impact: Any later API exposing audit references must enforce role scope and safe error handling.
Tests to add/update: Audit reference tests; role-scoped audit access tests; trace ID propagation tests.
Validation method: Verify audit references against existing audit tables and seeded traces. Validation run: targeted outcome trace and liability projection tests passed with 8 tests total; Black check passed; Ruff check passed with only the existing pyproject deprecation warning.
Acceptance criteria: Outcome trace identifies available audit records and missing audit evidence without leaking restricted payloads.
Dependencies: TASK-011; TASK-016; TASK-002.
Blocked by: None for the read-only support-trace slice. Full canonical audit taxonomy remains future work.
Risk level: High.
Rollback notes: Remove audit enrichment from trace.
Definition of done: Outcome/money trace contains audit/correlation evidence where current repo supports it. The implementation derives references from existing safe section fields only, excludes raw provider errors from support trace output, does not add schema, does not write audit records, and does not start TASK-019 route/API-family work. Priority: P0.

## TASK-019: Define DLaaS public/internal API families and permission matrix updates

Status: Complete (2026-06-22). Output: `docs/API_PERMISSION_MATRIX.md`; `docs/sa/API_SURFACE_MAP.md`.
Finding: TASK-019 is a documentation/contract task, not an endpoint implementation task. The current outcome trace, liability projection, and safe fulfilment/settlement status services provide enough source truth to define API-family guardrails without code, schema, or migration changes.
Validation: Read current route families, permission helpers, outcome trace/support trace behavior, liability projection behavior, safe status mappings, and related tests. Readback validation confirmed the API matrix covers campaigns, participants, links/codes, events, outcomes, rewards, funding, fulfilment, settlement, analytics, audit, credentials, and webhooks. No backend/frontend tests were run because only docs changed.
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

Status: Complete (2026-06-22). Output: `docs/sa/WEBHOOK_EVENT_CATALOG.md`; `docs/sa/API_SURFACE_MAP.md`.
Finding: TASK-020 is a documentation/contract task. Current partner seam tables and services already support tenant/client-scoped subscriptions, delivery rows, event type matching, signed delivery, retry, alert notification evidence, and dead-letter export; the missing piece was a named event catalog tied to current source truth.
Validation: Read roadmap, API permission matrix, API surface map, current-state/capability/state-machine/audit docs, target state, agent docs, partner seam migrations, service, router, worker, and partner seam docs. Readback validation confirmed the catalog covers campaign, outcome, reward, funding, fulfilment, settlement, and integration event families and maps them to current delivery mechanics. No backend/frontend tests were run because only docs changed.
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

Status: Complete (2026-06-22). Output: `docs/sa/OPERATOR_CONTROL_PLANE_BFF_CONTRACT.md`; `docs/sa/API_SURFACE_MAP.md`.
Finding: TASK-021 is a documentation/contract task. Existing admin experience routing already has a partial-section aggregate pattern, and current finance, funding, fulfilment, settlement, partner seam, audit, failure, DLQ, outcome trace, liability projection, and safe-status sources are sufficient to define the BFF contract without schema, migrations, API route implementation, or frontend work.
Validation: Read roadmap, webhook catalog, API permission matrix, API surface/current-state/capability/state-machine/audit docs, target state, agent docs, and current admin route/source-truth patterns. Readback validation confirmed the contract covers campaign readiness, outcome trace, funding/liability, fulfilment, settlement, integration health, audit, and failures; includes admin auth, tenant filters, read idempotency, partial-section behavior, permission-denied behavior, safe errors, redactions, and backend source ownership. No backend/frontend tests were run because only docs changed.
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
Blocked by: None. TASK-018 and TASK-019 provide the trace/audit and API guardrail dependencies needed for the contract.
Risk level: Medium.
Rollback notes: Revert BFF contract docs.
Definition of done: Backend BFF implementation can proceed before frontend screens. Priority: P1.

## TASK-022: Implement internal outcome trace API

Status: Complete (2026-06-22). Implemented a read-only internal/admin outcome trace API at `GET /admin/outcomes/{referral_track_id}/trace`.
Finding: TASK-022 was small enough for one implementation PR. The existing `services/outcome_trace_service.py` already provided the trace contract, missing-evidence handling, support trace references, and safe redactions, so the API layer only needed operator/admin auth, explicit tenant filtering, request validation, safe 400/403/404 handling, and route registration. No schema, migration, frontend, money movement, reward/funding/fulfilment/settlement mutation, audit write, webhook emission, or public external exposure was added.
Validation: Targeted API and service tests passed with 15 tests total using `.venv_codex`: `python -m pytest test/api/test_admin_outcomes_api.py test/test_outcome_trace_service.py --no-cov`. Black check passed for the changed route/test files. Ruff check passed for the changed route/test files with only the existing pyproject deprecation warning.
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
Blocked by: None. The outcome trace service and operator BFF contract are in place.
Risk level: High.
Rollback notes: Remove route; service can remain internal.
Definition of done: Internal outcome trace API passes contract and permission tests. Priority: P1.

## TASK-023: Define partner/customer safe status contract

Status: Complete (2026-06-22). Output: `docs/sa/PARTNER_CUSTOMER_SAFE_STATUS_CONTRACT.md`; `docs/sa/API_SURFACE_MAP.md`; `docs/sa/STATE_MACHINE_MAP.md`.
Finding: TASK-023 is a documentation/contract task. Current source truth includes outcome trace, liability projection, existing role-scoped portal routes, reward summaries, partner seam/webhook delivery state, and external-safe fulfilment/settlement mappings, but a broader implementation would be premature before the role-specific safe status contract is accepted.
Validation: Read roadmap, operator BFF contract, outcome trace contract/service/API/tests, liability model/service/tests, API permission matrix, API surface/current-state/capability/state-machine docs, target state, and agent docs. Readback validation confirmed the contract covers partners, distributors, sponsors/producers, referrers, and customers; defines safe statuses, action-required categories, source-family mappings, current fulfilment/settlement/reward/commission/webhook mappings, missing-evidence behavior, API guardrails, and redaction rules. No backend/frontend tests were run because only docs changed.
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
Blocked by: None. TASK-017 provides fulfilment/settlement safe mapping and TASK-019 provides API permission guardrails.
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

Status: Complete on 2026-06-22.
Output: `docs/sa/TENANT_SAFE_ANALYTICS_REPORTING_CONTRACT.md`.
Finding: TASK-024 is a documentation/contract task. Existing outcome trace, liability projection, safe status, webhook, operator control-plane, and partner/customer status contracts are sufficient to define tenant-safe analytics dimensions and freshness rules without schema, migration, API, frontend, or service changes.
Implementation notes: The contract defines reporting classes, approved dimension families, operational metrics, ledger-backed money metrics, tenant filter rules, freshness statuses, export constraints, ledger reconciliation statuses, privacy/redaction boundaries, and future validation expectations. It explicitly separates operational metrics from ledger-backed totals and preserves reward/commission no-double-counting rules.
Validation: Readback confirmed coverage for tenant-safe dimensions, tenant filters, freshness indicators, exports, ledger reconciliation, operational-vs-ledger separation, source ownership, redaction boundaries, and future reporting tests. No backend or frontend tests were run because this task changed documentation only.

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

Status: Complete on 2026-06-22.
Output: `docs/sa/SAAS_USAGE_BILLING_SEPARATION_MODEL.md`.
Finding: TASK-025 is a documentation/contract task. Current runtime metrics, rate-limit counters, and partner seam clients are useful hooks but are not billing-grade usage metering. Sponsor utilisation billing exists, but it remains separate from platform SaaS billing and must not be reused as subscription billing.
Implementation notes: The model defines SaaS packaging entities, candidate billable usage events, immutable usage event shape, rollup and quota rules, plan/subscription boundaries, billing hook families, API/auth direction, reporting relationship, privacy constraints, and sponsor-vs-SaaS separation.
Validation: Readback confirmed coverage for billable usage events, rollups, quotas, plans, subscriptions, billing hooks, idempotency, account/tenant/API credential attribution, sponsor-vs-SaaS separation, operational metrics vs billing-grade usage, and future tests. No backend or frontend tests were run because this task changed documentation only.

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

Status: Complete on 2026-06-22.
Output: `docs/sa/WHITE_LABEL_EMBED_SECURITY_DEPENDENCY_PLAN.md`.
Finding: TASK-026 is a documentation/dependency-gating task. Current source maps confirm no first-class tenant branding, custom domain, allowed-origin, embed client, scoped token, or SDK model exists. Implementation remains blocked until tenant isolation, public API contracts, account/membership and credential lifecycle, and partner/customer safe status APIs are implemented.
Implementation notes: The plan defines future tenant branding, custom domain, allowed-origin, embed client, embed token, SDK, and embed usage primitives; dependency gates; auth and tenant validation; CORS/origin rules; rate limits; safe errors; idempotency for config writes; cross-tenant leak prevention; and future test expectations. It does not authorize implementation before the gates are satisfied.
Validation: Readback confirmed coverage for tenant branding, custom domains, allowed origins, embed clients, SDK candidates, scoped tokens, auth/tenant validation, CORS/origin controls, rate limits, safe errors, config-write idempotency, cross-tenant leak prevention, blockers, and future tests. No backend or frontend tests were run because this task changed documentation only.

## TASK-049: Add read-only admin liability projection endpoint

Linked enhancement: DLaaS-010; DLaaS-014
Linked platform capability: 10. Funding/budget allocation; 11. Reward liability tracking; 15. Admin/operator workflow; 18. Internal API
Objective: Expose the existing read-only liability projection service through an authenticated admin/operator endpoint for one outcome/referral track.
Type: API.
Dependencies: TASK-016; TASK-018; TASK-019; TASK-022.
Likely files involved: `apps/api/routers/admin_outcomes.py`; `services/liability_projection_service.py`; `test/api/test_admin_outcomes_api.py`; `test/test_liability_projection_service.py`.
Stop conditions: Stop if the endpoint requires schema changes, live DB assumptions, money movement, fulfilment/settlement/funding mutation, raw provider data exposure, raw private identifiers, or broad route refactoring.
Validation expectation: Add targeted API tests for authorized access, unauthenticated/unauthorized access, tenant filtering, not-found or missing-evidence responses, redaction, and read-only behavior. Run liability projection service tests and admin outcomes API tests.
Explicit non-goals: Do not create or move money, reserve/release/settle/reverse obligations, mutate reward/commission/funding/fulfilment/settlement records, add schema or migrations, add frontend, or unblock TASK-027/TASK-028.
Definition of done: Operators can fetch a tenant-scoped liability projection over the existing service contract without changing source records. Priority: P1.
Status: Complete (2026-06-23). Output: `GET /admin/outcomes/{referral_track_id}/liability`.
Finding: The existing read-only `get_outcome_liability_projection` service was ready to expose through the admin outcomes router. TASK-049 added the endpoint using the current tenant normalization and operator identity boundary, preserving the read-only guardrail and safe 400/403/404 behavior.
Validation: `python -m pytest test/api/test_admin_outcomes_api.py test/test_liability_projection_service.py --no-cov` passed with 24 tests. `python -m black --check apps/api/routers/admin_outcomes.py test/api/test_admin_outcomes_api.py` passed. `python -m ruff check apps/api/routers/admin_outcomes.py test/api/test_admin_outcomes_api.py` passed with only the existing top-level linter settings deprecation warning. Outcome trace service was not changed; full backend pytest was not run for this focused API slice.

## TASK-050: Add operator control-plane BFF aggregate shell

Linked enhancement: DLaaS-014
Linked platform capability: 15. Admin/operator workflow; 18. Internal API
Objective: Add a minimal read-only operator BFF aggregate shell that returns the accepted envelope, section statuses, unavailable/not-implemented sections, guardrail text, tenant scope, and any already implemented outcome/liability sections where safely available.
Type: API.
Dependencies: TASK-021; TASK-022; TASK-049.
Likely files involved: `apps/api/routers/admin_experience.py` or a focused admin BFF router; `apps/api/main.py`; `services/outcome_trace_service.py`; `services/liability_projection_service.py`; `test/api/test_admin_experience_api.py` or new admin BFF tests.
Stop conditions: Stop if the task expands into frontend work, command/repair workflows, broad data joins, schema changes, money movement, or implementation of every BFF section at once.
Validation expectation: Add tests for admin auth, tenant filter enforcement, read-only aggregate response, partial section behavior, not-implemented section handling, permission-denied section handling where practical, and redaction guardrails.
Explicit non-goals: Do not implement frontend screens, repair/replay commands, funding/fulfilment/settlement mutations, full campaign readiness logic, full analytics, or new schema.
Definition of done: The control-plane has a stable backend aggregate shell that frontend work can consume without inventing state. Priority: P1.

## TASK-051: Add campaign readiness service implementation

Linked enhancement: DLaaS-004
Linked platform capability: 2. Campaign model; 10. Funding/budget allocation; 15. Admin/operator workflow
Objective: Implement the first read-only `campaign_readiness_service` slice from `docs/sa/CAMPAIGN_READINESS_SERVICE_CONTRACT.md` for campaign definition checks and safe missing-evidence/blocker output.
Type: Service.
Dependencies: TASK-007; TASK-019.
Likely files involved: `services/campaign_readiness_service.py`; `services/campaign_service.py`; `services/campaign_policy_service.py`; `test/test_campaign_readiness_service.py`.
Stop conditions: Stop if implementation requires schema changes, publishing/activating campaigns, creating campaign tracks, routing distributors, generating links, reserving funding, writing audit records, or relying on unverified live DB-only fields.
Validation expectation: Add service tests for campaign not found, tenant mismatch, inactive campaign, not-started/expired windows, exhausted cap, no active policy handling, unknown source handling, evidence redaction, and read-only behavior.
Explicit non-goals: Do not add API routes, frontend, lifecycle commands, route generation, funding mutation, audit writes, migrations, or live DB verification.
Definition of done: Campaign readiness can be derived in-process for core campaign checks with explicit blockers, warnings, unknowns, and source evidence. Priority: P1.

## TASK-052: Add campaign readiness admin endpoint

Linked enhancement: DLaaS-004; DLaaS-014
Linked platform capability: 2. Campaign model; 15. Admin/operator workflow; 18. Internal API
Objective: Expose the campaign readiness service through a read-only admin endpoint with tenant scope, operation validation, auth enforcement, safe errors, and no mutation.
Type: API.
Dependencies: TASK-051.
Likely files involved: `apps/api/routers/campaigns.py` or a focused admin campaign readiness router; `apps/api/main.py`; `services/campaign_readiness_service.py`; `test/api/test_campaign_readiness_api.py`.
Stop conditions: Stop if the endpoint needs lifecycle mutation, publish/activate commands, route generation, funding reservation, schema changes, or public/partner exposure.
Validation expectation: Add targeted API tests for authorized admin access, invalid operation, tenant mismatch/cross-tenant denial, 404 for inaccessible campaign, readiness response shape, and read-only behavior.
Explicit non-goals: Do not implement campaign activation, opportunity publication, routing, link generation, funding readiness mutations, frontend, or public API packaging.
Definition of done: Operators can request campaign readiness through an authenticated read-only admin API. Priority: P1.

## TASK-053: Add canonical link/code service facade

Linked enhancement: DLaaS-006
Linked platform capability: 5. Distribution link/code generation; 6. Attribution tracking
Objective: Implement a read-only/inspection-first canonical link/code facade over existing referral, campaign, composite, campaign-referral-link, and route-referral-link source evidence.
Type: Service.
Dependencies: TASK-009; TASK-019.
Likely files involved: `services/link_code_service.py`; `services/referral_code.py`; `services/composite_code_service.py`; `services/campaign_service.py`; `services/distribution/distributor_portal_service.py`; `test/test_link_code_service.py`.
Stop conditions: Stop if the facade requires a canonical persisted link table, code format changes, source mutation, void commands, track creation, accepted-terms flow changes, or schema migrations.
Validation expectation: Add service tests for supported source type mapping, inspect-by-source evidence, derived status mapping, invalid source types, unknown/missing source evidence, tenant scope, and redaction of raw UCN/token/secret fields.
Explicit non-goals: Do not add issue/resolve/void routes, do not create or validate new referral/campaign tracks, do not modify current referral/campaign/distribution behavior, and do not add schema.
Definition of done: Link/code evidence can be represented through one canonical facade while preserving current source ownership. Priority: P1.

## TASK-054: Add link/code inspect endpoint

Linked enhancement: DLaaS-006
Linked platform capability: 5. Distribution link/code generation; 17. Public API; 18. Internal API
Objective: Expose the canonical link/code facade through a read-only admin inspect endpoint for tenant-scoped operator diagnostics.
Type: API.
Dependencies: TASK-053.
Likely files involved: `apps/api/routers/admin_links.py` or another focused admin router; `apps/api/main.py`; `services/link_code_service.py`; `test/api/test_admin_links_api.py`.
Stop conditions: Stop if the endpoint becomes a public resolve API, mutates link/code state, creates tracks, voids links, changes accepted-terms behavior, or requires schema changes.
Validation expectation: Add tests for admin auth, tenant filter enforcement, source type validation, not-found handling, conflict/missing evidence shape, redaction, and read-only behavior.
Explicit non-goals: Do not implement issue, resolve, void, public validation, frontend, schema, or code format changes.
Definition of done: Operators can inspect existing link/code evidence through a safe canonical API without changing attribution behavior. Priority: P1.

## TASK-055: Add tenant-safe analytics read service

Linked enhancement: DLaaS-016
Linked platform capability: 22. Analytics/reporting
Objective: Implement a minimal tenant-safe analytics service that validates approved dimensions/report types and returns classified operational/read-model metrics from existing safe sources where already available.
Type: Service.
Dependencies: TASK-016; TASK-017; TASK-018; TASK-024.
Likely files involved: `services/tenant_safe_analytics_service.py`; `services/distribution/reporting_service.py`; `services/finance_metrics_service.py`; `services/liability_projection_service.py`; `services/fulfilment_safe_status.py`; `test/test_tenant_safe_analytics_service.py`.
Stop conditions: Stop if the task requires new materialized views, exports, billing-grade usage metering, ledger writebacks, schema changes, live DB assumptions, or raw private/provider/audit payload exposure.
Validation expectation: Add service tests for report type validation, approved/rejected dimensions, tenant filter handling, metric class labelling, freshness block output, unavailable source warnings, operational-vs-ledger separation, and redaction.
Explicit non-goals: Do not add API routes, exports, frontend charts, schema, rollup jobs, materialized views, money movement, billing usage events, or settlement/funding mutation.
Definition of done: A first backend analytics read model exists for safe operator use without claiming ledger authority beyond existing source evidence. Priority: P2.

## TASK-056: Add webhook event constants and validation helper

Linked enhancement: DLaaS-013
Linked platform capability: 19. Webhooks
Objective: Add a focused helper that centralizes accepted webhook event names from `docs/sa/WEBHOOK_EVENT_CATALOG.md` and validates event type strings without changing subscription or delivery behavior.
Type: Service.
Dependencies: TASK-020; TASK-019.
Likely files involved: `services/webhook_event_catalog.py` or `services/partner_webhook_events.py`; `services/partner_seam_service.py` only if a non-behavioral import is needed; `test/test_webhook_event_catalog.py`.
Stop conditions: Stop if validation would reject existing stored subscriptions/deliveries without migration, change queueing behavior, require schema changes, or alter webhook retry/signing behavior.
Validation expectation: Add helper tests for every catalog event type, invalid event names, family classification where included, case sensitivity, and no secret/provider/internal status leakage.
Explicit non-goals: Do not enforce validation on production subscription writes unless explicitly scoped later, do not emit events, do not change delivery rows, retry, signing, webhook APIs, schema, or migrations.
Definition of done: Future webhook tasks can import one tested catalog helper instead of duplicating event strings. Priority: P1.

## TASK-057: Add webhook payload envelope builder

Linked enhancement: DLaaS-013
Linked platform capability: 19. Webhooks
Objective: Add a pure payload builder for the accepted webhook envelope that accepts safe event, tenant, subject, correlation, data, and redaction inputs and returns a redacted payload without queueing delivery.
Type: Service.
Dependencies: TASK-020; TASK-056.
Likely files involved: `services/webhook_payload_builder.py` or `services/partner_webhook_events.py`; `test/test_webhook_payload_builder.py`.
Stop conditions: Stop if the task starts emitting events, queueing deliveries, changing partner seam APIs, reading raw provider payloads, exposing secrets, or requiring schema changes.
Validation expectation: Add tests for required envelope fields, schema version, valid event names, external tenant reference handling, redaction propagation, rejection of unsafe fields, and deterministic/safe correlation handling.
Explicit non-goals: Do not queue webhooks, create delivery rows, change subscription validation, mutate source state, add API routes, add schema, or change signing/retry behavior.
Definition of done: A tested payload envelope builder exists for later event producer tasks without side effects. Priority: P1.

## TASK-058: Add partner/customer safe status projection helper

Linked enhancement: DLaaS-015
Linked platform capability: 16. Partner/customer portal; 21. Notifications
Objective: Implement a focused helper that projects outcome, liability, fulfilment, settlement, reward, commission, and webhook source evidence into role-safe status/action-required categories from `docs/sa/PARTNER_CUSTOMER_SAFE_STATUS_CONTRACT.md`.
Type: Service.
Dependencies: TASK-017; TASK-023; TASK-049.
Likely files involved: `services/partner_customer_safe_status_service.py`; `services/fulfilment_safe_status.py`; `services/liability_projection_service.py`; `services/outcome_trace_service.py`; `test/test_partner_customer_safe_status_service.py`.
Stop conditions: Stop if the helper needs new schema, public API exposure, frontend work, raw provider/settlement/audit internals, private identifiers, or mutation of reward/funding/fulfilment/settlement/webhook records.
Validation expectation: Add service tests for role-specific redaction, safe status mapping, action-required categories, missing-evidence handling, unknown source statuses, no internal detail leakage, and tenant/participant-safe input assumptions.
Explicit non-goals: Do not add portal APIs, notification delivery, frontend, schema, money movement, repair/retry commands, or source status changes.
Definition of done: Partner/customer surfaces can reuse one tested safe-status projection helper before any role-specific API is added. Priority: P2.

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
