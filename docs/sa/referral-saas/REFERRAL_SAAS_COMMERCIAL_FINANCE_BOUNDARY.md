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

These fields are read-only posture and launch-gate evidence. They are not a
billing account, subscription, invoice, payment, payout, funding reservation, or
settlement instruction.

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

- H1 UI may show plan posture, launch blockers, and no-money boundaries.
- H1 UI must not show billing, invoice, funding, settlement, payout, wallet, or
  treasury actions as Referral SaaS product actions.
- H1 APIs must not expose Referral SaaS write routes for billing, invoices,
  funding, settlement, payouts, wallets, treasury, commissions, or money
  movement.
- The `/v1/referral-saas/accounts/{account_ref}/commercial-entitlement` response
  must return the commercial finance boundary as structured readback so frontend
  and support workflows can explain the separation plainly.
