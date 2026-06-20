# Application Component Map

This map explains the major moving parts in the Referral Engine application:
what each component does, where requests enter, which services carry the logic,
and which data areas are involved.

## Top-Level Runtime

| Component | Files | Responsibility |
| --- | --- | --- |
| FastAPI application | `apps/api/main.py` | Builds the API app, registers routers, configures health, metrics, CORS, DB lifecycle, and global error handling. |
| API settings | `apps/api/settings.py` | Loads environment settings such as DB DSN, API keys, worker secret, SQS, Redis, and tenant keys. |
| Database helpers | `utils/db.py` | Provides async Postgres connection pooling and connection context managers. |
| Queue helpers | `utils/queue.py` | Publishes events to SQS when configured, otherwise appends to a local JSONL queue file. |
| Security helpers | `utils/security.py` | Enforces platform admin, finance admin, distribution admin, system admin, partner, admin-or-partner, and any-key authentication. |
| Admin audit | `services/admin_audit_service.py`, `apps/api/routers/admin_audit.py` | Records and exposes sensitive admin actions across finance, distribution, and system operations. |
| Logging helpers | `apps/core/logging_utils.py`, `utils/logging.py` | Provides structured application logging. |

## Main Business Flow

```text
Partner issues referral code
        |
        v
Customer validates referral
        |
        v
UCN and account lifecycle events are recorded
        |
        v
Journey orchestrator advances referral state
        |
        v
Reward policy and fulfilment can run from journey state
```

Core tables involved include:

- `referrer_codes`
- `referral_instances`
- `referral_progress_events`
- `referral_rewards`
- `referral_processing_audit`

See also:

- `docs/SEQUENCE_FLOWS.md`
- `docs/ERD.md`
- `docs/RUNTIME_SMOKE_TEST.md`

## Referral Code And Validation

| Area | Entry points | Services | Purpose |
| --- | --- | --- | --- |
| Referrer bootstrap | `POST /referrals/bootstrap`, `POST /referrals/accept-terms` | `referral_bootstrap_service.py` | Creates or validates a referrer profile and terms state. |
| Referral code issuing | `POST /referrals/codes` | `referral_code.py` | Issues or retrieves referral codes for a referrer. |
| Public referral validation | `POST /public/referrals/validate` | `referral_code.py`, `campaign_service.py` | Validates a scanned/entered referral code and creates the referral track. |
| Referee UCN capture | `POST /referrals/referees/ucn` | `referral_code.py` | Links the referred customer UCN to the referral track. |

Main router files:

- `apps/api/routers/referrals.py`
- `apps/api/routers/referral_bootstrap.py`
- `apps/api/routers/composite_codes.py`
- `apps/api/routers/campaigns.py`

## Journey And Progress

| Area | Entry points | Services | Purpose |
| --- | --- | --- | --- |
| Partner progress event | `POST /v1/progress` | `progress_service.py` | Records progress events and queues platform progress messages. |
| Referrer progress read model | `GET /v1/referrers/{referrerUcn}` | `progress_service.py` | Returns UI-safe progress summaries for a referrer. |
| Worker journey processing | `POST /worker/referral-events` | `journey_orchestrator.py` | Applies queued progress events to referral journey state. |
| Journey rules | Internal | `journey_definitions.py`, `progress_definitions.py` | Defines allowed state transitions and progress display. |

Important behavior:

- Journey transitions are ordered.
- Out-of-order events are recorded/audited but do not incorrectly advance state.
- Completion is derived from journey state and reward rules.

## IDS / Hogan Enterprise Events

| Area | Entry points | Services | Purpose |
| --- | --- | --- | --- |
| Enterprise event ingestion | `POST /enterprise/events` | `apps/Workers/ids_consumer.py` | Stores raw Hogan/IDS events, dedupes them, normalizes qualifying events, and queues progress. |
| Inbox admin summary | `GET /admin/enterprise-events/summary` | `enterprise_event_inbox_service.py` | Shows event counts by processing status. |
| Inbox dashboard | `GET /admin/enterprise-events/dashboard` | `enterprise_event_inbox_service.py` | Shows dashboard counts by status, source system, event type, and recent problem events. |
| Inbox admin list | `GET /admin/enterprise-events` | `enterprise_event_inbox_service.py` | Lists recent inbox events with filters. |
| Inbox replay | `POST /admin/enterprise-events/{inbox_event_id}/replay` | `enterprise_event_inbox_service.py` | Dry-runs or queues a stored normalized payload again. |

Main data:

- `enterprise_event_inbox`
- `enterprise_events` compatibility view

Qualifying IDS/Hogan events currently include:

- `ACCOUNT_ACTIVATED`
- `DEBIT_ORDER_SWITCHED`
- `SALARY_DEPOSIT`
- `SALARY_SWITCHED`
- `POLICY_ACTIVATED`

See:

- `docs/IDS_HOGAN_EVENT_INBOX.md`

## Workers And Async Processing

| Worker | File | Purpose |
| --- | --- | --- |
| SQS referral worker | `apps/Workers/sqs_referral_worker.py` | Polls SQS and routes worker events to journey, leaderboard, or fulfilment logic. |
| Legacy/local referral consumer | `apps/Workers/referral_events_consumer.py` | Deprecated consumer path kept for compatibility. |
| IDS consumer | `apps/Workers/ids_consumer.py` | Ingests and normalizes Hogan/IDS events into the enterprise inbox. |
| Recommendation refresher | `apps/Workers/recommendation_refresher.py` | Refreshes recommendation data. |
| Reward scheduler | `apps/Workers/reward_scheduler.py` | Runs scheduled reward-related work. |
| Gamification hooks | `apps/Workers/gamification_hooks.py` | Supports gamification-related worker hooks. |

Worker endpoint:

- `apps/api/routers/worker.py`
- `POST /worker/referral-events`

Supported worker event families:

- `REFERRAL_PROGRESS_RECORDED`
- leaderboard rebuild events
- reward fulfilment requested events

## Rewards

| Area | Entry points | Services | Purpose |
| --- | --- | --- | --- |
| Reward application | `POST /rewards/apply` | `reward_service.py`, `reward_policy_service.py` | Applies reward instructions and emits downstream fulfilment events. |
| Reward summary | Reward summary endpoints | `reward_summary_service.py` | Returns reward state for referrals/referrers. |
| Reward policy | Internal | `reward_policy_service.py` | Determines base reward instructions from referral state and policies. |
| Reward events | Internal | `fulfilment_events.py` | Builds reward fulfilment requested events. |

Main routers:

- `apps/api/routers/rewards.py`
- `apps/api/routers/reward_summary.py`

Main data:

- `referral_rewards`
- reward policy/configuration tables
- fulfilment audit tables

## Fulfilment And Settlement

| Area | Entry points | Services | Purpose |
| --- | --- | --- | --- |
| Fulfilment processing | Worker event path, admin fulfilment routes | `services/fulfilment/service.py` | Fulfils reward requests through provider-specific implementations. |
| Provider resolution | Internal | `services/fulfilment/resolver.py`, `factory.py`, `providers/*` | Chooses and calls cash, data, eBucks, voucher, or tenant instruction providers. |
| Fulfilment audit | Admin fulfilment routes | `fulfilment_audit_service.py` | Tracks fulfilment attempts, statuses, and provider references. |
| Retry/replay | `POST /admin/fulfilment/replay/{audit_id}` | `fulfilment_replay_service.py`, `fulfilment_retry_*` | Requeues failed fulfilment where safe. |
| Provider health | Admin fulfilment provider routes | `fulfilment_provider_health_service.py`, `fulfilment_metrics_service.py` | Reports provider health and fulfilment metrics. |
| Settlement | Admin settlement routes | `services/fulfilment/settlement/*` | Manages settlement periods, batches, approvals, exceptions, reversals, certifications, and lock enforcement. |

Main routers:

- `apps/api/routers/admin_fulfilment.py`
- `apps/api/routers/admin_settlement.py`
- `apps/api/routers/admin_settlement_batches.py`
- `apps/api/routers/admin_settlement_approvals.py`
- `apps/api/routers/admin_settlement_exceptions.py`
- `apps/api/routers/admin_settlement_reversals.py`
- `apps/api/routers/admin_settlement_periods.py`
- `apps/api/routers/admin_settlement_certifications.py`
- `apps/api/routers/admin_settlement_lock_enforcement.py`

## Funding And Marketplace Funding

| Area | Entry points | Services | Purpose |
| --- | --- | --- | --- |
| Funding contracts | `apps/api/routers/funding_contracts.py` | `funding_contract_repository.py`, marketplace funding services | Manages funding agreements/contracts. |
| Funding admin | Admin funding routes | `services/funding/*` | Handles funding rules, reservations, limits, exposure, funding account forecasts, sponsor wallet forecasts, contract forecasts, alerts, reconciliation, and dashboard data. |
| Multi-currency | `apps/api/routers/admin_multi_currency.py` | `services/funding/multi_currency.py`, `apps/api/schemas/multi_currency.py` | Manages FX rates, conversion quotes, and cross-border settlement instructions. |
| Sponsor wallets | `apps/api/routers/marketplace_funding/sponsor_wallets.py` | `services/marketplace_funding/*` | Manages sponsor wallets, balances, ledger entries, top-ups, and sponsor funding state. |
| Sponsor billing | `apps/api/routers/sponsor_billing.py`, `apps/api/routers/sponsor_portal_billing.py` | `sponsor_billing_service.py`, `sponsor_billing_repository.py` | Creates sponsor invoices, invoice lines, invoice payment records, payment receipts, allocations, generated invoices from contract utilisation, sponsor statements, billing dashboards, VAT reports, and sponsor-facing billing views. |
| Budget governance | `apps/api/routers/admin_budget_governance.py` | `budget_governance_service.py` | Manages budget increase requests, approvals, rejections, approved contract increases, and contract ledger audit entries. |
| Distributor model | `apps/api/routers/distribution/admin_distributors.py` | `services/distribution/distributor_service.py`, `apps/api/schemas/distribution/distributors.py` | Manages distributor profiles, lifecycle status, channels, segments, regions, eligibility, capabilities, and operating limits. |
| Distributor wallets | `apps/api/routers/distribution/admin_distributor_wallets.py` | `services/distribution/distributor_wallet_service.py`, `apps/api/schemas/distribution/wallets.py` | Manages distributor earnings, holds, releases, payouts, reversals, balances, and wallet ledger entries. |
| Commission engine | `apps/api/routers/distribution/admin_commissions.py` | `services/distribution/commission_service.py`, `apps/api/schemas/distribution/commissions.py` | Manages commission rules, commission calculations, commission events, and optional distributor wallet credits. |
| Opportunity marketplace | `apps/api/routers/distribution/admin_opportunities.py` | `services/distribution/opportunity_service.py`, `apps/api/schemas/distribution/opportunities.py` | Manages sponsor-funded opportunities, targeting filters, lifecycle publishing, and distributor-ready marketplace listings. |
| Offer routing | `apps/api/routers/distribution/admin_routing.py` | `services/distribution/routing_service.py`, `apps/api/schemas/distribution/routing.py` | Scores active distributors against published opportunities, previews matches, persists offer routes, and tracks accept/decline status. |
| Distributor portal/API | `apps/api/routers/distribution/distributor_portal.py` | `services/distribution/distributor_portal_service.py`, `apps/api/schemas/distribution/distributor_portal.py` | Exposes distributor-facing profile, offer inbox, accept/decline actions, wallet, ledger, and performance views. |
| Marketplace governance | `apps/api/routers/distribution/admin_governance.py` | `services/distribution/governance_service.py`, `apps/api/schemas/distribution/governance.py` | Manages compliance reviews, disputes, distributor governance actions, operating-limit changes, and governance audit records. |
| Marketplace reporting | `apps/api/routers/distribution/admin_reporting.py` | `services/distribution/reporting_service.py`, `apps/api/schemas/distribution/reporting.py` | Provides marketplace overview, opportunity performance, distributor performance, and governance reporting. |

Main funding service modules:

- `services/funding/orchestrator.py`
- `services/funding/account_resolution.py`
- `services/funding/account_rules.py`
- `services/funding/reservations.py`
- `services/funding/exposure.py`
- `services/funding/exposure_limits.py`
- `services/funding/forecasting.py`
- `services/funding/alerts.py`
- `services/funding/reconciliation.py`
- `services/funding/dashboard.py`
- `services/funding/resolution_audit.py`

Main funding routers:

- `apps/api/routers/admin_funding.py`
- `apps/api/routers/admin_multi_currency.py`
- `apps/api/routers/admin_funding_rules.py`
- `apps/api/routers/admin_funding_audit.py`
- `apps/api/routers/admin_funding_forecast.py`
- `apps/api/routers/admin_funding_alerts.py`
- `apps/api/routers/admin_funding_reconciliation.py`
- `apps/api/routers/admin_budget_governance.py`
- `apps/api/routers/distribution/admin_distributors.py`
- `apps/api/routers/distribution/admin_distributor_wallets.py`
- `apps/api/routers/distribution/admin_commissions.py`
- `apps/api/routers/distribution/admin_opportunities.py`
- `apps/api/routers/distribution/admin_routing.py`
- `apps/api/routers/distribution/distributor_portal.py`
- `apps/api/routers/distribution/admin_governance.py`
- `apps/api/routers/distribution/admin_reporting.py`
- `apps/api/routers/funding_contracts.py`

Main marketplace funding modules:

- `services/funding/multi_currency.py`
- `sponsor_wallet_service.py`
- `sponsor_wallet_balance_service.py`
- `sponsor_wallet_ledger_service.py`
- `sponsor_wallet_repository.py`
- `sponsor_wallet_ledger_repository.py`
- `sponsor_funding_service.py`
- `funding_contract_service.py`
- `budget_governance_service.py`
- `sponsor_billing_service.py`
- `sponsor_billing_repository.py`

See:

- `docs/SPONSOR_BILLING.md`
- `docs/FUNDING_FORECASTING.md`
- `docs/BUDGET_GOVERNANCE.md`
- `docs/MULTI_CURRENCY.md`
- `docs/DISTRIBUTION_MARKETPLACE.md`

## Distribution Marketplace Target

The current funding and settlement components are the foundation for a broader
distribution marketplace. That target state is separate from funding completion.

| Target area | Current status | Intended responsibility |
| --- | --- | --- |
| Distributor model | Application-complete | Represent distributor entities, profiles, eligibility, operating limits, and lifecycle status. |
| Distributor wallets | Application-complete | Track distributor earnings, holds, reversals, releases, balances, and ledger entries. |
| Commission engine | Application-complete | Calculate distributor commission separately from customer or referrer rewards. |
| Opportunity marketplace | Application-complete | Publish sponsor-funded opportunities and make them available to eligible distributors. |
| Offer routing | Application-complete | Match offers, campaigns, sponsors, and products to suitable distributors. |
| Distributor portal/API | Application-complete | Let distributors view offers, tasks, performance, earnings, and statements. |
| Marketplace governance | Application-complete | Manage onboarding, compliance, disputes, suspensions, limits, and audit trails. |
| Marketplace reporting | Application-complete | Provide sponsor, platform, and distributor views of conversion, ROI, earnings, and settlement status. |

See:

- `docs/TARGET_STATE_ROADMAP.md`

## Recommendations And Gamification

| Area | Entry points | Services | Purpose |
| --- | --- | --- | --- |
| Recommendations | Recommendation endpoints and admin recommendation routes | `recommendation_service.py`, `recommendation_compliance_service.py` | Generates and governs next-best-action style recommendations. |
| Campaign insights | Admin recommendation endpoints | `admin_recommendations.py`, recommendation services | Surfaces campaign insights and recommendation analytics. |
| Missions | `apps/api/routers/missions.py` | `mission_service.py` | Tracks user missions and mission progress. |
| Badges | `apps/api/routers/badges.py` | `badge_service.py` | Awards and lists badges based on referral behavior. |
| Leaderboards | `apps/api/routers/leaderboards.py` | `leaderboard_service.py`, `leaderboard_events.py` | Maintains and rebuilds leaderboard standings. |
| Gamification | Internal/user-facing progress | `gamification_service.py` | Supports mission/badge/progress gamification state. |

See:

- `docs/RECOMMENDATIONS.md`
- `docs/RECOMMENDATIONS_OPTIMIZATION.md`

## Admin, Failure, Replay, And Governance

| Area | Entry points | Services | Purpose |
| --- | --- | --- | --- |
| Processing failures | `/admin/failures` | `failure_admin_service.py`, `failure_governance_service.py` | Lists, resolves, and reprocesses captured event failures. |
| DLQ replay | `/admin/dlq/replay` | `dlq_replay_service.py`, `dlq_service.py` | Replays supported DLQ payloads. |
| Referral projection replay | `/internal/replay/referrals/{referral_track_id}` | `replay_service.py` | Rebuilds referral projection from recorded progress events. |
| Privacy | Privacy endpoints | `privacy_service.py`, `privacy_purge_scheduler.py` | Handles privacy/erasure workflows. |
| Tenant admin | Admin tenant routes | `tenant_service.py` | Tenant-oriented admin operations. |

Replay types:

- Inbox replay queues a normalized enterprise event again.
- DLQ replay replays failed worker payloads.
- Referral projection replay rebuilds stored journey projection from progress
  event history.
- Fulfilment replay requeues failed fulfilment attempts.

## Provider Ranking And SLA

| Area | Entry points | Services | Purpose |
| --- | --- | --- | --- |
| Provider SLA | `apps/api/routers/provider_sla.py` | `provider_sla_service.py`, `provider_scorecard_service.py` | Reports provider SLA and scorecard information. |
| Provider ranking | Internal/admin endpoints | `provider_ranking_service.py`, `provider_routing_engine.py` | Ranks providers and supports provider routing decisions. |
| Provider statement imports | Admin/import flows | `provider_statement_import_service.py` | Imports provider statements for reconciliation/settlement support. |

## Finance And Reconciliation

| Area | Entry points | Services | Purpose |
| --- | --- | --- | --- |
| Finance metrics | Admin finance routes | `finance_metrics_service.py` | Provides finance/reconciliation metrics. |
| Reconciliation runs | Admin reconciliation routes | `reconciliation_run_service.py`, `reconciliation_history_service.py` | Tracks reconciliation runs and history. |
| Reconciliation exceptions | Admin reconciliation exception routes | `reconciliation_exception_service.py`, `reconciliation_exception_status.py` | Manages reconciliation exceptions and statuses. |

Main routers:

- `apps/api/routers/admin_finance.py`
- `apps/api/routers/admin_reconciliation.py`
- `apps/api/routers/admin_reconciliation_exceptions.py`

## API Surface By Audience

| Audience | Typical endpoints | Authentication |
| --- | --- | --- |
| Public/customer flow | `/public/referrals/validate` | Public validation request payload |
| Partner systems | `/referrals/*`, `/v1/progress`, `/enterprise/events` | Partner API key |
| Admin/Ops | `/admin/*`, `/internal/replay/*` | Admin API key |
| Worker/SQS bridge | `/worker/referral-events` | Worker secret |
| Health/metrics | `/healthz`, `/readyz`, `/health`, `/metrics` | Environment/network controlled |

## Data And Schema Areas

| Area | Folder/files | Purpose |
| --- | --- | --- |
| Migrations | `dp/migrations/*.sql` | Database schema evolution. |
| Seeds | `dp/seeds/*.sql` | Optional seed/reference data. |
| Migration runner | `scripts/init_db.py` | Applies migrations in sorted order. |
| Seed runner | `scripts/seed_db.py` | Applies seed SQL in sorted order. |
| Backfill/maintenance scripts | `scripts/*.py` | Operational refresh, backfill, and maintenance jobs. |

## Where To Start

For architecture:

- `docs/CURRENT_STATE_AUDIT.md`
- `docs/ERD.md`
- `docs/SEQUENCE_FLOWS.md`
- `docs/APPLICATION_COMPONENT_MAP.md`
- `docs/FRONTEND_API_CONTRACT_MAP.md`
- `docs/FRONTEND_BUILD_PLAN.md`
- `docs/AMPLIFI_FRONTEND_BRAND_NOTES.md`

For IDS/Hogan:

- `docs/IDS_HOGAN_EVENT_INBOX.md`
- `docs/RUNTIME_SMOKE_TEST.md`

For operations:

- `docs/PRODUCTION_RUNBOOK.md`
- `docs/MONITORING.md`
- `docs/ALERTING.md`
- `docs/TESTING.md`
