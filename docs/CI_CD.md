# CI/CD Guide

GitHub Actions workflows live in `.github/workflows/`.

## Current Workflows

- `ci.yml`: CI on push/PR. Runs backend checks, clean database readiness, security regression checks, and frontend checks.
- `deploy_compose.yml`: Manual remote Docker Compose deploy.
- `deploy_helm.yml`: Manual Helm deploy.

## Required Repository Secrets

- `APP_DB_DSN`: Database DSN supplied from the repository or environment secret store.
- `REMOTE_HOST`, `REMOTE_USER`, `REMOTE_SSH_KEY`: Required by `deploy_compose.yml`.
- `KUBE_CONFIG`: Required by `deploy_helm.yml`.

## Optional Repository Variables

- `REGISTRY`: Defaults to `ghcr.io` when omitted.
- `IMAGE_NAME`: Defaults from the repository owner and `referrals-api` when omitted.
- `CODECOV_TOKEN`: Optional. Used by CI coverage upload when configured.

## Safety Rules

- Do not commit real DSNs, API keys, SSH keys, kubeconfigs, provider credentials, or tenant secrets.
- Deployment workflows must consume sensitive values from GitHub Secrets or an approved secret manager.
- Local example values must be obvious placeholders.
- Production deployment changes require human review.
