# Referral SaaS Commercial Finance Boundary

TASK-381 keeps commercial finance explicitly outside the H1 Referral Management
and Campaign Attribution SaaS promise unless a separate commercial finance
workstream is contracted.

## H1 Referral SaaS Entitlement Fields

Referral SaaS may show only the minimum fields needed to explain whether safe
setup can move toward production-capable use:

- `planCode`
- `planName`
- `contractSource`
- `launchAllowed`
- `productionActivationBlocked`
- reference limits, such as campaign/event/export posture

These fields are launch-gate evidence. TASK-464 permits Amplifi Admin to record
the minimum non-financial entitlement source, reference, effective window, and
responsible owner against the existing customer account with idempotency and
audit evidence. They are not a billing account, subscription, invoice, payment,
payout, funding reservation, or settlement instruction.

## Deferred Commercial Finance Capabilities

The H1 product must not create, update, expose as actionable, or imply ownership
of:

- billing accounts
- subscriptions
- invoices
- payments
- payouts
- funding
- settlement
- wallet ledger movement
- commission ledger movement
- treasury movement

## Where DLaaS Finance Begins

Commercial finance belongs to a separate DLaaS or separately contracted
workstream when the product needs:

- sponsor billing
- funding operations
- settlement batches
- commission settlement
- payout execution
- wallet ledger movement

## UI And API Guardrails

- H1 UI may show plan posture, launch blockers, no-money boundaries, and the
  governed minimum entitlement-evidence action defined by TASK-464.
- H1 UI must not show billing, invoice, funding, settlement, payout, wallet, or
  treasury actions as Referral SaaS product actions.
- H1 APIs must not expose Referral SaaS write routes for billing, invoices,
  funding, settlement, payouts, wallets, treasury, commissions, or money
  movement.
- The `/v1/referral-saas/accounts/{account_ref}/commercial-entitlement` response
  must return the commercial finance boundary as structured readback so frontend
  and support workflows can explain the separation plainly.


## TASK-464 solution package architecture (2026-09-08)

Product boundary: Referral SaaS, with Shared Platform account metadata, membership,
audit, idempotency, routing and permissions. Source duplication: No.

The authoritative catalogue is `services/referral_saas_solution_packages.py`.
The existing `planCode` contract stores one of:

| Code | Commercial capability |
| --- | --- |
| `REFERRAL_MANAGEMENT` | Referral campaign management, links/codes, referral progress and customer referral evidence |
| `CAMPAIGN_ATTRIBUTION` | Campaign attribution evidence and source/channel explanation |
| `REFERRAL_MANAGEMENT_AND_ATTRIBUTION` | Composition of both solutions, using the same services |

Current architectural facts verified in source:

- `apps/api/routers/campaigns.py` calls standalone `create_campaign` separately
  from `validate_campaign_and_create_track` in `services/campaign_service.py`.
- Campaign validation requires an existing active `marketing_campaigns` record
  and writes `campaign_attributions`. The customer campaign-attribution API
  projects persisted evidence; it does not create campaigns.
- `services/composite_code_service.py` calls both the campaign and referral
  validators. Composite validation remains a shared integration dependency; it
  is not proof of independently deployable services or arbitrary external
  campaign ingestion.
- Attribution-only customers therefore still need platform-governed campaign
  registration and current campaign evidence. The package does not grant the
  customer referral campaign-management UI or its write APIs. Existing platform
  administration/integration APIs retain their existing authentication and
  tenant controls. Package selection does not provision credentials.

Customer-scoped campaign/referral/programme commands and campaign-attribution
reads enforce the selected solution in addition to existing role, capability and
account checks. Sidebar, home destinations and module rendering use the same
commercial projection; attribution loads only the included evidence family.
Shared account setup, People & access, integrations, support and existing governed
reporting/export primitives remain shared. The package catalogue defines no new
report formats, quotas, service tiers, prices or billing authority.

Uncontracted accounts retain existing safe setup access. Legacy Standard/Enterprise
records are not silently converted: an operator must select an agreed solution
and record current approval. Unknown, expired or future-dated packages cannot
open packaged customer capabilities or clear the commercial gate. Shared setup
remains available to repair evidence.

Approval is explicitly an operator attestation. References come from the signed
order form, contract or internal approval record; no contract repository verifies
them automatically. `responsibleOwner` now stores the selected active Account
owner membership reference, not a free-text name. The resolver rechecks account,
tenant, membership role and permission on readback. Suspending that membership
blocks readiness and packaged customer API access. No duplicate people model or
new Commercial owner role is introduced.

Effective dates use inclusive UTC calendar dates. The commercial gate additionally
requires active account/reference/tenant foundations. The existing production
decision keeps account, people/access, integrations, registered campaign evidence
and freshness prerequisites; recording approval is not production activation.
For attribution-only the campaign prerequisite points to campaign evidence rather
than presenting customer campaign creation as a next action.

Writes lock the account in a transaction, replay account-scoped audit evidence,
reject changed payloads using the same key, validate the current owner and persist
one metadata update plus one audit event. Audit says evidence was recorded; it
does not claim that delayed evidence is already commercially ready. Internal
payload hashes are excluded from command responses. The UI reuses an idempotency
key for a retry of the same draft.

No contractual limits are configured. The Commercial screen says so explicitly;
existing service safety bounds (including the reporting export cap) remain
service controls and are not represented as purchased quotas.

Verification: focused service/API/package tests, frontend journey/navigation/API
client tests, lint and production build; `python -m
scripts.referral_saas_commercial_entitlement_check` verifies all packages against
local migrated PostgreSQL, audit replay and owner revocation, then rolls back all
created evidence. Desktop visual QA is unavailable because the browser-control
Node runtime exits before connecting; no visual-pass claim is made.
