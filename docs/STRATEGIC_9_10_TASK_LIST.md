# Strategic 9/10 Task List

This is the broader execution backlog beyond the completed enterprise-readiness
checklist. Status values:

- `Done`: implemented and verified in this repo.
- `Partial`: meaningful coverage exists, but the full strategic target is not complete.
- `Todo`: not yet implemented.

## Phase 0: Prove The Platform

| Status | Task | Evidence |
| --- | --- | --- |
| Done | Fix migration baseline so a clean database can provision from zero. | `scripts/init_db.py`, migration replay gate |
| Done | Rename/fix remaining migration files with naming issues. | `scripts/check_migrations.py` |
| Done | Add CI check for duplicate migration numbers. | `.github/workflows/ci.yml`, `scripts/check_migrations.py` |
| Done | Add CI job: create empty DB, run migrations, run seed/bootstrap, hit `/readyz`. | `.github/workflows/ci.yml` now has `clean-db-readiness`: Postgres service, migrations, seed/bootstrap, API startup, and `/readyz` verification. |
| Done | Add backend smoke suite for critical APIs: health, session, partner, consumer, admin, distribution. | `scripts/target_state_smoke.py`, `scripts/core_role_journey_smoke.py` |
| Done | Add frontend CI gates: TypeScript build, smoke check, lint, unit tests. | `frontend/package.json`, `.github/workflows/ci.yml` |
| Done | Add frontend lint/format tooling: ESLint + Prettier. | `frontend/eslint.config.js`, `frontend/package.json` |
| Done | Add frontend test tooling: Vitest + React Testing Library. | `frontend/src/test/setup.ts`, frontend tests |
| Done | Add route-level bundle/code-splitting to reduce the main JS chunk. | `frontend/src/app/App.tsx` |
| Done | Document from-zero tenant provisioning as a release gate. | `docs/PRODUCTION_RUNBOOK.md` |

## Phase 1: Add The Experience Layer

| Status | Task | Evidence |
| --- | --- | --- |
| Done | Create consumer BFF endpoint: profile, progress, rewards, missions, leaderboard, proof. | `apps/api/routers/consumer_experience.py` |
| Done | Create admin command-centre BFF endpoint: health, events, funding, settlement, channels, risks. | `apps/api/routers/admin_experience.py`, `test/test_admin_experience_api.py` |
| Done | Create distributor BFF endpoint: opportunities, wallet, routes, commissions, performance. | `apps/api/routers/distributor_experience.py`, `test/test_distributor_experience_api.py` |
| Done | Create sponsor BFF endpoint: billing, forecasts, contracts, utilisation, alerts. | `apps/api/routers/sponsor_experience.py`, `test/test_sponsor_experience_api.py` |
| Done | Add role-scoped response shaping to BFF endpoints. | Consumer, admin, distributor, and sponsor BFFs enforce role/tenant scope |
| Done | Add backend tests for every BFF endpoint. | `test/test_consumer_experience_api.py`, `test/test_admin_experience_api.py`, `test/test_distributor_experience_api.py`, `test/test_sponsor_experience_api.py` |
| Done | Move frontend consumer page off raw domain API fan-out. | `frontend/src/pages/consumer/ConsumerPortalPage.tsx` |
| Done | Move admin overview/command centre onto the admin BFF. | `frontend/src/api/endpoints/adminExperience.ts`, `frontend/src/pages/admin/AdminOverviewPage.tsx` |
| Done | Move sponsor and distributor portals onto their BFF endpoints. | `frontend/src/pages/sponsor/SponsorPortalPage.tsx`, `frontend/src/pages/distributor/DistributorPortalPage.tsx` |
| Done | Add error/loading/empty-state standards for all BFF-backed pages. | Consumer page plus workspace smoke coverage |

## Phase 2: Frontend Maturity

| Status | Task | Evidence |
| --- | --- | --- |
| Done | Add TanStack Query for all server-state calls. | TanStack Query is installed with an app-wide provider, query client defaults, shared keys, experience hooks, operational hooks, partner integration hooks, distributor wallet hooks, shell health hooks, backend session hooks, and channel operations hooks; `frontend/scripts/maturity-check.mjs` gates the query infrastructure. |
| Done | Replace direct `useEffect + fetch` patterns with query hooks. | Critical workspace reads now use API clients/query hooks instead of raw page-level fetches; `frontend/scripts/maturity-check.mjs` prevents raw browser `fetch` calls in the key workspace pages. |
| Done | Split `DistributionCommandCentrePage` into feature components. | Marketplace browsing view is extracted to `frontend/src/pages/admin/distribution/DistributionMarketplaceView.tsx`; the maturity check gates this component boundary as part of the admin distribution standard. |
| Done | Split `SponsorPortalPage` into feature components. | Producer workspace view is extracted to `frontend/src/pages/sponsor/components/SponsorWorkspaceView.tsx`; the maturity check gates this component boundary. |
| Done | Split `DistributorPortalPage` into feature components. | Earnings hub view is extracted to `frontend/src/pages/distributor/components/DistributorHubView.tsx`; the maturity check gates this component boundary. |
| Done | Split `ConsumerPortalPage` into journey sections. | Consumer journey action panels extracted to `ConsumerJourneySections`; smoke checks now follow the component boundary. |
| Done | Add tests for consumer referral journey. | `frontend/src/pages/consumer/ConsumerPortalPage.test.tsx` |
| Done | Add tests for admin command-centre workflows. | `frontend/src/pages/admin/DistributionCommandCentrePage.test.tsx` |
| Done | Add tests for sponsor billing/forecast workflows. | `frontend/src/pages/sponsor/SponsorPortalPage.test.tsx` |
| Done | Add tests for distributor opportunity/wallet workflows. | `frontend/src/pages/distributor/DistributorPortalPage.test.tsx` |
| Done | Add tests for partner integration page. | `frontend/src/pages/partner/PartnerIntegrationPage.test.tsx` |
| Done | Add accessibility pass: keyboard navigation, labels, focus states. | `frontend/src/pages/WorkspaceAccessibility.test.tsx` checks representative workspaces for named controls, valid ARIA references, and no positive tabindex overrides; `frontend/src/styles/base.css` now has a shared focus-visible standard for links, buttons, form fields, and role-based controls. |
| Done | Add responsive QA for mobile/tablet/desktop. | `frontend/src/test/uxQuality.test.ts` and `frontend/scripts/smoke-check.mjs` now gate tablet workspace collapse, mobile data readability, compact controls, visible focus, and typography guardrails; frontend smoke is green at 134 checks. |
| Done | Add design-system primitives for tables, filters, panels, status, actions. | Shared primitives now cover tables, segmented filters, panels/titles, field labels, summaries, status badges, and action guardrails. |
| Done | Remove duplicated UI logic from large page files. | Shared `SummaryItem`, `SummaryGrid`, `PanelTitle`, `FieldLabel`, `DataTable`, `SegmentedFilter`, `StatusBadge`, and `ActionGuardrail` primitives replace repeated page-local UI logic; `frontend/scripts/maturity-check.mjs` gates the primitive set. |

## Phase 3: Channels Become Real

| Status | Task | Evidence |
| --- | --- | --- |
| Done | Implement WhatsApp provider adapter. | `services/channel_provider_adapters.py` adds `WhatsAppProviderAdapter` with WhatsApp-specific text payload shaping, adapter headers, and HMAC signing; `test/test_channel_readiness_service.py` verifies provider body, signature, and dispatch guardrails. |
| Done | Implement SMS provider adapter. | `services/channel_provider_adapters.py` adds `SmsProviderAdapter` with SMS-specific payload shaping, adapter headers, and HMAC signing; `test/test_channel_readiness_service.py` verifies provider body, signature, and dispatch guardrails. |
| Done | Add outbound delivery queue for channel messages. | `services/channel_readiness_service.py` now creates a `QUEUED` delivery record before provider handoff and exposes sanitized delivery operations through `/admin/channels/deliveries`; tests verify queue evidence and no raw recipient/message leakage. |
| Done | Add consent and opt-out checks before send. | Messaging dispatch requires consent evidence and blocks opted-out recipients before any provider call; `test/test_channel_readiness_service.py` covers both guardrails. |
| Done | Add signed provider callbacks where supported. | `/channels/webhooks/{channel_code}` requires HMAC signatures before normalizing callbacks or mutating delivery status; channel webhook tests cover valid signature handling. |
| Done | Add delivery status capture: queued, sent, delivered, failed. | Delivery records move through `QUEUED`, `SENT`, `FAILED`, and callback-driven `DELIVERED`; tests prove provider response and signed callback status capture. |
| Done | Add retry and dead-letter handling for channels. | Channel delivery retry is limited to recoverable provider failures, capped at three attempts, audited with `RETRY_QUEUED`, and moved to `DEAD_LETTERED` for non-retryable or exhausted failures; admin retry endpoint and service tests cover the lifecycle. |
| Done | Add channel audit trail. | Channel delivery state changes write sanitized audit events and `/admin/channels/audit` exposes operations evidence without raw recipient or message values; API and service tests cover the contract. |
| Done | Add channel observability: counts, failures, latency. | Delivery operations expose queued/sent/delivered/failed counts, while dispatch metrics already record delivery status, provider status, and latency without PII; focused channel tests remain green. |
| Done | Add admin channel operations dashboard. | `frontend/src/pages/admin/ChannelOperationsPage.tsx` adds an admin channel operations surface for readiness, delivery lifecycle filters, retryable failures, dead-letter posture, and audit evidence; route/navigation wiring, endpoint helpers, query hook, and focused tests are in place. |
| Done | Add consumer/distributor channel preferences. | Scoped `/channels/preferences/{audience}/{subject_id}` APIs store preferred, consented, and opted-out channels for consumer and distributor audiences; recommendation scoring applies preferences and excludes opted-out channels, with auth/scope tests in `test/api/test_channels_api.py`. |
| Done | Implement USSD after WhatsApp/SMS lifecycle is stable. | `services/channel_provider_adapters.py` adds `UssdProviderAdapter` with session payload shaping and HMAC signing; dispatch and inbound session menu tests verify USSD lifecycle behavior. |

## Phase 4: Partner And Security Hardening

| Status | Task | Evidence |
| --- | --- | --- |
| Done | Add OAuth token store/refresh maturity checks. | Partner OAuth-style client credential tokens are stored hashed with expiry, revocation, scope validation, and bearer authentication checks; `scripts/oauth_token_maturity_check.py` gates token lifecycle markers. |
| Done | Add partner rate limiting by client and tenant. | Rate-limit middleware keys requests by tenant and hashed client subject; `test/test_rate_limit.py` covers per-client buckets and is included in the security regression CI job. |
| Done | Add partner webhook delivery SLA metrics. | Webhook attempts now emit Prometheus count and latency metrics by tenant, client, event type, delivery status, and HTTP status; partner seam tests and monitoring docs cover the signal. |
| Done | Add webhook replay controls and audit. | Partner/admin webhook retry is limited to failed or cancelled deliveries, partner retries are client-scoped, retry requests write `PARTNER_WEBHOOK_DELIVERY_RETRY` audit evidence, and partner seam tests are in the security regression CI job. |
| Done | Add secret rotation runbook. | `docs/SECURITY_AUTH.md`, `docs/RELEASE_SECURITY_CHECKLIST.md` |
| Done | Add production readiness endpoint coverage tests. | `scripts/target_state_smoke.py`, readiness tests |
| Done | Audit all routers for auth consistency. | `utils/permissions.py`, `test/test_permissions.py` |
| Done | Add security regression suite to CI. | `.github/workflows/ci.yml` now has a dedicated `security-regression` job for settings, permission, and release evidence tests; local run is green. |
| Done | Add API permission matrix documentation. | `docs/API_PERMISSION_MATRIX.md` maps route families, role helpers, tenant rules, and regression evidence; linked from `docs/SECURITY_AUTH.md`. |
| Done | Add tenant isolation tests for sensitive endpoints. | `test/test_permissions.py`, BFF scope tests |

## Phase 5: 9/10 Release Gate

| Status | Task | Evidence |
| --- | --- | --- |
| Done | Full backend suite green in CI. | `.github/workflows/ci.yml` |
| Done | Frontend tests green in CI. | `.github/workflows/ci.yml` |
| Done | Clean DB provisioning green in CI. | `scripts/init_db.py`, migration gates |
| Done | Critical user journeys covered by tests. | Consumer, admin command-centre, sponsor, distributor, and partner workflow tests cover the critical role journeys; workspace smoke remains green. |
| Done | Main frontend bundle split and under agreed threshold. | `frontend/src/app/App.tsx` |
| Done | Consumer/admin/sponsor/distributor pages use BFF endpoints. | Consumer, admin, sponsor, and distributor pages load primary read models through BFF endpoints |
| Done | WhatsApp/SMS adapters proven in sandbox. | `scripts/channel_sandbox_smoke.py` verifies configured WhatsApp/SMS sandbox providers, dispatches consented test messages, and confirms delivery evidence through admin channel operations; command is documented in `docs/ONBOARDING_RUNBOOK.md`. |
| Done | Observability dashboard covers API, DB, queues, partner, channels. | Grafana overview now covers API, DB, SQS/Kafka readiness, BFF health, admin audit, partner webhooks, channel dispatch, enterprise events, and rewards; dashboard JSON has regression coverage. |
| Done | Runbook exists for tenant onboarding, partner onboarding, channel setup. | `docs/ONBOARDING_RUNBOOK.md` covers tenant, partner, channel, pilot validation, monitoring, handover, and rollback; linked from production and security release gates. |
| Done | One pilot tenant can be provisioned, configured, tested, and monitored end-to-end. | `scripts/pilot_tenant_validation.py` runs readiness, role journey smoke, admin command-centre, channel operations, consumer/distributor preferences, and optional WhatsApp/SMS sandbox proof for one tenant; command is documented in `docs/ONBOARDING_RUNBOOK.md`. |
