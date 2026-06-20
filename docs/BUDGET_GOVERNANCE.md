# Budget Governance

Budget governance is Phase 11.6. It controls approved changes to sponsor
funding contract budgets after a contract is already live.

## Current Capability

The platform now supports the first budget governance slice:

- Budget increase request creation
- Budget transfer request creation
- Budget exception creation
- Budget approval policy creation
- Pending request listing
- Approval policy listing
- Approval policy evaluation by tenant, sponsor, request type, and amount
- Request approval
- Request rejection
- Exception resolution
- Exception waiver
- Approved increase application to the funding contract
- Approved transfer application between funding contracts
- Contract ledger entry for approved budget increases
- Contract ledger entries for approved budget transfers

## Data Model

Primary table:

- `funding_budget_adjustment_requests`
- `funding_budget_transfer_requests`
- `funding_budget_exceptions`
- `funding_budget_approval_policies`

Approved increases also write to:

- `funding_contracts`
- `funding_contract_ledger`

The request tables track request lifecycle. The contract ledger records the
financial impact once a request is approved.

The exception table tracks overspend, policy-breach, or manual-review items that
need operational decisioning. Exceptions can be resolved when corrected or waived
when accepted by governance.

The approval policy table defines which approval level or role is required for a
budget request based on tenant, optional sponsor, request type, and amount band.

## Admin API

Create a budget adjustment request:

```text
POST /admin/funding/budget-governance/requests
```

List budget adjustment requests:

```text
GET /admin/funding/budget-governance/requests
```

Approve a request:

```text
POST /admin/funding/budget-governance/requests/{request_id}/approve
```

Reject a request:

```text
POST /admin/funding/budget-governance/requests/{request_id}/reject
```

Create a budget transfer request:

```text
POST /admin/funding/budget-governance/transfer-requests
```

List budget transfer requests:

```text
GET /admin/funding/budget-governance/transfer-requests
```

Approve a transfer request:

```text
POST /admin/funding/budget-governance/transfer-requests/{request_id}/approve
```

Reject a transfer request:

```text
POST /admin/funding/budget-governance/transfer-requests/{request_id}/reject
```

Create a budget exception:

```text
POST /admin/funding/budget-governance/exceptions
```

List budget exceptions:

```text
GET /admin/funding/budget-governance/exceptions
```

Resolve a budget exception:

```text
POST /admin/funding/budget-governance/exceptions/{exception_id}/resolve
```

Waive a budget exception:

```text
POST /admin/funding/budget-governance/exceptions/{exception_id}/waive
```

Create an approval policy:

```text
POST /admin/funding/budget-governance/approval-policies
```

List approval policies:

```text
GET /admin/funding/budget-governance/approval-policies
```

Evaluate an approval policy:

```text
POST /admin/funding/budget-governance/approval-policies/evaluate
```

## Approval Flow

```text
Budget increase requested
  -> Request stored as PENDING
  -> Finance/admin approves
  -> Contract value increases
  -> Contract remaining amount increases
  -> BUDGET_INCREASE_APPROVED ledger entry is written
```

## Transfer Flow

```text
Budget transfer requested
  -> Request stored as PENDING
  -> Finance/admin approves
  -> Source contract value and remaining amount decrease
  -> Target contract value and remaining amount increase
  -> BUDGET_TRANSFER_OUT_APPROVED ledger entry is written on source
  -> BUDGET_TRANSFER_IN_APPROVED ledger entry is written on target
```

## Exception Flow

```text
Budget exception detected
  -> Exception stored as OPEN
  -> Ops/finance reviews
  -> Exception is RESOLVED when corrected
  -> Or exception is WAIVED when accepted under governance
```

## Approval Policy Flow

```text
Budget request details supplied
  -> Tenant, sponsor, request type, and amount are evaluated
  -> Most specific matching ACTIVE policy is selected
  -> Required approval level and role are returned
  -> Finance/admin applies the decision using the normal approval endpoint
```

## Remaining Work

Remaining Phase 11.6 work:

- Budget decrease requests
- Optional sponsor-facing request submission
