# infra/

Infrastructure assets for local dev, Kubernetes deployment, and IaC.

## Layout
```
infra/
├─ docker/
│  ├─ Dockerfile.api
│  ├─ Dockerfile.worker
│  └─ docker-compose.yaml
├─ k8s/
│  ├─ api-deployment.yaml         # API Deployment + Service (+ probes)
│  ├─ api-deployment.cm.yaml      # Same as above, but mounts ConfigMap at /app/config
│  ├─ worker-deployment.yaml
│  ├─ secrets.yaml                # DSN & crypto secrets (example)
│  ├─ configmaps.yaml             # App config YAMLs (logging, kafka, db, settings.prod)
│  ├─ ingress.yaml                # Public entrypoint to the API Service
│  └─ servicemonitor.yaml         # (Optional) Prometheus Operator scraping
└─ terraform/
   ├─ README.md
   └─ main.tf
```

## How this links to the broader application

- **apps/api/main.py** exposes `/healthz`, `/readyz`, and `/metrics`.
  - K8s probes use those endpoints for safer rollouts and autorestarts.
  - `servicemonitor.yaml` scrapes `/metrics` if Prometheus Operator is installed. Grafana dashboard is under `monitoring/`.

- **config/** (YAML + Pydantic) can be mounted into the container at **`/app/config`** via `api-deployment.cm.yaml`.
  - The app reads `APP_ENV=prod` and overlays `config/settings.prod.yaml` (from the mounted ConfigMap).
  - Update `configmaps.yaml` to change topics/logging/pools **without rebuilding images**.

- **secrets.yaml** injects sensitive values via `secretKeyRef`. Replace with your real secret system if needed.

- **docker-compose.yaml** provides a **dev stack** (API + Postgres + Kafka/ZK). API on `localhost:8000`.

- **terraform/** is a skeleton to create a namespace and wire providers. Extend for managed DB, Kafka, and full cluster infra.

## Deploy (Kubernetes)
```bash
kubectl apply -f infra/k8s/secrets.yaml
kubectl apply -f infra/k8s/configmaps.yaml
kubectl apply -f infra/k8s/api-deployment.cm.yaml
kubectl apply -f infra/k8s/worker-deployment.yaml
kubectl apply -f infra/k8s/ingress.yaml
# Optional metrics scraping:
kubectl apply -f infra/k8s/servicemonitor.yaml
```

## Local dev
```bash
cd infra/docker
docker compose up --build
# API: http://localhost:8000/healthz | /readyz | /metrics
```
