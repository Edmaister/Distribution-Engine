# Helm Chart - referrals

## Install

```bash
helm upgrade --install referrals ./helm/referrals \
  --namespace referrals --create-namespace \
  --set image.registry=ghcr.io \
  --set image.repository=ORG/referrals-api \
  --set image.tag=latest \
  --set-string secrets.APP_DB_DSN="<set-from-secret-manager-or-ci>"
```

All `secrets.*` values are placeholders. Do not commit real DSNs, API keys, worker secrets, tenant keys, queue URLs, Redis URLs, or provider credentials.

## Values to customize

- `image.registry`, `image.repository`, `image.tag`
- `worker.enabled`, `worker.replicaCount`
- `secrets.APP_DB_DSN`
- `secrets.ADMIN_API_KEY`, `secrets.WORKER_SECRET`, `secrets.REFERRAL_CODE_SECRET`
- tenant keys such as `secrets.FNB_PARTNER_API_KEY` and `secrets.PNP_PARTNER_API_KEY`
- queue settings such as `secrets.APP_SQS_QUEUE_URL`, `secrets.APP_SQS_DLQ_URL`, `secrets.AWS_REGION`
- `env.APP_ENV`, `env.APP_KAFKA_CLIENT`, `env.APP_KAFKA_BROKER`
- `ingress.*`

## Health endpoints

- API probes use `/health`.

## Worker

- The chart can deploy a worker workload with `worker.enabled=true`.
- The worker uses the same image and starts `python -m apps.Workers.sqs_referral_worker`.
- The API Service selects only API pods, not worker pods.

## Migrations

- Use `values-migrations.yaml` to run `python scripts/init_db.py` as a Helm hook.
- Seeds are disabled by default in that overlay. Enable `migrations.applySeeds=true` only after reviewing seed data for the target environment.
