final result: blocked

Visual comparison could not be completed because the in-app browser helper failed to launch in this Windows sandbox.

Completed checks:
- Frontend production build passed.
- Frontend smoke check passed.
- Distributor route changes are scoped through the `distributor-app-shell` class and distributor page components.

Reference:
- Current target direction: dark premium Earnings Hub concept with first-class existing referral tracking.
- Marketplace target direction: dark distributor-facing campaign marketplace with search, filters, campaign cards, and preserved admin controls.
- Latest adjustment: Demand Marketplace is focused on campaign discovery; admin/operator controls moved to Demand Operations at `/admin/distribution/operations`.
- Latest adjustment: Earnings Hub is focused on earnings, opportunities, referral tracking, reputation, and leaderboard; action-heavy distributor controls moved to Earnings Operations at `/distributor/operations`.
- Latest adjustment: My Wallet added at `/distributor/wallet` with distributor wallet balances, settlement status, and wallet ledger movement using the existing distributor portal wallet APIs.
- Latest adjustment: Producer Workspace is focused on campaign performance, funding exposure, partner/channel readiness, and company-level supply posture; launch, lifecycle, statements, wallet ledger, invoices, receipts, and contract controls moved to Producer Operations at `/sponsor/operations`.
- Backend verification: local `/readyz` is OK for db/schema/funding/distribution/multi-currency/admin-audit; sponsor wallets, channel readiness, producer billing dashboard, producer wallet, and producer supply opportunity endpoints responded on `http://127.0.0.1:8000`.
- Latest adjustment: Partner Integration now falls back to an Amplifi Admin read-only integration posture when the partner self-service endpoint rejects an admin key. Local admin partner endpoints are currently returning 503, so the page surfaces unavailable admin data instead of blanking on 401.
- Latest adjustment: Producer Workspace spacing tightened to the Amplifi identity kit rhythm: 1280px content rail, 14px grid gaps, 8px cards, compact hero/action area, and shared Amplifi icon treatment.
- Latest adjustment: Producer Workspace now uses an immersive Amplifi shell, hiding the generic admin topbar and backend banners on `/sponsor` so the workspace header is the first row, matching the target company workspace reference.
