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
