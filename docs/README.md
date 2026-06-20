# Documentation — Referrals & Campaign Attribution Platform

This folder (`docs/`) is the **handbook for Systems Analysts (SAs)** and developers.  
It explains the data model, business flows, recommendations logic, performance strategies, and front-end integration.

---

## 📂 File Index

### 1. ERD.md
- **Entity-Relationship Diagram** (Mermaid)
- Shows all database tables, keys, and relationships.
- Useful for understanding how referrals, rewards, campaigns, policies, gamification, and IDS events link together.

### 2. SEQUENCE_FLOWS.md
- **Sequence diagrams** (Mermaid) of core flows:
  - Referral issuance → validation → UCN capture
  - IDS event ingestion → reward application
  - Nightly recommendation refresh
- Explains service-to-DB-to-Kafka interactions.

### 3. PERFORMANCE_TUNING.md
- Guidance for **scaling** with:
  - **Partitions** (large event/scan tables split monthly)
  - **Materialized views** (precomputed admin insights)
- Helps DBAs and architects maintain speed at scale.

### 4. RECOMMENDATIONS.md
- Explains **Next-Best-Action (NBA)** logic:
  - Inputs: referrals, rewards, missions, events
  - Outputs: recommendation cards (`SEND_INVITE`, `COMPLETE_MISSION`, `APPLY_REWARD`)
- Helps analysts understand how gamification keeps users engaged.

### 5. RECOMMENDATIONS_OPTIMIZATION.md
- Covers **caching & insights**:
  - `recommendations_cache`: precomputed user NBAs
  - `campaign_insights_cache`: fast admin conversion KPIs
- Documents nightly refresh jobs and admin endpoints.

### 6. FRONTEND_UI.md
- Blueprint for **user & admin UIs**:
  - User portal: dashboard, invite, rewards, leaderboards
  - Admin console: campaigns, policy editor, insights, reward ops
- Maps **API endpoints to UI components** for clarity.

### 7. PRODUCTION_RUNBOOK.md
- Operational runbook for API, worker, migrations, IDS/Hogan ingestion,
  replay, monitoring, and incident checks.
- Useful before handover, deployment, or production readiness review.

### 8. APPLICATION_COMPONENT_MAP.md
- Component-by-component map of routers, services, workers, data areas, and
  operational entry points.
- Best starting point for understanding how the codebase is arranged.

### 9. SECURITY_AUTH.md
- Explains public, partner, admin, and worker authentication.
- Documents local test keys, production secrets, tenant key mapping, and
  operational auth checks.

### 10. DEPLOYMENT_SANITY_CHECK.md
- Records the local deployment checks performed, Docker/Helm checks still to
  run in an enabled environment, and the commands to use.

### 11. TARGET_STATE_ROADMAP.md
- Separates Funding Platform completion from Distribution Marketplace completion.
- Defines the remaining funding work and the later distribution capabilities:
  distributor model, distributor wallets, commission engine, opportunity
  marketplace, routing, portal/API, governance, and reporting.

### 12. SPONSOR_BILLING.md
- Explains sponsor invoices, invoice lines, payments, invoice issuing, and
  invoice generation from unbilled funding contract utilisation.

### 13. FUNDING_FORECASTING.md
- Explains funding account forecasts, sponsor wallet runway, sponsor contract
  exhaustion forecasts, burn windows, top-up recommendations, and remaining
  forecasting work.

### 14. BUDGET_GOVERNANCE.md
- Explains budget increase requests, approval/rejection, contract budget
  adjustment, and the audit trail for approved increases.

### 15. MULTI_CURRENCY.md
- Explains FX rates, conversion quotes, existing multi-currency wallet records,
  cross-border settlement instructions, and the local runtime smoke test.

### 16. DISTRIBUTION_MARKETPLACE.md
- Explains distributor profiles, lifecycle status, channels, segments,
  regions, eligibility, capabilities, operating limits, distributor wallets,
  balances, ledger entries, commission rules, commission events, sponsor-funded
  opportunities, opportunity lifecycle controls, offer routing, route scoring,
  route acceptance/decline, distributor portal APIs, compliance reviews,
  disputes, governance audit records, and marketplace reporting APIs.

### 17. DISTRIBUTION_MARKETPLACE_SMOKE_TEST.md
- Explains how to prove the distribution marketplace backend with read-only
  runtime checks, optional end-to-end write-flow checks, and migration rollout
  readiness checks.

---

## 🔑 How to use these docs

- **Systems Analysts (SAs)**: Start with [ERD.md](ERD.md) and [SEQUENCE_FLOWS.md](SEQUENCE_FLOWS.md) to understand the data model and lifecycle flows.
- **Developers**: Use [PERFORMANCE_TUNING.md](PERFORMANCE_TUNING.md) and [FRONTEND_UI.md](FRONTEND_UI.md) when implementing backend or UI integrations.
- **Marketing / Ops**: [RECOMMENDATIONS.md](RECOMMENDATIONS.md) and [RECOMMENDATIONS_OPTIMIZATION.md](RECOMMENDATIONS_OPTIMIZATION.md) explain how recommendations and campaign insights are surfaced.

---

## 🧩 Bigger Picture

- **db/** → migrations & seeds define the schema.
- **utils/** → infra helpers (DB, Kafka, Crypto, Logging).
- **apps/** → FastAPI routers, services, and workers implement the logic.
- **docs/** → this folder, which explains everything for humans.

Together, these layers ensure the referral & campaign platform is **data-driven, auditable, and extensible**.
