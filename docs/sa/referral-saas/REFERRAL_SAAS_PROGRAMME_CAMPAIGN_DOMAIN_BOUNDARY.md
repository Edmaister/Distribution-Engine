# Referral SaaS Programme, Campaign, And Product Domain Boundary

Product boundary: Referral SaaS with Shared Platform trajectory.

Required boundary docs checked:

- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/referral-saas/ROADMAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`
- `docs/roadmap/ORDERED_TASK_LIST.md`

## Purpose

This document prevents execution drift after the configurable journey and
programme configuration work.

The current implementation has strong foundations for journey templates,
programme versions, campaign setup, campaign attribution, and runtime referral
binding. The remaining architecture gap is terminology and ownership: customer
product/offering, referral programme, campaign management, reward policy, and
journey runtime must not collapse into one overloaded configuration object.

## Domain Model

Use this model consistently:

```text
Customer account
  -> Customer product catalogue
    -> Product line
    -> Product offering
  -> Referral programme
    -> Approved journey version
    -> Default eligibility, terms, and incentive policy
    -> Allowed campaign override envelope
  -> Campaign
    -> Audience, channel, source, dates, creative, attribution settings
    -> Optional approved campaign-specific overrides
  -> Referral runtime
    -> Immutable effective rule snapshot
  -> Reporting and analytics
```

## Definitions

| Term | Meaning | Owner | Must not mean |
| --- | --- | --- | --- |
| Customer product line | A customer's business category, for example Transactional Banking, Insurance, Telco, Automotive, Retail, or Home Loans. | Customer admin or Amplifi Admin inside approved catalogue controls. | Amplifi SaaS package. |
| Customer product offering | A specific customer offer, for example Easy Account, Premier Account, Funeral Plan, Short-Term Insurance, Fibre Plan, or Vehicle Finance. | Customer admin or Amplifi Admin inside approved catalogue controls. | Referral programme, campaign, or journey template. |
| Amplifi service package | The commercial Referral SaaS module or bundle sold by Amplifi. | Amplifi. | The customer's real-world product. |
| Referral programme | A governed versioned referral business configuration for a customer/product/offering/market. | Customer admin and Amplifi Admin inside governance. | Campaign, campaign creative, channel plan, or source tracking. |
| Journey version | The milestone/transition/evidence model used by a programme. | Amplifi governed template plus customer-scoped published version. | Product/offering taxonomy or campaign plan. |
| Campaign | A time/channel/audience/source execution container that uses a published programme version. | Customer admin or Amplifi Admin. | Programme definition, journey model, or default reward engine. |
| Campaign override | A bounded campaign-specific variation, such as campaign-specific reward, dates, channel, cap, or attribution window. | Customer admin or Amplifi Admin only where the programme permits it. | Silent replacement of the programme or journey. |

## Required Separation

- `product_code` and `sub_product_code` must not be overloaded as the
  customer's real product line/offering unless a task explicitly migrates that
  meaning.
- Amplifi service packaging must remain separate from customer product
  taxonomy.
- Referral programme configuration must own default journey, eligibility,
  terms, and default incentive posture.
- Campaign management must own campaign audience, channel, source, schedule,
  attribution settings, lifecycle, and optional bounded overrides.
- A campaign may vary reward treatment only through explicit approved
  campaign-specific override controls.
- Runtime referrals must store the effective version snapshot they used so
  historical reporting and replay remain stable.

## Router And Service Direction

The current codebase already has separate service shapes:

- Programme configuration:
  `services/referral_saas_programme_configuration_service.py`
- Campaign management:
  `services/referral_saas_campaign_service.py`

The next tasks should make that separation clearer at the API and UX layer:

- Customer product catalogue APIs should be their own selected-customer product
  surface.
- Programme APIs should bind to customer product/offering references.
- Campaign APIs should bind to published programme versions and expose
  campaign-specific overrides separately.
- Legacy campaign journey-binding routes should be deprecated or wrapped so
  programme binding is the authoritative activation path.
- TASK-410 closes this boundary: campaign activation now derives journey
  context from the published programme version and legacy campaign
  journey-binding remains compatibility-only. It must not satisfy activation
  without a published programme binding.

## Build Parameters

Every task in this tranche must state:

- Product boundary: Referral SaaS, or Referral SaaS with Shared Platform
  trajectory.
- Required docs checked: this document, product brief, roadmap, gap matrix, and
  ordered task list.
- Source duplication: No.
- Service ownership: programme service, campaign service, product catalogue
  service, runtime resolver, reporting, or UX.
- No unsafe side effects: no provider dispatch, invite delivery, credentials,
  auth claim mutation, campaign activation unless explicitly scoped, billing,
  payout, settlement, funding, wallet, treasury, invoice, commission, sponsor
  billing, broad DLaaS marketplace behavior, or money movement.
- Tests: route/service/API/UI tests must prove the domain boundary, not just
  happy-path persistence.

## Success Criteria

This tranche is successful when:

- Customer product/offering is visible and stored separately from Amplifi SaaS
  package codes.
- Referral programmes can be configured against customer product/offering
  references.
- Campaigns are configured as separate execution plans bound to published
  programmes.
- Campaign-specific rewards or attribution differences are explicit approved
  overrides.
- Runtime referrals and reports can answer:
  - Which customer?
  - Which product/offering?
  - Which programme version?
  - Which campaign?
  - Which effective rules were used?
  - What was overridden and why?

