# Current State Map

## Source Of Truth Reviewed

Current facts in this map are derived from:

- Database migrations in `dp/migrations`.
- API routers in `apps/api/routers`.
- Service-layer modules in `services`.
- Existing docs in `docs/TARGET_STATE_ROADMAP.md`, `docs/TARGET_STATE_TASK_BACKLOG.md`, `docs/DISTRIBUTION_MARKETPLACE.md`, `docs/SPONSOR_BILLING.md`, `docs/PARTNER_SEAM.md`, and related operational docs.

## Architecture Summary

The repository is a FastAPI backend with a broad service layer and SQL migration chain. It already contains referral, campaign, event ingestion, reward, funding, fulfilment, settlement, distribution marketplace, partner integration, audit, reporting, and role-scoped experience APIs.

The current system is feature-rich, but the DLaaS platform abstractions are uneven. Some areas are mature operationally, while SaaS account packaging, canonical platform state, tenant-safe product APIs, and white-label/embed foundations are not yet first-class.

## Current Capability Map

| Capability | Current status | Evidence |
| --- | --- | --- |
| Tenant model | Partial | `tenants` table in `031_tenent.sql`; `services/tenant_service.py`; `/admin/tenants`. Tenant is mostly internal `tenant_code`, not yet full SaaS account. TASK-048 decides external parties should use an external identifier boundary that maps into `tenant_code`; TASK-004 maps the account-to-tenant boundary in `docs/sa/TENANT_ACCOUNT_BOUNDARY_MAP.md`. |
| Campaign model | Partial | `marketing_campaigns`, `marketing_campaign_policies`, `campaign_attributions`, `campaign_track_events`; `services/campaign_service.py`; `apps/api/routers/campaigns.py`. |
| Referral model | Exists | `referrer_codes`, `referral_instances`, `referral_progress_events`, `referral_qr_scans`; `services/referral_code.py`; `apps/api/routers/referrals.py`. |
| Distribution marketplace | Exists | `distribution_distributors`, wallets, commissions, opportunities, routes, governance, route referral links; `services/distribution/*`; `/admin/distribution/*`; `/distribution/portal/*`. |
| Link/code generation | Partial | Referral codes and campaign referral links exist; distribution route referral links exist. A canonical distribution link/code service is not yet the platform spine. |
| Attribution tracking | Partial | `campaign_attributions`, `campaign_track_events`, `distribution_route_referral_links`, `referral_instances`, and journey events exist. A single canonical attribution/outcome table is not yet explicit. |
| Event ingestion | Exists | `/v1/progress`, `/enterprise/events`, `/worker/referral-events`; `enterprise_event_inbox`; workers and queue utilities. |
| Qualification logic | Partial | Journey/progress definitions and campaign policy validation exist. A general rules engine for eligibility, qualification, fraud, limits, and reward rules is not yet canonical. |
| Reward rules/records | Exists | `rewards`, reward policies, reward summaries, reward apply flow, reward fulfilment request events. |
| Funding/budget | Exists | Funding accounts, reservations, limits, exposure, alerts, reconciliation, sponsor wallets, funding contracts, contract ledger, budget governance. |
| Fulfilment/settlement | Exists | Fulfilment service, audit, retry, provider health, settlement batches, approvals, exceptions, reversals, periods, certifications. |
| Audit trail | Exists/partial | `admin_audit_log`, `referral_processing_audit`, `fulfilment_audit`, distribution governance audit, funding audit. Audit exists but is not yet one canonical platform event spine. |
| APIs | Exists/partial | Many admin, partner, public, worker, and role experience APIs exist. A clean public DLaaS API surface is not fully separated from app-specific routes. |
| Webhooks | Exists | Partner client credentials, access tokens, subscriptions, deliveries, alerts, retries, and dead-letter export exist in partner seam. |
| Operator control plane backend | Exists/partial | Admin command centre, failures, DLQ, audit, finance, funding, fulfilment, settlement, distribution, and reporting APIs. UX can be built on this but needs canonical status/control-plane IA. |
| Partner/customer portal backend | Partial | Distributor, sponsor, consumer, partner integration, reward summary, and experience APIs exist. Partner/customer status should be normalized and made safe. |
| Analytics/reporting | Partial | Distribution reporting, finance metrics, materialized views, dashboards, recommendations, and admin summaries exist. Tenant-facing reporting contracts need hardening. |
| SaaS packaging | Missing/partial | Partner credentials exist. No full account, plan, subscription, seat, usage metering, quota, or platform billing model. Sponsor billing is not SaaS platform billing. |
| White-label/embed | Missing | No current first-class branding, custom domain, embed client, SDK token, or allowed-origin model was identified. |

## Major Backend Domains

| Domain | Tables/schema | Services | Routes |
| --- | --- | --- | --- |
| Tenants/campaigns | `tenants`, `marketing_campaigns`, `marketing_campaign_policies`, `campaign_attributions`, `campaign_track_events` | `tenant_service.py`, `campaign_service.py`, `campaign_policy_service.py` | `/admin/tenants`, `/campaigns` |
| Referrals/journey | `referrer_codes`, `referral_instances`, `referral_progress_events`, `referral_qr_scans`, `referral_event_failures` | `referral_code.py`, `progress_service.py`, `journey_orchestrator.py`, `journey_definitions.py` | `/referrals`, `/public/referrals/validate`, `/v1/progress`, `/worker/referral-events` |
| Rewards | `rewards`, reward policies, reward summary tables/views | `reward_service.py`, `reward_policy_service.py`, `reward_summary_service.py` | `/rewards`, `/v1/rewards/summary` |
| Funding | funding accounts, reservations, limits, exposure, alerts, reconciliation, sponsor wallets, funding allocations, funding contracts, contract ledger | `services/funding/*`, `services/marketplace_funding/*` | `/admin/funding/*`, `/admin/marketplace-funding/sponsor-wallets`, sponsor billing/portal routes |
| Fulfilment/settlement | fulfilment audit/policies, settlement ledger, batches, items, approvals, exceptions, reversals, periods, certifications | `services/fulfilment/*`, `services/fulfilment/settlement/*` | `/admin/fulfilment/*`, `/admin/settlements`, `/admin/settlement/*` |
| Distribution marketplace | distributors, distributor wallets/ledger, commission rules/events, opportunities, offer routes, governance, route referral links | `services/distribution/*` | `/admin/distribution/*`, `/distribution/portal/*` |
| Partner seam/webhooks | partner clients, access tokens, webhook subscriptions/deliveries/alerts | `partner_seam_service.py`, `apps/Workers/partner_webhook_worker.py` | `/oauth/token`, `/partner/*`, `/admin/partners/*` |
| Audit/failure/ops | admin audit, processing audit, fulfilment audit, governance audit, DLQ/failure tables | `admin_audit_service.py`, `failure_admin_service.py`, `dlq_service.py`, `dlq_replay_service.py` | `/admin/audit`, `/admin/failures`, `/admin/dlq`, `/admin/enterprise-events` |

## Current Risks

- Tenant is widely represented internally as `tenant_code`; full account/user/seat membership, external identifier mapping, and SaaS entitlement boundaries are not first-class.
- Multiple state machines exist across referral, campaign, reward, funding, fulfilment, settlement, distribution, and webhooks; they need a canonical cross-domain map.
- There is strong money-flow machinery, but reward, commission, funding, fulfilment, settlement, sponsor billing, and SaaS billing must stay clearly separated.
- Existing APIs are broad; public DLaaS APIs should be formalized rather than exposing every internal/admin route.
- Partner/customer UX should use safe derived statuses, not raw internal failure, fraud, or settlement states.
