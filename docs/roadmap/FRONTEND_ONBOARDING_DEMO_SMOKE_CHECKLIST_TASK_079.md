# TASK-079 Frontend Onboarding Demo Smoke Checklist

Date: 2026-06-28

## Purpose

TASK-079 verifies that the frontend demo journey can be shown end to end without live writes, backend state mutation, secrets, webhook delivery, funding, fulfilment, settlement, retry, or money movement.

## Smoke Path

1. Operator demo home renders and links to setup, readiness, monitoring, and distributor-safe status surfaces.
2. Company / organisation onboarding renders with local shell fields and disabled account creation.
3. Producer / sponsor onboarding renders with local shell fields and disabled funding/sponsor actions.
4. Distributor onboarding renders with local shell fields and disabled lifecycle, route, and wallet actions.
5. User/member/role setup renders with local shell fields and disabled invite, role, and membership actions.
6. Campaign/opportunity setup renders with local shell fields and disabled save, publish, and link/code actions.
7. Webhook/API setup renders with local shell fields and disabled credential, secret, subscription, activation, and test-delivery actions.
8. Onboarding readiness checklist renders setup links, blockers, and disabled go-live review actions.
9. Distribution Command Centre operations renders with mocked read-only data and no guarded lifecycle/funding workflow submission.
10. Distributor portal operations renders distributor-safe status without `tenant_code`, provider payload, raw status, UCN, or settlement internals in the safe-status panel.

## Guardrails

- No backend routes were added.
- No schema or migrations were added.
- No database access, production data, or secrets are required.
- No create, update, activate, launch, publish, approve, settle, fund, fulfil, retry, deliver, credential, subscription, webhook, or money movement action is executed by the smoke path.
- `tenant_code` remains an internal platform identifier; the demo journey uses external references in user-facing onboarding screens.

## Validation Commands

Targeted smoke test:

```powershell
npm.cmd test -- OnboardingDemoJourneySmoke.test.tsx
```

Related frontend journey tests:

```powershell
npm.cmd test -- OperatorDemoHomePage.test.tsx CompanyOnboardingPage.test.tsx ProducerSponsorOnboardingPage.test.tsx DistributorOnboardingPage.test.tsx MemberRoleOnboardingPage.test.tsx CampaignOpportunitySetupPage.test.tsx WebhookApiSetupPage.test.tsx OnboardingReadinessChecklistPage.test.tsx DistributionCommandCentrePage.test.tsx DistributorPortalPage.test.tsx
```

Full frontend confidence checks:

```powershell
npm.cmd test
npm.cmd run build
npm.cmd run lint
```

## Known Blockers

- TASK-027 remains blocked pending approved safe read-only runtime database access.
- TASK-028 remains blocked until TASK-027 produces verified drift results or specific unknowns are explicitly deferred.
- This smoke proof is frontend-only and does not replace live environment verification.
