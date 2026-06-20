# Data Classification

## Purpose

This document defines how the Referral Engine classifies and handles personal, operational, financial, and audit data.

The objective is to support POPIA/GDPR-aligned privacy controls, including anonymisation, retention, and right-to-erasure.

---

## Classification Levels

| Level | Description |
|---|---|
| PUBLIC | Non-sensitive data that can be shared externally |
| INTERNAL | Platform and tenant operational data |
| CONFIDENTIAL | Sensitive business data |
| PII | Personal information linked to an individual |
| SENSITIVE_PII | High-risk personal identifiers or hashed identifiers |
| FINANCIAL_RECORD | Reward, payout, and reconciliation data |
| AUDIT | Compliance and system activity evidence |

---

## Field Classification

| Field | Classification | Erasure Action |
|---|---|---|
| referrer_ucn | SENSITIVE_PII | Do not store raw value |
| referrer_ucn_hash | SENSITIVE_PII | Replace with anonymised deleted hash |
| referee_ucn | SENSITIVE_PII | Do not store raw value |
| referee_ucn_hash | SENSITIVE_PII | Nullify where possible |
| ip_address | PII | Nullify |
| device_fingerprint | PII | Nullify |
| display_name / alias | PII | Replace with anonymised value |
| referral_code | INTERNAL | Retain if no longer directly identifying |
| campaign_code | INTERNAL | Retain |
| product_code | INTERNAL | Retain |
| reward_amount | FINANCIAL_RECORD | Retain |
| payout_status | FINANCIAL_RECORD | Retain |
| audit event type | AUDIT | Retain |
| correlation_id | AUDIT | Retain |

---

## Retention Principles

PII must not be retained indefinitely.

| Data Type | Default Retention |
|---|---:|
| IP address | 90 days |
| Device fingerprint | 90 days |
| Referee identifier hash | 365 days |
| Referral event history | 5 years |
| Reward records | 5–7 years |
| Audit logs | 5–7 years |

Retention periods must be configurable by environment variable.

---

## Right-to-Erasure Principle

When a right-to-erasure request is processed, the platform must:

1. Locate records using hashed identifiers.
2. Anonymise personal identifiers.
3. Nullify unnecessary PII.
4. Preserve financial, reward, fraud, and audit records.
5. Emit an audit event.
6. Never expose raw PII in logs or API responses.

---

## Non-Negotiables

The platform must not:

- Hard delete financial records.
- Store raw UCN values without approval.
- Log raw PII.
- Keep PII indefinitely.
- Commit secrets to source control.
- Return raw exception details in API responses.

---

## Initial Implementation Status

| Item | Status |
|---|---|
| Data classification defined | Done |
| Erasure API | In progress |
| Audit event for erasure | In progress |
| Retention job | Pending |
| Automated retention enforcement | Pending |