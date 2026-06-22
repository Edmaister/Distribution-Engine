# API Permission Matrix

This matrix is the release-control view of API access. It maps each surface to
the backend permission helper, accepted role family, tenant boundary, and the
regression evidence expected before production promotion.

TASK-008 defines the participant taxonomy and maps these role families to current source tables, claims, and scope helpers in `docs/sa/PARTICIPANT_TAXONOMY_PERMISSION_MAP.md`.

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

TASK-005 defines the future account, tenant lifecycle, membership, seat, and external-reference model in `docs/sa/TENANT_ACCOUNT_LIFECYCLE_MEMBERSHIP_MODEL.md`. Until that model is implemented, this matrix remains the current permission contract. New account or membership routes must update this matrix with the resolved membership check, tenant-source rule, and regression evidence.

## DLaaS API Family Guardrails

TASK-019 defines these target guardrails before new DLaaS endpoint implementation. They do not add routes by themselves. Current route examples remain current-state facts; future public/internal endpoints must cite the relevant family before implementation.

Standard tenant rule: public and partner APIs should derive tenant scope from the authenticated credential, external tenant reference mapping, or role-specific external reference. Internal services and admin/operator APIs may continue using resolved `tenant_code` for partitioning, audit, funding, fulfilment, settlement, and reporting.

Standard safe error shape: new versioned DLaaS APIs should return a stable error envelope with a machine-readable `code`, safe `message`, `correlation_id` where available, and bounded validation `details` when useful. Do not include secrets, raw provider payloads, raw settlement internals, or private identifiers in client-facing errors.

| API family | Surface boundary | Auth and actor contract | Tenant and participant scope | Idempotency and validation | Event/audit expectation | Safe exposure rule |
| --- | --- | --- | --- | --- | --- | --- |
| Campaigns | Internal/admin first; future public management API only through a stable versioned contract. | Platform Admin or Distribution Admin for operator changes; future tenant admin or integration credential for tenant-owned changes. | Tenant must be resolved from identity or external tenant reference mapping; campaign ownership must be checked before reads or writes. | Mutating create/update/lifecycle operations require request validation and idempotency keys where duplicate commands could change state. | Mutations require audit evidence where supported; webhook event names wait for TASK-020. | Do not expose internal readiness blockers externally unless mapped to safe blocker categories. |
| Participants | Internal/admin and role-scoped partner/distributor/producer/consumer surfaces. | Use the narrowest existing helper or future membership permission; role-specific credentials must bind to participant claims. | Participant role and tenant scope must both match; external references such as `producer_ref`, `partner_ref`, `distributor_ref`, and `organisation_ref` map to internal records. | Mutating onboarding/status/governance actions require validation, audit, and duplicate protection where supported. | Governance/status changes require audit evidence; future lifecycle events wait for TASK-020. | Do not expose raw UCNs, private customer identifiers, or cross-role participant internals. |
| Links/codes | Public resolve/validation and partner/internal issue/list/void surfaces. | Public resolve is validation-only; issue/list/void requires Partner, Distribution Admin, or scoped role owner. | Link/code ownership must resolve to tenant, campaign, and participant context before privileged actions. | Issue and void commands require idempotency; resolve/validate reads must reject malformed or expired inputs safely. | Link lifecycle emissions wait for TASK-020; operator voids require audit where supported. | Public responses must return safe link/code state only, not raw attribution internals. |
| Events | Public/partner ingestion and internal worker/admin inspection. | Partner credential, integration credential, or System Admin for admin inspection/replay; Worker secret for internal processing. | Tenant is credential-derived for partner ingestion; admin tooling may require explicit tenant filters. | Ingestion requires source event identity, schema validation, dedupe/idempotency, and retry/dead-letter behavior. | Ingested events must create processing/audit evidence where current services support it; outbound event catalog waits for TASK-020. | Client responses should expose accepted/rejected/duplicate-style outcomes without raw worker errors. |
| Outcomes | Internal/operator read API first; future partner/customer views must be separately safe. | System Admin, Finance Admin, Distribution Admin, or a future scoped support permission depending on route purpose. | Outcome lookups must be tenant-scoped and must not trust caller-supplied tenant for non-admin identities. | Read-only and side-effect free; validation covers lookup type, tenant scope, and requested sections. | Uses support trace, missing evidence, audit references, and correlation references from the outcome trace contract. | External surfaces must not expose raw UCNs, raw provider errors, or raw audit internals. |
| Rewards | Internal/admin and tenant-safe summary surfaces. | Finance Admin for money operations; Partner or scoped role owner only for safe summaries. | Tenant, participant, and campaign scope must be enforced before reward reads or commands. | Reward mutations require idempotency and policy validation; summaries are read-only. | Reward commands require audit/correlation evidence where supported. | Keep customer reward and distributor commission boundaries separate. |
| Funding | Finance/internal/operator surfaces only until a safe tenant reporting contract exists. | Finance Admin for funding operations; System Admin only for support/audit views where applicable. | Cross-tenant operations require explicit tenant filters; tenant-facing reads must be derived and scoped. | Reserve/release/settle-style commands require idempotency and balance/limit validation. | Funding state changes require audit and reconciliation evidence where supported. | Do not expose account internals, wallet internals, or provider settlement details externally. |
| Fulfilment | Finance/internal/operator surfaces; future external status views are safe-derived only. | Finance Admin or Worker depending on operation; System Admin for replay/support only where designed. | Tenant and reward/commission ownership must be validated before reads or commands. | Fulfilment commands and retries require idempotency, bounded retry rules, and safe validation errors. | Fulfilment actions require audit/correlation evidence where supported. | External responses must use external-safe status mapping, not raw provider or DLQ details. |
| Settlement | Finance/internal/operator surfaces; future external status views are safe-derived only. | Finance Admin for settlement operations and approvals; System Admin for support/audit views where applicable. | Tenant, batch, item, reward, and commission ownership must be checked before exposure. | Settlement commands, approvals, reversals, and retries require idempotency or duplicate protection where applicable. | Settlement actions require audit/correlation evidence where supported. | External responses must use external-safe status mapping and hide raw settlement internals. |
| Analytics/reporting | Tenant-safe read APIs and operator reporting surfaces. | Tenant admin/integration credential for tenant reports; Finance/Distribution/System Admin for operator reports by domain. | Tenant filter is mandatory for tenant-facing reports; cross-tenant operator reports require explicit role scope. | Read-only; pagination, export parameters, freshness, and dimensions must be validated. | Export actions should be auditable where supported. | Reports must distinguish operational metrics from ledger-backed money totals and avoid private identifiers. |
| Audit/support | Internal/operator only unless a future support-safe customer view is explicitly designed. | System Admin for audit/replay; domain admins may read domain-scoped audit where authorized. | Cross-tenant support access must be explicit and traceable. | Read-only support traces are side-effect free; replay/repair actions require separate command contracts. | Must preserve correlation IDs, audit references, missing-evidence markers, and redactions. | Do not expose secrets, provider payloads, private identifiers, or raw DLQ payloads to external surfaces. |
| Credentials | Internal account/admin and partner integration management. | Platform Admin or future account admin for create/rotate/revoke; Partner OAuth/token flows must bind client identity. | Credential ownership maps external tenant/client references into internal `tenant_code` and partner/client records. | Create/rotate/revoke commands require validation, audit, one-time secret handling, and duplicate protection where supported. | Credential lifecycle changes require audit and usage attribution hooks. | Never return stored secrets after creation or write secrets to logs/errors. |
| Webhooks | Partner subscription/delivery API and admin/operator delivery tooling. | Partner identity for own subscriptions/deliveries; System Admin for replay/export/support; future tenant admin where scoped. | Subscription and delivery access must bind to tenant/client ownership. | Subscription mutations require idempotency and target URL validation; delivery retry/export requires guarded command contracts. | Delivery signing, retry, dead-letter, and alert evidence come from partner seam; event catalog waits for TASK-020. | Payload and delivery diagnostics must avoid raw internal state unless explicitly operator-only. |

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
