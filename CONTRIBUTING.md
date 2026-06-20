# Contributing to Referrals Platform

Thanks for wanting to contribute! This guide explains how we work, how to set up your environment, and what we expect from changes.

## Table of contents
- [Scope](#scope)
- [Architecture quick-tour](#architecture-quick-tour)
- [Getting started](#getting-started)
- [Local development](#local-development)
- [Code style & quality](#code-style--quality)
- [Testing](#testing)
- [Branching & pull requests](#branching--pull-requests)
- [Commit messages](#commit-messages)
- [Documentation](#documentation)
- [Security](#security)
- [Release & versioning](#release--versioning)

---

## Scope
This repository contains:
- **apps/**: FastAPI apps (API, admin, worker)
- **services/**: domain logic (reward_service, policy_service, etc.)
- **config/**: Pydantic settings & YAML overlays
- **db/**: migrations and seeds
- **scripts/**: ops/maintenance scripts
- **infra/**: Docker, Kubernetes (kustomize), Terraform
- **tests/**: unit & integration tests
- **utils/**: shared libraries (db, kafka, logging, metrics)

## Architecture quick-tour
- The API exposes health endpoints (`/healthz`, `/readyz`) and `/metrics` for Prometheus.
- Rewards are **idempotent** and emit Kafka `reward.applied` events.
- Policies/cooldowns are driven by config with DB/campaign overrides.
- K8s manifests use **kustomize** overlays (`dev`, `stage`, `prod`, `test`).

See **README.md** and **docs/** for deeper dives.

## Getting started
1. **Clone & install deps**
   ```bash
   git clone <repo-url>
   cd referrals-platform
   pip install -r requirements.txt
   ```
2. **Environment**
   ```bash
   cp .env.example .env
   # Edit DSN, Kafka broker, etc.
   ```
3. **Optional (Docker dev stack)**
   ```bash
   cd infra/docker
   docker compose up --build
   ```

## Local development
- Run API:
  ```bash
  uvicorn apps.api.main:app --reload --port 8000
  ```
- Helpful Make targets (if present):
  ```bash
  make db-init
  make db-seed
  make refresh-mv
  make health
  ```

## Code style & quality
- **Formatting:** `black` (configured in `pyproject.toml`).
- **Linting:** `ruff` (errors + imports), run locally:
  ```bash
  ruff check . && black --check .
  ```
- **Type hints:** encouraged in all new/changed code.
- **Logging:** use `utils.logging.get_logger` and **structured** log messages.

## Testing
- **Unit tests:** `tests/unit/`
- **Integration tests:** `tests/integration/`
- **Pytest defaults:** see `pytest.ini`
- Run everything:
  ```bash
  pytest
  ```
- Coverage (terminal report by default):
  ```bash
  pytest --cov=services --cov=apps --cov-report=term-missing
  ```

## Branching & pull requests
- Create a **feature branch** from `main`:
  ```bash
  git checkout -b feat/short-description
  ```
- Open a PR when ready. PR template (if available) should include:
  - **Summary** of the change
  - **Motivation/Context**
  - **Testing** performed (screenshots, logs if relevant)
  - **Docs** updates (if needed)
  - **Risk/rollback** plan

### PR checklist
- [ ] Code formatted with **black** and linted with **ruff**
- [ ] Unit/integration tests added or updated
- [ ] All tests pass (`pytest`)
- [ ] No breaking API changes (or documented in README/CHANGELOG)
- [ ] Env/infra changes documented (if any)

## Commit messages
Use clear, imperative subject lines:
```
feat(policy): add campaign-level overrides for warn_threshold
fix(rewards): ensure idempotent insert returns existing row
chore(ci): run tests with coverage and upload report
docs(readme): add quickstart instructions
```
- Prefix: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `build`, `ci`
- Keep body focused on **what** and **why** (not just how).

## Documentation
- High-level docs in **README.md**, deeper guides in **docs/**.
- If you change behavior, update relevant docs (or include a snippet in your PR).

## Security
- **Do not** commit secrets. Use `.env` locally and K8s `secrets.yaml` (or your secret manager) in deployment.
- Report security issues privately to the maintainers (do not open a public issue with sensitive details).

## Release & versioning
- CI builds Docker images using the commit SHA; latest tags for prod.
- Consider semantic versioning for published packages/images if applicable.

Thanks again for helping make this platform better! 🙌
