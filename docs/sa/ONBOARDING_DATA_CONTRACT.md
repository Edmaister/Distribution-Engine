# Onboarding Data Contract

Status: Accepted for TASK-081 on 2026-06-28.

## Purpose

This document defines the canonical frontend-to-backend data contract for the DLaaS onboarding journey created in TASK-070 through TASK-079.

It consolidates the completed frontend shell fields into stable contract language for:

- company / organisation onboarding;
- producer / sponsor onboarding;
- distributor onboarding;
- member / invite / role onboarding;
- campaign / opportunity setup;
- webhook / API setup;
- onboarding readiness checklist;
- future read-only onboarding state projection.

This is a contract document only. It does not add schema, routes, services, persistence, draft-save behavior, account creation, invite delivery, credential generation, webhook delivery, campaign publication, funding, wallet movement, fulfilment, settlement, retry, go-live activation, or money movement.

## Source Documents

- `docs/sa/TENANT_IDENTIFIER_BOUNDARY_DECISION.md`
- `docs/sa/TENANT_ACCOUNT_BOUNDARY_MAP.md`
- `docs/sa/TENANT_ACCOUNT_LIFECYCLE_MEMBERSHIP_MODEL.md`
- `docs/sa/PARTICIPANT_TAXONOMY_PERMISSION_MAP.md`
- `docs/API_PERMISSION_MATRIX.md`
- `docs/product/DLAAS_TARGET_STATE.md`
- `docs/roadmap/FRONTEND_ONBOARDING_WAVE_CHECKPOINT_TASK_080.md`
- `docs/roadmap/FRONTEND_ONBOARDING_DEMO_SMOKE_CHECKLIST_TASK_079.md`
- completed frontend shells under `frontend/src/pages/admin/`

## Contract Principles

1. `tenant_code` remains internal.
2. User-facing onboarding references use external identifiers.
3. Every future service must separate shell/draft state from persisted platform truth.
4. Read-only projection must surface missing evidence instead of pretending unavailable backend support exists.
5. No onboarding field in this contract authorizes live mutation by itself.
6. Secrets, credentials, raw provider details, raw UCNs, settlement internals, and internal audit payloads must not be exposed externally.
7. Funding, wallet, fulfilment, settlement, retry, webhook delivery, and money movement remain out of scope until separately authorized tasks implement and test them.

## Identifier Boundary

### User-Facing References

These references may appear in onboarding screens, future public/partner contracts, webhook setup, and tenant-facing setup experiences:

| Reference | Purpose | Contract rule |
| --- | --- | --- |
| `external_tenant_ref` | Generic SaaS-facing tenant/account reference. | Preferred external tenant reference for onboarding and integration setup. |
| `organisation_ref` | External organisation reference. | Identifies the organisation setup boundary. |
| `producer_ref` | External producer reference. | Identifies producer-side ownership or setup intent. |
| `sponsor_ref` | External sponsor reference. | Identifies sponsor/funding owner intent without creating money records. |
| `distributor_ref` | External distributor reference. | Identifies distributor setup intent without creating distributor records. |
| `opportunity_ref` | External opportunity/setup reference. | Identifies campaign opportunity setup intent without publication. |
| `campaign_code` | Campaign setup or diagnostic code. | May be user-facing when used as campaign setup or diagnostic reference. |

### Internal Identifiers

`tenant_code` is the internal runtime partition and data-isolation identifier. It may be used by internal services, admin/operator routes, audit, funding, fulfilment, settlement, reporting, and workers after identity resolution. It must not be the primary user-facing onboarding identifier.

Future read-only services may include resolved internal tenant scope only for authorized operator/admin responses. External, partner, distributor, producer, or customer-facing responses should use external references or omit internal tenant scope.

## Common Envelope

Future read-only onboarding projection should use a common envelope:

```json
{
  "contract_version": "onboarding.v1",
  "scope": {
    "external_tenant_ref": "acme-distribution",
    "organisation_ref": "org-acme",
    "resolved_tenant": {
      "status": "UNAVAILABLE",
      "tenant_code": null
    }
  },
  "sections": {},
  "readiness": {},
  "missing_evidence": [],
  "redactions": [],
  "guardrails": [],
  "source_warnings": []
}
```

`resolved_tenant.tenant_code` is nullable and internal/operator-only. If tenant resolution is unavailable, the response must say so through `missing_evidence` or `source_warnings`; it must not fabricate a tenant.

## Safe Status Values

Onboarding readiness and shell state should use these safe display statuses:

| Status | Display label | Meaning |
| --- | --- | --- |
| `NOT_STARTED` | Not started | Required setup intent or evidence is absent. |
| `DRAFT` | Draft | Local/shell state exists but is not persisted or verified. |
| `IN_PROGRESS` | In progress | Some setup fields or evidence are present. |
| `READY` | Ready | Required evidence for the section is present for read-only review. |
| `BLOCKED` | Blocked | A known blocker prevents readiness. |
| `UNAVAILABLE` | Unavailable | Backend/source evidence is not implemented or not returned. |
| `REVIEW_ONLY` | Review only | Information is visible but no live command is available. |

These values are safe display categories, not lifecycle commands.

## Missing Evidence Shape

Future read-only projection should expose missing evidence in a bounded shape:

```json
{
  "section": "campaign_opportunity",
  "code": "NO_BACKEND_SOURCE",
  "severity": "INFO",
  "message": "Campaign setup is currently shell-only."
}
```

Allowed severities: `INFO`, `WARNING`, `BLOCKER`.

Recommended codes:

- `NO_BACKEND_SOURCE`
- `NO_PERSISTED_DRAFT`
- `NO_RESOLVED_TENANT`
- `NO_MEMBERSHIP_SOURCE`
- `NO_CREDENTIAL_SOURCE`
- `NO_CAMPAIGN_SOURCE`
- `NO_READINESS_SOURCE`
- `LIVE_DB_VERIFICATION_BLOCKED`
- `DRIFT_VERIFICATION_BLOCKED`

## Company / Organisation Onboarding State

Canonical shape:

```json
{
  "organisation_name": "",
  "external_tenant_ref": "",
  "organisation_ref": "",
  "country": "",
  "organisation_type": "",
  "industry": "",
  "admin_contact": "",
  "intended_role": ""
}
```

Frontend shell source: `CompanyOnboardingPage.tsx`.

Field mapping:

| Shell field | Contract field | Notes |
| --- | --- | --- |
| Organisation name | `organisation_name` | Display/setup name only. |
| `external_tenant_ref` | `external_tenant_ref` | User-facing tenant/account reference. |
| `organisation_ref` | `organisation_ref` | User-facing organisation reference. |
| Country | `country` | Setup country/market. |
| Organisation type | `organisation_type` | Classification intent, not persisted account type. |
| Industry | `industry` | Setup metadata. |
| Admin contact | `admin_contact` | Contact placeholder; do not treat as delivered invite. |
| Intended role | `intended_role` | Role intent only; no membership or auth change. |

Non-live actions: account creation, tenant creation, membership creation, billing setup, and external-reference resolver behavior.

## Producer / Sponsor Onboarding State

Canonical shape:

```json
{
  "producer_sponsor_name": "",
  "external_tenant_ref": "",
  "producer_ref": "",
  "sponsor_ref": "",
  "organisation_ref": "",
  "industry": "",
  "funding_model_intention": "",
  "admin_contact": "",
  "campaign_opportunity_role": ""
}
```

Frontend shell source: `ProducerSponsorOnboardingPage.tsx`.

Field mapping:

| Shell field | Contract field | Notes |
| --- | --- | --- |
| Producer / sponsor name | `producer_sponsor_name` | Display/setup name. |
| `external_tenant_ref` | `external_tenant_ref` | User-facing tenant/account reference. |
| `producer_ref` | `producer_ref` | User-facing producer reference. |
| `sponsor_ref` | `sponsor_ref` | User-facing sponsor reference. |
| `organisation_ref` | `organisation_ref` | Parent organisation reference. |
| Industry / vertical | `industry` | Setup metadata. |
| Funding model intention | `funding_model_intention` | Intent only; no funding state. |
| Producer admin contact | `admin_contact` | Contact placeholder. |
| Campaign / opportunity role | `campaign_opportunity_role` | Ownership/setup intent. |

Non-live actions: sponsor creation, sponsor wallet creation, funding contracts, invoices, budget reservations, rewards, fulfilment, settlement, billing mutation, and money movement.

## Distributor Onboarding State

Canonical shape:

```json
{
  "distributor_name": "",
  "external_tenant_ref": "",
  "distributor_ref": "",
  "organisation_ref": "",
  "channel_type": "",
  "market_country": "",
  "admin_contact": "",
  "distribution_model": "",
  "campaign_opportunity_participation": ""
}
```

Frontend shell source: `DistributorOnboardingPage.tsx`.

Field mapping:

| Shell field | Contract field | Notes |
| --- | --- | --- |
| Distributor name | `distributor_name` | Display/setup name. |
| `external_tenant_ref` | `external_tenant_ref` | User-facing tenant/account reference. |
| `distributor_ref` | `distributor_ref` | User-facing distributor reference. |
| `organisation_ref` | `organisation_ref` | Parent organisation reference. |
| Channel type | `channel_type` | Partner/distributor channel classification. |
| Market / country | `market_country` | Setup market. |
| Distributor admin contact | `admin_contact` | Contact placeholder. |
| Distribution model | `distribution_model` | Route/link/channel intent only. |
| Campaign / opportunity participation | `campaign_opportunity_participation` | Participation intent only. |

Non-live actions: distributor creation, activation, suspension, termination, route activation, wallet creation, offer decision, commission, payout, fulfilment, settlement, retry, and money movement.

## Member / Invite / Role Onboarding State

Canonical shape:

```json
{
  "organisation_ref": "",
  "external_tenant_ref": "",
  "user_email": "",
  "display_name": "",
  "role_family": "",
  "participant_type": "",
  "access_scope": "",
  "invite_status": ""
}
```

Frontend shell source: `MemberRoleOnboardingPage.tsx`.

Field mapping:

| Shell field | Contract field | Notes |
| --- | --- | --- |
| `organisation_ref` | `organisation_ref` | User-facing organisation reference. |
| `external_tenant_ref` | `external_tenant_ref` | User-facing tenant/account reference. |
| User email | `user_email` | Draft contact value; do not deliver invite. |
| Display name | `display_name` | Display/setup value. |
| Role family | `role_family` | Role intent aligned to permission matrix families. |
| Participant type | `participant_type` | Target participant family. |
| Access scope | `access_scope` | Requested scope intent only. |
| Invite status | `invite_status` | Draft state label only. |

Non-live actions: user creation, invite delivery, identity-provider registration, membership creation, seat assignment, role assignment, auth claim changes, and permission changes.

## Campaign / Opportunity Setup State

Canonical shape:

```json
{
  "organisation_ref": "",
  "producer_ref": "",
  "sponsor_ref": "",
  "campaign_code": "",
  "opportunity_ref": "",
  "campaign_name": "",
  "market_country": "",
  "distribution_model": "",
  "eligible_distributor_type": "",
  "intended_outcome_event": "",
  "reward_commission_policy_intention": "",
  "funding_model_intention": "",
  "go_live_target_status": "",
  "link_code_intent": ""
}
```

Frontend shell source: `CampaignOpportunitySetupPage.tsx`.

Field mapping:

| Shell field | Contract field | Notes |
| --- | --- | --- |
| `organisation_ref` | `organisation_ref` | User-facing organisation reference. |
| `producer_ref / sponsor_ref` | `producer_ref`, `sponsor_ref` | Split contract fields; shell may capture either/both in one control. |
| `campaign_code` | `campaign_code` | User-facing campaign setup/diagnostic code. |
| `opportunity_ref` | `opportunity_ref` | User-facing opportunity setup reference. |
| Campaign name | `campaign_name` | Display/setup name. |
| Market / country | `market_country` | Setup market. |
| Channel / distribution model | `distribution_model` | Distribution intent only. |
| Eligible distributor type | `eligible_distributor_type` | Eligibility intent only. |
| Intended outcome event | `intended_outcome_event` | Event intent only. |
| Reward / commission policy intention | `reward_commission_policy_intention` | Policy intent only. |
| Funding model intention | `funding_model_intention` | Funding intent only. |
| Go-live target / status | `go_live_target_status` | Review label only. |
| Link/code intent | `link_code_intent` | Link/code setup intent only. |

Non-live actions: campaign creation, opportunity publication, launch, pause, close, route generation, link/code issuance, reward policy writes, funding reservation, fulfilment, settlement, retry, and money movement.

## Webhook / API Setup State

Canonical shape:

```json
{
  "organisation_ref": "",
  "external_tenant_ref": "",
  "integration_owner_contact": "",
  "api_environment_intention": "",
  "callback_url_placeholder": "",
  "selected_webhook_event_categories": [],
  "intended_authentication_method": "",
  "ip_allowlist_notes": "",
  "payload_format_version": "",
  "go_live_readiness_status": ""
}
```

Frontend shell source: `WebhookApiSetupPage.tsx`.

Field mapping:

| Shell field | Contract field | Notes |
| --- | --- | --- |
| `organisation_ref` | `organisation_ref` | User-facing organisation reference. |
| `external_tenant_ref` | `external_tenant_ref` | User-facing tenant/account reference. |
| Integration owner / contact | `integration_owner_contact` | Contact placeholder. |
| API environment intention | `api_environment_intention` | Sandbox/live intent only. |
| Callback URL placeholder | `callback_url_placeholder` | Placeholder only; no registration/validation. |
| Webhook event categories | `selected_webhook_event_categories` | Catalog category intent. |
| Intended authentication method | `intended_authentication_method` | Auth method intent only. |
| IP allowlist notes | `ip_allowlist_notes` | Notes only. |
| Payload format / version | `payload_format_version` | Preview format selection. |
| Go-live readiness status | `go_live_readiness_status` | Review label only. |

Non-live actions: API key creation, secret generation, secret rotation, token/certificate creation, callback registration, URL validation, webhook subscription, signing, queueing, retry, replay, delivery, persistence, and credential storage.

## Readiness Checklist State

Canonical shape:

```json
{
  "items": [
    {
      "category": "ORGANISATION_PROFILE",
      "status": "READY",
      "path": "/admin/onboarding/company",
      "evidence": "",
      "blockers": [],
      "next_actions": []
    }
  ],
  "summary": {
    "ready_count": 0,
    "blocked_count": 0,
    "total_count": 0
  }
}
```

Frontend shell source: `OnboardingReadinessChecklistPage.tsx`.

Canonical categories:

| Category | Current label |
| --- | --- |
| `ORGANISATION_PROFILE` | Organisation profile |
| `PRODUCER_SPONSOR_SETUP` | Producer / sponsor setup |
| `DISTRIBUTOR_SETUP` | Distributor setup |
| `MEMBERS_AND_ROLES` | Members and roles |
| `CAMPAIGN_OPPORTUNITY_SETUP` | Campaign / opportunity setup |
| `WEBHOOK_API_SETUP` | Webhook / API setup |
| `SECURITY_AND_PERMISSIONS` | Security and permissions |
| `GO_LIVE_CONTROLS` | Go-live controls |

Readiness status must use the safe status values in this document. Go-live control readiness must remain blocked or review-only until separate tasks implement and validate live activation.

## Fields That Must Not Be Exposed Externally

The following must not be exposed in external onboarding, partner, distributor, customer, webhook, or public responses unless a later task explicitly defines a safe operator-only contract:

- internal `tenant_code` as the primary external identifier;
- raw UCNs or private customer identifiers;
- raw provider payloads;
- raw settlement internals;
- raw audit payloads;
- worker secrets;
- API keys;
- client secrets;
- signing secrets;
- access tokens or refresh tokens;
- passwords or certificates;
- database DSNs or environment secret names;
- internal wallet/account numbers not explicitly safe for display;
- stack traces, SQL errors, or unrestricted exception details.

## Guardrails

This contract does not enable:

- secrets or API credentials;
- webhook subscription, signing, queueing, retry, replay, or delivery;
- account, tenant, company, producer, sponsor, distributor, user, member, invite, role, campaign, opportunity, wallet, funding, fulfilment, settlement, retry, or money records;
- account creation, invite delivery, campaign publication, go-live activation, funding reservation, wallet movement, fulfilment, settlement, payout, reversal, or money movement.

## Future Read-Only Projection Shape

TASK-082 and TASK-083 should project read-only onboarding state into this shape:

```json
{
  "contract_version": "onboarding.v1",
  "generated_at": "2026-06-28T00:00:00Z",
  "scope": {
    "external_tenant_ref": "",
    "organisation_ref": "",
    "producer_ref": "",
    "sponsor_ref": "",
    "distributor_ref": "",
    "campaign_code": "",
    "opportunity_ref": "",
    "resolved_tenant": {
      "status": "UNAVAILABLE",
      "tenant_code": null
    }
  },
  "sections": {
    "company": {
      "status": "DRAFT",
      "data": {},
      "missing_evidence": []
    },
    "producer_sponsor": {
      "status": "DRAFT",
      "data": {},
      "missing_evidence": []
    },
    "distributor": {
      "status": "DRAFT",
      "data": {},
      "missing_evidence": []
    },
    "member_role": {
      "status": "DRAFT",
      "data": {},
      "missing_evidence": []
    },
    "campaign_opportunity": {
      "status": "DRAFT",
      "data": {},
      "missing_evidence": []
    },
    "webhook_api": {
      "status": "DRAFT",
      "data": {},
      "missing_evidence": []
    }
  },
  "readiness": {
    "status": "REVIEW_ONLY",
    "items": [],
    "summary": {
      "ready_count": 0,
      "blocked_count": 0,
      "total_count": 0
    }
  },
  "guardrails": [
    "NO_LIVE_MUTATION",
    "TENANT_CODE_INTERNAL",
    "NO_MONEY_MOVEMENT"
  ],
  "redactions": [],
  "source_warnings": []
}
```

Projection rules:

- Projection must be read-only.
- Missing backend evidence must be explicit.
- Shell-only fields must remain marked as draft or unavailable unless a source exists.
- `tenant_code` may appear only inside `resolved_tenant` for authorized operator/admin contexts.
- External-facing projection must omit internal tenant scope.
- Do not infer readiness from frontend local state unless the source is explicitly labelled local/demo.

## Frontend Shell Mapping

| Frontend shell | Contract section | Status until backend source exists |
| --- | --- | --- |
| `CompanyOnboardingPage.tsx` | `company` | `DRAFT` or `UNAVAILABLE` |
| `ProducerSponsorOnboardingPage.tsx` | `producer_sponsor` | `DRAFT` or `UNAVAILABLE` |
| `DistributorOnboardingPage.tsx` | `distributor` | `DRAFT` or `UNAVAILABLE` |
| `MemberRoleOnboardingPage.tsx` | `member_role` | `DRAFT` or `UNAVAILABLE` |
| `CampaignOpportunitySetupPage.tsx` | `campaign_opportunity` | `DRAFT` or `UNAVAILABLE` |
| `WebhookApiSetupPage.tsx` | `webhook_api` | `DRAFT` or `UNAVAILABLE` |
| `OnboardingReadinessChecklistPage.tsx` | `readiness` | `REVIEW_ONLY` |

## Non-Goals And Blocked Areas

TASK-081 does not implement:

- persistence or draft-save APIs;
- typed helper code;
- schema or migrations;
- backend routes;
- frontend feature code;
- auth or permission changes;
- live DB verification;
- production onboarding;
- account or tenant creation;
- invite delivery;
- credential lifecycle;
- webhook delivery;
- campaign lifecycle commands;
- funding, wallet, fulfilment, settlement, retry, or money movement.

TASK-027 and TASK-028 remain blocked and are not affected by this contract.

## Validation / Readback Checklist

Before implementing TASK-082 or any onboarding read/write route, confirm:

- all six onboarding shell states are mapped to contract fields;
- readiness checklist categories map to safe statuses;
- `tenant_code` remains internal and is not the primary external identifier;
- external references are explicit: `external_tenant_ref`, `organisation_ref`, `producer_ref`, `sponsor_ref`, `distributor_ref`, `opportunity_ref`, and `campaign_code`;
- missing evidence has bounded codes and severities;
- fields that must not be exposed externally are listed and respected;
- read-only projection cannot mutate state;
- no secrets, credentials, webhook delivery, account creation, invite delivery, campaign publication, go-live activation, funding, wallet movement, fulfilment, settlement, retry, or money movement is enabled;
- TASK-027 and TASK-028 remain blocked until approved live verification access and drift evidence exist.
