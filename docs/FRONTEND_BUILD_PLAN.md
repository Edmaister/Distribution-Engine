# Frontend Build Plan

This plan converts the frontend API contract into an implementation blueprint.
It uses the Amplifi brand kit and CX/UX brief as the design foundation while
still avoiding marketing pages. The first frontend should be an operational
product surface: calm, dense, scannable, and built around daily
admin/sponsor/distributor workflows.

Source references:

- `C:\Users\Carla\Downloads\amplifi-brand-kit_2.html`
- `C:\Users\Carla\Downloads\amplifi-cx-ux-brief_6.html`

See also `docs/AMPLIFI_FRONTEND_BRAND_NOTES.md` for implementation-ready brand
rules.

## Amplifi Product Design Direction

Amplifi should feel like distribution infrastructure, not a generic referral
tool. The UI should signal trust, precision, scale, and operational control.

Core brand rules:

- Use `Amplifi` with capital A, lowercase rest, and the Signal Blue dot where
  the wordmark is shown.
- Position the product as a distribution infrastructure platform.
- Use exact, spare language. Avoid hype, exclamation points, and vague
  superlatives.
- Use Signal Blue as the sole brand accent.
- Use Gold only for premium or executive contexts.
- Avoid purple, neon palettes, busy gradients, and competing accent colours.
- Do not describe the product as a referral or loyalty platform in UI copy.

## Design Tokens

Initial CSS variables should be defined in `frontend/src/styles/tokens.css`.

```css
:root {
  --amplifi-ink: #0a0e1a;
  --amplifi-ink-mid: #1c2238;
  --amplifi-ink-soft: #3a4260;
  --amplifi-rule: #e4e7f0;
  --amplifi-white: #ffffff;
  --amplifi-off: #f5f6fa;
  --amplifi-signal: #1a56f0;
  --amplifi-signal-mid: #3d70f5;
  --amplifi-signal-light: #ebf0ff;
  --amplifi-gold: #c8a96e;
  --amplifi-gold-light: #f7f0e4;
  --amplifi-success: #0d9e72;
  --amplifi-success-light: #ecfdf5;
  --amplifi-warning: #d97706;
  --amplifi-warning-light: #fffbeb;
  --amplifi-danger: #dc2626;

  --font-sans: "Sora", system-ui, sans-serif;
  --font-mono: "DM Mono", ui-monospace, monospace;

  --text-xs: 11px;
  --text-sm: 13px;
  --text-base: 15px;
  --text-lg: 18px;
  --text-xl: 22px;
  --text-2xl: 28px;
  --text-3xl: 38px;

  --radius-sm: 8px;
  --radius-md: 10px;
  --radius-lg: 12px;
  --radius-xl: 16px;
}
```

Semantic colours may use success/warning/danger for statuses, but they should
not compete with Signal Blue as brand accents.

## Typography

| Role | Token | Use |
| --- | --- | --- |
| Display | Sora 800, tight line-height | Rarely used in product UI |
| Page title | Sora 700, 28-38px | Major page headings |
| Section title | Sora 600, 18-26px | Panels, tables, page sections |
| Body | Sora 400, 15px | Normal product copy |
| Label | Sora 500, 11px uppercase | Filters, status sections, table meta |
| Data/technical | DM Mono 400, 11-13px | IDs, metrics labels, timestamps, codes |

Operational UI should use smaller, tighter headings than the brand/landing
examples. Reserve large type for true external-facing pages.

## UX Principles From The Brief

The frontend should implement these as constraints:

- Infrastructure-grade trust at every touchpoint.
- Matched value before matched volume.
- Reward the behaviour, not just the outcome.
- Compliance as confidence, not constraint.
- Every surface serves a single job-to-be-done.
- Enterprise control without enterprise friction.

Practical translation:

- Always show status, amount, owner, and next step on operational records.
- Make eligibility and compliance visible as confidence signals.
- Use tables for comparison-heavy admin workflows.
- Use cards for individual opportunities, invoices, wallets, and summaries.
- Keep dashboards focused on momentum and control, not decoration.
- Show raw IDs where operations users need traceability.

## Personas To Design For

| Persona | Primary job | Frontend implication |
| --- | --- | --- |
| Distributor | Find matched opportunities, understand earnings, track progress, get paid | Offer inbox, earning clarity, wallet and performance views |
| Enterprise Operator | Launch and control compliant, measurable campaigns at scale | Admin control centre, distributor governance, audit, reporting |
| Community Admin | Enable members to participate with low operational overhead | Future community portal and shared wallet views |
| AI Distribution Agent | Operate through deterministic rules and full auditability | Future API/agent console and audit surfaces |

The current frontend plan covers the Enterprise Operator, Sponsor, and
Distributor slices first. Community Admin and AI Agent surfaces remain roadmap
items.

## Recommended Stack

| Layer | Recommendation | Reason |
| --- | --- | --- |
| App framework | React + Vite + TypeScript | Fast local development, simple deployment, good fit for an API-backed console |
| Routing | React Router | Clear route ownership across admin, sponsor, and distributor surfaces |
| API client | OpenAPI-generated or thin typed wrapper around `fetch` | Keeps frontend aligned to FastAPI contracts |
| Data fetching | TanStack Query | Handles loading, caching, retries, invalidation, and background refresh |
| Forms | React Hook Form + Zod | Good for admin forms and backend validation mapping |
| Tables | TanStack Table | Needed for audit logs, invoices, distributors, ledger, events |
| Charts | Recharts or lightweight chart library | Enough for operational cards and trends |
| Icons | lucide-react | Simple, consistent operational icon set |
| Styling | CSS variables + plain CSS modules or Tailwind | Keep Amplifi tokens separate from layout structure |

The first scaffold should include the Amplifi tokens immediately. Final visual
polish can still come later.

## Proposed Folder Structure

```text
frontend/
  package.json
  vite.config.ts
  tsconfig.json
  src/
    app/
      App.tsx
      routes.tsx
      providers.tsx
    api/
      client.ts
      endpoints/
        adminAudit.ts
        enterpriseEvents.ts
        funding.ts
        sponsorBilling.ts
        distribution.ts
        sponsorPortal.ts
        distributorPortal.ts
        health.ts
      types/
    auth/
      authStore.ts
      RequireRole.tsx
      ApiKeySessionPanel.tsx
    layout/
      AppShell.tsx
      Sidebar.tsx
      TopBar.tsx
      TenantSelector.tsx
      HealthBanner.tsx
    components/
      ActionBar.tsx
      ConfirmDialog.tsx
      DataTable.tsx
      EmptyState.tsx
      ErrorPanel.tsx
      FilterBar.tsx
      FormField.tsx
      KpiCard.tsx
      LoadingState.tsx
      StatusBadge.tsx
    pages/
      admin/
      sponsor/
      distributor/
    styles/
      tokens.css
      base.css
```

Fonts should be loaded in the app shell:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700;800&family=DM+Mono:wght@300;400;500&display=swap" rel="stylesheet">
```

If production policy blocks external font loading, bundle the font files later.

## Route Map

### Shared Routes

| Route | Page | Purpose |
| --- | --- | --- |
| `/` | Redirect | Send user to the relevant default surface |
| `/session` | Session setup | Temporary API-key/session setup until real identity exists |
| `/health` | Health view | Operational readiness view |

### Admin Console Routes

| Route | Page | Primary endpoints |
| --- | --- | --- |
| `/admin` | Admin overview | `/health`, `/readyz`, selected summaries |
| `/admin/operations/enterprise-events` | Enterprise Events | `/admin/enterprise-events/*` |
| `/admin/operations/audit` | Admin Audit | `/admin/audit`, `/admin/audit/summary` |
| `/admin/operations/failures` | Failures | `/admin/failures/*`, `/admin/dlq/replay` |
| `/admin/funding/dashboard` | Funding Dashboard | `/admin/funding/dashboard*` |
| `/admin/funding/contracts` | Funding Contracts | `/admin/funding/contracts*` |
| `/admin/funding/wallets` | Sponsor Wallets | `/admin/marketplace-funding/sponsor-wallets*` |
| `/admin/funding/billing` | Sponsor Billing | `/admin/funding/sponsor-billing/*` |
| `/admin/funding/governance` | Budget Governance | `/admin/funding/budget-governance/*` |
| `/admin/funding/multi-currency` | Multi-Currency | `/admin/multi-currency/*` |
| `/admin/distribution/distributors` | Distributors | `/admin/distribution/distributors*` |
| `/admin/distribution/opportunities` | Opportunities | `/admin/distribution/opportunities*` |
| `/admin/distribution/routing` | Routing | `/admin/distribution/routing*` |
| `/admin/distribution/commissions` | Commissions | `/admin/distribution/commissions*` |
| `/admin/distribution/wallets` | Distributor Wallets | `/admin/distribution/distributor-wallets*` |
| `/admin/distribution/governance` | Marketplace Governance | `/admin/distribution/governance*` |
| `/admin/distribution/reporting` | Marketplace Reporting | `/admin/distribution/reporting*` |
| `/admin/settlement` | Settlement Ops | `/admin/settlements*`, settlement workflow routes |
| `/admin/fulfilment` | Fulfilment Ops | `/admin/fulfilment*` |
| `/admin/privacy` | Privacy Ops | `/v1/privacy/*` |
| `/admin/tenants` | Tenant Admin | `/admin/tenants/*` |

### Sponsor Portal Routes

Base context: `tenant_code`, `sponsor_code`.

| Route | Page | Primary endpoints |
| --- | --- | --- |
| `/sponsor/:tenantCode/:sponsorCode` | Sponsor Dashboard | `/v1/tenants/{tenant}/sponsors/{sponsor}/billing/dashboard` |
| `/sponsor/:tenantCode/:sponsorCode/invoices` | Invoices | `/billing/invoices*` |
| `/sponsor/:tenantCode/:sponsorCode/statements` | Statements | `/billing/statements` |
| `/sponsor/:tenantCode/:sponsorCode/receipts` | Payment Receipts | `/billing/payment-receipts*` |
| `/sponsor/:tenantCode/:sponsorCode/wallet` | Wallet | `/billing/wallet` |
| `/sponsor/:tenantCode/:sponsorCode/contracts` | Contracts | `/billing/contracts*` |
| `/sponsor/:tenantCode/:sponsorCode/forecast` | Forecast | `/billing/forecast` |

### Distributor Portal Routes

Base context: `tenant_code`, `distributor_code`.

| Route | Page | Primary endpoints |
| --- | --- | --- |
| `/distributor/:tenantCode/:distributorCode` | Distributor Home | `/distribution/portal/profile`, `/performance` |
| `/distributor/:tenantCode/:distributorCode/offers` | Offer Inbox | `/distribution/portal/offers` |
| `/distributor/:tenantCode/:distributorCode/wallets` | Wallets | `/distribution/portal/wallets` |
| `/distributor/:tenantCode/:distributorCode/wallets/:walletId` | Wallet Ledger | `/distribution/portal/wallets/{wallet_id}/ledger` |
| `/distributor/:tenantCode/:distributorCode/performance` | Performance | `/distribution/portal/performance` |

## Navigation Model

Admin Console should use grouped navigation:

- Operations: Health, Enterprise Events, Audit, Failures
- Funding: Dashboard, Contracts, Sponsor Wallets, Billing, Governance,
  Forecasts, Multi-Currency
- Distribution: Reporting, Distributors, Opportunities, Routing, Commissions,
  Wallets, Governance
- Settlement/Fulfilment: Settlements, Approvals, Exceptions, Reversals,
  Fulfilment, Provider Health
- Platform: Tenants, Privacy

For the Admin Console, the brief's Enterprise Control Centre pattern is the
closest fit: dark Ink sidebar, Signal Blue active state, compact topbar, KPI
cards, and dense campaign/distributor tables.

Sponsor Portal should use:

- Dashboard
- Invoices
- Statements
- Receipts
- Wallet
- Contracts
- Forecast

Distributor Portal should use:

- Home
- Offers
- Wallets
- Performance

For Distributor Portal, use the brief's distributor dashboard and marketplace
patterns: light sidebar, compact opportunity cards, visible earnings, match
labels, and eligibility tags.

## Shared Components

| Component | Purpose |
| --- | --- |
| `AppShell` | Overall page shell with sidebar, top bar, content region |
| `TenantSelector` | Admin tenant context selection |
| `HealthBanner` | Shows degraded backend readiness |
| `DataTable` | Sortable/filterable operational tables |
| `FilterBar` | Date/status/tenant/sponsor/distributor filters |
| `StatusBadge` | Consistent display for statuses such as QUEUED, FAILED, PAID, ACTIVE |
| `KpiCard` | Compact metric cards |
| `OpportunityCard` | Distributor marketplace opportunity summary |
| `MetricDelta` | Small trend label for KPI movement |
| `EligibilityTag` | Compliance/eligibility indicator |
| `ConfirmDialog` | Required before write actions |
| `ActionBar` | Page-level create/export/replay/action controls |
| `ErrorPanel` | Standard API error display |
| `EmptyState` | Empty data states |
| `LoadingState` | Skeleton/loading placeholder |
| `FormField` | Consistent labels, errors, help text |

## API Client Shape

The API client should keep auth and base URL handling in one place.

```ts
type ApiRequestOptions = {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  path: string;
  query?: Record<string, string | number | boolean | null | undefined>;
  body?: unknown;
  apiKey?: string;
};
```

Client responsibilities:

- Prefix requests with configured API base URL.
- Add `x-api-key` from the current temporary session.
- Serialize query params.
- Parse JSON responses.
- Normalize backend errors into one frontend error shape.
- Expose request IDs/correlation IDs when present.

Endpoint modules should group functions by domain, for example:

- `adminAudit.listAuditLog()`
- `adminAudit.getAuditSummary()`
- `enterpriseEvents.listEvents()`
- `enterpriseEvents.replayEvent()`
- `sponsorBilling.listInvoices()`
- `distribution.listDistributors()`
- `distributorPortal.acceptOffer()`

## First Build Slice

The first UI slice should be read-heavy and low risk.

1. Create the React app shell.
2. Add Amplifi tokens, Sora/DM Mono font loading, and base layout styles.
3. Add temporary session setup for API base URL and API key.
4. Add health/readiness page.
5. Add Admin Audit summary/list page.
6. Add Enterprise Events summary/list page.
7. Add Distribution Reporting page.
8. Add Sponsor Billing dashboard/invoice list page.
9. Add Distributor Portal offer inbox read view.

Only after these are stable, add write actions:

- Replay enterprise event.
- Issue invoice.
- Record payment.
- Route opportunity.
- Accept/decline distributor offer.
- Wallet movement actions.

## UX Rules For First Version

- No marketing landing page.
- First screen after session setup should be a working operations view.
- Use compact tables and KPI cards, not oversized hero blocks.
- Always show active filters.
- Always show backend status for admin users.
- Write actions must use confirmation dialogs.
- Destructive or financial actions must show the entity ID and amount before
  confirmation.
- Do not hide raw IDs; operations users need traceability.
- Use Signal Blue for primary actions, links, active states, and focus rings.
- Use DM Mono for IDs, codes, timestamps, metric labels, and technical states.
- Avoid emoji in production UI; use lucide icons.

## Backend Work Unblocked By This Plan

The frontend can start without these, but they remain important before real
production users:

| Need | Backend work |
| --- | --- |
| Real login | OAuth2/OIDC or equivalent identity/session service |
| Portal ownership | User-to-tenant, user-to-sponsor, and user-to-distributor mapping |
| Better command centre | Aggregated UI summary endpoints for high-level dashboards |
| Exports | Invoice PDF, statement PDF, CSV exports |
| Sponsor self-service | Payment upload, invoice dispute, top-up request |
| Distributor self-service | Profile edit, payout request, compliance document upload |

## Recommended Implementation Phases

### Phase 1: Shell And Read-Only Admin

Deliver:

- `frontend/` scaffold
- API client
- temporary session setup
- Amplifi design tokens and base product shell
- health/readiness page
- audit summary/list
- enterprise events summary/list
- distribution reporting overview

Exit criteria:

- Can point to `http://127.0.0.1:8000`.
- Can use `test-admin-key`.
- Can load real local data.
- No write actions yet.

### Phase 2: Finance And Distribution Operations

Deliver:

- Sponsor billing dashboard and invoice list/detail
- Funding dashboard and sponsor wallets
- Distributor list/detail
- Opportunities and routing read views
- Commission events
- Multi-currency rates/quotes/settlement list

Exit criteria:

- Admin can inspect the commercial state without using Swagger.

### Phase 3: Controlled Write Actions

Deliver:

- Enterprise event replay
- Invoice issue/payment/reversal flows
- Distributor lifecycle actions
- Opportunity publish/close/reopen
- Offer route creation
- Distributor wallet movement actions

Exit criteria:

- Every write action has a confirmation dialog.
- Every write action refreshes relevant tables.
- Audit page reflects the action where backend audit exists.

### Phase 4: Sponsor And Distributor Portals

Deliver:

- Sponsor dashboard, invoices, statements, wallet, contracts, forecast
- Distributor profile, offers, accept/decline, wallets, ledger, performance

Exit criteria:

- Sponsor and distributor users can complete their read/decision workflows.
- Identity limitations are clearly marked until production auth is added.

### Phase 5: Production Identity And Polish

Deliver:

- Real login/session flow
- Role-aware navigation
- Tenant/sponsor/distributor ownership enforcement through identity
- Final branding tokens
- Accessibility pass
- Playwright smoke tests

Exit criteria:

- UI is ready for controlled pilot users.
