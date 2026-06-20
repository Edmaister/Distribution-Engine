# Deployment Sanity Check

Last local check: 2026-06-10

## Completed Checks

Python import/startup checks passed for:

- `apps.api.main`
- `apps.Workers.sqs_referral_worker`
- `apps.Workers.ids_consumer`
- `scripts.init_db`
- `scripts.seed_db`

Dependency file check:

- `requirements.txt` was converted to UTF-8 for Linux/Docker compatibility.
- `pip install -r requirements.txt --dry-run` parsed successfully.

Helm values check:

- `helm/referrals/values.yaml` parses as YAML.
- `helm/referrals/values-migrations.yaml` parses as YAML.
- `helm/referrals/values-monitoring.yaml` parses as YAML.
- `helm/referrals/Chart.yaml` parses as YAML.

Chart readiness updates:

- API and worker are modeled as separate deployments.
- API service selects API pods only.
- Worker uses the same image with command `python -m apps.Workers.sqs_referral_worker`.
- Required production auth, worker, SQS, AWS, and Redis settings are exposed as chart secrets.
- Migration overlay no longer applies seeds by default.
- Runtime readiness now checks required schema groups for foundation, funding,
  distribution, and multi-currency. Check `/readyz` after migrations.

Container hygiene:

- `.dockerignore` excludes virtual environments, local secrets, test caches,
  coverage files, local event queues, and generated office artifacts.

## Not Completed Locally

Docker image build could not be completed in this Windows session because the
current user/session cannot access the Docker engine pipe:

```text
permission denied while trying to connect to the docker API at npipe:////./pipe/docker_engine
```

Helm template/lint could not be completed because `helm` is not installed in
this local environment.

## Commands To Run In A Docker/Helm Enabled Environment

API image:

```bash
docker build -f Dockerfile -t referral-engine-api:smoke .
```

Worker image, if building a separate worker image:

```bash
docker build -f Dockerfile.worker -t referral-engine-worker:smoke .
```

Helm lint:

```bash
helm lint helm/referrals
```

Helm render:

```bash
helm template referrals helm/referrals \
  --set-string secrets.APP_DB_DSN="postgresql://user:pass@db:5432/referrals" \
  --set-string secrets.ADMIN_API_KEY="dummy-admin" \
  --set-string secrets.WORKER_SECRET="dummy-worker" \
  --set-string secrets.REFERRAL_CODE_SECRET="dummy-referral"
```

Migration hook render:

```bash
helm template referrals helm/referrals -f helm/referrals/values-migrations.yaml
```

Monitoring overlay render:

```bash
helm template referrals helm/referrals -f helm/referrals/values-monitoring.yaml
```
