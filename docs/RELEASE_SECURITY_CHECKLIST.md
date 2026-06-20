# Release Security Checklist

Use this checklist before promoting a release to production. The release owner
should attach the command output or review note for each row.

## Auth And Scope

| Control | Evidence | Release rule |
| --- | --- | --- |
| Role-based session contract | `python -m pytest test/test_frontend_api_contracts.py test/test_core_role_journey_smoke.py -q` | Consumer, producer, distributor, and admin workspaces resolve from backend-confirmed session identity. |
| Tenant, producer, distributor, and consumer scoping | `python -m pytest test/test_permissions.py test/test_consumer_experience_api.py -q` | Wrong-tenant and wrong-scope requests are rejected. |
| Scoped admin boundaries | `python -m pytest test/test_permissions.py test/test_admin_audit_api.py -q` | Finance, distribution, system, and platform admin keys keep intended boundaries. |
| Live role smoke | `python scripts/core_role_journey_smoke.py --base-url <base-url>` | Role sessions, read paths, and wrong-scope calls pass in the target environment. |

## Secrets

| Control | Evidence | Release rule |
| --- | --- | --- |
| Test keys disabled outside local/dev/test | Review `APP_ENV` and `docs/SECURITY_AUTH.md` | Production must not run with `APP_ENV` set to `local`, `dev`, or `test`. |
| Runtime secrets are externalised | Deployment manifest or platform secret reference | API keys, worker secret, database DSN, JWT secret, and provider secrets must not be baked into images. |
| Worker secret enforced | `python -m pytest test/test_worker.py test/test_security_and_error_handling.py -q` | Worker endpoint rejects missing or wrong secrets. |
| JWT signing and claim policy confirmed | IdP release note or security sign-off | Issuer, audience, expiry, role, tenant, producer, distributor, and subject claim mappings are approved. |

## PII And Data Handling

| Control | Evidence | Release rule |
| --- | --- | --- |
| Data classification reviewed | `docs/DATA_CLASIFICATION.md` | Sensitive identifiers, financial records, and audit records have agreed handling rules. |
| No raw PII in release evidence | Review logs, smoke output, and screenshots | Release artifacts must not contain raw UCNs, account numbers, tokens, or secrets. |
| Consumer joins validated | `python -m pytest test/test_data_quality_service.py -q` | No critical data-quality issue is accepted for customer-facing proof, reward, mission, or leaderboard journeys. |
| Privacy controls still pass | `python -m pytest test/test_privacy_api.py test/test_privacy_service.py -q` | Erasure/anonymisation behavior has not regressed. |

## Audit And Monitoring

| Control | Evidence | Release rule |
| --- | --- | --- |
| Admin audit writes are healthy | `python scripts/admin_audit_smoke.py --base-url <base-url>` | Sensitive admin action creates a successful audit row. |
| Target-state smoke passes | `python scripts/target_state_smoke.py --base-url <base-url>` | Health, readiness, role journeys, enterprise event, finance, distribution, audit, and metrics checks pass. |
| Audit metrics monitored | `/metrics` includes `admin_audit_writes_total` | `result="failure"` must not increase after release. |
| BFF partial response metrics monitored | `/metrics` includes `bff_aggregate_requests_total` | Sustained `status="partial"` for core journeys requires rollback review. |
| Tenant, partner, and channel onboarding | `docs/ONBOARDING_RUNBOOK.md` | Onboarding evidence, monitoring, handover, and rollback controls are complete before pilot traffic. |

## Sign-Off

Release sign-off requires:

- Release owner
- Security reviewer
- Operations reviewer
- Evidence location
- Accepted warnings with owner and expiry date
- Rollback decision and previous known-good version
