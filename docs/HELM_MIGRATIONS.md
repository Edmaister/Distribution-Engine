# Helm Hook — DB Migrations Job

This chart includes an **optional Kubernetes Job** that runs **database migrations** (and optionally seeds) on each **helm install/upgrade**.

## Enable
Use the provided overlay values file:
```bash
helm upgrade --install referrals ./helm/referrals   --namespace referrals --create-namespace   -f helm/referrals/values-migrations.yaml   --set image.registry=${REGISTRY:-ghcr.io}   --set image.repository=${IMAGE_NAME:-ORG/referrals-api}   --set image.tag=${TAG:-latest}   --set-string secrets.APP_DB_DSN="$APP_DB_DSN"
```

## What it does
- Creates a **Job** named `{{ release }}-referrals-migrations-<timestamp>`
- Annotated with Helm hooks:
  - `pre-install, pre-upgrade` — runs before the Deployment is applied
  - `hook-delete-policy: before-hook-creation,hook-succeeded` — keeps the history clean
- Runs inside the same container image as the API:
  - `python scripts/init_db.py`
  - If `migrations.applySeeds=true`, also runs `python scripts/seed_db.py`

## Values
```yaml
migrations:
  enabled: true        # turn on the Job hook
  applySeeds: true     # also seed after migrating
  backoffLimit: 1      # Job retry attempts
```

## Notes
- Ensure `secrets.APP_DB_DSN` is set (via values or external secrets).
- If you prefer **out-of-band migrations**, leave `migrations.enabled=false` and run the scripts via CI/CD instead.
