# Referral SaaS Programme Configuration Roadmap

Product boundary: Referral SaaS.

Required boundary docs checked:

- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/referral-saas/ROADMAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`
- `docs/roadmap/ORDERED_TASK_LIST.md`

## Purpose

TASK-383 through TASK-394 completed the governed customer journey
configuration spine for approved journey templates. The next maturity step is
not a larger free-form journey builder. It is a simple, governed programme
configuration model that lets a customer or Amplifi Admin manage one visible
business object:

```text
Referral programme
```

A programme binds the customer, market, journey version, campaign defaults,
approved incentive references, readiness posture, approval evidence, and
effective dates into one understandable versioned record.

## Target User Experience

The product should feel simple:

1. Choose the customer.
2. Open Programmes.
3. Create or copy a programme.
4. Pick an approved journey template.
5. Choose plain-language settings and approved incentives.
6. Validate the programme.
7. Submit for review.
8. Publish the version.
9. Create campaigns from that published programme.
10. Compare performance between versions.

The UI must not ask users to understand internal tenant codes, raw journey
payloads, provider secrets, payout mechanics, settlement, funding, billing,
auth claims, or DLaaS marketplace concepts.

## Target Architecture

The new control plane should introduce a versioned programme object above the
existing configurable journey layer:

```text
Programme draft
  -> Programme validation
  -> Programme review
  -> Published programme version
  -> Campaign binding
  -> Referral/runtime binding
  -> Analytics and historical replay
```

Each published programme version should bind:

- selected customer/account
- operating jurisdiction
- product and sub-product
- approved journey template version
- published customer journey version
- campaign defaults
- approved reward policy, mission, badge, and leaderboard references
- commercial entitlement/readiness posture
- integration readiness posture
- effective-from and effective-to dates
- approval evidence
- immutable configuration checksum

## Controls

- Customer-owned configuration is allowed only inside approved templates and
  approved catalogue references.
- Amplifi owns global templates, unsafe transition rules, catalogue approval,
  production activation policy, and environment gates.
- Drafts never affect live referrals.
- Validation and simulation must be side-effect-free.
- Publish creates immutable versions; edits create a new version.
- Campaigns bind to published programme versions, not loose drafts.
- New referrals bind to the applicable programme version for historical replay.
- Runtime fallback remains available until migration is proven in non-local
  environments.
- No provider dispatch, invite delivery, credential creation, auth-claim
  propagation, billing, funding, payout, settlement, invoice, wallet, treasury,
  or money movement is hidden inside programme setup.

## Task Tranche

TASK-396 through TASK-405 move the product from governed journey configuration
to a simple, governed programme configuration platform.

| Task | Outcome |
| --- | --- |
| TASK-396 | Define the simple programme configuration contract and ownership model. |
| TASK-397 | Add programme draft/version schema with immutable publish metadata. |
| TASK-398 | Add programme catalogue and draft read/save/validate APIs. |
| TASK-399 | Add programme validation and simulation over journey, incentives, campaign defaults, integrations, and entitlement posture. |
| TASK-400 | Add programme review, publish, retire, and rollback guardrails. |
| TASK-401 | Bind campaigns to published programme versions through customer-scoped create/update and activation gates. |
| TASK-402 | Completed: bind approved programme-scoped incentive and engagement references to published programme versions with effective-date, audit, idempotency, and no-side-effect guardrails. |
| TASK-403 | Completed: bind new referrals/runtime reads to published programme versions with historical replay posture and legacy fallback. |
| TASK-404 | Completed: add aggregate-only programme analytics and version comparison read models with guardrails, redactions, and no adjacent side effects. |
| TASK-405 | Add the simple customer Programme UX and end-to-end proof. |

## Post-Programme Domain Hardening Tranche

TASK-406 through TASK-414 close the remaining domain-modelling and CX gap
identified after the programme configuration review. The controlling artifact
is
`docs/sa/referral-saas/REFERRAL_SAAS_PROGRAMME_CAMPAIGN_DOMAIN_BOUNDARY.md`.

The purpose is not to add another configuration wizard. It is to make the
current programme and campaign platform commercially clear:

- customer product/offering taxonomy must be separate from Amplifi service
  packaging
- referral programme configuration must remain a different domain from
  campaign management
- campaigns must bind to published programme versions
- campaign reward or attribution differences must be explicit approved
  overrides
- runtime referrals and analytics must preserve customer, product/offering,
  programme, campaign, and effective-rule evidence

| Task | Outcome |
| --- | --- |
| TASK-406 | Lock the programme, campaign, product/offering, and override domain contract. |
| TASK-407 | Add customer product/offering catalogue schema and migration tests. |
| TASK-408 | Add selected-customer product/offering catalogue APIs and safe read models. |
| TASK-409 | Bind programme drafts and versions to customer product/offering references without overloading Amplifi package codes. |
| TASK-410 | Deprecate or wrap campaign journey-binding so programme binding is the authoritative campaign activation path. |
| TASK-411 | Add campaign-specific override contract, schema/API, and validation for reward, attribution, channel, cap, and date overrides. |
| TASK-412 | Add effective-rule runtime resolver snapshots across programme defaults and campaign overrides. |
| TASK-413 | Add reporting/analytics dimensions for customer product/offering, programme version, campaign, and override posture. |
| TASK-414 | Add simple customer-scoped UX for product catalogue, programme-to-product binding, campaign override review, and proof. |

## Definition Of Done

This tranche is complete when a selected customer can configure a referral
programme from approved building blocks, validate it, publish an immutable
version, create/bind campaigns from it, generate referrals against it, and
compare outcomes between versions without source-code changes or unsafe
adjacent side effects.

The post-programme hardening tranche is complete when the same flow also
answers, in plain language, which customer product/offering the programme is
for, which campaign used it, which overrides were approved, and which effective
rules were frozen for every new referral.
