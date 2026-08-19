# Referral SaaS Operations Workspace E2E Verification

## Verification status

TASK-430 is **in progress**. The automated contract, permission, routing, state,
and accessibility evidence passes. Physical desktop/mobile screenshots,
keyboard traversal, screen-reader spot checks, and visual no-overflow checks
remain the final local release evidence.

Product boundary: Referral SaaS with Shared Platform verification. Shared
primitives remain single-source; this task adds no product fork, schema, API, or
page-specific domain state.

## Automated evidence

| Release concern | Evidence | Result |
| --- | --- | --- |
| Global operations summary | `ReferralSaasWorkspacePage.test.tsx` verifies authoritative metrics, persisted destinations, customer discovery, complete queue navigation, and a plain-language degraded state. | Pass |
| Queue triage | `ReferralSaasOperationsQueuePage.test.tsx` verifies URL-restorable filters, pagination, persisted source destinations, and filtered empty states. | Pass |
| Customer visibility | `ReferralSaasCustomerPortfolioPage.test.tsx` verifies labelled customer context, URL search, persisted customer destinations, and customer selection before Programme or Commercial Governance. | Pass |
| Cross-page journey | `ReferralSaasOperationsWorkspaceJourney.test.tsx` verifies Operations -> Customer portfolio -> governed Programme/Commercial destination transitions. | Pass |
| Accessibility contract | The cross-page journey checks named interactive elements, valid ARIA references, and prohibits positive `tabindex` values on every rendered surface. | Pass |
| Global/customer shell | `Sidebar.test.tsx` verifies global navigation outside customer context and customer-scoped navigation only after account selection. | Pass |
| Role and jurisdiction filtering | `test_referral_saas_operations_service.py` and operator API tests verify permission-filtered read models, identity-jurisdiction intersection, unsupported-filter rejection, and hidden-jurisdiction denial. | Pass |
| Cross-account and cross-jurisdiction negatives | Account resolver API tests reject mismatched account and jurisdiction identities and return explicit no-leakage evidence. | Pass |
| Responsive implementation | Operations and portfolio layouts have bounded desktop, tablet, and mobile CSS tracks; physical viewport inspection remains outstanding. | Automated structure present; physical evidence pending |

## Focused automated run

The frontend operations suite passes 17 tests across five files:

- `ReferralSaasWorkspacePage.test.tsx`
- `ReferralSaasOperationsQueuePage.test.tsx`
- `ReferralSaasCustomerPortfolioPage.test.tsx`
- `ReferralSaasOperationsWorkspaceJourney.test.tsx`
- `Sidebar.test.tsx`

## Final physical acceptance checklist

Run the local API and frontend with representative Amplifi operator data, then
record screenshots at desktop and mobile widths.

1. Open `/admin/referral-saas` and confirm the global shell, authoritative
   metrics, customer search, work queue, and operational-attention panel are
   understandable without selected-customer context.
2. Open the full queue; apply role-permitted jurisdiction and work-type filters;
   confirm the URL restores the same state after refresh.
3. Open Customer portfolio; confirm only permitted jurisdictions and customers
   appear and that customer identity fields are labelled.
4. Select Programme Governance and Commercial Governance; confirm each requires
   customer selection and opens the authoritative customer-scoped route.
5. Repeat at 1440 x 900, 1024 x 768, and 390 x 844. Confirm no horizontal
   overflow, clipped text, overlapping controls, or layout shifts.
6. Traverse each page using keyboard only. Confirm visible focus, logical order,
   named actions, and no keyboard trap.
7. Spot-check headings, landmarks, status text, and form labels with a screen
   reader.
8. Simulate an unavailable overview dependency and an empty filtered queue;
   confirm both states explain the problem and preserve a recovery path.

TASK-430 can move to Complete only after this physical evidence is attached or
recorded in this document.
