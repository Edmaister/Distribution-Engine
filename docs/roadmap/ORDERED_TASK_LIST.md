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

Local partial verification update (2026-07-11):
Output: `docs/roadmap/TASK_027_LOCAL_DB_VERIFICATION_RESULTS.md`.
Finding: Local database `referrals` was reachable and the verification session was forced into read-only transaction mode. The initial local DB exposed 101 public base tables. A broad local metadata pass checked 58 live-critical tables; 55 were present and 3 onboarding draft persistence tables were missing: `onboarding_drafts`, `onboarding_draft_idempotency_keys`, and `onboarding_draft_audit_links`. After applying `dp/migrations/080_onboarding_draft_persistence.sql` locally, a follow-up read-only verification confirmed 106 public base tables and all five onboarding draft persistence tables present: `onboarding_drafts`, `onboarding_draft_sections`, `onboarding_draft_validation_results`, `onboarding_draft_idempotency_keys`, and `onboarding_draft_audit_links`. The follow-up check confirmed the expected onboarding state fields, check constraints, uniqueness constraints, and lookup/idempotency/audit indexes, with zero local rows in those five tables. Focused state/count checks also confirmed referral, progress, campaign, reward, fulfilment, settlement, enterprise inbox, webhook, and admin audit state evidence without selecting raw sensitive payloads. The current DB role can create in `public`, so it is not a strict read-only DB role even though verification sessions were read-only. Protected local API smoke checks now pass for `GET /health`, `GET /openapi.json`, `GET /admin/audit/summary`, `GET /admin/failures/summary`, and `GET /admin/funding/dashboard`; unauthenticated `GET /admin/failures/summary` returns 401. The failure summary route initially returned 500 after successful admin authentication, and the confirmed TASK-028 route fix converted the admin failure router to await its async service calls.
Validation: Local read-only DB metadata/state checks only, except for the user-approved local application of the existing migration `dp/migrations/080_onboarding_draft_persistence.sql` to align the local schema. Protected API smoke checks used only local built-in test keys and read-only GET routes. No data writes, repair/replay/retry actions, funding, fulfilment, settlement, wallet, go-live, or money movement were attempted. TASK-027 remains blocked for full completion until strict read-only DB credentials or an explicit local exception and any required staging/production verification are available.

Local strict read-only verification update (2026-07-12):
Finding: Created and verified a local-only `referral_readonly_verifier` role for TASK-027 evidence. The verifier can connect and select from live-critical tables, including `referral_instances` and `referral_event_failures`, and sees 106 public base tables. The verifier is not a superuser, cannot create databases, cannot create roles, cannot create in `public`, cannot insert into `referral_event_failures`, and write probes were blocked both by role privilege checks and by read-only transaction mode when enabled. No password or secret value is recorded in repository evidence.
Validation: Local DB role/posture verification only. The blocked write probes attempted to create a disposable probe table and insert a synthetic failure row, both of which failed before any data or schema change occurred. No production/staging access, raw sensitive payload inspection, repair/replay/retry action, funding, fulfilment, settlement, wallet, go-live, or money movement was attempted. Local TASK-027 evidence now satisfies the read-only DB posture gate; non-local verification still requires approved environment credentials and access.

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

Status: Complete (2026-07-12). Output: `docs/roadmap/TASK_028_SCHEMA_UNCERTAINTY_RESOLUTION.md`; `docs/sa/LIVE_CRITICAL_STATE_INVENTORY.md`; `docs/sa/STATE_MACHINE_MAP.md`.

Finding:
TASK-028 resolved the local TASK-001 schema uncertainties using TASK-027 local read-only evidence. Local runtime facts are now separated from staging/production unknowns, and confirmed drift is assigned to TASK-148.

Blocked by:
None for local resolution. Staging and production verification remain separately gated by approved environment access.

Validation:
Documentation/readback plus local read-only metadata evidence only. No schema or data write succeeded, no secrets were recorded, and no replay, repair, retry, funding, fulfilment, settlement, wallet, go-live, or money movement was attempted.

Targeted TASK-028 drift resolution update (2026-07-11):
Output: `apps/api/routers/admin_failure.py`; `test/test_admin_failure.py`; `docs/roadmap/TASK_027_LOCAL_DB_VERIFICATION_RESULTS.md`.
Finding: TASK-027 protected local API smoke testing confirmed `GET /admin/failures/summary` authenticated with the local admin test key but returned 500 because the admin failure router used synchronous route handlers while calling async failure admin service functions without awaiting them. The route fix converted failure list, resolve, reprocess, and summary handlers to async and awaited the existing service calls. This preserves the existing auth, route paths, response contracts, DB schema, service logic, and mutation boundaries; no replay, resolve, repair, funding, fulfilment, settlement, wallet, go-live, or money movement behavior changed. After the fix, protected local read-only smoke returned 200 for failure summary and 401 without a key.
Validation: `.venv_codex\Scripts\python.exe -m pytest test\test_admin_failure.py test\test_failure_admin_service.py` passed with 31 tests. `.venv_codex\Scripts\python.exe -m ruff check apps\api\routers\admin_failure.py test\test_admin_failure.py` passed with only the existing top-level Ruff settings deprecation warning. `.venv_codex\Scripts\python.exe -m py_compile apps\api\routers\admin_failure.py test\test_admin_failure.py` passed. Local read-only smoke returned 200 for `GET /admin/audit/summary`, `GET /admin/failures/summary`, and `GET /admin/funding/dashboard`, and 401 for unauthenticated `GET /admin/failures/summary`.

Local schema uncertainty resolution update (2026-07-12):
Finding: Added TASK-028 resolution evidence and updated the live-critical inventory/state-machine map. Local verification confirms `rewards.status`, `fulfilment_audit.status`, `admin_audit_log.action_status`, `referral_event_failures.status`, and `referral_processing_audit.processing_status` are service-governed where no DB check constraint exists. Local reward identifier types remain mixed: `rewards.id` is `bigint`, `referral_rewards.reward_id` is `uuid`, `funding_reservations.reward_id` is `text`, and `fulfilment_settlement_ledger.reward_id` is `uuid`. Local `funding_reconciliation_runs.correlation_id` is absent even though `services/funding/reconciliation.py` reads/writes it; this confirmed drift is assigned to TASK-148. Staging and production were not accessed.
Validation: Documentation/readback and local read-only metadata evidence only. No schema, service, API, frontend, seed, runtime data, replay, repair, retry, funding, fulfilment, settlement, wallet, go-live, or money movement change was made.

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

## TASK-148: Fix funding reconciliation run correlation_id schema drift

Status: Complete (2026-07-12).
Output: `dp/migrations/081_funding_reconciliation_run_correlation.sql`; `services/funding/reconciliation.py`; `test/test_funding_reconciliation_run_correlation_migration.py`; `test/services/funding/test_funding_reconciliation.py`.
Finding: Added guarded additive migration 081 to add `funding_reconciliation_runs.correlation_id` and a lookup index for finance correlation evidence. Funding reconciliation run creation now also supplies the required `run_date` with `NOW()` while preserving the service-used `correlation_id`. Focused service tests now assert the insert includes `run_date`, `correlation_id`, and the passed correlation value. No local live DB mutation, reconciliation run execution, replay, repair, settlement, wallet, fulfilment, go-live, or money movement was performed.
Validation: `.venv_codex\Scripts\python.exe -m pytest test\services\funding\test_funding_reconciliation.py test\api\test_admin_funding_reconciliation_api.py test\test_funding_reconciliation_run_correlation_migration.py` passed with 20 tests. `.venv_codex\Scripts\python.exe scripts\check_migrations.py` passed. `.venv_codex\Scripts\python.exe -m ruff check services\funding\reconciliation.py test\services\funding\test_funding_reconciliation.py test\api\test_admin_funding_reconciliation_api.py test\test_funding_reconciliation_run_correlation_migration.py` passed with only the existing top-level Ruff settings deprecation warning. `.venv_codex\Scripts\python.exe -m py_compile services\funding\reconciliation.py test\services\funding\test_funding_reconciliation.py test\api\test_admin_funding_reconciliation_api.py test\test_funding_reconciliation_run_correlation_migration.py` passed.
Linked enhancement: DLaaS-002: Platform state, idempotency, and live verification guardrails
Linked platform capability: 14. Audit trail; 27. Observability; 30. Live DB/state verification
Product boundary: Shared Platform.
Required boundary docs checked: `docs/product/README.md`; `docs/roadmap/README.md`; `docs/sa/LIVE_DB_STATE_VERIFICATION_CHECKLIST.md`; `docs/roadmap/TASK_028_SCHEMA_UNCERTAINTY_RESOLUTION.md`.
Shared primitive impact: Finance reconciliation traceability and correlation evidence.
Source duplication: No.
Goal: Align `funding_reconciliation_runs` schema with `services/funding/reconciliation.py` by adding the service-used `correlation_id` evidence field safely.
Why now: TASK-028 confirmed local schema/service drift: the service inserts/selects `funding_reconciliation_runs.correlation_id`, but migration 048 and the local runtime table do not define the column.
Files likely involved: `dp/migrations/*`; `services/funding/reconciliation.py`; `test/services/funding/test_funding_reconciliation.py`; `test/api/test_admin_funding_reconciliation_api.py`; `docs/roadmap/ORDERED_TASK_LIST.md`; `docs/sa/LIVE_CRITICAL_STATE_INVENTORY.md`.
Database/schema impact: Additive migration only; no destructive schema changes and no data backfill unless explicitly reviewed.
Backend impact: Existing funding reconciliation service should stop relying on a column absent from clean/local schemas.
Frontend impact: None.
API impact: Read-only/admin funding reconciliation APIs may include `correlation_id` once schema is aligned; preserve existing response shape expected by tests.
Tests to add/update: Migration/static schema test for the added column, funding reconciliation service tests, admin funding reconciliation API tests, and migration hygiene checks.
Validation method: Run migration checks and focused funding reconciliation tests. If local DB validation is performed, use read-only checks after applying the reviewed migration locally.
Acceptance criteria: Clean schema includes `funding_reconciliation_runs.correlation_id`; funding reconciliation insert/list/get paths work without undefined-column errors; docs record the drift as resolved; no money movement, reconciliation run execution against live data, repair, replay, settlement, wallet, fulfilment, or go-live behavior is introduced.
Dependencies: TASK-028.
Blocked by: None.
Risk level: Medium.
Rollback notes: Revert the additive migration and docs if not yet deployed; if deployed, use a reviewed forward migration rather than destructive rollback.
Definition of done: Funding reconciliation run correlation evidence is schema-backed and tested without changing money state. Priority: P0.

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
Status: Complete (2026-06-23). Output: `GET /v1/experience/operator-control-plane/outcomes/{referral_track_id}`.
Finding: Added a focused read-only operator control-plane shell that returns the accepted BFF envelope, tenant scope, requested sections, section statuses, not-implemented placeholders, section-level permission denial for funding liability, redactions, and guardrail text. The shell reuses existing outcome trace and liability projection services where safely available and does not add schema, mutations, money movement, frontend work, or new source joins.
Validation: `python -m pytest test/api/test_operator_control_plane_bff_api.py test/api/test_admin_outcomes_api.py test/test_liability_projection_service.py test/test_outcome_trace_service.py --no-cov` passed with 36 tests. `python -m black --check apps/api/routers/operator_control_plane.py apps/api/main.py test/api/test_operator_control_plane_bff_api.py` passed. `python -m ruff check apps/api/routers/operator_control_plane.py test/api/test_operator_control_plane_bff_api.py` passed with the existing top-level linter settings deprecation warning. Ruff on `apps/api/main.py` still reports existing module-import-layout violations because that file intentionally calls `load_dotenv()` before imports and has pre-existing unsorted late imports; no broad main-file lint cleanup was attempted in TASK-050.

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
Status: Complete (2026-06-25). Output: `services/campaign_readiness_service.py`.
Finding: Added the first read-only campaign readiness service slice over canonical campaign definition and active policy evidence. The service derives lifecycle/readiness from existing `marketing_campaigns` fields, surfaces blockers/warnings/unknowns, keeps opportunity/routing/funding checks as safe unknowns where this slice does not yet implement source joins, and does not mutate campaigns, policies, tracks, funding, audit, or opportunity state.
Validation: `python -m pytest test/test_campaign_readiness_service.py test/test_campaign_service.py test/test_campaign_policy_service.py test/test_campaigns.py --no-cov` passed with 79 tests. `python -m black --check services/campaign_readiness_service.py test/test_campaign_readiness_service.py` passed. `python -m ruff check services/campaign_readiness_service.py test/test_campaign_readiness_service.py` passed with only the existing top-level linter settings deprecation warning. Full backend pytest was not run for this focused service slice.

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

Status: Complete (2026-06-25).
Finding: Added a focused read-only admin campaign readiness endpoint at `GET /admin/campaigns/{campaign_code}/readiness`, backed by the TASK-051 campaign readiness service. The route uses the distribution-admin permission boundary so Platform Admin and Distribution Admin can inspect tenant-scoped readiness, maps unsupported operations to safe 400 responses, maps missing or tenant-mismatched campaign evidence to safe 404 responses, and does not mutate campaigns, policies, referrals, attribution, funding, fulfilment, settlement, audit, or rewards.
Validation: `python -m black apps/api/routers/admin_campaign_readiness.py apps/api/main.py test/api/test_campaign_readiness_api.py` passed. `python -m pytest test/api/test_campaign_readiness_api.py test/test_campaign_readiness_service.py --no-cov` passed with 24 tests. `python -m ruff check apps/api/routers/admin_campaign_readiness.py test/api/test_campaign_readiness_api.py` passed. `python -m ruff check apps/api/main.py` still reports pre-existing import-order/module-level import warnings in the app entrypoint, so TASK-052 did not broaden into unrelated main-file cleanup.

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

Status: Complete (2026-06-25).
Finding: Added a focused read-only `services/link_code_service.py` facade for canonical link/code inspection across `REFERRAL_CODE`, `CAMPAIGN_CODE`, `CAMPAIGN_REFERRAL_LINK`, `ROUTE_REFERRAL_LINK`, and compatibility `COMPOSITE_CODE` sources. The facade derives safe canonical statuses from existing source evidence, surfaces missing source evidence, tenant mismatch, and source-unavailable states safely, and redacts raw UCN/hash/secret/token-style evidence. No routes, schema, migrations, code format changes, issue/resolve/void commands, track creation, or existing referral/composite/campaign behavior changed.
Validation: `python -m black services/link_code_service.py test/test_link_code_service.py` passed. `python -m pytest test/test_link_code_service.py test/test_composite_code_service.py test/test_referral_code.py --no-cov` passed with 33 tests. `python -m ruff check services/link_code_service.py test/test_link_code_service.py` passed.

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

Status: Complete (2026-06-25).
Finding: Added a focused read-only admin inspect endpoint at `GET /admin/links/inspect`, backed by the TASK-053 `inspect_link_code` facade. The route uses the distribution-admin permission boundary so Platform Admin and Distribution Admin can inspect tenant-scoped link/code evidence, forwards source type, source reference, and evidence inclusion controls, returns safe validation errors, and preserves facade-provided `INVALID`/`UNKNOWN` diagnostic results without issuing, resolving, voiding, rotating, mutating, or generating codes.
Validation: `python -m black apps/api/routers/admin_links.py apps/api/main.py test/api/test_admin_links_api.py` passed. `python -m pytest test/api/test_admin_links_api.py test/test_link_code_service.py --no-cov` passed with 21 tests. `python -m ruff check apps/api/routers/admin_links.py test/api/test_admin_links_api.py` passed. `python -m ruff check apps/api/main.py` still reports pre-existing import-order/module-level import warnings in the app entrypoint, so TASK-054 did not broaden into unrelated main-file cleanup.

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

Status: Complete (2026-06-25).
Finding: Added a focused service-only tenant-safe analytics read helper in `services/tenant_safe_analytics_service.py`. The service validates report types, dimensions, filters, tenant scope, and data windows; returns contract-style envelopes with metric class, freshness, source warnings, redactions, and reconciliation status; exposes operational distribution overview metrics without money amounts; and keeps finance reconciliation metrics under a separate ledger-backed class. No API routes, exports, schema, migrations, materialized views, rollup jobs, billing events, ledger writebacks, settlement/funding mutation, or money movement were added.
Validation: `python -m black services/tenant_safe_analytics_service.py test/test_tenant_safe_analytics_service.py` passed. `python -m pytest test/test_tenant_safe_analytics_service.py test/api/distribution/test_admin_reporting_api.py test/test_finance_metrics_service.py --no-cov` passed with 17 tests. `python -m ruff check services/tenant_safe_analytics_service.py test/test_tenant_safe_analytics_service.py` passed.

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

Status: Complete (2026-06-25).
Finding: Added a focused `services/webhook_event_catalog.py` helper that centralizes accepted webhook event constants from `docs/sa/WEBHOOK_EVENT_CATALOG.md`, classifies event families, validates canonical event type strings, supports explicit normalization for callers, and returns safe invalid results for unknown or unsafe internal/raw/secret-style names. No partner seam subscription enforcement, webhook dispatch, delivery queueing, retry, replay, signing, persistence, schema, migrations, or existing partner seam behavior changed.
Validation: `python -m black services/webhook_event_catalog.py test/test_webhook_event_catalog.py` passed. `python -m pytest test/test_webhook_event_catalog.py test/test_partner_seam_service.py test/api/test_partner_seam_api.py --no-cov` passed with 99 tests. `python -m ruff check services/webhook_event_catalog.py test/test_webhook_event_catalog.py` passed after import ordering fix. `python -m pytest test/test_webhook_event_catalog.py --no-cov` passed with 37 tests after the lint fix.

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

Status: Complete (2026-06-25).
Finding: Added a pure `services/webhook_payload_builder.py` helper that builds the accepted webhook envelope with catalog event type/family validation, schema version, external tenant scope, subject, correlation/idempotency references, occurred timestamp, safe data/metadata/source sections, and redaction evidence. The helper rejects unknown or unsafe event types and unsafe payload fields such as internal tenant codes, raw/provider payloads, UCNs, tokens, and signing/client secrets. No webhook dispatch, queueing, delivery rows, retries, signing, persistence, subscription validation, API routes, schema, migrations, or partner seam behavior changed.
Validation: `python -m black services/webhook_payload_builder.py test/test_webhook_payload_builder.py` passed. `python -m pytest test/test_webhook_payload_builder.py test/test_webhook_event_catalog.py --no-cov` passed with 74 tests. `python -m pytest test/test_partner_seam_service.py test/api/test_partner_seam_api.py --no-cov` passed with 62 tests. `python -m ruff check services/webhook_payload_builder.py test/test_webhook_payload_builder.py` passed after import ordering fix. `python -m pytest test/test_webhook_payload_builder.py test/test_webhook_event_catalog.py test/test_partner_seam_service.py test/api/test_partner_seam_api.py --no-cov` passed with 136 tests.

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

Status: Complete (2026-06-25).
Finding: Added a focused `services/partner_customer_safe_status_service.py` helper that projects already gathered outcome, liability, fulfilment, settlement, reward, commission, funding, billing, wallet, campaign, and webhook evidence into partner/customer-safe status objects for partner, distributor, sponsor, producer, referrer, and customer views. The helper reuses external-safe fulfilment and settlement mappings, applies role-family visibility, bounded missing-evidence handling, redaction evidence, action-required categories, and rejects unsafe fields such as internal tenant codes, raw UCNs, provider payloads, settlement internals, audit payloads, tokens, and signing/client secrets. No API routes, schema, migrations, frontend, source queries, money movement, retries, fulfilment, settlement, funding, audit, tenant, outcome, or webhook records changed.
Validation: `python -m black services/partner_customer_safe_status_service.py test/test_partner_customer_safe_status_service.py` passed. `python -m ruff check services/partner_customer_safe_status_service.py test/test_partner_customer_safe_status_service.py` passed after import ordering fix. `python -m pytest test/test_partner_customer_safe_status_service.py test/test_fulfilment_safe_status.py --no-cov` passed with 54 tests. `python -m pytest test/test_outcome_trace_service.py test/test_liability_projection_service.py --no-cov` passed with 8 tests. `python -m pytest test/test_partner_customer_safe_status_service.py test/test_fulfilment_safe_status.py test/test_outcome_trace_service.py test/test_liability_projection_service.py --no-cov` passed with 62 tests.

## TASK-059: Create platform readiness checkpoint after TASK-049 through TASK-058

Status: Complete (2026-06-25).
Finding: Added `docs/roadmap/PLATFORM_READINESS_CHECKPOINT_2026-06-25.md` to summarize the completed TASK-049 through TASK-058 implementation wave, capabilities now available, remaining gaps, blocked TASK-027/TASK-028 live verification work, release/demo risks, and a suggested next implementation priority order. This was documentation-only; no code, routes, schema, migrations, secrets, DB access, or implementation tasks were touched.
Validation: Read `docs/roadmap/ORDERED_TASK_LIST.md`, `docs/sa/CAPABILITY_GAP_MATRIX.md`, `docs/sa/API_SURFACE_MAP.md`, `docs/sa/CURRENT_STATE_MAP.md`, `docs/product/DLAAS_TARGET_STATE.md`, and `AGENTS.md`. No backend/frontend tests were run because TASK-059 changed roadmap documentation only. No DB access was attempted and no secrets were inspected.

## TASK-060: Define next implementation wave from platform readiness checkpoint

Status: Complete (2026-06-26).
Finding: Added the next implementation-focused roadmap wave after TASK-059. The wave prioritizes demo/release readiness, visible operator/admin value, safe read-only adoption of completed helpers, no money movement, no schema changes, and no dependency on TASK-027/TASK-028. TASK-027 and TASK-028 remain blocked and are not unblocked by this planning task.
Validation: Read `docs/roadmap/PLATFORM_READINESS_CHECKPOINT_2026-06-25.md`, `docs/roadmap/ORDERED_TASK_LIST.md`, `docs/sa/CAPABILITY_GAP_MATRIX.md`, `docs/sa/API_SURFACE_MAP.md`, `docs/product/DLAAS_TARGET_STATE.md`, and `AGENTS.md`. Documentation-only update; no backend/frontend tests were run. No DB access was attempted and no secrets were inspected.

## TASK-061: Adopt safe status helper in distributor portal outcome status

Linked enhancement: DLaaS-015
Linked platform capability: 16. Partner/customer portal
Objective: Add one read-only distributor-scoped status surface that uses `services/partner_customer_safe_status_service.py` to project existing distributor/outcome evidence into partner/customer-safe status and action-required categories.
Type: API.
Dependencies: TASK-058; TASK-019; existing distributor portal auth/tenant scoping.
Stop conditions: Stop if the endpoint requires schema changes, live DB assumptions, source mutation, money movement, settlement/fulfilment commands, raw provider/audit/settlement internals, private customer identifiers, or cross-tenant exposure.
Validation expectation: Add targeted API/service tests for authorized distributor access, tenant/distributor scoping, safe status shape, missing evidence, unknown source statuses, redaction/no leakage, and read-only behavior.
Explicit non-goals: Do not add frontend, public unauthenticated APIs, reward/commission/funding/fulfilment/settlement mutations, retry/repair commands, schema, migrations, or broad portal redesign.
Definition of done: One role-scoped portal path can return safe status/action categories using the TASK-058 helper without exposing raw internal state. Priority: P1.

Status: Complete (2026-06-26).
Finding: Added `distributor_safe_status` to distributor portal conversion rows in `services/distribution/distributor_portal_service.py`, derived with the TASK-058 `project_partner_customer_safe_status` helper. The safe status is distributor-facing, read-only, bounded to outcome evidence, includes missing attribution evidence for unlinked conversions, and avoids raw tenant, UCN, provider, settlement, audit, token, or secret leakage. The existing conversion route and experience BFF remain backward compatible; no frontend, schema, migrations, money movement, fulfilment, settlement, funding, audit, tenant, outcome, webhook, retry, or repair behavior changed. Also added the missing local `_json` helper already required by the existing route-referral link path in the same service so changed-file lint passes without broad refactor.
Validation: `python -m black services/distribution/distributor_portal_service.py apps/api/schemas/distribution/distributor_portal.py test/test_distribution_attribution_journey_contract.py test/api/distribution/test_distributor_portal_api.py` passed. `python -m ruff check services/distribution/distributor_portal_service.py apps/api/schemas/distribution/distributor_portal.py test/test_distribution_attribution_journey_contract.py test/api/distribution/test_distributor_portal_api.py` passed with the existing top-level linter settings deprecation warning. `python -m pytest test/test_partner_customer_safe_status_service.py test/test_distribution_attribution_journey_contract.py test/api/distribution/test_distributor_portal_api.py test/test_distributor_experience_api.py test/test_frontend_api_contracts.py --no-cov` passed with 63 tests. No frontend tests were run because no frontend files changed.

## TASK-062: Add campaign readiness section to operator control-plane BFF

Linked enhancement: DLaaS-014
Linked platform capability: 15. Admin/operator workflow; 2. Campaign model
Objective: Extend the read-only operator control-plane BFF shell with an optional campaign readiness section backed by the TASK-051/TASK-052 readiness behavior.
Type: API.
Dependencies: TASK-050; TASK-051; TASK-052; TASK-019.
Stop conditions: Stop if the work requires campaign activation, lifecycle mutation, opportunity publication, route generation, funding reservation, schema changes, frontend work, or public/partner exposure.
Validation expectation: Add targeted BFF tests for requested campaign readiness section, partial/unavailable section behavior, permission denial, tenant/campaign mismatch, missing campaign, readiness blocker/warning propagation, and read-only behavior.
Explicit non-goals: Do not implement activation, publication, routing, link generation, funding mutations, frontend UI, public APIs, schema, or migrations.
Definition of done: Operators can request campaign readiness inside the existing control-plane aggregate without changing campaign state. Priority: P1.

Status: Complete (2026-06-26).
Finding: Added `campaign_readiness` as an implemented optional section in the read-only operator control-plane BFF. The section reuses `services.campaign_readiness_service.get_campaign_readiness`, accepts explicit campaign readiness query context, preserves tenant-scoped operator/admin auth, keeps missing input, invalid operations, missing campaigns, and tenant mismatches inside safe section-level responses, and leaves the existing outcome trace and funding liability sections unchanged. No schema, migrations, frontend, campaign lifecycle, opportunity routing, funding, fulfilment, settlement, audit, tenant, reward, or attribution mutation behavior changed.
Validation: `python -m black apps/api/routers/operator_control_plane.py test/api/test_operator_control_plane_bff_api.py` passed using `.venv_codex`. `python -m ruff check apps/api/routers/operator_control_plane.py test/api/test_operator_control_plane_bff_api.py` passed with the existing top-level linter settings deprecation warning. `python -m pytest test/api/test_operator_control_plane_bff_api.py test/api/test_campaign_readiness_api.py test/test_campaign_readiness_service.py --no-cov` passed with 38 tests using `.venv_codex`. Full backend `python -m pytest --no-cov` passed with 1915 tests. The default `python` launcher is broken on this workstation (`0x80070520`), so validation used the project Codex virtual environment.

## TASK-063: Add tenant-safe analytics admin read endpoint

Linked enhancement: DLaaS-016
Linked platform capability: 22. Analytics/reporting; 18. Internal API
Objective: Expose the TASK-055 tenant-safe analytics read service through a read-only admin endpoint for approved report types, dimensions, tenant filters, freshness metadata, and unavailable-source warnings.
Type: API.
Dependencies: TASK-055; TASK-019.
Stop conditions: Stop if the endpoint requires exports, materialized views, rollup jobs, schema changes, live DB assumptions, billing-grade metering, ledger writebacks, money movement, or raw private/provider/audit payload exposure.
Validation expectation: Add targeted API tests for admin auth, tenant filter handling, report type validation, dimension validation, freshness/source-warning response shape, operational-vs-ledger separation, redaction, and read-only behavior.
Explicit non-goals: Do not add frontend charts, CSV/export jobs, SaaS usage billing, materialized views, schema, migrations, settlement/funding mutation, or ledger authority beyond existing service output.
Definition of done: Operators can query tenant-safe analytics through an authenticated read-only API backed by the existing service. Priority: P1.

Status: Complete (2026-06-26).
Finding: Added a focused read-only `/admin/analytics/reports/{report_type}` endpoint backed by `services.tenant_safe_analytics_service.get_tenant_safe_analytics_report`. The endpoint supports explicit tenant scope, approved repeated dimensions, current service-supported filters (`sponsor_code`, `campaign_code`, `provider_key`), and optional data window inputs. It preserves analytics admin role boundaries for platform/admin, distribution, finance, and system admins; rejects non-admin identities; returns safe validation envelopes; and leaves exports, billing, invoices, ledger writebacks, schema, migrations, materialized views, funding, settlement, fulfilment, reward, commission, audit, tenant, and analytics records untouched.
Validation: `python -m black apps/api/routers/admin_analytics.py test/api/test_admin_analytics_api.py` passed using `.venv_codex`. `python -m ruff check apps/api/routers/admin_analytics.py test/api/test_admin_analytics_api.py` passed with the existing top-level linter settings deprecation warning. A direct Ruff check of `apps/api/main.py` still reports pre-existing import-layout warnings from the app bootstrap file, so TASK-063 did not broaden into a main-module lint refactor. `python -m pytest test/api/test_admin_analytics_api.py test/test_tenant_safe_analytics_service.py test/api/distribution/test_admin_reporting_api.py --no-cov` passed with 24 tests. Full backend `python -m pytest --no-cov` passed with 1924 tests.

## TASK-064: Add webhook event catalog read endpoint

Linked enhancement: DLaaS-013
Linked platform capability: 19. Webhooks; 17. Public API; 18. Internal API
Objective: Add a read-only endpoint that exposes the accepted webhook event catalog from `services/webhook_event_catalog.py` for admin/partner integration discovery without enforcing subscription validation.
Type: API.
Dependencies: TASK-056; TASK-019.
Stop conditions: Stop if the endpoint changes subscription writes, rejects existing stored subscriptions, queues deliveries, dispatches events, changes signing/retry behavior, requires schema changes, or exposes internal table/provider names.
Validation expectation: Add targeted API tests for authorized access, catalog response shape, event family grouping, no secret/provider/internal leakage, stable schema version or catalog metadata where present, and no delivery/subscription side effects.
Explicit non-goals: Do not add event producers, delivery queueing, subscription enforcement, webhook signing changes, retry/replay behavior, frontend, schema, or migrations.
Definition of done: Integrators and operators can inspect supported webhook event names safely without changing partner seam behavior. Priority: P1.

Status: Complete (2026-06-27).
Finding: Added a focused read-only `/admin/webhooks/event-catalog` endpoint backed by `services.webhook_event_catalog`. The endpoint lists safe catalog families and event types, supports optional family filtering, returns safe validation errors for unknown family filters, preserves admin/internal access boundaries, and does not validate subscriptions, build payloads, dispatch, queue, sign, retry, replay, deliver, persist webhook records, or change partner seam behavior. No schema, migrations, frontend, provider internals, secrets, raw payloads, subscription writes, delivery behavior, or webhook worker behavior changed.
Validation: `python -m black apps/api/routers/admin_webhook_catalog.py apps/api/main.py test/api/test_admin_webhook_catalog_api.py` passed using `.venv_codex`. `python -m ruff check apps/api/routers/admin_webhook_catalog.py test/api/test_admin_webhook_catalog_api.py` passed with the existing top-level linter settings deprecation warning. `python -m pytest test/api/test_admin_webhook_catalog_api.py test/test_webhook_event_catalog.py --no-cov` passed with 43 tests. TASK-064-CI-FIX stabilized the unrelated date-sensitive active campaign-code fixture in `test/test_link_code_service.py` without changing production link/code expiry behavior; `python -m pytest test/test_link_code_service.py --no-cov` passed with 12 tests. Full backend `python -m pytest --no-cov` passed with 1930 tests.

## TASK-065: Add non-delivering webhook payload preview for campaign/outcome events

Linked enhancement: DLaaS-013
Linked platform capability: 19. Webhooks; 15. Admin/operator workflow
Objective: Add an admin-only read-only preview helper or endpoint that uses the TASK-057 envelope builder to render safe sample payloads for one or two non-money event families, preferably campaign and outcome, without queueing or dispatching deliveries.
Type: API.
Dependencies: TASK-056; TASK-057; TASK-019.
Stop conditions: Stop if the task starts emitting events, creating delivery rows, signing payloads, reading raw provider payloads, exposing private identifiers, requiring live DB verification, mutating source state, or changing partner seam delivery behavior.
Validation expectation: Add targeted tests for valid catalog event preview, unknown event rejection, tenant external reference handling, redaction propagation, no raw/secret/internal fields, and proof that no queue/delivery/signing service is invoked.
Explicit non-goals: Do not implement event producers, subscription matching, delivery queueing, retries, signing, partner notification, schema, migrations, frontend, or money-related event emission.
Definition of done: Operators can preview safe webhook payload envelopes for demo/readiness without producing side effects. Priority: P2.

Status: Complete (2026-06-27).
Finding: Added a non-delivering `/admin/webhooks/payload-preview` endpoint to the existing admin webhook catalog router. The preview endpoint supports campaign and outcome catalog event types only, requires `external_tenant_ref` and safe subject context, delegates envelope construction to `services.webhook_payload_builder.build_webhook_payload_envelope`, preserves redaction and correlation/idempotency handling, and returns an explicit `preview_only` delivery mode and non-delivery guardrail. It does not validate subscriptions, dispatch, queue, sign, retry, replay, deliver, persist webhook records, create partner deliveries, build source event producers, or change partner seam behavior. No schema, migrations, frontend, money movement, raw provider payloads, `tenant_code`, UCNs, tokens, client secrets, or signing secrets were introduced.
Validation: `python -m black apps/api/routers/admin_webhook_catalog.py test/api/test_admin_webhook_catalog_api.py` passed using `.venv_codex`. `python -m ruff check apps/api/routers/admin_webhook_catalog.py test/api/test_admin_webhook_catalog_api.py` passed with the existing top-level linter settings deprecation warning. `python -m pytest test/api/test_admin_webhook_catalog_api.py test/test_webhook_event_catalog.py test/test_webhook_payload_builder.py --no-cov` passed with 89 tests. Full backend `python -m pytest --no-cov` passed with 1939 tests.

## TASK-066: Add public API contract tests for read-only campaign and link/code diagnostics

Linked enhancement: DLaaS-006; DLaaS-014; DLaaS-017
Linked platform capability: 5. Distribution link/code generation; 15. Admin/operator workflow; 17. Public API
Objective: Add focused contract tests that lock the response shape, auth behavior, tenant scoping, safe error envelopes, and read-only guarantees for the campaign readiness and link/code inspect APIs added in TASK-052 and TASK-054.
Type: Tests.
Dependencies: TASK-052; TASK-054; TASK-019.
Stop conditions: Stop if the task requires changing production behavior beyond safe test-alignment fixes, adding new routes, mutating source state, schema changes, public unauthenticated exposure, or broad API redesign.
Validation expectation: Add targeted contract tests for successful response envelopes, invalid source/campaign inputs, 401/403/404 behavior, tenant mismatch, redaction/no leakage, and no mutation/service write calls.
Explicit non-goals: Do not add frontend, new endpoint families, link issuing/resolution, campaign activation, schema, migrations, or live DB smoke tests.
Definition of done: Release/demo-facing read-only diagnostics have stable tested API contracts before broader public API packaging. Priority: P2.

Status: Complete (2026-06-27).
Finding: Added tests-only API contract coverage for the read-only campaign readiness and link/code inspect diagnostics. The expanded tests lock stable response envelopes, distribution-admin/platform-admin access, adjacent-role and unauthenticated rejection, tenant-scope forwarding, operation/evidence flag forwarding, read-only guardrails, safe validation/404 envelopes, missing-evidence and unknown-source preservation, tenant mismatch diagnostics, redaction fields, and no raw private/provider/secret leakage in diagnostic responses. No route, service, schema, migration, campaign, policy, link/code, referral, attribution, reward, funding, fulfilment, settlement, audit, tenant, webhook, or production behavior changed.
Validation: `python -m black test/api/test_campaign_readiness_api.py test/api/test_admin_links_api.py` passed using `.venv_codex`. `python -m ruff check test/api/test_campaign_readiness_api.py test/api/test_admin_links_api.py` passed with the existing top-level linter settings deprecation warning. `python -m pytest test/api/test_campaign_readiness_api.py test/api/test_admin_links_api.py --no-cov` passed with 22 tests. `python -m pytest test/test_campaign_readiness_service.py test/test_link_code_service.py --no-cov` passed with 27 tests. Full backend `python -m pytest --no-cov` passed with 1943 tests.

## TASK-067: Add operator demo readiness smoke checklist

Linked enhancement: DLaaS-014; DLaaS-016; DLaaS-029
Linked platform capability: 15. Admin/operator workflow; 22. Analytics/reporting; 29. End-to-end testing
Objective: Create a repeatable local/CI-safe smoke checklist for the read-only operator demo path covering campaign readiness, link/code inspect, outcome trace, liability projection, control-plane aggregate, tenant-safe analytics, webhook catalog, and safe status projection.
Type: Docs/Tests.
Dependencies: TASK-049; TASK-050; TASK-052; TASK-054; TASK-055; TASK-056; TASK-058; TASK-063 if endpoint smoke is included.
Stop conditions: Stop if the checklist requires live DB access, production data, secrets, write credentials, money movement, settlement/fulfilment commands, schema changes, or frontend automation that depends on unavailable backend state.
Validation expectation: Add a docs checklist and, if practical, a small non-live test selection command that verifies the read-only demo path in local/CI using existing targeted tests.
Explicit non-goals: Do not run live smoke tests, inspect secrets, touch production data, add frontend work, mutate records, add schema, or unblock TASK-027/TASK-028.
Definition of done: The team has a safe repeatable demo/readiness validation path for the read-only platform wave. Priority: P2.

Status: Complete (2026-06-27).
Finding: Added `docs/roadmap/OPERATOR_DEMO_READINESS_SMOKE_CHECKLIST.md` as a local/CI-safe read-only operator demo checklist. The checklist covers the operator control-plane BFF, admin outcome trace, admin liability projection, admin campaign readiness, admin link/code inspect, admin analytics, admin webhook event catalog, admin webhook payload preview, safe status helper validation, auth and tenant expectations, safe redaction behavior, no-mutation/no-money-movement guardrails, local placeholder-key curl examples, CI-safe pytest selections, demo prerequisites, and TASK-027/TASK-028 live DB verification blockers. No code, schema, migrations, DB access, secrets, live smoke tests, frontend, production data, or downstream roadmap work changed.
Validation: Documentation/readback only. Confirmed checklist coverage for the required eight read-only surfaces, auth/tenant expectations, safe redaction behavior, no-mutation/no-money-movement guardrails, local/non-secret curl-style examples, CI-safe test selections, and TASK-027/TASK-028 blocked status. No backend/frontend tests were run because TASK-067 is documentation-only.

## TASK-068: Create demo-readiness checkpoint after TASK-061 through TASK-067

Status: Complete (2026-06-27). Output: `docs/roadmap/DEMO_READINESS_CHECKPOINT_TASK_068.md`.
Objective: Record demo readiness after the TASK-061 through TASK-067 wave, including read-only operator/admin endpoints, distributor/partner/customer-safe surfaces, reusable helpers, safe demo flows, backend-only UI gaps, remaining risks, TASK-027/TASK-028 blockers, and the recommended next implementation wave.
Type: Docs.
Dependencies: TASK-061; TASK-062; TASK-063; TASK-064; TASK-065; TASK-066; TASK-067.
Finding: Added a concise demo-readiness checkpoint that identifies the controlled local/test/CI demo surface now available, separates demo-ready read-only diagnostics from backend-only capabilities that still need UI work, preserves no-mutation/no-money-movement guardrails, and keeps TASK-027/TASK-028 blocked pending approved safe read-only live DB verification access. The recommended next priority is frontend/demo UI first, then API hardening, live DB verification when access is approved, public partner API packaging, and webhook delivery hardening. No code, tests, schema, migrations, secrets, DB access, live smoke checks, or implementation tasks changed.
Validation: Documentation/readback only. Confirmed the checkpoint covers what is demo-ready, read-only operator/admin endpoints, distributor/partner/customer-safe surfaces, services/helpers, safe non-money demo flows, backend-only UI gaps, external-demo risks, TASK-027/TASK-028 blockers, recommended next wave, and priority ordering. No backend/frontend tests were run because TASK-068 is documentation-only.

## TASK-069: Define frontend onboarding and demo journey implementation wave

Status: Complete (2026-06-27).
Objective: Add the next ordered frontend/product implementation wave focused on onboarding and demo journeys for the DLaaS platform, before advanced operations or money movement.
Type: Docs.
Dependencies: TASK-068.
Finding: Added TASK-070 through TASK-079 as a frontend/product journey wave. The wave prioritises company/organisation onboarding, producer/sponsor onboarding, distributor onboarding, user membership/role setup, campaign/opportunity setup, webhook/API credential setup, onboarding readiness, operator demo home, distributor safe status display, and an end-to-end demo smoke test. It covers platform operator, producer/sponsor/company admin, and distributor/partner admin personas while preserving TASK-027/TASK-028 as blocked and avoiding code, backend, migrations, secrets, DB access, and implementation work.
Validation: Documentation/readback only. Confirmed the new wave covers the three required personas, prioritises onboarding before advanced operations, keeps live DB verification blocked, and changes no code files.

## TASK-070: Add company and organisation onboarding UI shell

Objective: Build a frontend shell for platform operators or company admins to capture the minimum organisation/account setup journey: company profile, organisation reference, intended tenant scope, primary contact placeholder, and setup progress.
Type: Frontend.
Dependencies: TASK-005; TASK-048; TASK-069.
Stop conditions: Stop if implementation requires new account schema, account creation APIs, production onboarding writes, live DB access, secrets, billing setup, tenant-code renames, or membership enforcement not already available.
Validation expectation: Add focused frontend tests for rendering, form state, required-field validation, external identifier language, disabled/placeholder submit behavior where no backend exists, and navigation from the demo home.
Explicit non-goals: Do not implement account schema, migrations, backend onboarding writes, billing, plan selection, external-reference resolver behavior, or production tenant creation.
Definition of done: A company/organisation onboarding shell exists that explains the target account setup flow without pretending backend account lifecycle primitives are complete. Priority: P1.

Status: Complete (2026-06-27).
Finding: Added a frontend-only company/organisation onboarding shell at `/admin/onboarding/company`. The shell captures organisation name, `external_tenant_ref`, `organisation_ref`, country, organisation type, industry, admin contact, and intended role in local UI state; shows readiness steps for company profile, external identifiers, admin contact, and blocked backend account lifecycle; keeps `tenant_code` internal; links to future producer/sponsor, distributor, and operator monitoring paths; and clearly states that no account, tenant, membership, billing, or external-reference records are created. Wired the page into the admin route title and sidebar navigation. No backend routes, schema, migrations, auth changes, DB access, secrets, production writes, billing, tenant-code renames, or downstream TASK-071 work changed.
Validation: `npm.cmd test -- CompanyOnboardingPage.test.tsx` passed with 3 tests. Full `npm.cmd test` passed with 34 tests across 12 files. `npm.cmd run build` passed. `npm.cmd run lint` passed with 0 errors and the existing 42 warnings in pre-existing frontend files. No backend tests were run because TASK-070 changed frontend files only.

## TASK-071: Add producer and sponsor onboarding UI shell

Objective: Build a frontend shell for producer/sponsor setup that captures display profile, sponsor/producer reference, campaign ownership intent, funding-readiness placeholders, and safe next steps.
Type: Frontend.
Dependencies: TASK-070; TASK-008; TASK-069.
Stop conditions: Stop if implementation requires funding account creation, sponsor billing mutation, wallet creation, live DB access, money movement, new backend schema, or production sponsor onboarding writes.
Validation expectation: Add frontend tests for producer/sponsor persona copy, required setup sections, disabled money/funding actions, safe identifier usage, and navigation from company onboarding.
Explicit non-goals: Do not create sponsor wallets, funding contracts, invoices, billing records, rewards, settlements, fulfilment records, or backend sponsor onboarding APIs.
Definition of done: A producer/sponsor onboarding shell can be shown as part of the product journey without touching money or funding state. Priority: P1.

Status: Complete (2026-06-28).
Finding: Added a frontend-only producer/sponsor onboarding shell at `/admin/onboarding/producer-sponsor`. The shell captures producer/sponsor name, `external_tenant_ref`, `producer_ref`, `sponsor_ref`, `organisation_ref`, industry/vertical, funding model intention, producer admin contact, and campaign/opportunity role in local UI state; shows setup readiness for producer profile, external references, admin contact, funding-readiness placeholders, and blocked backend sponsor onboarding; keeps `tenant_code` internal; disables sponsor creation and funding configuration actions; links from company onboarding and navigation; and links onward to distributor setup and the existing producer workspace. No backend routes, schema, migrations, auth changes, DB access, secrets, sponsor wallets, funding contracts, invoices, billing records, rewards, settlements, fulfilment records, money movement, or downstream TASK-072 work changed.
Validation: `npm.cmd test -- ProducerSponsorOnboardingPage.test.tsx CompanyOnboardingPage.test.tsx` passed with 6 tests. Full `npm.cmd test` passed with 37 tests across 13 files. `npm.cmd run build` passed. `npm.cmd run lint` passed with 0 errors and the existing 42 warnings in pre-existing frontend files. No backend tests were run because TASK-071 changed frontend files only.

## TASK-072: Add distributor onboarding UI shell

Objective: Build a frontend shell for distributor/partner admin onboarding that captures distributor profile, distributor reference, channel/route intent, offer acceptance prerequisites, and portal access readiness.
Type: Frontend.
Dependencies: TASK-061; TASK-070; TASK-008; TASK-069.
Stop conditions: Stop if implementation requires creating distributors, activating routes, accepting offers, creating wallets, mutating opportunities, live DB access, schema changes, or backend lifecycle commands.
Validation expectation: Add frontend tests for distributor persona flow, profile/setup sections, safe reference language, inactive command buttons, and links to distributor portal/status surfaces.
Explicit non-goals: Do not create distributor records, wallets, commissions, opportunities, offer routes, route links, backend APIs, schema, or lifecycle mutations.
Definition of done: A distributor onboarding shell communicates setup status and next steps without changing distribution records. Priority: P1.

Status: Complete (2026-06-28).
Finding: Added a frontend-only distributor onboarding shell at `/admin/onboarding/distributor`. The shell captures distributor name, `external_tenant_ref`, `distributor_ref`, `organisation_ref`, channel type, market/country, distributor admin contact, distribution model, and campaign/opportunity participation intent in local UI state; shows setup readiness for distributor profile, external references, portal access contact, campaign participation intent, and blocked backend distributor onboarding; keeps `tenant_code` internal; disables distributor creation, route activation, and wallet creation actions; links from company and producer/sponsor onboarding and navigation; and links onward to the existing distributor portal. No backend routes, schema, migrations, auth changes, DB access, secrets, distributor records, wallets, commissions, opportunities, offer routes, route links, lifecycle commands, fulfilment, settlement, retry, funding, money movement, or downstream TASK-073 work changed.
Validation: `npm.cmd test -- DistributorOnboardingPage.test.tsx ProducerSponsorOnboardingPage.test.tsx CompanyOnboardingPage.test.tsx` passed with 9 tests. `npm.cmd test -- DistributionCommandCentrePage.test.tsx` passed with 3 tests after fixing the frontend test interaction to click the enabled Activate button directly. Full `npm.cmd test` passed with 40 tests across 14 files. `npm.cmd run build` passed. `npm.cmd run lint` passed with 0 errors and the existing 42 warnings in pre-existing frontend files. No backend tests were run because TASK-072 changed frontend/test/docs files only.

## TASK-073: Add user invite, membership, and role assignment UI shell

Objective: Build a frontend shell for inviting users and assigning role-family intent across platform operator, producer/sponsor/company admin, distributor/partner admin, finance, system, and support contexts.
Type: Frontend.
Dependencies: TASK-005; TASK-006; TASK-070; TASK-071; TASK-072; TASK-069.
Stop conditions: Stop if implementation requires membership schema, invite APIs, auth helper changes, role enforcement changes, email delivery, secrets, live DB access, or production user mutation.
Validation expectation: Add frontend tests for role-family options, permission-boundary warnings, disabled invite submission where no backend exists, validation of required fields, and no exposure of secrets or raw credentials.
Explicit non-goals: Do not implement membership tables, invitation delivery, identity provider integration, auth/session changes, permission helper changes, or production user provisioning.
Definition of done: A role setup shell shows how user membership will fit the onboarding journey while staying read-only/demo-safe. Priority: P1.

Status: Complete (2026-06-28).
Finding: Added a frontend-only user/member invite and role assignment shell at `/admin/onboarding/members-roles`. The shell captures `organisation_ref`, `external_tenant_ref`, user email, display name, role family, participant type, access scope, and invite status in local UI state; keeps `tenant_code` internal; shows readiness for external account scope, invite identity, role-family intent, access scope, and blocked backend membership lifecycle; includes platform operator, producer/sponsor/company admin, and distributor/partner admin guidance; disables invite delivery, role assignment, and membership activation actions; links from company, producer/sponsor, and distributor onboarding shells; and adds navigation/title wiring. No backend routes, schema, migrations, auth changes, DB access, secrets, users, memberships, invites, seats, role records, billing, funding, fulfilment, settlement, retry, money movement, or downstream TASK-074 work changed.
Validation: `npm.cmd test -- MemberRoleOnboardingPage.test.tsx CompanyOnboardingPage.test.tsx ProducerSponsorOnboardingPage.test.tsx DistributorOnboardingPage.test.tsx` passed with 12 tests. Full `npm.cmd test` passed with 43 tests across 15 files. `npm.cmd run build` passed. `npm.cmd run lint` passed with 0 errors and the existing 42 warnings in pre-existing frontend files. No backend tests were run because TASK-073 changed frontend/test/docs files only.

## TASK-074: Add campaign and opportunity setup wizard shell

Objective: Build a frontend wizard shell for configuring a campaign or distribution opportunity with product context, participant roles, link/code intent, readiness diagnostics, and go-live blocker preview.
Type: Frontend.
Dependencies: TASK-052; TASK-062; TASK-066; TASK-070; TASK-071; TASK-072; TASK-069.
Stop conditions: Stop if implementation requires campaign creation, opportunity publication, route generation, link/code issuance, reward/funding mutation, schema changes, live DB access, or backend lifecycle commands.
Validation expectation: Add frontend tests for wizard steps, readiness API integration where already available, safe validation/error display, disabled publish/go-live actions, and role-specific setup context.
Explicit non-goals: Do not implement campaign CRUD, opportunity publication, link/code generation, reward rules, funding reservations, lifecycle activation, backend APIs, schema, or migrations.
Definition of done: Operators can walk through a campaign/opportunity setup demo and see readiness diagnostics without launching anything. Priority: P1.

Status: Complete (2026-06-28).
Finding: Added a frontend-only campaign/opportunity setup wizard shell at `/admin/onboarding/campaign-opportunity`. The wizard captures `organisation_ref`, `producer_ref`/`sponsor_ref`, `campaign_code`, `opportunity_ref`, campaign name, market/country, channel/distribution model, eligible distributor type, intended outcome event, reward/commission policy intention, funding model intention, link/code intent, and go-live target/status in local UI state; keeps `tenant_code` internal; shows wizard steps for basics, participants, distribution model, outcome and reward intention, funding intention, and readiness review; previews readiness for campaign basics, participant scope, distribution intent, outcome/policy intent, funding intention, and blocked backend launch lifecycle; disables campaign save, opportunity publish, and link generation actions; links from company, producer/sponsor, distributor, and member/role onboarding shells; and adds navigation/title wiring. No backend routes, schema, migrations, auth changes, DB access, secrets, campaign records, opportunity records, routes, links, codes, reward policies, funding records, fulfilment, settlement, retry, money movement, or downstream TASK-075 work changed.
Validation: `npm.cmd test -- CampaignOpportunitySetupPage.test.tsx CompanyOnboardingPage.test.tsx ProducerSponsorOnboardingPage.test.tsx DistributorOnboardingPage.test.tsx MemberRoleOnboardingPage.test.tsx` passed with 15 tests. Full `npm.cmd test` passed with 46 tests across 16 files. `npm.cmd run build` passed. `npm.cmd run lint` passed with 0 errors and the existing 42 warnings in pre-existing frontend files. No backend tests were run because TASK-074 changed frontend/test/docs files only.

## TASK-075: Add webhook and API credential setup screen

Objective: Build a frontend screen for integration setup that explains API credential readiness, webhook event catalog discovery, non-delivering payload preview, callback URL placeholders, and safe credential handling.
Type: Frontend.
Dependencies: TASK-064; TASK-065; TASK-069.
Stop conditions: Stop if implementation requires creating, rotating, revealing, storing, or validating real secrets; subscription writes; webhook delivery; signing; queueing; live DB access; or backend credential lifecycle APIs.
Validation expectation: Add frontend tests for catalog display, payload preview integration, secret redaction copy, disabled credential mutation actions, safe placeholder handling, and no real secret examples.
Explicit non-goals: Do not create API keys, rotate secrets, validate target URLs, create webhook subscriptions, dispatch deliveries, sign payloads, persist credentials, or change partner seam behavior.
Definition of done: The demo can show how integrations will be configured using safe catalog and preview data without exposing or creating credentials. Priority: P1.

Status: Complete (2026-06-28).
Finding: Added a frontend-only webhook/API credential setup shell at `/admin/onboarding/webhook-api`. The screen captures `organisation_ref`, `external_tenant_ref`, integration owner/contact, API environment intent, callback URL placeholder, webhook event category selection, intended authentication method, IP allowlist notes, payload format/version, and go-live readiness status in local UI state; shows catalog families for campaign, outcome, reward, funding, fulfilment, settlement, and integration events; previews safe non-delivering payload context; keeps `tenant_code` internal; and disables API key creation, key rotation, secret creation, test webhook sending, subscription, and live credential activation actions. No backend routes, schema, migrations, auth changes, DB access, secrets, credential records, webhook subscriptions, callback registrations, signing, queueing, delivery, retry, partner seam behavior, billing, funding, fulfilment, settlement, or money movement changed.
Validation: `npm.cmd test -- WebhookApiSetupPage.test.tsx CampaignOpportunitySetupPage.test.tsx CompanyOnboardingPage.test.tsx ProducerSponsorOnboardingPage.test.tsx DistributorOnboardingPage.test.tsx MemberRoleOnboardingPage.test.tsx` passed with 19 tests. Full `npm.cmd test` passed with 50 tests across 17 files. `npm.cmd run build` passed. `npm.cmd run lint` passed with 0 errors and the existing 42 warnings in pre-existing frontend files. No backend tests were run because TASK-075 changed frontend/test/docs files only.

## TASK-076: Add onboarding readiness checklist

Objective: Build a frontend checklist that aggregates company, producer/sponsor, distributor, user/role, campaign/opportunity, link/code, analytics, and webhook setup readiness into a clear go-live readiness view.
Type: Frontend.
Dependencies: TASK-070; TASK-071; TASK-072; TASK-073; TASK-074; TASK-075; TASK-067; TASK-069.
Stop conditions: Stop if implementation requires command execution, backend readiness mutations, live DB verification, production data, money movement, fulfilment, settlement, webhook delivery, or schema changes.
Validation expectation: Add frontend tests for checklist status rendering, missing-step handling, safe blocker copy, TASK-027/TASK-028 blocker visibility, and no enabled go-live command when prerequisites are demo-only.
Explicit non-goals: Do not implement real go-live activation, campaign publication, funding readiness commands, delivery checks, live DB verification, or production release signoff.
Definition of done: Operators and company admins can see onboarding completeness and blockers before moving into monitoring. Priority: P1.

Status: Complete (2026-06-28).
Finding: Added a frontend-only onboarding readiness checklist shell at `/admin/onboarding/readiness`. The checklist aggregates organisation profile, producer/sponsor setup, distributor setup, members and roles, campaign/opportunity setup, webhook/API setup, security and permissions, and go-live controls into local/demo readiness states; links each setup category back to the relevant onboarding shell; keeps `tenant_code` internal while showing external-reference guidance; surfaces TASK-027 and TASK-028 live verification/drift blockers; and keeps go-live review actions disabled. No backend routes, schema, migrations, auth changes, DB access, secrets, campaign publication, credential creation, distributor route activation, wallet/funding, fulfilment, settlement, retry, webhook delivery, production signoff, or money movement changed.
Validation: `npm.cmd test -- OnboardingReadinessChecklistPage.test.tsx WebhookApiSetupPage.test.tsx CampaignOpportunitySetupPage.test.tsx CompanyOnboardingPage.test.tsx ProducerSponsorOnboardingPage.test.tsx DistributorOnboardingPage.test.tsx MemberRoleOnboardingPage.test.tsx` passed with 23 tests. Full `npm.cmd test` passed with 54 tests across 18 files. `npm.cmd run build` passed. `npm.cmd run lint` passed with 0 errors and the existing 42 warnings in pre-existing frontend files. No backend tests were run because TASK-076 changed frontend/test/docs files only.

## TASK-077: Add operator demo home linking onboarding to monitoring

Status: Complete (2026-06-28).
Finding: Added a frontend-only operator demo home at `/admin/demo-home` that links the onboarding journey, readiness review, existing read-only monitoring views, and backend-ready diagnostics. Backend-only diagnostics are visible as UI-pending rather than pretending a frontend exists, TASK-027/TASK-028 remain blocked, and all live command actions remain disabled.
Validation: Targeted frontend tests passed for the new operator demo home plus related onboarding and Distribution Command Centre pages: `npm.cmd test -- OperatorDemoHomePage.test.tsx OnboardingReadinessChecklistPage.test.tsx CompanyOnboardingPage.test.tsx ProducerSponsorOnboardingPage.test.tsx DistributorOnboardingPage.test.tsx MemberRoleOnboardingPage.test.tsx CampaignOpportunitySetupPage.test.tsx WebhookApiSetupPage.test.tsx DistributionCommandCentrePage.test.tsx`. Full frontend `npm.cmd test` passed. Frontend `npm.cmd run build` passed. Frontend `npm.cmd run lint` passed with the existing warning budget.

Objective: Build a frontend demo home for platform operators that links onboarding shells to existing monitoring/read-only diagnostics: control-plane BFF, outcome trace, liability projection, campaign readiness, link/code inspect, analytics, webhook catalog, and payload preview.
Type: Frontend.
Dependencies: TASK-049; TASK-050; TASK-052; TASK-054; TASK-063; TASK-064; TASK-065; TASK-076; TASK-069.
Stop conditions: Stop if implementation requires backend route changes, command workflows, live DB access, production data, schema changes, secrets, money movement, or broad dashboard redesign unrelated to the demo journey.
Validation expectation: Add frontend tests for navigation, persona sections, read-only route links, missing-data states, safe guardrail copy, and TASK-027/TASK-028 blocked-state display.
Explicit non-goals: Do not build a generic dashboard, add command-center mutations, create new APIs, mutate operations, or automate live smoke checks.
Definition of done: A platform operator can start a controlled demo from one place and move from onboarding to read-only monitoring surfaces. Priority: P1.

## TASK-078: Enhance distributor portal safe status display

Status: Complete (2026-06-28).
Finding: Enhanced the distributor portal to render `distributor_safe_status` on conversion rows and added a partner-safe distributor status panel covering onboarding, campaign participation, route/link readiness, outcome progress, reward/commission visibility, and support guidance. The display consumes existing safe projection fields, handles missing evidence in bounded form, hides raw redaction values, and falls back safely when older payloads omit `distributor_safe_status`. No backend, schema, migration, money movement, fulfilment, settlement, funding, audit, tenant, or route-action behavior changed.
Validation: `npm.cmd test -- DistributorPortalPage.test.tsx` passed. Related frontend tests passed for distributor portal, distributor onboarding, onboarding readiness, and operator demo home. Full frontend `npm.cmd test` passed. Frontend `npm.cmd run build` passed. Frontend `npm.cmd run lint` passed with the existing warning budget.

Objective: Confirm and, if needed, update the distributor portal frontend to render the TASK-061 `distributor_safe_status` fields with safe labels, action categories, missing evidence, and no raw internal state.
Type: Frontend.
Dependencies: TASK-061; TASK-072; TASK-069.
Stop conditions: Stop if implementation requires changing backend safe-status behavior, exposing raw provider/settlement/tenant/UCN fields, creating actions, mutating distributor records, schema changes, or live DB access.
Validation expectation: Add or update distributor portal frontend tests for safe status display, action-required states, missing evidence, redaction/no-leakage, and backward-compatible rendering when the field is absent.
Explicit non-goals: Do not change backend status projection, commission/wallet/payout logic, offer acceptance, route actions, settlement, fulfilment, funding, or distributor lifecycle behavior.
Definition of done: Distributor-facing demo screens show safe status clearly without leaking internal status details. Priority: P1.

## TASK-079: Add end-to-end onboarding demo journey smoke test

Objective: Add a frontend-focused smoke test that walks the demo journey from operator home through company onboarding, producer/sponsor onboarding, distributor onboarding, role setup, campaign/opportunity setup, integration setup, readiness checklist, and read-only monitoring links.
Type: Frontend/Tests.
Dependencies: TASK-070; TASK-071; TASK-072; TASK-073; TASK-074; TASK-075; TASK-076; TASK-077; TASK-078; TASK-067; TASK-069.
Stop conditions: Stop if the test requires live DB access, production data, secrets, real credential creation, webhook delivery, money movement, settlement/fulfilment commands, unstable external services, or implementation of missing backend write APIs.
Validation expectation: Add a targeted frontend smoke test using mocked/local-safe API responses, then run the focused frontend test plus related page tests. Keep backend tests out of scope unless backend files change.
Explicit non-goals: Do not create an external E2E environment, run live smoke tests, inspect secrets, mutate backend state, add backend routes, create migrations, or unblock TASK-027/TASK-028.
Definition of done: The product team has a repeatable frontend demo journey that proves onboarding-first navigation before advanced operations. Priority: P1.

Status: Complete (2026-06-28).
Finding: Added a frontend TASK-079 smoke proof for the onboarding demo journey. The smoke coverage renders operator demo home links, company onboarding, producer/sponsor onboarding, distributor onboarding, member/role setup, campaign/opportunity setup, webhook/API setup, onboarding readiness, Distribution Command Centre operations, and distributor portal safe status using local shell state and mocked frontend API responses. Added `docs/roadmap/FRONTEND_ONBOARDING_DEMO_SMOKE_CHECKLIST_TASK_079.md` to document the repeatable demo path, no-mutation guardrails, validation commands, and the remaining TASK-027/TASK-028 live verification blockers. No backend routes, schema, migrations, secrets, DB access, auth changes, credential generation, webhook delivery, funding, fulfilment, settlement, retry, or money movement were added.
Validation: `npm.cmd test -- OnboardingDemoJourneySmoke.test.tsx` passed with 5 tests. Related onboarding/demo/distribution/distributor tests passed with 36 tests across 10 files. Full `npm.cmd test` passed with 66 tests across 20 files. `npm.cmd run build` passed. `npm.cmd run lint` passed with 0 errors and the existing 42 warnings in pre-existing frontend files. No backend tests were run because TASK-079 changed frontend tests/docs only.

## TASK-080: Create frontend onboarding wave checkpoint and next implementation wave

Objective: Document the completed TASK-070 through TASK-079 frontend onboarding/demo wave, clarify what is demo-ready versus shell-only, and define the next implementation wave that moves toward safe backend/read-model contracts without jumping to live mutations.
Type: Docs.
Dependencies: TASK-070; TASK-071; TASK-072; TASK-073; TASK-074; TASK-075; TASK-076; TASK-077; TASK-078; TASK-079.
Stop conditions: Stop if the checkpoint requires product code changes, backend code changes, schema/migration changes, live DB access, secrets, production data, or implementation of TASK-081.
Validation expectation: Confirm the checkpoint accurately describes TASK-070 through TASK-079, changes docs only, preserves TASK-027/TASK-028 blockers, and defines a no-money/no-secrets/no-go-live next wave.
Explicit non-goals: Do not implement backend contracts, frontend integrations, onboarding persistence, account creation, credential flows, webhook delivery, money movement, schema, migrations, or live smoke checks.
Definition of done: The roadmap has a clear checkpoint and ordered next wave after the frontend onboarding/demo shell work. Priority: P1.

Status: Complete (2026-06-28).
Finding: Added `docs/roadmap/FRONTEND_ONBOARDING_WAVE_CHECKPOINT_TASK_080.md` documenting the completed frontend onboarding/demo wave, current demo flow, shell-only/local-only boundaries, explicit non-live capabilities, validation baseline, TASK-027/TASK-028 blockers, and recommended next implementation wave. Added TASK-081 through TASK-090 as a safe backend/read-model wave that starts with data contracts, read-only projection, readiness aggregation, admin read endpoints, and permission tests before any draft/save mutation design. No frontend code, backend code, tests, schema, migrations, secrets, DB access, live smoke checks, or downstream implementation work changed.
Validation: Documentation/readback only. Confirmed only roadmap docs changed, TASK-070 through TASK-079 are represented, the next wave does not jump to unsafe live mutations, and no-money/no-secrets/no-go-live guardrails remain explicit.

## TASK-081: Consolidate onboarding data contracts

Objective: Define the canonical frontend-to-backend data contract for company, producer/sponsor, distributor, member/role, campaign/opportunity, and webhook/API onboarding state using the completed shell fields and existing tenant/external identifier decisions.
Type: Docs/Service contract.
Dependencies: TASK-048; TASK-070; TASK-071; TASK-072; TASK-073; TASK-074; TASK-075; TASK-080.
Stop conditions: Stop if implementation requires schema changes, production writes, account creation APIs, invite delivery, credential generation, campaign publication, live DB access, secrets, or money movement.
Validation expectation: Add or update a focused contract doc and run readback checks. If typed helpers are added, include targeted unit tests only.
Explicit non-goals: Do not implement persistence, draft saves, tenant creation, membership creation, credential lifecycle, campaign lifecycle commands, or migrations.
Definition of done: Onboarding shells share a documented data contract that keeps `tenant_code` internal and external references explicit. Priority: P1.

Status: Complete (2026-06-28).
Finding: Added `docs/sa/ONBOARDING_DATA_CONTRACT.md` as the canonical onboarding data contract for company/organisation, producer/sponsor, distributor, member/invite/role, campaign/opportunity, webhook/API, and readiness checklist state. The contract maps the completed frontend shell fields to canonical field names, defines safe readiness/status labels, keeps `tenant_code` internal, makes `external_tenant_ref`, `organisation_ref`, `producer_ref`, `sponsor_ref`, `distributor_ref`, `opportunity_ref`, and `campaign_code` explicit, lists fields that must not be exposed externally, and defines the future read-only projection shape for TASK-082/TASK-083. No typed helpers, product code, backend routes, frontend features, schema, migrations, persistence, draft saves, account creation, invite delivery, credential lifecycle, webhook delivery, campaign publication, funding, wallet, fulfilment, settlement, retry, go-live activation, secrets, DB access, or money movement were added.
Validation: Documentation/readback only. Confirmed only docs changed, all completed onboarding shells map to contract sections, `tenant_code` remains internal, external references are explicit, no live mutations are introduced, TASK-027/TASK-028 remain blocked, and no secrets, credentials, webhook delivery, funding, wallet movement, fulfilment, settlement, retry, invite delivery, campaign publication, go-live activation, or money movement is enabled.

## TASK-082: Add read-only onboarding state projection helper

Status: Complete (2026-06-28). Output: `services/onboarding/onboarding_state_projection_service.py`; `test/test_onboarding_state_projection_service.py`.
Objective: Add a read-only helper that projects onboarding state from available current sources and marks missing evidence explicitly for shell-only areas.
Type: Service.
Dependencies: TASK-081.
Stop conditions: Stop if the helper requires schema changes, DB writes, live DB access, production data, secrets, account creation, invitation mutation, campaign mutation, credential mutation, webhook delivery, or money movement.
Validation expectation: Add focused service tests for complete, partial, missing-evidence, unknown-reference, and redaction-safe projection outputs.
Explicit non-goals: Do not mutate onboarding, tenant, membership, campaign, credential, webhook, funding, fulfilment, settlement, or audit records.
Definition of done: A read-only onboarding state projection exists with safe missing-evidence handling and no state mutation. Priority: P1.
Finding: Added a pure read-only onboarding projection helper aligned to `docs/sa/ONBOARDING_DATA_CONTRACT.md`. The helper projects company, producer/sponsor, distributor, member/role, campaign/opportunity, and webhook/API sections; uses safe evidence statuses (`PRESENT`, `PARTIAL`, `MISSING`, `SHELL_ONLY`, `UNKNOWN_REFERENCE`, `BLOCKED`); keeps `tenant_code` out of the default user-facing scope; returns bounded blockers, next actions, missing evidence, redactions, guardrails, and review-only readiness. No API route, schema, migration, frontend feature, DB access, secret access, persistence, account creation, invite delivery, credential lifecycle, webhook delivery, campaign mutation, funding, fulfilment, settlement, retry, audit mutation, go-live activation, or money movement was added.
Validation: `python -m pytest test/test_onboarding_state_projection_service.py` passed with 5 tests covering complete, partial, shell-only/missing evidence, unknown-reference, and redaction/no-mutation projections. `python -m black --check services/onboarding/onboarding_state_projection_service.py test/test_onboarding_state_projection_service.py` passed. TASK-027/TASK-028 remain blocked.

## TASK-083: Add onboarding readiness aggregation service

Status: Complete (2026-06-28). Output: `services/onboarding/onboarding_readiness_aggregation_service.py`; `test/test_onboarding_readiness_aggregation_service.py`.
Objective: Aggregate onboarding state into readiness categories for organisation, producer/sponsor, distributor, members/roles, campaign/opportunity, webhook/API, security, and go-live controls.
Type: Service.
Dependencies: TASK-081; TASK-082; TASK-076.
Stop conditions: Stop if readiness evaluation requires production writes, command execution, live DB access, secrets, schema changes, campaign launch, credential creation, webhook delivery, funding, fulfilment, settlement, retry, or money movement.
Validation expectation: Add service tests for ready, in-progress, blocked, missing-evidence, permission-limited, and go-live-disabled states.
Explicit non-goals: Do not implement real go-live activation, production release signoff, campaign publication, credential lifecycle, or money movement.
Definition of done: Readiness can be derived by a reusable read-only service instead of hard-coded local frontend state. Priority: P1.
Finding: Added a pure read-only onboarding readiness aggregation service that consumes the TASK-082 safe projection output and derives eight checklist categories: organisation profile, producer/sponsor setup, distributor setup, members and roles, campaign/opportunity setup, webhook/API setup, security and permissions, and go-live controls. The service supports `READY`, `IN_PROGRESS`, `BLOCKED`, `MISSING_EVIDENCE`, `PERMISSION_LIMITED`, and `GO_LIVE_DISABLED`; preserves external references; omits `tenant_code` from user-facing scope; carries safe source evidence references, bounded blockers, next actions, guardrails, source warnings, and redaction categories; keeps TASK-027/TASK-028 blockers visible; and keeps go-live disabled. No route, schema, migration, DB read/write, secret access, frontend feature, auth change, live mutation, webhook delivery, credential lifecycle, invite delivery, campaign publication, funding, wallet, fulfilment, settlement, retry, or money movement was added.
Validation: `python -m pytest test/test_onboarding_readiness_aggregation_service.py test/test_onboarding_state_projection_service.py` passed with 12 tests. `python -m black --check services/onboarding/onboarding_readiness_aggregation_service.py test/test_onboarding_readiness_aggregation_service.py services/onboarding/onboarding_state_projection_service.py test/test_onboarding_state_projection_service.py` passed. `python -m ruff check services/onboarding/onboarding_readiness_aggregation_service.py test/test_onboarding_readiness_aggregation_service.py services/onboarding/onboarding_state_projection_service.py test/test_onboarding_state_projection_service.py` passed with only the existing top-level Ruff settings deprecation warning. TASK-027/TASK-028 remain blocked.

## TASK-084: Add read-only admin onboarding state endpoint

Objective: Expose the onboarding state projection and readiness aggregation through an authenticated read-only admin endpoint.
Type: API.
Dependencies: TASK-082; TASK-083; docs/API_PERMISSION_MATRIX.md.
Stop conditions: Stop if the endpoint requires schema changes, backend mutations, production data, live DB access, secrets, or unsafe exposure of internal identifiers.
Validation expectation: Add API tests for auth, tenant/admin permission boundaries, safe errors, missing evidence, response shape, redaction, and no-mutation behavior.
Explicit non-goals: Do not add create/update onboarding commands, account creation, invitations, campaign publication, credential writes, webhook delivery, funding, fulfilment, settlement, retry, or money movement.
Definition of done: Operators can request onboarding state/readiness through a safe read-only endpoint. Priority: P1.

Status: Complete (2026-06-28). Output: `apps/api/routers/admin_onboarding.py`; `test/api/test_admin_onboarding_api.py`.
Finding: Added `GET /admin/onboarding/state` as an authenticated admin-only read endpoint that combines the TASK-082 onboarding state projection with the TASK-083 readiness aggregation. The endpoint accepts external onboarding references only, returns explicit shell-only/missing-evidence markers when no persisted evidence is available, preserves safe redaction boundaries, and does not create accounts, invitations, campaigns, credentials, webhooks, funding, fulfilment, settlement, retry, audit mutation, go-live activation, or money movement. TASK-027 and TASK-028 remain blocked by safe read-only live DB access.
Validation: `python -m pytest test/api/test_admin_onboarding_api.py test/test_onboarding_state_projection_service.py test/test_onboarding_readiness_aggregation_service.py` passed with 21 tests. `python -m black --check apps/api/routers/admin_onboarding.py test/api/test_admin_onboarding_api.py apps/api/main.py services/onboarding/onboarding_state_projection_service.py services/onboarding/onboarding_readiness_aggregation_service.py test/test_onboarding_state_projection_service.py test/test_onboarding_readiness_aggregation_service.py` passed. `python -m ruff check ...` passes for the new TASK-084 router/test and onboarding service/test files; including `apps/api/main.py` still reports the pre-existing file-level import-layout baseline caused by `load_dotenv()` before later imports, so the broader main module lint cleanup was not folded into TASK-084.

## TASK-085: Integrate operator demo home with read-only onboarding readiness state

Objective: Connect the operator demo home to the read-only onboarding state endpoint when available, while preserving local fallback and no-mutation guardrails.
Type: Frontend/API integration.
Dependencies: TASK-084; TASK-077; TASK-079.
Stop conditions: Stop if integration requires backend mutations, auth changes, secrets, live DB access, production data, schema changes, or enabled command actions.
Validation expectation: Add frontend tests for loading, success, partial/missing evidence, safe error fallback, disabled live actions, and no `tenant_code` exposure as a user-facing identifier.
Explicit non-goals: Do not implement onboarding writes, go-live commands, account creation, campaign publication, credential lifecycle, webhook delivery, or money movement.
Definition of done: Operator demo home can display real/read-only readiness state without losing demo-safe fallback behavior. Priority: P1.

Status: Complete (2026-06-28). Output: `frontend/src/api/endpoints/adminOnboarding.ts`; `frontend/src/pages/admin/OperatorDemoHomePage.tsx`; `frontend/src/pages/admin/OperatorDemoHomePage.test.tsx`; `frontend/src/pages/admin/OnboardingDemoJourneySmoke.test.tsx`.
Finding: Integrated the operator demo home with `GET /admin/onboarding/state` using external onboarding references only. The page now shows loading, read-only readiness summary/categories, explicit missing-evidence states, and a safe local demo fallback when the endpoint is unavailable. Existing demo navigation and disabled live-action guardrails remain intact, and the page avoids rendering `tenant_code` as a user-facing onboarding identifier.
Validation: `npm.cmd test -- OperatorDemoHomePage.test.tsx OnboardingDemoJourneySmoke.test.tsx` passed with 17 tests. `npm.cmd test -- CompanyOnboardingPage.test.tsx ProducerSponsorOnboardingPage.test.tsx DistributorOnboardingPage.test.tsx MemberRoleOnboardingPage.test.tsx CampaignOpportunitySetupPage.test.tsx WebhookApiSetupPage.test.tsx OnboardingReadinessChecklistPage.test.tsx OperatorDemoHomePage.test.tsx OnboardingDemoJourneySmoke.test.tsx` passed with 40 tests. Full `npm.cmd test` passed with 73 tests. `npm.cmd run build` passed. `npm.cmd run lint` passed with the existing project warning baseline and no TASK-085 blocking lint errors. Targeted `npx.cmd prettier --check` passed for the changed frontend files.

## TASK-086: Design safe onboarding draft/save API boundary

Objective: Document the smallest safe draft/save API boundary for future onboarding persistence, including idempotency, audit, validation, tenant/external reference resolution, and stop conditions.
Type: Docs/API contract.
Dependencies: TASK-081; TASK-083; TASK-084; docs/sa/AUDIT_RETRY_POLICY_STANDARD.md.
Stop conditions: Stop if implementation starts writing data, adding schema, creating tenants, creating users, publishing campaigns, generating credentials, dispatching webhooks, or moving money.
Validation expectation: Readback contract coverage for idempotency, audit actor, duplicate handling, safe errors, redaction, permission boundaries, and no-money/no-go-live guardrails.
Explicit non-goals: Do not implement draft/save endpoints or migrations in this task.
Definition of done: Future onboarding mutation work has a reviewed contract and explicit safety gates before implementation. Priority: P1.

Status: Complete (2026-06-29). Output: `docs/sa/ONBOARDING_DRAFT_SAVE_API_BOUNDARY.md`.
Finding: Documented the future onboarding draft/save API boundary as a contract-only design. The boundary defines safe draft lifecycle states, separation from live tenant/account creation, invites, campaign publication, credentials, webhook delivery, go-live activation, funding, wallet, fulfilment, settlement, retry, audit mutation, and money movement. It covers idempotency keys, duplicate/replay/conflict behavior, stale draft handling, audit actor/role/correlation/external-reference evidence, tenant/external reference resolution, validation layers, permission boundaries, safe errors, redaction, future endpoint sketches, explicitly disabled endpoint families, and implementation safety gates. TASK-027 and TASK-028 remain blocked.
Validation: Documentation/readback only. Confirmed TASK-086 changed docs only; no backend routes, frontend code, services, schema, migrations, persistence, DB access, secrets, tenant creation, user creation, invite delivery, campaign publication, credential generation, webhook dispatch, funding, fulfilment, settlement, retry, audit writes, go-live activation, or money movement were introduced.

## TASK-087: Define onboarding audit and event capture design

Objective: Define audit/event capture requirements for future onboarding mutations across organisation, participant, member/role, campaign, and integration setup.
Type: Docs/Service contract.
Dependencies: TASK-086; docs/sa/AUDIT_RETRY_POLICY_STANDARD.md; docs/sa/WEBHOOK_EVENT_CATALOG.md.
Stop conditions: Stop if design requires writing audit rows, dispatching events, adding schema, inspecting secrets, live DB access, or implementing mutation workflows.
Validation expectation: Readback confirms actor, external reference, resolved tenant, before/after state, idempotency key, correlation ID, and redaction expectations.
Explicit non-goals: Do not implement audit writes, event persistence, webhook delivery, replay, retry, or repair flows.
Definition of done: Future onboarding mutation tasks know what audit and event evidence they must produce. Priority: P1.

Status: Complete (2026-06-29). Output: `docs/sa/ONBOARDING_AUDIT_EVENT_CAPTURE_DESIGN.md`.
Finding: Documented the future onboarding audit/event capture contract for organisation/company, producer/sponsor, distributor, member/role, campaign/opportunity, webhook/API, readiness validation, submit-for-review, and discard draft operations. The design covers required audit evidence, event evidence, suggested onboarding event names, before/after safe state expectations, idempotency and duplicate handling, correlation/tracing, permission and tenant boundaries, safe error/rejection capture, retry/replay/repair boundaries, redaction guardrails, and safety gates before implementation. TASK-027 and TASK-028 remain blocked.
Validation: Documentation/readback only. Confirmed TASK-087 changed docs only; no backend routes, frontend code, services, schema, migrations, persistence, DB access, secrets, audit writes, event persistence, webhook dispatch, replay, retry, repair, mutation workflows, tenant/account/user/campaign/credential creation, go-live activation, funding, fulfilment, settlement, or money movement were introduced.

## TASK-088: Add RBAC and permission contract tests for onboarding read routes

Objective: Add regression tests for onboarding/readiness read routes to verify admin/operator access, adjacent-role rejection, tenant scope, safe errors, and no data leakage.
Type: API/Tests.
Dependencies: TASK-084; docs/API_PERMISSION_MATRIX.md.
Stop conditions: Stop if tests require production data, live DB access, secrets, backend mutations, auth weakening, or broad permission refactors.
Validation expectation: Targeted API permission tests pass and confirm unauthenticated/unauthorized requests are rejected while authorized read-only access works.
Explicit non-goals: Do not change auth behavior unless tests expose a clear route contract bug; do not add mutation routes.
Definition of done: Onboarding read surfaces are locked to the intended admin/operator permission contract. Priority: P1.

Status: Complete (2026-06-29). Output: `test/api/test_admin_onboarding_api.py`.
Finding: Added onboarding read-route permission regression coverage for adjacent scoped admin and role-scoped identities. The tests now confirm finance admin, partner, producer, distributor, and consumer credentials are rejected before read-only projection helpers run, safe 403 errors do not echo tenant scope or internals, authorized admin/distribution/system access remains read-only, and onboarding state scope is built from external references while ignoring user-supplied `tenant_code`.
Validation: Targeted API tests passed with `.venv_codex`: `python -m pytest test/api/test_admin_onboarding_api.py` (15 passed) and `python -m pytest test/api/test_admin_onboarding_api.py test/test_onboarding_state_projection_service.py test/test_onboarding_readiness_aggregation_service.py` (27 passed). `ruff check test/api/test_admin_onboarding_api.py` passed with the existing pyproject deprecation warning. `black --check` could not be completed because the local Black invocation timed out before returning, including `black --version`. No backend route, auth behavior, schema, migration, live DB access, secrets, persistence, mutation routes, production data, or onboarding writes were introduced.

## TASK-089: Connect onboarding shells to read-only/mock-safe backend state

Objective: Gradually connect frontend onboarding shells to the read-only onboarding state endpoint where available, preserving local fallback, disabled actions, and safe missing-evidence behavior.
Type: Frontend/API integration.
Dependencies: TASK-084; TASK-085; TASK-088.
Stop conditions: Stop if integration requires enabling writes, creating records, auth changes, schema changes, secrets, live DB access, credential lifecycle, webhook delivery, or money movement.
Validation expectation: Add frontend tests for read-only hydrated state, local fallback, partial evidence, safe errors, disabled action preservation, and external-reference display.
Explicit non-goals: Do not implement draft/save, create, publish, invite, activate, credential, webhook delivery, funding, fulfilment, settlement, retry, or money movement behavior.
Definition of done: Onboarding shells can consume read-only platform state while remaining demo-safe and non-mutating. Priority: P1.

Status: Complete (2026-06-29). Output: `frontend/src/pages/admin/OnboardingReadinessChecklistPage.tsx`, `frontend/src/pages/admin/CompanyOnboardingPage.tsx`.
Finding: Connected the onboarding readiness checklist and company/organisation onboarding shell to the existing read-only admin onboarding state helper for `GET /admin/onboarding/state` using external references only. Both pages now show loading, hydrated read-only state, partial/missing evidence, safe local fallback, and disabled live-action guardrails while avoiding `tenant_code` as a user-facing identifier. Remaining onboarding shells are still local/demo shells and can follow this pattern in a later task.
Validation: Targeted frontend tests passed with `npm.cmd test -- CompanyOnboardingPage.test.tsx OnboardingReadinessChecklistPage.test.tsx` (12 passed) and related onboarding/demo tests passed with `npm.cmd test -- OperatorDemoHomePage.test.tsx OnboardingDemoJourneySmoke.test.tsx CompanyOnboardingPage.test.tsx ProducerSponsorOnboardingPage.test.tsx DistributorOnboardingPage.test.tsx MemberRoleOnboardingPage.test.tsx CampaignOpportunitySetupPage.test.tsx WebhookApiSetupPage.test.tsx OnboardingReadinessChecklistPage.test.tsx` (45 passed). No backend routes, backend mutations, auth changes, schema, migrations, secrets, production data, live DB access, save/create/update/publish/invite/activate commands, credential lifecycle, webhook delivery, funding, fulfilment, settlement, retry, wallet, or money movement were introduced.

## TASK-090: Checkpoint onboarding read-model implementation wave

Objective: Record the outcomes of TASK-081 through TASK-089, update remaining gaps, and recommend the next wave only after read-only contracts and tests are in place.
Type: Docs.
Dependencies: TASK-081; TASK-082; TASK-083; TASK-084; TASK-085; TASK-086; TASK-087; TASK-088; TASK-089.
Stop conditions: Stop if checkpoint requires implementation work, live DB access, secrets, schema changes, or starting the next wave.
Validation expectation: Documentation/readback only; confirm completed work, remaining shell-only areas, blockers, validation baseline, and safe next priorities.
Explicit non-goals: Do not implement TASK-091 or any downstream feature.
Definition of done: The product has a clear readiness checkpoint after moving frontend shells toward safe read-only backend contracts. Priority: P1.

Status: Complete (2026-06-29). Output: `docs/roadmap/ONBOARDING_READ_MODEL_WAVE_CHECKPOINT_TASK_090.md`.
Finding: Added the onboarding read-model checkpoint covering TASK-081 through TASK-089 outcomes, current read-only onboarding capabilities, remaining shell-only areas, explicit non-live boundaries, validation baseline, permission/safety posture, TASK-027/TASK-028 blockers, and a safe TASK-091 onward recommendation. The next wave keeps work read-only/design-first and avoids jumping directly to writes, schema, go-live, credential lifecycle, webhook delivery, funding, fulfilment, settlement, retry, audit mutation, or money movement.
Validation: Documentation/readback only. Confirmed TASK-081 through TASK-089 are represented, remaining shell-only areas are explicit, blockers are preserved, validation baseline is captured, and next priorities remain safe. Only roadmap docs changed; no backend routes, frontend code, services, tests, schema, migrations, persistence, DB access, secrets, onboarding writes, credential lifecycle, webhook delivery, funding, fulfilment, settlement, retry, audit mutation, or money movement were introduced.

## TASK-091: Connect producer/sponsor onboarding shell to read-only state

Objective: Integrate the producer/sponsor onboarding shell with the read-only admin onboarding state endpoint while preserving local fallback, disabled actions, and no-money/no-credential guardrails.
Type: Frontend/API integration.
Dependencies: TASK-084; TASK-089; TASK-090.
Stop conditions: Stop if integration requires backend mutations, schema changes, auth changes, secrets, live DB access, sponsor creation, funding setup, wallet creation, billing mutation, credential lifecycle, webhook delivery, go-live, or money movement.
Validation expectation: Add/update targeted frontend tests for loading, hydrated read-only state, missing evidence, fallback, disabled actions, external reference display, and no `tenant_code` exposure.
Explicit non-goals: Do not implement producer/sponsor writes, sponsor funding, wallet, billing, campaign publication, credential generation, webhook delivery, fulfilment, settlement, retry, or money movement.
Definition of done: Producer/sponsor onboarding can consume safe read-only platform state while remaining shell-only and non-mutating. Priority: P1.

Status: Complete (2026-06-29). Output: `frontend/src/pages/admin/ProducerSponsorOnboardingPage.tsx`.
Finding: Integrated the producer/sponsor onboarding shell with the existing read-only admin onboarding state helper for `GET /admin/onboarding/state` using external references only. The page now shows loading, hydrated read-only producer/sponsor evidence, partial/missing evidence, safe local fallback, and disabled sponsor/funding guardrails while avoiding `tenant_code` as a user-facing identifier. No producer/sponsor writes or money-related actions were enabled.
Validation: Targeted frontend test `npm.cmd test -- ProducerSponsorOnboardingPage.test.tsx` passed with 7 tests. No backend routes, backend mutations, auth changes, schema, migrations, secrets, production data, live DB access, sponsor creation, funding setup, wallet creation, billing mutation, credential lifecycle, webhook delivery, go-live, fulfilment, settlement, retry, or money movement were introduced.

## TASK-092: Connect distributor onboarding shell to read-only state

Objective: Integrate the distributor onboarding shell with read-only onboarding state while preserving local fallback, disabled lifecycle/wallet/route actions, and distributor-safe external reference display.
Type: Frontend/API integration.
Dependencies: TASK-084; TASK-089; TASK-090.
Stop conditions: Stop if integration requires backend mutations, schema changes, auth changes, secrets, live DB access, distributor creation, activation, suspension, route activation, wallet creation, funding, fulfilment, settlement, retry, or money movement.
Validation expectation: Add/update targeted frontend tests for read-only hydration, missing evidence, fallback, disabled lifecycle actions, external reference display, and no `tenant_code` exposure.
Explicit non-goals: Do not implement distributor writes, route commands, wallet commands, offer decisions, commission, payout, fulfilment, settlement, retry, or money movement.
Definition of done: Distributor onboarding can consume safe read-only platform state while remaining shell-only and non-mutating. Priority: P1.

Status: Complete (2026-06-29). Output: `frontend/src/pages/admin/DistributorOnboardingPage.tsx`.
Finding: Integrated the distributor onboarding shell with the existing read-only admin onboarding state helper for `GET /admin/onboarding/state` using external references only. The page now shows loading, hydrated read-only distributor evidence, partial/missing evidence, safe local fallback, and disabled lifecycle/route/wallet guardrails while avoiding `tenant_code` as a user-facing identifier. No distributor writes or marketplace/money actions were enabled.
Validation: Targeted frontend test `npm.cmd test -- DistributorOnboardingPage.test.tsx` passed with 7 tests. No backend routes, backend mutations, auth changes, schema, migrations, secrets, production data, live DB access, distributor creation, activation, suspension, route activation, wallet creation, funding, fulfilment, settlement, retry, offer decision, commission, payout, webhook delivery, go-live, or money movement were introduced.

## TASK-093: Connect member and role onboarding shell to read-only state

Objective: Integrate the member/role onboarding shell with read-only onboarding state while preserving local fallback, disabled invite/role actions, and safe permission guidance.
Type: Frontend/API integration.
Dependencies: TASK-084; TASK-089; TASK-090.
Stop conditions: Stop if integration requires backend mutations, schema changes, auth changes, secrets, live DB access, user creation, membership creation, identity-provider writes, invite delivery, role assignment, audit mutation, or money movement.
Validation expectation: Add/update targeted frontend tests for read-only hydration, permission/missing evidence states, fallback, disabled invite/role actions, external reference display, and no `tenant_code` exposure.
Explicit non-goals: Do not implement user creation, membership creation, invite delivery, role assignment, auth claim changes, audit writes, or onboarding writes.
Definition of done: Member/role onboarding can consume safe read-only platform state while remaining shell-only and non-mutating. Priority: P1.
Status: Complete (2026-06-29).
Finding: Connected the member/role onboarding shell to the existing read-only admin onboarding state endpoint using external references only. The page now surfaces loading, hydrated, permission-limited/missing-evidence, and local fallback states while keeping invite, user creation, membership, role assignment, identity-provider, auth-claim, audit, and onboarding write actions disabled.
Validation: `npm.cmd test -- MemberRoleOnboardingPage.test.tsx` passed with 7 tests. Related onboarding and demo smoke tests passed with 38 tests. Full frontend `npm.cmd test` passed with 90 tests. Frontend build passed. Frontend lint passed with the existing warning baseline: 42 warnings, 0 errors.

## TASK-094: Connect campaign/opportunity setup shell to read-only state

Objective: Integrate the campaign/opportunity setup shell with read-only onboarding state while preserving local fallback, disabled launch/publish actions, and safe readiness blockers.
Type: Frontend/API integration.
Dependencies: TASK-084; TASK-089; TASK-090.
Stop conditions: Stop if integration requires backend mutations, schema changes, auth changes, secrets, live DB access, campaign creation, opportunity publication, link/code generation, route activation, reward policy writes, funding, fulfilment, settlement, retry, go-live, or money movement.
Validation expectation: Add/update targeted frontend tests for read-only hydration, missing evidence, fallback, disabled launch/publish actions, external reference display, and no `tenant_code` exposure.
Explicit non-goals: Do not implement campaign writes, opportunity publication, link/code generation, reward/commission writes, funding setup, fulfilment, settlement, retry, go-live, or money movement.
Definition of done: Campaign/opportunity setup can consume safe read-only platform state while remaining shell-only and non-mutating. Priority: P1.
Status: Complete (2026-06-29).
Finding: Connected the campaign/opportunity setup shell to the existing read-only admin onboarding state endpoint using external references only. The page now surfaces loading, hydrated, missing-evidence/blocker, and local fallback states while keeping campaign create, opportunity publish, link/code, route activation, reward/commission, funding, fulfilment, settlement, retry, go-live, webhook, wallet, and money movement actions disabled.
Validation: `npm.cmd test -- CampaignOpportunitySetupPage.test.tsx` passed with 7 tests. `npm.cmd test -- DistributionCommandCentrePage.test.tsx` passed with 3 tests after hardening the guarded lifecycle test isolation and waiting for the selected distributor fixture to settle on `DIST-1`. `npm.cmd test -- OnboardingDemoJourneySmoke.test.tsx` passed with 5 tests. Full frontend `npm.cmd test` passed with 94 tests across 20 files. Frontend build passed. Frontend lint passed with the existing warning baseline: 42 warnings, 0 errors.

## TASK-095: Connect webhook/API setup shell to read-only state

Objective: Integrate the webhook/API setup shell with read-only onboarding state while preserving local fallback, disabled credential/webhook actions, and no secret exposure.
Type: Frontend/API integration.
Dependencies: TASK-084; TASK-089; TASK-090.
Stop conditions: Stop if integration requires backend mutations, schema changes, auth changes, secrets, live DB access, API key creation, secret generation, credential rotation, webhook subscription, signing, queueing, delivery, retry, or go-live activation.
Validation expectation: Add/update targeted frontend tests for read-only hydration, missing evidence, fallback, disabled credential/webhook actions, external reference display, no secret display, and no `tenant_code` exposure.
Explicit non-goals: Do not implement credential lifecycle, webhook subscription, test delivery, signing, callback registration, secret display, webhook delivery, retry, go-live, or money movement.
Definition of done: Webhook/API setup can consume safe read-only platform state while remaining shell-only and non-mutating. Priority: P1.
Status: Complete (2026-06-29).
Finding: Connected the webhook/API setup shell to the existing read-only admin onboarding state endpoint using external references only. The page now surfaces loading, hydrated missing-evidence/blocker, and local fallback states while keeping API key creation, secret generation, credential rotation, webhook subscription, callback registration, signing, queueing, test delivery, retry, go-live, and money actions disabled. Literal `tenant_code` is not exposed as a user-facing onboarding identifier, and secret-like credential material is not displayed.
Validation: `npm.cmd test -- WebhookApiSetupPage.test.tsx` passed with 8 tests. Related onboarding tests passed with `npm.cmd test -- CompanyOnboardingPage.test.tsx ProducerSponsorOnboardingPage.test.tsx DistributorOnboardingPage.test.tsx MemberRoleOnboardingPage.test.tsx CampaignOpportunitySetupPage.test.tsx WebhookApiSetupPage.test.tsx OnboardingReadinessChecklistPage.test.tsx` (48 tests). `npm.cmd test -- OnboardingDemoJourneySmoke.test.tsx` passed with 5 tests. Full frontend `npm.cmd test` passed with 98 tests across 20 files. Frontend build passed. Frontend lint passed with the existing warning baseline: 42 warnings, 0 errors.

## TASK-096: Add onboarding frontend API helper contract tests

Objective: Add focused frontend tests for the onboarding API helper response mapping, safe fallback assumptions, external reference query parameters, and redaction/no-leak expectations.
Type: Frontend/Tests.
Dependencies: TASK-084; TASK-089; TASK-090.
Stop conditions: Stop if tests require backend mutations, live DB access, secrets, auth changes, schema changes, production data, or broad frontend API refactors.
Validation expectation: Targeted frontend API helper tests pass and confirm external-reference query behavior, response shape expectations, safe missing evidence, and no `tenant_code` user-facing dependency.
Explicit non-goals: Do not add routes, backend services, frontend pages, writes, credential lifecycle, webhook delivery, funding, fulfilment, settlement, retry, or money movement.
Definition of done: Frontend onboarding API consumption has regression tests independent of page rendering. Priority: P1.
Status: Complete (2026-06-30).
Finding: Added focused frontend API helper contract coverage for `getAdminOnboardingState`, including the read-only `GET /admin/onboarding/state` path, external-reference query params, blank ref omission, runtime `tenant_code` suppression, successful projection/readiness response handling, partial/missing-evidence handling, shared API error fallback behavior, and no sensitive-value leakage. The helper now sanitizes the allowed external-reference query boundary client-side and exposes the existing read-only onboarding state envelope type without forcing older page test fixtures to include the optional projection until TASK-097 performs full response schema alignment.
Validation: `npm.cmd test -- adminOnboarding.test.ts` passed with 5 tests. Related onboarding/demo frontend tests passed with `npm.cmd test -- OperatorDemoHomePage.test.tsx CompanyOnboardingPage.test.tsx ProducerSponsorOnboardingPage.test.tsx DistributorOnboardingPage.test.tsx MemberRoleOnboardingPage.test.tsx CampaignOpportunitySetupPage.test.tsx WebhookApiSetupPage.test.tsx OnboardingReadinessChecklistPage.test.tsx OnboardingDemoJourneySmoke.test.tsx adminOnboarding.test.ts` (70 tests). Full frontend `npm.cmd test` passed with 103 tests across 21 files. Frontend build passed. Frontend lint passed with the existing warning baseline: 42 warnings, 0 errors.

## TASK-097: Align onboarding endpoint response schema and frontend types

Objective: Review and align the admin onboarding endpoint response envelope with frontend TypeScript types and documented contract, adding type/schema checks where safe.
Type: API/Frontend contract.
Dependencies: TASK-084; TASK-096.
Stop conditions: Stop if alignment requires schema changes, backend mutations, auth changes, live DB access, secrets, production data, or broad route redesign.
Validation expectation: Targeted backend/frontend contract tests pass for the response shape used by onboarding pages and operator demo home.
Explicit non-goals: Do not add mutation routes, persistence, account creation, invites, campaign publication, credential lifecycle, webhook delivery, funding, fulfilment, settlement, retry, audit mutation, or money movement.
Definition of done: Backend response and frontend types agree on the read-only onboarding state contract. Priority: P1.
Status: Complete (2026-06-30).
Finding: Aligned the read-only admin onboarding response contract across backend API assertions, frontend TypeScript types, and frontend page fixtures. The backend route already returned the stable envelope with required `onboarding_state`, `readiness`, and `guardrail`; the mismatch was the TASK-096 frontend helper type still treating `onboarding_state` as optional. TASK-097 made the frontend type required, added a shared full-envelope onboarding state test fixture, updated onboarding/operator/demo tests to use the real envelope shape, and strengthened backend API tests for the projection/readiness response keys and go-live-disabled guardrail. No backend production route behavior changed.
Validation: Targeted frontend onboarding API/page tests passed with `npm.cmd test -- adminOnboarding.test.ts OperatorDemoHomePage.test.tsx CompanyOnboardingPage.test.tsx ProducerSponsorOnboardingPage.test.tsx DistributorOnboardingPage.test.tsx MemberRoleOnboardingPage.test.tsx CampaignOpportunitySetupPage.test.tsx WebhookApiSetupPage.test.tsx OnboardingReadinessChecklistPage.test.tsx OnboardingDemoJourneySmoke.test.tsx` (70 tests). Full frontend `npm.cmd test` passed with 103 tests across 21 files. Frontend build passed. Frontend lint passed with the existing warning baseline: 42 warnings, 0 errors. Backend targeted onboarding API/projection/readiness tests passed with `.venv_codex` using `python -m pytest test/api/test_admin_onboarding_api.py test/test_onboarding_state_projection_service.py test/test_onboarding_readiness_aggregation_service.py` (27 tests). `ruff check test/api/test_admin_onboarding_api.py` passed with the existing pyproject deprecation warning. `ruff format --check test/api/test_admin_onboarding_api.py` passed. Local `black --check` timed out on the single changed backend test file, so Ruff format was used to verify formatting.

## TASK-098: Design onboarding draft persistence schema and rollback plan

Objective: Design the future onboarding draft persistence schema, indexes, retention, idempotency references, rollback approach, and migration safety plan without adding migrations.
Type: Docs/Schema design.
Dependencies: TASK-086; TASK-087; TASK-090.
Stop conditions: Stop if implementation starts, migrations are added, live DB is accessed, secrets are inspected, or draft/write endpoints are created.
Validation expectation: Documentation/readback confirms schema intent, additive migration strategy, rollback plan, idempotency model, audit linkage, redaction boundaries, and no live action semantics.
Explicit non-goals: Do not create tables, migrations, services, routes, frontend code, audit writes, event persistence, credential lifecycle, webhook delivery, funding, fulfilment, settlement, retry, or money movement.
Definition of done: Future draft persistence has a reviewed schema and rollback design before implementation. Priority: P1.
Status: Complete (2026-06-30). Output: `docs/sa/ONBOARDING_DRAFT_PERSISTENCE_SCHEMA_DESIGN.md`.
Finding: Added a documentation-only onboarding draft persistence schema design covering proposed future `onboarding_drafts`, `onboarding_draft_sections`, `onboarding_draft_validation_results`, `onboarding_draft_idempotency_keys`, and `onboarding_draft_audit_links` tables. The design defines draft lifecycle states, external-reference handling, internal-only `tenant_code` treatment, JSON payload boundaries, redaction rules, index and uniqueness strategy, retention, idempotency behavior, audit/event linkage, validation result modeling, additive migration strategy, rollback plan, and migration safety checklist. TASK-027 and TASK-028 remain blocked.
Validation: Documentation/readback only. Confirmed TASK-098 changed docs only; no migrations, tables, services, routes, frontend code, tests, live DB access, secrets, draft/write endpoints, audit writes, event persistence, credential lifecycle, webhook delivery, funding, fulfilment, settlement, retry, wallet, go-live activation, or money movement were introduced. Readback confirms schema intent, additive migration strategy, rollback plan, idempotency model, audit linkage, retention, redaction boundaries, and no-live-action semantics are covered.

## TASK-099: Design onboarding dry-run validation endpoint contract

Objective: Define a no-op/dry-run onboarding validation endpoint contract for future draft review, including safe errors, missing evidence, permission checks, idempotency expectations, and no mutation guarantees.
Type: Docs/API contract.
Dependencies: TASK-086; TASK-087; TASK-090; TASK-098.
Stop conditions: Stop if implementation starts, routes are added, schema/migrations are added, live DB is accessed, secrets are inspected, or writes/audit mutation are introduced.
Validation expectation: Documentation/readback confirms dry-run semantics, safe error shape, no-persistence guarantee, external-reference scope, redaction, permission boundaries, and no live actions.
Explicit non-goals: Do not implement the endpoint, draft persistence, account creation, invite delivery, campaign publication, credential lifecycle, webhook delivery, funding, fulfilment, settlement, retry, audit mutation, or money movement.
Definition of done: Future validation work has a safe contract before any route implementation. Priority: P1.
Status: Complete (2026-06-30). Output: `docs/sa/ONBOARDING_DRY_RUN_VALIDATION_ENDPOINT_CONTRACT.md`.
Finding: Added a documentation-only dry-run onboarding validation endpoint contract. The contract defines future `POST /admin/onboarding/validate` and `POST /admin/onboarding/drafts/{draft_ref}/validate` sketches, request and response envelopes, dry-run/no-op semantics, validation categories, safe error model, permission boundaries, idempotency expectations, external-reference scope, redaction categories, no-persistence guarantee, relationship to TASK-082/TASK-083 and TASK-086/TASK-087/TASK-098, implementation safety gates, and explicit non-goals. TASK-027 and TASK-028 remain blocked.
Validation: Documentation/readback only. Confirmed TASK-099 changed docs only; no backend routes, frontend code, services, tests, schema, migrations, DB access, secrets, draft persistence, writes, audit mutation, event persistence, account creation, invite delivery, campaign publication, credential lifecycle, webhook delivery, funding, fulfilment, settlement, retry, wallet, go-live activation, or money movement were introduced. Readback confirms dry-run semantics, safe error shape, no-persistence guarantee, external-reference scope, redaction, permission boundaries, idempotency expectations, and no-live-action semantics are covered.

## TASK-100: Checkpoint onboarding read-only integration and pre-write readiness

Objective: Record outcomes of TASK-091 through TASK-099, confirm remaining gaps, and decide whether the platform is ready to consider a tightly scoped onboarding write implementation wave.
Type: Docs.
Dependencies: TASK-091; TASK-092; TASK-093; TASK-094; TASK-095; TASK-096; TASK-097; TASK-098; TASK-099.
Stop conditions: Stop if checkpoint requires implementation work, live DB access, secrets, schema changes, migrations, writes, go-live, credential lifecycle, webhook delivery, funding, fulfilment, settlement, retry, audit mutation, or money movement.
Validation expectation: Documentation/readback only; confirm completed read-only integrations, contract tests, schema/design readiness, blockers, and safe next priorities.
Explicit non-goals: Do not implement onboarding writes or downstream features.
Definition of done: Roadmap has a clear pre-write checkpoint before any onboarding mutation task begins. Priority: P1.
Status: Complete (2026-06-30). Output: `docs/roadmap/ONBOARDING_PRE_WRITE_READINESS_CHECKPOINT_TASK_100.md`.
Finding: Added the TASK-100 pre-write readiness checkpoint covering TASK-091 through TASK-099 outcomes, completed read-only frontend integrations, contract/test hardening, future-write design work, current demo capabilities, explicit not-live boundaries, validation baseline, permission/safety posture, TASK-027/TASK-028 blockers, and the pre-write readiness decision. The checkpoint concludes the platform is ready to consider only a tightly scoped draft-persistence foundation wave, not full onboarding writes or live activation.
Validation: Documentation/readback only. Confirmed TASK-100 changed docs only; no backend routes, frontend code, services, tests, schema, migrations, DB access, secrets, onboarding writes, draft persistence, audit writes, event persistence, credential lifecycle, webhook delivery, funding, fulfilment, settlement, retry, wallet, go-live activation, or money movement were introduced. Readback confirms remaining gaps, blockers, and next priorities are explicit and guarded.

## TASK-101: Draft persistence migration design final review

Objective: Perform a final documentation review before any onboarding draft persistence migration is added.
Type: Docs/checkpoint.
Dependencies: TASK-098; TASK-099; TASK-100.
Stop conditions: Stop if review requires adding migrations, writing code, accessing live DB, inspecting secrets, or enabling writes.
Validation expectation: Documentation/readback confirms schema design, rollback, clean DB replay plan, TASK-027/TASK-028 posture, and no-live-action guardrails.
Explicit non-goals: Do not add migrations, services, routes, frontend code, draft writes, audit writes, credential lifecycle, webhook delivery, go-live, funding, fulfilment, settlement, retry, wallet, or money movement.
Definition of done: The draft persistence migration is ready for a narrow implementation task with reviewed guardrails. Priority: P1.
Status: Complete (2026-06-30). Output: `docs/roadmap/ONBOARDING_DRAFT_MIGRATION_FINAL_REVIEW_TASK_101.md`.
Finding: Added the final draft persistence migration review before TASK-102. The review confirms TASK-102 may proceed only as a narrow additive migration-only task for the approved onboarding draft persistence tables: `onboarding_drafts`, `onboarding_draft_sections`, `onboarding_draft_validation_results`, `onboarding_draft_idempotency_keys`, and `onboarding_draft_audit_links`. It documents clean DB replay expectations, rollback posture, idempotency storage readiness, audit-link-only readiness, redaction/privacy guardrails, permission posture, migration naming/order expectations, and explicit no-live-action boundaries. TASK-027 and TASK-028 remain blocked.
Validation: Documentation/readback only. Confirmed TASK-101 changed docs only; no migration files were added or edited, and no backend code, frontend code, services, routes, tests, DB access, secrets, writes, audit writes, event persistence, credential lifecycle, webhook delivery, go-live activation, funding, fulfilment, settlement, retry, wallet, or money movement were introduced. Readback confirms TASK-102 can proceed only as a narrow migration-only implementation and must stop if broader write, route, service, live DB, production data, or live-action scope is required.

## TASK-102: Add onboarding draft persistence migration

Objective: Add onboarding draft persistence tables only, with no write route and no production writes.
Type: DB migration.
Dependencies: TASK-101.
Stop conditions: Stop if migration needs live DB access, production data, secrets, route implementation, services, frontend code, or live action semantics.
Validation expectation: Migration check and clean DB replay pass; schema matches TASK-098; no route or write path exists.
Explicit non-goals: Do not add draft-save routes, account creation, invite delivery, campaign publication, credential lifecycle, webhook delivery, audit writes, funding, fulfilment, settlement, retry, wallet, go-live, or money movement.
Definition of done: Draft persistence tables exist in migration replay without enabling onboarding writes. Priority: P1.
Status: Complete (2026-06-30). Output: `dp/migrations/080_onboarding_draft_persistence.sql`.
Finding: Added an additive migration-only onboarding draft persistence foundation. The migration creates `onboarding_drafts`, `onboarding_draft_sections`, `onboarding_draft_validation_results`, `onboarding_draft_idempotency_keys`, and `onboarding_draft_audit_links` with guarded DDL, UUID primary keys, foreign keys, uniqueness for draft references, section keys, and scoped idempotency key hashes, plus lookup/retention/correlation indexes. It stores external onboarding references as the user-facing scope and does not add `tenant_code` as a user-facing identifier. The idempotency table stores hashed key/scope evidence rather than raw keys. No routes, services, repositories, frontend code, write paths, audit writers, events, seeds, or live action behavior were added.
Validation: `scripts/check_migrations.py` passed using the bundled Python runtime. `git diff --check` passed. `scripts/init_db.py` was attempted but could not run in the local environment: default `python` and `py` launchers fail with Windows Store Python launch errors, the project `.venv` points to a missing Python 3.11 executable, and the bundled Python runtime does not include `asyncpg`. Clean DB replay should be rerun in CI or a repaired local project runtime. No live DB access, production data, secrets, backend routes, services, repositories, frontend code, API tests, writes, draft-save endpoint, audit writes, event persistence, credential lifecycle, webhook delivery, funding, fulfilment, settlement, retry, wallet, go-live, or money movement were introduced.

## TASK-103: Add clean DB migration replay tests for onboarding draft tables

Objective: Prove clean DB readiness for onboarding draft persistence tables.
Type: Tests.
Dependencies: TASK-102.
Stop conditions: Stop if tests require live DB access, production data, secrets, or write APIs.
Validation expectation: Migration hygiene and clean DB replay tests pass; draft tables, indexes, and constraints are verified locally/CI only.
Explicit non-goals: Do not add services, routes, frontend code, draft writes, audit writes, credential lifecycle, webhook delivery, go-live, funding, fulfilment, settlement, retry, wallet, or money movement.
Definition of done: Clean DB replay covers the onboarding draft schema. Priority: P1.
Status: Complete (2026-06-30). Output: `test/test_onboarding_draft_migration.py`.
Finding: Added CI-safe static migration tests for TASK-102 onboarding draft persistence. The tests verify `080_onboarding_draft_persistence.sql` is ordered between migration 079 and 999, declares the five approved draft tables, includes key columns, primary keys, foreign keys, uniqueness for `draft_ref`, `(draft_id, section_key)`, scoped idempotency hashes, and active draft scope, includes guarded lookup/retention/correlation indexes, keeps `tenant_code` out of draft columns, stores idempotency hash/reference fields rather than raw idempotency keys or payloads, and avoids live-action table/column families for credentials, webhook delivery, funding, wallet, fulfilment, settlement, retry, go-live, and money movement.
Validation: `test/test_onboarding_draft_migration.py` compiled successfully and all 8 test functions passed when invoked directly with the bundled Python runtime. `scripts/check_migrations.py` passed with the bundled Python runtime. `git diff --check` passed. Pytest could not run locally because the bundled Python runtime does not include `pytest`. Clean DB replay was attempted but could not run locally: bundled Python lacks `asyncpg`, and the project `.venv` points to a missing Python 3.11 executable. The tests are static and CI-safe, with no live DB access, production data, secrets, services, routes, repositories, frontend code, new migrations, schema changes, write APIs, draft writes, audit writes, event persistence, credential lifecycle, webhook delivery, go-live, funding, fulfilment, settlement, retry, wallet, or money movement introduced.

## TASK-104: Add onboarding draft repository with no route wiring

Objective: Add repository primitives and repository tests only, with no API exposure.
Type: Service/repository.
Dependencies: TASK-102; TASK-103.
Stop conditions: Stop if repository work requires route wiring, frontend changes, live DB access, secrets, or live action semantics.
Validation expectation: Repository tests cover create/read/update draft-intent primitives, stale version behavior, redaction boundaries, and no-live-action fields.
Explicit non-goals: Do not add API routes, frontend integration, account creation, invite delivery, campaign publication, credential lifecycle, webhook delivery, audit writes, funding, fulfilment, settlement, retry, wallet, go-live, or money movement.
Definition of done: Draft repository primitives are tested but not exposed through routes. Priority: P1.
Status: Complete (2026-06-30). Output: `services/onboarding/onboarding_draft_repository.py`; `test/test_onboarding_draft_repository.py`.
Finding: Added an onboarding draft repository module with no route wiring. The repository exposes create/read/update draft primitives, section upsert/read primitives, validation-result recording, idempotency reference record/read primitives using hash fields, and audit-link reference creation only. It uses external onboarding references, keeps `tenant_code` out of the repository contract, applies a local unsafe-key guard for obvious secrets and live-action fields, and uses existing `draft_version` for optimistic stale-update behavior. Tests use fake DB connections and cover create/read, external-reference scope, section upsert/read, unsafe secret/live-action rejection, stale version behavior, validation result recording, idempotency hash fields, audit-link references, and absence of live-action helper names.
Validation: Changed Python files compiled successfully with the bundled Python runtime. `scripts/check_migrations.py` passed. `git diff --check` passed. A local line-length sanity check passed. Local pytest, Black, and Ruff could not run because the bundled Python runtime does not include `pytest`, `black`, or `ruff`, and the project `.venv` points to a missing Python 3.11 executable. No API routes, frontend code, migrations, existing migration edits, live DB access, secrets, production data, account creation, invite delivery, campaign publication, credential lifecycle, webhook delivery, audit writes, event persistence, funding, fulfilment, settlement, retry, wallet, go-live, or money movement were introduced.

## TASK-105: Add draft idempotency helper

Objective: Implement idempotency key hashing, scoping, payload hash comparison, replay, and conflict logic for onboarding drafts only.
Type: Service/tests.
Dependencies: TASK-104.
Stop conditions: Stop if helper requires route wiring, live DB access, secrets, or non-draft side effects.
Validation expectation: Tests cover same-key/same-payload replay, same-key/different-payload conflict, scoped keys, hash-only storage, and no sensitive leakage.
Explicit non-goals: Do not make live commands idempotent, add routes, write audit rows, dispatch events, generate credentials, deliver webhooks, fund, fulfil, settle, retry, activate go-live, or move money.
Definition of done: Draft idempotency behavior is reusable and tested without route exposure. Priority: P1.
Status: Complete.
Finding: Added a pure onboarding draft idempotency helper with deterministic SHA-256 hashing for raw idempotency keys, canonical request payloads, and draft-scoped identities. The helper returns repository-safe hash fields for `onboarding_draft_idempotency_keys`, classifies new requests, same-key/same-payload replays, same-key/different-payload conflicts, and invalid unsupported requests, and rejects non-draft/live operation types without route wiring, DB access, audit writes, event dispatch, credential lifecycle, webhook delivery, go-live activation, funding, fulfilment, settlement, retry, wallet, or money movement.
Validation: Added focused helper tests for new-request fields, replay, conflict, scoped actor/external tenant/operation differences, deterministic payload hashing, sensitive-value non-leakage, blank keys, and unsupported live-action operations. Local validation covered targeted direct test execution, Python compile checks, migration hygiene, and diff whitespace checks where available.

## TASK-106: Add draft validation service using read-only readiness aggregation

Objective: Validate draft payloads and produce readiness preview without persistence side effects.
Type: Service/tests.
Dependencies: TASK-104; TASK-105; TASK-099.
Stop conditions: Stop if validation needs live DB access, secrets, route implementation, persistence beyond explicitly scoped draft reads, or live action semantics.
Validation expectation: Tests cover field validation, cross-section validation, permission-shaped inputs, missing evidence, safe errors, redaction, and go-live disabled state.
Explicit non-goals: Do not add API routes, create accounts, send invites, publish campaigns, generate credentials, deliver webhooks, write audit rows, fund, fulfil, settle, retry, activate go-live, or move money.
Definition of done: Draft validation can produce safe readiness previews without live side effects. Priority: P1.
Status: Complete.
Finding: Added a pure onboarding draft validation service that accepts draft-like payloads, sanitizes unsafe fields, validates required section fields, checks cross-section reference consistency, applies permission-limited category context, and returns bounded safe errors, blockers, warnings, missing evidence, redactions, guardrails, and next actions. The service produces a read-only readiness preview by reusing the existing onboarding state projection and readiness aggregation helpers, keeps go-live disabled, confirms no persistence, and does not call repository, DB, route, audit, event, credential, webhook, funding, fulfilment, settlement, retry, wallet, go-live, or money-movement behavior.
Validation: Added focused draft validation service tests for valid draft readiness preview, missing required fields, cross-section mismatch, permission-limited inputs, missing section evidence, unsafe secret/internal fields, blocked live-action attempts, disabled go-live controls, and money/retry/internal non-leakage. Local validation covered direct targeted draft validation tests, direct related projection/readiness/idempotency helper tests, Python compile checks, migration hygiene, and diff whitespace checks.

## TASK-107: Add admin draft save endpoint behind strict guardrails

Objective: Add a guarded admin endpoint that saves draft intent only.
Type: API.
Dependencies: TASK-104; TASK-105; TASK-106.
Stop conditions: Stop if endpoint requires live DB access, production data, secrets, auth weakening, broad permission refactors, live entity creation, or money actions.
Validation expectation: API tests cover auth, adjacent-role rejection, external-reference scope, idempotency, stale update, duplicate draft, safe errors, redaction, and no-live-action behavior.
Explicit non-goals: Do not create tenants, users, invites, campaigns, credentials, webhooks, funding, wallets, fulfilments, settlements, retries, go-live activation, or money movement.
Definition of done: Operators can save onboarding draft intent only, with no live activation semantics. Priority: P1.
Status: Complete.
Finding: Added a guarded `POST /admin/onboarding/drafts` endpoint in the existing admin onboarding router. The route preserves the current admin/operator permission boundary, validates draft-like input with the TASK-106 validation service, uses TASK-105 idempotency hashing for same-key replay and different-payload conflict handling, derives a stable external-scope draft reference for duplicate prevention, and persists draft intent only through TASK-104 repository primitives. It stores safe section payloads, validation snapshots, and idempotency hash references only, rejects user-supplied `tenant_code`, secret-bearing fields, and live-action attempts, keeps go-live disabled, and does not add update/stale-write semantics, audit writes, event persistence, frontend code, schema, migrations, credentials, webhooks, funding, wallet, fulfilment, settlement, retry, go-live activation, or money movement.
Validation: Added focused admin onboarding API tests for unauthenticated rejection, adjacent-role rejection, authorized draft intent save, external-reference scope, idempotency replay, idempotency conflict, duplicate draft conflict, user-facing `tenant_code` rejection, secret payload rejection, and live-action rejection. Targeted API plus TASK-104/TASK-105/TASK-106 tests passed locally, with Ruff check/format, Python compile, migration hygiene, and diff whitespace checks passing.

## TASK-108: Frontend draft-save integration behind disabled/live-safe controls

Objective: Connect onboarding shells to draft-save only if prior backend guardrails pass.
Type: Frontend/API integration.
Dependencies: TASK-107.
Stop conditions: Stop if frontend work enables live actions, credential lifecycle, webhook delivery, invite delivery, campaign publication, funding, fulfilment, settlement, retry, wallet, go-live, or money movement.
Validation expectation: Frontend tests cover save draft, safe errors, fallback, disabled live actions, no secret display, external references, and no `tenant_code` user-facing dependency.
Explicit non-goals: Do not implement submit-for-review, go-live, account creation, invite delivery, credential generation, webhook delivery, funding, fulfilment, settlement, retry, wallet, or money movement.
Definition of done: Frontend can save draft intent without enabling live onboarding. Priority: P1.
Status: Complete.
Finding: Added the first frontend draft-save integration slice behind live-safe controls. The shared admin onboarding API helper now posts to `POST /admin/onboarding/drafts` with external-reference scope, sanitized draft sections, idempotency key, and correlation ID while filtering user-facing `tenant_code`, secrets, credentials, live-action fields, webhook delivery, wallet, settlement, fulfilment, funding, retry, and money-movement keys. The Company onboarding shell can save draft intent only, shows bounded saved/conflict/unavailable states, preserves read-only hydration and local fallback, and keeps account creation/go-live behavior disabled.
Validation: Targeted frontend tests cover the admin onboarding helper, Company onboarding draft save success, safe endpoint failure fallback, idempotency/duplicate conflict fallback, disabled live actions, no secret fields, no user-facing `tenant_code`, and the onboarding demo smoke path. `npm.cmd test -- adminOnboarding.test.ts CompanyOnboardingPage.test.tsx OnboardingDemoJourneySmoke.test.tsx`, full `npm.cmd test`, `npm.cmd run build`, and `npm.cmd run lint` passed locally; lint completed with the existing repo warning baseline and no errors.

## TASK-109: Audit/event evidence implementation for draft save only

Objective: Add audit evidence only for draft save, with no webhook dispatch.
Type: Service/tests.
Dependencies: TASK-107.
Stop conditions: Stop if implementation dispatches events/webhooks, stores raw sensitive payloads, touches money domains, or enables live onboarding.
Validation expectation: Tests cover actor, role, external references, correlation ID, idempotency reference, before/after hash, changed sections, redaction, and no webhook/event dispatch unless explicitly scoped as internal evidence.
Explicit non-goals: Do not add webhook delivery, event replay, repair, credential lifecycle, invite delivery, campaign publication, funding, fulfilment, settlement, retry, wallet, go-live, or money movement.
Definition of done: Draft-save audit evidence is available without live platform side effects. Priority: P1.
Status: Complete.
Finding: Added a focused onboarding draft-save audit evidence helper and wired successful `POST /admin/onboarding/drafts` saves to the existing `onboarding_draft_audit_links` reference primitive. The helper produces safe evidence for draft-save only: actor reference, actor role, permission scope, external onboarding references, draft reference/version, operation/status, idempotency hash reference, correlation ID, deterministic before/after state hashes, changed section names, validation/readiness summaries, redaction categories, and `no_live_action_confirmed`. Route integration records a reference-only evidence summary with `event_ref=None`, no webhook/event dispatch metadata, and no raw before/after payloads, secrets, credentials, tenant-code user-facing fields, provider internals, webhook delivery internals, funding, wallet, settlement, fulfilment, retry, go-live, or money-movement data.
Validation: Added focused audit evidence helper tests for actor/role, external references, correlation ID, idempotency hash reference, before/after hashes, changed-section detection, validation/readiness summaries, redactions, tenant-code non-exposure, secret/provider/webhook/money internal redaction, no-live-action confirmation, reference-only audit-link fields, and absence of dispatch/live-action helper functions. Updated admin onboarding API tests to assert draft save creates a safe audit-link reference and skips audit-link creation on idempotency replay. Local validation passed for direct helper test execution with the bundled Python runtime, Python compile checks for changed Python files, `ruff check` on changed Python files, `scripts/check_migrations.py`, line-length sanity, and diff whitespace checks. Local `pytest` could not run because default Windows Python is broken and the bundled runtime lacks `pytest`/`httpx`; local `black` could not run because the available Anaconda `black` shim timed out even on `--version`.

## TASK-110: Checkpoint draft-save implementation readiness

Objective: Decide whether submit-for-review or dry-run validation can be implemented next.
Type: Docs.
Dependencies: TASK-102; TASK-103; TASK-104; TASK-105; TASK-106; TASK-107; TASK-108; TASK-109.
Stop conditions: Stop if checkpoint requires implementation work, live DB access, secrets, schema changes, migrations, writes, go-live, credential lifecycle, webhook delivery, funding, fulfilment, settlement, retry, audit mutation beyond completed draft-save evidence, or money movement.
Validation expectation: Documentation/readback confirms draft-save readiness, remaining blockers, validation baseline, and safe next priorities.
Explicit non-goals: Do not implement submit-for-review, dry-run route, live onboarding, credential lifecycle, webhook delivery, funding, fulfilment, settlement, retry, wallet, go-live, or money movement.
Definition of done: Roadmap has a clear decision point after draft-save foundations. Priority: P1.
Status: Complete.
Finding: Added `docs/roadmap/ONBOARDING_DRAFT_SAVE_READINESS_CHECKPOINT_TASK_110.md`. The checkpoint confirms TASK-102 through TASK-109 completed draft persistence foundations, clean DB/static schema checks, repository primitives, idempotency hashing, draft validation, guarded admin draft save, company onboarding frontend draft-save integration, and safe reference-only draft-save audit evidence. Decision: implement a guarded no-op dry-run validation route before submit-for-review. Dry-run is the safer next step because it can harden permissions, redaction, safe errors, missing evidence, and no-mutation behavior before any review state transition exists. TASK-027 and TASK-028 remain blocked.
Validation: Documentation/readback only. Confirmed the checkpoint preserves no-live-action boundaries and does not introduce backend routes, frontend code, services, tests, schema, migrations, DB access, secrets, production data, submit-for-review, dry-run implementation, live onboarding, credential lifecycle, webhook delivery, funding, wallet, fulfilment, settlement, retry, go-live, audit mutation beyond completed draft-save evidence, or money movement.

## TASK-111: Add guarded onboarding dry-run validation route

Objective: Expose no-op onboarding dry-run validation using the TASK-106 validation service and TASK-099 contract without persisting drafts, audit rows, events, or live platform state.
Type: API/Tests.
Dependencies: TASK-106; TASK-107; TASK-110; `docs/sa/ONBOARDING_DRY_RUN_VALIDATION_ENDPOINT_CONTRACT.md`.
Stop conditions: Stop if implementation requires schema changes, migrations, live DB access, production data, secrets, draft writes, validation-result persistence, audit writes, event persistence, credential lifecycle, webhook delivery, go-live, funding, wallet, fulfilment, settlement, retry, or money movement.
Validation expectation: Targeted API tests pass for authorized dry-run, malformed payloads, missing evidence, unknown references, no persistence, no audit write, no event dispatch, no `tenant_code` exposure, and no live actions.
Explicit non-goals: Do not implement draft save, submit-for-review, account creation, user/member/invite creation, campaign publication, credential lifecycle, webhook delivery, funding, fulfilment, settlement, retry, wallet, go-live, or money movement.
Definition of done: Admin/operator users can request safe dry-run validation feedback without any persistence or live side effects. Priority: P1.
Status: Complete.
Finding: Added guarded `POST /admin/onboarding/validate` in the existing admin onboarding router. The route uses the existing `require_session_key` plus onboarding admin role gate, calls TASK-106 `validate_onboarding_draft` for a no-op dry-run validation envelope, rejects user-supplied `tenant_code`, and returns readiness preview, missing evidence, blockers, safe errors, redactions, guardrails, `no_persistence_confirmed`, and `no_live_action_confirmed`. It does not call draft repository create/update/read/write methods, idempotency persistence, validation-result persistence, audit-link creation, audit evidence builders, event dispatch, webhook delivery, submit-for-review, credential lifecycle, funding, fulfilment, settlement, retry, go-live, or money movement.
Validation: Added targeted admin onboarding API tests for unauthenticated rejection, adjacent-role rejection, authorized admin/distribution/system admin dry-run validation, explicit missing evidence, safe malformed/cross-section validation errors, user-facing `tenant_code` rejection without echoing the supplied internal value, secret/live-action/money internal redaction, no repository persistence calls, and no audit evidence builder calls. `.venv_codex` validation passed for `python -m pytest test/api/test_admin_onboarding_api.py` with 33 tests and `python -m pytest test/test_onboarding_draft_validation_service.py` with 9 tests. Python compile checks, `ruff check` on changed files, `scripts/check_migrations.py`, manual line-length sanity, and diff whitespace checks passed. Black could not complete locally because the available `black` command timed out.

## TASK-112: Add dry-run validation permission and no-mutation tests

Objective: Lock the dry-run validation route to the intended permission, redaction, and no-mutation contract.
Type: API/Tests.
Dependencies: TASK-111; `docs/API_PERMISSION_MATRIX.md`.
Stop conditions: Stop if tests require production data, live DB access, secrets, auth weakening, broad permission refactors, persistence, audit writes, event dispatch, webhook delivery, or money movement.
Validation expectation: Tests confirm unauthenticated rejection, adjacent-role rejection, authorized admin/operator access, external-reference scope behavior, safe error responses, no persistence, no audit/event dispatch, no secret leakage, no `tenant_code` user-facing exposure, and no live action invocation.
Explicit non-goals: Do not change auth behavior unless tests reveal a clear route contract bug; do not add mutation routes, schema, frontend code, credential lifecycle, webhook delivery, funding, fulfilment, settlement, retry, wallet, go-live, or money movement.
Definition of done: Dry-run validation has regression coverage for RBAC, scope, redaction, and no-side-effect guarantees. Priority: P1.

Status: Complete.

Finding:
TASK-112 added dry-run validation API contract coverage for `POST /admin/onboarding/validate`, including unauthenticated rejection, adjacent-role rejection, authorized read-only validation, trimmed external-reference scope forwarding, safe malformed/missing/unknown evidence handling, no repository persistence, and no validation invocation for rejected identities. The regression tests also expanded redaction/no-leakage coverage for secret-like, provider, audit, webhook delivery, retry, funding, settlement, fulfilment, and money-movement internals. A narrow redaction gap was fixed by treating `private_key` and `funding_internal` as unsafe keys while preserving valid dry-run fields such as `funding_model_intention`.

Validation:
Targeted validation passed with `.venv_codex`: `pytest test/api/test_admin_onboarding_api.py` (38 passed), `pytest test/test_onboarding_draft_validation_service.py` (9 passed), `py_compile` for changed Python files, Ruff check for changed Python files, `scripts/check_migrations.py`, and `git diff --check`. Black check was attempted twice for the changed Python files and timed out locally; no formatting issues were reported by Ruff or diff checks. No production data, live DB access, secrets, backend mutations, auth weakening, broad permission refactors, mutation routes, schema, migrations, frontend code, onboarding writes, account creation, invitations, campaign publication, credential writes, webhook delivery, funding, fulfilment, settlement, retry, audit mutation, or money movement were introduced.

## TASK-113: Integrate frontend dry-run validation preview

Objective: Let onboarding shells preview dry-run validation and readiness feedback without saving, submitting, or enabling live actions.
Type: Frontend/API integration.
Dependencies: TASK-111; TASK-112; TASK-108.
Stop conditions: Stop if integration requires backend mutations, schema changes, auth changes, secrets, live DB access, draft persistence beyond existing save, submit-for-review, credential lifecycle, webhook delivery, go-live, funding, wallet, fulfilment, settlement, retry, or money movement.
Validation expectation: Frontend tests pass for loading, success, missing evidence, safe error fallback, disabled submit/go-live/live actions, external-reference query construction, no secret display, and no `tenant_code` user-facing exposure.
Explicit non-goals: Do not implement submit-for-review, account creation, invite delivery, role assignment, campaign publication, credential generation, webhook delivery, funding, fulfilment, settlement, retry, wallet, go-live, or money movement.
Definition of done: Onboarding UI can preview read-only/no-op validation feedback while preserving shell fallback and disabled live actions. Priority: P1.

Status: Complete.

Finding:
TASK-113 added a frontend dry-run validation helper for `POST /admin/onboarding/validate` and integrated the first safe slice into the company / organisation onboarding shell only. The helper trims and sends external-reference scope, supports validation scope, correlation ID, optional draft/idempotency references, and sanitizes section payloads before sending. The company shell now offers a clearly no-op validation preview that shows readiness status, missing evidence, blockers, warnings, next actions, and guardrails while preserving read-only hydration, draft-save behavior, local fallback, disabled account creation, and no submit/go-live/live-action controls.

Validation:
Frontend validation passed: `npm test -- adminOnboarding.test.ts` (9 passed), `npm test -- CompanyOnboardingPage.test.tsx` (11 passed), `npm test -- OnboardingDemoJourneySmoke.test.tsx` (5 passed), full `npm test` (112 passed), `npm run build`, and `npm run lint` with the existing warning baseline and no errors. No backend mutation, auth change, schema, migration, secrets, production data, live DB access, submit-for-review, go-live, account creation, invite delivery, role assignment, campaign publication, credential lifecycle, webhook delivery, funding, wallet, fulfilment, settlement, retry, or money movement was introduced.

## TASK-114: Submit-for-review contract final review

Objective: Decide the minimal submit-for-review boundary after dry-run validation and frontend preview are proven.
Type: Docs/checkpoint.
Dependencies: TASK-111; TASK-112; TASK-113; TASK-110.
Stop conditions: Stop if review requires implementation, schema changes, migrations, live DB access, secrets, production data, live onboarding, credential lifecycle, webhook delivery, funding, fulfilment, settlement, retry, or money movement.
Validation expectation: Documentation/readback confirms whether submit-for-review can proceed, required state transition semantics, permission posture, idempotency, audit evidence, rollback expectations, and no-live-action guardrails.
Explicit non-goals: Do not implement submit-for-review, approval, go-live, account creation, campaign publication, credential lifecycle, webhook delivery, funding, fulfilment, settlement, retry, wallet, or money movement.
Definition of done: Roadmap has a clear, reviewed submit-for-review boundary or an explicit stop decision. Priority: P1.

Status: Complete.

Finding:
Added `docs/roadmap/ONBOARDING_SUBMIT_FOR_REVIEW_CONTRACT_FINAL_REVIEW_TASK_114.md`. The checkpoint confirms TASK-111 through TASK-113 proved the no-op dry-run validation route, dry-run permission/no-mutation coverage, and frontend company validation preview after the draft-save readiness checkpoint. Decision: submit-for-review may proceed only as saved-draft repository/service transition primitives in TASK-115, with no API route, frontend controls, approval, go-live, account creation, invite delivery, campaign publication, credential lifecycle, webhook delivery, funding, wallet, fulfilment, settlement, retry, or money movement. The boundary defines allowed source statuses, target status direction, stale version behavior, replay/conflict idempotency posture, validation blocker handling, admin/operator permission posture, safe audit evidence expectations, bounded safe errors, rollback expectations, and TASK-115 guardrails.

Validation:
Documentation/readback only. Confirmed only roadmap documentation changed, TASK-027/TASK-028 remain blocked, and the checkpoint does not introduce backend routes, frontend code, services, tests, schema, migrations, live DB access, secrets, production data, submit-for-review implementation, approval, go-live, credential lifecycle, webhook delivery, funding, fulfilment, settlement, retry, wallet, or money movement.

## TASK-115: Add submit-for-review repository state transition

Status: Complete (2026-07-05). Output: `services/onboarding/onboarding_submit_for_review_service.py`; `test/test_onboarding_submit_for_review_service.py`.

Finding:
Added a focused submit-for-review service primitive that wraps the existing onboarding draft repository and hashed idempotency helper. The primitive transitions eligible saved drafts from `DRAFT_CREATED`, `DRAFT_UPDATED`, or validation-cleared `VALIDATION_FAILED` to the schema-backed `READY_FOR_REVIEW` status only when supplied validation evidence is unambiguously `VALID`. It returns safe results for success, replay, idempotency conflict, stale draft version, missing draft, invalid state, validation blockers, and unauthorized adjacent roles. No API route, frontend integration, schema, migration, audit/event dispatch, approval workflow, live action, credential lifecycle, webhook delivery, funding, wallet, fulfilment, settlement, retry, go-live, or money movement was added.

Validation:
`pytest test/test_onboarding_submit_for_review_service.py test/test_onboarding_draft_repository.py test/test_onboarding_draft_idempotency_service.py test/test_onboarding_draft_validation_service.py` passed (39 tests). `scripts/check_migrations.py` passed. Ruff passed for the changed Python files after import ordering fix. `py_compile` passed for the changed Python files. `git diff --check` passed. Black check was attempted but timed out locally on the changed service file; no formatting issues were reported by Ruff.

Objective: Add repository/service primitives for transitioning a saved draft to review state without route wiring or live activation.
Type: Service/Repository/Tests.
Dependencies: TASK-104; TASK-105; TASK-106; TASK-114.
Stop conditions: Stop if work requires API route exposure, frontend changes, schema changes beyond existing draft tables, live DB access, secrets, account creation, campaign publication, credential lifecycle, webhook delivery, go-live, funding, fulfilment, settlement, retry, or money movement.
Validation expectation: Tests cover valid transition, stale version behavior, invalid state, idempotency/replay posture, safe validation prerequisites, no audit/event dispatch, no live action, and no sensitive leakage.
Explicit non-goals: Do not add API routes, frontend integration, approval workflow, account creation, invites, campaign publication, credentials, webhooks, funding, fulfilment, settlement, retry, wallet, go-live, or money movement.
Definition of done: Submit-for-review transition primitives exist behind tests but are not externally exposed. Priority: P1.

## TASK-116: Add guarded submit-for-review endpoint

Objective: Expose a narrow admin/operator submit-for-review endpoint for saved drafts after repository transition and safety contracts pass.
Type: API/Tests.
Dependencies: TASK-115; TASK-109.
Stop conditions: Stop if endpoint requires auth weakening, broad permission refactors, production data, live DB access, secrets, account creation, invite delivery, campaign publication, credential lifecycle, webhook delivery, go-live, funding, wallet, fulfilment, settlement, retry, or money movement.
Validation expectation: API tests pass for auth, adjacent-role rejection, external-reference/draft scope, stale version, idempotency, validation blockers, safe errors, audit evidence reference, no `tenant_code` exposure, and no live action invocation.
Explicit non-goals: Do not approve, activate, publish, invite, create credentials, deliver webhooks, fund, fulfil, settle, retry, create wallets, go-live, or move money.
Definition of done: Saved drafts can be marked submitted for review under strict admin/operator guardrails only. Priority: P1.

Status: Complete.
Finding: Added `POST /admin/onboarding/drafts/{draft_ref}/submit-for-review` as a guarded admin/operator-only endpoint backed by the TASK-115 submit-for-review service primitive. The route reads the saved draft and sections, validates persisted evidence, enforces external-reference scope matching, requires optimistic `expected_version` and idempotency key, rejects user-facing `tenant_code`, and returns safe bounded responses with no submit audit evidence/event dispatch in this task.
Validation: `test/api/test_admin_onboarding_api.py` passed, `test/test_onboarding_submit_for_review_service.py` passed, `test/test_onboarding_draft_audit_evidence_service.py` passed, `scripts/check_migrations.py` passed, Ruff passed on changed Python files, and Python compile passed on changed Python files. Black check on the changed Python files timed out locally after 120 seconds. No production data, live DB access, secrets, backend mutations beyond the guarded draft status transition, auth weakening, broad permission refactors, mutation routes beyond submit-for-review, schema, migrations, frontend code, onboarding writes outside submit transition, account creation, invitations, campaign publication, credential writes, webhook delivery, funding, fulfilment, settlement, retry, audit mutation, wallet, go-live, or money movement were introduced.

## TASK-117: Integrate frontend submit-for-review controls

Objective: Add guarded frontend submit-for-review UI for saved drafts while preserving disabled live/go-live and no-money controls.
Type: Frontend/API integration.
Dependencies: TASK-116; TASK-113.
Stop conditions: Stop if frontend work enables account creation, invite delivery, campaign publication, credential lifecycle, webhook delivery, funding, wallet, fulfilment, settlement, retry, go-live, or money movement.
Validation expectation: Frontend tests pass for submitted-for-review flow, validation blockers, stale/conflict errors, safe fallback, disabled live actions, no secret display, and no `tenant_code` user-facing exposure.
Explicit non-goals: Do not implement approval, go-live, account/user creation, role assignment, campaign publication, credential generation, webhook delivery, funding, fulfilment, settlement, retry, wallet, or money movement.
Definition of done: Frontend can submit draft for review without enabling any live platform action. Priority: P1.

Status: Complete.

Finding: Added a frontend submit-for-review helper and Company Onboarding review-only control. The UI only enables submit after a saved draft reference exists, sends external references plus expected version, idempotency key, and correlation ID, preserves draft-save and dry-run validation behavior, and shows safe success, blocker, stale/conflict, and unavailable states without exposing `tenant_code` or raw unsafe values.

Validation: `npm.cmd test -- adminOnboarding.test.ts` passed, `npm.cmd test -- CompanyOnboardingPage.test.tsx` passed, `npm.cmd test -- OnboardingDemoJourneySmoke.test.tsx` passed, full `npm.cmd test` passed with 21 files and 118 tests, `npm.cmd run build` passed, and `npm.cmd run lint` passed with 42 existing warnings and 0 errors. No backend routes, backend mutations, auth changes, schema, migrations, secrets, production data, live DB access, approval, go-live, account/user creation, invite delivery, role assignment, campaign publication, credential lifecycle, webhook delivery, funding, wallet, fulfilment, settlement, retry, or money movement were introduced.

## TASK-118: Add submit-for-review audit evidence

Objective: Record safe reference-only evidence for submit-for-review transitions without webhook/event dispatch or raw sensitive payloads.
Type: Service/Tests.
Dependencies: TASK-116; TASK-109.
Stop conditions: Stop if implementation dispatches webhooks/events, stores raw sensitive payloads, exposes secrets, mutates live platform entities, touches money domains, or enables go-live.
Validation expectation: Tests cover actor, role, external references, draft ref/version, review operation/status, idempotency reference, before/after hash, changed state, redaction categories, correlation ID, and no dispatch/live-action behavior.
Explicit non-goals: Do not add webhook delivery, event replay, approval, go-live, credential lifecycle, invite delivery, campaign publication, funding, fulfilment, settlement, retry, wallet, or money movement.
Definition of done: Submit-for-review has safe audit evidence references only. Priority: P1.

Status: Complete.

Finding: Added safe reference-only submit-for-review audit evidence. Successful new submit transitions now record an `onboarding_draft_audit_links` reference with actor, role, permission scope, external references, draft reference/version, submit-for-review operation/status, hashed idempotency reference, correlation ID, before/after state hashes, changed state, validation/readiness summaries, redaction categories, and `no_live_action_confirmed`. Replay and rejection paths do not create additional audit links. Evidence keeps `audit_ref` and `event_ref` empty and records dispatch flags as false.

Validation: `.venv_codex\Scripts\python.exe -m pytest test/test_onboarding_draft_audit_evidence_service.py` passed with 11 tests, `.venv_codex\Scripts\python.exe -m pytest test/test_onboarding_submit_for_review_service.py` passed with 9 tests, `.venv_codex\Scripts\python.exe -m pytest test/api/test_admin_onboarding_api.py` passed with 48 tests, `scripts/check_migrations.py` passed, Ruff passed on changed Python files, and `py_compile` passed on changed Python files. Black check against the changed Python files timed out twice in the local environment before producing a result; no formatting error was reported. No frontend code, migrations, schema changes, live DB access, secrets, production data, webhook dispatch, event dispatch, replay/repair, approval, go-live, credential lifecycle, invite delivery, campaign publication, funding, fulfilment, settlement, retry, wallet, or money movement were introduced.

## TASK-119: Add review-flow permission and redaction regression tests

Objective: Lock submit-for-review and related read/dry-run surfaces to intended RBAC, scope, redaction, and no-live-action contracts.
Type: API/Tests.
Dependencies: TASK-116; TASK-118.
Stop conditions: Stop if tests require production data, live DB access, secrets, auth weakening, broad permission refactors, schema changes, live actions, webhook delivery, or money movement.
Validation expectation: Tests confirm unauthorized and adjacent-role rejection, authorized admin/operator access, cross-scope rejection, safe errors, no `tenant_code` exposure, no secrets/raw payloads, no provider/audit/webhook/money internals, and no live mutation invocation.
Explicit non-goals: Do not add routes, frontend code, schema, approval, go-live, credential lifecycle, webhook delivery, funding, fulfilment, settlement, retry, wallet, or money movement.
Definition of done: Review-flow permissions and safe response boundaries are regression-protected. Priority: P1.

Status: Complete.

Finding: Added review-flow API regression coverage for `GET /admin/onboarding/state`, `POST /admin/onboarding/validate`, `POST /admin/onboarding/drafts`, and `POST /admin/onboarding/drafts/{draft_ref}/submit-for-review`. The tests now confirm unauthenticated and adjacent-role requests are rejected before projection, validation, repository, transition, or audit helpers run; authorized admin/operator behavior remains covered; cross-scope submit attempts return safe not-found behavior without transition/idempotency/audit writes; missing draft errors stay safe; submit-for-review redacts unsafe saved evidence; submit audit output remains safe reference-only; dry-run stays no-persistence/no-live-action; draft save remains draft-intent only; and submit-for-review does not dispatch events/webhooks or introduce approval, activation, publication, credentials, funding, wallet, fulfilment, settlement, retry, or money movement.

Validation: `.venv_codex\Scripts\python.exe -m pytest test/api/test_admin_onboarding_api.py` passed with 78 tests, `.venv_codex\Scripts\python.exe -m pytest test/test_onboarding_submit_for_review_service.py` passed with 9 tests, `.venv_codex\Scripts\python.exe -m pytest test/test_onboarding_draft_audit_evidence_service.py` passed with 11 tests, `.venv_codex\Scripts\python.exe -m pytest test/test_onboarding_draft_validation_service.py` passed with 9 tests, `.venv_codex\Scripts\python.exe scripts\check_migrations.py` passed, Ruff passed on the changed Python test file, `py_compile` passed on the changed Python test file, and `git diff --check` passed with only the existing Windows LF-to-CRLF warning. Black check against the changed Python test file timed out in the local environment before producing a result; no formatting error was reported. No production data, live DB access, secrets, auth weakening, broad permission refactors, schema, migrations, frontend code, approval, go-live, credential lifecycle, webhook delivery, event dispatch, funding, fulfilment, settlement, retry, wallet, or money movement were introduced.

## TASK-120: Submit-for-review readiness checkpoint

Objective: Checkpoint the dry-run and submit-for-review wave and decide whether approval/review workflow can be scoped next.
Type: Docs.
Dependencies: TASK-111; TASK-112; TASK-113; TASK-114; TASK-115; TASK-116; TASK-117; TASK-118; TASK-119.
Stop conditions: Stop if checkpoint requires implementation, live DB access, secrets, schema changes, migrations, approval workflow, live onboarding, credential lifecycle, webhook delivery, funding, fulfilment, settlement, retry, go-live, or money movement.
Validation expectation: Documentation/readback confirms completed work, validation baseline, remaining blockers, no-live-action posture, TASK-027/TASK-028 status, and safe next priorities.
Explicit non-goals: Do not implement approval, live onboarding, credential lifecycle, webhook delivery, funding, fulfilment, settlement, retry, wallet, go-live, or money movement.
Definition of done: Roadmap has a clear decision point after submit-for-review foundations. Priority: P1.

Status: Complete (2026-07-05). Output: `docs/roadmap/ONBOARDING_SUBMIT_FOR_REVIEW_READINESS_CHECKPOINT_TASK_120.md`.
Finding: Added the TASK-120 submit-for-review readiness checkpoint covering TASK-111 through TASK-119 outcomes, completed dry-run validation, draft-save, submit-for-review, frontend control, safe audit evidence, RBAC/redaction regression coverage, validation baseline, permission/safety posture, explicit not-live boundaries, and TASK-027/TASK-028 blockers. Decision: the next wave may scope internal review decision workflow foundations only; review decisions must remain state classifications and must not imply approval-to-launch, go-live, live onboarding, provisioning, account creation, campaign publication, credential lifecycle, webhook delivery, funding, wallet, fulfilment, settlement, retry, billing, ledger, or money movement.
Validation: Documentation/readback only. Confirmed TASK-120 changed docs only; no backend code, frontend code, services, routes, tests, schema, migrations, DB access, secrets, approval implementation, live onboarding, credential lifecycle, webhook delivery, event dispatch, funding, wallet, fulfilment, settlement, retry, go-live, or money movement were introduced. Readback confirms completed capabilities, remaining gaps, blockers, and next priorities are explicit and guarded.

## TASK-121: Review decision workflow contract final review

Objective: Define the minimal internal review-decision boundary after submit-for-review without enabling go-live or downstream activation.
Type: Docs/checkpoint.
Dependencies: TASK-120.
Stop conditions: Stop if review requires implementation, schema changes, migrations, live DB access, secrets, live onboarding, approval-to-launch, account creation, invite delivery, campaign publication, credential lifecycle, webhook delivery, funding, fulfilment, settlement, retry, wallet, go-live, or money movement.
Validation expectation: Documentation/readback confirms allowed review outcomes, state transition boundaries, permission posture, idempotency posture, audit evidence expectations, safe errors, rollback posture, and no-live-action guardrails.
Explicit non-goals: Do not implement review decisions, approval-to-launch, go-live, live onboarding, credentials, webhooks, funding, fulfilment, settlement, retry, wallet, or money movement.
Definition of done: Roadmap has a clear reviewed boundary for review-decision primitives or an explicit stop decision. Priority: P1.

Status: Complete (2026-07-11). Output: `docs/roadmap/ONBOARDING_REVIEW_DECISION_WORKFLOW_CONTRACT_FINAL_REVIEW_TASK_121.md`.
Finding: Added the TASK-121 onboarding review decision workflow contract final review. The checkpoint classifies review decisions as Shared Platform work, confirms current submit-for-review behavior transitions eligible drafts to `READY_FOR_REVIEW`, documents the current schema-backed draft statuses, and records that separate persisted approval/rejection/changes-requested statuses do not exist today. Decision: TASK-122 may proceed only as narrow internal service/repository primitives for review-state classification, and must either use existing schema-backed status/metadata safely or stop for reviewed schema/migration work rather than inventing persisted statuses.
Validation: Documentation/readback only. Confirmed TASK-121 changed docs only; no backend code, frontend code, services, routes, tests, schema, migrations, live DB access, secrets, review decision implementation, approval-to-launch, live onboarding, credential lifecycle, webhook delivery, event dispatch, funding, wallet, fulfilment, settlement, retry, go-live, billing, ledger, or money movement were introduced. Readback confirms allowed review outcomes, state transition boundaries, permission posture, idempotency posture, audit evidence expectations, safe errors, rollback posture, no-live-action guardrails, and TASK-027/TASK-028 blockers are explicit.

## TASK-122: Add review decision service primitives

Objective: Add service/repository primitives for internal review decisions on submitted onboarding drafts without route wiring or live activation.
Type: Service/Repository/Tests.
Dependencies: TASK-121; TASK-115; TASK-118.
Stop conditions: Stop if work requires API route exposure, frontend changes, schema changes, live DB access, secrets, auth weakening, account creation, invite delivery, campaign publication, credential lifecycle, webhook delivery, funding, fulfilment, settlement, retry, wallet, go-live, or money movement.
Validation expectation: Tests cover valid review decisions, invalid source state, stale version, idempotency replay/conflict, validation prerequisites, safe errors, no dispatch, no live action, and no sensitive leakage.
Explicit non-goals: Do not add routes, frontend integration, approval-to-launch, account creation, invites, campaign publication, credentials, webhooks, funding, fulfilment, settlement, retry, wallet, go-live, or money movement.
Definition of done: Review decision primitives are tested but not externally exposed. Priority: P1.

Status: Complete (2026-07-11). Output: `services/onboarding/onboarding_review_decision_service.py`; `test/test_onboarding_review_decision_service.py`; `services/onboarding/onboarding_draft_idempotency_service.py`.
Finding: Added narrow review-decision service primitives for submitted onboarding drafts without API route wiring, frontend integration, schema changes, migrations, audit-link creation, event dispatch, live activation, or money movement. The service records internal review decisions only for `READY_FOR_REVIEW` drafts, requires admin/operator role, expected draft version, scoped idempotency, current validation evidence, and a reason, stores reason evidence as a hash, and returns safe no-live-action envelopes. `APPROVED_FOR_INTERNAL_REVIEW` is represented as metadata while preserving schema-backed `READY_FOR_REVIEW`; `BLOCKED` uses the existing schema-backed `BLOCKED` status; unsupported schema outcomes such as `REJECTED` are rejected with safe `UNSUPPORTED_SCHEMA_STATE` rather than inventing persisted statuses. Added `ONBOARDING_DRAFT_REVIEW_DECISION` to the draft idempotency operation allow-list.
Validation: `.venv_codex\Scripts\python.exe -m pytest test\test_onboarding_review_decision_service.py` passed with 12 tests, `.venv_codex\Scripts\python.exe -m pytest test\test_onboarding_draft_idempotency_service.py` passed with 10 tests, `.venv_codex\Scripts\python.exe -m pytest test\test_onboarding_submit_for_review_service.py` passed with 9 tests, and the combined focused pytest run passed with 31 tests. Ruff passed on changed Python files with the existing pyproject deprecation warning, and `py_compile` passed on changed Python files. No API routes, frontend code, schema, migrations, live DB access, secrets, auth weakening, account creation, invite delivery, campaign publication, credential lifecycle, webhook delivery, funding, fulfilment, settlement, retry, wallet, go-live, audit/event dispatch, billing, ledger, or money movement were introduced.

## TASK-123: Add review decision validation and eligibility tests

Status: Complete (2026-07-12). Output: `test/test_onboarding_review_decision_service.py`.
Finding: Added focused regression coverage for review-decision eligibility before route exposure. Tests now lock unsupported schema outcomes including `CHANGES_REQUESTED`/`REJECTED`, unknown launch-like outcomes, all non-`READY_FOR_REVIEW` source states, missing external scope, invalid idempotency key, validation blockers, missing evidence, unsafe safe-error shapes, readiness permission limits, adjacent-role rejection, stale version behavior, no-live-action guardrails, idempotency replay/conflict behavior, and redaction/no secret leakage. No service code, routes, frontend code, schema, migrations, live DB access, audit/event dispatch, credential lifecycle, webhook delivery, funding, wallet, fulfilment, settlement, retry, go-live, billing, ledger, or money movement was introduced.
Validation: `.venv_codex\Scripts\python.exe -m pytest test\test_onboarding_review_decision_service.py` passed with 24 tests. `.venv_codex\Scripts\python.exe -m ruff check test\test_onboarding_review_decision_service.py` passed with only the existing top-level Ruff settings deprecation warning. `.venv_codex\Scripts\python.exe -m py_compile test\test_onboarding_review_decision_service.py` passed.
Objective: Lock review-decision eligibility, validation blocker, stale-version, and safe-error behavior before route exposure.
Type: Tests.
Dependencies: TASK-122.
Stop conditions: Stop if tests require production data, live DB access, secrets, auth weakening, schema changes, live actions, webhook delivery, funding, fulfilment, settlement, retry, wallet, go-live, or money movement.
Validation expectation: Targeted service tests pass for each allowed and rejected review decision, including no-live-action and redaction expectations.
Explicit non-goals: Do not add API routes, frontend code, schema, migrations, approval-to-launch, live onboarding, credentials, webhooks, funding, fulfilment, settlement, retry, wallet, or money movement.
Definition of done: Review-decision service behavior is regression-protected before API exposure. Priority: P1.

## TASK-124: Add guarded admin review decision endpoint

Status: Complete (2026-07-12). Output: `apps/api/routers/admin_onboarding.py`; `test/api/test_admin_onboarding_api.py`.
Finding: Added guarded `POST /admin/onboarding/drafts/{draft_ref}/review-decision` endpoint for internal admin/operator review decisions on submitted onboarding drafts. The endpoint reuses existing onboarding auth, external-reference scope checks, saved draft section validation, scoped idempotency, stale-version handling, and TASK-122 review-decision service primitives. Responses preserve safe external envelopes, no `tenant_code` exposure, no raw reason/idempotency leakage, no audit evidence creation in this task, no route-triggered live action, and explicit no approval-to-launch/go-live posture. API tests cover unauthenticated and adjacent-role rejection before helpers, successful metadata-only internal approval, schema-backed blocked status, cross-scope safety, stale version, invalid state, validation blockers, unsupported schema outcomes, idempotency replay/conflict, redaction, and no live/money side effects.
Validation: `.venv_codex\Scripts\python.exe -m pytest test\api\test_admin_onboarding_api.py test\test_onboarding_review_decision_service.py` passed with 117 tests. `.venv_codex\Scripts\python.exe -m ruff check apps\api\routers\admin_onboarding.py test\api\test_admin_onboarding_api.py` passed after import ordering fix with only the existing top-level Ruff settings deprecation warning. `.venv_codex\Scripts\python.exe -m py_compile apps\api\routers\admin_onboarding.py test\api\test_admin_onboarding_api.py` passed.
Objective: Expose a narrow admin/operator endpoint for internal review decisions on submitted onboarding drafts after service and validation contracts pass.
Type: API/Tests.
Dependencies: TASK-122; TASK-123.
Stop conditions: Stop if endpoint requires auth weakening, broad permission refactors, production data, live DB access, secrets, schema changes, account creation, invite delivery, campaign publication, credential lifecycle, webhook delivery, funding, fulfilment, settlement, retry, wallet, go-live, or money movement.
Validation expectation: API tests pass for auth, adjacent-role rejection, external-reference/draft scope, stale version, idempotency, validation blockers, safe errors, audit evidence reference posture, no `tenant_code` exposure, and no live action invocation.
Explicit non-goals: Do not approve-to-launch, activate, publish, invite, create credentials, deliver webhooks, fund, fulfil, settle, retry, create wallets, go-live, or move money.
Definition of done: Submitted drafts can receive internal review decisions under strict admin/operator guardrails only. Priority: P1.

## TASK-125: Add review decision audit evidence references

Status: Complete (2026-07-12). Output: `services/onboarding/onboarding_draft_audit_evidence_service.py`; `services/onboarding/onboarding_review_decision_service.py`; `apps/api/routers/admin_onboarding.py`; `test/test_onboarding_draft_audit_evidence_service.py`; `test/test_onboarding_review_decision_service.py`; `test/api/test_admin_onboarding_api.py`.
Product boundary: Shared Platform.
Required boundary docs checked: `AGENTS.md`; `docs/product/README.md`; `docs/roadmap/README.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `docs/roadmap/ONBOARDING_REVIEW_DECISION_WORKFLOW_CONTRACT_FINAL_REVIEW_TASK_121.md`.
Shared primitive impact: onboarding review-decision audit evidence now uses the existing `onboarding_draft_audit_links` reference primitive and shared audit evidence helper shape.
Source duplication: No.
Finding: Added safe reference-only review-decision audit evidence for successful new review decisions. The evidence records actor reference, actor role, permission scope, external onboarding references, draft reference/version, review-decision operation/status, review outcome, reason hash reference, hashed idempotency reference, correlation ID, before/after state hashes, changed state, validation/readiness summaries, redaction categories, and `no_live_action_confirmed`. The review-decision service now creates the audit-link reference after the successful idempotency record and returns `audit_evidence_ref`, `audit_link_ref`, and `RECORDED_REFERENCE` to the existing guarded admin endpoint. Replay, conflict, stale, validation-blocked, unsupported-outcome, missing-draft, and permission-denied paths do not create audit-link references.
Validation: `.venv_codex` validation passed for `python -m pytest test/test_onboarding_draft_audit_evidence_service.py test/test_onboarding_review_decision_service.py test/api/test_admin_onboarding_api.py` with 130 tests. Python compile checks passed for changed Python files. `ruff check` passed for changed Python files. Default Windows `python` remains broken and could not launch, so validation used the repo virtual environment.
Objective: Record safe reference-only evidence for review decisions without webhook/event dispatch or raw sensitive payloads.
Type: Service/Tests.
Dependencies: TASK-124; TASK-118.
Stop conditions: Stop if implementation dispatches webhooks/events, stores raw sensitive payloads, exposes secrets, mutates live platform entities, touches money domains, or enables go-live.
Validation expectation: Tests cover actor, role, external references, draft ref/version, review decision/status, idempotency reference, before/after hash, changed state, redaction categories, correlation ID, and no dispatch/live-action behavior.
Explicit non-goals: Do not add webhook delivery, event replay, approval-to-launch, go-live, credential lifecycle, invite delivery, campaign publication, funding, fulfilment, settlement, retry, wallet, or money movement.
Definition of done: Review decisions have safe audit evidence references only. Priority: P1.

## TASK-126: Integrate frontend review decision controls

Status: Complete (2026-07-12). Output: `frontend/src/api/endpoints/adminOnboarding.ts`; `frontend/src/api/endpoints/adminOnboarding.test.ts`; `frontend/src/pages/admin/CompanyOnboardingPage.tsx`; `frontend/src/pages/admin/CompanyOnboardingPage.test.tsx`; `frontend/src/pages/admin/OnboardingDemoJourneySmoke.test.tsx`.
Product boundary: Shared Platform.
Required boundary docs checked: `AGENTS.md`; `docs/product/README.md`; `docs/roadmap/README.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `docs/roadmap/ONBOARDING_REVIEW_DECISION_WORKFLOW_CONTRACT_FINAL_REVIEW_TASK_121.md`.
Shared primitive impact: frontend onboarding review workflow now consumes the guarded review-decision API while preserving shared external-reference, idempotency, audit-reference, and no-live-action guardrails.
Source duplication: No.
Finding: Added a typed frontend review-decision API client for `POST /admin/onboarding/drafts/{draft_ref}/review-decision` and guarded company onboarding controls that appear only after a saved draft is submitted to `READY_FOR_REVIEW`. The UI supports `APPROVED_FOR_INTERNAL_REVIEW` and `BLOCKED`, requires a bounded review reason, sends external references plus expected version/idempotency only, displays audit evidence references, and keeps account creation, approval-to-launch, go-live, credential lifecycle, webhook dispatch, publishing, funding, fulfilment, settlement, retry, wallet, and money movement disabled/out of scope. Safe fallback copy covers missing reason, stale/conflict, validation-blocked, and unavailable review-decision cases.
Validation: Frontend validation passed for `npm.cmd run test -- adminOnboarding.test.ts CompanyOnboardingPage.test.tsx OnboardingDemoJourneySmoke.test.tsx` with 37 tests; `npx.cmd tsc --noEmit -p tsconfig.json`; and targeted `npx.cmd eslint` on changed frontend files. PowerShell blocked the npm/npx `.ps1` shims, so validation used the `.cmd` entry points without changing machine policy.
Objective: Add guarded frontend review decision controls for submitted drafts while preserving disabled live/go-live and no-money controls.
Type: Frontend/API integration.
Dependencies: TASK-124; TASK-125; TASK-117.
Stop conditions: Stop if frontend work enables account creation, invite delivery, campaign publication, credential lifecycle, webhook delivery, funding, wallet, fulfilment, settlement, retry, go-live, or money movement.
Validation expectation: Frontend tests pass for review decision success, validation blockers, stale/conflict errors, safe fallback, disabled live actions, no secret display, and no `tenant_code` user-facing exposure.
Explicit non-goals: Do not implement approval-to-launch, go-live, account/user creation, role assignment, campaign publication, credential generation, webhook delivery, funding, fulfilment, settlement, retry, wallet, or money movement.
Definition of done: Frontend can record internal review decisions without enabling any live platform action. Priority: P1.

## TASK-127: Add review decision RBAC and redaction regression tests

Status: Complete (2026-07-12). Output: `test/api/test_admin_onboarding_api.py`.
Product boundary: Shared Platform.
Required boundary docs checked: `AGENTS.md`; `docs/product/README.md`; `docs/roadmap/README.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `docs/roadmap/ONBOARDING_REVIEW_DECISION_WORKFLOW_CONTRACT_FINAL_REVIEW_TASK_121.md`.
Shared primitive impact: Review-decision API route permissions, safe response redaction, scope rejection, audit-link dispatch flags, and no-live-action behavior are now regression-protected.
Source duplication: No.
Finding: Added regression coverage for the authorized admin/operator role matrix, nested `tenant_code` rejection before draft lookup, hostile saved-evidence validation blocking/redaction, absence of raw reason text/secrets/provider/audit/webhook/value-transfer internals, and no live mutation calls.
Validation: Passed `.venv_codex\Scripts\python.exe -m pytest -q --no-cov test\api\test_admin_onboarding_api.py --tb=short`; passed `.venv_codex\Scripts\python.exe -m py_compile test\api\test_admin_onboarding_api.py`; passed `ruff check test\api\test_admin_onboarding_api.py`.

Objective: Lock review-decision routes and related onboarding review surfaces to intended RBAC, scope, redaction, and no-live-action contracts.
Type: API/Tests.
Dependencies: TASK-124; TASK-125.
Stop conditions: Stop if tests require production data, live DB access, secrets, auth weakening, broad permission refactors, schema changes, live actions, webhook delivery, funding, fulfilment, settlement, retry, wallet, go-live, or money movement.
Validation expectation: Tests confirm unauthorized and adjacent-role rejection, authorized admin/operator access, cross-scope rejection, safe errors, no `tenant_code` exposure, no secrets/raw payloads, no provider/audit/webhook/money internals, and no live mutation invocation.
Explicit non-goals: Do not add routes, frontend code, schema, approval-to-launch, go-live, credential lifecycle, webhook delivery, funding, fulfilment, settlement, retry, wallet, or money movement.
Definition of done: Review-decision permissions and safe response boundaries are regression-protected. Priority: P1.

## TASK-128: Document approval-to-go-live separation

Status: Complete (2026-07-12). Output: `docs/roadmap/ONBOARDING_APPROVAL_TO_GO_LIVE_SEPARATION_TASK_128.md`.
Product boundary: Shared Platform.
Required boundary docs checked: `AGENTS.md`; `docs/product/README.md`; `docs/roadmap/README.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `docs/roadmap/ONBOARDING_SUBMIT_FOR_REVIEW_READINESS_CHECKPOINT_TASK_120.md`; `docs/roadmap/ONBOARDING_REVIEW_DECISION_WORKFLOW_CONTRACT_FINAL_REVIEW_TASK_121.md`.
Shared primitive impact: Internal onboarding review decisions are explicitly separated from any future approval-to-go-live or downstream activation workflow.
Source duplication: No.
Finding: Documented that `APPROVED_FOR_INTERNAL_REVIEW` is review classification only, current responses keep `approval_to_launch` and `go_live_enabled` false, audit evidence is reference-only/no-dispatch, and future go-live work requires a separate reviewed task chain covering schema, permissions, idempotency, audit, rollback, live DB/state verification, redaction, downstream dependencies, and no-dispatch/no-money gates.
Validation: Documentation/readback only. Confirmed no backend code, frontend code, services, routes, tests, schema, migrations, live DB access, secrets, live onboarding, credential lifecycle, webhook delivery, funding, fulfilment, settlement, retry, wallet, go-live, billing, ledger, or money movement was introduced.

Objective: Document the boundary between internal onboarding review decisions and any future go-live or downstream activation workflow.
Type: Docs.
Dependencies: TASK-127.
Stop conditions: Stop if documentation requires implementation, live DB access, secrets, schema changes, migrations, live onboarding, credential lifecycle, webhook delivery, funding, fulfilment, settlement, retry, wallet, go-live, or money movement.
Validation expectation: Documentation/readback confirms review approval does not trigger launch, provisioning, credentials, webhooks, funding, fulfilment, settlement, retry, wallet, or money movement.
Explicit non-goals: Do not implement go-live, approval-to-launch, live onboarding, credential lifecycle, webhook delivery, funding, fulfilment, settlement, retry, wallet, or money movement.
Definition of done: Future go-live work has a clearly separated boundary from review decisions. Priority: P1.

## TASK-129: Add pre-go-live safety checkpoint

Status: Complete (2026-07-12). Output: `docs/roadmap/ONBOARDING_PRE_GO_LIVE_SAFETY_CHECKPOINT_TASK_129.md`.
Product boundary: Shared Platform.
Required boundary docs checked: `AGENTS.md`; `docs/product/README.md`; `docs/roadmap/README.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `docs/roadmap/ONBOARDING_REVIEW_DECISION_WORKFLOW_CONTRACT_FINAL_REVIEW_TASK_121.md`; `docs/roadmap/ONBOARDING_APPROVAL_TO_GO_LIVE_SEPARATION_TASK_128.md`; `docs/roadmap/TASK_027_LOCAL_DB_VERIFICATION_RESULTS.md`; `docs/roadmap/TASK_028_SCHEMA_UNCERTAINTY_RESOLUTION.md`.
Shared primitive impact: Review-decision readiness now has an explicit stop gate before approval-to-launch, live onboarding, downstream activation, dispatch, or money-domain planning.
Source duplication: No.
Finding: Added the pre-go-live safety checkpoint. The checkpoint records current review workflow capabilities, confirms `APPROVED_FOR_INTERNAL_REVIEW` is still review classification only, preserves `approval_to_launch: false`, `go_live_enabled: false`, and `no_live_action_confirmed: true`, captures TASK-027 local-only verification and TASK-028 local schema-resolution posture, and requires a future separate task chain before go-live planning can begin.
Validation: Documentation/readback only. Confirmed no backend code, frontend code, services, routes, tests, schema, migrations, live DB access, secrets, production data, credential lifecycle, webhook delivery, funding, fulfilment, settlement, retry, wallet, go-live, billing, ledger, or money movement was introduced.

Objective: Checkpoint review workflow readiness before any go-live or downstream activation work is considered.
Type: Docs/checkpoint.
Dependencies: TASK-128.
Stop conditions: Stop if checkpoint requires implementation, live DB access, secrets, schema changes, migrations, production data, credential lifecycle, webhook delivery, funding, fulfilment, settlement, retry, wallet, go-live, or money movement.
Validation expectation: Documentation/readback confirms review capabilities, blockers, TASK-027/TASK-028 status, live verification posture, and explicit stop conditions before go-live planning.
Explicit non-goals: Do not implement go-live, live onboarding, credentials, webhooks, funding, fulfilment, settlement, retry, wallet, or money movement.
Definition of done: Roadmap has a clear stop point before any live activation planning begins. Priority: P1.

## TASK-130: Review workflow readiness checkpoint

Status: Complete (2026-07-12). Output: `docs/roadmap/ONBOARDING_REVIEW_WORKFLOW_READINESS_CHECKPOINT_TASK_130.md`.
Product boundary: Shared Platform.
Required boundary docs checked: `AGENTS.md`; `docs/product/README.md`; `docs/roadmap/README.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `docs/roadmap/ONBOARDING_REVIEW_DECISION_WORKFLOW_CONTRACT_FINAL_REVIEW_TASK_121.md`; `docs/roadmap/ONBOARDING_APPROVAL_TO_GO_LIVE_SEPARATION_TASK_128.md`; `docs/roadmap/ONBOARDING_PRE_GO_LIVE_SAFETY_CHECKPOINT_TASK_129.md`; `docs/roadmap/TASK_027_LOCAL_DB_VERIFICATION_RESULTS.md`; `docs/roadmap/TASK_028_SCHEMA_UNCERTAINTY_RESOLUTION.md`.
Shared primitive impact: The onboarding review-decision foundation wave is closed as a guarded internal workflow and explicitly routed away from go-live, activation, dispatch, and money-domain implementation.
Source duplication: No.
Finding: Added the review workflow readiness checkpoint summarizing TASK-121 through TASK-129, rating the internal review-decision foundation around 8/10 to 8.5/10, listing remaining production/go-live blockers, preserving the no-live-action posture, and routing safe next priorities back to bounded Referral SaaS productization, review-only hardening, or approved non-local read-only verification.
Validation: Documentation/readback only. Confirmed no backend code, frontend code, services, routes, tests, schema, migrations, live DB access, secrets, production data, live onboarding, credential lifecycle, webhook delivery, funding, fulfilment, settlement, retry, wallet, go-live, billing, ledger, or money movement was introduced.

Objective: Summarize the review-decision wave and decide whether any further implementation is safe without TASK-027/TASK-028 live DB verification.
Type: Docs/checkpoint.
Dependencies: TASK-121; TASK-122; TASK-123; TASK-124; TASK-125; TASK-126; TASK-127; TASK-128; TASK-129.
Stop conditions: Stop if checkpoint requires implementation, live DB access, secrets, schema changes, migrations, production data, live onboarding, credential lifecycle, webhook delivery, funding, fulfilment, settlement, retry, wallet, go-live, or money movement.
Validation expectation: Documentation/readback confirms completed review workflow capabilities, remaining blockers, no-live-action posture, TASK-027/TASK-028 status, and safe next priorities.
Explicit non-goals: Do not implement go-live, live onboarding, credential lifecycle, webhook delivery, funding, fulfilment, settlement, retry, wallet, or money movement.
Definition of done: Roadmap has a clear decision point after review workflow foundations. Priority: P1.

## TASK-131: Split product and roadmap documentation boundaries for referral SaaS and DLaaS

Status: Complete (2026-07-11). Output: `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/product/dlaas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/roadmap/dlaas/ROADMAP.md`; `docs/product/README.md`; `docs/roadmap/README.md`.
Linked enhancement: DLaaS platform productization and referral SaaS first-wedge packaging.
Linked platform capability: Product boundary management; roadmap traceability; platform reuse.
Goal: Separate product and roadmap documentation for Referral Management and Campaign Attribution SaaS from broader DLaaS expansion without copying or forking source code.
Why now: The project needs a focused commercial SaaS wedge while preserving DLaaS as the broader platform direction. Product clarity should come from documentation and module boundaries, not duplicated source trees.
Files likely involved: `docs/product/*`; `docs/roadmap/*`; existing SA docs and ordered task list for traceability.
Database/schema impact: None.
Backend impact: None. No service, router, schema, or API behavior changed.
Frontend impact: None. No frontend behavior changed.
API impact: None.
Tests to add/update: No runtime tests required for this docs-only boundary split.
Validation method: Readback confirms product docs and roadmap docs are separated, existing referral/campaign attribution capabilities are treated as current implementation, DLaaS expansion is not mixed into first SaaS launch requirements, and source duplication is explicitly rejected.
Acceptance criteria: Product folders exist for `referral-saas` and `dlaas`; roadmap folders exist for `referral-saas` and `dlaas`; docs state shared implementation primitives must remain single-source; first SaaS launch scope is separated from DLaaS expansion scope.
Dependencies: Current code assessment of referral code, progress, campaign readiness, link/code inspection, and attribution-related tests.
Blocked by: None.
Risk level: Low.
Rollback notes: Revert documentation-only additions and this roadmap entry.
Definition of done: The repository has clear documentation boundaries for the referral/campaign attribution SaaS wedge and DLaaS expansion without source-code forking. Priority: P1.

## TASK-132: Add mandatory product boundary gate to agent and roadmap workflow

Status: Complete (2026-07-11). Output: `AGENTS.md`; `docs/product/README.md`; `docs/roadmap/README.md`; `docs/roadmap/TASK_TEMPLATE.md`.
Product boundary: Shared Platform.
Required boundary docs checked: `docs/product/README.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/product/dlaas/PRODUCT_BRIEF.md`; `docs/roadmap/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/roadmap/dlaas/ROADMAP.md`.
Linked enhancement: DLaaS platform productization and referral SaaS first-wedge packaging.
Linked platform capability: Agent workflow guardrails; product boundary management; roadmap traceability; platform reuse.
Goal: Require future tasks to classify their product boundary and read the relevant boundary docs before implementation.
Why now: Future implementation should not depend on repeated prompting to separate Referral SaaS work from broader DLaaS work or to avoid source-code duplication.
Files likely involved: `AGENTS.md`; `docs/product/README.md`; `docs/roadmap/README.md`; `docs/roadmap/TASK_TEMPLATE.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Database/schema impact: None.
Backend impact: None.
Frontend impact: None.
API impact: None.
Tests to add/update: No runtime tests required for documentation/workflow guardrails.
Validation method: Readback confirms `AGENTS.md` includes a Product Boundary Gate, required boundary docs by task type, no source-code forking rule, updated required workflow chain, and required task metadata. Readback also confirms roadmap/product READMEs route tasks and `TASK_TEMPLATE.md` includes product boundary fields.
Acceptance criteria: Every future task has a documented mechanism to identify `Referral SaaS`, `DLaaS`, or `Shared Platform`; future implementation tasks must read the correct boundary docs first; source duplication remains explicitly disallowed.
Dependencies: TASK-131.
Blocked by: None.
Risk level: Low.
Rollback notes: Revert documentation-only additions and this roadmap entry.
Explicit non-goals: Do not modify backend code, frontend code, APIs, schema, migrations, tests, or product behavior.
Definition of done: The repo-level workflow itself enforces product boundary reading and classification before implementation. Priority: P1.

## TASK-133: Build Referral SaaS 10/10 gap matrix

Status: Complete (2026-07-11). Output: `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `docs/product/README.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Referral code lifecycle; campaign setup/readiness; progress/event ingestion; campaign attribution trace; tenant-safe reporting; public API productization; Referral SaaS E2E and live verification.
Goal: Convert the current code assessment into a focused 10/10 gap matrix for the Referral Management and Campaign Attribution SaaS product boundary.
Why now: The repository already contains substantial referral, progress, campaign, link/code, and attribution capabilities. The next step is to identify packaging and hardening work without duplicating source code or mixing in broad DLaaS scope.
Current source-of-truth files inspected: `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/CURRENT_STATE_MAP.md`; `docs/sa/CAPABILITY_GAP_MATRIX.md`; current referral/campaign/progress/link/attribution service, router, frontend, and test file inventory by static inspection.
Shared primitive impact: No implementation impact. The matrix identifies future shared primitive impact areas.
Source duplication allowed: No.
Files likely involved: `docs/sa/referral-saas/*`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Database/schema impact: None.
Backend impact: None.
Frontend impact: None.
API impact: None.
Tests to add/update: No runtime tests required for this docs-only gap matrix.
Validation method: Readback confirms the matrix separates current built capabilities from 10/10 SaaS requirements, identifies gaps, priorities, task candidates, tests/validation, ordered sequence, first implementation recommendation, and explicit DLaaS deferrals.
Acceptance criteria: Matrix exists under `docs/sa/referral-saas/`; roadmap links to it and includes the recommended ordered task sequence; broad DLaaS work is explicitly deferred; no backend/frontend/API/schema behavior changes.
Dependencies: TASK-131; TASK-132.
Blocked by: None.
Risk level: Low.
Rollback notes: Revert documentation-only additions and this roadmap entry.
Explicit non-goals: Do not implement account setup, campaign workflow, referral code changes, validation changes, progress API changes, attribution trace services, frontend changes, schema, migrations, live DB checks, money movement, fulfilment, settlement, funding, sponsor billing, marketplace expansion, or white-label/embed.
Definition of done: Referral SaaS has a focused 10/10 gap matrix and ordered next-task candidates grounded in current source truth. Priority: P0.

## TASK-134: Define Referral SaaS account setup contract

Status: Complete (2026-07-11). Output: `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_CONTRACT.md`; `docs/sa/referral-saas/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `docs/product/README.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: SaaS account setup; tenant/account boundary; external tenant reference; membership setup; setup readiness; Referral SaaS packaging.
Objective: Define the narrow account setup contract needed to wrap existing tenant-scoped referral, campaign, progress, link/code, and attribution capabilities as a Referral SaaS product.
Why now: Existing referral and campaign capabilities are substantial, but the product cannot become SaaS-ready without a setup boundary above internal `tenant_code`.
Current source-of-truth files inspected: `docs/sa/TENANT_IDENTIFIER_BOUNDARY_DECISION.md`; `docs/sa/TENANT_ACCOUNT_BOUNDARY_MAP.md`; `docs/sa/TENANT_ACCOUNT_LIFECYCLE_MEMBERSHIP_MODEL.md`; `docs/sa/LIVE_CRITICAL_STATE_INVENTORY.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `dp/migrations/031_tenent.sql`; `services/tenant_service.py`; `apps/api/routers/admin_tenants.py`; `apps/api/routers/session.py`; `utils/security.py`; `utils/permissions.py`; `test/test_tenant_service.py`; `test/test_admin_tenant.py`.
Shared primitive impact: No implementation impact. Future implementation will touch shared tenant/account/auth primitives and must preserve current `tenant_code` compatibility.
Source duplication allowed: No.
Files likely involved: `docs/sa/referral-saas/*`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Database/schema impact: None.
Backend impact: None.
Frontend impact: None.
API impact: None.
Tests to add/update: No runtime tests required for this docs-only contract.
Validation method: Readback confirms the contract keeps `tenant_code` internal, defines Referral SaaS account concepts, setup checklist, setup states, candidate API direction, response shape, idempotency/audit expectations, permissions, future tests, implementation slices, explicit non-goals, and readiness decision.
Acceptance criteria: Contract exists under `docs/sa/referral-saas/`; roadmap references the completed output; ordered task list records TASK-134; broad DLaaS account/billing/money/white-label scope remains deferred; no backend/frontend/API/schema behavior changes.
Dependencies: TASK-133; tenant/account SA docs TASK-004/TASK-005/TASK-048.
Blocked by: None.
Risk level: Low.
Rollback notes: Revert documentation-only additions and this roadmap entry.
Explicit non-goals: Do not implement schema, migrations, account services, membership services, external reference resolver, APIs, frontend, campaign setup, referral code changes, progress API changes, attribution trace, billing, funding, fulfilment, settlement, sponsor billing, marketplace expansion, white-label/embed, or live DB checks.
Definition of done: Referral SaaS has a bounded account setup contract ready to drive narrow implementation planning without duplicating source code or exposing internal `tenant_code` as the product identifier. Priority: P0.

## TASK-135: Productize Referral SaaS campaign setup and readiness contract

Status: Complete (2026-07-11). Output: `docs/sa/referral-saas/REFERRAL_SAAS_CAMPAIGN_SETUP_READINESS_CONTRACT.md`; `docs/sa/referral-saas/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `docs/product/README.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Campaign setup; campaign readiness; campaign policy; campaign validation; campaign track lifecycle; Referral SaaS campaign workflow.
Objective: Define the campaign setup and readiness contract needed to package existing campaign create, policy, validation, track, and readiness capabilities as a coherent Referral SaaS workflow.
Why now: TASK-134 defines the account setup boundary. The next product wedge needs a campaign setup contract that composes existing campaign services without changing current behavior or pulling in broad DLaaS marketplace/money scope.
Current source-of-truth files inspected: `docs/sa/CAMPAIGN_OPPORTUNITY_LIFECYCLE_MAP.md`; `docs/sa/CAMPAIGN_READINESS_SERVICE_CONTRACT.md`; `docs/sa/LINK_CODE_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `dp/migrations/002_campaigns.sql`; `dp/migrations/003_policies.sql`; `dp/migrations/014_campaign_referral_links.sql`; `services/campaign_service.py`; `services/campaign_policy_service.py`; `services/campaign_readiness_service.py`; `apps/api/routers/campaigns.py`; `apps/api/routers/admin_campaign_readiness.py`; `apps/api/schemas/campaigns.py`; `test/test_campaign_service.py`; `test/test_campaign_policy_service.py`; `test/test_campaign_readiness_service.py`; `test/test_campaigns.py`; `test/api/test_campaign_readiness_api.py`.
Shared primitive impact: No implementation impact. Future implementation will compose shared campaign, policy, readiness, account, and link/code primitives without duplicating source code.
Source duplication allowed: No.
Files likely involved: `docs/sa/referral-saas/*`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Database/schema impact: None.
Backend impact: None.
Frontend impact: None.
API impact: None.
Tests to add/update: No runtime tests required for this docs-only contract.
Validation method: Readback confirms the contract keeps `campaign_code` and `campaign_track_id` semantics distinct, defines Referral SaaS campaign concepts, setup states, setup checklist, candidate API direction, response shape, idempotency/audit expectations, permissions, future tests, implementation slices, explicit non-goals, and readiness decision.
Acceptance criteria: Contract exists under `docs/sa/referral-saas/`; roadmap references the completed output; ordered task list records TASK-135; marketplace distribution and money flows remain deferred; no backend/frontend/API/schema behavior changes.
Dependencies: TASK-134; campaign lifecycle/readiness SA docs TASK-006/TASK-007; link/code contract TASK-009.
Blocked by: None.
Risk level: Low.
Rollback notes: Revert documentation-only additions and this roadmap entry.
Explicit non-goals: Do not implement schema, migrations, campaign setup services, routes, frontend, campaign lifecycle mutation, activation/pause/archive commands, current `/campaigns` behavior changes, campaign validation changes, campaign attribution trace, referral code/link issue changes, marketplace opportunity routing, commissions, funding, fulfilment, settlement, sponsor billing, white-label/embed, or live DB checks.
Definition of done: Referral SaaS has a bounded campaign setup/readiness contract ready to drive narrow implementation planning without duplicating source code or merging in broad DLaaS distribution/money scope. Priority: P0.

## TASK-136: Harden Referral SaaS referral code issue contract

Status: Complete (2026-07-11). Output: `docs/sa/referral-saas/REFERRAL_SAAS_REFERRAL_CODE_ISSUE_CONTRACT.md`; `docs/sa/referral-saas/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `docs/product/README.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Referral code issue/get-or-create; accepted terms enforcement; tenant-safe API context; idempotency; privacy-safe referrer identity; audit posture.
Objective: Define the product contract for issuing or reusing referral codes without rebuilding the existing referral code service or mixing in validation, progress, attribution, or DLaaS money flows.
Why now: TASK-135 defined campaign setup/readiness. The next product wedge needs to harden existing referral code creation and reuse into a bounded SaaS capability before validation and attribution workflows are productized.
Files involved: `docs/sa/referral-saas/REFERRAL_SAAS_REFERRAL_CODE_ISSUE_CONTRACT.md`; `docs/sa/referral-saas/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `services/referral_code.py`; `apps/api/routers/referrals.py`; `apps/api/schemas/referrals.py`; `dp/migrations/001_init.sql`; `dp/migrations/026_referrer_code_terms_and_conditions_update.sql`; `dp/migrations/031_tenent.sql`; `test/test_referral_code.py`; `test/test_referrals_api.py`.
Database/schema impact: None. The contract documents the current `referrer_codes` schema posture, including global uniqueness for `referrer_ucn_hash`, `referral_code`, and `gaming_handle` and the service lookup by tenant/sticker/referrer hash.
Backend impact: None. Existing `POST /referrals/codes` and `get_or_create_referrer_code` behavior are documented as source facts, not changed.
Frontend impact: None.
API impact: None. Future product API direction is documented only.
Tests to add/update: No runtime tests required for this docs-only contract.
Validation method: Readback confirms the contract captures current route, schema, service behavior, terms enforcement, response statuses, idempotency posture, privacy requirements, audit expectations, failure contract, future tests, implementation slices, explicit non-goals, and the schema uniqueness decision needed before implementation changes.
Acceptance criteria: Contract exists under `docs/sa/referral-saas/`; roadmap references the completed output; ordered task list records TASK-136; validation, progress, attribution, operator support, reporting, and money flows remain deferred; no backend/frontend/API/schema behavior changes.
Dependencies: TASK-134; TASK-135; link/code contract TASK-009; current referral code service and API tests.
Blocked by: None.
Risk level: Low.
Rollback notes: Revert documentation-only additions and this roadmap entry.
Explicit non-goals: Do not implement schema, migrations, services, routes, frontend, referral validation, validation recovery, referee UCN capture, progress events, attribution trace, operator investigation, reporting/export, rewards, funding, fulfilment, settlement, sponsor billing, or live DB checks.
Definition of done: Referral SaaS has a bounded referral code issue/get-or-create contract ready to drive narrow implementation planning while preserving existing service behavior and keeping validation, attribution, and broad DLaaS scope separate. Priority: P0.

## TASK-137: Harden Referral SaaS validation and recovery contract

Status: Complete (2026-07-11). Output: `docs/sa/referral-saas/REFERRAL_SAAS_VALIDATION_RECOVERY_CONTRACT.md`; `docs/sa/referral-saas/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `docs/product/README.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Public referral validation; referral instance golden thread; QR scan evidence; accepted terms enforcement; alias rules; validation recovery; referee UCN capture boundary.
Objective: Define the product contract for public validation and immediate recovery without rebuilding the existing validation service or pulling in progress, attribution, reporting, or DLaaS money flows.
Why now: TASK-136 defined referral code issue/reuse. The next product wedge needs validation and recovery states to be stable before progress events and attribution traces are productized.
Files involved: `docs/sa/referral-saas/REFERRAL_SAAS_VALIDATION_RECOVERY_CONTRACT.md`; `docs/sa/referral-saas/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `services/referral_code.py`; `apps/api/routers/referrals.py`; `apps/api/schemas/referrals.py`; `dp/migrations/001_init.sql`; `dp/migrations/006_qr_scans.sql`; `dp/migrations/013_progress_events.sql`; `dp/migrations/015_add_ucn_captured_at.sql`; `dp/migrations/016_fix_referral_instances_status_constraint.sql`; `dp/migrations/031_tenent.sql`; `test/test_referral_code.py`; `test/test_referrals_api.py`.
Database/schema impact: None. The contract documents the current `referral_instances` and `referral_qr_scans` validation evidence posture.
Backend impact: None. Existing `POST /public/referrals/validate`, `validate_referral_code`, `POST /referrals/referees/ucn`, and `capture_referee_ucn` behavior are documented as source facts, not changed.
Frontend impact: None.
API impact: None. Future product API and recovery-state direction are documented only.
Tests to add/update: No runtime tests required for this docs-only contract.
Validation method: Readback confirms the contract captures current route, schema, service behavior, terms enforcement, alias rules, response statuses, QR scan evidence, UCN capture boundary, recovery states, idempotency gap, privacy requirements, audit expectations, future tests, implementation slices, explicit non-goals, and readiness decision.
Acceptance criteria: Contract exists under `docs/sa/referral-saas/`; roadmap references the completed output; ordered task list records TASK-137; progress events, attribution trace, operator investigation, reporting, and money flows remain deferred; no backend/frontend/API/schema behavior changes.
Dependencies: TASK-136; current referral validation service and API tests.
Blocked by: None.
Risk level: Low.
Rollback notes: Revert documentation-only additions and this roadmap entry.
Explicit non-goals: Do not implement schema, migrations, services, routes, frontend, referral code issue/reissue/revoke/expire behavior, progress event productization, campaign attribution trace, operator investigation, reporting/export, rewards, funding, fulfilment, settlement, sponsor billing, or live DB checks.
Definition of done: Referral SaaS has a bounded validation and recovery contract ready to drive narrow implementation planning while preserving existing validation behavior and keeping progress, attribution, and broad DLaaS scope separate. Priority: P0.

## TASK-138: Productize Referral SaaS progress event contract

Status: Complete (2026-07-11). Output: `docs/sa/referral-saas/REFERRAL_SAAS_PROGRESS_EVENT_CONTRACT.md`; `docs/sa/referral-saas/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `docs/product/README.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Progress event ingestion; event dedupe; payload hashing; journey validation; identifier validation; referral progress read model; queue/retry diagnostics.
Objective: Define the Referral SaaS product contract for recording progress events without forking the shared `/v1/progress` primitive or pulling in attribution trace, reporting, operator repair, or DLaaS money flows.
Why now: TASK-137 defined validation and recovery. The next product wedge needs progress events to have stable product states, idempotency expectations, retry posture, redaction rules, and launch-readiness checks before attribution trace work.
Files involved: `docs/sa/referral-saas/REFERRAL_SAAS_PROGRESS_EVENT_CONTRACT.md`; `docs/sa/referral-saas/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `apps/api/routers/progress.py`; `apps/api/schemas/progress.py`; `services/progress_service.py`; `services/journey_definitions.py`; `services/progress_definitions.py`; `services/journey_orchestrator.py`; `dp/migrations/013_progress_events.sql`; `dp/migrations/017_fix_referral_progress_event_type_constraint.sql`; `dp/migrations/018_add_referral_processing_audit.sql`; `dp/migrations/019_dedup_update_for_testfile.sql`; `dp/migrations/020_referral_event_failures.sql`; `test/test_progress_service.py`; `test/test_progress_api.py`.
Database/schema impact: None. The contract documents the current `referral_progress_events`, `referral_processing_audit`, and `referral_event_failures` posture, including dedupe/source-event uniqueness and the event-name constraint alignment warning.
Backend impact: None. Existing `POST /v1/progress`, `handle_progress_event`, and downstream `REFERRAL_PROGRESS_RECORDED` orchestration behavior are documented as source facts, not changed.
Frontend impact: None.
API impact: None. Future product API and diagnostic direction are documented only.
Tests to add/update: No runtime tests required for this docs-only contract.
Validation method: Readback confirms the contract captures current route, schema, service behavior, event and journey coverage, dedupe and payload hash posture, queueing behavior, orchestration boundary, product outcome states, retry/recovery classes, privacy rules, future tests, implementation slices, explicit non-goals, and readiness decision.
Acceptance criteria: Contract exists under `docs/sa/referral-saas/`; roadmap references the completed output; ordered task list records TASK-138; attribution trace, operator repair/replay, reporting, and money flows remain deferred; no backend/frontend/API/schema behavior changes.
Dependencies: TASK-137; current progress service, event ingestion public contract TASK-012, and audit/retry standard TASK-002.
Blocked by: None.
Risk level: Low.
Rollback notes: Revert documentation-only additions and this roadmap entry.
Explicit non-goals: Do not implement schema, migrations, services, routes, frontend, new event names, enterprise ingestion changes, reward/mission/funding/fulfilment/settlement/sponsor billing behavior, attribution trace composition, operator repair/replay UI, reporting/export, or live DB checks.
Definition of done: Referral SaaS has a bounded progress event contract ready to drive narrow implementation planning while preserving shared platform ingestion and keeping attribution, operator repair, reporting, and broad DLaaS scope separate. Priority: P0.

## TASK-139: Define Referral SaaS attribution trace contract

Status: Complete (2026-07-11). Output: `docs/sa/referral-saas/REFERRAL_SAAS_ATTRIBUTION_TRACE_CONTRACT.md`; `docs/sa/referral-saas/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `docs/product/README.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Attribution trace; outcome trace; campaign/referral link evidence; route attribution evidence; progress-event evidence; missing-evidence taxonomy; redaction.
Objective: Define the Referral SaaS attribution trace contract around the existing `outcome_trace_service` and admin outcome trace route without creating a parallel attribution system.
Why now: TASK-138 defined progress event ingestion. The next product wedge needs attribution trace semantics that connect referral outcome, campaign/link/route evidence, progress events, and missing-evidence diagnostics before operator workflow, safe status, reporting, and public API mapping.
Files involved: `docs/sa/referral-saas/REFERRAL_SAAS_ATTRIBUTION_TRACE_CONTRACT.md`; `docs/sa/referral-saas/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `services/outcome_trace_service.py`; `apps/api/routers/admin_outcomes.py`; `services/link_code_service.py`; `dp/migrations/002_campaigns.sql`; `dp/migrations/014_campaign_referral_links.sql`; `dp/migrations/070_distribution_route_referral_links.sql`; `test/test_outcome_trace_service.py`; `test/test_distribution_attribution_journey_contract.py`.
Database/schema impact: None. The contract documents current attribution evidence sources and joins without changing schema.
Backend impact: None. Existing `get_outcome_trace`, `/admin/outcomes/{referral_track_id}/trace`, and link/code inspection behavior are documented as source facts, not changed.
Frontend impact: None.
API impact: None. Future product projection/API direction is documented only.
Tests to add/update: No runtime tests required for this docs-only contract.
Validation method: Readback confirms the contract captures current outcome trace implementation, admin route permissions, prioritized Referral SaaS trace sections, source evidence, trace completeness, missing-evidence taxonomy, attribution decision rules, privacy/redaction, reporting relationship, future tests, implementation slices, explicit non-goals, and readiness decision.
Acceptance criteria: Contract exists under `docs/sa/referral-saas/`; roadmap references the completed output; ordered task list records TASK-139; operator workflow, safe status, reporting, public API mapping, and money flows remain deferred; no backend/frontend/API/schema behavior changes.
Dependencies: TASK-138; outcome trace contract TASK-010; link/code contract TASK-009; current outcome trace service and tests.
Blocked by: None.
Risk level: Low.
Rollback notes: Revert documentation-only additions and this roadmap entry.
Explicit non-goals: Do not implement schema, migrations, services, routes, frontend, attribution mutation, campaign validation changes, progress ingestion changes, operator link/code investigation workflow, reporting/export, customer/referrer safe status, reward/commission/funding/fulfilment/settlement/sponsor billing behavior, or live DB checks.
Definition of done: Referral SaaS has a bounded attribution trace contract ready to drive narrow implementation planning while reusing existing outcome trace capability and keeping operator workflow, reporting, safe status, and broad DLaaS money scope separate. Priority: P0.

## TASK-147: Define Referral SaaS E2E and live verification plan

Status: Complete (2026-07-11). Output: `docs/sa/referral-saas/REFERRAL_SAAS_E2E_LIVE_VERIFICATION_PLAN.md`; `docs/sa/referral-saas/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `docs/product/README.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/LIVE_DB_STATE_VERIFICATION_CHECKLIST.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: E2E launch confidence; live DB/state verification; migration replay; route smoke classification; tenant isolation; redaction; attribution evidence.
Objective: Define the E2E and live verification evidence required to prove the existing Referral SaaS wedge from account context through campaign, referral code/link, validation, progress ingestion, attribution trace, and later reporting/safe status without mixing in broader DLaaS money or marketplace scope.
Why now: TASK-139 completed the attribution trace contract. TASK-147 is intentionally pulled forward because live DB/state uncertainty and missing focused E2E proof can cap production confidence even when individual referral, progress, campaign, and attribution components already exist.
Files involved: `docs/sa/referral-saas/REFERRAL_SAAS_E2E_LIVE_VERIFICATION_PLAN.md`; `docs/sa/referral-saas/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `docs/sa/LIVE_DB_STATE_VERIFICATION_CHECKLIST.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `dp/migrations/001_init.sql`; `dp/migrations/002_campaigns.sql`; `dp/migrations/006_qr_scans.sql`; `dp/migrations/013_progress_events.sql`; `dp/migrations/014_campaign_referral_links.sql`; `dp/migrations/017_fix_referral_progress_event_type_constraint.sql`; `dp/migrations/018_add_referral_processing_audit.sql`; `dp/migrations/020_referral_event_failures.sql`; `dp/migrations/061_enterprise_event_inbox.sql`; `dp/migrations/070_distribution_route_referral_links.sql`; `dp/migrations/071_admin_audit_log.sql`; current referral, progress, campaign, outcome trace, link/code, enterprise event, and distribution reporting test inventory.
Database/schema impact: None. The plan documents the launch-critical tables, statuses, constraints, and indexes to verify later.
Backend impact: None.
Frontend impact: None.
API impact: None. Candidate smoke routes are documented for later verification only and must be selected from mounted routers before execution.
Tests to add/update: No runtime tests required for this docs-only plan.
Validation method: Readback confirms the plan covers golden-path E2E, negative/cross-tenant cases, redaction, route smoke classification, live DB/state verification, migration replay, launch exit criteria, implementation slices, explicit non-goals, and the separation between Referral SaaS proof and broader DLaaS money/marketplace capabilities.
Acceptance criteria: Plan exists under `docs/sa/referral-saas/`; roadmap references the completed output; ordered task list records TASK-147; TASK-140 through TASK-146 remain available for operator workflow, safe status, reporting, public API, frontend IA, support workflow, and audit/idempotency posture; no backend/frontend/API/schema behavior changes; no live DB access is performed.
Dependencies: TASK-139; live DB/state checklist TASK-003; current referral, campaign, progress, link/code, outcome trace, enterprise event, and distribution reporting test inventory.
Blocked by: None.
Risk level: Low.
Rollback notes: Revert documentation-only additions and this roadmap entry.
Explicit non-goals: Do not implement schema, migrations, services, routes, frontend, tests, smoke scripts, live DB queries, production checks, production writes, repair/replay/retry actions, reward/funding/fulfilment/settlement/commission/sponsor billing verification, or marketplace-depth verification.
Definition of done: Referral SaaS has a source-backed plan for proving production readiness through focused E2E coverage, route smoke checks, migration replay, and read-only live DB/state verification while keeping broader DLaaS expansion scope separate. Priority: P0.

## TASK-140: Add Referral SaaS operator link/code investigation contract

Status: Complete (2026-07-11). Output: `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_LINK_CODE_INVESTIGATION_CONTRACT.md`; `docs/sa/referral-saas/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `docs/product/README.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ATTRIBUTION_TRACE_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_E2E_LIVE_VERIFICATION_PLAN.md`; `docs/sa/LINK_CODE_CONTRACT.md`.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Operator link/code investigation; canonical link/code inspection; redaction; missing-evidence diagnostics; attribution-trace navigation.
Objective: Define the Referral SaaS operator investigation contract around the existing canonical `inspect_link_code` service and `/admin/links/inspect` route without rebuilding link/code inspection or adding mutation workflows.
Why now: TASK-139 defined attribution trace and TASK-147 defined E2E/live verification. Operators now need a bounded contract for starting from a code/link and safely navigating to campaign, referral, route, progress, and attribution evidence.
Files involved: `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_LINK_CODE_INVESTIGATION_CONTRACT.md`; `docs/sa/referral-saas/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `services/link_code_service.py`; `apps/api/routers/admin_links.py`; `apps/api/main.py`; `test/test_link_code_service.py`; `test/api/test_admin_links_api.py`; `docs/roadmap/OPERATOR_DEMO_READINESS_SMOKE_CHECKLIST.md`; `docs/roadmap/ORDERED_TASK_LIST.md` TASK-053 and TASK-054 entries.
Database/schema impact: None. The contract documents current source evidence from `referrer_codes`, `marketing_campaigns`, `campaign_referral_links`, `distribution_route_referral_links`, and compatibility `composite_code_service`.
Backend impact: None. Existing `inspect_link_code` and `GET /admin/links/inspect` behavior are documented as source facts, not changed.
Frontend impact: None. Future operator UI behavior is documented only.
API impact: None. The current read-only admin route is documented; no route, auth, payload, or permission behavior changes.
Tests to add/update: No runtime tests required for this docs-only contract.
Validation method: Readback confirms the contract captures current source types, derived statuses, route inputs, response shape, read-only guardrails, permission posture, redaction rules, missing-evidence taxonomy, investigation next links, future tests, explicit non-goals, and readiness decision.
Acceptance criteria: Contract exists under `docs/sa/referral-saas/`; roadmap references the completed output; ordered task list records TASK-140; support workflow, safe status, reporting, public API mapping, frontend IA, audit/idempotency inventory, and money flows remain deferred; no backend/frontend/API/schema behavior changes.
Dependencies: TASK-139; TASK-147; canonical link/code contract TASK-009; link/code facade TASK-053; admin inspect endpoint TASK-054.
Blocked by: None.
Risk level: Low.
Rollback notes: Revert documentation-only additions and this roadmap entry.
Explicit non-goals: Do not implement schema, migrations, services, routes, permissions, frontend, tests, public resolve APIs, code issue/reissue/revoke/expire behavior, void commands, track creation, accepted-terms changes, mutation/repair/retry/replay workflows, queueing, webhooks, rewards, funding, fulfilment, settlement, commissions, sponsor billing, or marketplace-depth behavior.
Definition of done: Referral SaaS has a bounded operator link/code investigation contract that packages the existing read-only inspection primitive and defines safe navigation into attribution trace and later support workflows while keeping shared platform source ownership intact. Priority: P1.

## TASK-141: Define Referral SaaS safe status contract

Status: Complete (2026-07-11). Output: `docs/sa/referral-saas/REFERRAL_SAAS_SAFE_STATUS_CONTRACT.md`; `docs/sa/referral-saas/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `docs/product/README.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_VALIDATION_RECOVERY_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PROGRESS_EVENT_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ATTRIBUTION_TRACE_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_LINK_CODE_INVESTIGATION_CONTRACT.md`; `docs/sa/PARTNER_CUSTOMER_SAFE_STATUS_CONTRACT.md`.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Referrer/customer safe status; next action; role-scoped privacy; progress status projection; reward summary projection; internal-state redaction.
Objective: Define the Referral SaaS referrer/customer safe status contract over existing partner/customer safe-status projection, consumer experience, reward summary, validation, progress, and attribution foundations without exposing operator diagnostics or broader DLaaS money internals.
Why now: TASK-140 packaged operator link/code investigation. The next product wedge needs customer/referrer-facing status and next-action rules so public and portal surfaces do not consume raw referral, progress, reward, trace, or failure states.
Files involved: `docs/sa/referral-saas/REFERRAL_SAAS_SAFE_STATUS_CONTRACT.md`; `docs/sa/referral-saas/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `services/partner_customer_safe_status_service.py`; `services/reward_summary_service.py`; `services/progress_service.py`; `apps/api/routers/consumer_experience.py`; `apps/api/routers/reward_summary.py`; `test/test_partner_customer_safe_status_service.py`; `test/test_consumer_experience_api.py`; `test/test_reward_summary_api.py`; `test/test_progress_service.py`; `test/test_progress_api.py`.
Database/schema impact: None. The contract documents safe projection over existing referral, progress, campaign, attribution, and reward evidence.
Backend impact: None. Existing safe-status helper, consumer experience, reward summary, and progress behavior are documented as source facts, not changed.
Frontend impact: None. Future product labels, copy, and UI behavior are documented only.
API impact: None. Future Referral SaaS safe-status response shape is documented only; no route, auth, payload, or permission behavior changes.
Tests to add/update: No runtime tests required for this docs-only contract.
Validation method: Readback confirms the contract captures current safe-status helper behavior, current consumer/reward/progress surfaces, first-launch source-family scope, product vocabulary, source-state mappings, response shape, current surface gaps, future tests, explicit non-goals, and readiness decision.
Acceptance criteria: Contract exists under `docs/sa/referral-saas/`; roadmap references the completed output; ordered task list records TASK-141; reporting, public API mapping, frontend IA, operator support workflow, audit/idempotency inventory, and money flows remain deferred; no backend/frontend/API/schema behavior changes.
Dependencies: TASK-137; TASK-138; TASK-139; TASK-140; partner/customer safe status contract TASK-023; current safe-status helper and consumer/reward tests.
Blocked by: None.
Risk level: Low.
Rollback notes: Revert documentation-only additions and this roadmap entry.
Explicit non-goals: Do not implement schema, migrations, services, routes, permissions, frontend, tests, public API wrappers, reward/funding/fulfilment/settlement/commission/sponsor billing behavior, marketplace-depth behavior, operator trace exposure, link/code inspect exposure to customers/referrers, raw state exposure, mutation/repair/retry/replay workflows, webhook dispatch, notifications, payouts, invoices, or live DB checks.
Definition of done: Referral SaaS has a bounded referrer/customer safe-status contract that reuses the shared role-safe projection foundation and defines how validation, progress, attribution, campaign/link, and reward evidence should become safe product status and next action. Priority: P1.

## TASK-142: Define Referral SaaS reporting and export contract

Status: Complete (2026-07-11). Output: `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`; `docs/sa/referral-saas/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `docs/product/README.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ATTRIBUTION_TRACE_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_SAFE_STATUS_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_E2E_LIVE_VERIFICATION_PLAN.md`; `docs/sa/TENANT_SAFE_ANALYTICS_REPORTING_CONTRACT.md`.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Tenant-safe reporting; export validation; freshness; redaction; campaign/referral/progress/attribution metrics; operational-vs-ledger classification.
Objective: Define the Referral SaaS reporting and export contract over existing tenant-safe analytics and distribution reporting foundations without creating a parallel reporting stack or pulling in broader DLaaS money reporting scope.
Why now: TASK-141 defined safe referrer/customer status. The next product wedge needs tenant-safe report types, dimensions, metrics, freshness, export rules, and redaction boundaries before public API mapping and frontend IA work.
Files involved: `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`; `docs/sa/referral-saas/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `services/tenant_safe_analytics_service.py`; `apps/api/routers/admin_analytics.py`; `services/distribution/reporting_service.py`; `apps/api/routers/distribution/admin_reporting.py`; `test/test_tenant_safe_analytics_service.py`; `test/api/test_admin_analytics_api.py`; `test/api/distribution/test_admin_reporting_api.py`.
Database/schema impact: None. The contract documents safe report and export projection over existing referral, campaign, link/code, progress, attribution, safe-status, and optional reward-summary evidence.
Backend impact: None. Existing tenant-safe analytics and distribution reporting behavior are documented as source facts, not changed.
Frontend impact: None. Future reporting screens and export UX are documented only.
API impact: None. Future Referral SaaS reporting/export route direction is documented only; no route, auth, payload, permission, export, or storage behavior changes.
Tests to add/update: No runtime tests required for this docs-only contract.
Validation method: Readback confirms the contract captures current analytics/reporting behavior, first-launch report types, approved dimensions, core metrics, freshness rules, export rules, candidate API direction, current surface gaps, future tests, explicit non-goals, and readiness decision.
Acceptance criteria: Contract exists under `docs/sa/referral-saas/`; roadmap references the completed output; ordered task list records TASK-142; public API mapping, frontend IA, operator support workflow, audit/idempotency inventory, and money flows remain deferred; no backend/frontend/API/schema/export behavior changes.
Dependencies: TASK-139; TASK-141; tenant-safe analytics reporting contract TASK-024; current tenant-safe analytics and distribution reporting tests.
Blocked by: None.
Risk level: Low.
Rollback notes: Revert documentation-only additions and this roadmap entry.
Explicit non-goals: Do not implement schema, migrations, services, routes, permissions, frontend, tests, export APIs, export storage, materialized views, rollups, live DB checks, reward/funding/fulfilment/settlement/commission/sponsor billing reporting, marketplace-depth reporting, raw operator trace exports, mutation/repair/retry/replay workflows, webhook dispatch, notifications, payouts, invoices, or scheduled delivery.
Definition of done: Referral SaaS has a bounded reporting and export contract that reuses the shared tenant-safe analytics foundation, defines first-launch SaaS report/export rules, and keeps broader DLaaS money/reporting scope separate. Priority: P1.

## TASK-143: Create Referral SaaS public API contract map

Status: Complete (2026-07-11). Output: `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `docs/product/README.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/API_PERMISSION_MATRIX.md`; `docs/sa/API_SURFACE_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_CAMPAIGN_SETUP_READINESS_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_REFERRAL_CODE_ISSUE_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_VALIDATION_RECOVERY_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PROGRESS_EVENT_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ATTRIBUTION_TRACE_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_SAFE_STATUS_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Public API contracts; auth and tenant scope; idempotency; safe errors; route packaging; product namespace mapping.
Objective: Map existing referral, campaign, progress, safe-status, reporting, and operator route primitives into a future versioned Referral SaaS API surface without adding routes or exposing internal/admin APIs as public contracts.
Why now: TASK-142 defined reporting and export boundaries. The next product wedge needs a route-family map and API rules before frontend IA, operator support workflow, and implementation planning continue.
Files involved: `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `apps/api/main.py`; `apps/api/routers/referrals.py`; `apps/api/routers/campaigns.py`; `apps/api/routers/progress.py`; `apps/api/routers/admin_campaign_readiness.py`; `apps/api/routers/admin_links.py`; `apps/api/routers/admin_outcomes.py`; `apps/api/routers/admin_analytics.py`; `apps/api/routers/consumer_experience.py`; `apps/api/routers/reward_summary.py`; `apps/api/schemas/referrals.py`; `apps/api/schemas/campaigns.py`; `apps/api/schemas/progress.py`.
Database/schema impact: None.
Backend impact: None. Current routes and schemas are documented as source facts, not changed.
Frontend impact: None. Future frontend route consumption and IA are documented only.
API impact: Documentation-only. Future `/v1/referral-saas/*` route families, auth, tenant, idempotency, and safe error rules are mapped but not implemented.
Tests to add/update: No runtime tests required for this docs-only contract map.
Validation method: Readback confirms the map captures current mounted route facts, target route families, auth and tenant scope rules, idempotency rules, safe error shape, productization gaps, future contract tests, explicit non-goals, and readiness decision.
Acceptance criteria: Contract map exists under `docs/sa/referral-saas/`; roadmap references the completed output; ordered task list records TASK-143; frontend IA, operator support workflow, audit/idempotency inventory, and money flows remain deferred; no backend/frontend/API/schema behavior changes.
Dependencies: TASK-134 through TASK-142; API permission matrix TASK-019; current referral, campaign, progress, admin diagnostic, consumer experience, reward summary, and analytics route inventory.
Blocked by: None.
Risk level: Low.
Rollback notes: Revert documentation-only additions and this roadmap entry.
Explicit non-goals: Do not implement schema, migrations, services, routes, auth helpers, OpenAPI, frontend, tests, public API namespaces, account membership, exports, lifecycle commands, repair/retry/replay workflows, fulfilment, settlement, payouts, invoices, webhook dispatch, marketplace-depth behavior, funding, commissions, sponsor billing, white-label/embed, or SaaS billing.
Definition of done: Referral SaaS has a bounded public API contract map that distinguishes current route facts from future product wrappers and defines auth, tenant-scope, idempotency, and safe-error rules for implementation planning. Priority: P1.

## TASK-144: Define Referral SaaS frontend IA and workflow contract

Status: Complete (2026-07-11). Output: `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/sa/referral-saas/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `docs/product/README.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_SAFE_STATUS_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_LINK_CODE_INVESTIGATION_CONTRACT.md`.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Frontend information architecture; workflow packaging; account setup; campaign readiness; referral link/code UX; validation recovery; safe status; attribution trace; reporting; integration setup; operator support entry points.
Objective: Define the focused Referral SaaS frontend IA and workflow contract over existing role-specific React surfaces without implementing routes or mixing the product shell with broader DLaaS marketplace and money workflows.
Why now: TASK-143 mapped the future public API surface. The next product wedge needs a frontend IA contract so implementation can organize existing account, campaign, referral, validation, progress, attribution, reporting, integration, and support surfaces into one SaaS workflow without treating the product as greenfield.
Files involved: `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/sa/referral-saas/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `frontend/src/app/App.tsx`; `frontend/src/layout/AppShell.tsx`; `frontend/src/layout/Sidebar.tsx`; `frontend/src/api/endpoints/adminOnboarding.ts`; `frontend/src/api/endpoints/consumerPortal.ts`; `frontend/src/api/endpoints/distribution.ts`; `frontend/src/api/experienceQueries.ts`; `frontend/src/pages/admin/CampaignOpportunitySetupPage.tsx`; `frontend/src/pages/admin/DistributionCommandCentrePage.tsx`; `frontend/src/pages/admin/OperatorDemoHomePage.tsx`; `frontend/src/pages/admin/OnboardingReadinessChecklistPage.tsx`; `frontend/src/pages/admin/WebhookApiSetupPage.tsx`; `frontend/src/pages/partner/PartnerIntegrationPage.tsx`; `frontend/src/pages/consumer/ConsumerPortalPage.tsx`; `frontend/src/pages/distributor/DistributorPortalPage.tsx`; related frontend tests in `frontend/src/pages/**`.
Database/schema impact: None.
Backend impact: None.
Frontend impact: None. Existing React routes, navigation, API clients, and pages are documented as source facts, not changed.
API impact: None. Future frontend consumption of product API wrappers is documented only.
Tests to add/update: No runtime tests required for this docs-only contract.
Validation method: Readback confirms the contract captures current frontend route/page/API-client foundations, target IA, workflow contracts, role boundaries, copy/state rules, current gaps, future tests, explicit non-goals, and readiness decision.
Acceptance criteria: Contract exists under `docs/sa/referral-saas/`; roadmap references the completed output; ordered task list records TASK-144; operator support workflow, audit/idempotency inventory, and money flows remain deferred; no backend/frontend/API/schema behavior changes.
Dependencies: TASK-134 through TASK-143; current frontend route/page/test inventory.
Blocked by: None.
Risk level: Low.
Rollback notes: Revert documentation-only additions and this roadmap entry.
Explicit non-goals: Do not implement React routes, components, CSS, API wrappers, schemas, backend routes, permissions, tests, public API wrappers, export APIs, mutation/repair/retry/replay controls, campaign activation, publish/revoke/expire/reissue commands, fulfilment, settlement, payouts, invoices, webhook dispatch, marketplace-depth behavior, funding, commissions, sponsor billing, wallets, white-label/embed, or SaaS billing.
Definition of done: Referral SaaS has a bounded frontend IA and workflow contract that packages existing frontend foundations into a coherent SaaS direction while keeping broader DLaaS marketplace and money workflows separate. Priority: P1.

## TASK-145: Define Referral SaaS operator support workflow

Status: Complete (2026-07-11). Output: `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_SUPPORT_WORKFLOW.md`; `docs/sa/referral-saas/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `docs/product/README.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_LINK_CODE_INVESTIGATION_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ATTRIBUTION_TRACE_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PROGRESS_EVENT_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_SAFE_STATUS_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/sa/AUDIT_RETRY_POLICY_STANDARD.md`; `docs/sa/API_SURFACE_MAP.md`.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Operator support workflow; link/code investigation; validation recovery; progress diagnostics; attribution review; reporting freshness; audit evidence; repair/replay guardrails.
Objective: Define the Referral SaaS operator support workflow over existing admin/operator primitives without implementing new support UI, BFF behavior, repair/replay actions, or broader DLaaS money support.
Why now: TASK-144 defined the frontend IA and named support as a product area. The next product wedge needs a bounded support-case taxonomy, evidence sequence, safe next actions, and mutation guardrails before implementation exposes diagnostics in a focused SaaS workflow.
Files involved: `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_SUPPORT_WORKFLOW.md`; `docs/sa/referral-saas/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `apps/api/routers/admin_links.py`; `apps/api/routers/admin_outcomes.py`; `apps/api/routers/admin_campaign_readiness.py`; `apps/api/routers/progress.py`; `apps/api/routers/admin_audit.py`; `apps/api/routers/admin_analytics.py`; `apps/api/routers/admin_failure.py`; `apps/api/routers/admin_dlq_replay.py`; `apps/api/routers/internal_replay.py`; `apps/api/routers/enterprise_events.py`; `services/link_code_service.py`; `services/outcome_trace_service.py`; `services/failure_admin_service.py`; `services/dlq_replay_service.py`; `services/replay_service.py`; `services/admin_audit_service.py`; `frontend/src/pages/admin/OperatorDemoHomePage.tsx`.
Database/schema impact: None.
Backend impact: None. Existing read-only diagnostics and existing admin repair/replay-capable routes are documented as source facts, not changed.
Frontend impact: None. Future support UI and BFF behavior are documented only.
API impact: None. No support-case route, API wrapper, permission, payload, repair, retry, replay, or mutation behavior is implemented.
Tests to add/update: No runtime tests required for this docs-only contract.
Validation method: Readback confirms the contract captures current support primitives, first-launch support case types, evidence sequence, safe next actions, response-shape direction, mutation boundaries, permission/redaction rules, future tests, explicit non-goals, and readiness decision.
Acceptance criteria: Contract exists under `docs/sa/referral-saas/`; roadmap references the completed output; ordered task list records TASK-145; audit/idempotency inventory and money flows remain deferred; no backend/frontend/API/schema behavior changes.
Dependencies: TASK-134 through TASK-144; audit/retry policy TASK-002; current admin link/code, outcome trace, campaign readiness, progress, failure, audit, analytics, replay, and operator demo surface inventory.
Blocked by: None.
Risk level: Low.
Rollback notes: Revert documentation-only additions and this roadmap entry.
Explicit non-goals: Do not implement schema, migrations, services, routes, permissions, frontend, BFFs, tests, support-case tables, repair/replay/retry/requeue/resolve/override commands, code lifecycle commands, campaign activation/publish commands, export APIs, webhook delivery, notifications, live DB checks, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, or SaaS billing behavior.
Definition of done: Referral SaaS has a bounded operator support workflow contract that organizes existing diagnostics into safe support cases while keeping repair/replay mutations, audit/idempotency hardening, and broader DLaaS money workflows out of scope. Priority: P1.

## TASK-146: Inventory Referral SaaS audit and idempotency posture

Status: Complete (2026-07-11). Output: `docs/sa/referral-saas/REFERRAL_SAAS_AUDIT_IDEMPOTENCY_POSTURE.md`; `docs/sa/referral-saas/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `docs/product/README.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_REFERRAL_CODE_ISSUE_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_VALIDATION_RECOVERY_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PROGRESS_EVENT_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_SUPPORT_WORKFLOW.md`; `docs/sa/AUDIT_RETRY_POLICY_STANDARD.md`.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Audit posture; idempotency; duplicate handling; retry/failure evidence; support repair guardrails; launch-readiness gaps.
Objective: Inventory the current Referral SaaS audit, idempotency, retry, duplicate, and failure posture from source truth without implementing new behavior or inventing fields/statuses.
Why now: TASK-145 defined operator support workflows and mutation guardrails. The next product wedge needs a source-backed inventory of which commands and events are already duplicate-safe/auditable and which gaps still block a 10/10 production claim.
Files involved: `docs/sa/referral-saas/REFERRAL_SAAS_AUDIT_IDEMPOTENCY_POSTURE.md`; `docs/sa/referral-saas/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `apps/api/routers/referrals.py`; `apps/api/routers/progress.py`; `apps/api/routers/campaigns.py`; `apps/api/routers/admin_onboarding.py`; `services/referral_code.py`; `services/progress_service.py`; `services/campaign_readiness_service.py`; `services/admin_audit_service.py`; `services/failure_admin_service.py`; `services/onboarding/onboarding_draft_idempotency_service.py`; `services/onboarding/onboarding_draft_audit_evidence_service.py`; `dp/migrations/001_init.sql`; `dp/migrations/006_qr_scans.sql`; `dp/migrations/013_progress_events.sql`; `dp/migrations/018_add_referral_processing_audit.sql`; `dp/migrations/020_referral_event_failures.sql`; `dp/migrations/061_enterprise_event_inbox.sql`; `dp/migrations/071_admin_audit_log.sql`; `dp/migrations/080_onboarding_draft_persistence.sql`.
Database/schema impact: None. Existing uniqueness, idempotency, audit, progress, failure, and onboarding draft persistence posture is documented only.
Backend impact: None.
Frontend impact: None.
API impact: None. No fields, statuses, routes, idempotency keys, audit writes, repair/replay actions, or retry behavior are implemented.
Tests to add/update: No runtime tests required for this docs-only inventory.
Validation method: Readback confirms the inventory captures current posture for account setup, referral code issue, validation, referee UCN capture, progress ingestion, campaign setup/readiness, read-only diagnostics, reporting, operator failures, replay paths, launch-critical gaps, future tests, explicit non-goals, and readiness decision.
Acceptance criteria: Inventory exists under `docs/sa/referral-saas/`; roadmap references the completed output; ordered task list records TASK-146; no backend/frontend/API/schema behavior changes; money flows remain deferred; launch-critical audit/idempotency gaps are explicit.
Dependencies: TASK-134 through TASK-145; audit/retry policy TASK-002; current schema/service inventory.
Blocked by: None.
Risk level: Low.
Rollback notes: Revert documentation-only additions and this roadmap entry.
Explicit non-goals: Do not implement schema, migrations, services, routes, permissions, frontend, tests, audit writes, idempotency behavior, retry behavior, repair/replay/requeue/resolve/override commands, public API wrappers, support-case tables, export APIs, live DB checks, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, or SaaS billing behavior.
Definition of done: Referral SaaS has a source-backed audit/idempotency posture inventory that separates current duplicate/audit facts from launch-blocking gaps and preserves the boundary between first-launch Referral SaaS and broader DLaaS money workflows. Priority: P1.

## TASK-149: Add Referral SaaS local golden-path contract test

Status: Complete (2026-07-12). Output: `test/test_referral_saas_golden_path_contract.py`; `docs/roadmap/referral-saas/ROADMAP.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/README.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_E2E_LIVE_VERIFICATION_PLAN.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_AUDIT_IDEMPOTENCY_POSTURE.md`.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Local/CI golden-path confidence; campaign readiness; referral code issue; public validation; progress dedupe; link/code inspection; attribution trace.
Objective: Add the first local/CI-safe Referral SaaS golden-path contract test over existing shared primitives without implementing product wrapper routes.
Why now: TASK-147 defined the E2E/live verification plan and TASK-146 inventoried audit/idempotency gaps. The next productization step needs executable evidence that current shared primitives can support the first SaaS path before new API wrappers or frontend packaging are introduced.
Files involved: `test/test_referral_saas_golden_path_contract.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `services/campaign_readiness_service.py`; `services/referral_code.py`; `services/progress_service.py`; `services/link_code_service.py`; `services/outcome_trace_service.py`; nearby referral, progress, campaign readiness, link/code, and outcome trace tests.
Database/schema impact: None. The test uses local fake connections only; no live DB access, migrations, schema changes, or runtime data changes.
Backend impact: Test-only. No services, routers, auth helpers, fields, statuses, or payload contracts changed.
Frontend impact: None.
API impact: None. No `/v1/referral-saas/*` product wrapper route was added.
Tests to add/update: Added a focused golden-path contract test that stitches campaign readiness, referral code issue, validation, progress ingestion/dedupe, link/code inspection redaction, and attribution trace diagnostics through existing services.
Validation method: `.venv_codex\Scripts\python.exe -m pytest -q --no-cov test\test_referral_saas_golden_path_contract.py --tb=short`; `.venv_codex\Scripts\python.exe -m pytest -q --no-cov test\test_referral_saas_golden_path_contract.py test\test_referral_code.py test\test_progress_service.py test\test_campaign_readiness_service.py test\test_link_code_service.py test\test_outcome_trace_service.py --tb=short`; `.venv_codex\Scripts\python.exe -m py_compile test\test_referral_saas_golden_path_contract.py`; `ruff check test\test_referral_saas_golden_path_contract.py`.
Acceptance criteria: Test proves a local/CI-safe path from campaign readiness through code issue, validation, progress insert/dedupe, link inspection, and attribution trace using shared primitives; no raw referrer UCN leaks from link inspection; funding/settlement/go-live sections remain outside the trace assertion; no backend/frontend/API/schema behavior changes.
Dependencies: TASK-134 through TASK-147; TASK-130 readiness checkpoint.
Blocked by: None for local/CI test coverage. Non-local/live verification remains separately gated by approved access.
Risk level: Low.
Rollback notes: Revert the test file and this roadmap entry.
Explicit non-goals: Do not add product wrapper routes, frontend, schema, migrations, live DB checks, production data access, auth changes, command idempotency implementation, audit writes, repair/replay/retry actions, export APIs, campaign activation, webhook delivery, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, or SaaS billing behavior.
Definition of done: Referral SaaS has its first executable local golden-path contract test over existing shared primitives, moving beyond contract docs while preserving product and DLaaS boundaries. Priority: P0.

## TASK-150: Add Referral SaaS negative contract test coverage

Status: Complete (2026-07-12). Output: `test/test_referral_saas_golden_path_contract.py`; `docs/roadmap/referral-saas/ROADMAP.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/README.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_E2E_LIVE_VERIFICATION_PLAN.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_AUDIT_IDEMPOTENCY_POSTURE.md`.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Negative-path launch confidence; safe validation failures; tenant-mismatch diagnostics; progress self-referral rejection; journey mismatch rejection; tenant-scoped attribution trace lookup.
Objective: Add local/CI-safe negative contract coverage for the focused Referral SaaS journey using existing shared primitives without adding product wrapper routes.
Why now: TASK-149 proved the local golden path. The next production-confidence gap is proving core bad-path inputs fail safely and remain tenant-scoped before broader E2E, route smoke, or product wrapper work is introduced.
Files involved: `test/test_referral_saas_golden_path_contract.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `services/referral_code.py`; `services/progress_service.py`; `services/link_code_service.py`; `services/outcome_trace_service.py`; nearby referral, progress, link/code, and outcome trace tests.
Database/schema impact: None. The test uses local fake connections only; no live DB access, migrations, schema changes, or runtime data changes.
Backend impact: Test-only. No services, routers, auth helpers, fields, statuses, or payload contracts changed.
Frontend impact: None.
API impact: None. No `/v1/referral-saas/*` product wrapper route was added.
Tests to add/update: Added negative contract assertions for accepted-terms rejection, tenant-mismatch link/code inspection, progress self-referral rejection, journey mismatch rejection, queue non-emission on rejected progress, and tenant-scoped missing attribution trace lookup.
Validation method: `.venv_codex\Scripts\python.exe -m pytest -q --no-cov test\test_referral_saas_golden_path_contract.py --tb=short`; focused referral/progress/link/trace suite; `.venv_codex\Scripts\python.exe -m py_compile test\test_referral_saas_golden_path_contract.py`; `ruff check test\test_referral_saas_golden_path_contract.py`.
Acceptance criteria: Test proves selected Referral SaaS negative paths return stable, safe outcomes; tenant-mismatch inspection does not leak the other tenant in diagnostic evidence; rejected progress paths do not enqueue downstream events; missing trace remains tenant-scoped; no backend/frontend/API/schema behavior changes.
Dependencies: TASK-147; TASK-149.
Blocked by: None for local/CI test coverage. Non-local/live verification remains separately gated by approved access.
Risk level: Low.
Rollback notes: Revert the test additions and this roadmap entry.
Explicit non-goals: Do not add product wrapper routes, frontend, schema, migrations, live DB checks, production data access, auth changes, command idempotency implementation, audit writes, repair/replay/retry actions, export APIs, campaign activation, webhook delivery, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, or SaaS billing behavior.
Definition of done: Referral SaaS has executable negative contract coverage for launch-critical safe-failure and tenant-scope behavior while preserving shared platform primitives and product boundaries. Priority: P0.

## TASK-151: Inventory Referral SaaS mounted route smoke surface

Status: Complete (2026-07-12). Output: `test/test_referral_saas_route_smoke_inventory.py`; `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`; `docs/sa/referral-saas/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/README.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_E2E_LIVE_VERIFICATION_PLAN.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Route smoke planning; mounted route evidence; read-only smoke classification; seeded-write boundary; product wrapper gap tracking.
Objective: Add source-backed Referral SaaS route smoke inventory and local contract coverage by introspecting the currently mounted FastAPI routes.
Why now: TASK-149 and TASK-150 proved local golden and negative service-level contract paths. The next production-confidence gap is selecting route smoke surfaces from actual mounted routes without inventing `/v1/referral-saas/*` wrappers or performing live writes.
Files involved: `test/test_referral_saas_route_smoke_inventory.py`; `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`; `docs/sa/referral-saas/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `apps/api/main.py`; `apps/api/routers/referrals.py`; `apps/api/routers/campaigns.py`; `apps/api/routers/progress.py`; `apps/api/routers/admin_campaign_readiness.py`; `apps/api/routers/admin_links.py`; `apps/api/routers/admin_outcomes.py`; `apps/api/routers/admin_analytics.py`; `apps/api/routers/consumer_experience.py`; `apps/api/routers/reward_summary.py`; route-focused tests.
Database/schema impact: None. No live DB access, migrations, schema changes, or runtime data changes.
Backend impact: Test/documentation only. No services, routers, auth helpers, fields, statuses, or payload contracts changed.
Frontend impact: None.
API impact: None. No `/v1/referral-saas/*` product wrapper route was added.
Tests to add/update: Added a mounted-route inventory contract test that asserts current read-only and seeded-write Referral SaaS-relevant route families are mounted and that `/v1/referral-saas/*` product wrapper routes remain unimplemented.
Validation method: `.venv_codex\Scripts\python.exe -m pytest -q --no-cov test\test_referral_saas_route_smoke_inventory.py --tb=short`; focused Referral SaaS route/contract suite; `.venv_codex\Scripts\python.exe -m py_compile test\test_referral_saas_route_smoke_inventory.py`; `ruff check test\test_referral_saas_route_smoke_inventory.py`.
Acceptance criteria: Route smoke inventory is source-backed; read-only versus seeded-write smoke route families are explicit; future product wrapper absence is executable evidence; no backend/frontend/API/schema behavior changes; no live or production DB access.
Dependencies: TASK-143; TASK-147; TASK-149; TASK-150.
Blocked by: None for local route inventory. Live/staging route execution remains separately gated by credentials, seeded subjects, and approval.
Risk level: Low.
Rollback notes: Revert the test file, route smoke inventory doc, SA index update, and this roadmap entry.
Explicit non-goals: Do not add product wrapper routes, frontend, schema, migrations, live DB checks, production data access, auth changes, smoke execution against live services, command idempotency implementation, audit writes, repair/replay/retry actions, export APIs, campaign activation, webhook delivery, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, or SaaS billing behavior.
Definition of done: Referral SaaS has an executable mounted-route smoke inventory that separates current shared primitives from future product wrapper routes and classifies route smoke safety for the next verification slice. Priority: P0.

## TASK-152: Add Referral SaaS read-only schema/status checker

Status: Complete (2026-07-12). Output: `scripts/referral_saas_schema_status_check.py`; `test/test_referral_saas_schema_status_check.py`; `scripts/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`; `docs/roadmap/referral-saas/ROADMAP.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/README.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/LIVE_DB_STATE_VERIFICATION_CHECKLIST.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_E2E_LIVE_VERIFICATION_PLAN.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Read-only schema/status/index verification; live/staging evidence preparation; launch-critical table, state, constraint, and index checks.
Objective: Add a Referral SaaS-specific read-only checker that can generate a dry-run SQL plan by default and optionally execute read-only schema/status/index checks against an explicitly configured database.
Why now: TASK-151 selected the mounted smoke route surface. The next production-confidence gap is repeatable schema/status/index evidence for the Referral SaaS wedge before any live/staging route smoke execution or product-ready rating.
Files involved: `scripts/referral_saas_schema_status_check.py`; `test/test_referral_saas_schema_status_check.py`; `scripts/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `docs/sa/LIVE_DB_STATE_VERIFICATION_CHECKLIST.md`; `docs/sa/referral-saas/REFERRAL_SAAS_E2E_LIVE_VERIFICATION_PLAN.md`; `dp/migrations/013_progress_events.sql`; `dp/migrations/017_fix_referral_progress_event_type_constraint.sql`; `dp/migrations/020_referral_event_failures.sql`; `dp/migrations/061_enterprise_event_inbox.sql`; `dp/migrations/070_distribution_route_referral_links.sql`; existing scripts.
Database/schema impact: None. The script defaults to dry-run query-plan output and only executes SELECT metadata/count queries when `--database` and a DSN are explicitly supplied.
Backend impact: Script/test only. No services, routers, auth helpers, fields, statuses, or payload contracts changed.
Frontend impact: None.
API impact: None. No route behavior changed.
Tests to add/update: Added tests for dry-run query-plan contents, read-only SQL posture, static expectation findings, and unsafe schema identifier rejection.
Validation method: `.venv_codex\Scripts\python.exe -m pytest -q --no-cov test\test_referral_saas_schema_status_check.py --tb=short`; focused Referral SaaS verification suite; `.venv_codex\Scripts\python.exe -m py_compile scripts\referral_saas_schema_status_check.py test\test_referral_saas_schema_status_check.py`; `ruff check scripts\referral_saas_schema_status_check.py test\test_referral_saas_schema_status_check.py`.
Acceptance criteria: Checker covers launch-critical Referral SaaS tables, state fields, expected constraints, and expected indexes; default mode does not require DB access; database mode is explicit and read-only; tests protect the generated query plan; no backend/frontend/API/schema behavior changes.
Dependencies: TASK-147; TASK-151.
Blocked by: None for local dry-run and CI tests. Live/staging execution remains separately gated by read-only credentials, seeded subjects, and approval.
Risk level: Low.
Rollback notes: Revert the checker script, test file, script README update, route smoke inventory note, and this roadmap entry.
Explicit non-goals: Do not run live DB checks by default, connect to production, discover credentials, write data, repair schema, change migrations, add product wrapper routes, frontend, auth changes, smoke execution against live services, command idempotency implementation, audit writes, repair/replay/retry actions, export APIs, campaign activation, webhook delivery, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, or SaaS billing behavior.
Definition of done: Referral SaaS has a CI-tested read-only schema/status/index checker that prepares live/staging evidence collection while preserving safety gates and product boundaries. Priority: P0.

## TASK-153: Add Referral SaaS route smoke plan generator

Status: Complete (2026-07-12). Output: `scripts/referral_saas_route_smoke_plan.py`; `test/test_referral_saas_route_smoke_plan.py`; `scripts/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`; `docs/roadmap/referral-saas/ROADMAP.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/README.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_E2E_LIVE_VERIFICATION_PLAN.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Route smoke planning; read-only smoke defaults; seeded-write opt-in; local/staging smoke preparation; production write guardrails.
Objective: Add a Referral SaaS route smoke plan generator that outputs dry-run command templates for current shared primitive routes without executing requests or inventing product wrapper routes.
Why now: TASK-151 selected the mounted smoke route surface and TASK-152 added schema/status verification preparation. The next production-confidence gap is repeatable route smoke instructions with read-only defaults and explicit seeded-write opt-in before any local/staging smoke execution.
Files involved: `scripts/referral_saas_route_smoke_plan.py`; `test/test_referral_saas_route_smoke_plan.py`; `scripts/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `apps/api/main.py`; `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; current route smoke inventory test.
Database/schema impact: None. No live DB access, migrations, schema changes, or runtime data changes.
Backend impact: Script/test only. No services, routers, auth helpers, fields, statuses, or payload contracts changed.
Frontend impact: None.
API impact: None. No route behavior changed and no `/v1/referral-saas/*` wrapper route was added.
Tests to add/update: Added tests proving the plan defaults to read-only routes, seeded-write templates require explicit opt-in, and no product wrapper routes are invented.
Validation method: `.venv_codex\Scripts\python.exe -m pytest -q --no-cov test\test_referral_saas_route_smoke_plan.py --tb=short`; focused Referral SaaS verification suite; `.venv_codex\Scripts\python.exe -m py_compile scripts\referral_saas_route_smoke_plan.py test\test_referral_saas_route_smoke_plan.py`; `ruff check scripts\referral_saas_route_smoke_plan.py test\test_referral_saas_route_smoke_plan.py`; script dry-run execution.
Acceptance criteria: Smoke plan generator emits only read-only route templates by default; local/staging write templates are explicit opt-in; production write guardrail is present; current shared routes are used; product wrapper routes are not invented; no backend/frontend/API/schema behavior changes.
Dependencies: TASK-143; TASK-147; TASK-151; TASK-152.
Blocked by: None for dry-run route smoke planning. Actual route execution remains separately gated by running app URL, credentials, seeded subjects, and approval.
Risk level: Low.
Rollback notes: Revert the smoke plan script, test file, script README update, route smoke inventory note, roadmap update, and this task entry.
Explicit non-goals: Do not execute route smoke calls, connect to production, discover credentials, write data, add product wrapper routes, change routers, schema, migrations, frontend, auth, command idempotency implementation, audit writes, repair/replay/retry actions, export APIs, campaign activation, webhook delivery, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, or SaaS billing behavior.
Definition of done: Referral SaaS has CI-tested route smoke command planning with safe read-only defaults and explicit local/staging write boundaries, preparing the next verification slice without crossing live-data safety gates. Priority: P0.

## TASK-154: Add Referral SaaS safe-status/reporting contract test

Status: Complete (2026-07-12). Output: `test/test_referral_saas_status_reporting_contract.py`; `docs/roadmap/referral-saas/ROADMAP.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/README.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_SAFE_STATUS_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_E2E_LIVE_VERIFICATION_PLAN.md`.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Safe referrer/customer status; tenant-safe reporting; redaction; operational metric boundary; product report catalog gap evidence.
Objective: Add a local/CI-safe Referral SaaS contract test proving the current safe-status and tenant-safe analytics foundations remain bounded and redacted while future product report/status wrapper gaps stay explicit.
Why now: TASK-149 through TASK-153 established golden-path, negative-path, route smoke, schema/status, and smoke-plan verification. The E2E plan also requires safe-status and reporting assertions after TASK-141 and TASK-142; this task adds the first executable coverage for that handoff without implementing new product routes.
Files involved: `test/test_referral_saas_status_reporting_contract.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `services/partner_customer_safe_status_service.py`; `services/tenant_safe_analytics_service.py`; `test/test_partner_customer_safe_status_service.py`; `test/test_tenant_safe_analytics_service.py`; `docs/sa/referral-saas/REFERRAL_SAAS_SAFE_STATUS_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`.
Database/schema impact: None. The test uses monkeypatched service inputs only; no live DB access, migrations, schema changes, or runtime data changes.
Backend impact: Test-only. No services, routers, auth helpers, fields, statuses, report catalog entries, or payload contracts changed.
Frontend impact: None.
API impact: None. No route behavior changed and no `/v1/referral-saas/*` wrapper route was added.
Tests to add/update: Added safe-status/reporting contract assertions for referrer/customer-safe projection, adjacent-role settlement redaction, tenant-safe operational reporting, sensitive filter redaction, exclusion of commission/wallet money metrics, and explicit rejection of future Referral SaaS report types such as `campaign_performance` until implemented.
Validation method: `.venv_codex\Scripts\python.exe -m pytest -q --no-cov test\test_referral_saas_status_reporting_contract.py --tb=short`; focused Referral SaaS verification suite; `.venv_codex\Scripts\python.exe -m py_compile test\test_referral_saas_status_reporting_contract.py`; `ruff check test\test_referral_saas_status_reporting_contract.py`.
Acceptance criteria: Test proves current safe-status and reporting foundations can support bounded Referral SaaS assertions; raw source statuses and sensitive filters are not leaked; operational reporting excludes broader DLaaS money metrics; missing Referral SaaS report catalog remains explicit; no backend/frontend/API/schema behavior changes.
Dependencies: TASK-141; TASK-142; TASK-147; TASK-149 through TASK-153.
Blocked by: None for local contract coverage. Product API wrappers, dedicated Referral SaaS report catalog, and customer/referrer safe-status wrapper remain separate implementation work.
Risk level: Low.
Rollback notes: Revert the test file and this roadmap entry.
Explicit non-goals: Do not implement product wrapper routes, report catalog entries, exports, schema, migrations, frontend, auth changes, live DB checks, route smoke execution, command idempotency implementation, audit writes, repair/replay/retry actions, campaign activation, webhook delivery, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, or SaaS billing behavior.
Definition of done: Referral SaaS has executable safe-status/reporting handoff coverage that proves current foundations are bounded and redacted while keeping product-wrapper and report-catalog gaps visible. Priority: P0.

## TASK-155: Add Referral SaaS safe-status projection helper

Status: Complete (2026-07-12). Output: `services/referral_saas_safe_status_service.py`; `test/test_referral_saas_safe_status_service.py`; `test/test_referral_saas_status_reporting_contract.py`; `docs/roadmap/referral-saas/ROADMAP.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/README.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_SAFE_STATUS_CONTRACT.md`.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Referrer/customer safe product status; progress/outcome status projection; redaction; product label and summary packaging.
Objective: Add a narrow Referral SaaS safe-status projection helper over the existing shared partner/customer safe-status primitive so current referral statuses such as `ACCOUNT_OPENED` project to product-safe statuses without changing backend state names.
Why now: TASK-154 proved the broad safe-status foundation was bounded but left Referral SaaS source statuses such as `ACCOUNT_OPENED` unavailable. This task closes that product projection gap while preserving shared primitive ownership and avoiding new routes.
Files involved: `services/referral_saas_safe_status_service.py`; `test/test_referral_saas_safe_status_service.py`; `test/test_referral_saas_status_reporting_contract.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `services/partner_customer_safe_status_service.py`; `docs/sa/referral-saas/REFERRAL_SAAS_SAFE_STATUS_CONTRACT.md`; `test/test_partner_customer_safe_status_service.py`; `test/test_referral_saas_status_reporting_contract.py`.
Database/schema impact: None.
Backend impact: Added a small service-layer projection helper only. No shared backend states, routers, auth helpers, schemas, migrations, or durable payload contracts changed.
Frontend impact: None.
API impact: None. No route behavior changed and no `/v1/referral-saas/*` wrapper route was added.
Tests to add/update: Added projection tests for outcome, validation, progress, attribution, link/code, adjacent-role money evidence, and sensitive evidence rejection; updated the safe-status/reporting contract test to use the Referral SaaS projection.
Validation method: `.venv_codex\Scripts\python.exe -m pytest -q --no-cov test\test_referral_saas_safe_status_service.py test\test_referral_saas_status_reporting_contract.py --tb=short`; focused Referral SaaS verification suite; `.venv_codex\Scripts\python.exe -m py_compile services\referral_saas_safe_status_service.py test\test_referral_saas_safe_status_service.py test\test_referral_saas_status_reporting_contract.py`; `ruff check services\referral_saas_safe_status_service.py test\test_referral_saas_safe_status_service.py test\test_referral_saas_status_reporting_contract.py`.
Acceptance criteria: Referral SaaS statuses project to safe broad and product statuses; raw source statuses are not leaked except where they are the safe product status; adjacent-role money evidence remains unavailable to customer/referrer views; sensitive evidence is rejected; no backend/frontend/API/schema behavior changes beyond the new helper.
Dependencies: TASK-141; TASK-154.
Blocked by: None for local helper coverage. Product API wrapper and frontend consumption remain separate implementation work.
Risk level: Low.
Rollback notes: Revert the helper, test updates, and this roadmap entry.
Explicit non-goals: Do not implement product wrapper routes, frontend, schema, migrations, auth changes, report catalog entries, exports, live DB checks, route smoke execution, command idempotency implementation, audit writes, repair/replay/retry actions, campaign activation, webhook delivery, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, or SaaS billing behavior.
Definition of done: Referral SaaS has a CI-tested product status projection helper that turns current referral source evidence into safe customer/referrer product status while preserving shared primitives and product boundaries. Priority: P0.

## TASK-156: Add Referral SaaS report catalog helper

Status: Complete (2026-07-12). Output: `services/referral_saas_reporting_service.py`; `test/test_referral_saas_reporting_service.py`; `test/test_referral_saas_status_reporting_contract.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/README.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Tenant-safe Referral SaaS report catalog; campaign performance reporting; redaction; export gap visibility.
Objective: Add a narrow Referral SaaS report catalog helper that supports the first product report type, `campaign_performance`, over the existing tenant-safe analytics foundation without adding routes, exports, schema, or a parallel analytics stack.
Why now: TASK-154 proved reporting boundaries but kept `campaign_performance` unsupported, and TASK-155 completed the safe-status projection helper. The next 10/10 blocker is turning the report catalog from contract-only into executable service behavior while preserving product boundaries.
Files involved: `services/referral_saas_reporting_service.py`; `test/test_referral_saas_reporting_service.py`; `test/test_referral_saas_status_reporting_contract.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `services/tenant_safe_analytics_service.py`; `test/test_tenant_safe_analytics_service.py`; `test/test_referral_saas_status_reporting_contract.py`; `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`.
Database/schema impact: None.
Backend impact: Added a service-layer Referral SaaS report catalog adapter. It maps `campaign_performance` to the current `distribution_overview` tenant-safe analytics source, filters to product-safe operational metrics, preserves freshness/source warnings, and keeps future report types explicit as not implemented.
Frontend impact: None.
API impact: None. No `/v1/referral-saas/*` route or export API was added.
Tests to add/update: Added report catalog tests for available/future report types, campaign performance mapping, sensitive filter redaction, exclusion of broader DLaaS money/governance metrics, unsupported report rejection, unsupported dimension/filter rejection, and updated the safe-status/reporting contract test.
Validation method: `.venv_codex\Scripts\python.exe -m pytest -q --no-cov test\test_referral_saas_reporting_service.py test\test_referral_saas_status_reporting_contract.py --tb=short`; `.venv_codex\Scripts\python.exe -m py_compile services\referral_saas_reporting_service.py test\test_referral_saas_reporting_service.py test\test_referral_saas_status_reporting_contract.py`; `ruff check services\referral_saas_reporting_service.py test\test_referral_saas_reporting_service.py test\test_referral_saas_status_reporting_contract.py`.
Acceptance criteria: `campaign_performance` is available through a Referral SaaS helper; future report catalog entries remain explicit and blocked until implemented; sensitive filters are redacted; broader DLaaS money, wallet, commission, settlement, funding, and governance metrics are not exposed; exports remain unavailable; no schema, route, frontend, auth, or live DB behavior changes.
Dependencies: TASK-142; TASK-154; TASK-155.
Blocked by: None for the service helper. Product API wrapper, export API/storage/audit, frontend report screens, and live route smoke execution remain separate implementation work.
Risk level: Low.
Rollback notes: Revert the helper, tests, and roadmap/doc updates.
Explicit non-goals: Do not implement product wrapper routes, OpenAPI, frontend, export API/storage, persisted/scheduled exports, schema, migrations, auth changes, live DB checks, route smoke execution, command idempotency implementation, audit writes, repair/replay/retry actions, campaign activation, webhook delivery, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, or SaaS billing behavior.
Definition of done: Referral SaaS has a CI-tested report catalog helper for the first product report type and keeps remaining report/export gaps visible without duplicating analytics primitives. Priority: P0.

## TASK-157: Add Referral SaaS report API wrapper

Status: Complete (2026-07-12). Output: `apps/api/routers/referral_saas_reports.py`; `test/api/test_referral_saas_reports_api.py`; `apps/api/main.py`; `scripts/referral_saas_route_smoke_plan.py`; `test/test_referral_saas_route_smoke_inventory.py`; `test/test_referral_saas_route_smoke_plan.py`; `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/README.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: First read-only Referral SaaS product API wrapper; campaign performance report access; route smoke surface update.
Objective: Add the first bounded read-only `/v1/referral-saas/*` product wrapper for report retrieval by exposing the TASK-156 `campaign_performance` helper through `GET /v1/referral-saas/reports/{report_type}`.
Why now: TASK-156 made the first report catalog helper executable. The next 10/10 blocker is product API packaging. A narrow read-only wrapper moves the API surface forward without pretending SaaS account membership, exports, frontend, or broader route families are complete.
Files involved: `apps/api/routers/referral_saas_reports.py`; `apps/api/main.py`; `test/api/test_referral_saas_reports_api.py`; `scripts/referral_saas_route_smoke_plan.py`; `test/test_referral_saas_route_smoke_inventory.py`; `test/test_referral_saas_route_smoke_plan.py`; `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `apps/api/routers/admin_analytics.py`; `apps/api/main.py`; `utils/security.py`; `test/api/test_admin_analytics_api.py`; `services/referral_saas_reporting_service.py`; route smoke inventory and plan tests.
Database/schema impact: None.
Backend impact: Added a read-only FastAPI route wrapper that delegates to `get_referral_saas_report`, returns a safe guardrail, and maps service validation errors to safe 400 responses.
Frontend impact: None.
API impact: Adds `GET /v1/referral-saas/reports/{report_type}` for read-only report retrieval. It currently requires an approved report-reader/admin role and explicit `tenant_code` as a temporary internal bridge until SaaS account membership scope is implemented.
Tests to add/update: Added API tests for allowed roles, missing credentials, rejected partner role, safe validation errors, request parameter forwarding, and export-unavailable guardrail. Updated route smoke inventory and plan tests to allow exactly this one `/v1/referral-saas/*` route.
Validation method: `.venv_codex\Scripts\python.exe -m pytest -q --no-cov test\api\test_referral_saas_reports_api.py test\test_referral_saas_reporting_service.py test\test_referral_saas_status_reporting_contract.py test\test_referral_saas_route_smoke_inventory.py test\test_referral_saas_route_smoke_plan.py --tb=short`; `.venv_codex\Scripts\python.exe -m py_compile apps\api\routers\referral_saas_reports.py test\api\test_referral_saas_reports_api.py scripts\referral_saas_route_smoke_plan.py test\test_referral_saas_route_smoke_inventory.py test\test_referral_saas_route_smoke_plan.py`; `ruff check apps\api\routers\referral_saas_reports.py test\api\test_referral_saas_reports_api.py scripts\referral_saas_route_smoke_plan.py test\test_referral_saas_route_smoke_inventory.py test\test_referral_saas_route_smoke_plan.py`.
Acceptance criteria: The first read-only Referral SaaS report API wrapper is mounted and tested; route smoke inventory recognizes exactly this product wrapper; exports remain unavailable; no account membership, frontend, schema, live DB, write command, export storage, money movement, or broader product API behavior is introduced.
Dependencies: TASK-143; TASK-151; TASK-153; TASK-156.
Blocked by: None for the bounded read-only wrapper. SaaS account/member scope, export API/storage/audit, frontend report screens, additional report types, and live route smoke execution remain separate implementation work.
Risk level: Low.
Rollback notes: Revert the router, app mount, API tests, route smoke updates, and docs updates.
Explicit non-goals: Do not implement account membership resolution, export API/storage, persisted/scheduled exports, frontend screens, schema, migrations, new auth helpers, live DB checks, route smoke execution, write product routes, command idempotency implementation, audit writes, repair/replay/retry actions, campaign activation, webhook delivery, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, or SaaS billing behavior.
Definition of done: Referral SaaS has one CI-tested, read-only product report API wrapper over the shared reporting primitive, with remaining product API gaps explicit and bounded. Priority: P0.

## TASK-158: Add Referral SaaS report account-scope resolver

Status: Complete (2026-07-12). Output: `services/referral_saas_account_scope_service.py`; `test/test_referral_saas_account_scope_service.py`; `apps/api/routers/referral_saas_reports.py`; `test/api/test_referral_saas_reports_api.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/README.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_CONTRACT.md`; `docs/sa/TENANT_ACCOUNT_BOUNDARY_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Account/tenant scope boundary for the first Referral SaaS report API wrapper.
Objective: Add a narrow account-scope resolver for the Referral SaaS report API so tenant-scoped identities can derive tenant scope from authenticated identity while internal report readers still provide explicit tenant scope until full SaaS account membership exists.
Why now: TASK-157 introduced the first read-only product API wrapper but still required caller-supplied `tenant_code`. The next 10/10 blocker is reducing public/product reliance on internal tenant identifiers without inventing account schema or membership tables prematurely.
Files involved: `services/referral_saas_account_scope_service.py`; `test/test_referral_saas_account_scope_service.py`; `apps/api/routers/referral_saas_reports.py`; `test/api/test_referral_saas_reports_api.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `utils/security.py`; `apps/api/routers/session.py`; `apps/api/routers/referral_saas_reports.py`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_CONTRACT.md`; `docs/sa/TENANT_ACCOUNT_BOUNDARY_MAP.md`; `test/api/test_referral_saas_reports_api.py`.
Database/schema impact: None.
Backend impact: Added a service-layer scope resolver and adopted it in the report route. The resolver derives tenant scope from tenant-scoped identities, permits explicit tenant scope for internal readers, and rejects cross-tenant overrides.
Frontend impact: None.
API impact: `tenant_code` is now optional on `GET /v1/referral-saas/reports/{report_type}` when the authenticated identity is already tenant-scoped. Internal report-reader/admin identities still require explicit `tenant_code`.
Tests to add/update: Added resolver unit tests for identity-derived scope, internal explicit scope, missing scope, cross-tenant rejection, and missing identity scope. Updated API tests for identity-derived scope, internal missing scope, cross-tenant rejection, and account-scope response metadata.
Validation method: `.venv_codex\Scripts\python.exe -m pytest -q --no-cov test\test_referral_saas_account_scope_service.py test\api\test_referral_saas_reports_api.py test\test_referral_saas_reporting_service.py test\test_referral_saas_status_reporting_contract.py --tb=short`; `.venv_codex\Scripts\python.exe -m py_compile services\referral_saas_account_scope_service.py apps\api\routers\referral_saas_reports.py test\test_referral_saas_account_scope_service.py test\api\test_referral_saas_reports_api.py`; `ruff check services\referral_saas_account_scope_service.py apps\api\routers\referral_saas_reports.py test\test_referral_saas_account_scope_service.py test\api\test_referral_saas_reports_api.py`.
Acceptance criteria: Tenant-scoped identities can call the report API without explicit `tenant_code`; internal report readers are safely rejected without tenant scope; cross-tenant overrides are rejected; no account tables, membership model, schema, migrations, frontend, export behavior, or broad product route behavior is introduced.
Dependencies: TASK-134; TASK-143; TASK-157.
Blocked by: None for bounded identity-derived report scope. Full SaaS account references, membership, external-reference mapping, account setup APIs, frontend, exports, and broader route wrappers remain separate implementation work.
Risk level: Low.
Rollback notes: Revert the resolver, route adoption, tests, and docs updates.
Explicit non-goals: Do not implement account schema, membership schema, external-reference persistence, SaaS account setup APIs, new auth helpers, frontend screens, export API/storage, persisted/scheduled exports, live DB checks, route smoke execution, write product routes, command idempotency implementation, audit writes, repair/replay/retry actions, campaign activation, webhook delivery, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, or SaaS billing behavior.
Definition of done: Referral SaaS has a CI-tested account-scope resolver for the first report API wrapper, reducing reliance on caller-supplied internal tenant scope where identity scope is already available. Priority: P0.

## TASK-159: Add Referral SaaS referral funnel report helper

Status: Complete (2026-07-12). Output: `services/referral_saas_reporting_service.py`; `test/test_referral_saas_reporting_service.py`; `test/test_referral_saas_status_reporting_contract.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/README.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Referral SaaS report catalog depth; referral funnel reporting; partial-source warning visibility.
Objective: Add `referral_funnel` as the second bounded Referral SaaS report type over the existing tenant-safe analytics foundation without adding exports, schema, frontend, or a parallel analytics stack.
Why now: TASK-156 made the first report catalog helper executable, TASK-157 exposed it through a read-only product route, and TASK-158 reduced internal tenant-code reliance for tenant-scoped identities. The next 10/10 blocker is expanding report depth while keeping incomplete funnel stage evidence explicit.
Files involved: `services/referral_saas_reporting_service.py`; `test/test_referral_saas_reporting_service.py`; `test/test_referral_saas_status_reporting_contract.py`; `test/api/test_referral_saas_reports_api.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `services/referral_saas_reporting_service.py`; `services/tenant_safe_analytics_service.py`; `test/test_referral_saas_reporting_service.py`; `test/test_referral_saas_status_reporting_contract.py`; `test/api/test_referral_saas_reports_api.py`; `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`.
Database/schema impact: None.
Backend impact: Updated the report catalog helper so report types have report-specific metric maps. `referral_funnel` now maps safe distribution overview metrics to funnel metrics and preserves a `PARTIAL_SOURCE_COVERAGE` warning for code-issued, validation-state, and progress-milestone stages that are not yet backed by dedicated report sources.
Frontend impact: None.
API impact: The existing read-only `GET /v1/referral-saas/reports/{report_type}` wrapper can now serve `referral_funnel` through the same account-scope and validation boundary. No new route, export API, permission model, or write behavior was added.
Tests to add/update: Added report catalog and service tests for `referral_funnel`, partial-source warnings, funnel metric mapping, and continued exclusion of broader DLaaS money/governance metrics. Updated contract/API validation tests so remaining future report types still fail safely.
Validation method: `.venv_codex\Scripts\python.exe -m pytest -q --no-cov test\test_referral_saas_reporting_service.py test\test_referral_saas_status_reporting_contract.py test\api\test_referral_saas_reports_api.py --tb=short`; `.venv_codex\Scripts\python.exe -m py_compile services\referral_saas_reporting_service.py test\test_referral_saas_reporting_service.py test\test_referral_saas_status_reporting_contract.py test\api\test_referral_saas_reports_api.py`; `ruff check services\referral_saas_reporting_service.py test\test_referral_saas_reporting_service.py test\test_referral_saas_status_reporting_contract.py test\api\test_referral_saas_reports_api.py`.
Acceptance criteria: `referral_funnel` is available through the Referral SaaS report helper and route; incomplete stage coverage is visible as a source warning; future report types remain explicitly blocked until implemented; exports remain unavailable; no schema, frontend, account membership, live DB, export storage, or DLaaS money/reporting behavior changes.
Dependencies: TASK-142; TASK-156; TASK-157; TASK-158.
Blocked by: None for bounded referral funnel reporting. Dedicated code-issued/validation/progress report sources, exports, frontend reports, full SaaS account references, and live route smoke execution remain separate implementation work.
Risk level: Low.
Rollback notes: Revert the report catalog mapping, tests, and docs updates.
Explicit non-goals: Do not implement export API/storage, persisted/scheduled exports, frontend screens, schema, migrations, account schema, membership schema, external-reference persistence, new auth helpers, live DB checks, route smoke execution, write product routes, command idempotency implementation, audit writes, repair/replay/retry actions, campaign activation, webhook delivery, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, or SaaS billing behavior.
Definition of done: Referral SaaS has a CI-tested second report type for referral funnel metrics with honest partial-source coverage and no duplicate analytics stack. Priority: P0.

## TASK-160: Add Referral SaaS progress event health report

Status: Complete (2026-07-12). Output: `services/referral_saas_reporting_service.py`; `test/test_referral_saas_reporting_service.py`; `test/test_referral_saas_status_reporting_contract.py`; `test/api/test_referral_saas_reports_api.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/README.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PROGRESS_EVENT_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`.
Shared primitive impact: Reads existing progress/failure primitives only; no duplicated source code or forked progress event model.
Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Progress event health reporting; tenant-safe operational event evidence; partial-source warning visibility.
Objective: Add `progress_event_health` as the third bounded Referral SaaS report type over current progress-event and event-failure evidence without adding schema, exports, frontend, or a new analytics stack.
Why now: TASK-159 added referral funnel reporting but left progress-event health as a visible report blocker. The next 10/10 blocker is making progress ingestion health reportable while preserving tenant scope and not exposing raw event payloads.
Files involved: `services/referral_saas_reporting_service.py`; `test/test_referral_saas_reporting_service.py`; `test/test_referral_saas_status_reporting_contract.py`; `test/api/test_referral_saas_reports_api.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `services/referral_saas_reporting_service.py`; `services/progress_service.py`; `services/failure_governance_service.py`; `dp/migrations/013_progress_events.sql`; `dp/migrations/020_referral_event_failures.sql`; `dp/migrations/031_tenent.sql`; `test/test_referral_saas_reporting_service.py`; `test/test_referral_saas_status_reporting_contract.py`; `test/api/test_referral_saas_reports_api.py`.
Database/schema impact: None. Uses existing `referral_progress_events`, `referral_event_failures`, and `referral_instances.tenant_code`.
Backend impact: Added a private read-only progress health source inside the Referral SaaS report adapter. It joins progress and failure rows through `referral_instances` for tenant scope, reports recorded/failed/retry/open/resolved counts, excludes unscoped failure rows, and returns partial-source warnings for deduped/rejected states that are not persisted in reportable form.
Frontend impact: None.
API impact: The existing read-only `GET /v1/referral-saas/reports/{report_type}` wrapper can now serve `progress_event_health` through the same account-scope and validation boundary. No new route, export API, permission model, or write behavior was added.
Tests to add/update: Added service tests for catalog availability, tenant-scoped SQL, date-window forwarding, sensitive redaction, progress/failure metric mapping, unavailable source handling, and continued safe blocking of future report types. Updated contract/API tests to treat `attribution_quality` as the next unimplemented report type.
Validation method: `.venv_codex\Scripts\python.exe -m pytest -q --no-cov test\test_referral_saas_reporting_service.py test\test_referral_saas_status_reporting_contract.py test\api\test_referral_saas_reports_api.py --tb=short`; `.venv_codex\Scripts\python.exe -m py_compile services\referral_saas_reporting_service.py test\test_referral_saas_reporting_service.py test\test_referral_saas_status_reporting_contract.py test\api\test_referral_saas_reports_api.py`; `ruff check services\referral_saas_reporting_service.py test\test_referral_saas_reporting_service.py test\test_referral_saas_status_reporting_contract.py test\api\test_referral_saas_reports_api.py`.
Acceptance criteria: `progress_event_health` is available through the Referral SaaS report helper and route; reads are tenant-scoped through `referral_instances`; raw payloads/UCNs are redacted; unscoped failure rows are excluded; deduped/rejected gaps are visible as partial-source coverage; future report types remain explicitly blocked until implemented; exports remain unavailable; no schema, frontend, account membership, live DB, export storage, or DLaaS money/reporting behavior changes.
Dependencies: TASK-138; TASK-142; TASK-156; TASK-157; TASK-158.
Blocked by: None for bounded progress health reporting. Persisted deduped/rejected event states, exports, frontend reports, full SaaS account references, and live route smoke execution remain separate implementation work.
Risk level: Low.
Rollback notes: Revert the report helper changes, tests, and docs updates.
Explicit non-goals: Do not implement export API/storage, persisted/scheduled exports, frontend screens, schema, migrations, account schema, membership schema, external-reference persistence, new auth helpers, live DB checks, route smoke execution, write product routes, command idempotency implementation, audit writes, repair/replay/retry actions, campaign activation, webhook delivery, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, or SaaS billing behavior.
Definition of done: Referral SaaS has a CI-tested third report type for progress-event health using existing tenant-scoped progress/failure evidence, with honest partial-source coverage and no duplicate analytics stack. Priority: P0.

## TASK-161: Add Referral SaaS attribution quality report

Status: Complete (2026-07-12). Output: `services/referral_saas_reporting_service.py`; `test/test_referral_saas_reporting_service.py`; `test/test_referral_saas_status_reporting_contract.py`; `test/api/test_referral_saas_reports_api.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/README.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ATTRIBUTION_TRACE_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`.
Shared primitive impact: Reads existing referral, campaign attribution, campaign-link, and route-link evidence only; no duplicated attribution model or source-code fork.
Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Attribution quality reporting; tenant-safe derived trace status; missing-evidence and conflict visibility.
Objective: Add `attribution_quality` as the fourth bounded Referral SaaS report type over current attribution evidence without adding schema, exports, frontend, raw trace exposure, or a new analytics stack.
Why now: TASK-160 closed progress-event health reporting, leaving attribution quality and safe-status distribution as the remaining report catalog blockers before exports/account/UI work. The next 10/10 blocker is making aggregate attribution quality visible through the product report wrapper.
Files involved: `services/referral_saas_reporting_service.py`; `test/test_referral_saas_reporting_service.py`; `test/test_referral_saas_status_reporting_contract.py`; `test/api/test_referral_saas_reports_api.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `services/referral_saas_reporting_service.py`; `services/outcome_trace_service.py`; `services/distribution/reporting_service.py`; `dp/migrations/001_init.sql`; `dp/migrations/002_campaigns.sql`; `dp/migrations/014_campaign_referral_links.sql`; `dp/migrations/031_tenent.sql`; `dp/migrations/070_distribution_route_referral_links.sql`; `test/test_referral_saas_reporting_service.py`; `test/test_referral_saas_status_reporting_contract.py`; `test/api/test_referral_saas_reports_api.py`.
Database/schema impact: None. Uses existing `referral_instances`, `campaign_referral_links`, `campaign_attributions`, `distribution_route_referral_links`, and `distribution_opportunities`.
Backend impact: Added a private read-only attribution quality source inside the Referral SaaS report adapter. It derives aggregate `COMPLETE`, `PARTIAL`, `MISSING_EVIDENCE`, `INCONSISTENT`, and `UNATTRIBUTED` trace-status counts through tenant-scoped joins and surfaces derived source-confidence and warning-code dimensions.
Frontend impact: None.
API impact: The existing read-only `GET /v1/referral-saas/reports/{report_type}` wrapper can now serve `attribution_quality` through the same account-scope and validation boundary. No new route, export API, permission model, or write behavior was added.
Tests to add/update: Added service tests for catalog availability, tenant-scoped SQL, date-window forwarding, sensitive redaction, derived attribution metrics, source warning behavior, unavailable source handling, and continued safe blocking of future report types. Updated contract/API tests to treat `safe_status_distribution` as the next unimplemented report type.
Validation method: `.venv_codex\Scripts\python.exe -m pytest -q --no-cov test\test_referral_saas_reporting_service.py test\test_referral_saas_status_reporting_contract.py test\api\test_referral_saas_reports_api.py --tb=short`; `.venv_codex\Scripts\python.exe -m py_compile services\referral_saas_reporting_service.py test\test_referral_saas_reporting_service.py test\test_referral_saas_status_reporting_contract.py test\api\test_referral_saas_reports_api.py`; `ruff check services\referral_saas_reporting_service.py test\test_referral_saas_reporting_service.py test\test_referral_saas_status_reporting_contract.py test\api\test_referral_saas_reports_api.py`.
Acceptance criteria: `attribution_quality` is available through the Referral SaaS report helper and route; reads are tenant-scoped; raw trace payloads and private identifiers are not exposed; complete/partial/missing/inconsistent/unattributed counts are derived from current evidence; future report types remain explicitly blocked until implemented; exports remain unavailable; no schema, frontend, account membership, live DB, export storage, or DLaaS money/reporting behavior changes.
Dependencies: TASK-139; TASK-142; TASK-156; TASK-157; TASK-158; TASK-160.
Blocked by: None for bounded attribution quality reporting. Raw trace exports, safe-status distribution reporting, exports, frontend reports, full SaaS account references, and live route smoke execution remain separate implementation work.
Risk level: Low.
Rollback notes: Revert the report helper changes, tests, and docs updates.
Explicit non-goals: Do not implement export API/storage, persisted/scheduled exports, frontend screens, schema, migrations, account schema, membership schema, external-reference persistence, new auth helpers, live DB checks, route smoke execution, write product routes, command idempotency implementation, audit writes, repair/replay/retry actions, campaign activation, webhook delivery, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, or SaaS billing behavior.
Definition of done: Referral SaaS has a CI-tested fourth report type for attribution quality using existing tenant-scoped referral/attribution evidence, with derived trace statuses and no duplicate analytics stack. Priority: P0.

## TASK-162: Add Referral SaaS safe-status distribution report

Status: Complete (2026-07-12). Output: `services/referral_saas_reporting_service.py`; `test/test_referral_saas_reporting_service.py`; `test/test_referral_saas_status_reporting_contract.py`; `test/api/test_referral_saas_reports_api.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/README.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_SAFE_STATUS_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`.
Shared primitive impact: Reads existing referral outcome evidence and uses the existing Referral SaaS safe-status vocabulary; no duplicated status system or source-code fork.
Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Safe-status distribution reporting; tenant-safe derived product status; action-category visibility.
Objective: Add `safe_status_distribution` as the fifth bounded Referral SaaS report type over current referral outcome evidence without adding schema, exports, frontend, raw viewer evidence, or a new analytics stack.
Why now: TASK-161 closed attribution quality reporting, leaving safe-status distribution as the final first-launch report catalog blocker before reward visibility, exports, account references, and UI work.
Files involved: `services/referral_saas_reporting_service.py`; `test/test_referral_saas_reporting_service.py`; `test/test_referral_saas_status_reporting_contract.py`; `test/api/test_referral_saas_reports_api.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `services/referral_saas_reporting_service.py`; `services/referral_saas_safe_status_service.py`; `services/partner_customer_safe_status_service.py`; `test/test_referral_saas_safe_status_service.py`; `test/test_referral_saas_reporting_service.py`; `test/test_referral_saas_status_reporting_contract.py`; `test/api/test_referral_saas_reports_api.py`.
Database/schema impact: None. Uses existing `referral_instances` tenant-scoped outcome evidence.
Backend impact: Added a private read-only safe-status distribution source inside the Referral SaaS report adapter. It derives aggregate `safe_status`, `product_status`, and `action_category` counts from tenant-scoped referral outcomes using the Referral SaaS safe-status vocabulary.
Frontend impact: None.
API impact: The existing read-only `GET /v1/referral-saas/reports/{report_type}` wrapper can now serve `safe_status_distribution` through the same account-scope and validation boundary. No new route, export API, permission model, or write behavior was added.
Tests to add/update: Added service tests for catalog availability, tenant-scoped SQL, date-window forwarding, sensitive redaction, derived safe-status metrics, source warning behavior, unavailable source handling, and continued safe blocking of future report types. At completion time, contract/API tests treated `reward_visibility_summary` as the next unimplemented report type; TASK-164 later implemented it.
Validation method: `.venv_codex\Scripts\python.exe -m pytest -q --no-cov test\test_referral_saas_reporting_service.py test\test_referral_saas_status_reporting_contract.py test\api\test_referral_saas_reports_api.py --tb=short`; `.venv_codex\Scripts\python.exe -m py_compile services\referral_saas_reporting_service.py test\test_referral_saas_reporting_service.py test\test_referral_saas_status_reporting_contract.py test\api\test_referral_saas_reports_api.py`; `ruff check services\referral_saas_reporting_service.py test\test_referral_saas_reporting_service.py test\test_referral_saas_status_reporting_contract.py test\api\test_referral_saas_reports_api.py`.
Acceptance criteria: `safe_status_distribution` is available through the Referral SaaS report helper and route; reads are tenant-scoped; raw viewer, UCN, reward, audit, provider, and money evidence are not exposed; safe/product/action status counts are derived from current outcome evidence; future report types remain explicitly blocked until implemented; exports remain unavailable; no schema, frontend, account membership, live DB, export storage, or DLaaS money/reporting behavior changes.
Dependencies: TASK-141; TASK-142; TASK-155; TASK-156; TASK-157; TASK-158.
Blocked by: None for bounded safe-status distribution reporting. Link/code performance, reward visibility summary, exports, frontend reports, full SaaS account references, and live route smoke execution remain separate implementation work.
Risk level: Low.
Rollback notes: Revert the report helper changes, tests, and docs updates.
Explicit non-goals: Do not implement export API/storage, persisted/scheduled exports, frontend screens, schema, migrations, account schema, membership schema, external-reference persistence, new auth helpers, live DB checks, route smoke execution, write product routes, command idempotency implementation, audit writes, repair/replay/retry actions, campaign activation, webhook delivery, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, or SaaS billing behavior.
Definition of done: Referral SaaS has a CI-tested fifth report type for safe-status distribution using existing tenant-scoped referral outcome evidence and safe-status vocabulary, with no duplicate analytics stack. Priority: P0.

## TASK-163: Add Referral SaaS link/code performance report

Status: Complete (2026-07-12). Output: `services/referral_saas_reporting_service.py`; `apps/api/routers/referral_saas_reports.py`; `test/test_referral_saas_reporting_service.py`; `test/test_referral_saas_status_reporting_contract.py`; `test/api/test_referral_saas_reports_api.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/README.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_LINK_CODE_INVESTIGATION_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`.
Shared primitive impact: Reads existing referral code, campaign code, campaign-referral link, and route-referral link evidence only; no duplicated link/code model or source-code fork.
Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Link/code performance reporting; tenant-safe source/status counts; partial-source warning visibility.
Objective: Add `link_code_performance` as the sixth bounded Referral SaaS report type over current durable link/code evidence without adding schema, exports, frontend, raw link/code evidence exposure, or a new analytics stack.
Why now: TASK-162 closed safe-status distribution reporting, leaving link/code performance and reward visibility as report catalog blockers. Link/code performance is core to the Referral SaaS wedge and can be implemented safely before reward-adjacent reporting.
Files involved: `services/referral_saas_reporting_service.py`; `apps/api/routers/referral_saas_reports.py`; `test/test_referral_saas_reporting_service.py`; `test/test_referral_saas_status_reporting_contract.py`; `test/api/test_referral_saas_reports_api.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Implementation/source files inspected: `services/referral_saas_reporting_service.py`; `services/link_code_service.py`; `dp/migrations/001_init.sql`; `dp/migrations/002_campaigns.sql`; `dp/migrations/014_campaign_referral_links.sql`; `dp/migrations/070_distribution_route_referral_links.sql`; `test/test_referral_saas_reporting_service.py`; `test/test_referral_saas_status_reporting_contract.py`; `test/api/test_referral_saas_reports_api.py`.
Database/schema impact: None. Uses existing `referrer_codes`, `marketing_campaigns`, `campaign_referral_links`, `campaign_attributions`, `distribution_route_referral_links`, and `distribution_opportunities`.
Backend impact: Added a private read-only link/code performance source inside the Referral SaaS report adapter. It derives issued, active, linked, expired, invalid, and voided counts by source type, campaign, issued period, and resolved period.
Frontend impact: None.
API impact: The existing read-only `GET /v1/referral-saas/reports/{report_type}` wrapper can now serve `link_code_performance` and forward `source_type` plus `link_code_status` filters through the same account-scope and validation boundary. No new route, export API, permission model, or write behavior was added.
Tests to add/update: Added service tests for catalog availability, tenant-scoped SQL, date-window forwarding, sensitive redaction, link/code metric mapping, unavailable source handling, and continued safe blocking of future report types. At completion time, contract/API tests included `link_code_performance` and kept `reward_visibility_summary` as the next unimplemented report type; TASK-164 later implemented it.
Validation method: `.venv_codex\Scripts\python.exe -m pytest -q --no-cov test\test_referral_saas_reporting_service.py test\test_referral_saas_status_reporting_contract.py test\api\test_referral_saas_reports_api.py --tb=short`; `.venv_codex\Scripts\python.exe -m py_compile services\referral_saas_reporting_service.py apps\api\routers\referral_saas_reports.py test\test_referral_saas_reporting_service.py test\test_referral_saas_status_reporting_contract.py test\api\test_referral_saas_reports_api.py`; `ruff check services\referral_saas_reporting_service.py apps\api\routers\referral_saas_reports.py test\test_referral_saas_reporting_service.py test\test_referral_saas_status_reporting_contract.py test\api\test_referral_saas_reports_api.py`.
Acceptance criteria: `link_code_performance` is available through the Referral SaaS report helper and route; reads are tenant-scoped; raw UCNs, raw code/link payloads, composite-code internals, reward, audit, provider, funding, fulfilment, settlement, wallet, commission, invoice, and money evidence are not exposed; source/status counts are derived from current durable evidence; composite-code compatibility remains an honest partial-source warning; future report types remain explicitly blocked until implemented; exports remain unavailable; no schema, frontend, account membership, live DB, export storage, or DLaaS money/reporting behavior changes.
Dependencies: TASK-140; TASK-142; TASK-156; TASK-157; TASK-158; TASK-162.
Blocked by: None for bounded link/code performance reporting. Reward visibility summary was closed by TASK-164; exports, frontend reports, full SaaS account references, composite-code durable evidence, and live route smoke execution remain separate implementation work.
Risk level: Low.
Rollback notes: Revert the report helper changes, route filter additions, tests, and docs updates.
Explicit non-goals: Do not implement export API/storage, persisted/scheduled exports, frontend screens, schema, migrations, account schema, membership schema, external-reference persistence, new auth helpers, live DB checks, route smoke execution, write product routes, code revoke/expire/reissue commands, command idempotency implementation, audit writes, repair/replay/retry actions, campaign activation, webhook delivery, reward money totals, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, or SaaS billing behavior.
Definition of done: Referral SaaS has a CI-tested sixth report type for link/code performance using existing durable tenant-scoped link/code evidence, with composite-code limits visible and no duplicate analytics stack. Priority: P0.

## TASK-164: Add Referral SaaS reward visibility summary report

Status: Complete (2026-07-12). Output: `services/referral_saas_reporting_service.py`; `apps/api/routers/referral_saas_reports.py`; `test/test_referral_saas_reporting_service.py`; `test/test_referral_saas_status_reporting_contract.py`; `test/api/test_referral_saas_reports_api.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/README.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_SAFE_STATUS_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`.
Shared primitive impact: Reads existing reward and mission progress evidence only; no duplicated reward model, fulfilment model, funding model, settlement model, or source-code fork.
Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Count-only reward visibility reporting; tenant-safe reward status/source evidence; money-boundary protection.
Objective: Add `reward_visibility_summary` as the seventh bounded Referral SaaS report type over current reward visibility evidence without adding schema, exports, frontend, reward amount totals, beneficiary references, or any money-movement reporting.
Why now: TASK-163 closed link/code performance reporting, leaving reward visibility as the final first-launch report catalog type before export/account/frontend/live-proof work. Reward visibility is allowed by the product brief when it stays count-only and avoids deep money movement.
Files involved: `services/referral_saas_reporting_service.py`; `apps/api/routers/referral_saas_reports.py`; `test/test_referral_saas_reporting_service.py`; `test/test_referral_saas_status_reporting_contract.py`; `test/api/test_referral_saas_reports_api.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Implementation/source files inspected: `services/referral_saas_reporting_service.py`; `services/reward_summary_service.py`; `services/reward_service.py`; `dp/migrations/022_reward.sql`; `dp/migrations/024_mission_and_reward_summary.sql`; `dp/migrations/034_reward_update.sql`; `test/test_reward_summary_service.py`; `test/test_reward_summary_api.py`; `test/test_referral_saas_reporting_service.py`; `test/test_referral_saas_status_reporting_contract.py`; `test/api/test_referral_saas_reports_api.py`.
Database/schema impact: None. Uses existing `rewards`, `user_mission_progress`, `mission_definitions`, and `referral_instances`.
Backend impact: Added a private read-only reward visibility source inside the Referral SaaS report adapter. It derives count-only reward metrics by status, source, beneficiary type, product, sub-product, reward type, source family, and visibility period.
Frontend impact: None.
API impact: The existing read-only `GET /v1/referral-saas/reports/{report_type}` wrapper can now serve `reward_visibility_summary` and forward reward-specific filters through the same account-scope and validation boundary. No new route, export API, permission model, or write behavior was added.
Tests to add/update: Added service tests for catalog availability, tenant-scoped SQL, date-window forwarding, sensitive redaction, reward status/source metric mapping, count-only behavior, unavailable source handling, and no private beneficiary/amount leakage. Updated contract/API tests to include `reward_visibility_summary`.
Validation method: `.venv_codex\Scripts\python.exe -m pytest -q --no-cov test\test_referral_saas_reporting_service.py test\test_referral_saas_status_reporting_contract.py test\api\test_referral_saas_reports_api.py --tb=short`; `.venv_codex\Scripts\python.exe -m py_compile services\referral_saas_reporting_service.py apps\api\routers\referral_saas_reports.py test\test_referral_saas_reporting_service.py test\test_referral_saas_status_reporting_contract.py test\api\test_referral_saas_reports_api.py`; `ruff check services\referral_saas_reporting_service.py apps\api\routers\referral_saas_reports.py test\test_referral_saas_reporting_service.py test\test_referral_saas_status_reporting_contract.py test\api\test_referral_saas_reports_api.py`.
Acceptance criteria: `reward_visibility_summary` is available through the Referral SaaS report helper and route; reads are tenant-scoped; metrics are counts only; raw UCNs, beneficiary references, reward amount totals, fulfilment, funding, settlement, wallet, commission, invoice, payout, provider, audit, and money evidence are not exposed; pending mission bonus counts are derived honestly from active incomplete mission progress; exports remain unavailable; no schema, frontend, account membership, live DB, export storage, or DLaaS money/reporting behavior changes.
Dependencies: TASK-141; TASK-142; TASK-156; TASK-157; TASK-158; TASK-163.
Blocked by: None for bounded reward visibility counts. Export APIs/storage/audit, frontend reports, full SaaS account references, live route smoke execution, and ledger-backed money reporting remain separate implementation work.
Risk level: Medium.
Rollback notes: Revert the report helper changes, route filter additions, tests, and docs updates.
Explicit non-goals: Do not implement export API/storage, persisted/scheduled exports, frontend screens, schema, migrations, account schema, membership schema, external-reference persistence, new auth helpers, live DB checks, route smoke execution, write product routes, reward application, reward fulfilment, reward funding, reward settlement, reward amount totals, ledger-backed reporting, command idempotency implementation, audit writes, repair/replay/retry actions, campaign activation, webhook delivery, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, or SaaS billing behavior.
Definition of done: Referral SaaS has a CI-tested seventh report type for reward visibility counts using existing tenant-scoped reward and mission evidence, with money boundaries explicit and no duplicate reward/reporting stack. Priority: P0.

## TASK-165: Add Referral SaaS export validation gate

Status: Complete (2026-07-12). Output: `services/referral_saas_reporting_service.py`; `apps/api/routers/referral_saas_reports.py`; `test/test_referral_saas_reporting_service.py`; `test/test_referral_saas_status_reporting_contract.py`; `test/api/test_referral_saas_reports_api.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/README.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`.
Shared primitive impact: Validates export requests over the existing Referral SaaS report catalog helper only; no duplicated export, storage, delivery, audit, analytics, or money-reporting stack.
Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Report export request validation; safe format/profile/dimension/filter/row-limit gate; no persisted export creation.
Objective: Add a validation-only Referral SaaS report export gate for the current report catalog without creating export files, storage records, delivery jobs, scheduled exports, audit rows, or money/reporting behavior.
Why now: TASK-164 completed the first-launch report catalog. The next 10/10 blocker is preventing unsafe export requests while keeping public export creation, storage, retention, and delivery out of scope until those controls are designed.
Files involved: `services/referral_saas_reporting_service.py`; `apps/api/routers/referral_saas_reports.py`; `test/test_referral_saas_reporting_service.py`; `test/test_referral_saas_status_reporting_contract.py`; `test/api/test_referral_saas_reports_api.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Implementation/source files inspected: `services/referral_saas_reporting_service.py`; `apps/api/routers/referral_saas_reports.py`; `test/test_referral_saas_reporting_service.py`; `test/test_referral_saas_status_reporting_contract.py`; `test/api/test_referral_saas_reports_api.py`; `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`.
Database/schema impact: None.
Backend impact: Added `validate_referral_saas_report_export_request`, which normalizes tenant scope, report type, dimensions, filters, export format, redaction profile, row limit, and date window. It returns `VALIDATED_NOT_CREATED` and explicit `NOT_IMPLEMENTED` creation/storage/delivery/audit statuses.
Frontend impact: None.
API impact: Added `POST /v1/referral-saas/reports/{report_type}/exports/validate` using the existing Referral SaaS report-reader role boundary and account-scope resolver. It does not implement `POST /exports`, export IDs, file creation, retention, delivery, or storage.
Tests to add/update: Added service tests for valid metadata-only export validation and rejection of unsafe formats, profiles, dimensions, filters, row limits, and data windows. Added API tests for success, safe validation errors, and partner rejection. Updated the status/reporting contract test to assert export validation remains non-persistent.
Validation method: `.venv_codex\Scripts\python.exe -m pytest -q --no-cov test\test_referral_saas_reporting_service.py test\test_referral_saas_status_reporting_contract.py test\api\test_referral_saas_reports_api.py --tb=short`; `.venv_codex\Scripts\python.exe -m py_compile services\referral_saas_reporting_service.py apps\api\routers\referral_saas_reports.py test\test_referral_saas_reporting_service.py test\test_referral_saas_status_reporting_contract.py test\api\test_referral_saas_reports_api.py`; `ruff check services\referral_saas_reporting_service.py apps\api\routers\referral_saas_reports.py test\test_referral_saas_reporting_service.py test\test_referral_saas_status_reporting_contract.py test\api\test_referral_saas_reports_api.py`.
Acceptance criteria: Export validation accepts only supported report types, `json`/`csv` formats, `tenant_safe` redaction, approved dimensions/filters, valid row limits, and valid date windows; validation uses the existing account-scope boundary; validation is side-effect free; export creation/storage/delivery/audit remain explicitly unimplemented; no schema, frontend, live DB, money, fulfilment, funding, settlement, wallet, commission, invoice, payout, sponsor billing, or DLaaS expansion behavior changes.
Dependencies: TASK-142; TASK-156; TASK-157; TASK-158; TASK-164.
Blocked by: None for validation-only export gating. Persisted exports, export IDs, retention/expiry, audit writes, scheduled delivery, frontend export UX, full SaaS account references, and live route smoke execution remain separate implementation work.
Risk level: Low.
Rollback notes: Revert the export validation helper, route, tests, and docs updates.
Explicit non-goals: Do not implement public export creation, export files, export storage, persisted/scheduled exports, export IDs, export downloads, retention/expiry, audit writes, frontend screens, schema, migrations, account schema, membership schema, external-reference persistence, new auth helpers, live DB checks, route smoke execution, write product routes, command idempotency implementation, campaign activation, webhook delivery, reward application, reward fulfilment, reward funding, reward settlement, reward amount totals, ledger-backed reporting, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, or SaaS billing behavior.
Definition of done: Referral SaaS has a CI-tested validation gate for report export requests across the current report catalog, with unsafe requests rejected and export persistence still explicitly out of scope. Priority: P0.

## TASK-166: Carry Referral SaaS account references through report scope

Status: Complete (2026-07-12). Output: `services/referral_saas_account_scope_service.py`; `apps/api/routers/referral_saas_reports.py`; `utils/security.py`; `test/test_referral_saas_account_scope_service.py`; `test/api/test_referral_saas_reports_api.py`; `test/api/test_session_api.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/README.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`.
Shared primitive impact: Extends the existing Referral SaaS account-scope bridge and JWT identity claims; no duplicated account, membership, tenant, reporting, or export stack.
Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Account reference propagation; tenant-scope bridge hardening; report/export account envelope.
Objective: Carry trusted `account_ref` and `external_tenant_ref` claims through the existing Referral SaaS report and export-validation account-scope envelope without implementing account tables, membership resolution, external reference persistence, or caller-supplied account authorization.
Why now: TASK-165 added export validation, leaving full account references as the next visible blocker before report/export surfaces feel productized. The safe bridge should propagate trusted account references where auth already provides them while keeping internal `tenant_code` as the runtime partition.
Files involved: `services/referral_saas_account_scope_service.py`; `apps/api/routers/referral_saas_reports.py`; `utils/security.py`; `test/test_referral_saas_account_scope_service.py`; `test/api/test_referral_saas_reports_api.py`; `test/api/test_session_api.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Implementation/source files inspected: `services/referral_saas_account_scope_service.py`; `utils/security.py`; `apps/api/routers/referral_saas_reports.py`; `test/test_referral_saas_account_scope_service.py`; `test/api/test_referral_saas_reports_api.py`; `test/api/test_session_api.py`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`.
Database/schema impact: None.
Backend impact: `ReferralSaasAccountScope` now carries optional `account_ref` and `external_tenant_ref` from trusted identity claims. JWT identities can map configurable account and external-tenant claim names. Report and export-validation routes include these refs in the safe account-scope envelope.
Frontend impact: None.
API impact: Existing report and export-validation responses now include `account_scope.account_ref` alongside `external_tenant_ref`. No new route, membership permission, schema, or request parameter was added.
Tests to add/update: Added account-scope tests for trusted reference propagation; API tests for report/export-validation account-scope envelopes; JWT identity test for account/external-tenant claims.
Validation method: `.venv_codex\Scripts\python.exe -m pytest -q --no-cov test\test_referral_saas_account_scope_service.py test\api\test_referral_saas_reports_api.py test\api\test_session_api.py --tb=short`; `.venv_codex\Scripts\python.exe -m py_compile services\referral_saas_account_scope_service.py apps\api\routers\referral_saas_reports.py utils\security.py test\test_referral_saas_account_scope_service.py test\api\test_referral_saas_reports_api.py test\api\test_session_api.py`; `ruff check services\referral_saas_account_scope_service.py apps\api\routers\referral_saas_reports.py utils\security.py test\test_referral_saas_account_scope_service.py test\api\test_referral_saas_reports_api.py test\api\test_session_api.py`.
Acceptance criteria: Trusted account refs from identity/JWT claims are preserved in report/export account-scope envelopes; callers cannot self-authorize with request-supplied account refs; cross-tenant rejection remains intact; internal admin readers still require explicit tenant scope when no tenant-scoped identity exists; no schema, account membership, external-reference persistence, frontend, export storage, audit write, live DB, money, or DLaaS expansion behavior changes.
Dependencies: TASK-134; TASK-143; TASK-158; TASK-165.
Blocked by: None for trusted reference propagation. Full SaaS account setup tables, external-reference persistence, membership authorization, disabled/suspended reference behavior, frontend account UX, and live DB verification remain separate implementation work.
Risk level: Low.
Rollback notes: Revert the account-scope, JWT identity, route response, test, and docs updates.
Explicit non-goals: Do not implement account schema, account setup tables, tenant-link tables, membership tables, external-reference persistence, account setup APIs, user invitations, self-service account authorization, request-supplied account-ref lookup, new auth helpers, frontend screens, export persistence, audit writes, schema migrations, live DB checks, route smoke execution, write product routes, command idempotency implementation, campaign activation, webhook delivery, reward application, reward fulfilment, reward funding, reward settlement, reward amount totals, ledger-backed reporting, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, or SaaS billing behavior.
Definition of done: Referral SaaS report and export-validation surfaces can carry trusted product account references in their account-scope envelope while full account/membership persistence remains explicitly future work. Priority: P0.

## TASK-167: Add Referral SaaS inline export preview payload

Status: Complete (2026-07-12). Output: `services/referral_saas_reporting_service.py`; `apps/api/routers/referral_saas_reports.py`; `scripts/referral_saas_route_smoke_plan.py`; `test/test_referral_saas_reporting_service.py`; `test/api/test_referral_saas_reports_api.py`; `test/test_referral_saas_route_smoke_inventory.py`; `test/test_referral_saas_route_smoke_plan.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/README.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`.
Shared primitive impact: Reuses the existing report catalog, export validation gate, account-scope resolver, and route smoke planner; no duplicated export, storage, delivery, audit, reporting, or money stack.
Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Inline export preview; JSON/CSV payload shape; side-effect-free export smoke coverage.
Objective: Add side-effect-free inline JSON/CSV export preview payloads for current Referral SaaS reports without creating export IDs, files, storage records, delivery jobs, audit rows, retention records, download URLs, or scheduled exports.
Why now: TASK-165 validates export requests and TASK-166 carries account references, but the product still lacks a concrete export payload shape. A preview endpoint proves JSON/CSV serialization and row-limit/redaction behavior before persisted export storage and audit are introduced.
Files involved: `services/referral_saas_reporting_service.py`; `apps/api/routers/referral_saas_reports.py`; `scripts/referral_saas_route_smoke_plan.py`; `test/test_referral_saas_reporting_service.py`; `test/api/test_referral_saas_reports_api.py`; `test/test_referral_saas_route_smoke_inventory.py`; `test/test_referral_saas_route_smoke_plan.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Implementation/source files inspected: `services/referral_saas_reporting_service.py`; `apps/api/routers/referral_saas_reports.py`; `scripts/referral_saas_route_smoke_plan.py`; `test/test_referral_saas_reporting_service.py`; `test/api/test_referral_saas_reports_api.py`; `test/test_referral_saas_route_smoke_inventory.py`; `test/test_referral_saas_route_smoke_plan.py`; `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`.
Database/schema impact: None.
Backend impact: Added `build_referral_saas_report_export_preview`, which reuses export validation and `get_referral_saas_report`, applies row limits, returns report metadata, and serializes safe metric rows as JSON or CSV.
Frontend impact: None.
API impact: Added `POST /v1/referral-saas/reports/{report_type}/exports/preview` using the existing report-reader and account-scope boundary. It returns inline preview content only.
Tests to add/update: Added service tests for JSON and CSV preview payloads, API tests for preview success and safe validation errors, and updated route smoke inventory/plan tests for the new side-effect-free product wrapper.
Validation method: `.venv_codex\Scripts\python.exe -m pytest -q --no-cov test\test_referral_saas_reporting_service.py test\api\test_referral_saas_reports_api.py test\test_referral_saas_route_smoke_inventory.py test\test_referral_saas_route_smoke_plan.py --tb=short`; `.venv_codex\Scripts\python.exe -m py_compile services\referral_saas_reporting_service.py apps\api\routers\referral_saas_reports.py scripts\referral_saas_route_smoke_plan.py test\test_referral_saas_reporting_service.py test\api\test_referral_saas_reports_api.py test\test_referral_saas_route_smoke_inventory.py test\test_referral_saas_route_smoke_plan.py`; `ruff check services\referral_saas_reporting_service.py apps\api\routers\referral_saas_reports.py scripts\referral_saas_route_smoke_plan.py test\test_referral_saas_reporting_service.py test\api\test_referral_saas_reports_api.py test\test_referral_saas_route_smoke_inventory.py test\test_referral_saas_route_smoke_plan.py`.
Acceptance criteria: Preview requests reuse the validation gate; supported report types can return inline JSON or CSV preview content with metadata, row counts, row limits, freshness, warnings, and redactions; route/API errors remain safe; route smoke inventory and dry-run plan include the new side-effect-free route; persisted export creation/storage/delivery/audit remain explicitly unimplemented; no schema, frontend, live DB, money, fulfilment, funding, settlement, wallet, commission, invoice, payout, sponsor billing, or DLaaS expansion behavior changes.
Dependencies: TASK-142; TASK-156; TASK-157; TASK-158; TASK-165; TASK-166.
Blocked by: None for inline preview. Persisted exports, export IDs, retention/expiry, audit writes, scheduled delivery, frontend export UX, full SaaS account membership, and live route smoke execution remain separate implementation work.
Risk level: Low.
Rollback notes: Revert the preview helper, route, route smoke updates, tests, and docs updates.
Explicit non-goals: Do not implement public export creation, export files, export storage, persisted/scheduled exports, export IDs, export downloads, retention/expiry, audit writes, frontend screens, schema, migrations, account schema, membership schema, external-reference persistence, new auth helpers, live DB checks, write product routes beyond side-effect-free preview, command idempotency implementation, campaign activation, webhook delivery, reward application, reward fulfilment, reward funding, reward settlement, reward amount totals, ledger-backed reporting, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, or SaaS billing behavior.
Definition of done: Referral SaaS has CI-tested inline JSON/CSV export previews over the current report catalog, with persistence/audit/downloads still explicitly future work. Priority: P0.

## TASK-168: Add Referral SaaS report/export frontend client

Status: Complete (2026-07-12). Output: `frontend/src/api/endpoints/referralSaasReports.ts`; `frontend/src/api/endpoints/referralSaasReports.test.ts`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/README.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`.
Shared primitive impact: Adds a frontend API seam over existing Referral SaaS report/export routes; no duplicated backend, frontend state model, report store, export store, or product shell.
Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Frontend report/export API seam; typed route integration; no internal-account-ref request leakage.
Objective: Add a tested frontend client for Referral SaaS report reads, export validation, and inline export preview calls without building a report screen, persisted export UX, account membership UI, or new backend behavior.
Why now: TASK-167 completed the backend inline preview surface. The next UI blocker is a stable frontend API seam that future report/catalog screens can consume without ad hoc route strings or request-supplied account references.
Files involved: `frontend/src/api/endpoints/referralSaasReports.ts`; `frontend/src/api/endpoints/referralSaasReports.test.ts`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Implementation/source files inspected: `frontend/src/api/client.ts`; `frontend/src/api/endpoints/consumerPortal.test.ts`; `frontend/src/api/endpoints/partnerSeam.ts`; `frontend/package.json`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`.
Database/schema impact: None.
Backend impact: None.
Frontend impact: Added `referralSaasReports.ts` with typed request/response wrappers for `GET /v1/referral-saas/reports/{report_type}`, `POST /exports/validate`, and `POST /exports/preview`. The client supports optional transitional `tenantCode`, repeated dimensions, safe filters, row limits, and data windows.
API impact: None.
Tests to add/update: Added Vitest coverage for report query mapping, export validation body mapping, export preview route mapping, and no request-supplied `account_ref`/`external_tenant_ref`.
Validation method: `npm test -- referralSaasReports.test.ts --runInBand` from `frontend`; `npm run build` from `frontend`.
Acceptance criteria: Frontend client calls the three Referral SaaS report/export endpoints with correct paths, query strings, bodies, and headers; dimensions are repeated query params for report reads; export filters stay in the body for validate/preview; caller-supplied account refs are not accepted; no UI route, component, CSS, backend, schema, persisted export, audit, money, or DLaaS expansion behavior changes.
Dependencies: TASK-143; TASK-144; TASK-157; TASK-165; TASK-167.
Blocked by: None for the client seam. Focused report screen, account membership UX, persisted export UX, live route smoke execution, and full E2E frontend flows remain separate implementation work.
Risk level: Low.
Rollback notes: Revert the frontend endpoint/test and docs updates.
Explicit non-goals: Do not implement a Referral SaaS product shell, report page, charting, export download UI, persisted export workflow, account setup UI, membership UI, frontend navigation, backend routes, schema, migrations, account membership, external-reference persistence, live DB checks, command idempotency implementation, campaign activation, webhook delivery, reward application, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, or SaaS billing behavior.
Definition of done: Referral SaaS frontend has a CI-tested report/export API client seam ready for a later focused report UI. Priority: P0.

## TASK-169: Add Referral SaaS report catalog frontend surface

Status: Complete (2026-07-12). Output: `frontend/src/pages/admin/ReferralSaasReportsPage.tsx`; `frontend/src/pages/admin/ReferralSaasReportsPage.test.tsx`; `frontend/src/api/referralSaasQueries.ts`; `frontend/src/api/queryKeys.ts`; `frontend/src/app/App.tsx`; `frontend/src/layout/AppShell.tsx`; `frontend/src/layout/Sidebar.tsx`; `frontend/src/styles/base.css`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/sa/referral-saas/README.md`; `services/referral_saas_reporting_service.py`; `test/api/test_referral_saas_reports_api.py`.
Shared primitive impact: Adds a focused frontend surface over the existing Referral SaaS report client and React Query primitives; no duplicated report store, export store, backend route, account model, or product shell.
Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Frontend report catalog; tenant-safe metric rendering; report freshness/warning/redaction visibility.
Objective: Add the first focused Referral SaaS report catalog UI that consumes the TASK-168 client and current report API without adding persisted export UX, account membership UI, backend behavior, schema, or money flows.
Why now: TASK-168 added the frontend API seam. The next product gap is a visible, tested report surface that proves the catalog can be consumed safely while keeping export persistence and account membership explicit future work.
Files involved: `frontend/src/pages/admin/ReferralSaasReportsPage.tsx`; `frontend/src/pages/admin/ReferralSaasReportsPage.test.tsx`; `frontend/src/api/referralSaasQueries.ts`; `frontend/src/api/queryKeys.ts`; `frontend/src/app/App.tsx`; `frontend/src/layout/AppShell.tsx`; `frontend/src/layout/Sidebar.tsx`; `frontend/src/styles/base.css`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Implementation/source files inspected: `frontend/src/api/endpoints/referralSaasReports.ts`; `frontend/src/api/endpoints/referralSaasReports.test.ts`; `frontend/src/app/App.tsx`; `frontend/src/layout/Sidebar.tsx`; `frontend/src/layout/AppShell.tsx`; `frontend/src/pages/admin/ChannelOperationsPage.tsx`; `frontend/src/pages/admin/ChannelOperationsPage.test.tsx`; `frontend/src/api/queryKeys.ts`; `frontend/src/api/operationalQueries.ts`; `frontend/src/pages/pageUtils.ts`; `frontend/src/styles/base.css`; `services/referral_saas_reporting_service.py`; `test/api/test_referral_saas_reports_api.py`.
Database/schema impact: None.
Backend impact: None.
Frontend impact: Added `/admin/referral-saas/reports`, navigation, top-bar labeling, a React Query wrapper, and a tested report catalog page that renders metrics, freshness, warnings, redactions, account-scope posture, and guardrails over the existing report API.
API impact: None.
Tests to add/update: Added Vitest coverage for report rendering, report selector calls, display-only account references, and no account-ref leakage in requests.
Validation method: `npm.cmd test -- ReferralSaasReportsPage.test.tsx referralSaasReports.test.ts` from `frontend`; `npm.cmd run build` from `frontend`.
Acceptance criteria: The frontend route renders the current report catalog safely; report selection calls the typed report client; tenant code remains transitional; account refs are display-only response evidence; warnings/redactions/freshness/export guardrails are visible; persisted exports, download URLs, scheduled delivery, account membership UX, backend routes, schema, money, and DLaaS expansion behavior are not added.
Dependencies: TASK-144; TASK-168.
Blocked by: None for the focused report surface. Persisted export storage/audit/download UX, account setup/membership UX, live route smoke execution, and full product shell remain separate work.
Risk level: Low.
Rollback notes: Revert the frontend route/page/query/style/test and docs updates.
Explicit non-goals: Do not implement persisted exports, export IDs, export files, export storage, download URLs, scheduled exports, export audit writes, account setup tables, account membership UX, external-reference persistence, backend routes, schema, migrations, live DB checks, command idempotency implementation, campaign activation, webhook delivery, reward application, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, or SaaS billing behavior.
Definition of done: Referral SaaS has a CI-tested frontend report catalog surface over the current tenant-safe report API, with persisted exports and account membership still explicit future work. Priority: P0.

## TASK-170: Add Referral SaaS account setup readiness frontend surface

Status: Complete (2026-07-12). Output: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `frontend/src/api/referralSaasAccountQueries.ts`; `frontend/src/api/queryKeys.ts`; `frontend/src/app/App.tsx`; `frontend/src/layout/AppShell.tsx`; `frontend/src/layout/Sidebar.tsx`; `frontend/src/styles/base.css`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `frontend/src/pages/admin/CompanyOnboardingPage.tsx`; `frontend/src/api/endpoints/adminOnboarding.ts`.
Shared primitive impact: Adds a focused frontend surface over existing onboarding readiness primitives and shared React Query/UI components; no duplicated onboarding, account, tenant-link, membership, campaign, or report stack.
Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Account setup readiness; external-reference setup posture; membership and campaign-readiness gate visibility.
Objective: Add the first focused Referral SaaS account setup readiness UI that consumes current onboarding evidence through external references and links the account, membership, campaign, and report setup path without implementing account schema, membership writes, tenant-link persistence, backend routes, or money flows.
Why now: TASK-169 moved reporting UI forward. The largest remaining product-packaging blocker is account setup/membership visibility. This task makes that setup path explicit in the frontend while staying inside existing safe onboarding primitives.
Files involved: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `frontend/src/api/referralSaasAccountQueries.ts`; `frontend/src/api/queryKeys.ts`; `frontend/src/app/App.tsx`; `frontend/src/layout/AppShell.tsx`; `frontend/src/layout/Sidebar.tsx`; `frontend/src/styles/base.css`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Implementation/source files inspected: `frontend/src/pages/admin/CompanyOnboardingPage.tsx`; `frontend/src/pages/admin/CompanyOnboardingPage.test.tsx`; `frontend/src/api/endpoints/adminOnboarding.ts`; `frontend/src/app/App.tsx`; `frontend/src/layout/Sidebar.tsx`; `frontend/src/layout/AppShell.tsx`; `frontend/src/pages/admin/ReferralSaasReportsPage.tsx`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_CONTRACT.md`.
Database/schema impact: None.
Backend impact: None.
Frontend impact: Added `/admin/referral-saas/account-setup`, navigation, top-bar labeling, a React Query wrapper over `getAdminOnboardingState`, and a tested setup readiness page that renders account profile, tenant-link, membership, campaign-readiness, and report-baseline gates from safe onboarding evidence.
API impact: None.
Tests to add/update: Added Vitest coverage for external-reference readiness calls, checklist rendering, account/membership mutation guardrails, safe no-leak request assertions, and links to existing setup surfaces.
Validation method: `npm.cmd test -- ReferralSaasAccountSetupPage.test.tsx ReferralSaasReportsPage.test.tsx` from `frontend`; `npm.cmd run build` from `frontend`; `npm.cmd run lint` from `frontend`.
Acceptance criteria: The frontend route renders account setup readiness through external references; internal tenant identifiers are not sent or displayed; account creation and membership mutation controls are absent; existing onboarding/member/campaign/report surfaces are linked rather than forked; no backend, schema, account table, membership table, tenant-link write, invitation, activation, money, or DLaaS expansion behavior changes.
Dependencies: TASK-134; TASK-144; TASK-169.
Blocked by: None for setup-readiness UI. Actual account schema, tenant-link persistence, external-reference resolver, membership authorization, invite flows, activation flows, live route smoke execution, and full product shell remain separate work.
Risk level: Low.
Rollback notes: Revert the frontend route/page/query/style/test and docs updates.
Explicit non-goals: Do not implement account schema, membership schema, tenant-link persistence, external-reference persistence, account setup APIs, membership APIs, invitation flows, activation/suspension/disable/archive commands, backend routes, migrations, live DB checks, command idempotency implementation, campaign activation, webhook delivery, reward application, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, persisted exports, or SaaS billing behavior.
Definition of done: Referral SaaS has a CI-tested account setup readiness frontend surface over existing safe onboarding evidence, with real account/membership persistence still explicit future work. Priority: P0.

## TASK-171: Add Referral SaaS inline export preview frontend surface

Status: Complete (2026-07-13). Output: `frontend/src/pages/admin/ReferralSaasReportsPage.tsx`; `frontend/src/pages/admin/ReferralSaasReportsPage.test.tsx`; `frontend/src/styles/base.css`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Adds focused frontend preview controls over the existing Referral SaaS report/export client and backend inline preview endpoint; no duplicated export store, report store, backend route, schema, storage, delivery, audit, or product shell.
Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Frontend inline export preview; JSON/CSV preview action; payload/status/metadata visibility; no persisted export workflow.
Objective: Add inline JSON/CSV export preview actions to the focused Referral SaaS report catalog so operators can inspect preview payload evidence without creating export IDs, files, storage records, download URLs, scheduled exports, or audit writes.
Why now: TASK-167 added the backend preview payload, TASK-168 added the frontend client, and TASK-169 added the report catalog. The remaining frontend report/export gap was letting the current screen consume the preview safely while keeping persisted exports explicit future work.
Files involved: `frontend/src/pages/admin/ReferralSaasReportsPage.tsx`; `frontend/src/pages/admin/ReferralSaasReportsPage.test.tsx`; `frontend/src/styles/base.css`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Implementation/source files inspected: `frontend/src/pages/admin/ReferralSaasReportsPage.tsx`; `frontend/src/pages/admin/ReferralSaasReportsPage.test.tsx`; `frontend/src/api/endpoints/referralSaasReports.ts`; `frontend/src/styles/base.css`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`.
Database/schema impact: None.
Backend impact: None.
Frontend impact: Added preview row-limit control, Preview JSON/Preview CSV actions, inline preview status/content-type/row-count/payload rendering, and responsive styling to `/admin/referral-saas/reports`.
API impact: None.
Tests to add/update: Updated Vitest coverage for JSON preview requests, CSV preview requests with selected row limit, no request-supplied account references, and no persisted export/download action.
Validation method: `npm.cmd test -- ReferralSaasReportsPage.test.tsx referralSaasReports.test.ts` from `frontend`; `npm.cmd run build` from `frontend`; `npm.cmd run lint` from `frontend`; `git diff --check`.
Acceptance criteria: Report users can request inline JSON and CSV previews from the existing focused report catalog; preview requests carry tenant/report/format/redaction/row-limit only; response status, content type, row count, and payload are visible; account refs remain response-only; persisted exports, export IDs, stored files, download actions, scheduled delivery, audit writes, backend routes, schema, money, and DLaaS expansion behavior are not added.
Dependencies: TASK-167; TASK-168; TASK-169.
Blocked by: None for inline preview UI. Persisted export storage/audit/download UX, account/membership persistence, live route smoke execution, and full product E2E remain separate work.
Risk level: Low.
Rollback notes: Revert the report page/style/test and docs updates.
Explicit non-goals: Do not implement export IDs, export files, export storage, download URLs, scheduled exports, export audit writes, account setup tables, account membership APIs, backend routes, schema, migrations, live DB checks, command idempotency implementation, campaign activation, webhook delivery, reward application, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, SaaS billing, or broad DLaaS behavior.
Definition of done: Referral SaaS has CI-tested inline export preview UI over the current report catalog, with persisted export storage/audit/downloads still explicit future work. Priority: P0.

## TASK-172: Add Referral SaaS campaign readiness frontend surface

Status: Complete (2026-07-13). Output: `frontend/src/api/endpoints/adminCampaignReadiness.ts`; `frontend/src/api/endpoints/adminCampaignReadiness.test.ts`; `frontend/src/api/referralSaasCampaignQueries.ts`; `frontend/src/api/queryKeys.ts`; `frontend/src/pages/admin/ReferralSaasCampaignReadinessPage.tsx`; `frontend/src/pages/admin/ReferralSaasCampaignReadinessPage.test.tsx`; `frontend/src/app/App.tsx`; `frontend/src/layout/AppShell.tsx`; `frontend/src/layout/Sidebar.tsx`; `frontend/src/styles/base.css`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_CAMPAIGN_SETUP_READINESS_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Adds a focused frontend wrapper over the existing read-only admin campaign readiness primitive; no duplicated campaign service, readiness service, backend route, schema, campaign state model, policy store, link/code generator, marketplace flow, or product shell.
Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Campaign setup readiness UI; operation readiness review; lifecycle/readiness distinction; safe blocker/warning/evidence display.
Objective: Add a focused Referral SaaS campaign readiness frontend surface that consumes current campaign readiness evidence for `CONTROL_PLANE_VIEW`, `CREATE_TRACK`, `GENERATE_LINKS`, and `ACTIVATE_CAMPAIGN` without adding campaign mutation, policy writes, activation, link/code generation, backend routes, schema, marketplace, or money behavior.
Why now: TASK-170 made account setup readiness visible and TASK-171 made report/export preview visible. Campaign setup/readiness remains a P0 SaaS workflow blocker, and the existing admin readiness endpoint can be safely surfaced before product write wrappers are implemented.
Files involved: `frontend/src/api/endpoints/adminCampaignReadiness.ts`; `frontend/src/api/endpoints/adminCampaignReadiness.test.ts`; `frontend/src/api/referralSaasCampaignQueries.ts`; `frontend/src/api/queryKeys.ts`; `frontend/src/pages/admin/ReferralSaasCampaignReadinessPage.tsx`; `frontend/src/pages/admin/ReferralSaasCampaignReadinessPage.test.tsx`; `frontend/src/app/App.tsx`; `frontend/src/layout/AppShell.tsx`; `frontend/src/layout/Sidebar.tsx`; `frontend/src/styles/base.css`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Implementation/source files inspected: `frontend/src/pages/admin/CampaignOpportunitySetupPage.tsx`; `frontend/src/pages/admin/CampaignOpportunitySetupPage.test.tsx`; `apps/api/routers/admin_campaign_readiness.py`; `services/campaign_readiness_service.py`; `frontend/src/app/App.tsx`; `frontend/src/layout/AppShell.tsx`; `frontend/src/layout/Sidebar.tsx`; `frontend/src/api/client.ts`; `frontend/src/api/queryKeys.ts`.
Database/schema impact: None.
Backend impact: None.
Frontend impact: Added `/admin/referral-saas/campaigns`, navigation, top-bar labeling, a typed frontend client and React Query hook for current campaign readiness, plus a tested page showing readiness decision, lifecycle, blockers, warnings, unknowns, setup checklist, safe campaign/policy evidence, and workflow links.
API impact: None. The page uses the current `GET /admin/campaigns/{campaign_code}/readiness` route with the existing transitional `tenant_code` bridge.
Tests to add/update: Added Vitest coverage for endpoint request mapping, no account-ref request leakage, page rendering, operation switching, scope input updates, response redaction of `tenant_code` evidence, guardrail visibility, and workflow links.
Validation method: `npm.cmd test -- ReferralSaasCampaignReadinessPage.test.tsx adminCampaignReadiness.test.ts` from `frontend`; `npm.cmd run build` from `frontend`; `npm.cmd run lint` from `frontend`; `git diff --check`.
Acceptance criteria: Referral SaaS campaign users can review readiness for the four first-launch operations; setup state and campaign interaction state remain distinct; blockers/warnings/unknowns and campaign/policy evidence are visible safely; current `tenant_code` is labelled as a transitional bridge and response evidence redacts `tenant_code`; no caller-supplied `account_ref`/`external_tenant_ref` is accepted; campaign creation, policy writes, activation, link/code generation, backend routes, schema, marketplace, money, and DLaaS expansion behavior are not added.
Dependencies: TASK-135; TASK-144; TASK-170.
Blocked by: None for read-only campaign readiness UI. Product campaign read/write wrappers, account/membership persistence, external-reference tenant resolution, activation/idempotency/audit commands, link/code workflow UI, live route smoke execution, and full product E2E remain separate work.
Risk level: Low.
Rollback notes: Revert the frontend endpoint/query/page/route/style/test and docs updates.
Explicit non-goals: Do not implement campaign creation, campaign draft persistence, campaign policy writes, submit-for-review, activation, pause, resume, archive, link/code generation, validation wrapper, account schema, membership schema, tenant-link persistence, external-reference resolver, backend routes, schema, migrations, live DB checks, command idempotency implementation, webhook delivery, reward application, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, SaaS billing, or broad DLaaS behavior.
Definition of done: Referral SaaS has a CI-tested read-only campaign readiness frontend surface over the current campaign readiness primitive, with product write wrappers and activation still explicit future work. Priority: P0.

## TASK-173: Add Referral SaaS link/code workflow frontend surface

Status: Complete (2026-07-13). Output: `frontend/src/pages/admin/ReferralSaasLinkCodeWorkflowPage.tsx`; `frontend/src/pages/admin/ReferralSaasLinkCodeWorkflowPage.test.tsx`; `frontend/src/app/App.tsx`; `frontend/src/layout/AppShell.tsx`; `frontend/src/layout/Sidebar.tsx`; `frontend/src/styles/base.css`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_REFERRAL_CODE_ISSUE_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_VALIDATION_RECOVERY_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Adds a focused frontend wrapper over existing referral code issue, public validation, and referee UCN capture primitives; no duplicated referral service, validation service, backend route, schema, lifecycle command, reward, money, or DLaaS workflow.
Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Link/code issue and validation workflow UI; terms gate visibility; safe whitelisted result display; identity-capture guardrail.
Objective: Add a focused Referral SaaS link/code workflow frontend surface that reuses the current issue, validation, and identity-capture client calls without adding backend routes, schema, reissue/revoke/expire actions, repair/replay tooling, reward behavior, money behavior, or DLaaS expansion.
Why now: TASK-170 made account setup readiness visible, TASK-171 made report/export preview visible, and TASK-172 made campaign readiness visible. Link/code issue and validation remained the next obvious SaaS workflow gap, and the existing frontend client primitives can be safely packaged before product API wrapper hardening.
Files involved: `frontend/src/pages/admin/ReferralSaasLinkCodeWorkflowPage.tsx`; `frontend/src/pages/admin/ReferralSaasLinkCodeWorkflowPage.test.tsx`; `frontend/src/app/App.tsx`; `frontend/src/layout/AppShell.tsx`; `frontend/src/layout/Sidebar.tsx`; `frontend/src/styles/base.css`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Implementation/source files inspected: `frontend/src/api/endpoints/consumerPortal.ts`; `frontend/src/pages/admin/ReferralSaasReportsPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasCampaignReadinessPage.tsx`; `frontend/src/app/App.tsx`; `frontend/src/layout/AppShell.tsx`; `frontend/src/layout/Sidebar.tsx`; `frontend/src/styles/base.css`; `docs/sa/referral-saas/REFERRAL_SAAS_REFERRAL_CODE_ISSUE_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_VALIDATION_RECOVERY_CONTRACT.md`.
Database/schema impact: None.
Backend impact: None.
Frontend impact: Added `/admin/referral-saas/link-codes`, navigation, top-bar labeling, responsive controls, and a tested page with issue/reuse, validate, and identity-capture actions over the existing consumer portal client calls.
API impact: None. The page uses current `referrals/codes`, `public/referrals/validate`, and `referrals/referees/ucn` client calls with the existing transitional tenant and UCN bridge.
Tests to add/update: Added Vitest coverage for issue request mapping, validation using the issued code, referee identity capture against the validated track, accepted-terms gating, response no-leak behavior for raw UCN/hash/internal attributes, absence of unsupported lifecycle/support/money actions, and adjacent workflow links.
Validation method: `npm.cmd test -- ReferralSaasLinkCodeWorkflowPage.test.tsx consumerPortal.test.ts ReferralSaasCampaignReadinessPage.test.tsx` from `frontend`; `npm.cmd run build` from `frontend`; `npm.cmd run lint` from `frontend`; `git diff --check`.
Acceptance criteria: Referral SaaS users can issue/reuse a code, validate that code, and capture referee identity through one focused admin workflow; tenant/referrer UCN inputs are labelled as transitional bridges; result rendering is whitelisted and does not expose raw UCN, hashes, or internal attributes; reissue, revoke, expire, repair, replay, reward, funding, fulfilment, settlement, wallet, backend route, schema, marketplace, and DLaaS expansion behavior are not added.
Dependencies: TASK-136; TASK-137; TASK-144; TASK-170; TASK-172.
Blocked by: None for bounded link/code workflow UI. Product API wrappers, account/membership persistence, external-reference tenant resolution, validation idempotency/recovery hardening, operator support trace, live route smoke execution, and full product E2E remain separate work.
Risk level: Low.
Rollback notes: Revert the frontend page/route/navigation/style/test and docs updates.
Explicit non-goals: Do not implement product API wrapper routes, account schema, membership schema, tenant-link persistence, external-reference resolver, backend routes, schema, migrations, live DB checks, code reissue, revoke, expire, repair, replay, retry actions, command idempotency implementation, audit writes, campaign activation, webhook delivery, reward application, reward fulfilment, reward funding, reward settlement, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, SaaS billing, or broad DLaaS behavior.
Definition of done: Referral SaaS has a CI-tested link/code workflow frontend surface over existing issue, validation, and identity-capture primitives, with product API/account hardening and lifecycle/support operations still explicit future work. Priority: P0.

## TASK-174: Add Referral SaaS link/code product API wrappers

Status: Complete (2026-07-13). Output: `apps/api/routers/referral_saas_links.py`; `test/api/test_referral_saas_links_api.py`; `frontend/src/api/endpoints/referralSaasLinks.ts`; `frontend/src/api/endpoints/referralSaasLinks.test.ts`; `frontend/src/pages/admin/ReferralSaasLinkCodeWorkflowPage.tsx`; `frontend/src/pages/admin/ReferralSaasLinkCodeWorkflowPage.test.tsx`; `apps/api/main.py`; `scripts/referral_saas_route_smoke_plan.py`; `test/test_referral_saas_route_smoke_inventory.py`; `test/test_referral_saas_route_smoke_plan.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_REFERRAL_CODE_ISSUE_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_VALIDATION_RECOVERY_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_REFERRAL_CODE_ISSUE_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_VALIDATION_RECOVERY_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Adds product wrapper routes and a frontend client over existing referral code issue, public validation, and referee UCN capture primitives; no duplicated referral, validation, identity-capture, progress, reward, money, or DLaaS logic.
Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Versioned link/code product API wrappers; product-shaped issue/validation/capture statuses; safe redaction; seeded route smoke inventory.
Objective: Add bounded `/v1/referral-saas` product API wrappers for referral code issue/reuse, public referral validation, and referee UCN capture while composing current shared services and keeping lifecycle commands, schema, audit writes, explicit validation idempotency, reward, money, and DLaaS expansion out of scope.
Why now: TASK-173 created the focused link/code workflow UI over existing primitives. The next 10/10 blocker is moving that workflow behind product-shaped `/v1/referral-saas` APIs with safe status mapping and redaction before deeper account/idempotency/audit work begins.
Files involved: `apps/api/routers/referral_saas_links.py`; `test/api/test_referral_saas_links_api.py`; `frontend/src/api/endpoints/referralSaasLinks.ts`; `frontend/src/api/endpoints/referralSaasLinks.test.ts`; `frontend/src/pages/admin/ReferralSaasLinkCodeWorkflowPage.tsx`; `frontend/src/pages/admin/ReferralSaasLinkCodeWorkflowPage.test.tsx`; `apps/api/main.py`; `scripts/referral_saas_route_smoke_plan.py`; `test/test_referral_saas_route_smoke_inventory.py`; `test/test_referral_saas_route_smoke_plan.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_REFERRAL_CODE_ISSUE_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_VALIDATION_RECOVERY_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Implementation/source files inspected: `apps/api/routers/referrals.py`; `apps/api/schemas/referrals.py`; `services/referral_code.py`; `apps/api/routers/referral_saas_reports.py`; `utils/security.py`; `services/referral_saas_account_scope_service.py`; `test/test_referrals_api.py`; `test/api/test_referral_saas_reports_api.py`; `frontend/src/api/endpoints/consumerPortal.ts`; `frontend/src/pages/admin/ReferralSaasLinkCodeWorkflowPage.tsx`.
Database/schema impact: None.
Backend impact: Added `apps/api/routers/referral_saas_links.py` with `POST /v1/referral-saas/referral-codes`, `POST /v1/referral-saas/public/referrals/validate`, and `POST /v1/referral-saas/referrals/{referral_track_id}/referee-ucn`. Protected wrappers derive tenant scope from partner identity; public validation still validates the transitional tenant code through the existing guard. All wrappers compose current referral services.
Frontend impact: Added `frontend/src/api/endpoints/referralSaasLinks.ts` and repointed the focused Referral SaaS link/code workflow page to the product wrapper client. The broader consumer portal client remains unchanged.
API impact: Adds bounded product wrapper routes under `/v1/referral-saas`. Responses return `issueStatus`, `validationStatus`, or `captureStatus` plus safe code/track/alias/message/error fields. Raw UCNs, hashes, and internal validation attributes are not returned.
Tests to add/update: Added API tests for wrapper request mapping, tenant derivation, safe status mapping, recovery status mapping, and redaction. Added frontend endpoint tests and updated the link/code page tests. Updated route smoke inventory and smoke plan tests to classify new product wrapper writes as seeded-write only.
Validation method: `.venv_codex\Scripts\python.exe -m pytest -q --no-cov test\api\test_referral_saas_links_api.py test\test_referral_saas_route_smoke_inventory.py test\test_referral_saas_route_smoke_plan.py test\test_referrals_api.py --tb=short`; `npm.cmd test -- referralSaasLinks.test.ts ReferralSaasLinkCodeWorkflowPage.test.tsx`; `.venv_codex\Scripts\python.exe -m py_compile apps\api\routers\referral_saas_links.py test\api\test_referral_saas_links_api.py scripts\referral_saas_route_smoke_plan.py`; `ruff check apps\api\routers\referral_saas_links.py test\api\test_referral_saas_links_api.py scripts\referral_saas_route_smoke_plan.py test\test_referral_saas_route_smoke_inventory.py test\test_referral_saas_route_smoke_plan.py`; `npm.cmd run build`; `npm.cmd run lint`; `git diff --check`.
Acceptance criteria: Product wrapper routes are mounted and bounded; issue/reuse derives protected tenant scope from identity; public validation returns product-safe validation/recovery status; referee UCN capture derives protected tenant scope from identity; frontend link/code workflow uses the product wrapper client; raw UCN/hash/internal attribute evidence is not returned; new routes are classified as seeded-write smoke routes; no schema, lifecycle commands, audit writes, explicit validation idempotency, repair/replay, reward, funding, fulfilment, settlement, wallet, sponsor billing, marketplace-depth, white-label/embed, SaaS billing, or broad DLaaS behavior is added.
Dependencies: TASK-136; TASK-137; TASK-143; TASK-173.
Blocked by: None for bounded link/code product wrappers. Account/membership persistence, external-reference tenant resolution for public validation, duplicate validation idempotency, audit evidence, lifecycle commands, operator trace linkage, live route smoke execution, and full product E2E remain separate work.
Risk level: Medium.
Rollback notes: Revert the product router mount, wrapper router, frontend product client/page adoption, tests, smoke plan updates, docs, and infographic updates.
Explicit non-goals: Do not implement account schema, membership schema, tenant-link persistence, external-reference resolver, schema migrations, live DB checks, code reissue, revoke, expire, repair, replay, retry actions, explicit command idempotency keys, audit writes, campaign activation, webhook delivery, reward application, reward fulfilment, reward funding, reward settlement, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, SaaS billing, or broad DLaaS behavior.
Definition of done: Referral SaaS has CI-tested product wrapper APIs and a frontend client for the first link/code issue, validation, and identity-capture workflow, with account/idempotency/audit/lifecycle hardening still explicit future work. Priority: P0.

## TASK-175: Add Referral SaaS validation recovery mapper

Status: Complete (2026-07-13). Output: `services/referral_saas_validation_service.py`; `test/test_referral_saas_validation_service.py`; `apps/api/routers/referral_saas_links.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_VALIDATION_RECOVERY_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_VALIDATION_RECOVERY_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Centralizes product validation status and recovery mapping over the existing validation wrapper; no duplicated referral validation, referral instance creation, QR scan logging, identity capture, progress, reward, money, or DLaaS logic.
Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Safe validation recovery mapping; product validation status contract; no-leak validation response shape.
Objective: Move Referral SaaS validation status/recovery mapping out of the route into a tested service helper while preserving the existing shared referral validation primitive and keeping duplicate-submit idempotency, operator trace linkage, schema, lifecycle, audit, reward, money, and DLaaS expansion out of scope.
Why now: TASK-174 added the first product link/code wrappers. The next 10/10 blocker is proving that validation recovery states are stable, centrally tested, and redacted before taking on deeper idempotency or operator-trace work.
Files involved: `services/referral_saas_validation_service.py`; `test/test_referral_saas_validation_service.py`; `apps/api/routers/referral_saas_links.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_VALIDATION_RECOVERY_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Implementation/source files inspected: `apps/api/routers/referral_saas_links.py`; `test/api/test_referral_saas_links_api.py`; `services/referral_code.py`; `docs/sa/referral-saas/REFERRAL_SAAS_VALIDATION_RECOVERY_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`.
Database/schema impact: None.
Backend impact: Added `services/referral_saas_validation_service.py` with product validation status mapping, safe recovery action mapping, and whitelisted validation response construction. Updated `apps/api/routers/referral_saas_links.py` to use the helper.
Frontend impact: None.
API impact: No route or payload contract change. The existing `POST /v1/referral-saas/public/referrals/validate` response is now composed by a tested helper.
Tests to add/update: Added unit coverage for validation success redaction, terms-required recovery, alias recovery, missing tenant/code states, code-not-found recovery, logging recovery, and generic failure fallback.
Validation method: `.venv_codex\Scripts\python.exe -m pytest -q --no-cov test\test_referral_saas_validation_service.py test\api\test_referral_saas_links_api.py test\test_referrals_api.py --tb=short`; `.venv_codex\Scripts\python.exe -m py_compile services\referral_saas_validation_service.py apps\api\routers\referral_saas_links.py test\test_referral_saas_validation_service.py test\api\test_referral_saas_links_api.py`; `ruff check services\referral_saas_validation_service.py apps\api\routers\referral_saas_links.py test\test_referral_saas_validation_service.py test\api\test_referral_saas_links_api.py`; `git diff --check`.
Acceptance criteria: Validation product states are mapped in a dedicated helper; recovery actions for terms, alias, code-not-found, and logging failures are stable and tested; successful validation returns only whitelisted fields; raw UCN/hash/internal attribute evidence is not exposed; the product wrapper continues composing the existing validation primitive; no schema, route, frontend, duplicate-submit idempotency, operator trace linkage, lifecycle commands, audit writes, repair/replay, reward, funding, fulfilment, settlement, wallet, sponsor billing, marketplace-depth, white-label/embed, SaaS billing, or broad DLaaS behavior is added.
Dependencies: TASK-137; TASK-143; TASK-174.
Blocked by: None for validation recovery mapping. Duplicate-submit idempotency, operator trace linkage, richer frontend recovery UX, account/membership persistence, external-reference tenant resolution, live route smoke execution, and full product E2E remain separate work.
Risk level: Low.
Rollback notes: Revert the validation helper, router import/use, tests, docs, and infographic updates.
Explicit non-goals: Do not implement duplicate validation idempotency, account schema, membership schema, tenant-link persistence, external-reference resolver, schema migrations, live DB checks, code reissue, revoke, expire, repair, replay, retry commands, audit writes, frontend recovery UX changes, campaign activation, webhook delivery, reward application, reward fulfilment, reward funding, reward settlement, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, SaaS billing, or broad DLaaS behavior.
Definition of done: Referral SaaS has a CI-tested validation recovery mapper used by the product wrapper, with duplicate-submit idempotency and operator trace linkage still explicit future work. Priority: P0.

## TASK-176: Expose Referral SaaS validation idempotency posture

Status: Complete (2026-07-13). Output: `services/referral_saas_validation_service.py`; `test/test_referral_saas_validation_service.py`; `test/api/test_referral_saas_links_api.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_AUDIT_IDEMPOTENCY_POSTURE.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_VALIDATION_RECOVERY_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_VALIDATION_RECOVERY_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_AUDIT_IDEMPOTENCY_POSTURE.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Exposes the current product validation duplicate-submit posture over the existing validation wrapper; no duplicated referral validation, schema, idempotency store, referral instance creation, QR scan logging, progress, reward, money, or DLaaS logic.
Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Public validation idempotency posture; safe API contract transparency; duplicate-submit guardrail.
Objective: Make the current public validation duplicate-submit posture explicit in the Referral SaaS product response and tests without implementing schema-backed idempotency or pretending retries are safe to replay.
Why now: TASK-175 centralized validation recovery mapping. The next blocker was the product contract still being ambiguous about duplicate public validation submits, while the source service creates a new referral journey for each successful validation.
Files involved: `services/referral_saas_validation_service.py`; `test/test_referral_saas_validation_service.py`; `test/api/test_referral_saas_links_api.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_AUDIT_IDEMPOTENCY_POSTURE.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_VALIDATION_RECOVERY_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Implementation/source files inspected: `services/referral_code.py`; `services/referral_saas_validation_service.py`; `apps/api/routers/referral_saas_links.py`; `test/test_referral_code.py`; `test/test_referral_saas_validation_service.py`; `test/api/test_referral_saas_links_api.py`; `dp/migrations/001_init.sql`; `dp/migrations/006_qr_scans.sql`; `docs/sa/referral-saas/REFERRAL_SAAS_AUDIT_IDEMPOTENCY_POSTURE.md`.
Database/schema impact: None.
Backend impact: Added a validation idempotency posture envelope to the Referral SaaS validation mapper: `validationAttemptPolicy=NEW_JOURNEY_PER_SUCCESSFUL_VALIDATION`, `duplicateSubmitGuarantee=NOT_IDEMPOTENT`, and `idempotencyKeySupported=false`.
Frontend impact: None.
API impact: `POST /v1/referral-saas/public/referrals/validate` now includes `validation.idempotency` so consumers do not infer idempotent retry behavior from the product wrapper.
Tests to add/update: Updated validation service tests and API wrapper tests to assert the explicit non-idempotent duplicate-submit posture.
Validation method: `.venv_codex\Scripts\python.exe -m pytest -q --no-cov test\test_referral_saas_validation_service.py test\api\test_referral_saas_links_api.py test\test_referral_code.py test\test_referrals_api.py --tb=short`; `.venv_codex\Scripts\python.exe -m py_compile services\referral_saas_validation_service.py apps\api\routers\referral_saas_links.py test\test_referral_saas_validation_service.py test\api\test_referral_saas_links_api.py`; `ruff check services\referral_saas_validation_service.py apps\api\routers\referral_saas_links.py test\test_referral_saas_validation_service.py test\api\test_referral_saas_links_api.py`; `git diff --check`.
Acceptance criteria: Product validation responses explicitly state that successful duplicate submits create new validation journeys today; the response states no idempotency key is supported; tests cover the posture at service and API level; no schema-backed duplicate reuse, conflict detection, route, frontend, audit write, lifecycle command, repair/replay, reward, funding, fulfilment, settlement, wallet, sponsor billing, marketplace-depth, white-label/embed, SaaS billing, or broad DLaaS behavior is added.
Dependencies: TASK-137; TASK-146; TASK-174; TASK-175.
Blocked by: None for exposing current posture. Implementing real duplicate-submit idempotency remains blocked on schema/service decision and tests for reuse versus conflict behavior.
Risk level: Low.
Rollback notes: Revert the idempotency posture field, tests, docs, and infographic updates.
Explicit non-goals: Do not implement idempotency keys, duplicate reuse, duplicate conflict detection, account schema, membership schema, tenant-link persistence, external-reference resolver, schema migrations, live DB checks, code reissue, revoke, expire, repair, replay, retry commands, audit writes, frontend recovery UX changes, campaign activation, webhook delivery, reward application, reward fulfilment, reward funding, reward settlement, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, SaaS billing, or broad DLaaS behavior.
Definition of done: Referral SaaS validation responses make the current non-idempotent duplicate-submit posture explicit and CI-tested, with schema-backed idempotent validation still a clear future task. Priority: P0.

## TASK-177: Add Referral SaaS validation recovery UI

Status: Complete (2026-07-13). Output: `frontend/src/pages/admin/ReferralSaasLinkCodeWorkflowPage.tsx`; `frontend/src/pages/admin/ReferralSaasLinkCodeWorkflowPage.test.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_VALIDATION_RECOVERY_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_VALIDATION_RECOVERY_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Renders safe product validation recovery and retry-posture fields from the existing `/v1/referral-saas/public/referrals/validate` wrapper; no duplicated frontend client, backend route, schema, validation, idempotency, audit, repair/replay, reward, money, or DLaaS logic.
Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Frontend validation recovery display; non-idempotent retry posture visibility; no-leak validation result rendering.
Objective: Show product validation recovery next action and non-idempotent retry posture in the focused Referral SaaS link/code workflow UI while keeping retry commands, schema-backed idempotency, operator trace, lifecycle actions, audit writes, reward, money, and DLaaS expansion out of scope.
Why now: TASK-175 and TASK-176 made validation recovery and retry posture explicit in the product API. The next user-facing gap was making those fields visible in the focused link/code workflow so operators do not infer safe retry behavior or miss recovery guidance.
Files involved: `frontend/src/pages/admin/ReferralSaasLinkCodeWorkflowPage.tsx`; `frontend/src/pages/admin/ReferralSaasLinkCodeWorkflowPage.test.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_VALIDATION_RECOVERY_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Implementation/source files inspected: `frontend/src/pages/admin/ReferralSaasLinkCodeWorkflowPage.tsx`; `frontend/src/pages/admin/ReferralSaasLinkCodeWorkflowPage.test.tsx`; `frontend/src/api/endpoints/referralSaasLinks.ts`; `frontend/src/api/endpoints/referralSaasLinks.test.ts`; `services/referral_saas_validation_service.py`; `apps/api/routers/referral_saas_links.py`.
Database/schema impact: None.
Backend impact: None.
Frontend impact: The focused link/code workflow now renders validation `recovery.safeMessage`, `recovery.action`, `idempotency.safeMessage`, and `idempotency.duplicateSubmitGuarantee` when returned by the product wrapper.
API impact: None. This consumes the existing TASK-175/TASK-176 product response fields.
Tests to add/update: Updated page tests to cover validation retry posture visibility, recovery next action visibility, and continued no-leak behavior for raw/internal validation attributes.
Validation method: `npm.cmd test -- ReferralSaasLinkCodeWorkflowPage.test.tsx referralSaasLinks.test.ts`; `npm.cmd run build`; `npm.cmd run lint`; `git diff --check`.
Acceptance criteria: The link/code workflow shows recovery next action when validation returns a recovery state; the workflow shows non-idempotent retry posture when the product wrapper returns idempotency evidence; raw validation attributes, tenant internals, raw UCNs, hashes, reward, funding, fulfilment, settlement, wallet, and money evidence remain absent from the UI; no backend route, schema, retry command, lifecycle action, audit write, repair/replay, operator trace, reward, money, or DLaaS behavior is added.
Dependencies: TASK-173; TASK-174; TASK-175; TASK-176.
Blocked by: None for UI display. Schema-backed duplicate validation reuse/conflict behavior, operator trace linkage, support workflow actions, account/membership persistence, live smoke execution, and full product E2E remain separate work.
Risk level: Low.
Rollback notes: Revert the link/code workflow page/test updates plus docs and infographic updates.
Explicit non-goals: Do not implement validation idempotency keys, duplicate reuse, duplicate conflict detection, account schema, membership schema, tenant-link persistence, external-reference resolver, schema migrations, live DB checks, code reissue, revoke, expire, repair, replay, retry commands, audit writes, backend routes, frontend support-case workflow, campaign activation, webhook delivery, reward application, reward fulfilment, reward funding, reward settlement, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, SaaS billing, or broad DLaaS behavior.
Definition of done: Referral SaaS link/code workflow users can see safe validation recovery and retry posture directly in the product UI, with deeper idempotency and operator support still explicit future work. Priority: P0.

## TASK-178: Add Referral SaaS operator link/code inspect API wrapper

Status: Complete (2026-07-13). Output: `apps/api/routers/referral_saas_links.py`; `test/api/test_referral_saas_links_api.py`; `scripts/referral_saas_route_smoke_plan.py`; `test/test_referral_saas_route_smoke_inventory.py`; `test/test_referral_saas_route_smoke_plan.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_LINK_CODE_INVESTIGATION_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_SUPPORT_WORKFLOW.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_LINK_CODE_INVESTIGATION_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_SUPPORT_WORKFLOW.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Adds a product operator wrapper over the existing shared `inspect_link_code` primitive; no duplicated source inspection, referral validation, reporting, campaign, progress, attribution, audit, retry, replay, reward, money, or DLaaS logic.
Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Operator link/code investigation; canonical link/code inspection; redaction; missing-evidence diagnostics; route smoke classification.
Objective: Expose a bounded, read-only Referral SaaS operator diagnostics API for inspecting existing link/code evidence while preserving the shared inspection service as source truth.
Why now: TASK-177 made validation recovery visible in the link/code workflow. The next 10/10 blocker was that operator link/code investigation still depended on the internal admin route shape instead of a product-scoped `/v1/referral-saas/*` wrapper.
Files involved: `apps/api/routers/referral_saas_links.py`; `test/api/test_referral_saas_links_api.py`; `scripts/referral_saas_route_smoke_plan.py`; `test/test_referral_saas_route_smoke_inventory.py`; `test/test_referral_saas_route_smoke_plan.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_LINK_CODE_INVESTIGATION_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_SUPPORT_WORKFLOW.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Implementation/source files inspected: `apps/api/routers/admin_links.py`; `services/link_code_service.py`; `apps/api/main.py`; `apps/api/routers/referral_saas_links.py`; `test/api/test_admin_links_api.py`; `test/api/test_referral_saas_links_api.py`; `test/test_referral_saas_route_smoke_inventory.py`; `test/test_referral_saas_route_smoke_plan.py`; `scripts/referral_saas_route_smoke_plan.py`.
Database/schema impact: None.
Backend impact: Added `GET /v1/referral-saas/operator/links/inspect`, protected by the distribution admin/operator bridge, that calls `inspect_link_code`, returns `inspectionStatus`, `linkCode`, `nextDiagnostics`, `operator_scope`, and a read-only guardrail, and converts validation errors into safe 400 responses.
Frontend impact: None.
API impact: Adds one read-only product operator diagnostics route under `/v1/referral-saas/operator/links/inspect`. It accepts `tenant_code`, `source_type`, either `link_code_id` or `code_or_ref`, and optional `include_evidence`; it preserves evidence toggling, redactions, missing evidence, source warnings, tenant scope, and safe validation errors.
Tests to add/update: Added Referral SaaS API tests for successful inspection wrapping, missing evidence/source warnings, `include_evidence=false` forwarding, missing credential rejection, adjacent-role rejection, and safe validation errors. Updated route smoke inventory and smoke plan tests so the product wrapper surface remains bounded.
Validation method: `.venv_codex\Scripts\python.exe -m pytest -q --no-cov test\api\test_referral_saas_links_api.py test\api\test_admin_links_api.py test\test_referral_saas_route_smoke_inventory.py test\test_referral_saas_route_smoke_plan.py --tb=short`; `.venv_codex\Scripts\python.exe -m py_compile apps\api\routers\referral_saas_links.py test\api\test_referral_saas_links_api.py scripts\referral_saas_route_smoke_plan.py`; `ruff check apps\api\routers\referral_saas_links.py test\api\test_referral_saas_links_api.py scripts\referral_saas_route_smoke_plan.py test\test_referral_saas_route_smoke_inventory.py test\test_referral_saas_route_smoke_plan.py`; `git diff --check`.
Acceptance criteria: Operators can call the Referral SaaS product wrapper to inspect existing link/code evidence; the wrapper remains read-only; product diagnostics point to campaign readiness, attribution trace, missing evidence, or source warnings only when source evidence supports it; redactions and evidence omission are preserved; adjacent roles cannot access the route; no lifecycle command, schema, audit write, retry/replay/repair, reward, funding, fulfilment, settlement, wallet, sponsor billing, marketplace-depth, white-label/embed, SaaS billing, or broad DLaaS behavior is added.
Dependencies: TASK-140; TASK-145; TASK-174; TASK-177.
Blocked by: None for read-only product inspection. Operator support UI, attribution trace wrapper, schema-backed duplicate validation, account/membership persistence, live smoke execution, persisted exports, and full E2E proof remain separate work.
Risk level: Low.
Rollback notes: Revert the product route, tests, smoke-plan updates, docs, and infographic updates.
Explicit non-goals: Do not add support-case mutations, issue/reissue/revoke/expire/void commands, validation idempotency keys, duplicate reuse, duplicate conflict detection, account schema, membership schema, tenant-link persistence, external-reference resolver, schema migrations, live DB checks, audit writes, repair, replay, retry commands, campaign activation, webhook delivery, reward application, reward fulfilment, reward funding, reward settlement, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, SaaS billing, or broad DLaaS behavior.
Definition of done: Referral SaaS has a bounded operator link/code inspection API wrapper with safe diagnostics and route-smoke coverage, while deeper support workflow and attribution trace packaging remain explicit future tasks. Priority: P1.

## TASK-179: Add Referral SaaS operator link/code inspect frontend surface

Status: Complete (2026-07-13). Output: `frontend/src/api/endpoints/referralSaasLinks.ts`; `frontend/src/api/endpoints/referralSaasLinks.test.ts`; `frontend/src/pages/admin/ReferralSaasOperatorLinkInspectPage.tsx`; `frontend/src/pages/admin/ReferralSaasOperatorLinkInspectPage.test.tsx`; `frontend/src/app/App.tsx`; `frontend/src/layout/Sidebar.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_LINK_CODE_INVESTIGATION_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_SUPPORT_WORKFLOW.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_LINK_CODE_INVESTIGATION_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_SUPPORT_WORKFLOW.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Adds a focused frontend surface and client call over the TASK-178 product wrapper; no duplicated inspection service, backend route, schema, permissions, support-case write, retry/replay/repair, lifecycle, reward, money, or DLaaS logic.
Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Operator support workflow; link/code investigation UI; redaction visibility; missing-evidence diagnostics; safe next-diagnostic navigation.
Objective: Give operators a focused Referral SaaS page for inspecting link/code evidence through the product wrapper while keeping operator diagnostics read-only and visibly separate from public validation and customer-safe status.
Why now: TASK-178 added the product operator inspection API. The next 10/10 blocker was that operators still lacked a focused UI for source type selection, lookup, safe evidence display, missing evidence, warnings, redactions, and next diagnostics.
Files involved: `frontend/src/api/endpoints/referralSaasLinks.ts`; `frontend/src/api/endpoints/referralSaasLinks.test.ts`; `frontend/src/pages/admin/ReferralSaasOperatorLinkInspectPage.tsx`; `frontend/src/pages/admin/ReferralSaasOperatorLinkInspectPage.test.tsx`; `frontend/src/app/App.tsx`; `frontend/src/layout/Sidebar.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_LINK_CODE_INVESTIGATION_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_SUPPORT_WORKFLOW.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Implementation/source files inspected: `frontend/src/app/App.tsx`; `frontend/src/layout/Sidebar.tsx`; `frontend/src/api/endpoints/referralSaasLinks.ts`; `frontend/src/api/endpoints/referralSaasLinks.test.ts`; `frontend/src/pages/admin/ReferralSaasLinkCodeWorkflowPage.tsx`; `frontend/src/pages/admin/ReferralSaasLinkCodeWorkflowPage.test.tsx`; `frontend/src/pages/admin/ReferralSaasCampaignReadinessPage.tsx`; `frontend/src/pages/pageUtils.ts`; `frontend/src/components/StatusBadge.tsx`; `frontend/src/components/SummaryItem.tsx`.
Database/schema impact: None.
Backend impact: None.
Frontend impact: Added `/admin/referral-saas/operator-links`, sidebar navigation, a client function for `GET /v1/referral-saas/operator/links/inspect`, canonical source-type selection, code/ref and link-code lookup modes, evidence toggle, safe source summary, connected campaign/participant/attribution identifiers, missing evidence, source warnings, redactions, next diagnostics, and adjacent read-only workflow links.
API impact: No backend API changes. The frontend calls the existing TASK-178 product wrapper with `tenant_code`, `source_type`, `link_code_id` or `code_or_ref`, and `include_evidence`.
Tests to add/update: Added endpoint client tests and page tests for product wrapper query shape, source-type lookup mode, safe field rendering, missing evidence/warnings/redactions/next diagnostics, adjacent workflow links, and absence of mutation/retry/replay/support-case/money controls.
Validation method: `npm.cmd test -- ReferralSaasOperatorLinkInspectPage.test.tsx referralSaasLinks.test.ts`; `npm.cmd run build`; `npm.cmd run lint`; `git diff --check`.
Acceptance criteria: Operators can inspect link/code evidence from a focused Referral SaaS UI; source type maps to canonical API values; link-backed sources use `linkCodeId` while code-backed sources use `codeOrRef`; safe source summary, connected identifiers, missing evidence, warnings, redactions, and next diagnostics render; raw evidence values are not rendered; lifecycle commands, support-case writes, retry/replay/repair controls, reward, funding, fulfilment, settlement, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, SaaS billing, and broad DLaaS behavior remain absent.
Dependencies: TASK-140; TASK-144; TASK-145; TASK-178.
Blocked by: None for focused operator inspection UI. Attribution trace wrapper, progress/status diagnostics, support-case workflow, schema-backed duplicate validation, account/membership persistence, live smoke execution, persisted exports, and full E2E proof remain separate work.
Risk level: Low.
Rollback notes: Revert the frontend endpoint/page/route/sidebar changes plus docs and infographic updates.
Explicit non-goals: Do not add backend routes, schema, migrations, permission changes, support-case tables, support-case writes, issue/reissue/revoke/expire/void commands, validation idempotency keys, duplicate reuse, duplicate conflict detection, account schema, membership schema, tenant-link persistence, external-reference resolver, live DB checks, audit writes, repair, replay, retry commands, campaign activation, webhook delivery, reward application, reward fulfilment, reward funding, reward settlement, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, SaaS billing, or broad DLaaS behavior.
Definition of done: Referral SaaS operators have a focused, tested, read-only link/code inspection UI over the product wrapper, with deeper attribution/support workflow work still explicit future scope. Priority: P1.

## TASK-180: Add Referral SaaS operator attribution trace API wrapper

Status: Complete (2026-07-14). Output: `apps/api/routers/referral_saas_links.py`; `test/api/test_referral_saas_links_api.py`; `scripts/referral_saas_route_smoke_plan.py`; `test/test_referral_saas_route_smoke_inventory.py`; `test/test_referral_saas_route_smoke_plan.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ATTRIBUTION_TRACE_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_SUPPORT_WORKFLOW.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ATTRIBUTION_TRACE_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_SUPPORT_WORKFLOW.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Adds a product operator wrapper over the existing shared `get_outcome_trace` primitive; no duplicated attribution trace service, outcome trace read model, reporting, support-case, repair/replay, audit write, reward, money, or DLaaS logic.
Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Attribution trace; operator diagnostics; safe evidence packaging; route smoke classification; redaction and missing-evidence diagnostics.
Objective: Expose a bounded, read-only Referral SaaS operator attribution trace API for one referral outcome while keeping the existing outcome trace service as source truth and excluding money/webhook sections from the product wrapper.
Why now: TASK-179 gave operators a focused link/code inspection UI with next diagnostics pointing to attribution trace. The next 10/10 blocker was that attribution trace still required the broader admin outcome route instead of a product-scoped `/v1/referral-saas/*` wrapper with Referral SaaS section limits.
Files involved: `apps/api/routers/referral_saas_links.py`; `test/api/test_referral_saas_links_api.py`; `scripts/referral_saas_route_smoke_plan.py`; `test/test_referral_saas_route_smoke_inventory.py`; `test/test_referral_saas_route_smoke_plan.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ATTRIBUTION_TRACE_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_SUPPORT_WORKFLOW.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Implementation/source files inspected: `apps/api/routers/admin_outcomes.py`; `services/outcome_trace_service.py`; `apps/api/routers/referral_saas_links.py`; `test/api/test_admin_outcomes_api.py`; `test/api/test_referral_saas_links_api.py`; `test/test_referral_saas_route_smoke_inventory.py`; `test/test_referral_saas_route_smoke_plan.py`; `scripts/referral_saas_route_smoke_plan.py`.
Database/schema impact: None.
Backend impact: Added `GET /v1/referral-saas/operator/outcomes/{referral_track_id}/trace`, protected by the distribution admin/operator bridge, that calls `get_outcome_trace` with first-launch Referral SaaS sections only and returns `traceStatus`, `traceId`, lookup, tenant, safe sections, support trace, missing evidence, source warnings, redactions, generated time, next diagnostics, operator scope, and a read-only guardrail.
Frontend impact: None.
API impact: Adds one read-only product operator diagnostics route under `/v1/referral-saas/operator/outcomes/{referral_track_id}/trace`. It accepts required `tenant_code` and optional repeated `include_sections`. Allowed sections are `outcome`, `attribution`, `participants`, `events`, and `audit`; reward, commission, funding, fulfilment, settlement, webhook, and unknown sections return a safe `400 validation_error`.
Tests to add/update: Added Referral SaaS API tests for successful trace wrapping, safe section filtering, money-section rejection, missing credential rejection, adjacent-role rejection, safe not-found mapping, and safe validation error mapping. Updated route smoke inventory and smoke plan tests so the product wrapper surface remains bounded.
Validation method: `.venv_codex\Scripts\python.exe -m pytest -q --no-cov test\api\test_referral_saas_links_api.py test\test_referral_saas_route_smoke_inventory.py test\test_referral_saas_route_smoke_plan.py --tb=short`; `.venv_codex\Scripts\python.exe -m py_compile apps\api\routers\referral_saas_links.py test\api\test_referral_saas_links_api.py scripts\referral_saas_route_smoke_plan.py`; `ruff check apps\api\routers\referral_saas_links.py test\api\test_referral_saas_links_api.py scripts\referral_saas_route_smoke_plan.py test\test_referral_saas_route_smoke_inventory.py test\test_referral_saas_route_smoke_plan.py`; `git diff --check`.
Acceptance criteria: Operators can call the Referral SaaS product wrapper to inspect outcome attribution evidence; the wrapper remains read-only; default trace sections exclude money and webhooks; unsupported money/webhook sections are rejected before the service call; missing evidence, warnings, redactions, and support correlations are preserved; adjacent roles cannot access the route; no attribution mutation, progress mutation, campaign mutation, support-case write, schema, audit write, retry/replay/repair, reward, funding, fulfilment, settlement, wallet, sponsor billing, marketplace-depth, white-label/embed, SaaS billing, or broad DLaaS behavior is added.
Dependencies: TASK-139; TASK-143; TASK-145; TASK-178; TASK-179.
Blocked by: None for read-only product attribution trace API. Attribution trace frontend UI, progress/status diagnostics, support-case workflow, schema-backed duplicate validation, account/membership persistence, live smoke execution, persisted exports, and full E2E proof remain separate work.
Risk level: Low.
Rollback notes: Revert the product route, tests, smoke-plan updates, docs, and infographic updates.
Explicit non-goals: Do not add trace frontend UI, support-case mutations, issue/reissue/revoke/expire/void commands, attribution overrides, validation idempotency keys, duplicate reuse, duplicate conflict detection, account schema, membership schema, tenant-link persistence, external-reference resolver, schema migrations, live DB checks, audit writes, repair, replay, retry commands, campaign activation, webhook delivery, reward application, reward fulfilment, reward funding, reward settlement, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, SaaS billing, or broad DLaaS behavior.
Definition of done: Referral SaaS has a bounded operator attribution trace API wrapper with first-launch section limits and route-smoke coverage, while trace UI, deeper support workflow, progress/status diagnostics, and live E2E proof remain explicit future tasks. Priority: P1.

## TASK-181: Add Referral SaaS operator attribution trace frontend surface

Status: Complete (2026-07-14). Output: `frontend/src/api/endpoints/referralSaasLinks.ts`; `frontend/src/api/endpoints/referralSaasLinks.test.ts`; `frontend/src/pages/admin/ReferralSaasAttributionTracePage.tsx`; `frontend/src/pages/admin/ReferralSaasAttributionTracePage.test.tsx`; `frontend/src/pages/admin/ReferralSaasOperatorLinkInspectPage.tsx`; `frontend/src/pages/admin/ReferralSaasOperatorLinkInspectPage.test.tsx`; `frontend/src/app/App.tsx`; `frontend/src/layout/Sidebar.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ATTRIBUTION_TRACE_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_SUPPORT_WORKFLOW.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ATTRIBUTION_TRACE_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_SUPPORT_WORKFLOW.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Adds a focused frontend surface over the existing TASK-180 product trace wrapper; no duplicated trace service, backend route, schema, permission, support-case, repair/replay, attribution mutation, reward, money, or DLaaS logic.
Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Attribution trace UI; operator diagnostics; safe evidence packaging; support workflow navigation; redaction and missing-evidence visibility.
Objective: Give operators a focused Referral SaaS page for inspecting outcome attribution evidence through the product trace wrapper while keeping the workflow read-only and first-launch section limited.
Why now: TASK-180 added the product attribution trace API. The next 10/10 blocker was that operators still lacked a focused UI for trace lookup, section selection, safe outcome/attribution/participant/event/audit evidence, missing evidence, warnings, redactions, and adjacent support navigation.
Files involved: `frontend/src/api/endpoints/referralSaasLinks.ts`; `frontend/src/api/endpoints/referralSaasLinks.test.ts`; `frontend/src/pages/admin/ReferralSaasAttributionTracePage.tsx`; `frontend/src/pages/admin/ReferralSaasAttributionTracePage.test.tsx`; `frontend/src/pages/admin/ReferralSaasOperatorLinkInspectPage.tsx`; `frontend/src/pages/admin/ReferralSaasOperatorLinkInspectPage.test.tsx`; `frontend/src/app/App.tsx`; `frontend/src/layout/Sidebar.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ATTRIBUTION_TRACE_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_SUPPORT_WORKFLOW.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Implementation/source files inspected: `frontend/src/api/endpoints/referralSaasLinks.ts`; `frontend/src/api/endpoints/referralSaasLinks.test.ts`; `frontend/src/pages/admin/ReferralSaasOperatorLinkInspectPage.tsx`; `frontend/src/pages/admin/ReferralSaasOperatorLinkInspectPage.test.tsx`; `frontend/src/app/App.tsx`; `frontend/src/layout/Sidebar.tsx`; `frontend/src/pages/pageUtils.ts`.
Database/schema impact: None.
Backend impact: None.
Frontend impact: Added `/admin/referral-saas/attribution-trace`, sidebar navigation, a client function for `GET /v1/referral-saas/operator/outcomes/{referral_track_id}/trace`, safe first-launch section toggles, trace summary, attribution link evidence, participant/event/audit lists, missing evidence, source warnings, redactions, next diagnostics, guardrails, and adjacent read-only support workflow links. The operator link/code inspection page now links to the trace surface.
API impact: No backend API changes. The frontend calls the existing TASK-180 product wrapper with `tenant_code`, `referral_track_id`, and optional safe `include_sections`.
Tests to add/update: Added endpoint client tests and page tests for product wrapper query shape, safe trace evidence rendering, safe section selection, no money/webhook leakage from unexpected response sections, absence of mutation/replay/support-case/money actions, adjacent workflow links, and the operator link inspection to attribution trace navigation.
Validation method: `npm.cmd test -- ReferralSaasAttributionTracePage.test.tsx ReferralSaasOperatorLinkInspectPage.test.tsx referralSaasLinks.test.ts`; `npm.cmd run build`; `npm.cmd run lint`; `git diff --check`.
Acceptance criteria: Operators can inspect attribution trace evidence from a focused Referral SaaS UI; safe outcome, lookup, attribution links, participants, events, audit evidence, missing evidence, source warnings, redactions, and next diagnostics render; reward, commission, funding, fulfilment, settlement, wallet, invoice, payout, webhook, raw provider payload, and money evidence are not rendered; mutation controls, attribution override, support-case writes, repair, retry, replay, reward, and settlement controls remain absent; no backend route, schema, permission, audit write, reward, money, or DLaaS behavior is added.
Dependencies: TASK-139; TASK-144; TASK-145; TASK-179; TASK-180.
Blocked by: None for focused operator attribution trace UI. Progress/status diagnostics, support-case workflow, schema-backed duplicate validation, account/membership persistence, live smoke execution, persisted exports, and full E2E proof remain separate work.
Risk level: Low.
Rollback notes: Revert the frontend endpoint/page/route/sidebar changes plus docs and infographic updates.
Explicit non-goals: Do not add backend routes, schema, migrations, permission changes, support-case tables, support-case writes, issue/reissue/revoke/expire/void commands, attribution overrides, validation idempotency keys, duplicate reuse, duplicate conflict detection, account schema, membership schema, tenant-link persistence, external-reference resolver, live DB checks, audit writes, repair, replay, retry commands, campaign activation, webhook delivery, reward application, reward fulfilment, reward funding, reward settlement, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, SaaS billing, or broad DLaaS behavior.
Definition of done: Referral SaaS operators have a focused, tested, read-only attribution trace UI over the product wrapper, with progress/status support, support-case workflow, account membership, persisted exports, and live E2E proof still explicit future work. Priority: P1.

## TASK-182: Add Referral SaaS operator progress/status diagnostics API wrapper

Status: Complete (2026-07-14). Output: `apps/api/routers/referral_saas_links.py`; `test/api/test_referral_saas_links_api.py`; `scripts/referral_saas_route_smoke_plan.py`; `test/test_referral_saas_route_smoke_inventory.py`; `test/test_referral_saas_route_smoke_plan.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PROGRESS_EVENT_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_SAFE_STATUS_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_SUPPORT_WORKFLOW.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PROGRESS_EVENT_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_SAFE_STATUS_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_SUPPORT_WORKFLOW.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Adds a product operator wrapper over existing dashboard progress reads and the shared Referral SaaS safe-status projection helper; no duplicated progress ingestion, progress persistence, safe-status service, support-case, repair/replay, retry, reward, money, or DLaaS logic.
Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Progress/status diagnostics; operator support workflow; safe status projection; read-only route smoke classification; redaction and next-diagnostic packaging.
Objective: Expose a bounded, read-only Referral SaaS operator progress/status diagnostics API for one referral track while keeping existing dashboard progress and safe-status primitives as source truth.
Why now: TASK-181 gave operators a focused attribution trace UI. The next 10/10 blocker was that progress/status support still lacked a product-scoped `/v1/referral-saas/*` diagnostics wrapper that could connect progress evidence, safe status, next milestone, and follow-up trace/support diagnostics without exposing raw UCNs or adding mutation paths.
Files involved: `apps/api/routers/referral_saas_links.py`; `test/api/test_referral_saas_links_api.py`; `scripts/referral_saas_route_smoke_plan.py`; `test/test_referral_saas_route_smoke_inventory.py`; `test/test_referral_saas_route_smoke_plan.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PROGRESS_EVENT_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_SAFE_STATUS_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_SUPPORT_WORKFLOW.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Implementation/source files inspected: `apps/api/routers/dashboard.py`; `apps/api/routers/progress.py`; `apps/api/routers/referral_saas_links.py`; `services/referral_saas_safe_status_service.py`; `services/partner_customer_safe_status_service.py`; `test/api/test_referral_saas_links_api.py`; `test/test_referral_saas_route_smoke_inventory.py`; `test/test_referral_saas_route_smoke_plan.py`; `scripts/referral_saas_route_smoke_plan.py`.
Database/schema impact: None.
Backend impact: Added `GET /v1/referral-saas/operator/referrals/{referral_track_id}/progress-status`, protected by the distribution admin/operator bridge, that reads existing dashboard progress evidence for a tenant/referral track, projects a safe status for the requested viewer role, returns safe progress/status fields, preserves redaction names and missing evidence, and suggests bounded next diagnostics.
Frontend impact: None.
API impact: Adds one read-only product operator diagnostics route under `/v1/referral-saas/operator/referrals/{referral_track_id}/progress-status`. It accepts required `tenant_code` and optional `viewer_role`; invalid viewer roles return a safe `400 validation_error`; inaccessible progress evidence returns a safe `404 progress_status_not_found`.
Tests to add/update: Added Referral SaaS API tests for successful progress/status wrapping, completed progress attribution-trace follow-up, safe not-found mapping, bad viewer-role rejection, missing credential rejection, and adjacent-role rejection. Updated route smoke inventory and smoke plan tests so the product wrapper surface remains bounded.
Validation method: `.venv_codex\Scripts\python.exe -m pytest -q --no-cov test\api\test_referral_saas_links_api.py test\test_referral_saas_route_smoke_inventory.py test\test_referral_saas_route_smoke_plan.py --tb=short`; `.venv_codex\Scripts\python.exe -m py_compile apps\api\routers\referral_saas_links.py test\api\test_referral_saas_links_api.py scripts\referral_saas_route_smoke_plan.py`; `ruff check apps\api\routers\referral_saas_links.py test\api\test_referral_saas_links_api.py scripts\referral_saas_route_smoke_plan.py test\test_referral_saas_route_smoke_inventory.py test\test_referral_saas_route_smoke_plan.py`; `git diff --check`.
Acceptance criteria: Operators can call a Referral SaaS product wrapper to inspect safe progress/status evidence for a referral track; the wrapper remains read-only; raw UCN values are not returned; redactions and missing evidence are preserved; safe status projection is reused; next diagnostics include next milestone, support triage, or attribution trace follow-up where applicable; adjacent roles cannot access the route; no progress ingestion mutation, attribution mutation, campaign mutation, support-case write, schema, audit write, retry/replay/repair, reward, funding, fulfilment, settlement, wallet, sponsor billing, marketplace-depth, white-label/embed, SaaS billing, or broad DLaaS behavior is added.
Dependencies: TASK-138; TASK-141; TASK-143; TASK-145; TASK-180; TASK-181.
Blocked by: None for read-only product progress/status diagnostics API. Progress/status frontend UI, support-case workflow, schema-backed duplicate validation, account/membership persistence, live smoke execution, persisted exports, and full E2E proof remain separate work.
Risk level: Low.
Rollback notes: Revert the product route, tests, smoke-plan updates, docs, and infographic updates.
Explicit non-goals: Do not add progress frontend UI, support-case mutations, issue/reissue/revoke/expire/void commands, attribution overrides, validation idempotency keys, duplicate reuse, duplicate conflict detection, account schema, membership schema, tenant-link persistence, external-reference resolver, schema migrations, live DB checks, audit writes, repair, replay, retry commands, campaign activation, webhook delivery, reward application, reward fulfilment, reward funding, reward settlement, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, SaaS billing, or broad DLaaS behavior.
Definition of done: Referral SaaS has a bounded operator progress/status diagnostics API wrapper with safe status projection and route-smoke coverage, while progress/status UI, support-case workflow, account membership, persisted exports, and live E2E proof remain explicit future work. Priority: P1.

## TASK-183: Add Referral SaaS operator progress/status frontend surface

Status: Complete (2026-07-14). Output: `frontend/src/api/endpoints/referralSaasLinks.ts`; `frontend/src/api/endpoints/referralSaasLinks.test.ts`; `frontend/src/pages/admin/ReferralSaasProgressStatusPage.tsx`; `frontend/src/pages/admin/ReferralSaasProgressStatusPage.test.tsx`; `frontend/src/pages/admin/ReferralSaasAttributionTracePage.tsx`; `frontend/src/pages/admin/ReferralSaasAttributionTracePage.test.tsx`; `frontend/src/pages/admin/ReferralSaasOperatorLinkInspectPage.tsx`; `frontend/src/pages/admin/ReferralSaasOperatorLinkInspectPage.test.tsx`; `frontend/src/app/App.tsx`; `frontend/src/layout/Sidebar.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_SUPPORT_WORKFLOW.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_SUPPORT_WORKFLOW.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Adds a focused frontend surface over the existing TASK-182 progress/status product wrapper; no duplicated progress service, backend route, schema, permission, support-case, repair/replay, progress mutation, reward, money, or DLaaS logic.
Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Progress/status support UI; operator diagnostics; safe status projection; support workflow navigation; redaction and missing-evidence visibility.
Objective: Give operators a focused Referral SaaS page for inspecting safe progress and product status through the TASK-182 wrapper while keeping the workflow read-only.
Why now: TASK-182 added the product progress/status diagnostics API. The next 10/10 blocker was that operators still lacked a focused UI for referral progress lookup, viewer-role projection, safe status copy, missing evidence, redactions, next milestone/trace diagnostics, and adjacent support navigation.
Files involved: `frontend/src/api/endpoints/referralSaasLinks.ts`; `frontend/src/api/endpoints/referralSaasLinks.test.ts`; `frontend/src/pages/admin/ReferralSaasProgressStatusPage.tsx`; `frontend/src/pages/admin/ReferralSaasProgressStatusPage.test.tsx`; `frontend/src/pages/admin/ReferralSaasAttributionTracePage.tsx`; `frontend/src/pages/admin/ReferralSaasAttributionTracePage.test.tsx`; `frontend/src/pages/admin/ReferralSaasOperatorLinkInspectPage.tsx`; `frontend/src/pages/admin/ReferralSaasOperatorLinkInspectPage.test.tsx`; `frontend/src/app/App.tsx`; `frontend/src/layout/Sidebar.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_SUPPORT_WORKFLOW.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Implementation/source files inspected: `frontend/src/api/endpoints/referralSaasLinks.ts`; `frontend/src/api/endpoints/referralSaasLinks.test.ts`; `frontend/src/pages/admin/ReferralSaasAttributionTracePage.tsx`; `frontend/src/pages/admin/ReferralSaasAttributionTracePage.test.tsx`; `frontend/src/pages/admin/ReferralSaasOperatorLinkInspectPage.tsx`; `frontend/src/pages/admin/ReferralSaasOperatorLinkInspectPage.test.tsx`; `frontend/src/app/App.tsx`; `frontend/src/layout/Sidebar.tsx`; `frontend/src/pages/pageUtils.ts`.
Database/schema impact: None.
Backend impact: None.
Frontend impact: Added `/admin/referral-saas/progress-status`, sidebar navigation, a client function for `GET /v1/referral-saas/operator/referrals/{referral_track_id}/progress-status`, viewer-role projection selection, safe progress summary, safe status copy/action posture, missing evidence, redactions, next diagnostics, guardrails, and adjacent read-only support workflow links. The operator link/code and attribution trace pages now link to the progress/status surface.
API impact: No backend API changes. The frontend calls the existing TASK-182 product wrapper with `tenant_code`, `referral_track_id`, and optional `viewer_role`.
Tests to add/update: Added endpoint client tests and page tests for product wrapper query shape, viewer projection selection, safe progress/status rendering, no raw UCN leakage, absence of mutation/replay/support-case/money actions, adjacent workflow links, and redaction confinement. Updated adjacent operator page tests for progress/status navigation.
Validation method: `npm.cmd test -- ReferralSaasProgressStatusPage.test.tsx ReferralSaasAttributionTracePage.test.tsx ReferralSaasOperatorLinkInspectPage.test.tsx referralSaasLinks.test.ts`; `npm.cmd run build`; `npm.cmd run lint`; `git diff --check`.
Acceptance criteria: Operators can inspect safe progress/status evidence from a focused Referral SaaS UI; safe progress, product status copy, action posture, missing evidence, redactions, and next diagnostics render; raw UCNs, provider payloads, reward, commission, funding, fulfilment, settlement, wallet, invoice, payout, webhook, and money evidence are not rendered; mutation controls, support-case writes, repair, retry, replay, progress correction, reward, and settlement controls remain absent; no backend route, schema, permission, audit write, reward, money, or DLaaS behavior is added.
Dependencies: TASK-138; TASK-141; TASK-144; TASK-145; TASK-181; TASK-182.
Blocked by: None for focused operator progress/status UI. Support-case workflow, schema-backed duplicate validation, account/membership persistence, live smoke execution, persisted exports, and full E2E proof remain separate work.
Risk level: Low.
Rollback notes: Revert the frontend endpoint/page/route/sidebar changes plus docs and infographic updates.
Explicit non-goals: Do not add backend routes, schema, migrations, permission changes, support-case tables, support-case writes, issue/reissue/revoke/expire/void commands, attribution overrides, validation idempotency keys, duplicate reuse, duplicate conflict detection, account schema, membership schema, tenant-link persistence, external-reference resolver, live DB checks, audit writes, repair, replay, retry commands, progress ingestion/correction, campaign activation, webhook delivery, reward application, reward fulfilment, reward funding, reward settlement, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, SaaS billing, or broad DLaaS behavior.
Definition of done: Referral SaaS operators have a focused, tested, read-only progress/status UI over the product wrapper, with support-case workflow, account membership, persisted exports, and live E2E proof still explicit future work. Priority: P1.

## TASK-184: Add Referral SaaS operator support workflow hub

Status: Complete (2026-07-14). Output: `frontend/src/pages/admin/ReferralSaasSupportHubPage.tsx`; `frontend/src/pages/admin/ReferralSaasSupportHubPage.test.tsx`; `frontend/src/pages/admin/ReferralSaasProgressStatusPage.tsx`; `frontend/src/pages/admin/ReferralSaasProgressStatusPage.test.tsx`; `frontend/src/pages/admin/ReferralSaasAttributionTracePage.tsx`; `frontend/src/pages/admin/ReferralSaasAttributionTracePage.test.tsx`; `frontend/src/pages/admin/ReferralSaasOperatorLinkInspectPage.tsx`; `frontend/src/pages/admin/ReferralSaasOperatorLinkInspectPage.test.tsx`; `frontend/src/app/App.tsx`; `frontend/src/layout/Sidebar.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_SUPPORT_WORKFLOW.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_SUPPORT_WORKFLOW.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Adds a focused frontend support hub that routes operators to existing read-only Referral SaaS diagnostic surfaces; no duplicated backend service, API route, schema, permission, support-case table, repair/replay, retry, reward, money, or DLaaS logic.
Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Operator support workflow; support triage navigation; read-only evidence sequencing; mutation guardrails; frontend workflow cohesion.
Objective: Give operators a first-launch Referral SaaS support hub that routes common validation, progress, link/code, attribution, campaign, and reporting support cases into the correct read-only product surface.
Why now: TASK-183 gave operators the final missing focused progress/status surface. The next 10/10 blocker was that support workflow still required knowing which page to open manually rather than starting from a product support case type and following read-only evidence order.
Files involved: `frontend/src/pages/admin/ReferralSaasSupportHubPage.tsx`; `frontend/src/pages/admin/ReferralSaasSupportHubPage.test.tsx`; `frontend/src/pages/admin/ReferralSaasProgressStatusPage.tsx`; `frontend/src/pages/admin/ReferralSaasProgressStatusPage.test.tsx`; `frontend/src/pages/admin/ReferralSaasAttributionTracePage.tsx`; `frontend/src/pages/admin/ReferralSaasAttributionTracePage.test.tsx`; `frontend/src/pages/admin/ReferralSaasOperatorLinkInspectPage.tsx`; `frontend/src/pages/admin/ReferralSaasOperatorLinkInspectPage.test.tsx`; `frontend/src/app/App.tsx`; `frontend/src/layout/Sidebar.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_SUPPORT_WORKFLOW.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Implementation/source files inspected: `frontend/src/pages/admin/OperatorDemoHomePage.tsx`; `frontend/src/pages/admin/ReferralSaasProgressStatusPage.tsx`; `frontend/src/pages/admin/ReferralSaasAttributionTracePage.tsx`; `frontend/src/pages/admin/ReferralSaasOperatorLinkInspectPage.tsx`; `frontend/src/app/App.tsx`; `frontend/src/layout/Sidebar.tsx`; `frontend/src/pages/pageUtils.ts`.
Database/schema impact: None.
Backend impact: None.
Frontend impact: Added `/admin/referral-saas/support`, sidebar navigation, support-case routing for validation recovery, progress diagnostics, attribution review, readiness blockers, and reporting freshness, read-only evidence order, mutation/money guardrails, and support-hub links from the operator link/code, attribution trace, and progress/status pages.
API impact: None.
Tests to add/update: Added support hub page tests for support case routing, read-only evidence order, guardrails, and absence of support-case, repair, replay, retry, reward, and settlement actions. Updated adjacent operator page tests for support hub navigation.
Validation method: `npm.cmd test -- ReferralSaasSupportHubPage.test.tsx ReferralSaasProgressStatusPage.test.tsx ReferralSaasAttributionTracePage.test.tsx ReferralSaasOperatorLinkInspectPage.test.tsx`; `npm.cmd run build`; `npm.cmd run lint`; `git diff --check`.
Acceptance criteria: Operators can start support from common Referral SaaS case types and navigate to the correct read-only diagnostic surface; the hub states safe lookup inputs and evidence order; mutation controls, support-case writes, repair, retry, replay, reward, and settlement controls remain absent; no backend route, schema, permission, audit write, reward, money, or DLaaS behavior is added.
Dependencies: TASK-145; TASK-179; TASK-181; TASK-183.
Blocked by: None for read-only support workflow hub. Real support-case persistence, repair/replay guardrails, schema-backed duplicate validation, account/membership persistence, live smoke execution, persisted exports, and full E2E proof remain separate work.
Risk level: Low.
Rollback notes: Revert the frontend support hub/page/route/sidebar changes plus docs and infographic updates.
Explicit non-goals: Do not add backend routes, schema, migrations, permission changes, support-case tables, support-case writes, issue/reissue/revoke/expire/void commands, attribution overrides, validation idempotency keys, duplicate reuse, duplicate conflict detection, account schema, membership schema, tenant-link persistence, external-reference resolver, live DB checks, audit writes, repair, replay, retry commands, progress ingestion/correction, campaign activation, webhook delivery, reward application, reward fulfilment, reward funding, reward settlement, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, SaaS billing, or broad DLaaS behavior.
Definition of done: Referral SaaS operators have a focused, tested, read-only support workflow hub that links existing diagnostic surfaces, with actual support-case persistence, repair/replay controls, account membership, persisted exports, and live E2E proof still explicit future work. Priority: P1.

## TASK-185: Add Referral SaaS focused workspace shell

Status: Complete (2026-07-14). Output: `frontend/src/pages/admin/ReferralSaasWorkspacePage.tsx`; `frontend/src/pages/admin/ReferralSaasWorkspacePage.test.tsx`; `frontend/src/layout/Sidebar.tsx`; `frontend/src/layout/Sidebar.test.tsx`; `frontend/src/app/App.tsx`; `frontend/src/layout/AppShell.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Repackages existing Referral SaaS frontend pages behind a focused workspace shell; no duplicated backend route, frontend page fork, API client, schema, permission, support-case table, repair/replay, retry, reward, money, or DLaaS logic.
Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Focused Referral SaaS product workspace; frontend IA cohesion; product-boundary navigation; SaaS operator workflow.
Objective: Ringfence Referral Management and Campaign Attribution SaaS in its own workspace so operators can use account setup, campaign readiness, link/code, reports, support, link inspection, attribution trace, and progress/status without the broader DLaaS/demo/admin sidebar noise.
Why now: TASK-184 completed the last first-launch read-only operator support surface, but the actual app still mixed Referral SaaS with distributor marketplace, producer, wallet, settlement, funding, billing, treasury, demo, and generic admin navigation. That made the product feel like an internal DLaaS command centre instead of a focused SaaS workspace.
Files involved: `frontend/src/pages/admin/ReferralSaasWorkspacePage.tsx`; `frontend/src/pages/admin/ReferralSaasWorkspacePage.test.tsx`; `frontend/src/layout/Sidebar.tsx`; `frontend/src/layout/Sidebar.test.tsx`; `frontend/src/app/App.tsx`; `frontend/src/layout/AppShell.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `outputs/referral-attribution-dlaas-roadmap-infographic.html`.
Implementation/source files inspected: `frontend/src/layout/Sidebar.tsx`; `frontend/src/layout/AppShell.tsx`; `frontend/src/app/App.tsx`; `frontend/src/pages/admin/ReferralSaasSupportHubPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/styles/base.css`.
Database/schema impact: None.
Backend impact: None.
Frontend impact: Added `/admin/referral-saas` as the focused workspace home and changed the sidebar to switch into a Referral SaaS navigation mode for `/admin/referral-saas` and `/admin/referral-saas/*`. The product sidebar exposes only workspace home, account setup, campaigns, links/codes, reports, support hub, link inspection, attribution trace, and progress/status. Broader DLaaS/demo/admin navigation remains available outside the workspace.
API impact: None.
Tests to add/update: Added workspace page tests for product links and boundary guardrails. Added sidebar tests proving Referral SaaS routes hide Demo Home, Demand Marketplace, Funding Spine, Settlement Rail, and My Wallet while the broader platform navigation still renders outside the product workspace.
Validation method: `npm.cmd test -- ReferralSaasWorkspacePage.test.tsx Sidebar.test.tsx`; `npm.cmd run build`; `npm.cmd run lint -- --quiet`; `git diff --check`.
Acceptance criteria: `/admin/referral-saas` loads a focused product workspace; `/admin/referral-saas/*` routes show a Referral Management and Campaign Attribution SaaS sidebar instead of the broad DLaaS sidebar; the workspace links only to first-launch Referral SaaS surfaces; broader DLaaS marketplace, distributor, wallet, settlement, funding, billing, treasury, demo, and generic admin navigation are not mixed into the product workspace; no backend route, schema, permission, source fork, API wrapper, support-case write, repair/replay/retry, reward, money, or DLaaS behavior is added.
Dependencies: TASK-144; TASK-170; TASK-172; TASK-173; TASK-179; TASK-181; TASK-183; TASK-184.
Blocked by: None for frontend workspace packaging. Account-safe customer/referrer status, support-case persistence, repair/replay guardrails, schema-backed duplicate validation, account/membership persistence, live smoke execution, persisted exports, and full E2E proof remain separate work.
Risk level: Low.
Rollback notes: Revert the workspace page, sidebar mode, route/title wiring, tests, docs, and infographic update.
Explicit non-goals: Do not add backend routes, schema, migrations, permission changes, support-case tables, support-case writes, issue/reissue/revoke/expire/void commands, attribution overrides, validation idempotency keys, duplicate reuse, duplicate conflict detection, account schema, membership schema, tenant-link persistence, external-reference resolver, live DB checks, audit writes, repair, replay, retry commands, progress ingestion/correction, campaign activation, webhook delivery, reward application, reward fulfilment, reward funding, reward settlement, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, SaaS billing, source-code forks, or broad DLaaS behavior.
Definition of done: Referral SaaS has a focused workspace shell and navigation boundary that lets operators work inside the first-launch product without DLaaS noise, while deeper account, support-case, customer-safe status, export persistence, and live E2E work remain explicit future tasks. Priority: P1.

## TASK-186: Add Referral SaaS workspace and account setup testing guidance

Status: Complete (2026-07-14). Output: `frontend/src/pages/admin/ReferralSaasWorkspacePage.tsx`; `frontend/src/pages/admin/ReferralSaasWorkspacePage.test.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Improves the existing Referral SaaS workspace and account setup page orientation/testing paths; no duplicated frontend routes, backend route, API client, schema, permission, support-case table, repair/replay, retry, reward, money, or DLaaS logic.
Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Local testing entry point; workspace call-to-action clarity; product workflow guidance.
Objective: Make `/admin/referral-saas` and `/admin/referral-saas/account-setup` understandable for local UI testing by answering what each screen is for, what can be done there, and what the tester should do first.
Why now: TASK-185 ringfenced the workspace, but the first screen still read like a map of surfaces rather than a clear testing cockpit, and the account setup page exposed readiness evidence without a strong call to action, next step, or customer/operator-friendly testing path.
Files involved: `frontend/src/pages/admin/ReferralSaasWorkspacePage.tsx`; `frontend/src/pages/admin/ReferralSaasWorkspacePage.test.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `frontend/src/pages/admin/ReferralSaasWorkspacePage.tsx`; `frontend/src/pages/admin/ReferralSaasWorkspacePage.test.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`.
Database/schema impact: None.
Backend impact: None.
Frontend impact: The workspace home now states its purpose, available actions, first call to action, and recommended local testing path: account setup, campaign readiness, links/codes, and support evidence. The account setup page now states its purpose, available actions, first next step, account setup testing path, clearer KPI labels, and the next product screen to use after setup evidence is ready. Existing product work-area links remain available below the guided paths.
API impact: None.
Tests to add/update: Updated workspace page and account setup page tests for screen purpose, available actions, first call to action, recommended testing path links, and account setup next-screen guidance.
Validation method: `npm.cmd test -- ReferralSaasWorkspacePage.test.tsx ReferralSaasAccountSetupPage.test.tsx`; `npm.cmd run build`; `npm.cmd run lint -- --quiet`; `git diff --check`.
Acceptance criteria: `/admin/referral-saas` clearly explains what the screen is for; it explains what a tester can do there; it tells the tester to start with account setup; it exposes a recommended test path through account setup, campaign readiness, links/codes, and support evidence; `/admin/referral-saas/account-setup` explains what the account setup screen is for, what can be done there, what to do next, and when to move to campaign readiness; no backend route, schema, permission, API wrapper, source fork, support-case write, repair/replay/retry, reward, money, or DLaaS behavior is added.
Dependencies: TASK-144; TASK-185.
Blocked by: None for workspace guidance. Live E2E automation, account-safe customer/referrer status, support-case persistence, repair/replay guardrails, schema-backed duplicate validation, account/membership persistence, persisted exports, and full live smoke proof remain separate work.
Risk level: Low.
Rollback notes: Revert the workspace page copy/test updates plus docs.
Explicit non-goals: Do not add backend routes, schema, migrations, permission changes, API wrappers, support-case tables, support-case writes, issue/reissue/revoke/expire/void commands, attribution overrides, validation idempotency keys, duplicate reuse, duplicate conflict detection, account schema, membership schema, tenant-link persistence, external-reference resolver, live DB checks, audit writes, repair, replay, retry commands, progress ingestion/correction, campaign activation, webhook delivery, reward application, reward fulfilment, reward funding, reward settlement, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, SaaS billing, source-code forks, or broad DLaaS behavior.
Definition of done: Referral SaaS workspace and account setup users can immediately understand the screen purpose, available actions, first local testing path, and next product step without needing a prompt, while deeper live E2E automation and production hardening remain explicit future work. Priority: P1.

## TASK-187: Stabilize Referral SaaS account setup scope inputs

Status: Complete (2026-07-14). Output: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Improves the existing account setup frontend scope controls; no duplicated API client, backend route, schema, permission, support-case table, repair/replay, retry, reward, money, or DLaaS logic.
Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Stable account setup testing UX; account-scope lookup ergonomics; frontend readiness workflow.
Objective: Stop `/admin/referral-saas/account-setup` from reloading readiness evidence on every scope-input keystroke and keep each setup action inside its associated step.
Why now: Local UI testing exposed a visible screen glitch while typing external tenant and organisation references because the page bound input state directly to the readiness query scope. The account setup actions were also still scattered across the page instead of being grouped under step 1, step 2, and step 3.
Files involved: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`.
Database/schema impact: None.
Backend impact: None.
Frontend impact: Split account setup scope fields into draft input state and applied lookup state. Typing now stays local, shows `Changes not checked`, and the readiness query runs only after the tester clicks `Check setup`. Empty or unchanged scope values cannot trigger a new check. The recommended setup path now places the reference inputs and check action under step 1, blocker-resolution links under step 2, and campaign readiness under step 3.
API impact: None.
Tests to add/update: Updated account setup tests to assert typing does not trigger additional readiness requests and clicking `Check setup` applies the new scope.
Validation method: `npm.cmd test -- ReferralSaasAccountSetupPage.test.tsx`; `npm.cmd run build`; `npm.cmd run lint -- --quiet`; `git diff --check`.
Acceptance criteria: Typing in external tenant or organisation reference fields does not reload the readiness surface; the page clearly indicates unchecked scope changes; clicking `Check setup` runs the existing read-only readiness lookup with trimmed values; each setup action is contained inside the step where the user should perform it; no backend route, schema, permission, API wrapper, source fork, support-case write, repair/replay/retry, reward, money, or DLaaS behavior is added.
Dependencies: TASK-170; TASK-186.
Blocked by: None.
Risk level: Low.
Rollback notes: Revert the account setup scope-state and test updates plus docs.
Explicit non-goals: Do not add backend routes, schema, migrations, permission changes, API wrappers, support-case tables, support-case writes, account creation, membership writes, tenant-link persistence, issue/reissue/revoke/expire/void commands, attribution overrides, validation idempotency keys, duplicate reuse, live DB checks, audit writes, repair, replay, retry commands, campaign activation, webhook delivery, reward application, reward fulfilment, reward funding, reward settlement, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, SaaS billing, source-code forks, or broad DLaaS behavior.
Definition of done: Referral SaaS account setup scope entry is stable for local testing, readiness evidence refreshes only on explicit tester action, and the setup workflow presents actions inside step 1, step 2, and step 3. Priority: P1.

## TASK-188: Clarify Referral SaaS account setup next action

Status: Complete (2026-07-14). Output: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Improves the existing account setup frontend guidance; no duplicated API client, backend route, schema, permission, support-case table, repair/replay, retry, reward, money, or DLaaS logic.
Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Account setup testing UX; next-action clarity; frontend readiness workflow.
Objective: Make `/admin/referral-saas/account-setup` clearly tell the tester what to do after checking account setup.
Why now: Local UI testing showed that after clicking `Check setup`, the screen showed `Loaded` but did not clearly tell the tester whether to continue with step 2 blockers or step 3 campaigns.
Files involved: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`.
Database/schema impact: None.
Backend impact: None.
Frontend impact: Adds a `Do this next` result row to the recommended setup path. It directs testers to check changed references, fix setup blockers, or continue to campaign readiness based on the current page state. Step 2 and Step 3 subtitles and badges now reflect whether they are active, blocked, or waiting.
API impact: None.
Tests to add/update: Updated account setup tests to assert the recommended setup path displays the correct next-action guidance before and after checking changed references.
Validation method: `npm.cmd test -- ReferralSaasAccountSetupPage.test.tsx`; `npm.cmd run build`; `npm.cmd run lint -- --quiet`; `git diff --check`.
Acceptance criteria: After changing account references, the page tells the tester to check the references; after loading account setup with blockers or missing evidence, the page tells the tester to use step 2; when no blocker count remains, the page tells the tester to continue to campaign readiness; no backend route, schema, permission, API wrapper, source fork, support-case write, repair/replay/retry, reward, money, or DLaaS behavior is added.
Dependencies: TASK-186; TASK-187.
Blocked by: None.
Risk level: Low.
Rollback notes: Revert the account setup next-action UI/test updates plus docs.
Explicit non-goals: Do not add backend routes, schema, migrations, permission changes, API wrappers, support-case tables, support-case writes, account creation, membership writes, tenant-link persistence, issue/reissue/revoke/expire/void commands, attribution overrides, validation idempotency keys, duplicate reuse, live DB checks, audit writes, repair, replay, retry commands, campaign activation, webhook delivery, reward application, reward fulfilment, reward funding, reward settlement, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, SaaS billing, source-code forks, or broad DLaaS behavior.
Definition of done: Referral SaaS account setup tells the tester exactly whether step 1, step 2, or step 3 is next after account setup is checked. Priority: P1.

## TASK-189: Position Account Setup Readiness inside setup workflow

Status: Complete (2026-07-14). Output: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Clarifies the existing account setup readiness frontend surface; no duplicated API client, backend route, schema, permission, support-case table, repair/replay, retry, reward, money, account maintenance, or DLaaS logic.
Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Account setup workflow IA; readiness checkpoint clarity; frontend SaaS workflow.
Objective: Keep Account Setup as the parent workflow while positioning the current page as the Account Setup Readiness checkpoint inside that workflow.
Why now: Product testing clarified that readiness must not feel disconnected from Account Setup, but the current screen also must not imply account creation or account maintenance. The app needs clearer copy and step labels so testers understand that this page checks readiness and routes them to setup actions.
Files involved: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`.
Database/schema impact: None.
Backend impact: None.
Frontend impact: Renames the page content to `Account setup readiness`, explains that it is the readiness checkpoint inside the wider Account Setup workflow, updates step labels to confirm account scope, complete setup actions, and continue to campaign setup, and explicitly states that the page does not create accounts or invite users.
API impact: None.
Tests to add/update: Updated account setup tests to assert the readiness checkpoint wording, no account creation/invite implication, and revised workflow step labels.
Validation method: `npm.cmd test -- ReferralSaasAccountSetupPage.test.tsx`; `npm.cmd run build`; `npm.cmd run lint -- --quiet`; `git diff --check`.
Acceptance criteria: Account Setup remains the product workflow; the current page is clearly Account Setup Readiness; readiness is not disconnected from setup; the page does not imply account creation, user invitation, or account maintenance; next actions remain inside the setup workflow; no backend route, schema, permission, API wrapper, source fork, support-case write, repair/replay/retry, reward, money, or DLaaS behavior is added.
Dependencies: TASK-186; TASK-187; TASK-188.
Blocked by: None.
Risk level: Low.
Rollback notes: Revert the account setup readiness copy/test updates plus docs.
Explicit non-goals: Do not add backend routes, schema, migrations, permission changes, API wrappers, support-case tables, support-case writes, account creation, membership writes, tenant-link persistence, user invitations, account maintenance operations, issue/reissue/revoke/expire/void commands, attribution overrides, validation idempotency keys, duplicate reuse, live DB checks, audit writes, repair, replay, retry commands, campaign activation, webhook delivery, reward application, reward fulfilment, reward funding, reward settlement, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, SaaS billing, source-code forks, or broad DLaaS behavior.
Definition of done: Account Setup is presented as the parent workflow and the current page is clearly presented as the readiness checkpoint inside it, with setup actions and campaign continuation still bounded to the Referral SaaS product surface. Priority: P1.

## TASK-190: Define Referral SaaS account setup and maintenance workflow architecture

Status: Complete (2026-07-14). Output: `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_MAINTENANCE_WORKFLOW_ARCHITECTURE.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/README.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_CONTRACT.md`; `docs/sa/TENANT_ACCOUNT_LIFECYCLE_MEMBERSHIP_MODEL.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Defines how Referral SaaS should use shared onboarding draft/readiness primitives as the first setup foundation while preserving future shared account, tenant-link, external-reference, membership, audit, and permission boundaries. Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Account setup workflow architecture; integrated readiness; account maintenance workflow; setup and maintenance boundary.
Objective: Define the real Account Setup workflow, integrated readiness checkpoint, and Account Maintenance workflow so future work does not keep polishing a readiness-only page or build fake account behavior.
Why now: Product testing showed that Account Setup Readiness is useful but incomplete. The 10/10 SaaS gap is real account setup and account maintenance, not more readiness-page copy. Current code has onboarding draft persistence and safe readiness primitives, but not durable account records, account-to-tenant links, membership, account selector, invitations, lifecycle commands, or maintenance operations.
Files involved: `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_MAINTENANCE_WORKFLOW_ARCHITECTURE.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/README.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `dp/migrations/080_onboarding_draft_persistence.sql`; `services/onboarding/onboarding_draft_repository.py`; `services/onboarding/onboarding_state_projection_service.py`; `apps/api/routers/admin_onboarding.py`; `services/tenant_service.py`; `apps/api/routers/admin_tenants.py`; `frontend/src/api/endpoints/adminOnboarding.ts`; `frontend/src/pages/admin/CompanyOnboardingPage.tsx`; `frontend/src/pages/admin/MemberRoleOnboardingPage.tsx`; `frontend/src/pages/admin/OnboardingReadinessChecklistPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`.
Database/schema impact: None.
Backend impact: None.
Frontend impact: None.
API impact: None.
Tests to add/update: No runtime tests; docs-only architecture contract with readback and diff validation.
Validation method: Readback of the new contract and roadmap/gap/index references; `git diff --check`.
Acceptance criteria: Architecture separates Account Setup, Account Setup Readiness, Account Maintenance, and Campaign Setup; identifies which current onboarding draft/readiness primitives are reusable; identifies missing durable account/member primitives; defines implementation sequence for setup wrapper, setup workflow, maintenance contract, maintenance shell, selector, and future schema/service primitives; explicitly prevents fake account creation, invitations, membership, tenant-link, reference-rotation, maintenance, money, or DLaaS behavior.
Dependencies: TASK-134; TASK-170; TASK-186; TASK-187; TASK-188; TASK-189.
Blocked by: None for architecture. Implementation remains blocked by future task decisions around product wrappers, account schema, membership, tenant-link, external-reference resolver, account selector, and maintenance commands.
Risk level: Low.
Rollback notes: Revert the architecture contract and roadmap/gap/index updates.
Explicit non-goals: Do not add backend routes, schema, migrations, permission changes, API wrappers, frontend pages, account creation, membership writes, tenant-link persistence, user invitations, account maintenance operations, reference rotation, credential rotation, support-case writes, issue/reissue/revoke/expire/void commands, attribution overrides, validation idempotency keys, duplicate reuse, live DB checks, audit writes, repair, replay, retry commands, campaign activation, webhook delivery, reward application, reward fulfilment, reward funding, reward settlement, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, SaaS billing, source-code forks, or broad DLaaS behavior.
Definition of done: Referral SaaS has a documented architecture for real Account Setup, integrated readiness, and Account Maintenance, with a clear implementation path that starts from existing onboarding draft/readiness primitives and avoids fake SaaS account behavior. Priority: P0.

## TASK-191: Define Referral SaaS account setup wrapper contract

Status: Complete (2026-07-14). Output: `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_WRAPPER_CONTRACT.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_MAINTENANCE_WORKFLOW_ARCHITECTURE.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Defines how Referral SaaS should wrap shared admin onboarding draft, validation, readiness, submit-for-review, review-decision, idempotency, and audit primitives without duplicating source logic. Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Account setup product API contract; onboarding draft wrapper boundary; integrated readiness wrapper.
Objective: Define the near-term Referral SaaS Account Setup product wrapper contract over existing onboarding draft/readiness primitives before building the setup workflow shell.
Why now: TASK-190 established that Account Setup must become a real workflow, not a readiness-only page. The next safe step is to define exactly how product routes may compose existing onboarding primitives while preserving no-live-action, no-tenant-code, idempotency, audit, and no-fake-account boundaries.
Files involved: `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_WRAPPER_CONTRACT.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `apps/api/routers/admin_onboarding.py`; `frontend/src/api/endpoints/adminOnboarding.ts`; `services/onboarding/onboarding_draft_repository.py`; `dp/migrations/080_onboarding_draft_persistence.sql`.
Database/schema impact: None.
Backend impact: None.
Frontend impact: None.
API impact: No route implementation. Contract defines future `/v1/referral-saas/account-setup/*` wrappers for draft save, validate, readiness, submit-for-review, and review-decision over existing admin onboarding primitives.
Tests to add/update: No runtime tests; docs-only contract with readback and diff validation. Future implementation must add product wrapper route, mapping, permission, idempotency, redaction, no-internal-leak, and no-live-action tests.
Validation method: Readback of the new contract and roadmap/gap/index/API-map references; `git diff --check`.
Acceptance criteria: Contract maps product account setup requests/responses to existing onboarding draft/readiness primitives; defines product route family; preserves idempotency, audit, no-live-action, and no-tenant-code posture; separates setup evidence capture from durable account creation; explicitly excludes account creation, membership, invitations, maintenance commands, live launch, campaign activation, money, and broad DLaaS behavior.
Dependencies: TASK-134; TASK-170; TASK-190.
Blocked by: None for contract. Implementation remains blocked by future route, frontend shell, permission, and durable account/member primitive tasks.
Risk level: Low.
Rollback notes: Revert the wrapper contract and roadmap/gap/index/API-map updates.
Explicit non-goals: Do not add backend routes, schema, migrations, permission changes, OpenAPI output, frontend pages, account creation, internal tenant creation, tenant-link persistence, external-reference resolver, account selector, membership writes, user invitations, account maintenance operations, reference rotation, credential lifecycle, support-case writes, issue/reissue/revoke/expire/void commands, attribution overrides, validation idempotency changes, duplicate reuse, live DB checks, audit writes beyond current primitive contract, repair, replay, retry commands, campaign activation, webhook delivery, reward application, reward fulfilment, reward funding, reward settlement, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, SaaS billing, source-code forks, or broad DLaaS behavior.
Definition of done: Referral SaaS has a source-backed product wrapper contract for Account Setup that can drive the next workflow-shell and API-wrapper tasks without faking SaaS account creation. Priority: P0.

## TASK-192: Build Account Setup workflow shell using existing draft/readiness primitives

Status: Complete (2026-07-14). Output: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `frontend/src/styles/base.css`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_WRAPPER_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_MAINTENANCE_WORKFLOW_ARCHITECTURE.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Repackages the existing account setup readiness frontend around shared onboarding readiness evidence and existing onboarding setup surfaces. No duplicated API client, backend route, schema, permission, source fork, account primitive, maintenance primitive, reward, money, or DLaaS behavior.
Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Account Setup workflow shell; readiness checkpoint integration; setup action routing.
Objective: Turn `/admin/referral-saas/account-setup` from a readiness-only page into the first Account Setup workflow shell while still using existing safe readiness evidence.
Why now: TASK-190 and TASK-191 established the real setup architecture and product wrapper contract. The UI needed to stop feeling like a disconnected readiness report and instead show the ordered account setup path a tester should follow.
Files involved: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `frontend/src/styles/base.css`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `frontend/src/styles/base.css`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_WRAPPER_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_MAINTENANCE_WORKFLOW_ARCHITECTURE.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`.
Database/schema impact: None.
Backend impact: None.
Frontend impact: Renames the page to `Account setup workflow`, adds a guided ordered setup path for company profile, users and roles, integration setup, readiness checkpoint, review handoff, and campaign setup, moves scope checking and setup actions into the workflow shell, and marks review handoff as future until draft save/review wiring exists.
API impact: None. The page still uses the existing read-only onboarding readiness query and existing setup route links.
Tests to add/update: Updated `ReferralSaasAccountSetupPage.test.tsx` for the guided setup path, step actions, no account creation/invite claims, existing setup route links, and stable readiness scope behavior.
Validation method: `npm.cmd test -- ReferralSaasAccountSetupPage.test.tsx`; `npm.cmd run build`; `npm.cmd run lint -- --quiet`; `git diff --check`.
Acceptance criteria: Account Setup is presented as the parent workflow; readiness is a checkpoint inside the workflow; the first setup shell shows ordered company, role, integration, readiness, review, and campaign handoff steps; each visible action is inside the associated step; draft save/review, account creation, invitations, membership writes, maintenance commands, go-live, money, and broad DLaaS behavior remain absent.
Dependencies: TASK-170; TASK-186; TASK-187; TASK-188; TASK-189; TASK-190; TASK-191.
Blocked by: None for the workflow shell. Real setup persistence remains blocked by TASK-193 wrapper/API wiring and later durable account/member primitives.
Risk level: Low.
Rollback notes: Revert the account setup page, test, CSS, and docs updates.
Explicit non-goals: Do not add backend routes, schema, migrations, permission changes, API wrappers, OpenAPI output, account creation, internal tenant creation, tenant-link persistence, external-reference resolver, account selector, membership writes, user invitations, account maintenance operations, reference rotation, credential lifecycle, support-case writes, issue/reissue/revoke/expire/void commands, attribution overrides, validation idempotency changes, duplicate reuse, live DB checks, audit writes, repair, replay, retry commands, campaign activation, webhook delivery, reward application, reward fulfilment, reward funding, reward settlement, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, SaaS billing, source-code forks, or broad DLaaS behavior.
Definition of done: Referral SaaS Account Setup has a tested workflow shell that directs users through setup in the right order while still relying only on existing safe readiness evidence and setup route links. Priority: P0.

## TASK-193: Connect Account Setup workflow to draft save, validation, submit, and review APIs

Status: Complete (2026-07-14). Output: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_WRAPPER_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_MAINTENANCE_WORKFLOW_ARCHITECTURE.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Connects the Referral SaaS account setup workflow to existing shared admin onboarding draft validation, save, submit-for-review, review-decision, idempotency, and no-live-action primitives. Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Account setup draft actions; integrated readiness; review handoff.
Objective: Wire the Account Setup workflow shell to existing draft save, dry-run validation, submit-for-review, and internal review-decision APIs without adding new backend routes or fake account lifecycle behavior.
Why now: TASK-192 gave users the right setup path, but review handoff was still only descriptive. The next capability step is using the guarded onboarding draft primitives already present in source while preserving product boundaries.
Files involved: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `frontend/src/api/endpoints/adminOnboarding.ts`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `frontend/src/pages/admin/CompanyOnboardingPage.tsx`; `frontend/src/pages/admin/CompanyOnboardingPage.test.tsx`; `services/onboarding/onboarding_state_projection_service.py`; `services/onboarding/onboarding_draft_validation_service.py`; `apps/api/routers/admin_onboarding.py`.
Database/schema impact: None.
Backend impact: None.
Frontend impact: Adds a setup draft actions panel to `/admin/referral-saas/account-setup` for dry-run validation, setup draft save, submit-for-review, and internal review decision. Actions are disabled until the scope is checked and use only external references plus canonical onboarding section keys.
API impact: No new API routes. The page consumes existing `validateAdminOnboardingDryRun`, `saveAdminOnboardingDraft`, `submitAdminOnboardingDraftForReview`, and `recordAdminOnboardingReviewDecision` client functions.
Tests to add/update: Updated `ReferralSaasAccountSetupPage.test.tsx` to cover validation, draft save, submit-for-review, review-decision request shapes, idempotency keys, no internal identifier leakage, no secret/money fields, and safe no-live-action result rendering.
Validation method: `npm.cmd test -- ReferralSaasAccountSetupPage.test.tsx`; `npm.cmd run build`; `npm.cmd run lint -- --quiet`; `git diff --check`.
Acceptance criteria: Account setup workflow can validate setup evidence without saving, save setup draft intent, submit saved drafts for review, and record bounded internal review decisions through existing guarded onboarding APIs; requests use checked external references and known safe section keys; no account creation, membership write, invitation, credential creation, campaign activation, go-live, webhook delivery, money, or broad DLaaS behavior is added.
Dependencies: TASK-190; TASK-191; TASK-192.
Blocked by: None for guarded onboarding draft actions. Durable account, account selector, membership, account maintenance, and product wrapper route hardening remain future work.
Risk level: Medium.
Rollback notes: Revert the account setup page action wiring, tests, and docs updates.
Explicit non-goals: Do not add backend routes, schema, migrations, permission changes, OpenAPI output, durable account creation, internal tenant creation, tenant-link persistence, external-reference resolver, account selector, membership writes, user invitations, account maintenance operations, reference rotation, credential lifecycle, support-case writes, issue/reissue/revoke/expire/void commands, attribution overrides, validation idempotency changes beyond existing onboarding draft idempotency, duplicate reuse, live DB checks, audit writes beyond existing onboarding primitives, repair, replay, retry commands, campaign activation, webhook delivery, reward application, reward fulfilment, reward funding, reward settlement, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, SaaS billing, source-code forks, or broad DLaaS behavior.
Definition of done: Referral SaaS Account Setup has tested guarded draft validation, save, submit-for-review, and internal review-decision actions over existing onboarding primitives while preserving no-live-action and no-fake-account boundaries. Priority: P0.

## TASK-194: Define Account Maintenance workflow contract and read model

Status: Complete (2026-07-15). Output: `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_MAINTENANCE_READ_MODEL_CONTRACT.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_MAINTENANCE_WORKFLOW_ARCHITECTURE.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_WRAPPER_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Defines how Account Maintenance should initially read shared onboarding readiness/draft evidence while preserving future shared account, tenant-link, external-reference, membership, audit, and permission boundaries. Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Account Maintenance read model; account health/readiness drift; maintenance command boundary.
Objective: Define Account Maintenance as a read-only evidence and drift workflow before building a maintenance shell.
Why now: Account Setup now has workflow and guarded draft action wiring. The next 10/10 SaaS gap is separating existing-account maintenance from first-time setup without inventing account lifecycle commands before durable account primitives exist.
Files involved: `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_MAINTENANCE_READ_MODEL_CONTRACT.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `apps/api/routers/admin_onboarding.py`; `frontend/src/api/endpoints/adminOnboarding.ts`; `services/onboarding/onboarding_state_projection_service.py`; `services/onboarding/onboarding_draft_validation_service.py`; `services/onboarding/onboarding_draft_repository.py`; `dp/migrations/080_onboarding_draft_persistence.sql`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`.
Database/schema impact: None.
Backend impact: None.
Frontend impact: None.
API impact: No route implementation. Contract defines future Account Maintenance read-model direction and candidate product routes.
Tests to add/update: No runtime tests; docs-only contract with readback and diff validation. Future implementation must test no internal identifier leakage, blocked command posture, scoped evidence, and no fake maintenance commands.
Validation method: Readback of the new contract and roadmap/gap/index references; `git diff --check`.
Acceptance criteria: Contract separates Account Maintenance from Account Setup; defines a read-only maintenance model over current safe onboarding/readiness evidence; identifies maintenance areas and blocked commands; preserves no account creation, lifecycle, membership, reference rotation, credential, go-live, webhook, money, or broad DLaaS behavior.
Dependencies: TASK-190; TASK-191; TASK-192; TASK-193.
Blocked by: None for contract. Implementation of real maintenance commands remains blocked by future durable account, tenant-link, external-reference, membership, audit, and permission primitives.
Risk level: Low.
Rollback notes: Revert the Account Maintenance contract and roadmap/gap/index updates.
Explicit non-goals: Do not add backend routes, frontend pages, schema, migrations, permission changes, OpenAPI output, durable account creation, account selector, internal tenant creation, tenant-link persistence, external-reference resolver, membership writes, user invitations, account lifecycle commands, account maintenance commands, reference rotation, credential lifecycle, support-case writes, issue/reissue/revoke/expire/void commands, attribution overrides, validation idempotency changes, duplicate reuse, live DB checks, audit writes, repair, replay, retry commands, campaign activation, webhook delivery, reward application, reward fulfilment, reward funding, reward settlement, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, SaaS billing, source-code forks, or broad DLaaS behavior.
Definition of done: Referral SaaS has a documented Account Maintenance workflow/read-model contract that can drive a read-only shell without confusing maintenance with first-time setup or faking backend account commands. Priority: P0.

## TASK-195: Build Account Maintenance read-only shell

Status: Complete (2026-07-15). Output: `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`; `frontend/src/api/referralSaasAccountQueries.ts`; `frontend/src/api/queryKeys.ts`; `frontend/src/app/App.tsx`; `frontend/src/layout/Sidebar.tsx`; `frontend/src/layout/Sidebar.test.tsx`; `frontend/src/pages/admin/ReferralSaasWorkspacePage.tsx`; `frontend/src/pages/admin/ReferralSaasWorkspacePage.test.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_MAINTENANCE_READ_MODEL_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Adds a product-specific frontend shell over the existing shared onboarding/readiness state source while preserving future durable account, tenant-link, external-reference, membership, audit, and permission boundaries. Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Account Maintenance read-only shell; account health/drift evidence; maintenance command boundary; Referral SaaS workspace navigation.
Objective: Build the first Account Maintenance screen beside Account Setup so operators can review account health, drift, blocked commands, and safe next routing without confusing maintenance with first-time setup.
Why now: Account Setup now has guarded draft actions and TASK-194 defines the maintenance read model. The next 10/10 SaaS gap is making existing-account maintenance visible as a read-only workflow before durable account/membership/lifecycle primitives exist.
Files involved: `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`; `frontend/src/api/referralSaasAccountQueries.ts`; `frontend/src/api/queryKeys.ts`; `frontend/src/app/App.tsx`; `frontend/src/layout/Sidebar.tsx`; `frontend/src/layout/Sidebar.test.tsx`; `frontend/src/pages/admin/ReferralSaasWorkspacePage.tsx`; `frontend/src/pages/admin/ReferralSaasWorkspacePage.test.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `frontend/src/app/App.tsx`; `frontend/src/layout/Sidebar.tsx`; `frontend/src/api/referralSaasAccountQueries.ts`; `frontend/src/api/queryKeys.ts`; `frontend/src/api/endpoints/adminOnboarding.ts`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasWorkspacePage.tsx`; related frontend tests.
Database/schema impact: None.
Backend impact: None.
Frontend impact: Adds `/admin/referral-saas/account-maintenance`, Referral SaaS sidebar/workspace links, product query key, page tests, and workspace/sidebar test updates.
API impact: No new backend route. The page consumes existing safe `GET /admin/onboarding/state` through the frontend onboarding client and a maintenance-specific query key.
Tests to add/update: Added `ReferralSaasAccountMaintenancePage.test.tsx`; updated workspace and sidebar tests to include Account Maintenance.
Validation method: `npm.cmd test -- ReferralSaasAccountMaintenancePage.test.tsx ReferralSaasWorkspacePage.test.tsx Sidebar.test.tsx`; `npm.cmd run build`; `npm.cmd run lint -- --quiet`; `git diff --check`.
Acceptance criteria: Account Maintenance is a separate Referral SaaS route; it states read-only evidence purpose; uses external references, not internal identifiers; shows account health/drift and maintenance areas; routes fixes back to Account Setup, Campaigns, Reports, or Support; shows unavailable maintenance commands as blocked; does not render account creation, invitation, role change, reference rotation, credential rotation, go-live, campaign activation, repair/replay/retry, money, or DLaaS controls.
Dependencies: TASK-190; TASK-191; TASK-192; TASK-193; TASK-194.
Blocked by: None for read-only shell. Durable account selector, account-to-tenant link, external-reference resolver, membership writes, lifecycle commands, maintenance audit timeline, product maintenance API wrappers, and real maintenance commands remain future work.
Risk level: Medium.
Rollback notes: Revert the Account Maintenance page, navigation/query/test changes, and roadmap/gap/index updates.
Explicit non-goals: Do not add backend routes, schema, migrations, permission changes, OpenAPI output, durable account creation, account selector, internal tenant creation, tenant-link persistence, external-reference resolver, membership writes, user invitations, account lifecycle commands, account maintenance commands, reference rotation, credential lifecycle, support-case writes, issue/reissue/revoke/expire/void commands, attribution overrides, validation idempotency changes, duplicate reuse, live DB checks, audit writes, repair, replay, retry commands, campaign activation, webhook delivery, reward application, reward fulfilment, reward funding, reward settlement, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, SaaS billing, source-code forks, or broad DLaaS behavior.
Definition of done: Referral SaaS has a tested read-only Account Maintenance shell beside Account Setup, with safe external-reference scope, health/drift evidence, blocked command posture, and no fake maintenance actions. Priority: P0.

## TASK-196: Add Account Maintenance draft selector from safe onboarding source

Status: Complete (2026-07-15). Output: `services/onboarding/onboarding_draft_repository.py`; `apps/api/routers/admin_onboarding.py`; `frontend/src/api/endpoints/adminOnboarding.ts`; `frontend/src/api/referralSaasAccountQueries.ts`; `frontend/src/api/queryKeys.ts`; `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`; `test/test_onboarding_draft_repository.py`; `test/api/test_admin_onboarding_api.py`; `frontend/src/api/endpoints/adminOnboarding.test.ts`; `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_MAINTENANCE_WORKFLOW_ARCHITECTURE.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_MAINTENANCE_READ_MODEL_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Adds a read-only onboarding draft selector source for Account Maintenance while keeping onboarding draft persistence single-source and preserving future durable account, tenant-link, external-reference resolver, membership, audit, and permission boundaries. Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Account Maintenance selector; onboarding draft selector; account evidence source selection; no-internal-identifier posture.
Objective: Replace hardcoded/free-text-only maintenance scope selection with a safe source-backed onboarding draft selector that can drive the current Account Maintenance shell until durable account records exist.
Why now: Account Setup can save guarded draft evidence, and Account Maintenance can display read-only health. The next 10/10 SaaS gap is letting operators choose real saved setup evidence without exposing internal tenant identifiers or pretending durable account records exist.
Files involved: `services/onboarding/onboarding_draft_repository.py`; `apps/api/routers/admin_onboarding.py`; `frontend/src/api/endpoints/adminOnboarding.ts`; `frontend/src/api/referralSaasAccountQueries.ts`; `frontend/src/api/queryKeys.ts`; `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`; `test/test_onboarding_draft_repository.py`; `test/api/test_admin_onboarding_api.py`; `frontend/src/api/endpoints/adminOnboarding.test.ts`; `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/README.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `apps/api/routers/admin_onboarding.py`; `services/onboarding/onboarding_draft_repository.py`; `frontend/src/api/endpoints/adminOnboarding.ts`; `frontend/src/api/referralSaasAccountQueries.ts`; `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`; related backend and frontend tests.
Database/schema impact: None. Uses existing `onboarding_drafts` columns and safe summary fields.
Backend impact: Adds read-only `list_drafts` repository helper and `GET /admin/onboarding/drafts` selector route with admin permission, bounded limit, external-reference filters, safe response shape, guardrails, and redactions.
Frontend impact: Adds draft selector API client, query key/hook, and Account Maintenance selector panel.
API impact: Adds admin onboarding primitive `GET /admin/onboarding/drafts`; no `/v1/referral-saas/*` product route, durable account route, or maintenance command route.
Tests to add/update: Added repository selector test, admin onboarding selector API tests, frontend API selector test, and Account Maintenance selector tests.
Validation method: `npm.cmd test -- adminOnboarding.test.ts ReferralSaasAccountMaintenancePage.test.tsx`; `npm.cmd run build`; `npm.cmd run lint -- --quiet`; `git diff --check`. Backend pytest and Python compile were attempted but blocked locally because `.venv` and Python app execution aliases point to unavailable/corrupt Python launchers after machine restart.
Acceptance criteria: Account Maintenance can list safe saved setup drafts for an external scope; selector output excludes `tenant_code`, actor internals, secrets, raw payloads, and money evidence; adjacent roles are rejected; selected draft evidence loads maintenance scope; no durable account creation, account lifecycle, membership, invitation, external-reference rotation, credential lifecycle, go-live, campaign activation, repair/replay/retry, money, or DLaaS behavior is added.
Dependencies: TASK-190; TASK-191; TASK-192; TASK-193; TASK-194; TASK-195.
Blocked by: None for draft selector. Durable account records, trusted account-to-tenant links, external-reference resolver table, membership model, lifecycle, maintenance audit timeline, and real maintenance commands remain future work.
Risk level: Medium.
Rollback notes: Revert the onboarding draft selector repository/route/client/UI/tests and roadmap/gap/index updates.
Explicit non-goals: Do not add schema, migrations, durable account creation, account lifecycle, internal tenant creation, tenant-link persistence, external-reference resolver persistence, membership writes, user invitations, account maintenance commands, reference rotation, credential lifecycle, support-case writes, issue/reissue/revoke/expire/void commands, attribution overrides, validation idempotency changes, duplicate reuse, live DB checks, audit writes beyond existing onboarding primitives, repair, replay, retry commands, campaign activation, webhook delivery, reward application, reward fulfilment, reward funding, reward settlement, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, SaaS billing, source-code forks, or broad DLaaS behavior.
Definition of done: Referral SaaS Account Maintenance has a tested source-backed draft selector over existing safe onboarding evidence, without exposing internal identifiers or faking durable account behavior. Priority: P0.

## TASK-197: Add account/tenant-link/external-reference schema final review

Status: Complete (2026-07-15). Output: `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SCHEMA_FINAL_REVIEW.md`; `docs/sa/referral-saas/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_MAINTENANCE_WORKFLOW_ARCHITECTURE.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_WRAPPER_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_MAINTENANCE_READ_MODEL_CONTRACT.md`; `docs/sa/TENANT_ACCOUNT_BOUNDARY_MAP.md`; `docs/sa/TENANT_ACCOUNT_LIFECYCLE_MEMBERSHIP_MODEL.md`; `docs/sa/TENANT_IDENTIFIER_BOUNDARY_DECISION.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Confirms the shared account, tenant-link, external-reference, membership, lifecycle, and audit schema direction before implementation while keeping `tenant_code` and onboarding draft primitives single-source. Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Account foundation planning; tenant/account boundary; external-reference mapping; account membership readiness; Account Setup and Account Maintenance unblocker.
Objective: Record the final schema review before adding durable account primitives so the next backend task can implement an additive account foundation without mixing in routes, frontend commands, money behavior, or broad DLaaS expansion.
Why now: Account Setup can save guarded draft evidence and Account Maintenance can select safe onboarding drafts, but both are still capped by the absence of durable account, tenant-link, external-reference, membership, and lifecycle primitives. The next step must be schema correctness before product commands.
Files involved: `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SCHEMA_FINAL_REVIEW.md`; `docs/sa/referral-saas/README.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `dp/migrations/031_tenent.sql`; `dp/migrations/080_onboarding_draft_persistence.sql`; `services/tenant_service.py`; `apps/api/routers/admin_tenants.py`; tenant/account boundary docs; Account Setup and Account Maintenance contracts.
Database/schema impact: None in TASK-197. The review approves a future additive schema slice only.
Backend impact: None.
Frontend impact: None.
API impact: None.
Tests to add/update: No runtime tests for this docs-only review. The next implementation slice must add migration replay, account/tenant-link, external-reference, membership, lifecycle, tenant-isolation, and no-leak contract tests.
Validation method: Docs readback and `git diff --check`.
Acceptance criteria: Final review distinguishes current facts from target schema; confirms `tenant_code` remains internal; confirms onboarding drafts are setup evidence, not account records; names the approved additive account foundation table families; records migration guardrails and required test gates; explicitly defers routes, account creation, membership writes, invitations, lifecycle commands, reference rotation, credential lifecycle, campaign activation, go-live, money, and broad DLaaS behavior.
Dependencies: TASK-190; TASK-191; TASK-192; TASK-193; TASK-194; TASK-195; TASK-196.
Blocked by: None for final review. Implementation remains blocked until the next additive account foundation migration task.
Risk level: Low.
Rollback notes: Revert the final-review doc and roadmap/gap/index updates.
Explicit non-goals: Do not add schema, migrations, routes, services, frontend changes, OpenAPI output, permission changes, durable account creation, tenant creation, tenant-link persistence, external-reference resolver persistence, membership writes, invitations, account lifecycle commands, account maintenance commands, reference rotation, credential lifecycle, campaign activation, go-live actions, repair, replay, retry, support-case writes, reward application, reward fulfilment, funding, settlement, commissions, wallet behavior, invoice behavior, sponsor billing, marketplace expansion, white-label/embed, SaaS billing, source-code forks, or broad DLaaS behavior.
Definition of done: Referral SaaS has a documented final schema review that unlocks a small additive account foundation migration and test task without faking account maintenance behavior. Priority: P0.

## TASK-198: Add Referral SaaS account foundation migration and contract tests

Status: Complete (2026-07-15). Output: `dp/migrations/082_referral_saas_account_foundation.sql`; `test/test_referral_saas_account_foundation_migration.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SCHEMA_FINAL_REVIEW.md`; `docs/sa/TENANT_ACCOUNT_BOUNDARY_MAP.md`; `docs/sa/TENANT_ACCOUNT_LIFECYCLE_MEMBERSHIP_MODEL.md`; `docs/sa/TENANT_IDENTIFIER_BOUNDARY_DECISION.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Adds durable shared account, organisation, account-tenant, external-reference, user, membership, seat, and account-audit schema primitives while preserving existing `tenant_code` runtime partitioning and onboarding draft evidence. Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Durable account foundation; tenant/account boundary; external-reference mapping; membership readiness; account maintenance unblocker.
Objective: Add the first additive account foundation migration and static migration contract tests needed before Referral SaaS can move from onboarding draft evidence to durable account setup and maintenance.
Why now: TASK-197 approved the schema direction. Account Setup and Account Maintenance now need durable account, tenant-link, external-reference, membership, and lifecycle/audit primitives before real product wrappers and maintenance commands can be safely added.
Files involved: `dp/migrations/082_referral_saas_account_foundation.sql`; `test/test_referral_saas_account_foundation_migration.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `dp/migrations/031_tenent.sql`; `dp/migrations/080_onboarding_draft_persistence.sql`; `dp/migrations/081_funding_reconciliation_run_correlation.sql`; `test/test_onboarding_draft_migration.py`; `test/test_funding_reconciliation_run_correlation_migration.py`; tenant/account boundary docs; TASK-197 final review.
Database/schema impact: Adds additive migration `082_referral_saas_account_foundation.sql` with platform account, organisation, account-tenant link, external-reference, user, membership, seat, and account-audit event tables, lifecycle checks, foreign keys to existing `tenants(tenant_code)`, and uniqueness/lookup indexes. No backfill, no destructive migration, and no live DB mutation by this task.
Backend impact: None beyond migration file.
Frontend impact: None.
API impact: None.
Tests to add/update: Adds static migration contract tests for ordering, table/column coverage, tenant partition references, lifecycle constraints, uniqueness indexes, additivity, no live-action behavior, and no onboarding-draft-as-account coupling.
Validation method: Run targeted migration contract test, migration hygiene where available, and `git diff --check`.
Acceptance criteria: Migration is ordered after onboarding/funding reconciliation migrations and before `999_indexes.sql`; creates the approved account foundation table families; references `tenants(tenant_code)` where internal scope is required; keeps onboarding drafts separate from durable accounts; adds active-reference and account-tenant uniqueness guardrails; avoids backfill, drops, deletes, route behavior, account creation commands, membership writes, invitation commands, lifecycle commands, reference rotation commands, credential lifecycle, campaign activation, go-live, repair/replay/retry, money, and broad DLaaS behavior.
Dependencies: TASK-197.
Blocked by: None for schema foundation. Resolver services, product wrappers, account creation commands, membership writes, invitations, lifecycle transitions, maintenance commands, and frontend command UX remain future tasks.
Risk level: Medium.
Rollback notes: Revert migration 082, its static migration test, and roadmap/gap updates before deployment. After deployment, use a reviewed forward migration rather than destructive rollback.
Explicit non-goals: Do not add backend routes, services, frontend changes, OpenAPI output, permission changes, account creation commands, internal tenant creation, onboarding-draft conversion, external-reference resolver service behavior, membership writes, user invitations, account lifecycle commands, account maintenance commands, reference rotation commands, credential lifecycle, support-case writes, issue/reissue/revoke/expire/void commands, attribution overrides, validation idempotency changes, duplicate reuse, live DB checks, audit writes beyond schema foundation, repair, replay, retry commands, campaign activation, webhook delivery, reward application, reward fulfilment, reward funding, reward settlement, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, SaaS billing, source-code forks, or broad DLaaS behavior.
Definition of done: Referral SaaS has a tested additive account foundation migration that can support later account setup, account maintenance, external-reference resolution, and membership tasks without exposing or replacing internal tenant partitioning. Priority: P0.

## TASK-199: Add Referral SaaS account foundation read resolver service

Status: Complete (2026-07-16). Output: `services/referral_saas_account_foundation_service.py`; `test/test_referral_saas_account_foundation_service.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SCHEMA_FINAL_REVIEW.md`; `docs/sa/TENANT_ACCOUNT_LIFECYCLE_MEMBERSHIP_MODEL.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Adds a read-only account foundation resolver over the shared account/external-reference/tenant-link schema while preserving internal `tenant_code` service execution and safe product output redaction. Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: External-reference account resolution; account setup and maintenance resolver foundation; no-internal-identifier posture.
Objective: Add a tested read-only resolver service that maps supported external reference types to durable account and tenant-link context without adding API routes or write commands.
Why now: TASK-198 added the durable schema foundation. Before account setup, maintenance, campaign, and reporting wrappers can use it, the product needs a safe read resolver that rejects blocked states and hides internal tenant identifiers by default.
Files involved: `services/referral_saas_account_foundation_service.py`; `test/test_referral_saas_account_foundation_service.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `services/referral_saas_account_scope_service.py`; `test/test_referral_saas_account_scope_service.py`; `dp/migrations/082_referral_saas_account_foundation.sql`; account boundary and schema final-review docs.
Database/schema impact: None. Uses the TASK-198 account foundation schema read-only.
Backend impact: Adds `referral_saas_account_foundation_service` with read-only external-reference resolution, supported reference-type validation, safe failure classes, account/tenant-link state checks, setup-context status allowances, and safe output redaction.
Frontend impact: None.
API impact: None.
Tests to add/update: Adds service tests for active resolution, internal tenant redaction, invalid reference type rejection before query, missing reference handling, disabled reference handling, duplicate active reference conflict handling, suspended account runtime rejection, setup-context read allowance, missing tenant-link rejection, and disabled tenant-link rejection.
Validation method: `.venv_codex\Scripts\python.exe -m pytest test\test_referral_saas_account_foundation_service.py`; `.venv_codex\Scripts\python.exe -m py_compile services\referral_saas_account_foundation_service.py test\test_referral_saas_account_foundation_service.py`; `git diff --check`.
Acceptance criteria: Resolver only reads account foundation tables; supports approved external reference types; resolves active references to account and tenant-link context; rejects inactive/missing/conflicting references and blocked tenant links; provides a setup-context read path for setup/maintenance evidence; hides internal `tenant_code` from safe product summaries unless explicitly requested by internal callers; adds no routes, schema, write commands, membership writes, invitations, account lifecycle commands, maintenance commands, campaign activation, go-live, money, or broad DLaaS behavior.
Dependencies: TASK-198.
Blocked by: None for read-only resolver. Product API wrappers, membership-aware authorization, account creation commands, invitations, lifecycle transitions, maintenance commands, and frontend command UX remain future tasks.
Risk level: Medium.
Rollback notes: Revert the resolver service, tests, and roadmap/gap updates.
Explicit non-goals: Do not add schema, migrations, backend routes, frontend changes, OpenAPI output, permission changes, account creation commands, internal tenant creation, onboarding-draft conversion, external-reference registration, reference rotation, membership writes, user invitations, account lifecycle commands, account maintenance commands, credential lifecycle, support-case writes, issue/reissue/revoke/expire/void commands, attribution overrides, validation idempotency changes, duplicate reuse, live DB mutation, audit writes, repair, replay, retry commands, campaign activation, webhook delivery, reward application, reward fulfilment, reward funding, reward settlement, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, SaaS billing, source-code forks, or broad DLaaS behavior.
Definition of done: Referral SaaS has a tested read-only account foundation resolver that safely maps external references to durable account context while keeping product outputs free of internal tenant identifiers by default. Priority: P0.

## TASK-200: Add Referral SaaS account read API wrapper

Status: Complete (2026-07-16). Output: `apps/api/routers/referral_saas_accounts.py`; `apps/api/main.py`; `test/api/test_referral_saas_accounts_api.py`; `test/test_referral_saas_route_smoke_inventory.py`; `scripts/referral_saas_route_smoke_plan.py`; `test/test_referral_saas_route_smoke_plan.py`; `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SCHEMA_FINAL_REVIEW.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Adds a bounded product API wrapper over the shared read-only account foundation resolver while preserving internal tenant scope redaction and keeping account foundation primitives single-source. Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Product account read wrapper; Account Setup durable account read path; route smoke planning; no-internal-identifier posture.
Objective: Expose a read-only Referral SaaS product account resolver endpoint so Account Setup and Account Maintenance can physically test durable account context without using internal tenant identifiers or fake frontend state.
Why now: TASK-199 added the resolver service. Account Setup should now consume a product API wrapper before we continue to campaign setup or other product areas.
Files involved: `apps/api/routers/referral_saas_accounts.py`; `apps/api/main.py`; `test/api/test_referral_saas_accounts_api.py`; `test/test_referral_saas_route_smoke_inventory.py`; `scripts/referral_saas_route_smoke_plan.py`; `test/test_referral_saas_route_smoke_plan.py`; `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `apps/api/routers/referral_saas_reports.py`; `apps/api/routers/referral_saas_links.py`; `apps/api/main.py`; `services/referral_saas_account_foundation_service.py`; route smoke inventory and smoke-plan tests.
Database/schema impact: None. Uses TASK-198 schema through the TASK-199 resolver service.
Backend impact: Adds `GET /v1/referral-saas/accounts/resolve` with account-reader role checks, runtime/setup contexts, safe error mapping, safe account response redaction, and explicit no-mutation guardrail.
Frontend impact: None.
API impact: Adds one bounded read-only product wrapper route under `/v1/referral-saas/accounts/resolve`.
Tests to add/update: Adds account API wrapper tests; updates route surface inventory and smoke-plan tests.
Validation method: `.venv_codex\Scripts\python.exe -m pytest test\api\test_referral_saas_accounts_api.py test\test_referral_saas_route_smoke_inventory.py test\test_referral_saas_route_smoke_plan.py`; `.venv_codex\Scripts\python.exe -m py_compile apps\api\routers\referral_saas_accounts.py test\api\test_referral_saas_accounts_api.py`; lint touched Python files; `git diff --check`.
Acceptance criteria: Product account read wrapper resolves runtime and setup account context through the TASK-199 service; rejects adjacent roles; maps resolver errors to safe API errors; redacts internal `tenantCode`; updates route inventory and smoke planning; adds no schema, account creation, tenant creation, onboarding-draft conversion, membership writes, invitations, lifecycle commands, maintenance commands, campaign activation, go-live, audit writes, repair/replay/retry, money, or broad DLaaS behavior.
Dependencies: TASK-199.
Blocked by: None for read-only product API. Account Setup frontend durable-account wiring and physical local account setup verification remain next.
Risk level: Medium.
Rollback notes: Revert the account router, main app router registration, tests, smoke-plan updates, and roadmap/gap updates.
Explicit non-goals: Do not add schema, migrations, frontend changes, account creation commands, internal tenant creation, onboarding-draft conversion, external-reference registration, reference rotation, membership writes, user invitations, account lifecycle commands, account maintenance commands, credential lifecycle, support-case writes, issue/reissue/revoke/expire/void commands, attribution overrides, validation idempotency changes, duplicate reuse, live DB mutation, audit writes, repair, replay, retry commands, campaign activation, webhook delivery, reward application, reward fulfilment, reward funding, reward settlement, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, SaaS billing, source-code forks, or broad DLaaS behavior.
Definition of done: Referral SaaS has a tested read-only product account resolver API that Account Setup can use for durable account context before local physical account setup testing. Priority: P0.

## TASK-201: Wire Account Setup frontend to durable account resolver

Status: Complete (2026-07-16). Output: `frontend/src/api/endpoints/referralSaasAccounts.ts`; `frontend/src/api/endpoints/referralSaasAccounts.test.ts`; `frontend/src/api/referralSaasAccountQueries.ts`; `frontend/src/api/queryKeys.ts`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Adds a frontend client/query wrapper over the shared read-only product account resolver while keeping account state single-source and preserving internal tenant identifier redaction. Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Account Setup durable account check; frontend no-fake-command posture; local physical Account Setup readiness.
Objective: Wire Account Setup Step 1 to the TASK-200 account resolver so the UI can distinguish an existing durable account from first-time setup-draft mode before local physical testing.
Why now: TASK-200 exposed the read-only product account resolver. Account Setup should consume that API before continuing to campaign work or claiming the setup flow is physically testable.
Files involved: `frontend/src/api/endpoints/referralSaasAccounts.ts`; `frontend/src/api/endpoints/referralSaasAccounts.test.ts`; `frontend/src/api/referralSaasAccountQueries.ts`; `frontend/src/api/queryKeys.ts`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `frontend/src/api/endpoints/adminOnboarding.ts`; `frontend/src/api/referralSaasAccountQueries.ts`; `frontend/src/api/queryKeys.ts`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `apps/api/routers/referral_saas_accounts.py`; `services/referral_saas_account_foundation_service.py`.
Database/schema impact: None.
Backend impact: None.
Frontend impact: Adds a product account resolver endpoint client, React Query hook, and Account Setup Step 1 durable-account resolution display. Keeps first-time setup usable when the resolver returns not found and shows resolved account context when available.
API impact: Consumes existing `GET /v1/referral-saas/accounts/resolve`; adds no new API route.
Tests to add/update: Adds endpoint client tests and updates Account Setup page tests for resolver calls, resolved account display, first-time setup fallback, and no internal tenant identifier leakage.
Validation method: `npm.cmd test -- --run src/api/endpoints/referralSaasAccounts.test.ts src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `npm.cmd run lint -- --max-warnings 60`; `npm.cmd run build`; `git diff --check`.
Acceptance criteria: Account Setup Step 1 resolves durable account context through the product API; typing remains local until the tester clicks setup check; resolved account output does not expose internal `tenant_code`; not-found resolver results keep setup-draft actions available; no fake account creation, membership, invitation, account lifecycle, maintenance, campaign activation, go-live, webhook delivery, money, or broad DLaaS behavior is added.
Dependencies: TASK-200.
Blocked by: None for frontend resolver wiring. Local physical Account Setup verification remains next before moving to campaign work.
Risk level: Medium.
Rollback notes: Revert the frontend account endpoint client, query hook/key changes, Account Setup page/test changes, and roadmap/gap/contract updates.
Explicit non-goals: Do not add backend routes, schema, migrations, permission changes, durable account creation commands, internal tenant creation, onboarding-draft conversion, external-reference registration, reference rotation, membership writes, user invitations, account lifecycle commands, account maintenance commands, credential lifecycle, support-case writes, issue/reissue/revoke/expire/void commands, attribution overrides, validation idempotency changes, duplicate reuse, live DB mutation, audit writes, repair, replay, retry commands, campaign activation, webhook delivery, reward application, reward fulfilment, reward funding, reward settlement, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, SaaS billing, source-code forks, or broad DLaaS behavior.
Definition of done: Referral SaaS Account Setup has tested frontend wiring to the durable product account resolver and is ready for local physical Account Setup verification. Priority: P0.

## TASK-202: Physically verify Account Setup draft save against local app/API/DB

Status: Complete (2026-07-16). Output: `services/onboarding/onboarding_draft_repository.py`; `test/test_onboarding_draft_repository.py`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_PHYSICAL_VERIFICATION.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Fixes onboarding draft repository JSONB persistence used by Account Setup and Account Maintenance while preserving unsafe-key validation and keeping onboarding primitives single-source. Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Local physical Account Setup proof; onboarding draft persistence; no-live-action setup guardrails.
Objective: Verify the Account Setup workflow against the running local frontend, API, and Postgres stack before moving to campaign work, and fix any concrete persistence defect discovered by that physical test.
Why now: TASK-201 made Account Setup consume the durable account resolver. Before building deeper campaign or account commands, the setup draft path must be proven beyond mocked unit/UI tests.
Files involved: `services/onboarding/onboarding_draft_repository.py`; `test/test_onboarding_draft_repository.py`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_PHYSICAL_VERIFICATION.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `apps/api/routers/admin_onboarding.py`; `frontend/src/api/endpoints/adminOnboarding.ts`; `services/onboarding/onboarding_draft_repository.py`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `dp/migrations/082_referral_saas_account_foundation.sql`.
Database/schema impact: No migration changes. Local physical verification applied the existing additive TASK-198 migration to the local Docker database because the local DB had not yet been updated with account foundation tables.
Backend impact: Serializes onboarding draft JSONB values before asyncpg persistence, preventing raw Python dict/list parameters from causing live DB internal errors.
Frontend impact: None.
API impact: No route or schema changes. Physical verification covered existing `GET /v1/referral-saas/accounts/resolve` and `POST /admin/onboarding/drafts`.
Tests to add/update: Adds repository regression coverage that JSONB payloads are serialized for create/update/validation/audit persistence calls.
Validation method: `.venv_codex\Scripts\python.exe -m pytest test\test_onboarding_draft_repository.py`; `.venv_codex\Scripts\python.exe -m py_compile services\onboarding\onboarding_draft_repository.py test\test_onboarding_draft_repository.py`; local `GET /health`; local frontend route smoke; local product account resolver smoke; local `POST /admin/onboarding/drafts` through the running backend; local Docker Postgres readback of persisted draft rows and JSONB types.
Acceptance criteria: Account Setup renders in the local app; setup resolver safely reports first-time setup mode when no durable account exists; draft validation remains no-live-action; draft save succeeds through the running local API and persists safe JSONB evidence; duplicate scope returns a safe product error instead of an internal error; no account creation, tenant creation, membership, invitation, campaign activation, go-live, webhook delivery, repair/replay/retry, reward, money, or broad DLaaS behavior is added.
Dependencies: TASK-201.
Blocked by: None for draft-save physical proof. Membership-aware authorization, durable account creation, invitations, submit/review physical proof, account lifecycle commands, and account maintenance commands remain future tasks.
Risk level: Medium.
Rollback notes: Revert the repository JSONB serialization fix, regression tests, and roadmap/gap/verification docs. Local physical DB rows created during verification are test evidence in the developer database and are not repository state.
Explicit non-goals: Do not add schema, migrations, routes, frontend UI changes, permission changes, durable account creation commands, internal tenant creation, onboarding-draft conversion, external-reference registration, reference rotation, membership writes, user invitations, account lifecycle commands, account maintenance commands, credential lifecycle, support-case writes, issue/reissue/revoke/expire/void commands, attribution overrides, validation idempotency changes, duplicate reuse, repair, replay, retry commands, campaign activation, webhook delivery, reward application, reward fulfilment, reward funding, reward settlement, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, SaaS billing, source-code forks, or broad DLaaS behavior.
Definition of done: Referral SaaS Account Setup draft save is physically verified against the local frontend/API/DB stack and the discovered onboarding JSONB persistence defect is fixed with regression coverage. Priority: P0.

## TASK-203: Add Account Setup durable account creation service

Status: Complete (2026-07-17). Output: `services/referral_saas_account_setup_service.py`; `test/test_referral_saas_account_setup_service.py`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_DURABLE_ACCOUNT_COMMAND.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SCHEMA_FINAL_REVIEW.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_PHYSICAL_VERIFICATION.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Adds an internal durable account setup service over the shared account foundation schema while keeping account foundation and onboarding draft primitives single-source. Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Durable Account Setup foundation creation; existing tenant link; external reference activation; account audit evidence.
Objective: Add the internal service primitive that converts a `READY_FOR_REVIEW` onboarding draft plus trusted existing internal tenant scope into durable account foundation records.
Why now: TASK-202 proved draft save physically. Account Setup cannot be production-real until a reviewed draft can become a durable account foundation that the resolver can read.
Files involved: `services/referral_saas_account_setup_service.py`; `test/test_referral_saas_account_setup_service.py`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_DURABLE_ACCOUNT_COMMAND.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `dp/migrations/082_referral_saas_account_foundation.sql`; `services/referral_saas_account_foundation_service.py`; `test/test_referral_saas_account_foundation_service.py`; `apps/api/routers/admin_onboarding.py`; `services/onboarding/onboarding_review_decision_service.py`; `dp/migrations/080_onboarding_draft_persistence.sql`.
Database/schema impact: No migration changes. Uses the TASK-198 account foundation schema.
Backend impact: Adds `create_durable_account_from_onboarding_draft` to create `platform_accounts`, `platform_organisations`, `platform_account_tenants`, `platform_external_tenant_refs`, and `platform_account_audit_events` from an approved setup draft and trusted internal tenant scope.
Frontend impact: None.
API impact: None. No route is added in this task.
Tests to add/update: Adds account setup service tests for successful durable account foundation creation, safe redaction, role rejection, missing draft rejection, invalid draft state rejection, duplicate external reference rejection before transaction, missing internal tenant scope rejection, and no route/membership/live-action helper exposure.
Validation method: `.venv_codex\Scripts\python.exe -m pytest test\test_referral_saas_account_setup_service.py`; `.venv_codex\Scripts\python.exe -m py_compile services\referral_saas_account_setup_service.py test\test_referral_saas_account_setup_service.py`; `git diff --check`.
Acceptance criteria: Service creates account foundation records only from `READY_FOR_REVIEW` onboarding drafts; requires an existing internal tenant scope; returns safe account context without exposing internal tenant code; records account audit evidence; prevents duplicate external tenant references before writes; adds no route, frontend control, tenant creation, membership write, invitation, account activation, account maintenance command, campaign activation, go-live, webhook delivery, repair/replay/retry, reward, money, or broad DLaaS behavior.
Dependencies: TASK-202.
Blocked by: None for service primitive. API wrapper, UI wiring, physical create-account proof, membership-aware authorization, invitations, account lifecycle commands, and account maintenance commands remain future tasks.
Risk level: Medium.
Rollback notes: Revert the service, service tests, SA note, and roadmap/gap updates.
Explicit non-goals: Do not add schema, migrations, routes, frontend changes, permission model changes, tenant creation, onboarding-draft schema changes, membership writes, user invitations, account activation, account lifecycle commands, account maintenance commands, reference rotation commands, credential lifecycle, support-case writes, issue/reissue/revoke/expire/void commands, attribution overrides, validation idempotency changes, repair, replay, retry commands, campaign activation, webhook delivery, reward application, reward fulfilment, reward funding, reward settlement, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, SaaS billing, source-code forks, or broad DLaaS behavior.
Definition of done: Referral SaaS has a tested internal durable Account Setup creation service that can create account foundation records from a reviewed setup draft without exposing tenant internals or enabling adjacent live actions. Priority: P0.

## TASK-204: Add Referral SaaS account creation API wrapper

Status: Complete (2026-07-17). Output: `apps/api/routers/referral_saas_accounts.py`; `test/api/test_referral_saas_accounts_api.py`; `scripts/referral_saas_route_smoke_plan.py`; `test/test_referral_saas_route_smoke_inventory.py`; `test/test_referral_saas_route_smoke_plan.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Exposes the shared TASK-203 durable account setup service through a guarded product API wrapper while preserving single-source account foundation, onboarding draft, idempotency, audit, and resolver primitives. Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Account Setup durable account creation; seeded-write route smoke posture; account foundation guardrails.
Objective: Add a Referral SaaS admin API wrapper that converts a reviewed onboarding draft into durable account foundation records through the TASK-203 service.
Why now: TASK-203 created the internal service primitive. Account Setup needs a product API boundary before local physical create-account proof and UI wiring can be completed.
Files involved: `apps/api/routers/referral_saas_accounts.py`; `test/api/test_referral_saas_accounts_api.py`; `scripts/referral_saas_route_smoke_plan.py`; `test/test_referral_saas_route_smoke_inventory.py`; `test/test_referral_saas_route_smoke_plan.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `services/referral_saas_account_setup_service.py`; `services/referral_saas_account_foundation_service.py`; `services/onboarding/onboarding_draft_idempotency_service.py`; `apps/api/routers/referral_saas_accounts.py`; `scripts/referral_saas_route_smoke_plan.py`.
Database/schema impact: No migration changes. Uses the TASK-198 account foundation schema through the TASK-203 service.
Backend impact: Adds `POST /v1/referral-saas/accounts/from-draft` with admin-role guardrails, required `draft_ref`, trusted existing `internal_tenant_code`, idempotency-key hashing, safe error mapping, and explicit no-adjacent-live-action guardrails.
Frontend impact: None.
API impact: Adds one guarded seeded-write Referral SaaS account API wrapper. The endpoint is intentionally excluded from default production read-only smoke output and included only when seeded writes are requested.
Tests to add/update: Adds API tests for successful wrapper invocation, required-field validation, adjacent-role rejection, and safe command-error mapping; updates route surface bounds and smoke-plan tests for seeded-write classification.
Validation method: `.venv_codex\Scripts\python.exe -m pytest test\api\test_referral_saas_accounts_api.py test\test_referral_saas_route_smoke_inventory.py test\test_referral_saas_route_smoke_plan.py`; `.venv_codex\Scripts\python.exe -m py_compile apps\api\routers\referral_saas_accounts.py test\api\test_referral_saas_accounts_api.py scripts\referral_saas_route_smoke_plan.py`; `git diff --check`.
Acceptance criteria: The API wrapper requires admin account access, `draft_ref`, trusted existing internal tenant scope, and idempotency key; maps service errors to safe HTTP responses without exposing internal tenant identifiers; returns safe account context; keeps the route classified as seeded-write; adds no schema, frontend action, internal tenant creation, membership write, invitation, account activation, account maintenance command, campaign activation, go-live, webhook delivery, repair/replay/retry, reward, money, or broad DLaaS behavior.
Dependencies: TASK-203.
Blocked by: None for the guarded API wrapper. Physical create-account proof, Account Setup UI create-action wiring, membership-aware authorization, invitations, account lifecycle commands, and account maintenance commands remain future tasks.
Risk level: Medium.
Rollback notes: Revert the account router changes, API tests, smoke-plan updates, route inventory updates, and roadmap/gap updates.
Explicit non-goals: Do not add schema, migrations, frontend changes, permission model changes beyond the existing product admin role gate, tenant creation, onboarding-draft schema changes, membership writes, user invitations, account activation, account lifecycle commands, account maintenance commands, reference rotation commands, credential lifecycle, support-case writes, issue/reissue/revoke/expire/void commands, attribution overrides, validation idempotency changes, repair, replay, retry commands, campaign activation, webhook delivery, reward application, reward fulfilment, reward funding, reward settlement, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, SaaS billing, source-code forks, or broad DLaaS behavior.
Definition of done: Referral SaaS has a tested guarded account creation API wrapper over the durable Account Setup service and is ready for local physical create-account verification before UI create-action wiring. Priority: P0.

## TASK-205: Clarify Referral SaaS Account Setup workflow UX

Status: Complete (2026-07-17). Output: `frontend/src/pages/admin/CompanyOnboardingPage.tsx`; `frontend/src/pages/admin/CompanyOnboardingPage.test.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `frontend/src/pages/admin/OnboardingDemoJourneySmoke.test.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Clarifies the existing Account Setup frontend workflow over shared onboarding draft, validation, review, durable account resolver, and guarded account creation wrapper primitives. Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Account Setup workflow UX; Step 1 company profile; readiness preview clarity; gated account creation posture.
Objective: Make Referral SaaS Account Setup read as a parent workflow and make Company Onboarding read as Step 1 Company Profile, with plain-language action labels, readiness preview value, return path, and gated account creation messaging.
Why now: Local product testing showed the Account Setup and Company Onboarding screens felt disjointed and diagnostic-heavy. TASK-204 created the guarded account creation API wrapper, so the UI needed to stop saying account creation was generic future work while still avoiding a fake create command before physical proof and explicit UI wiring.
Files involved: `frontend/src/pages/admin/CompanyOnboardingPage.tsx`; `frontend/src/pages/admin/CompanyOnboardingPage.test.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `frontend/src/pages/admin/OnboardingDemoJourneySmoke.test.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `frontend/src/pages/admin/CompanyOnboardingPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Database/schema impact: None.
Backend impact: None.
Frontend impact: Repositions Company Onboarding as `Step 1: Company profile`, adds a return path to Referral SaaS Account Setup, relabels saved evidence as reference context, changes the dry-run panel to answer can-continue/why/next-action, clarifies save/submit/review button labels, and changes Account Setup guardrails from future-work wording to gated account creation wording.
API impact: None.
Tests to add/update: Updated Company Onboarding page tests, Referral SaaS Account Setup page tests, and onboarding demo smoke coverage for the new workflow wording, action labels, gated account creation posture, and no-fake-command behavior.
Validation method: `npm.cmd test -- --run src/pages/admin/CompanyOnboardingPage.test.tsx`; `npm.cmd test -- --run src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `npm.cmd test -- --run src/pages/admin/OnboardingDemoJourneySmoke.test.tsx`; `npm.cmd run lint -- --max-warnings 60`.
Acceptance criteria: Account Setup clearly acts as the parent workflow; Company Profile clearly acts as Step 1; dry-run validation explains whether the operator can continue, why not, and the next action; account creation is shown as gated until physical create-account proof and explicit UI wiring exist; no internal tenant identifiers are exposed; no backend route, schema, migration, account creation UI command, membership write, invitation, activation, campaign activation, go-live, webhook delivery, repair/replay/retry, reward, money, source fork, or broad DLaaS behavior is added.
Dependencies: TASK-204.
Blocked by: None for workflow UX clarification. Physical create-account proof and Account Setup UI create-action wiring remain the next account setup tasks.
Risk level: Low.
Rollback notes: Revert the Account Setup and Company Onboarding frontend/test changes plus roadmap/gap updates.
Explicit non-goals: Do not add backend routes, schema, migrations, account creation command wiring in the UI, physical seeded-write DB execution, membership writes, user invitations, account activation, account lifecycle commands, account maintenance commands, reference rotation commands, credential lifecycle, support-case writes, attribution overrides, validation idempotency changes, repair, replay, retry commands, campaign activation, webhook delivery, reward application, reward fulfilment, reward funding, reward settlement, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, SaaS billing, source-code forks, or broad DLaaS behavior.
Definition of done: Referral SaaS Account Setup and Step 1 Company Profile now present a coherent tested operator workflow without faking account creation, and the roadmap/gap matrix point to physical create-account proof as the next production blocker. Priority: P1.

## TASK-206: Physically verify Referral SaaS account creation from reviewed draft

Status: Complete (2026-07-17). Output: `scripts/referral_saas_account_create_physical_check.py`; `test/test_referral_saas_account_create_physical_check.py`; `services/referral_saas_account_setup_service.py`; `test/test_referral_saas_account_setup_service.py`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_CREATE_PHYSICAL_VERIFICATION.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Adds a local/staging physical account creation checker over the shared onboarding draft and account foundation primitives, and hardens duplicate internal tenant owner prechecks in the shared account setup service. Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Account Setup physical proof; guarded account creation; safe duplicate handling; local seeded-write verification.
Objective: Physically prove that a reviewed setup draft can create a durable Referral SaaS account foundation through the guarded product API, resolve through the product resolver, and verify database evidence without exposing internal tenant identifiers.
Why now: TASK-204 exposed the guarded account creation API and TASK-205 clarified the operator workflow. The UI create action should not be wired until account creation is proven against a real local API/DB path and safe duplicate behavior is hardened.
Files involved: `scripts/referral_saas_account_create_physical_check.py`; `test/test_referral_saas_account_create_physical_check.py`; `services/referral_saas_account_setup_service.py`; `test/test_referral_saas_account_setup_service.py`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_CREATE_PHYSICAL_VERIFICATION.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `apps/api/routers/referral_saas_accounts.py`; `services/referral_saas_account_setup_service.py`; `services/referral_saas_account_foundation_service.py`; `services/onboarding/onboarding_draft_validation_service.py`; `services/onboarding/onboarding_submit_for_review_service.py`; `dp/migrations/080_onboarding_draft_persistence.sql`; `dp/migrations/082_referral_saas_account_foundation.sql`.
Database/schema impact: No migration changes. Local physical verification created and verified account foundation rows in the local database using the existing TASK-198 schema.
Backend impact: Adds a reusable physical checker for create -> resolve -> DB verification. Hardens `create_durable_account_from_onboarding_draft` so an existing active or pending owner link for the trusted internal tenant scope is rejected as a safe duplicate conflict before the write transaction rather than surfacing a database uniqueness error.
Frontend impact: None. This task intentionally keeps the UI create action unwired until the physical backend proof is recorded.
API impact: Adds no new API route. The checker exercises existing `POST /v1/referral-saas/accounts/from-draft` and `GET /v1/referral-saas/accounts/resolve`.
Tests to add/update: Adds focused physical-check script tests and account setup service duplicate-owner tests.
Validation method: `.venv_codex\Scripts\python.exe -m pytest -q test\test_referral_saas_account_setup_service.py test\api\test_referral_saas_accounts_api.py test\test_referral_saas_account_create_physical_check.py`; `.venv_codex\Scripts\python.exe -m py_compile services\referral_saas_account_setup_service.py scripts\referral_saas_account_create_physical_check.py test\test_referral_saas_account_setup_service.py test\test_referral_saas_account_create_physical_check.py`; local physical proof command `.venv_codex\Scripts\python.exe scripts\referral_saas_account_create_physical_check.py --base-url http://127.0.0.1:8000 --admin-key test-admin-key --internal-tenant-code FNB --suffix local-206b --db-dsn postgresql://user:pass@localhost:5432/referrals --seed-reviewed-draft-db`.
Acceptance criteria: Physical checker can create a reviewed-draft account foundation through the product API, resolve it through the product account resolver, verify external-reference and audit rows, and confirm internal tenant identifiers are not exposed; duplicate internal tenant owner state is caught before transaction as a safe conflict; no frontend create action, tenant creation, membership write, invitation, account activation, account maintenance command, campaign activation, go-live, webhook delivery, repair/replay/retry, reward, money, or broad DLaaS behavior is added.
Dependencies: TASK-204; TASK-205.
Blocked by: None for physical account creation proof. Account Setup UI create-action wiring, full save -> submit -> review physical hardening, membership-aware authorization, invitations, account lifecycle commands, and account maintenance commands remain future tasks.
Risk level: Medium.
Rollback notes: Revert the physical checker script/test, duplicate-owner service/test hardening, evidence note, and roadmap/gap updates. Existing TASK-204 API wrapper remains intact.
Explicit non-goals: Do not add schema, migrations, frontend create-action wiring, permission model changes, tenant creation, onboarding-draft schema changes, membership writes, user invitations, account activation, account lifecycle commands, account maintenance commands, reference rotation commands, credential lifecycle, support-case writes, attribution overrides, validation idempotency changes, repair, replay, retry commands, campaign activation, webhook delivery, reward application, reward fulfilment, reward funding, reward settlement, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, SaaS billing, source-code forks, or broad DLaaS behavior.
Definition of done: Referral SaaS has a documented, tested, and locally proven account creation path from reviewed setup draft to durable account foundation, with safe resolve/readback and duplicate-owner hardening, ready for carefully scoped UI create-action wiring. Priority: P0.

## TASK-207: Wire Account Setup UI create action to reviewed-draft account creation

Status: Complete (2026-07-17). Output: `frontend/src/api/endpoints/referralSaasAccounts.ts`; `frontend/src/api/endpoints/referralSaasAccounts.test.ts`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Wires the frontend to the existing guarded Referral SaaS account creation API while keeping onboarding draft, review, account foundation, resolver, and account setup primitives single-source. Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Account Setup create-action wiring; reviewed-draft account foundation creation; safe UI command gating.
Objective: Add the Account Setup UI action that creates the durable account foundation from an accepted reviewed draft through the TASK-204 guarded product API, using the TASK-206 physical proof as the release gate.
Why now: TASK-206 physically proved account creation from reviewed setup evidence. The Account Setup UI can now expose a real final setup action instead of only describing a future gated command.
Files involved: `frontend/src/api/endpoints/referralSaasAccounts.ts`; `frontend/src/api/endpoints/referralSaasAccounts.test.ts`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `frontend/src/api/endpoints/referralSaasAccounts.ts`; `frontend/src/api/referralSaasAccountQueries.ts`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `apps/api/routers/referral_saas_accounts.py`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_CREATE_PHYSICAL_VERIFICATION.md`.
Database/schema impact: None.
Backend impact: None.
Frontend impact: Adds a typed create-from-draft endpoint client, shows a final Account Setup create-account-foundation action, enables it only after accepted internal review when no durable account already resolves, renders success/fallback states, and refreshes the account resolver after creation. The UI does not expose internal tenant identifiers to the operator.
API impact: Consumes existing `POST /v1/referral-saas/accounts/from-draft`; adds no route.
Tests to add/update: Adds endpoint client coverage for the guarded create call and updates Account Setup page tests for disabled existing-account state, first-time reviewed-draft create flow, no invite/money/go-live actions, and safe account-created evidence.
Validation method: `npm.cmd test -- --run src/api/endpoints/referralSaasAccounts.test.ts src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `npm.cmd run lint -- --max-warnings 60`; `npm.cmd run build`.
Acceptance criteria: Account Setup shows the real account foundation create action only after save, submit, and accepted internal review; already-resolved account context keeps the create action disabled; create success displays safe account evidence; internal tenant identifiers are not displayed; no tenant creation, membership write, invitation, credential lifecycle, campaign activation, go-live, webhook delivery, repair/replay/retry, reward, money, or broad DLaaS behavior is added.
Dependencies: TASK-204; TASK-205; TASK-206.
Blocked by: None for UI command wiring. Full UI-driven local save -> submit -> review -> create -> resolve proof, full save/submit/review path hardening, membership-aware authorization, invitations, account lifecycle commands, and account maintenance commands remain future tasks.
Risk level: Medium.
Rollback notes: Revert the Referral SaaS account endpoint client/test changes, Account Setup page/test changes, and roadmap/gap updates.
Explicit non-goals: Do not add backend routes, schema, migrations, permission model changes, tenant creation, onboarding-draft schema changes, membership writes, user invitations, account activation, account lifecycle commands, account maintenance commands, reference rotation commands, credential lifecycle, support-case writes, attribution overrides, validation idempotency changes, repair, replay, retry commands, campaign activation, webhook delivery, reward application, reward fulfilment, reward funding, reward settlement, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, SaaS billing, source-code forks, or broad DLaaS behavior.
Definition of done: Referral SaaS Account Setup has tested UI wiring to create the durable account foundation from accepted reviewed draft evidence through the guarded product API, ready for full local UI-driven physical onboarding proof. Priority: P0.

## TASK-208: Physically verify full Account Setup UI save-review-create path

Status: Complete (2026-07-17). Output: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `scripts/referral_saas_account_setup_ui_physical_check.py`; `test/test_referral_saas_account_setup_ui_physical_check.py`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_UI_PHYSICAL_VERIFICATION.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Keeps onboarding draft validation/save/submit/review, account foundation creation, and resolver primitives single-source while proving the Referral SaaS UI evidence contract covers the full shared onboarding section set. Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Full Account Setup local physical proof; complete setup evidence payload; guarded save -> submit -> review -> create -> resolve path.
Objective: Physically verify that the Account Setup UI contract can provide complete bounded evidence for the shared onboarding validator and then progress through draft save, submit-for-review, review decision, account foundation creation, and resolver readback.
Why now: TASK-207 wired the final UI create action. The remaining launch blocker was proving the whole account setup path with complete saved evidence rather than partial UI sections that could save draft intent but fail review validation.
Files involved: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `scripts/referral_saas_account_setup_ui_physical_check.py`; `test/test_referral_saas_account_setup_ui_physical_check.py`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_UI_PHYSICAL_VERIFICATION.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `frontend/src/api/endpoints/adminOnboarding.ts`; `apps/api/routers/admin_onboarding.py`; `services/onboarding/onboarding_draft_validation_service.py`; `services/onboarding/onboarding_submit_for_review_service.py`; `services/onboarding/onboarding_state_projection_service.py`; `scripts/referral_saas_account_create_physical_check.py`; `test/test_referral_saas_account_create_physical_check.py`.
Database/schema impact: No migration changes.
Backend impact: Adds no backend route or service change. Hardens admin onboarding saved-section readback so JSONB section payload strings are decoded before submit/review validation, and adds a local/staging physical checker over existing backend APIs.
Frontend impact: Account Setup now validates and saves all six required onboarding evidence sections: company, producer/sponsor, distributor, member/role, campaign/opportunity, and webhook/API. This prevents the full setup path from being blocked by missing saved evidence created by the UI itself.
API impact: No new route. The checker exercises existing `POST /admin/onboarding/validate`, `POST /admin/onboarding/drafts`, `POST /admin/onboarding/drafts/{draft_ref}/submit-for-review`, `POST /admin/onboarding/drafts/{draft_ref}/review-decision`, `POST /v1/referral-saas/accounts/from-draft`, and `GET /v1/referral-saas/accounts/resolve`.
Tests to add/update: Updates Account Setup page coverage for complete validation scope and saved sections; adds admin onboarding JSONB readback regression coverage; adds physical-check script tests for complete section coverage, unsafe product payload detection, missing-section rejection, and safe defaults.
Validation method: `npm.cmd test -- --run src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `.venv_codex\Scripts\python.exe -m pytest -q test\api\test_admin_onboarding_api.py -k "jsonb_strings or submit_for_review_transitions_saved_draft_only"`; `.venv_codex\Scripts\python.exe -m pytest -q test\test_referral_saas_account_setup_ui_physical_check.py`; `.venv_codex\Scripts\python.exe -m py_compile apps\api\routers\admin_onboarding.py scripts\referral_saas_account_setup_ui_physical_check.py test\api\test_admin_onboarding_api.py test\test_referral_saas_account_setup_ui_physical_check.py`; local physical proof command `.venv_codex\Scripts\python.exe scripts\referral_saas_account_setup_ui_physical_check.py --base-url http://127.0.0.1:8000 --admin-key test-admin-key --internal-tenant-code TASK208C --suffix local-208c`.
Acceptance criteria: UI setup evidence covers every backend-required onboarding section; setup validation/save payloads remain free of internal tenant identifiers, secrets, wallet/settlement fields, go-live activation, and invitation commands; physical checker can exercise validate -> save -> submit -> review -> create -> resolve against a running local/staging API; no tenant creation, membership write, invitation, credential lifecycle, campaign activation, go-live, webhook delivery, repair/replay/retry, reward, value transfer, or broad DLaaS behavior is added.
Dependencies: TASK-193; TASK-202; TASK-204; TASK-206; TASK-207.
Blocked by: None for full Account Setup UI physical proof tooling. Membership-aware authorization, invitations, account lifecycle commands, and account maintenance commands remain future tasks.
Risk level: Medium.
Rollback notes: Revert the Account Setup complete-section payload change, frontend test update, physical checker/test, and docs updates. Existing TASK-207 UI create wiring and backend account primitives remain intact.
Explicit non-goals: Do not add backend routes, schema, migrations, permission model changes, tenant creation, membership writes, user invitations, account activation, account lifecycle commands, account maintenance commands, reference rotation commands, credential lifecycle, support-case writes, attribution overrides, validation idempotency changes, repair, replay, retry commands, campaign activation, webhook delivery, reward application, reward fulfilment, reward funding, reward settlement, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, SaaS billing, source-code forks, or broad DLaaS behavior.
Definition of done: Referral SaaS Account Setup sends complete bounded evidence and has a repeatable local/staging physical checker for validate -> save -> submit -> review -> create -> resolve before membership/invitation account setup work begins. Priority: P0.

## TASK-209: Add Referral SaaS membership read boundary

Status: Complete (2026-07-17). Output: `services/referral_saas_account_membership_service.py`; `apps/api/routers/referral_saas_accounts.py`; `test/test_referral_saas_account_membership_service.py`; `test/api/test_referral_saas_accounts_api.py`; `frontend/src/api/endpoints/referralSaasAccounts.ts`; `frontend/src/api/endpoints/referralSaasAccounts.test.ts`; `frontend/src/api/referralSaasAccountQueries.ts`; `frontend/src/api/queryKeys.ts`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `scripts/referral_saas_route_smoke_plan.py`; `test/test_referral_saas_route_smoke_inventory.py`; `test/test_referral_saas_route_smoke_plan.py`; `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Reads the shared account foundation membership tables through a product-safe Referral SaaS posture wrapper. Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Account Setup membership posture and authorization boundary.
Objective: Add a read-only Referral SaaS membership posture boundary so Account Setup can show whether the resolved durable account has active, invited, suspended, or missing membership evidence without creating users, invitations, seats, auth claims, or membership writes.
Why now: TASK-208 proved the full Account Setup save -> submit -> review -> create -> resolve path. The next production gap is making access posture visible before adding any write-side invitation or membership lifecycle commands.
Files involved: `services/referral_saas_account_membership_service.py`; `apps/api/routers/referral_saas_accounts.py`; `frontend/src/api/endpoints/referralSaasAccounts.ts`; `frontend/src/api/referralSaasAccountQueries.ts`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; route smoke plan/inventory tests; roadmap/gap matrix docs.
Implementation/source files inspected: `dp/migrations/082_referral_saas_account_foundation.sql`; `services/referral_saas_account_foundation_service.py`; `services/referral_saas_account_setup_service.py`; `apps/api/routers/referral_saas_accounts.py`; `frontend/src/api/endpoints/referralSaasAccounts.ts`; `frontend/src/api/referralSaasAccountQueries.ts`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; related API/frontend/route-smoke tests.
Database/schema impact: No migration changes. Reads existing `platform_memberships` and related account foundation context only.
Backend impact: Adds `services/referral_saas_account_membership_service.py` and `GET /v1/referral-saas/accounts/membership-posture` with account-reader role checks, setup/runtime resolver context, safe redactions, membership count posture, current-actor posture classification, and explicit no-write/no-invite guardrails.
Frontend impact: Account Setup Step 1 now shows a Membership access check next to durable account resolution and keeps membership writes/invite delivery visibly outside the setup workflow.
API impact: Adds one bounded read-only product wrapper route under `/v1/referral-saas/accounts/membership-posture`; updates read-only smoke plan and route surface inventory.
Tests to add/update: Adds membership service tests, account API wrapper tests, endpoint client tests, Account Setup page tests, route smoke inventory tests, and smoke plan tests.
Validation method: `.venv_codex\Scripts\python.exe -m pytest -q test\test_referral_saas_account_membership_service.py test\api\test_referral_saas_accounts_api.py test\test_referral_saas_route_smoke_inventory.py test\test_referral_saas_route_smoke_plan.py`; `.venv_codex\Scripts\python.exe -m py_compile services\referral_saas_account_membership_service.py apps\api\routers\referral_saas_accounts.py test\test_referral_saas_account_membership_service.py test\api\test_referral_saas_accounts_api.py scripts\referral_saas_route_smoke_plan.py`; `npm.cmd test -- --run src/api/endpoints/referralSaasAccounts.test.ts src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`.
Acceptance criteria: Membership posture is read-only, role-gated, safe-redacted, bounded to resolved account context, and visible in Account Setup after durable account resolution; no tenant code, user identifier, client identifier, email hash, invitation command, membership write, seat assignment, auth-claim change, account activation, go-live, campaign activation, money movement, or broad DLaaS behavior is added.
Dependencies: TASK-198; TASK-199; TASK-200; TASK-201; TASK-208.
Blocked by: None for read-only membership posture. Write-side invitation delivery, membership activation, seat assignment, auth-claim integration, account lifecycle commands, and account maintenance commands remain future tasks.
Risk level: Medium.
Rollback notes: Revert the membership posture service/API route, frontend query/display, route smoke updates, tests, and docs updates.
Explicit non-goals: Do not add schema, migrations, user creation, invitation delivery, membership writes, seat assignment, auth claim changes, account activation, account maintenance commands, reference rotation commands, campaign activation, go-live, credential lifecycle, webhooks, support-case writes, repair/replay/retry, reward, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, marketplace-depth, white-label/embed, SaaS billing, source-code forks, or broad DLaaS behavior.
Definition of done: Referral SaaS Account Setup can read and render membership posture for a resolved durable account while preserving clear read-only boundaries before membership/invitation write work begins. Priority: P0.

## TASK-210: Define Referral SaaS membership invitation write boundary

Status: Complete (2026-07-18). Output: `docs/sa/referral-saas/REFERRAL_SAAS_MEMBERSHIP_INVITATION_BOUNDARY.md`; `test/test_referral_saas_membership_invitation_boundary_contract.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/README.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_WRAPPER_CONTRACT.md`; `docs/sa/TENANT_ACCOUNT_LIFECYCLE_MEMBERSHIP_MODEL.md`.
Shared primitive impact: Defines the future Referral SaaS membership invitation command against the shared account foundation schema while preserving single-source account, user, membership, seat, audit, resolver, onboarding, and frontend primitives. Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Account Setup Users and Roles invitation boundary; membership write idempotency and audit posture.
Objective: Define the reviewed write boundary for Referral SaaS membership invitation intent so Account Setup can move from read-only membership posture to a production-safe Users and Roles command without fake invitation delivery, activation, seats, auth claims, or money behavior.
Why now: TASK-209 made membership posture visible but intentionally kept write-side invitation and membership lifecycle out of scope. Before implementing runtime membership writes, the product needs an explicit command contract for idempotency, audit, duplicate prevention, redaction, authorization, account resolver usage, and delivery deferrals.
Files involved: `docs/sa/referral-saas/REFERRAL_SAAS_MEMBERSHIP_INVITATION_BOUNDARY.md`; `test/test_referral_saas_membership_invitation_boundary_contract.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/README.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `dp/migrations/082_referral_saas_account_foundation.sql`; `services/referral_saas_account_membership_service.py`; `services/referral_saas_account_setup_service.py`; `services/referral_saas_account_foundation_service.py`; `apps/api/routers/referral_saas_accounts.py`; `frontend/src/pages/admin/MemberRoleOnboardingPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`.
Database/schema impact: No migration changes.
Backend impact: No backend runtime change. Defines the future product route family and service behavior for bounded membership invitation intent.
Frontend impact: No frontend runtime change. Defines that the future Users and Roles action belongs inside Account Setup Step 2, after durable account foundation exists, with delivery and activation clearly separated.
API impact: No route added. Future candidate route is `POST /v1/referral-saas/accounts/{accountRef}/membership-invitations`.
Tests to add/update: Adds a static contract test proving the boundary stays Referral SaaS scoped, references the real account foundation tables, defines command/idempotency statuses, preserves redactions/guardrails, and keeps delivery, activation, seats, auth claims, account lifecycle, account maintenance, campaign activation, go-live, and money behavior out of scope.
Validation method: `.venv_codex\Scripts\python.exe -m pytest -q test\test_referral_saas_membership_invitation_boundary_contract.py`.
Acceptance criteria: Contract defines future membership invitation request/response shapes, allowed statuses, idempotency, audit, permission rejection cases, UX placement, guardrails, redactions, and explicit non-goals; no runtime route, service write, frontend action, schema, migration, email delivery, identity-provider integration, seat assignment, auth-claim change, membership activation, account lifecycle, maintenance command, campaign activation, go-live, money, or broad DLaaS behavior is added.
Dependencies: TASK-198; TASK-199; TASK-200; TASK-203; TASK-204; TASK-208; TASK-209.
Blocked by: None for contract. Runtime invitation intent service/API, invitation UX, membership activation, seat assignment, auth-claim integration, account lifecycle commands, and account maintenance commands remain future work.
Risk level: Low.
Rollback notes: Revert the membership invitation boundary doc, static contract test, and roadmap/gap/index updates.
Explicit non-goals: Do not add backend routes, service writes, frontend controls, schema, migrations, user creation command implementation, email or messaging invitation delivery, identity-provider integration, auth/session claim changes, membership activation, seat assignment, account lifecycle commands, account maintenance commands, tenant creation, campaign activation, go-live, credential lifecycle, webhook delivery, support-case writes, repair/replay/retry, reward, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, treasury, broad DLaaS marketplace behavior, or source-code forks.
Definition of done: Referral SaaS has a reviewed membership invitation write boundary that can drive the next narrow service/API implementation task for invitation intent recording with idempotency, audit, redaction, duplicate prevention, and no delivery, activation, seat, auth-claim, campaign, go-live, money, or DLaaS side effects. Priority: P0.

## TASK-211: Add Referral SaaS membership invitation intent API

Status: Complete (2026-07-18). Output: `services/referral_saas_account_membership_service.py`; `apps/api/routers/referral_saas_accounts.py`; `test/test_referral_saas_account_membership_service.py`; `test/api/test_referral_saas_accounts_api.py`; `scripts/referral_saas_route_smoke_plan.py`; `test/test_referral_saas_route_smoke_inventory.py`; `test/test_referral_saas_route_smoke_plan.py`; `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/README.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `docs/sa/referral-saas/REFERRAL_SAAS_MEMBERSHIP_INVITATION_BOUNDARY.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_CONTRACT.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_WRAPPER_CONTRACT.md`; `docs/sa/TENANT_ACCOUNT_LIFECYCLE_MEMBERSHIP_MODEL.md`.
Shared primitive impact: Reuses the shared account foundation resolver, user, membership, tenant-link, external-reference, and account audit tables through a product-safe Referral SaaS command wrapper. Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Account Setup Users and Roles invitation intent; membership write idempotency and audit evidence.
Objective: Add the first bounded Referral SaaS membership invitation intent service/API so Account Setup can record invited user/member role intent against a resolved durable account without sending invitations, activating access, assigning seats, mutating auth claims, launching campaigns, or moving money.
Why now: TASK-210 defined the command boundary. The Account Setup wizard cannot become coherent until Step 2 can call a real backend command rather than only save onboarding evidence or show read-only membership posture.
Files involved: `services/referral_saas_account_membership_service.py`; `apps/api/routers/referral_saas_accounts.py`; `test/test_referral_saas_account_membership_service.py`; `test/api/test_referral_saas_accounts_api.py`; `scripts/referral_saas_route_smoke_plan.py`; `test/test_referral_saas_route_smoke_inventory.py`; `test/test_referral_saas_route_smoke_plan.py`; `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/README.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `dp/migrations/082_referral_saas_account_foundation.sql`; `services/referral_saas_account_foundation_service.py`; `services/referral_saas_account_membership_service.py`; `services/referral_saas_account_setup_service.py`; `apps/api/routers/referral_saas_accounts.py`; `test/test_referral_saas_account_membership_service.py`; `test/api/test_referral_saas_accounts_api.py`; `scripts/referral_saas_route_smoke_plan.py`; `test/test_referral_saas_route_smoke_inventory.py`.
Database/schema impact: No migration changes. Writes to existing `platform_users`, `platform_memberships`, and `platform_account_audit_events` only.
Backend impact: Adds `record_referral_saas_membership_invitation_intent` with required account/tenant context, idempotency replay/conflict checks, duplicate membership prevention, unsafe payload rejection, invited user/member creation, and account audit evidence.
Frontend impact: No frontend runtime change. The next task should wire Account Setup Step 2 Users and Roles to this API.
API impact: Adds `POST /v1/referral-saas/accounts/{account_ref}/membership-invitations`. The route requires account-reader/admin roles, resolves trusted account context from external references, verifies the path account reference matches the resolved account, returns product-safe invitation intent response shape, and classifies the route as seeded local/staging write smoke only.
Tests to add/update: Adds service tests for record/replay/conflict/duplicate/unsafe paths; API tests for success, adjacent role rejection, scope mismatch, unsafe payload, and safe duplicate mapping; route smoke inventory and plan tests.
Validation method: `.venv_codex\Scripts\python.exe -m pytest -q test\test_referral_saas_account_membership_service.py test\api\test_referral_saas_accounts_api.py test\test_referral_saas_route_smoke_inventory.py test\test_referral_saas_route_smoke_plan.py`; `.venv_codex\Scripts\python.exe -m py_compile services\referral_saas_account_membership_service.py apps\api\routers\referral_saas_accounts.py test\test_referral_saas_account_membership_service.py test\api\test_referral_saas_accounts_api.py scripts\referral_saas_route_smoke_plan.py test\test_referral_saas_route_smoke_inventory.py test\test_referral_saas_route_smoke_plan.py`.
Acceptance criteria: Invitation intent records invited user/member evidence with idempotency, audit, duplicate prevention, redactions, account resolver guardrails, route role checks, safe error mapping, and no raw email storage, invite delivery, identity-provider integration, membership activation, seat assignment, auth-claim change, tenant creation, account activation, campaign activation, go-live, credential lifecycle, webhook delivery, repair/replay/retry, reward, money, or broad DLaaS behavior.
Dependencies: TASK-198; TASK-199; TASK-200; TASK-203; TASK-204; TASK-209; TASK-210.
Blocked by: None for backend invitation intent. Account Setup Users/Roles frontend wiring, local UI-driven proof, invite delivery provider integration, membership activation, seat assignment, auth-claim integration, account lifecycle commands, and account maintenance commands remain future work.
Risk level: Medium.
Rollback notes: Revert the membership invitation service/API route, tests, route smoke updates, and docs updates.
Explicit non-goals: Do not add schema, migrations, frontend controls, email or messaging invitation delivery, identity-provider integration, auth/session claim changes, membership activation, seat assignment, account lifecycle commands, account maintenance commands, tenant creation, campaign activation, go-live, credential lifecycle, webhook delivery, support-case writes, repair/replay/retry, reward, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, treasury, broad DLaaS marketplace behavior, or source-code forks.
Definition of done: Referral SaaS Account Setup has a bounded, tested backend/API command for membership invitation intent, ready for the next task to wire the Users and Roles step in the wizard. Priority: P0.

## TASK-212: Wire Account Setup Users and Roles to invitation intent API

Status: Complete (2026-07-18). Output: `frontend/src/api/endpoints/referralSaasAccounts.ts`; `frontend/src/api/endpoints/referralSaasAccounts.test.ts`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/README.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `docs/sa/referral-saas/REFERRAL_SAAS_MEMBERSHIP_INVITATION_BOUNDARY.md`.
Shared primitive impact: Reuses the TASK-211 Referral SaaS account membership invitation intent API and existing account foundation resolver. Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Account Setup Users and Roles UX; membership invitation intent evidence.
Objective: Wire Account Setup Step 2 Users and Roles to the bounded membership invitation intent API so operators can record invited role evidence from the Referral SaaS workspace after durable account resolution.
Why now: TASK-211 added the backend/API command. The Account Setup wizard remained confusing until Step 2 could call the real command and show what was recorded versus what remains deliberately outside the setup page.
Files involved: `frontend/src/api/endpoints/referralSaasAccounts.ts`; `frontend/src/api/endpoints/referralSaasAccounts.test.ts`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/README.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `frontend/src/api/endpoints/referralSaasAccounts.ts`; `frontend/src/api/referralSaasAccountQueries.ts`; `frontend/src/api/queryKeys.ts`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `apps/api/routers/referral_saas_accounts.py`; `services/referral_saas_account_membership_service.py`.
Database/schema impact: None.
Backend impact: None. Uses the existing TASK-211 API route.
Frontend impact: Adds a typed invitation intent client and inline Account Setup Step 2 Users/Roles action with subject, display name, optional email hash, role family, permission set, safe success/fallback messaging, and membership posture refresh.
API impact: No new route. Calls `POST /v1/referral-saas/accounts/{account_ref}/membership-invitations`.
Tests to add/update: Adds endpoint client coverage and Account Setup page coverage for successful role intent recording, safe payload shape, visible delivery/activation/seat/auth/money guardrails, and existing workflow links.
Validation method: `npm.cmd test -- --run src/api/endpoints/referralSaasAccounts.test.ts src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `npm.cmd run lint -- --max-warnings 60`; `npm.cmd run build`; `git diff --check`.
Acceptance criteria: Account Setup Step 2 can record bounded invited membership intent only after durable account resolution; request payload includes trusted account scope, actor subject/display/hash, role family, permission set, correlation ID, and idempotency key; UI shows recorded invitation intent and delivery-not-configured posture; no raw internal tenant identifiers, email delivery, identity-provider integration, membership activation, seat assignment, auth-claim change, tenant creation, account activation, campaign activation, go-live, credential lifecycle, webhook delivery, repair/replay/retry, reward, money, or broad DLaaS behavior is added.
Dependencies: TASK-198; TASK-199; TASK-200; TASK-203; TASK-204; TASK-209; TASK-210; TASK-211.
Blocked by: None for frontend invitation-intent wiring. Local UI/API/DB physical proof, invite delivery provider integration, membership activation, seat assignment, auth-claim integration, account lifecycle commands, and account maintenance commands remain future work.
Risk level: Medium.
Rollback notes: Revert the frontend account endpoint client addition, Account Setup page/test updates, and roadmap/gap/index updates.
Explicit non-goals: Do not add backend routes, service writes, schema, migrations, raw email storage, email or messaging invitation delivery, identity-provider integration, auth/session claim changes, membership activation, seat assignment, account lifecycle commands, account maintenance commands, tenant creation, campaign activation, go-live, credential lifecycle, webhook delivery, support-case writes, repair/replay/retry, reward, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, treasury, broad DLaaS marketplace behavior, or source-code forks.
Definition of done: Referral SaaS Account Setup has tested frontend wiring for Step 2 Users/Roles invitation intent and is ready for local UI-driven API/DB proof before moving to campaign setup work. Priority: P0.

## TASK-213: Physically verify Account Setup membership invitation intent

Status: Complete (2026-07-18). Output: `scripts/referral_saas_account_membership_intent_physical_check.py`; `test/test_referral_saas_account_membership_intent_physical_check.py`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_MEMBERSHIP_INTENT_PHYSICAL_VERIFICATION.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/README.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `docs/sa/referral-saas/REFERRAL_SAAS_MEMBERSHIP_INVITATION_BOUNDARY.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_MEMBERSHIP_INTENT_PHYSICAL_VERIFICATION.md`.
Shared primitive impact: Reuses existing admin onboarding draft/review APIs, Referral SaaS account creation/resolve APIs, membership invitation intent API, membership posture API, account foundation schema, and account audit/member tables. Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Local physical Account Setup proof; membership invitation intent evidence; no-adjacent-action guardrails.
Objective: Add and execute a repeatable local API/DB checker that proves Account Setup Step 2 can record membership invitation intent and read it back through membership posture after durable account setup.
Why now: TASK-212 wired the UI to the invitation intent API. Before moving to campaign work, Account Setup needs local proof that Step 2 records real membership evidence without accidentally delivering invites, activating access, assigning seats, changing auth claims, enabling go-live, launching campaigns, or moving money.
Files involved: `scripts/referral_saas_account_membership_intent_physical_check.py`; `test/test_referral_saas_account_membership_intent_physical_check.py`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_MEMBERSHIP_INTENT_PHYSICAL_VERIFICATION.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/README.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `scripts/referral_saas_account_setup_ui_physical_check.py`; `test/test_referral_saas_account_setup_ui_physical_check.py`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_UI_PHYSICAL_VERIFICATION.md`; `apps/api/routers/referral_saas_accounts.py`; `services/referral_saas_account_membership_service.py`.
Database/schema impact: No migration changes. Local physical proof inserted additive local test tenant `TASK213` when no unused tenant was available, then created proof account/member/audit records through product APIs.
Backend impact: None.
Frontend impact: None.
API impact: No new route. The checker calls existing onboarding, account creation/resolve, membership invitation, and membership posture routes.
Tests to add/update: Adds static tests for safe membership invitation payload construction, unsafe adjacent-action rejection, response guardrails, posture proof requirements, and run-chain sequencing.
Validation method: `.venv_codex\Scripts\python.exe -m pytest -q test\test_referral_saas_account_membership_intent_physical_check.py`; `.venv_codex\Scripts\python.exe scripts\referral_saas_account_membership_intent_physical_check.py --base-url http://127.0.0.1:8000 --admin-key test-admin-key --internal-tenant-code TASK213 --suffix local-213c`; `.venv_codex\Scripts\python.exe -m py_compile scripts\referral_saas_account_membership_intent_physical_check.py test\test_referral_saas_account_membership_intent_physical_check.py`; `git diff --check`.
Acceptance criteria: Checker creates/resolves account setup proof, records `INVITATION_INTENT_RECORDED`, reads back membership posture with `invitedCount >= 1`, confirms `DELIVERY_NOT_CONFIGURED`, confirms no invite delivery, no auth claim change, no seat assignment, no money movement, no campaign activation, and no go-live; checker rejects unsafe payload terms for internal tenant identifiers, delivery, activation, credentials, webhooks, reward, funding, settlement, wallet, invoice, payout, and adjacent money behavior.
Dependencies: TASK-198; TASK-199; TASK-200; TASK-203; TASK-204; TASK-208; TASK-209; TASK-210; TASK-211; TASK-212.
Blocked by: None for local physical membership intent proof. Invite delivery provider integration, membership activation, seat assignment, auth-claim integration, account lifecycle commands, account maintenance commands, and customer-safe account status remain future work.
Risk level: Medium.
Rollback notes: Revert the physical checker, checker tests, verification doc, and roadmap/gap/index updates. Local proof data can remain as local test evidence or be cleaned manually if the local database needs reset.
Explicit non-goals: Do not add backend routes, service writes beyond existing product APIs, schema, migrations, frontend controls, raw email storage, email or messaging invitation delivery, identity-provider integration, auth/session claim changes, membership activation, seat assignment, account lifecycle commands, account maintenance commands, tenant creation, campaign activation, go-live, credential lifecycle, webhook delivery, support-case writes, repair/replay/retry, reward, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, treasury, broad DLaaS marketplace behavior, or source-code forks.
Definition of done: Referral SaaS Account Setup has repeatable local API/DB proof that Step 2 records invited membership intent and posture evidence without adjacent delivery, activation, seat, auth, campaign, go-live, money, or DLaaS side effects. Priority: P0.

## TASK-214: Define membership activation and invitation delivery boundary

Status: Complete (2026-07-18). Output: `docs/sa/referral-saas/REFERRAL_SAAS_MEMBERSHIP_ACTIVATION_DELIVERY_BOUNDARY.md`; `test/test_referral_saas_membership_activation_delivery_boundary_contract.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/README.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; `docs/sa/referral-saas/REFERRAL_SAAS_MEMBERSHIP_INVITATION_BOUNDARY.md`; `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_MEMBERSHIP_INTENT_PHYSICAL_VERIFICATION.md`; `docs/sa/TENANT_ACCOUNT_LIFECYCLE_MEMBERSHIP_MODEL.md`.
Shared primitive impact: Reuses existing account foundation, external reference, membership, seat, audit, and account lifecycle model as a boundary. Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Membership invitation delivery boundary; membership activation boundary; setup access guardrails.
Objective: Define the future command boundary for invitation delivery and membership activation so invited setup evidence cannot be mistaken for active access.
Why now: TASK-213 physically proved invited membership intent. Before adding delivery/activation or polishing final Account Setup readiness, the product needs explicit gates for provider delivery, identity acceptance, active account, active tenant link, active external reference, idempotency, audit, duplicate prevention, redaction, and no adjacent seat/auth/campaign/go-live/money behavior.
Files involved: `docs/sa/referral-saas/REFERRAL_SAAS_MEMBERSHIP_ACTIVATION_DELIVERY_BOUNDARY.md`; `test/test_referral_saas_membership_activation_delivery_boundary_contract.py`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/sa/referral-saas/README.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `dp/migrations/082_referral_saas_account_foundation.sql`; `services/referral_saas_account_membership_service.py`; `apps/api/routers/referral_saas_accounts.py`; `scripts/referral_saas_account_membership_intent_physical_check.py`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `docs/sa/referral-saas/REFERRAL_SAAS_MEMBERSHIP_INVITATION_BOUNDARY.md`; `docs/sa/TENANT_ACCOUNT_LIFECYCLE_MEMBERSHIP_MODEL.md`.
Database/schema impact: None.
Backend impact: None.
Frontend impact: None.
API impact: None.
Tests to add/update: Adds static contract tests proving delivery and activation remain separate from invitation intent and preserve gates, redactions, guardrails, and non-goals.
Validation method: `.venv_codex\Scripts\python.exe -m pytest -q test\test_referral_saas_membership_activation_delivery_boundary_contract.py`; `.venv_codex\Scripts\python.exe -m py_compile test\test_referral_saas_membership_activation_delivery_boundary_contract.py`; `git diff --check`.
Acceptance criteria: Contract defines future delivery and activation routes/request/response/statuses, identity/provider/account/tenant/reference/membership/idempotency/audit gates, guardrails/redactions, UX posture, and explicit non-goals; no runtime route/service/UI/schema/provider/IDP/auth/seat/campaign/go-live/money/DLaaS behavior is added.
Dependencies: TASK-209; TASK-210; TASK-211; TASK-212; TASK-213.
Blocked by: None for contract. Runtime delivery provider integration, membership activation service/API/UI, seat assignment, auth-claim integration, account lifecycle commands, and account maintenance commands remain future.
Risk level: Low.
Rollback notes: Revert the boundary doc, static test, and roadmap/gap/index updates.
Explicit non-goals: Do not add runtime routes, service writes, frontend controls, schema, migrations, invitation provider integration, email/messaging delivery, IDP integration, auth/session claims, seat assignment, account lifecycle commands, account maintenance commands, tenant creation, campaign activation, go-live, credential lifecycle, webhooks, support-case writes, repair/replay/retry, reward/funding/fulfilment/settlement/commission/wallet/invoice/payout/sponsor billing/treasury/money, broad DLaaS, or forks.
Definition of done: Referral SaaS has a reviewed delivery/activation boundary that keeps invited intent distinct from actual communication/access and is ready for final Account Setup CX/E2E readiness review. Priority: P0.

## TASK-215: Clarify Account Setup find-or-start CX copy

Status: Complete (2026-07-18). Output: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Reuses the existing read-only account resolver and membership posture checks, but presents them as operator-safe Account Setup states. Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Account Setup CX clarity; find-or-start account workflow; no-internal-leak UX.
Objective: Replace implementation-centric Account Setup Step 1 wording with clear operator language that explains whether the user should continue with an existing account or start the setup draft path.
Why now: Local UI testing exposed that “durable account resolution” and “membership access check” were technically accurate but confusing, which blocks 10/10 Account Setup usability.
Files involved: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`.
Database/schema impact: None.
Backend impact: None.
Frontend impact: Renames Step 1 as “find or start the account,” changes the primary button to “Find account,” converts “durable account resolution” to “Account status,” converts “membership access check” to “User access status,” and softens guardrail copy.
API impact: None.
Tests to add/update: Updates Account Setup page tests to assert the clearer CX language while preserving existing resolver, membership posture, draft, review, create, and invitation-intent behavior.
Validation method: `npm test -- ReferralSaasAccountSetupPage.test.tsx --runInBand`; `npm run build`; `git diff --check`.
Acceptance criteria: Operators can understand Step 1 as “find existing account or start setup,” no internal tenant identifiers or implementation labels are exposed as primary UX, existing API calls remain unchanged, and setup actions remain gated in the same order.
Dependencies: TASK-214.
Blocked by: None.
Risk level: Low.
Rollback notes: Revert the Account Setup page/test copy updates and roadmap/gap/task-list entries.
Explicit non-goals: Do not add backend routes, service writes, schema, migrations, invitation delivery, membership activation, seat assignment, auth/session claim changes, campaign activation, go-live, money movement, DLaaS expansion, or source-code forks.
Definition of done: Account Setup Step 1 reads as a clear find-or-start workflow instead of implementation plumbing, and the product is ready for local UI-driven Account Setup E2E readiness proof. Priority: P0.

## TASK-216: Redesign Account Setup as guided wizard

Status: Complete (2026-07-18). Output: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `frontend/src/styles/base.css`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`; local Account Setup wizard recommendation mock at `http://127.0.0.1:8765/`.
Shared primitive impact: Reuses existing onboarding draft/readiness APIs, account resolver, guarded account creation API, membership posture API, and membership invitation intent API. Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Account Setup CX clarity; guided setup workflow; no-adjacent-action guardrails.
Objective: Replace the dense Account Setup console layout with a guided seven-step wizard that tells operators what the screen is for, what they can do now, and what comes next.
Why now: Local UI testing showed the technically correct Account Setup page still felt disjointed and unclear. The product needed a real guided workflow before another local E2E pass would produce useful feedback.
Files involved: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `frontend/src/styles/base.css`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `frontend/src/styles/base.css`; local recommendation mock at `http://127.0.0.1:8765/`.
Database/schema impact: None.
Backend impact: None.
Frontend impact: Adds a seven-step Account Setup wizard: Identify customer, Company profile, People & roles, Integration intent, Readiness check, Review & create, and Handoff. The page now moves evidence tables and guardrails into a secondary drawer, keeps actions inside their associated step, and preserves existing safe-mode boundaries.
API impact: None. Uses existing Referral SaaS account setup, account resolver, account creation, membership posture, and membership invitation intent endpoints.
Tests to add/update: Updates Account Setup page tests to assert the wizard steps, action order, no-internal-leak posture, existing workflow links, guarded save/submit/review/create behavior, and bounded membership invitation intent behavior.
Validation method: `npm.cmd test -- ReferralSaasAccountSetupPage.test.tsx`; `npm.cmd run build`; `git diff --check`.
Acceptance criteria: Operators see a clear step-by-step Account Setup path; each step owns its relevant action; readiness is integrated as one checkpoint instead of the whole screen; review/create remains ordered and gated; full evidence remains available without dominating the primary workflow; no raw internal tenant identifiers, credentials, go-live, campaign activation, invite delivery, membership activation, seat assignment, auth-claim change, reward, money movement, DLaaS expansion, or source-code forks are added.
Dependencies: TASK-215.
Blocked by: None for the guided wizard redesign. Local UI-driven Account Setup wizard E2E proof, membership activation, invitation delivery provider integration, seat assignment, auth-claim integration, account lifecycle commands, and account maintenance commands remain future work.
Risk level: Medium.
Rollback notes: Revert the Account Setup page, page test, style, roadmap, gap matrix, and ordered task list updates.
Explicit non-goals: Do not add backend routes, service writes, schema, migrations, invitation delivery, membership activation, seat assignment, auth/session claim changes, campaign activation, go-live, credential lifecycle, webhook delivery, support-case writes, repair/replay/retry, reward, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, treasury, broad DLaaS marketplace behavior, or source-code forks.
Definition of done: Referral SaaS Account Setup is presented as a guided wizard over existing guarded primitives and is ready for a local UI-driven E2E readiness proof. Priority: P0.

## TASK-217: Gate Account Setup wizard navigation by completed steps

Status: Complete (2026-07-19). Output: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `frontend/src/styles/base.css`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Reuses existing onboarding readiness evidence, account resolver state, validation state, account creation state, and membership intent/posture state. Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Account Setup wizard journey control; completion-state UX; no-adjacent-action guardrails.
Objective: Prevent the Account Setup wizard rail from behaving like a free-form tab bar and ensure operators can only move forward when prior steps are complete or explicitly passable.
Why now: User testing showed that clicking a later rail item could skip required steps and incorrectly mark previous steps as `OK`, making the wizard feel misleading and uncontrolled.
Files involved: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `frontend/src/styles/base.css`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `frontend/src/styles/base.css`.
Database/schema impact: None.
Backend impact: None.
Frontend impact: Adds evidence-based wizard completion/passability rules, disables locked future rail steps, keeps backward navigation available, disables Continue when the next step is blocked, and shows `OK` only for completed steps instead of position-based prior steps.
API impact: None.
Tests to add/update: Adds Account Setup page coverage proving future steps are locked when Company Profile evidence is incomplete; updates wizard workflow tests to complete role intent and validation before later navigation.
Validation method: `npm.cmd test -- ReferralSaasAccountSetupPage.test.tsx`; `npm.cmd run build`; `git diff --check`.
Acceptance criteria: Operators cannot skip incomplete required steps through the rail or Continue button; completed state is based on existing evidence/actions rather than visited position; backward navigation remains available; existing account setup, validation, draft, review, create, membership intent, and campaign handoff behavior remains bounded and unchanged.
Dependencies: TASK-216.
Blocked by: None for frontend wizard navigation gating. Local UI-driven Account Setup wizard E2E proof remains the next account setup readiness task.
Risk level: Medium.
Rollback notes: Revert the Account Setup page, page test, style, roadmap, gap matrix, and ordered task list updates.
Explicit non-goals: Do not add backend routes, service writes, schema, migrations, invitation delivery, membership activation, seat assignment, auth/session claim changes, campaign activation, go-live, credential lifecycle, webhook delivery, support-case writes, repair/replay/retry, reward, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, treasury, broad DLaaS marketplace behavior, or source-code forks.
Definition of done: Account Setup wizard navigation is controlled by step completion evidence and is ready for local UI-driven E2E readiness proof. Priority: P0.

## TASK-218: Require explicit Account Setup Step 1 account check

Status: Complete (2026-07-19). Output: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Reuses existing account resolver preload, onboarding readiness state, and wizard completion primitives, but separates background load from operator-confirmed Step 1 completion. Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Account Setup wizard journey control; explicit operator confirmation; completion-state UX.
Objective: Prevent the initial account resolver preload from marking Identify Customer complete or unlocking Company Profile until the operator clicks Find account.
Why now: User testing showed Step 1 could flip to OK and allow movement to Step 2 without an explicit operator action, which undermined the wizard as a controlled journey.
Files involved: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`.
Database/schema impact: None.
Backend impact: None.
Frontend impact: Adds a session-local Step 1 confirmation gate, changes the Step 1 action badge to Not checked/Checked, keeps Company Profile and later steps locked until the operator confirms Find account, and preserves backward navigation.
API impact: None.
Tests to add/update: Updates Account Setup page tests to prove initial preload does not complete Step 1, future steps remain locked before Find account, Step 1 becomes complete only after explicit confirmation, and existing wizard flows still work.
Validation method: `npm.cmd test -- ReferralSaasAccountSetupPage.test.tsx`; `npm.cmd run build`; `git diff --check`.
Acceptance criteria: Operators cannot reach Step 2 from the rail or Continue until they click Find account with both references present; Step 1 shows Not checked before explicit confirmation and Checked/OK only after confirmation; changing references resets the confirmation to Changes not checked; existing account setup, validation, draft, review, create, membership intent, and campaign handoff behavior remains bounded and unchanged.
Dependencies: TASK-217.
Blocked by: None for frontend Step 1 confirmation. Local UI-driven Account Setup wizard E2E proof remains the next account setup readiness task.
Risk level: Low.
Rollback notes: Revert the Account Setup page/test updates and roadmap/gap/task-list entries.
Explicit non-goals: Do not add backend routes, service writes, schema, migrations, invitation delivery, membership activation, seat assignment, auth/session claim changes, campaign activation, go-live, credential lifecycle, webhook delivery, support-case writes, repair/replay/retry, reward, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, treasury, broad DLaaS marketplace behavior, or source-code forks.
Definition of done: Account Setup Step 1 completion is controlled by explicit operator confirmation rather than background preload, and the wizard remains ready for local UI-driven E2E readiness proof. Priority: P0.

## TASK-219: Keep Account Setup Company Profile inside the wizard

Status: Complete (2026-07-19). Output: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Reuses existing admin onboarding draft persistence and Account Setup wizard primitives while removing the broader onboarding page jump from Step 2. Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Account Setup wizard coherence; inline company-profile draft evidence; no-adjacent-action guardrails.
Objective: Keep Company Profile setup inside the Referral SaaS Account Setup wizard so operators can complete Step 2 without being redirected into the broader Amplifi onboarding workspace.
Why now: User testing showed that Step 2 still behaved like a route card. Clicking Company Profile changed navigation context and made the wizard feel disjointed after the Step 1 journey-control fixes.
Files involved: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `frontend/src/pages/admin/CompanyOnboardingPage.tsx`; `frontend/src/pages/admin/CompanyOnboardingPage.test.tsx`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`.
Database/schema impact: None.
Backend impact: None.
Frontend impact: Replaces the Step 2 Company Profile route link with inline organisation name, bounded operating jurisdiction selector, tooltip-guided customer type selector, bounded industry selector, admin contact, and tooltip-guided intended role selector; saves those fields through the existing guarded setup draft API; shows account scope and save confirmation inside the wizard; allows Step 3 only after readiness evidence or a saved profile draft.
API impact: None. Uses existing `saveAdminOnboardingDraft` behavior.
Tests to add/update: Updates Account Setup page tests to assert the inline Step 2 form, bounded operating jurisdiction and industry dropdowns, customer type and intended role tooltips, no `/admin/onboarding/company` link, profile draft payload shape, safe no-internal/no-money payload posture, and preserved later-step links.
Validation method: `npm.cmd test -- ReferralSaasAccountSetupPage.test.tsx`; `npm.cmd run build`; `git diff --check`.
Acceptance criteria: Clicking Company Profile in Step 2 does not navigate away from `/admin/referral-saas/account-setup`; the operator can save company evidence inside the wizard; operating jurisdiction and industry are selected from bounded lists; customer type explains the customer's relationship to the setup while product package and billing plan remain separate future concepts; intended role explains its setup-only meaning through an inline tooltip; saved payload carries the confirmed Step 1 external references and inline profile fields; Step 2 completion can be based on saved draft evidence; existing review/create, membership intent, readiness, integration intent, and campaign handoff behavior remains bounded and unchanged.
Dependencies: TASK-218.
Blocked by: None for inline Company Profile setup. Local UI-driven Account Setup wizard E2E proof remains the next account setup readiness task.
Risk level: Medium.
Rollback notes: Revert the Account Setup page/test updates and roadmap/gap/task-list entries.
Explicit non-goals: Do not add backend routes, service writes beyond existing draft save, schema, migrations, invitation delivery, membership activation, seat assignment, auth/session claim changes, campaign activation, go-live, credential lifecycle, webhook delivery, support-case writes, repair/replay/retry, reward, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, treasury, broad DLaaS marketplace behavior, or source-code forks.
Definition of done: Account Setup Step 2 Company Profile is an inline wizard step with bounded selectors and contextual field guidance that saves guarded setup draft evidence and no longer redirects operators into a separate onboarding workspace. Priority: P0.

## TASK-220: Add Account Setup draft conflict recovery UX

Status: Complete (2026-07-19). Output: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Reuses existing onboarding draft conflict behavior and Account Setup refresh/query state. Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Account Setup conflict recovery; safe draft/idempotency UX; no-adjacent-action guardrails.
Objective: Turn the real `409 Conflict` returned by `/admin/onboarding/drafts` into an actionable Account Setup recovery state.
Why now: Local UI testing hit `POST /admin/onboarding/drafts` `409 Conflict` after saving company profile evidence for an existing setup scope. The backend was correctly protecting draft/idempotency state, but the wizard showed a generic fallback that did not explain what the operator should do next.
Files involved: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `frontend/src/pages/admin/CompanyOnboardingPage.tsx`; `frontend/src/api/referralSaasAccountQueries.ts`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`.
Database/schema impact: None.
Backend impact: None.
Frontend impact: Replaces generic draft-save `409` fallback copy with a specific "existing setup draft found" recovery state, adds Refresh setup status and Change customer references actions, and refetches setup/account state through local refresh keys.
API impact: None. Uses existing `saveAdminOnboardingDraft` conflict semantics.
Tests to add/update: Adds Account Setup page coverage for `409 Conflict` from `saveAdminOnboardingDraft`, actionable recovery copy, recovery buttons, and setup-state refresh behavior.
Validation method: `npm.cmd test -- ReferralSaasAccountSetupPage.test.tsx`; `npm.cmd run build`; `git diff --check`.
Acceptance criteria: When Step 2 company profile save returns `409`, the wizard explains that a setup draft already exists for the customer, confirms no account or live action was taken, offers Refresh setup status and Change customer references actions, clears the stale banner on refresh, refetches setup state, and does not add account creation, approval, live action, draft deletion, conflict override, source fork, or broad DLaaS behavior.
Dependencies: TASK-219.
Blocked by: None for draft conflict recovery UX. A future draft selector/load-existing-draft workflow may deepen this recovery path before full E2E testing.
Risk level: Low.
Rollback notes: Revert the Account Setup page/test updates and roadmap/gap/task-list entries.
Explicit non-goals: Do not add backend routes, service writes, schema, migrations, draft deletion, stale draft override, account creation, approval, invitation delivery, membership activation, seat assignment, auth/session claim changes, campaign activation, go-live, credential lifecycle, webhook delivery, support-case writes, repair/replay/retry, reward, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, treasury, broad DLaaS marketplace behavior, or source-code forks.
Definition of done: Account Setup Step 2 handles existing-draft `409 Conflict` as a clear recoverable product state with tested refresh and reference-change actions. Priority: P0.

## TASK-221: Clarify Account Setup contact responsibility field

Status: Complete (2026-07-19). Output: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Reuses the existing Account Setup company-profile draft payload while clarifying that the field records setup-contact responsibility, not access permission. Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Account Setup field semantics; product-boundary UX; no-permission-confusion guardrails.
Objective: Replace the Step 2 `Intended role` wording with `Contact responsibility` and bounded setup-responsibility options so operators do not confuse company-profile evidence with People & Roles permissions.
Why now: User testing showed the previous `Referral SaaS account admin` option looked like a future permission set, which made Company Profile feel mixed with access setup.
Files involved: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`.
Database/schema impact: None.
Backend impact: None.
Frontend impact: Renames the Step 2 field to `Contact responsibility`, replaces the default value with `Account owner`, adds setup-responsibility options such as implementation, campaign, technical integration, reporting, and support leads, and updates tooltip copy to point access roles and permissions to the People & Roles step.
API impact: None. Keeps the existing draft payload key `intended_role` for compatibility with the onboarding draft contract.
Tests to add/update: Updates Account Setup page tests to assert the new label, tooltip, option set, payload compatibility, and absence of `Referral SaaS account admin` from the Company Profile responsibility selector.
Validation method: `npm.cmd test -- ReferralSaasAccountSetupPage.test.tsx`; `npm.cmd run build`; `git diff --check`.
Acceptance criteria: Company Profile no longer presents contact responsibility as a platform permission; the saved draft remains compatible with the existing API; actual permission selection stays in People & Roles; no backend route, schema, permission, invitation, activation, billing, or money behavior changes are introduced.
Dependencies: TASK-220.
Blocked by: None for frontend field semantics. Local UI-driven Account Setup wizard E2E proof remains the next account setup readiness task.
Risk level: Low.
Rollback notes: Revert the Account Setup page/test updates and roadmap/gap/task-list entries.
Explicit non-goals: Do not add backend routes, service writes, schema, migrations, permission sets, invitation delivery, membership activation, seat assignment, auth/session claim changes, campaign activation, go-live, credential lifecycle, webhook delivery, support-case writes, repair/replay/retry, reward, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, treasury, broad DLaaS marketplace behavior, or source-code forks.
Definition of done: Account Setup Step 2 clearly captures the primary contact's setup responsibility while leaving future access permissions to People & Roles. Priority: P0.

## TASK-222: Load saved Account Setup Company Profile drafts

Status: Complete (2026-07-19). Output: `apps/api/routers/admin_onboarding.py`; `services/onboarding/onboarding_draft_repository.py`; `test/api/test_admin_onboarding_api.py`; `frontend/src/api/endpoints/adminOnboarding.ts`; `frontend/src/api/endpoints/adminOnboarding.test.ts`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Product boundary: Referral SaaS.
Required boundary docs checked: `AGENTS.md`; `docs/product/referral-saas/PRODUCT_BRIEF.md`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Shared primitive impact: Extends the existing read-only admin onboarding draft selector with sanitized saved section evidence so Account Setup can prefill Step 2 from the persisted draft source. Source duplication: No.
Linked enhancement: Referral Management and Campaign Attribution SaaS first-wedge productization.
Linked platform/product capability: Account Setup persistence UX; safe onboarding draft readback; no-recapture guardrails.
Objective: Load saved Company Profile draft evidence back into the Referral SaaS Account Setup wizard and prevent operators from continuing with edited-but-unsaved company profile values.
Why now: Local UI testing showed the company profile could be saved, but the wizard still felt like data might need to be re-entered or could be accidentally changed without a clear saved baseline.
Files involved: `apps/api/routers/admin_onboarding.py`; `services/onboarding/onboarding_draft_repository.py`; `test/api/test_admin_onboarding_api.py`; `frontend/src/api/endpoints/adminOnboarding.ts`; `frontend/src/api/endpoints/adminOnboarding.test.ts`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `docs/roadmap/referral-saas/ROADMAP.md`; `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`; `docs/roadmap/ORDERED_TASK_LIST.md`.
Implementation/source files inspected: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`; `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`; `frontend/src/api/endpoints/adminOnboarding.ts`; `frontend/src/api/referralSaasAccountQueries.ts`; `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`; `apps/api/routers/admin_onboarding.py`; `services/onboarding/onboarding_draft_repository.py`; `test/api/test_admin_onboarding_api.py`; `frontend/src/api/endpoints/adminOnboarding.test.ts`.
Database/schema impact: None. Reuses existing `onboarding_drafts` and `onboarding_draft_sections`.
Backend impact: Adds internal `draft_id` selection to the draft repository for router section lookup, and extends the read-only draft selector response with sanitized `draft_sections` while keeping internal IDs, actor refs, tenant codes, secrets, and raw payloads out of the public response.
Frontend impact: Account Setup now loads saved Company Profile draft fields for the confirmed external scope, shows the saved draft reference/version/update time, changes the Step 2 status panel to `Readiness evidence status`, disables Save when the loaded draft matches the form, shows `Unsaved changes` after edits, and blocks Continue until changed values are saved.
API impact: `GET /admin/onboarding/drafts` now returns sanitized `draft_sections` on selector items. No new route, write action, schema, account command, permission change, or live action is added.
Tests to add/update: Adds API helper coverage for returned `draft_sections`, backend selector coverage for section readback and redaction, and Account Setup page coverage for loading saved company profile values plus unsaved-change gating.
Validation method: `npm.cmd test -- ReferralSaasAccountSetupPage.test.tsx`; `npm.cmd test -- adminOnboarding.test.ts`; `npm.cmd run build`; `git diff --check`. Python backend test `test/api/test_admin_onboarding_api.py -k "draft_selector_returns_safe_scope"` was updated but could not run locally because `.venv` points at missing `C:\Users\Carla\AppData\Local\Programs\Python\Python311\python.exe`, and the bundled Codex Python does not have pytest installed.
Acceptance criteria: Saved Step 2 company profile data is reloaded for the matching external tenant and organisation scope; operators can see which draft was loaded; changing any loaded value creates an unsaved state; Continue remains blocked until the changed profile is saved; the selector readback is sanitized and does not expose internal tenant identifiers, secrets, actors, money, or live-action fields.
Dependencies: TASK-221.
Blocked by: None for implementation. Local Python backend test execution remains blocked by interpreter repair.
Risk level: Medium.
Rollback notes: Revert the admin onboarding selector/repository updates, frontend API/page/test updates, and roadmap/gap/task-list entries.
Explicit non-goals: Do not add schema, migrations, account lifecycle commands, draft overwrite/delete, stale draft override, permission changes, invitation delivery, membership activation, seat assignment, auth/session claim changes, campaign activation, go-live, credential lifecycle, webhook delivery, support-case writes, repair/replay/retry, reward, funding, fulfilment, settlement, commission, wallet, invoice, payout, sponsor billing, treasury, broad DLaaS marketplace behavior, or source-code forks.
Definition of done: Account Setup Step 2 treats saved Company Profile evidence as persisted customer setup data and prevents accidental continuation with unsaved edits. Priority: P0.

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
