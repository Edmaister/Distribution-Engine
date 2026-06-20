# DLaaS Agent Runbook

This runbook explains how Codex should execute DLaaS roadmap work without manual prompting for every step.

It is an operating guide only. It must not be used to implement product features outside the ordered task list.

## Source Of Truth

Codex must read these sources before major work:

1. `AGENTS.md`
2. `docs/product/DLAAS_TARGET_STATE.md`
3. `docs/sa/`
4. `docs/sa/CAPABILITY_GAP_MATRIX.md`
5. `docs/roadmap/ENHANCEMENT_BACKLOG.md`
6. `docs/roadmap/ORDERED_TASK_LIST.md`
7. `docs/agent/DLAAS_AGENT_STOP_CONDITIONS.md`

The workflow is:

```text
Target State -> SA Docs -> Gap Matrix -> Enhancement Backlog -> Ordered Task List -> Implementation -> Tests -> Docs Update
```

## Runner Cycle

1. Read the source documents.
2. Confirm completed and blocked tasks in `docs/roadmap/ORDERED_TASK_LIST.md`.
3. Select the highest-priority unblocked task by dependency order.
4. Run the readiness checklist from `.agents/skills/dlaas-task-runner/SKILL.md`.
5. If readiness fails, stop and report the missing information.
6. If readiness passes, restate the task scope before editing.
7. Implement only that one task.
8. Run relevant tests or docs validation.
9. Review against `docs/agent/DLAAS_AGENT_STOP_CONDITIONS.md`.
10. Run the Definition of Done review prompt.
11. Update task status and related docs.
12. Create follow-up tasks for any gaps.
13. Stop and summarize.

## Branch And Review Guidance

- Use one branch or PR per task where possible.
- Keep each task small enough to review independently.
- Do not auto-merge.
- Do not bundle unrelated fixes.
- If a task expands beyond one reviewable unit, stop and split it into follow-up tasks.

## Git Baseline Requirement Before Autonomous Task Execution

Autonomous DLaaS task execution requires a clean Git baseline before product work begins. Codex must not run product tasks while core source folders are untracked because diffs, rollback safety, branch review, and PR scope cannot be trusted.

Baseline inspection from `TASK-030`:

- Current branch: `master`.
- GitHub remote detected: No remote was configured by `git remote -v`.
- Recent commit: `dd91298 Add DLaaS agent runner framework`.
- Current status included modified roadmap docs plus many untracked product and local files.
- No `git add`, `git commit`, file deletion, product-code change, schema change, frontend build, or live DB check was performed for this classification.

Untracked baseline classification:

| Path | Classification | Rationale |
|---|---|---|
| `.docker-codex-config/` | ignore | Local Docker/Codex state, including lock files; not source. |
| `.dockerignore` | commit to baseline | Project container config. |
| `.gitignore` | commit to baseline | Required safety guard for local files, runtime outputs, archives, caches, and secrets/certs. |
| `CONTRIBUTING.md` | commit to baseline | Project contribution documentation. |
| `Core Domain Features.txt` | inspect before deciding | Legacy/product notes; review for accuracy before baseline commit. |
| `Dockerfile` | commit to baseline | Project runtime/build source. |
| `Dockerfile.worker` | commit to baseline | Worker runtime/build source. |
| `Front-end Blueprint.txt` | inspect before deciding | Legacy frontend plan; review against DLaaS docs before commit. |
| `LICENSE` | commit to baseline | Project license text. |
| `LICENSE.zip` | delete/archive outside repo | Large archive; do not commit generated/binary archive without explicit reason. |
| `Support Queries.txt` | inspect before deciding | May contain operational queries or sensitive patterns; review before commit. |
| `apps/` | commit to baseline | Core API and worker product source. |
| `body` | delete/archive outside repo | Empty local artifact; not source. |
| `config/` | inspect before deciding | Configuration source may be valid, but prod/dev files must be reviewed for secrets. |
| `coveragerc` | commit to baseline | Test coverage configuration. |
| `deploy/` | commit to baseline | Deployment manifests; review as part of baseline. |
| `design-qa.md` | commit to baseline | Project QA documentation. |
| `docker` | delete/archive outside repo | Empty local artifact; not source. |
| `dp/` | commit to baseline | Database migrations/seeds/docs; core source for DLaaS backend truth. |
| `env.example` | commit to baseline | Example environment template; confirm no real secrets before commit. |
| `examples/` | commit to baseline | Partner/client examples. |
| `folder strucuture.txt` | inspect before deciding | Legacy documentation with typo; review before commit. |
| `frontend/` | commit to baseline | Existing frontend source should be tracked as baseline before future UI work. |
| `github/` | inspect before deciding | Non-standard GitHub folder; compare with `.github/` before commit. |
| `helm/` | inspect before deciding | Helm source is likely valid, but shortcut files and secret templates need review. |
| `loadtests/` | commit to baseline | Load test source. |
| `local_worker.py` | commit to baseline | Local worker entrypoint/source. |
| `monitoring/` | inspect before deciding | Monitoring source is likely valid, but `secrets.yaml` and infra files need review. |
| `project quickstart instructions.md` | commit to baseline | Project onboarding documentation. |
| `pyproject.toml` | commit to baseline | Python project configuration. |
| `pytest.ini` | commit to baseline | Test configuration. |
| `requirements.txt` | commit to baseline | Python dependency manifest. |
| `run_test.ps1` | commit to baseline | Test helper script. |
| `run_tests.ps1` | inspect before deciding | Empty script; decide whether to remove, fill, or keep. |
| `scripts/` | commit to baseline | Operational/dev scripts; review no secrets before commit. |
| `services/` | commit to baseline | Core service-layer product source. |
| `test/` | commit to baseline | Test suite. |
| `utils/` | commit to baseline | Core utility source. |
| `welcome-to-docker/` | inspect before deciding | Looks like sample/tutorial material; confirm whether project-owned. |

Files and folders that must never be committed:

- `.env` and `.env.*` except `env.example`.
- `.venv/`, `.venv_codex/`, `venv/`, and `ENV/`.
- `.coverage`, `.coverage.*`, `htmlcov/`, coverage XML, and test caches.
- `local_events.jsonl`, `outputs/`, `repositories/`, `.docker-codex-config/`, and local runtime logs.
- Dependency/build artifacts such as `node_modules/`, `dist/`, `build/`, `.next/`, and frontend coverage output.
- Secrets, certificates, keys, provider payloads, access tokens, and files matching `*.pem`, `*.key`, `*.crt`, `*.p12`, or `*.pfx`.
- Large/generated archives such as `*.zip` unless explicitly reviewed and approved.

Recommended safe commit sequence:

1. Commit `.gitignore` first so unsafe local artifacts stay out of later diffs.
2. Commit core project baseline in small groups: root project config/docs, backend source, database migrations/seeds, services/utils, API/workers, tests, scripts, deployment/helm/monitoring after secret review, and frontend source.
3. Commit docs/agent framework only if it is not already tracked in the current branch.
4. Leave `inspect before deciding` and `delete/archive outside repo` items unstaged until a human reviews them.

Until this baseline is committed or deliberately ignored, the DLaaS agent runner is not ready for autonomous branch/PR execution.

Post-baseline GitHub readiness verification from `TASK-031`:

- Current branch: `main`.
- Branch tracking: `main` tracks `origin/main`.
- GitHub remote: `https://github.com/Edmaister/Distribution-Engine.git`.
- Latest baseline commit observed: `d9c538d Add core product source baseline`.
- Baseline push status: pushed to `origin/main` according to branch tracking and commit history.
- Unsafe local files were not tracked by Git and were ignored by `.gitignore`: `.env`, virtual environments, coverage artifacts, `local_events.jsonl`, `outputs/`, `.docker-codex-config/`, and `*.zip`.

Remaining untracked items after the baseline push:

| Path | Recommendation | Blocks autonomous agent execution? | Rationale |
|---|---|---|---|
| `Core Domain Features.txt` | inspect before deciding | No, if left untracked and not touched by agent tasks | Legacy product notes; review for accuracy before committing. |
| `Front-end Blueprint.txt` | inspect before deciding | No, if left untracked and not touched by agent tasks | Legacy frontend plan; review against DLaaS source-of-truth docs. |
| `Support Queries.txt` | inspect before deciding | No, if left untracked and not touched by agent tasks | May include operational query patterns; review for sensitivity. |
| `body` | delete/archive outside repo | No | Empty local artifact. |
| `config/` | inspect before deciding | Yes for config/auth/deploy tasks | Contains environment/config files; review for secrets and decide source ownership. |
| `docker` | delete/archive outside repo | No | Empty local artifact. |
| `eline readiness` | inspect before deciding | No, but should be archived or removed outside a task | Oddly named local artifact; review before keeping. |
| `folder strucuture.txt` | inspect before deciding | No | Legacy documentation with typo; review before committing. |
| `github/` | inspect before deciding | Yes for CI/CD tasks | Non-standard GitHub folder; compare with `.github/` before committing. |
| `helm/` | inspect before deciding | Yes for deployment tasks | Helm chart appears source-like, but includes a shortcut file and secret template that need review. |
| `monitoring/` | inspect before deciding | Yes for observability/deployment tasks | Monitoring/infra files include `secrets.yaml`; review before committing. |
| `run_tests.ps1` | inspect before deciding | No | Empty script; decide whether to keep, populate, or archive. |
| `welcome-to-docker/` | inspect before deciding | No | Sample/tutorial material; confirm whether project-owned. |

Autonomous DLaaS agent execution may proceed only for tasks that do not depend on the remaining untracked config, CI/CD, Helm, or monitoring assets. Before deployment, auth/config, observability, infrastructure, or CI/CD tasks, clean or classify those untracked areas first.

Remaining-untracked cleanup review from `TASK-032`:

- This was a Git/readiness cleanup review only.
- No files were staged, committed, deleted, archived, or modified outside documentation.
- No product code, business logic, database schema, frontend UI, or live DB checks were changed or run.
- `run_test.ps1` is tracked and contains the active local test runner; `run_tests.ps1` is empty and should not replace it.
- `docker` and `body` are empty files, not folders.
- `welcome-to-docker/` is a nested sample repository with its own `.git/`; it is not part of the DLaaS product baseline.
- `github/` is not the active GitHub Actions folder. `.github/` contains the tracked Codex prompts and CI workflow; `github/` appears to be legacy/useful deployment material that should be reviewed and migrated under `.github/` only if still wanted.

Remaining untracked classification:

| Path | Classification | Rationale |
|---|---|---|
| `Core Domain Features.txt` | archive outside repo | Legacy product notes with stale terminology and encoding artifacts; current DLaaS docs are the source of truth. |
| `Front-end Blueprint.txt` | archive outside repo | Legacy/generic frontend plan; not aligned to DLaaS control-plane guardrails. |
| `Support Queries.txt` | archive outside repo | Contains operational SQL examples and specific-looking IDs; do not commit without redaction review. |
| `body` | delete after human confirmation | Empty accidental file. |
| `config/` | keep untracked temporarily | Source-like config exists, but `settings.dev.yaml`/`settings.prod.yaml` contain placeholder DSNs and must be reviewed before committing. `config/__pycache__/` remains ignored. |
| `docker` | delete after human confirmation | Empty accidental file. |
| `eline readiness` | delete after human confirmation | Accidental artifact containing Git diff output from a prior readiness step. |
| `folder strucuture.txt` | archive outside repo | Legacy architecture note with typo and encoding artifacts; not source-of-truth. |
| `github/` | keep untracked temporarily | Useful legacy CI/CD docs and deploy workflows, but should be compared/migrated into `.github/` rather than committed as a parallel folder. |
| `helm/` | keep untracked temporarily | Helm chart is useful deployment source, but includes a Windows shortcut and secret templates that require review before commit. |
| `monitoring/` | keep untracked temporarily | Useful observability/infra source, but includes `secrets.yaml`, placeholder secrets, and hardcoded dev passwords that require cleanup before commit. |
| `run_tests.ps1` | delete after human confirmation | Empty duplicate; `run_test.ps1` is the tracked runner. |
| `welcome-to-docker/` | archive outside repo | Docker tutorial/sample app with nested `.git/`; not part of this product. |

Secret and sensitive-file findings:

- `config/settings.dev.yaml` and `config/settings.prod.yaml` include placeholder DSNs with `appuser:apppass`.
- `helm/referrals/templates/secret.yaml` is a secret template using Helm values; `helm/referrals/values.yaml` leaves secret values empty.
- `helm/referrals/README_HELM.md` shows example DSNs and secret names.
- `github/workflows/deploy_*.yml` references GitHub Secrets such as `REMOTE_HOST`, `REMOTE_USER`, `REMOTE_SSH_KEY`, `KUBE_CONFIG`, and `APP_DB_DSN`; no literal secret values were found there.
- `monitoring/infra/k8s/secrets.yaml` contains placeholder secret values such as `please-change-me`.
- `monitoring/infra/docker/docker-compose.yaml` and `monitoring/infra/k8s/configmaps.yaml` include local/dev DSNs and passwords.
- No private keys or certificate bodies were found in the inspected untracked files.

Final readiness policy:

- Backend and documentation tasks may proceed if they do not depend on untracked `config/`, `github/`, `helm/`, or `monitoring/`.
- Frontend tasks may proceed from the tracked frontend baseline, but must not rely on legacy `Front-end Blueprint.txt`.
- CI/CD tasks are blocked until `github/` is migrated, ignored, or archived.
- Deployment tasks are blocked until `config/`, `helm/`, and `monitoring/infra` are reviewed and cleaned.
- Monitoring tasks are blocked until `monitoring/` is reviewed and secret placeholders are converted to safe examples or ignored.
- Broad autonomous execution remains blocked until the remaining untracked items are either committed after review, ignored, archived, or deleted after human confirmation.

Accidental local artifact review from `TASK-033`:

- This was a Git/workspace cleanup review only.
- No files were staged, committed, deleted, archived, or modified outside documentation.
- `body` is an empty file and should be deleted after human confirmation.
- `docker` is an empty file, not a Docker folder, and should be deleted after human confirmation.
- `eline readiness` is an accidental readiness artifact containing Git diff output and should be deleted after human confirmation or archived outside the repo if the diff evidence is still wanted.
- `run_tests.ps1` is an empty duplicate test-runner file. `run_test.ps1` is tracked and contains the active PowerShell test runner, so `run_tests.ps1` should be deleted after human confirmation.

These four files do not block backend/docs, frontend, CI/CD, deployment, or monitoring tasks if they remain untracked and untouched, but they do block a fully clean broad autonomous workspace until removed or archived.

Config/infra templating update from `TASK-036`:

- Credential-looking DSNs in `config/settings.dev.yaml`, `config/settings.prod.yaml`, and `config/settings.py` were replaced with placeholders or environment-variable references.
- Reviewed deploy workflows were copied from `github/workflows/` into `.github/workflows/`; the legacy `github/` folder was left in place.
- `github/docs/CI_CD.md` was copied into `docs/CI_CD.md` with secret-handling guidance.
- The Helm README install example now uses a placeholder secret value, and `helm/referrals/values.yaml` continues to keep secret values empty.
- Local credential-looking DSNs/passwords in `monitoring/infra/docker/docker-compose.yaml` and `monitoring/infra/k8s/configmaps.yaml` were replaced with placeholders or environment-variable references.
- `monitoring/infra/k8s/secrets.yaml` remains untracked and must stay ignored unless it is converted to a safe `*.example.yaml` file in a later task.
- `.gitignore` now ignores `*.lnk` and `monitoring/infra/k8s/secrets.yaml`.

After TASK-036, CI/CD workflow migration is ready for review and staging. Deployment, Helm, and monitoring assets are safer to commit, but broad autonomous execution still depends on either staging the safe baseline or explicitly archiving/ignoring remaining legacy/untracked folders.

Legacy artifact review from `TASK-037`:

- This was a Git/workspace cleanup review only.
- No files were staged, committed, deleted, moved, archived, or modified outside documentation.
- `github/` has been superseded by copied files in `.github/workflows/` and `docs/CI_CD.md`; the legacy folder can be archived or deleted after human confirmation.
- `welcome-to-docker/` is an unrelated Docker tutorial/sample app with a nested `.git/`, package files, public assets, and React source; it should be archived outside the repo or deleted after human confirmation.
- `Support Queries.txt` contains operational SQL plus specific-looking referral track IDs, a referrer UCN, and a gaming handle; archive outside the repo unless it is intentionally redacted and converted into safe support documentation.
- `Core Domain Features.txt`, `Front-end Blueprint.txt`, and `folder strucuture.txt` are stale legacy notes with encoding artifacts and assumptions that conflict with or duplicate the DLaaS target-state, SA, and roadmap docs; archive outside the repo unless useful portions are deliberately migrated into the appropriate docs.

Final legacy/untracked policy:

| Path | Classification | Migration target if retained |
|---|---|---|
| `Core Domain Features.txt` | archive outside repo | Extract only still-accurate platform notes into `docs/product/` or `docs/sa/` after review. |
| `Front-end Blueprint.txt` | archive outside repo | Extract only DLaaS-aligned UX ideas into `docs/sa/CONTROL_PLANE_UX_BLUEPRINT.md` after backend truth review. |
| `Support Queries.txt` | archive outside repo | Redact and convert into a safe support runbook under `docs/` only if still needed. |
| `folder strucuture.txt` | archive outside repo | Extract only useful architecture notes into `docs/sa/` after review. |
| `github/` | archive/delete after human confirmation | Already migrated to `.github/workflows/` and `docs/CI_CD.md`. |
| `welcome-to-docker/` | archive/delete after human confirmation | No migration target; unrelated sample app. |

These remaining legacy items block broad autonomous execution while they remain untracked in the workspace. They do not block narrow backend/docs work if left untouched, but the preferred next cleanup is to archive them outside the repo or delete them after human confirmation.

## Readiness Requirements

A task is ready only when:

- It has a `TASK-XXX` ID.
- It links to an enhancement in `docs/roadmap/ENHANCEMENT_BACKLOG.md`.
- The enhancement links to a capability in `docs/sa/CAPABILITY_GAP_MATRIX.md`.
- Dependencies are satisfied.
- Backend source of truth is known.
- Schema, states, APIs, auth, permissions, tests, risks, and DB/state validation needs are known or explicitly not relevant.

## Implementation Boundaries

- Do not invent backend fields, statuses, schemas, APIs, routes, or response bodies.
- Treat database schema and service-layer code as current source of truth.
- Do not start frontend/control-plane work unless backend truth is known.
- Do not change reward, funding, fulfilment, settlement, audit, auth, security, or production-data behavior without tests and required approval.
- Do not assume live DB state without validation.

## Completion Report

Every runner cycle should end with:

- Selected task ID and title.
- Readiness result.
- Files changed.
- Tests or validation performed.
- Definition of Done result.
- Task status update.
- Follow-up tasks.
- Remaining gaps.
- Recommended next action.
