# Security And Authentication

This application uses backend-confirmed session identity, local API keys, JWT
bearer tokens, and worker secrets to separate public, partner, admin, and
worker traffic. Local API keys remain the development fallback; JWT bearer
tokens are the target path for user-facing Producer - Supply, Distributor -
Demand, Consumer, Partner, and Amplifi Admin sessions.

## Auth Surfaces

| Surface | Examples | Auth mechanism |
| --- | --- | --- |
| Public referral validation | `POST /public/referrals/validate` | Request validation rules; no partner/admin API key. |
| Partner APIs | `/referrals/*`, `/v1/progress`, `/enterprise/events` | `Authorization: Bearer ...` with partner/admin JWT, partner OAuth bearer token where supported, or `x-api-key` with tenant-bound partner key. |
| Platform admin APIs | General `/admin/*` operations | `Authorization: Bearer ...` with admin JWT or `x-api-key` with platform admin key. |
| Finance admin APIs | Funding, sponsor billing, settlement, FX, wallets | `Authorization: Bearer ...` with admin/finance-admin JWT or `x-api-key` with platform admin or finance admin key. |
| Distribution admin APIs | Distributors, opportunities, routing, commissions, reporting, governance | `Authorization: Bearer ...` with admin/distribution-admin JWT or `x-api-key` with platform admin or distribution admin key. |
| System admin APIs | Enterprise event admin, DLQ replay, internal replay | `Authorization: Bearer ...` with admin/system-admin JWT or `x-api-key` with platform admin or system admin key. |
| Admin audit APIs | `/admin/audit` | `Authorization: Bearer ...` with admin/system-admin JWT or `x-api-key` with platform admin or system admin key. |
| Worker endpoint | `POST /worker/referral-events` | `x-worker-secret` or event body `secret`. |
| Health/metrics | `/healthz`, `/readyz`, `/health`, `/metrics` | Usually protected by network/runtime controls. |

## Key Resolution

The auth logic lives in `utils/security.py`.

Main dependency helpers:

- `require_admin_key`
- `require_finance_admin_key`
- `require_distribution_admin_key`
- `require_system_admin_key`
- `require_partner_key`
- `require_admin_or_partner_key`
- `require_any_key`
- `require_session_key`
- `require_admin_partner_or_producer_key`
- `require_admin_partner_or_distributor_key`
- `require_admin_partner_or_consumer_key`

The release sign-off view of route families, allowed roles, tenant rules, and
required regression evidence is maintained in
`docs/API_PERMISSION_MATRIX.md`.

Session introspection lives at:

```text
GET /auth/session
```

That route returns the confirmed role, tenant, optional producer/distributor
claims, workspace access, and recommended starting workspace. The frontend uses
this response for the sidebar, workspace banner, and role-scoped pages so UX
guidance comes from the same permission contract as the API.

JWT bearer tokens are accepted when `AUTH_JWT_SECRET` is configured. The token
must be signed with HS256 and can optionally be constrained with:

- `AUTH_JWT_ISSUER`
- `AUTH_JWT_AUDIENCE`

Recognised JWT claims:

- role: `role` or `amplifi_role`
- tenant: `tenant_code` or `tenant`
- subject: `sub`
- producer: `producer_code`
- distributor: `distributor_code`
- client: `client_id`
- scopes: `scopes` or `scope`

Those claim names are configurable for production IdPs:

- `AUTH_JWT_ROLE_CLAIMS`
- `AUTH_JWT_TENANT_CLAIMS`
- `AUTH_JWT_SUBJECT_CLAIMS`
- `AUTH_JWT_PRODUCER_CLAIMS`
- `AUTH_JWT_DISTRIBUTOR_CLAIMS`
- `AUTH_JWT_CLIENT_CLAIMS`
- `AUTH_JWT_SCOPE_CLAIMS`

The same central permission helpers validate local keys and JWT identities, so
Producer, Distributor, Consumer, Partner, and scoped Admin access behaves the
same regardless of whether the session came from a local key or bearer token.
Production IdP/OAuth binding still needs the selected issuer, token lifecycle,
and role/tenant claim policy to be finalised.

Partner keys map to tenant identity:

- FNB keys return tenant `FNB`.
- PNP keys return tenant `PNP`.
- Platform admin keys return role `ADMIN` and tenant `INTERNAL`.
- Scoped admin keys return `FINANCE_ADMIN`, `DISTRIBUTION_ADMIN`, or
  `SYSTEM_ADMIN` and tenant `INTERNAL`.

The platform admin key is intentionally allowed through all scoped admin
dependencies. Scoped admin keys are narrower: a distribution admin key cannot
perform finance actions, and a finance admin key cannot perform distribution
actions.

Tenant identity is used by routers so callers do not need to send or spoof the
tenant manually. For example, `POST /enterprise/events` derives `tenantCode`
from the partner key.

## Local Test Keys

Local/dev/test environments allow built-in test keys:

- `test-admin-key`
- `test-finance-admin-key`
- `test-distribution-admin-key`
- `test-system-admin-key`
- `test-partner-key`
- `test-fnb-key`
- `test-pnp-key`
- `test-fnb-producer-insureco-key`
- `test-fnb-distributor-insurance-advocate-key`
- `test-fnb-consumer-key`

These are enabled only when `APP_ENV` is one of:

- `local`
- `dev`
- `test`

Production must set `APP_ENV=production` or another non-test value so built-in
test keys are not accepted.

## Required Production Secrets

Core:

- `ADMIN_API_KEY`
- `FINANCE_ADMIN_API_KEY`
- `DISTRIBUTION_ADMIN_API_KEY`
- `SYSTEM_ADMIN_API_KEY`
- `WORKER_SECRET`
- `REFERRAL_CODE_SECRET`
- `APP_DB_DSN`

Tenant keys:

- `FNB_PARTNER_API_KEY`
- `FNB_TENANT_USER_API_KEY`
- `FNB_TENANT_ADMIN_API_KEY`
- `PNP_PARTNER_API_KEY`
- `PNP_TENANT_USER_API_KEY`
- `PNP_TENANT_ADMIN_API_KEY`

Queue/cloud:

- `APP_SQS_QUEUE_URL`
- `APP_SQS_DLQ_URL`
- `AWS_REGION`

Optional:

- `REDIS_URL`
- `APP_CORS_ALLOW_ORIGINS`
- `AUTH_JWT_SECRET`
- `AUTH_JWT_ISSUER`
- `AUTH_JWT_AUDIENCE`
- `AUTH_JWT_ROLE_CLAIMS`
- `AUTH_JWT_TENANT_CLAIMS`
- `AUTH_JWT_SUBJECT_CLAIMS`
- `AUTH_JWT_PRODUCER_CLAIMS`
- `AUTH_JWT_DISTRIBUTOR_CLAIMS`
- `AUTH_JWT_CLIENT_CLAIMS`
- `AUTH_JWT_SCOPE_CLAIMS`

## Worker Secret

The worker route validates:

- `x-worker-secret` header, or
- event body field `secret`

The value must match `WORKER_SECRET`.

This protects `/worker/referral-events`, which can advance referral journeys,
trigger leaderboard rebuilds, and process reward fulfilment events.

## Admin Audit Trail

Sensitive admin actions are written to `admin_audit_log` when migration
`071_admin_audit_log.sql` has been applied.

The first audited actions are:

- FX rate creation/update.
- Cross-border settlement instruction creation.
- Sponsor invoice creation, generation, issue, payment recording, receipt
  allocation, payment reversal, and payment allocation reversal.
- Settlement approval requests, approvals, and rejections.
- Settlement reversal creation, approval, and execution.
- Distributor creation, activation, suspension, and termination.
- Commission rule creation and commission calculation.
- Distributor wallet creation, credits, holds, hold releases, payouts, and
  reversals.
- Opportunity creation, publishing, closing, and reopening.
- Opportunity routing and route accept/decline decisions.
- Enterprise event replay attempts.

The audit log can be queried through:

```text
GET /admin/audit
GET /admin/audit/summary
```

Supported filters include `action_domain`, `action_type`, `tenant_code`,
`target_type`, `target_id`, and `limit`.

The summary endpoint supports `action_domain`, `tenant_code`, and `hours`.

Local/dev smoke test:

```text
.\.venv_codex\Scripts\python.exe scripts\admin_audit_smoke.py
```

## IDS/Hogan Event Auth

`POST /enterprise/events` requires admin or partner authentication.

Recommended production usage:

- Hogan/IDS integration should use a tenant-bound partner key or a dedicated
  integration key configured as a partner key.
- Admin keys should be reserved for operational/admin tooling.
- Do not expose worker secrets to Hogan/IDS clients.

## Operational Checks

Before production:

- Set `APP_ENV` to a non-test value.
- Confirm no local test key is accepted.
- Confirm JWT session introspection returns the expected role, tenant, and
  workspace access for each deployed role.
- Confirm invalid issuer, audience, expiry, and role claims are rejected.
- Confirm partner key can access partner endpoints.
- Confirm partner key cannot access admin endpoints.
- Confirm admin key can access admin endpoints.
- Confirm finance admin key can access funding/billing/settlement/FX endpoints
  but not distribution endpoints.
- Confirm distribution admin key can access distribution endpoints but not
  finance endpoints.
- Confirm system admin key can access replay/event admin endpoints but not
  finance or distribution endpoints.
- Confirm worker endpoint rejects missing or wrong `x-worker-secret`.
- Confirm secrets are injected by runtime secret management, not baked into the
  image.

Release sign-off evidence is tracked in
`docs/RELEASE_SECURITY_CHECKLIST.md`.
