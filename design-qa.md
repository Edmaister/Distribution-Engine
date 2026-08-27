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
---

## TASK-462 Account establishment

Source visual truth paths:
- C:/Users/Carla/AppData/Local/Temp/codex-clipboard-5e96148e-a671-49f2-93a8-8f60b358288f.png
- C:/Users/Carla/AppData/Local/Temp/codex-clipboard-44370ab2-be2a-4f9b-858e-294590c8d123.png
- C:/Users/Carla/AppData/Local/Temp/codex-clipboard-63485a00-da5b-4e65-ad03-71ba86f0e5c5.png
- C:/Users/Carla/AppData/Local/Temp/codex-clipboard-aaa9dc3b-6def-4069-947a-a03168f3f0a1.png

Implementation route: http://127.0.0.1:5173/admin/referral-saas/account-maintenance/49cb3b6d-e8bc-4ae0-81a6-9d5f6115a6da/settings
Implementation screenshot path: unavailable
Reference viewport: desktop, approximately 1782 x 1030 pixels at browser density
Implementation viewport and density: unavailable because capture failed
State: Organisation, Jurisdiction & environment, Agreement, and Activation stages implemented; browser-rendered evidence unavailable.

Full-view comparison evidence:
- Blocked. The trusted in-app browser process exited during startup before the implementation could be captured.
- The supplied source screens were available in the task, but the local image inspection helper also failed with the same Windows sandbox refresh error.

Focused region comparison evidence:
- Blocked for the same reason. No valid implementation screenshot exists for normalized side-by-side comparison.

Code and interaction validation:
- Bundled Sora and DM Mono typography remains scoped through the selected-customer Amplifi shell.
- Four interactive stages use authoritative account registry, readiness, commercial entitlement, and production activation evidence.
- The guarded profile-maintenance command remains available behind Maintain organisation.
- Focused Sidebar and selected-customer tests passed: 50/50.
- Production build passed.
- Browser primary interaction and console checks: blocked.

Findings:
- [Blocked] Pixel-level font weight, line wrapping, column proportions, spacing rhythm, and responsive screenshots cannot be certified without a rendered capture.
- [Expected constraint] Prototype-only registration, named owner/reviewer, effective-date, and audit-reference values are not invented; returned backend evidence or explicit unavailable values are used instead.
- [Expected constraint] Governed actions route to existing health, integrations, and commercial destinations rather than prototype-only endpoints.

Comparison history:
- Initial implementation completed from the four supplied visual states.
- User capture C:/Users/Carla/AppData/Local/Temp/codex-clipboard-c6ab1a86-62d7-4da9-bc13-e9b9934302a1.png exposed a P1 grid-placement failure: an undefined visually-hidden class rendered the accessibility heading as a fourth grid item, displaced the three intended columns, and squeezed evidence values into vertical text.
- Fixed by using the established sr-only utility, assigning explicit steps/main/governance grid areas, adding min-width guards, defining the two-row tablet and one-column mobile areas, and restoring the white prototype canvas.
- Post-fix focused tests and production build passed; post-fix screenshot capture remains blocked by the Windows browser helper failure.
- P0/P1/P2 visual comparison could not start because implementation capture failed.
- No screenshot-driven visual fixes were claimed.

- User capture C:/Users/Carla/AppData/Local/Temp/codex-clipboard-1ff0bcf8-34cf-4b39-bba3-5d93816361d3.png confirmed the corrected column layout but exposed two progression-state issues: completed and current markers were both blue, and the referenced sr-only utility was not actually defined, leaving the accessibility heading visible.
- Corrected the visible semantics to blue for completed stages, amber for the selected stage, and neutral for future stages; implemented the shared sr-only utility so the accessibility heading is removed from the visual layout.
- Post-correction visual comparison remains blocked until a refreshed implementation capture is available.

final result: blocked