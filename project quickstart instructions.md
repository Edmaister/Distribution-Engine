# Referrals Platform

End-to-end platform for referral-based customer acquisition and campaign attribution.

## Features
- **Refer-a-friend with gamification** (badges, missions, leaderboards)
- **Campaign code attribution** (unique QR/ref codes, campaign rewards)
- **Reward service** with idempotent application, Kafka event publishing, and Prometheus metrics
- **Cooldown + policy service** for quality gating
- **Config-driven** (`config/` overlays YAMLs + env vars)
- **Monitoring** with `/metrics` (Prometheus), dashboards under `monitoring/`
- **Infrastructure** in `infra/` (Docker, K8s, Terraform)
- **Tests** split into `unit/` and `integration/` with `pytest`

## Folder structure
```
referrals-platform/
├─ apps/              # FastAPI apps (api, admin, worker)
├─ config/            # Settings, cooldowns, YAML configs
├─ db/                # Migrations + seeds
├─ docs/              # Project docs (incl. TESTING.md)
├─ infra/             # Docker, k8s, terraform, overlays
├─ monitoring/        # Grafana dashboards, Prometheus rules
├─ scripts/           # Admin/DB scripts (init, seeds, health, etc.)
├─ services/          # reward_service, policy_service, etc.
├─ tests/             # Unit + integration tests
├─ utils/             # Shared libs (db, kafka, logging, metrics)
│
├─ .env.example       # ✅ sample env vars
├─ pyproject.toml     # ✅ black/ruff/pytest config
├─ requirements.txt   # ✅ deps if not using poetry
└─ README.md          # ✅ this file
```

## Quickstart

### 1. Clone & install deps
```bash
git clone https://github.com/ORG/referrals-platform.git
cd referrals-platform
pip install -r requirements.txt
```

### 2. Set env vars
```bash
cp .env.example .env
# Edit DB_DSN, Kafka broker, etc.
```

### 3. Run API locally
```bash
uvicorn apps.api.main:app --reload --port 8000
```

### 4. Dev stack (Docker Compose)
```bash
cd infra/docker
docker compose up --build
```

### 5. Tests
```bash
pytest
```

## CI/CD
- GitHub Actions workflow under `.github/workflows/ci.yml`
- Runs pytest + coverage, builds/pushes Docker images
- Optional Codecov integration

## Infra
- K8s manifests under `infra/k8s`
- Overlays for `dev`, `stage`, `prod`, `test`
- ConfigMaps mount app configs, secrets injected separately
- Terraform skeleton in `infra/terraform`

---

Built with ❤️ for scalable, gamified referrals and campaign attribution.

License

This project is licensed under a proprietary license.
© 2025 Edwin Tait. All rights reserved.

The Referrals Platform may not be used, copied, modified, distributed, or sublicensed without prior written permission from the copyright holder.
For licensing inquiries, please contact Edwin Tait.
