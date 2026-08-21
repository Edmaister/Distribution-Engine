# Referral SaaS Operations Workspace E2E Verification

## Verification status

TASK-430 is **Complete (2026-08-21)**. The automated contract, permission, routing, state,
and accessibility evidence passes. Physical desktop, tablet, and mobile
inspection is recorded below and the responsive defects it exposed have been
corrected. Manual keyboard traversal and screen-reader spot checks were
confirmed on 2026-08-21.

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
| Responsive implementation | Physical inspection at 1440 x 900, 1024 x 768, and 390 x 844 exposed a tablet breakpoint and shell-overflow defect. The shared shell now collapses at 1100px, constrains itself to the viewport, presents navigation as a contained horizontal rail, and stacks session controls. | Pass after correction; screenshots recorded below |

## Physical responsive evidence

| Viewport | Evidence | Result |
| --- | --- | --- |
| Desktop, 1440 x 900 | `evidence/task-430/operations-desktop-1440x900.png` | Pass. Global navigation, session controls, connection state, and workspace loading/degraded posture remain legible without overlap. |
| Tablet, 1024 x 768 | `evidence/task-430/operations-tablet-1024x768.png` | Pass after correction. Navigation uses a contained horizontal rail and session controls stack within the viewport. |
| Mobile, 390 x 844 | `evidence/task-430/operations-mobile-390x844.png` | Pass after correction. The full vertical sidebar no longer consumes the first viewport; the page remains usable with compact navigation and stacked controls. |

The first physical run was not accepted: the 1024px layout retained the full
sidebar and clipped the session controls, while the 390px layout placed the
full sidebar above the page and widened the shell. The release evidence is
therefore tied to the shared-shell correction rather than a screenshot-only
sign-off.

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
   page overflow, clipped text, overlapping controls, or layout shifts.
   Completed for the Operations entry surface; evidence is recorded above.
6. Traverse each page using keyboard only. Confirm visible focus, logical order,
   named actions, and no keyboard trap. Confirmed on 2026-08-21.
7. Spot-check headings, landmarks, status text, and form labels with a screen
   reader. Confirmed on 2026-08-21.
8. Simulate an unavailable overview dependency and an empty filtered queue;
   confirm both states explain the problem and preserve a recovery path.

Manual keyboard traversal and screen-reader spot checks were confirmed on
2026-08-21. With the responsive screenshots and no-overflow checks recorded
above, TASK-430 moved to Complete on 2026-08-21.
