# Deployment Options

Two ready-to-use paths:

## 1) Kubernetes (Helm)
- Files:
  - `.github/workflows/deploy_helm.yml`
  - `helm/referrals/*`
- Secrets:
  - `KUBE_CONFIG` — kubeconfig content
  - `APP_DB_DSN` — database DSN used by the API
- Vars:
  - `REGISTRY` (default `ghcr.io`)
  - `IMAGE_NAME` (default `ORG/referrals-api`)
- Run:
  - Actions → Deploy (Helm) → choose image tag + namespace.

## 2) Remote Docker Compose (SSH)
- Files:
  - `.github/workflows/deploy_compose.yml`
- Secrets:
  - `REMOTE_HOST`, `REMOTE_USER`, `REMOTE_SSH_KEY`
- Requires:
  - Remote host with Docker, a working `docker-compose.yml` in `/opt/referrals`.
- Run:
  - Actions → Deploy (Remote Docker Compose) → choose image tag.

Both consume the image produced by CI and pushed to your registry.
