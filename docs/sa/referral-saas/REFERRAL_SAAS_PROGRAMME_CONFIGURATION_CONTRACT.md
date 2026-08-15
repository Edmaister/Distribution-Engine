# Referral SaaS Programme Configuration Contract

Product boundary: Referral SaaS.

Task: TASK-396.

Required boundary docs checked:

- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/referral-saas/ROADMAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_PROGRAMME_CONFIGURATION_ROADMAP.md`

## Purpose

This contract defines the customer/admin-facing `Referral programme`
configuration object.

The programme is the simple business object that sits above the existing
governed journey configuration spine. It lets a customer or Amplifi Admin
configure referral management and campaign attribution in one place without
editing raw journey-engine tables, seed files, reward engines, provider
payloads, auth claims, billing, settlement, or money flows.

## Plain-Language Product Model

The UI and API should use this mental model:

```text
Customer
  -> Programme
    -> Version
      -> Campaigns
        -> Referrals and outcomes
```

For users, a programme answers five questions:

1. What customer and market is this for?
2. What referral journey should this programme use?
3. What campaign defaults and approved incentives apply?
4. Is this safe to publish and use?
5. Which campaigns and referrals used this version?

The product must not make customers reason about internal `tenant_code`,
source-code journey definitions, raw event schemas, provider adapters, vault
references, identity-provider claims, payout mechanics, settlement, funding,
billing, or DLaaS marketplace concepts.

## Ownership Model

| Configuration area | Customer admin | Amplifi Admin | Engineering/platform |
| --- | --- | --- | --- |
| Create a programme draft from approved options | Yes | Yes | No |
| Copy an existing programme version into a new draft | Yes, for their customer | Yes | No |
| Edit programme display name and description | Yes | Yes | No |
| Select operating jurisdiction from allowed account jurisdictions | Yes | Yes | No |
| Select product/sub-product within the Referral SaaS entitlement | Yes | Yes | No |
| Select approved journey template/version | Yes, from approved catalogue | Yes | No |
| Select published customer journey version | Yes, where compatible | Yes | No |
| Set campaign defaults within approved ranges | Yes | Yes | No |
| Select approved reward policy, mission, badge, and leaderboard references | Yes, where entitled | Yes | No |
| Submit for review | Yes | Yes | No |
| Approve or block review | No, unless policy allows SoD role | Yes | No |
| Publish, retire, or rollback a programme version | No, unless explicitly entitled | Yes | No |
| Define a new global journey type | No | Governance request only | Yes |
| Define new milestones, transitions, evidence models, or runtime engines | No | Governance request only | Yes |
| Define new reward calculation engines | No | Governance request only | Yes |
| Configure provider secrets, credentials, auth claims, billing, payout, settlement, or money movement | No | Separate governed workflow | Separate governed workflow |

## Programme Object Contract

A programme draft or published version is account-scoped and must carry enough
metadata to explain its business meaning without leaking internal identifiers.

### Required Business Fields

| Field | Meaning | Control |
| --- | --- | --- |
| `programme_name` | Customer-visible name, such as `Home Loans Referral Programme`. | Required, bounded length, customer-safe text. |
| `programme_description` | Short explanation of the programme's purpose. | Optional, customer-safe text. |
| `account_id` | Durable selected customer account. | Server resolved; not customer editable as raw id. |
| `operating_jurisdiction_code` | Market where the programme operates. | Must match the selected account's allowed jurisdictions. |
| `product_code` | Product boundary, initially Referral SaaS. | Must remain in approved product catalogue. |
| `sub_product_code` | Sub-product/package, such as referral management or campaign attribution bundle. | Must match entitlement and approved catalogue. |
| `programme_status` | Draft/review/published/retired/rollback posture. | Server controlled. |
| `effective_from` | First date this version can be used. | Must pass validation and activation windows. |
| `effective_to` | Optional last date this version can be used. | Must be after `effective_from`. |

### Required Configuration Bindings

| Binding | Meaning | Control |
| --- | --- | --- |
| `journey_template_version_ref` | Approved global journey template version. | Approved templates only. |
| `customer_journey_version_ref` | Published customer journey version generated from the approved template. | Published, same account, compatible status only. |
| `campaign_defaults_ref` or inline defaults | Default campaign settings such as attribution window, allowed channels, and launch posture. | Bounded fields only; no activation side effect. |
| `reward_policy_version_ref` | Approved reward policy reference where incentives are enabled. | Approved catalogue only; no payout or reward application. |
| `mission_definition_version_refs` | Optional approved mission definitions. | Approved catalogue only; no mission progress mutation. |
| `badge_definition_version_refs` | Optional approved badge definitions. | Approved catalogue only; no badge award mutation. |
| `leaderboard_definition_version_refs` | Optional approved leaderboard definitions. | Approved catalogue only; no scoring mutation. |
| `integration_readiness_ref` | Snapshot of integration readiness used during validation/publish. | Read-only evidence; no provider dispatch. |
| `commercial_entitlement_ref` | Snapshot of entitled features/limits used during validation/publish. | Read-only evidence; no billing or money movement. |

### Required Governance Fields

| Field | Meaning | Control |
| --- | --- | --- |
| `draft_version` | Monotonic draft revision number. | Server controlled. |
| `published_version` | Immutable published programme version number. | Server controlled. |
| `configuration_checksum` | Hash of the canonical approved configuration snapshot. | Required for published versions. |
| `validation_result_ref` | Latest side-effect-free validation evidence. | Required before publish. |
| `review_status` | Review state and decision posture. | Server controlled. |
| `reviewed_by`, `reviewed_at`, `review_reason` | Human approval/block evidence. | Required when review is required. |
| `published_by`, `published_at` | Publish evidence. | Required for published versions. |
| `retired_by`, `retired_at`, `retirement_reason` | Retirement evidence. | Required for retired versions. |
| `rollback_from_version_ref` | Optional rollback lineage. | Explicit rollback only. |
| `idempotency_key_hash` | Write replay guard. | Required for write commands. |
| `payload_hash` | Conflicting replay detection. | Required for write commands. |
| `audit_ref` | Audit evidence anchor. | Required for write commands. |

## Lifecycle Contract

| State | User meaning | Allowed next actions |
| --- | --- | --- |
| `DRAFT` | The programme is being configured and has no live effect. | Edit, validate, submit for review, discard. |
| `VALIDATION_FAILED` | The draft has blockers. | Fix draft, validate again. |
| `VALIDATED` | The draft is structurally safe but not approved or published. | Submit for review or publish if policy allows. |
| `READY_FOR_REVIEW` | The draft is waiting for approval. | Approve, block, request changes. |
| `APPROVED_FOR_PUBLISH` | Review passed and publish is allowed. | Publish or request changes. |
| `PUBLISHED` | This immutable version can be used by campaigns. | Bind campaign, copy to new draft, retire if safe. |
| `RETIRED` | This version can no longer be selected for new campaigns. | Read, compare, rollback request where allowed. |
| `ROLLBACK_READY` | A previous safe version can be restored as the active selection. | Publish rollback version through explicit command. |
| `BLOCKED` | Governance, entitlement, validation, or safety gates block progress. | Resolve blocker or create a new draft. |

Edits to a published programme must create a new draft/version. Published
versions are immutable.

## Command Boundary

Future programme commands must be customer/account scoped and idempotent:

| Command | Purpose | Side effects allowed |
| --- | --- | --- |
| `create_programme_draft` | Start a programme from approved defaults or a copied version. | Draft rows, audit only. |
| `save_programme_draft` | Persist safe configuration intent. | Draft rows, validation stale marker, audit only. |
| `validate_programme_draft` | Prove the draft can progress. | Validation evidence and audit only. |
| `submit_programme_review` | Move a valid draft to human review. | Review status and audit only. |
| `record_programme_review_decision` | Approve, block, or request changes. | Review evidence and audit only. |
| `publish_programme_version` | Create immutable version available for campaign binding. | Published programme version and audit only. |
| `retire_programme_version` | Stop new campaign use of a version. | Lifecycle status and audit only. |
| `prepare_programme_rollback` | Validate rollback posture. | Rollback readiness evidence and audit only. |

No command may send invites, dispatch providers, create credentials, assign
seats, mutate auth claims, activate campaigns, create referrals, apply rewards,
award badges, score leaderboards, generate invoices, reserve funds, settle
payouts, or move money.

## Validation Contract

Programme validation must be deterministic and side-effect-free.

Validation should return:

- `overall_status`: `READY`, `NEEDS_ATTENTION`, or `BLOCKED`.
- `publish_allowed`: boolean.
- `campaign_binding_allowed`: boolean.
- `plain_language_summary`: a short user-facing explanation.
- `blockers`: ordered list with owner, reason, fixing action, and target page.
- `warnings`: items that can wait but should be visible before launch.
- `configuration_snapshot`: redacted, canonical summary used for checksum.
- `guardrails`: explicit no-provider/no-auth/no-billing/no-money posture.

Validation must check:

- selected account exists and matches the actor scope
- operating jurisdiction is allowed
- product/sub-product is entitled
- journey template version is approved
- customer journey version is published, same-account, and compatible
- campaign defaults are inside approved ranges
- incentive/mission/badge/leaderboard references are approved and compatible
- integration readiness is fresh enough for the intended launch posture
- commercial entitlement allows the requested programme features
- effective dates are valid
- no unsafe raw identifiers, secrets, provider payloads, auth claims, billing,
  settlement, payout, wallet, treasury, invoice, or money fields are present

## API Shape

TASK-396 is contract-only. Future API routes should follow the selected-customer
route pattern and avoid unscoped global customer access:

```text
GET  /v1/referral-saas/accounts/{account_id}/programmes
GET  /v1/referral-saas/accounts/{account_id}/programmes/catalogue
GET  /v1/referral-saas/accounts/{account_id}/programmes/drafts/{draft_id}
POST /v1/referral-saas/accounts/{account_id}/programmes/drafts
PUT  /v1/referral-saas/accounts/{account_id}/programmes/drafts/{draft_id}
POST /v1/referral-saas/accounts/{account_id}/programmes/drafts/{draft_id}/validate
POST /v1/referral-saas/accounts/{account_id}/programmes/drafts/{draft_id}/submit-review
POST /v1/referral-saas/accounts/{account_id}/programmes/drafts/{draft_id}/review-decision
POST /v1/referral-saas/accounts/{account_id}/programmes/drafts/{draft_id}/publish
POST /v1/referral-saas/accounts/{account_id}/programmes/versions/{version_id}/retire
GET  /v1/referral-saas/accounts/{account_id}/programmes/versions/{version_id}/analytics
```

The exact route set may be refined in TASK-398 through TASK-404, but every
write route must preserve account scope, capability checks, idempotency,
payload hashing, audit evidence, and redaction.

## Frontend Contract

The target UX should expose one simple customer-scoped workspace:

```text
Customer profile
  -> Programmes
    -> Programme list
    -> Create or copy programme
    -> Configure
    -> Validate
    -> Review and publish
    -> Campaigns using this version
    -> Version comparison
```

The screen should answer:

- What programme am I configuring?
- Which customer and market is it for?
- Is it a draft, published version, or retired version?
- What is blocking publish?
- What can wait?
- What is the next safe action?
- Which campaigns use this programme version?
- What changed between versions?

The default user view should not show raw JSON, internal identifiers, hashes,
provider/vault references, auth claims, billing fields, or money evidence.
Diagnostics may exist behind an Amplifi Admin disclosure.

## Redaction And Boundary Rules

Customer-facing responses must not expose:

- internal `tenant_code`
- raw UCN or raw identity payloads
- raw event payloads or source payload hashes
- raw journey definition JSON unless behind governed admin diagnostics
- provider payloads, secrets, vault paths, keys, signing material, or tokens
- auth claims, identity-provider payloads, session details, or credential data
- reward payout amounts where money movement is not in scope
- invoice, billing, funding, settlement, wallet, treasury, commission, or money
  movement data

Safe labels may include:

- customer display name
- operating jurisdiction
- external customer/organisation references
- account code
- programme name
- programme status
- version number
- approved template name
- safe readiness status
- campaign count and aggregate outcome metrics

## Success Criteria For TASK-396

TASK-396 is complete when:

- The programme contract defines the user-facing model and governance model.
- Allowed customer/admin configuration is separated from Amplifi/engineering
  governance.
- Required fields, lifecycle states, command boundaries, validation rules,
  redactions, idempotency, audit, and side-effect boundaries are explicit.
- The next implementation tasks can add schema, APIs, runtime binding, and UX
  without debating what the programme object means.

