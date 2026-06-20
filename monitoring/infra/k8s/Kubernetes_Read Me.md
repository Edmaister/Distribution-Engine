# Kustomize layouts

## Structure
```
infra/k8s/
├─ base/
│  ├─ api-deployment.yaml
│  ├─ worker-deployment.yaml
│  └─ kustomization.yaml
└─ overlays/
   ├─ dev/
   │  ├─ kustomization.yaml
   │  ├─ patch-api-env.yaml
   │  ├─ patch-api-replicas.yaml
   │  └─ ingress.yaml
   ├─ stage/
   │  ├─ kustomization.yaml
   │  ├─ patch-api-env.yaml
   │  ├─ patch-api-replicas.yaml
   │  └─ ingress.yaml
   ├─ prod/
   │  ├─ kustomization.yaml
   │  ├─ patch-api-env.yaml
   │  ├─ patch-api-replicas.yaml
   │  ├─ patch-api-configmap.yaml
   │  └─ ingress.yaml
   └─ test/
      ├─ kustomization.yaml
      ├─ patch-api-env.yaml
      └─ patch-api-replicas.yaml
```

## Usage
Apply dev:
```bash
kubectl apply -k infra/k8s/overlays/dev
```
Apply stage:
```bash
kubectl apply -k infra/k8s/overlays/stage
```
Apply prod (mounts ConfigMap at /app/config and scrapes /metrics):
```bash
kubectl apply -k infra/k8s/overlays/prod
```
Apply test:
```bash
kubectl apply -k infra/k8s/overlays/test
```
