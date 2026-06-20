# API Permission Matrix

This matrix is the release-control view of API access. It maps each surface to
the backend permission helper, accepted role family, tenant boundary, and the
regression evidence expected before production promotion.

## Role Families

| Role family | Typical actor | Tenant scope | Primary credential |
| --- | --- | --- | --- |
| Public | Anonymous visitor or pre-auth referral validation | None; validation-only | No credential, request validation only |
| Consumer | Consumer workspace user | Own tenant and consumer claim | JWT or tenant consumer key |
| Producer | Sponsor or producer workspace user | Own tenant and producer claim | JWT or tenant producer key |
| Distributor | Distributor workspace user | Own tenant and distributor claim | JWT or tenant distributor key |
| Partner | Tenant-bound integration client | Tenant derived from partner credential | JWT, partner OAuth token, or tenant partner API key |
| Finance Admin | Funding, billing, settlement, FX operator | Cross-tenant operational scope | Finance admin JWT or API key |
| Distribution Admin | Channel, distributor, route, opportunity operator | Cross-tenant operational scope | Distribution admin JWT or API key |
| System Admin | Audit, replay, enterprise event, and platform operations | Cross-tenant operational scope | System admin JWT or API key |
| Platform Admin | Break-glass/full platform operator | Cross-tenant operational scope | Platform admin JWT or API key |
| Worker | Internal async processor | Event payload scope | Worker secret |

## Endpoint Matrix

| Surface | Route examples | Required helper or control | Allowed roles | Tenant rule | Required regression evidence |
| --- | --- | --- | --- | --- | --- |
| Public referral validation | `POST /public/referrals/validate` | Request validation | Public | Does not trust caller-supplied tenant for privileged action | Public validation smoke |
| Auth/session introspection | `GET /auth/session` | `require_session_key` | Platform Admin, scoped admins, Partner, Producer, Distributor, Consumer | Identity response must reflect resolved tenant and role claims | Session role tests and workspace smoke |
| Consumer BFF | `/v1/experience/consumer` | `require_admin_partner_or_consumer_key` | Platform Admin, Partner, Consumer | Consumer identity is tenant-scoped; partner/admin may operate for configured tenant | Consumer experience API tests |
| Distributor BFF | `/v1/experience/distributor` | `require_admin_partner_or_distributor_key` | Platform Admin, Partner, Distributor | Distributor claim limits distributor workspace access | Distributor experience API tests |
| Sponsor BFF | `/v1/experience/sponsor` | `require_admin_partner_or_producer_key` | Platform Admin, Partner, Producer | Producer claim limits sponsor workspace access | Sponsor experience API tests |
| Admin command-centre BFF | `/v1/experience/admin-command-centre` | `require_system_admin_key` | Platform Admin, System Admin | Cross-tenant read model; tenant must be explicit and audited where applicable | Admin experience API tests |
| Partner referral/progress APIs | `/referrals/*`, `/v1/progress`, `/rewards/*` | `require_partner_key`, `require_admin_or_partner_key`, or role-scoped helper | Platform Admin, Partner, selected role owner | Partner tenant is derived from credential; do not accept spoofed tenant ownership | Partner and tenant isolation tests |
| Enterprise event ingress | `POST /enterprise/events` | `require_admin_or_partner_key` | Platform Admin, Partner | Partner credential determines tenant; admin tools may set explicit tenant | Enterprise event auth tests |
| Partner seam OAuth and webhooks | `/partner-seam/*` | Partner OAuth/token controls plus partner identity checks | Partner, Platform Admin where operational | Client identity must bind to tenant and token lifecycle | Partner seam tests and webhook replay tests |
| Finance operations | `/admin/finance`, `/admin/funding/*`, `/admin/sponsor-billing/*`, `/admin/settlement/*`, FX and wallet finance routes | `require_finance_admin_key` | Platform Admin, Finance Admin | Cross-tenant finance operations; tenant filters must be explicit | Permission tests for finance-vs-distribution separation |
| Distribution operations | `/admin/channels`, distributor, opportunity, route, commission, governance, reporting routes | `require_distribution_admin_key` | Platform Admin, Distribution Admin | Cross-tenant distribution operations; tenant filters must be explicit | Permission tests for distribution-vs-finance separation |
| System operations | `/admin/enterprise-events`, `/admin/dlq`, `/internal/replay`, `/admin/audit` | `require_system_admin_key` | Platform Admin, System Admin | Cross-tenant system operations; replay and audit actions must be recorded | System admin permission and audit tests |
| General admin operations | Remaining `/admin/*` routes not scoped to finance/distribution/system | `require_admin_key` | Platform Admin | Cross-tenant by design; prefer narrower helper for new route families | Router auth consistency audit |
| Worker event processing | `POST /worker/referral-events` | Worker secret check | Worker | Payload must include trusted internal secret; not a user or partner API | Worker secret smoke |
| Health and readiness | `/healthz`, `/readyz`, `/health`, `/metrics` | Runtime/network controls | Operations platform | No tenant data in response | Deployment smoke and monitoring checks |

## New Route Gate

Before adding or promoting an API route, the owner must confirm:

| Gate | Standard |
| --- | --- |
| Smallest role | Use the narrowest helper that matches the business action. |
| Tenant source | Tenant must come from resolved identity unless the route is an admin operation. |
| Claim binding | Producer, distributor, and consumer routes must respect their role-specific claim. |
| Audit | Mutating finance, distribution, system, replay, and settlement operations require audit evidence where supported. |
| Test | Add or update a regression test for allowed role, rejected adjacent role, and tenant isolation. |
| Documentation | Update this matrix when a new route family or permission helper is introduced. |

## Release Sign-Off

The production release reviewer should sign off the matrix by checking:

- Platform admin can reach admin-only surfaces.
- Finance admin is blocked from distribution-only surfaces.
- Distribution admin is blocked from finance-only surfaces.
- System admin is blocked from finance/distribution business operations.
- Partner credentials cannot reach admin surfaces.
- Tenant-bound partner, producer, distributor, and consumer credentials cannot read another tenant's sensitive data.
- Worker secret is required for worker routes.
- Local test keys are rejected when `APP_ENV` is not `local`, `dev`, or `test`.
