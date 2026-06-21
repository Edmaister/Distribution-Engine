# Terraform (placeholder)

Suggested layout:
infra/terraform/
├─ envs/
│  ├─ dev/
│  └─ prod/
└─ modules/

Start by defining providers, backend (state), and a minimal Postgres + Kubernetes namespace.
