# Front-to-Back Referral Test Cases

This matrix captures the behaviours we want to prove from the user entry point through backend processing, reward creation, fulfilment, and operational visibility.

## Scope

- Frontend entry points: `/consumer`, `/distributor`, `/sponsor`, `/admin`, `/admin/distribution`, `/admin/settlements`, `/admin/billing`, `/admin/events`, and `/admin/health`.
- Core APIs: `/referrals/bootstrap`, `/referrals/accept-terms`, `/referrals/codes`, `/public/referrals/validate`, `/referrals/referees/ucn`, `/v1/progress`, `/v1/referrers/{referrerUcn}`, `/v1/referrers/{referrerUcn}/dashboard`, `/v1/referrals/{referralTrackId}/dashboard`, `/rewards/apply`, and `/admin/fulfilment/*`.
- Backend services: referral code issue and validation, progress service, journey orchestrator, reward service, fulfilment provider routing, fulfilment audit, retry/replay, settlement, funding, reconciliation, and dashboard summaries.
- Out of scope for these cases: provider contract testing against real external providers. Those should be covered by provider sandbox tests and contract tests.

## Test Data Baseline

Use deterministic tenant and actor data so the same scenario can be run locally, in CI, and against a seeded test environment.

| Data | Example | Notes |
| --- | --- | --- |
| Tenant | `FNB` | Must match the API key tenant used by partner/admin auth. |
| Referrer UCN | `9999999999` | Existing or freshly bootstrapped referrer. |
| Referee UCN | `1234567890` | Distinct from referrer. |
| Product | `Transactional` | Aligns with current lifecycle tests. |
| Sub-product | `DDA13` | Aligns with current lifecycle tests. |
| Journey | Catalog configured journey / `v1` | Banking uses `BANKING_TRANSACTIONAL`; Insurance and Retail Loyalty use their own configured journey definitions. |
| Distributor | Seeded active distributor | Needed for distribution attribution scenarios. |
| Sponsor/producer | Seeded funded sponsor | Needed for funding and settlement scenarios. |

## Configured Vertical Baseline

The platform should be exercised as a catalog-driven engine, not as a
banking-only lifecycle. Banking remains the primary transactional fixture, while
Insurance and Retail Loyalty prove that journeys, milestones, identifiers,
rewards, leaderboard rules, fulfilment routing, and regulatory overlays can vary
by vertical.

| Vertical | Journey | Completion proof |
| --- | --- | --- |
| Banking | `BANKING_TRANSACTIONAL` / `v1` | Account, funding, and salary/transaction completion events. |
| Insurance | `INSURANCE_POLICY` / `v1` | Quote, policy issue, first premium, and policy completion events. |
| Retail Loyalty | `RETAIL_LOYALTY` / `v1` | Basket, order, and first purchase completion events. |

## P0 End-to-End Cases

| ID | Scenario | Entry point | Steps | Expected backend result | Expected UI/API confirmation |
| --- | --- | --- | --- | --- | --- |
| FTBE-001 | Referrer starts referral journey | `/consumer` | Bootstrap referrer, accept terms, issue referral code. | Referrer profile exists, terms are accepted, one active referrer code is created for the tenant/sticker/segment. | Consumer portal shows the referrer context and issued referral code without duplicate code creation on repeat. |
| FTBE-002 | Referee validates referral code | `/consumer` public validation flow | Submit referral code with accepted terms, alias/device metadata where available. | `validate_referral_code` creates/updates a referral instance and logs the QR/scan attempt. Invalid tenant or code does not create a valid referral. | Response contains `valid=true`, `referralTrackId`, `validationOutcome=VALIDATED`; UI shows the next step to capture UCN. |
| FTBE-003 | Referee UCN is captured | `/consumer` | Submit `referralTrackId` and referee UCN. | Referee UCN is stored via the referral capture service, protected/hash fields are populated, and the referral moves to UCN-captured state. | UI/API response is successful; referral dashboard can be loaded by `referralTrackId`. |
| FTBE-004 | Progress completes normal lifecycle | Backend event/API entry | Post `UCN_CAPTURED`, `ACCOUNT_OPENED`, `ACCOUNT_ACTIVATED`, `FUNDED`, then `SALARY_SWITCHED` or `FIRST_TRANSACTION_COMPLETED` to `/v1/progress`. | `referral_progress_events` records each fact, journey orchestrator advances allowed states, referral completes only after funded plus qualifying sub-function, and audit rows are `PROCESSED`. | `/v1/referrers/{referrerUcn}` and referral dashboard show 100% progress, complete status, next milestone cleared or finalised. |
| FTBE-005 | Reward is created for completed referral | Reward processing entry | Apply reward or trigger the completion path that invokes reward logic. | One idempotent reward exists for the referral and beneficiary; reward policy resolves in the correct order: campaign override, sticker-level, fallback. | Consumer reward summary totals include pending/earned reward and the referral appears in dashboard history. |
| FTBE-006 | Reward fulfilment succeeds | Fulfilment service/provider path | Route reward to selected provider, process fulfilment, store provider reference. | `fulfilment_audit` records `SUCCESS`, idempotency key is persisted, provider reference is stored, and duplicate attempts are skipped. | Admin fulfilment dashboard success count increases; fulfilment audit detail shows provider and reference. |
| FTBE-007 | Settlement includes fulfilled reward | `/admin/settlements` | Generate settlement batch for the period containing the fulfilled reward. | Batch item includes the fulfilled reward, totals reconcile to reward/fulfilment ledgers, and approval/certification rules are enforced. | Settlement Operations page shows the batch, item counts, totals, and approval/certification status. |

## P0 Failure and Idempotency Cases

| ID | Scenario | Entry point | Steps | Expected backend result | Expected UI/API confirmation |
| --- | --- | --- | --- | --- | --- |
| FTBE-008 | Duplicate referral code issue is safe | `/consumer` | Request a code twice for the same referrer, tenant, sticker, and segment. | Existing active code is returned or only one active code is created according to service rules. | UI continues to show one code and does not imply a new referral was created. |
| FTBE-009 | Duplicate validation is safe | `/public/referrals/validate` | Validate the same code multiple times with the same device/referee context. | Scan attempts are auditable; referral instance is not incorrectly duplicated. | UI/API returns stable `referralTrackId` or clear duplicate/validation message. |
| FTBE-010 | Duplicate progress event is ignored | `/v1/progress` | Submit the same source system/event ID twice. | First request creates the progress fact; second returns deduped response and does not mutate state twice. | API returns `deduped=true` on duplicate; dashboards remain unchanged after duplicate. |
| FTBE-011 | Out-of-order progress does not advance state | `/v1/progress` | Submit `FUNDED` before `ACCOUNT_OPENED`/`ACCOUNT_ACTIVATED`. | Event is stored for audit, journey state remains at prior allowed state, and audit reason is `out_of_order`. | Consumer/admin dashboards show current milestone, not completed progress. |
| FTBE-012 | Backward progress does not regress state | `/v1/progress` | Reach `FUNDED`, then submit another earlier `ACCOUNT_OPENED`. | Referral remains `FUNDED`; audit row is ignored/duplicate. | Dashboards continue showing funded progress and do not move backwards. |
| FTBE-013 | Reward application is idempotent | `/rewards/apply` | Apply the same reward instruction twice with same referral and beneficiary. | Only one reward is persisted; second call returns existing/idempotent result or clear duplicate handling. | Reward summary total is not doubled. |
| FTBE-014 | Fulfilment duplicate is skipped | Fulfilment service | Process same reward/idempotency key twice. | First fulfilment executes; second creates `SKIPPED_DUPLICATE` or equivalent audit state without provider call. | Admin fulfilment duplicate skipped count increases; no extra provider reference is created. |

## P1 Fulfilment Operations Cases

| ID | Scenario | Entry point | Steps | Expected backend result | Expected UI/API confirmation |
| --- | --- | --- | --- | --- | --- |
| FTBE-015 | Retryable provider failure is recoverable | Fulfilment provider adapter | Simulate timeout or transient provider error. | Audit status becomes `FAILED_RETRYABLE`, attempt count increments, retry policy schedules another attempt. | `/admin/fulfilment/failures` lists the item with retryable status and error code. |
| FTBE-016 | Final provider failure is visible | Fulfilment provider adapter | Exhaust max attempts or simulate non-retryable provider rejection. | Audit status becomes `FAILED_FINAL` or `DLQ`, failure reason is stored, and no settlement item is created as successful. | Admin fulfilment page shows failure counts and the failed audit detail. |
| FTBE-017 | Manual replay succeeds | `/admin/fulfilment/replay/{audit_id}` | Replay a failed audit after provider/service recovery. | Replay creates a new attempt, updates status to `SUCCESS`, stores provider reference, and links audit trail. | Admin fulfilment dashboard moves the item from failure to success or shows replay outcome. |
| FTBE-018 | Provider health influences routing | `/admin/fulfilment/providers/health` | Mark a provider degraded/unhealthy, then process a reward. | Routing selects an eligible healthy provider or circuit breaker prevents unsafe call. | Provider health endpoint and admin dashboard show degraded provider and routed/blocked outcome. |
| FTBE-019 | Fulfilment audit lookup works | `/admin/fulfilment/audit/{audit_id}` | Load a known audit ID and an unknown audit ID. | Known audit returns full audit; unknown returns `not_found`. | Admin detail state can display audit data and missing-state copy cleanly. |

## P1 Distribution and Attribution Cases

| ID | Scenario | Entry point | Steps | Expected backend result | Expected UI/API confirmation |
| --- | --- | --- | --- | --- | --- |
| FTBE-020 | Admin publishes demand and distributor accepts | `/admin/distribution`, `/distributor` | Create or use a seeded opportunity, publish it, route it, accept the offer. | Opportunity status becomes published; route moves to accepted; distributor wallet/performance context remains tenant-scoped. | Admin and distributor portals both show the accepted route. |
| FTBE-021 | Distributor links referral to route | `/distributor` | Link an accepted offer to a referral track ID. | Distribution attribution link is created once and attached to the referral/opportunity route. | Distributor conversions view shows the referral; admin reporting includes attribution. |
| FTBE-022 | Unaccepted route cannot link referral | `/distributor` | Attempt to link referral to a draft/declined/unaccepted route. | Service rejects with validation error; no attribution row is created. | UI shows the failure and route remains unchanged. |
| FTBE-023 | Distributor performance updates after conversion | `/distributor`, `/admin/distribution` | Complete referral lifecycle after route link. | Conversion counts and commission/attribution summaries update for route, distributor, and opportunity. | Distributor performance and admin reporting reflect routed, accepted, converted, and completed counts. |

## P1 Funding, Billing, and Settlement Cases

| ID | Scenario | Entry point | Steps | Expected backend result | Expected UI/API confirmation |
| --- | --- | --- | --- | --- | --- |
| FTBE-024 | Funded sponsor can support reward spend | `/sponsor`, `/admin/billing` | Load sponsor wallet/contracts, process reward, reserve/consume funds. | Wallet/contract ledger reflects reservation/consumption; exposure and forecast update. | Sponsor portal shows wallet movement and forecast impact. |
| FTBE-025 | Insufficient funding blocks or flags reward | Reward/fulfilment path | Process reward where sponsor wallet/contract has insufficient available balance. | Funding reservation fails or creates governance exception according to policy; fulfilment does not silently succeed. | Sponsor/admin funding views show alert, exception, or blocked status. |
| FTBE-026 | Billing statement matches settled rewards | `/sponsor`, `/admin/billing` | Generate/load billing statement for period with fulfilled rewards. | Statement totals reconcile to settlement batch and sponsor ledger. | Sponsor statement shows invoice/payment/outstanding totals accurately. |
| FTBE-027 | Settlement reversal updates ledgers | `/admin/settlements` | Reverse a settled reward item. | Reversal record is created, settlement and wallet/contract ledgers are adjusted, audit trail is retained. | Settlement page shows reversal status and updated totals. |

## P2 UI and Contract Cases

| ID | Scenario | Entry point | Steps | Expected backend result | Expected UI/API confirmation |
| --- | --- | --- | --- | --- | --- |
| FTBE-028 | Auth and tenant boundaries hold | All protected routes | Use missing, invalid, partner, and admin keys across partner/admin endpoints. | Protected endpoints reject the wrong role/key; tenant is derived from auth where required. | UI shows clear blocked/error states and never leaks other-tenant data. |
| FTBE-029 | API errors render useful UI states | `/consumer`, `/distributor`, `/sponsor`, `/admin` | Force 400, 401/403, 404, 409, 429, and 500 responses. | API returns structured errors and correlation IDs where available. | Pages show non-empty error panels and keep forms recoverable. |
| FTBE-030 | Loading and empty states are stable | All primary pages | Load pages with no records and slow responses. | No backend changes expected. | Loading, empty, and retry controls render without layout shift or broken tables. |
| FTBE-031 | Frontend request contracts match API schemas | Frontend API clients | Exercise each client in `frontend/src/api/endpoints/*` with seeded responses. | Request field names match backend schemas; response parsing tolerates optional fields. | No runtime errors in portal pages; visible fields map to correct response properties. |
| FTBE-032 | Dashboard totals agree across surfaces | `/consumer`, `/admin`, `/sponsor`, `/distributor` | Complete one referral and reward, then compare dashboards. | Source tables, materialized/summary APIs, and reporting endpoints produce consistent counts/totals. | Consumer reward summary, distributor conversions, sponsor spend, fulfilment dashboard, and settlement views agree. |

## Automation Map

| Layer | Recommended automation |
| --- | --- |
| Frontend smoke | Keep `npm run build` and `npm run smoke`; add browser tests for `/consumer`, `/distributor`, `/sponsor`, and admin pages once fixtures are stable. |
| API contract | Add pytest API tests for each endpoint request/response shape using FastAPI test client and seeded/mocked services. |
| Service behaviour | Extend existing service tests for idempotency, out-of-order events, fulfilment failures, funding failures, and replay. |
| Integration | Extend `test/test_lifecycle_e2e.py` to cover reward creation, fulfilment success/failure, and dashboard assertions. |
| Full journey | Add a small Playwright or API-driven smoke that runs FTBE-001 through FTBE-007 against a seeded environment. |

## Existing Coverage Anchors

- `test/test_lifecycle_e2e.py` already covers progress completion, duplicate events, out-of-order events, backward events, and funded-plus-sub-function completion.
- `test/test_referrals_api.py`, `test/test_referral_bootstrap_api.py`, and `test/test_rewards_router.py` cover parts of the referral and reward API surface.
- `test/test_fulfilment_*.py` covers fulfilment services, provider health, audit, replay, reconciliation, retry, and settlement behaviours.
- `test/api/distribution/*` covers distribution portal/admin APIs and attribution-related reporting.

## Open Decisions

- Decide whether the full journey smoke should drive the UI with Playwright or drive APIs and use frontend smoke checks only.
- Decide which provider adapters should have sandbox contract tests versus mocked service tests.
- Define the canonical seeded campaign/sponsor/distributor fixture names for repeatable CI runs.
