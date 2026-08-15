from __future__ import annotations

from apps.api.main import app


def _mounted_routes() -> set[tuple[str, str]]:
    mounted: set[tuple[str, str]] = set()
    for route in app.routes:
        path = getattr(route, "path", "")
        methods = getattr(route, "methods", set()) or set()
        for method in methods:
            if method in {"HEAD", "OPTIONS"}:
                continue
            mounted.add((method, path))
    return mounted


def test_referral_saas_current_smoke_routes_are_mounted():
    mounted = _mounted_routes()

    read_only_smoke_routes = {
        ("GET", "/admin/campaigns/{campaign_code}/readiness"),
        ("GET", "/admin/links/inspect"),
        ("GET", "/admin/outcomes/{referral_track_id}/trace"),
        ("GET", "/admin/analytics/reports/{report_type}"),
        ("GET", "/v1/referral-saas/operator/links/inspect"),
        ("GET", "/v1/referral-saas/operator/support-cases"),
        ("GET", "/v1/referral-saas/operator/outcomes/{referral_track_id}/trace"),
        ("GET", "/v1/referral-saas/operator/referrals/{referral_track_id}/progress-status"),
        ("GET", "/v1/referral-saas/workspace/overview"),
        ("GET", "/v1/referral-saas/workspace/account-context"),
        ("GET", "/v1/referral-saas/journey-templates"),
        ("GET", "/v1/referral-saas/journey-templates/{template_code}"),
        ("GET", "/v1/referral-saas/accounts"),
        ("GET", "/v1/referral-saas/accounts/resolve"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/journey-drafts"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/programmes"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/programmes/catalogue"),
        (
            "GET",
            "/v1/referral-saas/accounts/{account_ref}/programmes/drafts/{draft_ref}",
        ),
        ("GET", "/v1/referral-saas/accounts/membership-posture"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/membership-activation-readiness"),
        (
            "GET",
            "/v1/referral-saas/accounts/{account_ref}/memberships/{membership_ref}/login-completion-readiness",
        ),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/identity-login-reconciliation"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/technical-setup-readiness"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/commercial-entitlement"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/production-activation"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/integrations/configuration"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/integrations/execution-readiness"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/integrations/provider-vault/readiness"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/integrations/credential-requests"),
        (
            "GET",
            "/v1/referral-saas/accounts/{account_ref}/integrations/credential-requests/{credential_request_ref}",
        ),
        (
            "GET",
            "/v1/referral-saas/accounts/{account_ref}/integrations/provider-vault/executions/{execution_ref}",
        ),
        ("POST", "/v1/referral-saas/accounts/{account_ref}/integrations/configuration/validate"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/referrals"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/referrals/{referral_track_id}"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/referrer-identities"),
        (
            "GET",
            "/v1/referral-saas/accounts/{account_ref}/referrer-identities/{safe_referrer_key}",
        ),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/referral-attribution"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/journey-analytics"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/journey-versions"),
        (
            "GET",
            "/v1/referral-saas/accounts/{account_ref}/journey-versions/{version_ref}/incentive-bindings",
        ),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/campaigns"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/campaign-attribution"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/campaigns/{campaign_code}"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/campaigns/{campaign_code}/journey-binding"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/campaigns/{campaign_code}/lifecycle"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/campaigns/{campaign_code}/readiness"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/exports/{export_request_id}"),
        (
            "GET",
            "/v1/referral-saas/accounts/{account_ref}/exports/{export_request_id}/download",
        ),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/reports/{report_type}"),
        (
            "GET",
            "/v1/referral-saas/accounts/{account_ref}/reports/{report_type}/delivery-schedules",
        ),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/delivery-schedules/{schedule_id}"),
        (
            "GET",
            "/v1/referral-saas/accounts/{account_ref}/delivery-schedules/{schedule_id}/readiness",
        ),
        (
            "GET",
            "/v1/referral-saas/accounts/{account_ref}/support-cases/{case_ref}/repair-replay-readiness",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/support-cases/{case_ref}/repair-replay-commands",
        ),
        ("POST", "/v1/referral-saas/accounts/{account_ref}/reports/{report_type}/exports/preview"),
        ("POST", "/v1/referral-saas/accounts/{account_ref}/reports/{report_type}/exports/validate"),
        ("GET", "/v1/referral-saas/reports/{report_type}"),
        ("POST", "/v1/referral-saas/reports/{report_type}/exports/preview"),
        ("POST", "/v1/referral-saas/reports/{report_type}/exports/validate"),
        ("GET", "/v1/experience/consumer"),
        ("GET", "/v1/rewards/summary/{referral_track_id}"),
        ("GET", "/v1/rewards/summary/referrers/{referrer_ucn}"),
        ("GET", "/v1/referrers/{referrerUcn}"),
    }
    seeded_write_smoke_routes = {
        ("POST", "/campaigns"),
        ("POST", "/campaigns/validate"),
        ("PATCH", "/campaigns/tracks/{campaign_track_id}"),
        ("PUT", "/campaigns/{campaign_code}/policy"),
        ("POST", "/public/referrals/validate"),
        ("POST", "/referrals/codes"),
        ("POST", "/referrals/referees/ucn"),
        ("POST", "/v1/referral-saas/accounts/from-draft"),
        ("PUT", "/v1/referral-saas/accounts/{account_ref}/journey-drafts"),
        ("POST", "/v1/referral-saas/accounts/{account_ref}/programmes/drafts"),
        (
            "PUT",
            "/v1/referral-saas/accounts/{account_ref}/programmes/drafts/{draft_ref}",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/programmes/drafts/{draft_ref}/validate",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/programmes/drafts/{draft_ref}/submit-review",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/programmes/drafts/{draft_ref}/review-decision",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/programmes/drafts/{draft_ref}/publish",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/programmes/versions/{version_ref}/retire",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/programmes/versions/{version_ref}/rollback-readiness",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/journey-drafts/{draft_ref}/validate",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/journey-drafts/{draft_ref}/publish",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/journey-versions/{version_ref}/archive",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/journey-versions/{version_ref}/incentive-bindings",
        ),
        ("PATCH", "/v1/referral-saas/accounts/{account_ref}/profile"),
        ("POST", "/v1/referral-saas/accounts/{account_ref}/campaigns"),
        (
            "PUT",
            "/v1/referral-saas/accounts/{account_ref}/campaigns/{campaign_code}/journey-binding",
        ),
        (
            "PUT",
            "/v1/referral-saas/accounts/{account_ref}/campaigns/{campaign_code}/programme-binding",
        ),
        (
            "PUT",
            "/v1/referral-saas/accounts/{account_ref}/campaigns/{campaign_code}/policy-settings",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/campaigns/{campaign_code}/review-submissions",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/campaigns/{campaign_code}/review-decisions",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/campaigns/{campaign_code}/activation-requests",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/campaigns/{campaign_code}/lifecycle-commands",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/campaigns/{campaign_code}/referral-codes",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/campaigns/{campaign_code}/referrals/validate",
        ),
        ("POST", "/v1/referral-saas/accounts/{account_ref}/membership-invitations"),
        (
            "PATCH",
            "/v1/referral-saas/accounts/{account_ref}/membership-invitations/{membership_ref}",
        ),
        (
            "DELETE",
            "/v1/referral-saas/accounts/{account_ref}/membership-invitations/{membership_ref}",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/membership-invitations/{membership_ref}/delivery",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/membership-invitations/{membership_ref}/acceptance-token",
        ),
        ("POST", "/v1/referral-saas/membership-acceptance/validate"),
        ("POST", "/v1/referral-saas/membership-acceptance/accept"),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/memberships/{membership_ref}/activation",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/memberships/{membership_ref}/access-provisioning",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/memberships/{membership_ref}/login-completion-intents",
        ),
        ("PUT", "/v1/referral-saas/accounts/{account_ref}/integrations/configuration"),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/integrations/api-access/verification",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/integrations/webhooks/test-dispatch",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/integrations/message-providers/test-check",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/integrations/credential-requests",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/integrations/credential-requests/{credential_request_ref}/review-decisions",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/integrations/credential-requests/{credential_request_ref}/execution-checks",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/integrations/credential-requests/{credential_request_ref}/provider-vault-executions",
        ),
        ("POST", "/v1/referral-saas/accounts/{account_ref}/activation-requests"),
        ("POST", "/v1/referral-saas/accounts/{account_ref}/reports/{report_type}/exports"),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/reports/{report_type}/exports/{export_request_id}/file",
        ),
        ("DELETE", "/v1/referral-saas/accounts/{account_ref}/exports/{export_request_id}"),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/reports/{report_type}/delivery-schedules",
        ),
        ("PATCH", "/v1/referral-saas/accounts/{account_ref}/delivery-schedules/{schedule_id}"),
        ("POST", "/v1/referral-saas/accounts/{account_ref}/support-cases/{case_ref}/assignment"),
        ("POST", "/v1/referral-saas/referral-codes"),
        ("POST", "/v1/referral-saas/public/referrals/validate"),
        ("POST", "/v1/referral-saas/referrals/{referral_track_id}/referee-ucn"),
        ("POST", "/v1/progress"),
    }

    assert read_only_smoke_routes <= mounted
    assert seeded_write_smoke_routes <= mounted


def test_referral_saas_product_wrapper_route_surface_is_bounded():
    mounted = _mounted_routes()

    assert {
        item for item in mounted if item[1].startswith("/v1/referral-saas")
    } == {
        ("GET", "/v1/referral-saas/reports/{report_type}"),
        ("GET", "/v1/referral-saas/operator/links/inspect"),
        ("GET", "/v1/referral-saas/operator/support-cases"),
        ("GET", "/v1/referral-saas/operator/outcomes/{referral_track_id}/trace"),
        ("GET", "/v1/referral-saas/operator/referrals/{referral_track_id}/progress-status"),
        ("GET", "/v1/referral-saas/workspace/overview"),
        ("GET", "/v1/referral-saas/workspace/account-context"),
        ("GET", "/v1/referral-saas/journey-templates"),
        ("GET", "/v1/referral-saas/journey-templates/{template_code}"),
        ("GET", "/v1/referral-saas/accounts"),
        ("GET", "/v1/referral-saas/accounts/resolve"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/journey-drafts"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/programmes"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/programmes/catalogue"),
        (
            "GET",
            "/v1/referral-saas/accounts/{account_ref}/programmes/drafts/{draft_ref}",
        ),
        ("GET", "/v1/referral-saas/accounts/membership-posture"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/membership-activation-readiness"),
        (
            "GET",
            "/v1/referral-saas/accounts/{account_ref}/memberships/{membership_ref}/login-completion-readiness",
        ),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/identity-login-reconciliation"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/technical-setup-readiness"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/commercial-entitlement"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/production-activation"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/integrations/configuration"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/integrations/execution-readiness"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/integrations/provider-vault/readiness"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/integrations/credential-requests"),
        (
            "GET",
            "/v1/referral-saas/accounts/{account_ref}/integrations/credential-requests/{credential_request_ref}",
        ),
        (
            "GET",
            "/v1/referral-saas/accounts/{account_ref}/integrations/provider-vault/executions/{execution_ref}",
        ),
        ("POST", "/v1/referral-saas/accounts/{account_ref}/integrations/configuration/validate"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/referrals"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/referrals/{referral_track_id}"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/referrer-identities"),
        (
            "GET",
            "/v1/referral-saas/accounts/{account_ref}/referrer-identities/{safe_referrer_key}",
        ),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/referral-attribution"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/journey-analytics"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/journey-versions"),
        (
            "GET",
            "/v1/referral-saas/accounts/{account_ref}/journey-versions/{version_ref}/incentive-bindings",
        ),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/campaigns"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/campaign-attribution"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/campaigns/{campaign_code}"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/campaigns/{campaign_code}/journey-binding"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/campaigns/{campaign_code}/lifecycle"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/campaigns/{campaign_code}/readiness"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/exports/{export_request_id}"),
        (
            "GET",
            "/v1/referral-saas/accounts/{account_ref}/exports/{export_request_id}/download",
        ),
        ("DELETE", "/v1/referral-saas/accounts/{account_ref}/exports/{export_request_id}"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/reports/{report_type}"),
        (
            "GET",
            "/v1/referral-saas/accounts/{account_ref}/reports/{report_type}/delivery-schedules",
        ),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/delivery-schedules/{schedule_id}"),
        (
            "GET",
            "/v1/referral-saas/accounts/{account_ref}/delivery-schedules/{schedule_id}/readiness",
        ),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/support-cases"),
        ("GET", "/v1/referral-saas/accounts/{account_ref}/support-cases/{case_ref}"),
        (
            "GET",
            "/v1/referral-saas/accounts/{account_ref}/support-cases/{case_ref}/repair-replay-readiness",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/support-cases/{case_ref}/repair-replay-commands",
        ),
        ("POST", "/v1/referral-saas/accounts/{account_ref}/reports/{report_type}/exports/preview"),
        ("POST", "/v1/referral-saas/accounts/{account_ref}/reports/{report_type}/exports/validate"),
        ("POST", "/v1/referral-saas/accounts/from-draft"),
        ("PUT", "/v1/referral-saas/accounts/{account_ref}/journey-drafts"),
        ("POST", "/v1/referral-saas/accounts/{account_ref}/programmes/drafts"),
        (
            "PUT",
            "/v1/referral-saas/accounts/{account_ref}/programmes/drafts/{draft_ref}",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/programmes/drafts/{draft_ref}/validate",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/programmes/drafts/{draft_ref}/submit-review",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/programmes/drafts/{draft_ref}/review-decision",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/programmes/drafts/{draft_ref}/publish",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/programmes/versions/{version_ref}/retire",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/programmes/versions/{version_ref}/rollback-readiness",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/journey-drafts/{draft_ref}/validate",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/journey-drafts/{draft_ref}/publish",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/journey-versions/{version_ref}/archive",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/journey-versions/{version_ref}/incentive-bindings",
        ),
        ("PATCH", "/v1/referral-saas/accounts/{account_ref}/profile"),
        ("POST", "/v1/referral-saas/accounts/{account_ref}/campaigns"),
        (
            "PUT",
            "/v1/referral-saas/accounts/{account_ref}/campaigns/{campaign_code}/journey-binding",
        ),
        (
            "PUT",
            "/v1/referral-saas/accounts/{account_ref}/campaigns/{campaign_code}/programme-binding",
        ),
        ("POST", "/v1/referral-saas/accounts/{account_ref}/support-cases"),
        ("POST", "/v1/referral-saas/accounts/{account_ref}/support-cases/{case_ref}/notes"),
        ("POST", "/v1/referral-saas/accounts/{account_ref}/support-cases/{case_ref}/status"),
        ("POST", "/v1/referral-saas/accounts/{account_ref}/support-cases/{case_ref}/assignment"),
        (
            "PUT",
            "/v1/referral-saas/accounts/{account_ref}/campaigns/{campaign_code}/policy-settings",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/campaigns/{campaign_code}/review-submissions",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/campaigns/{campaign_code}/review-decisions",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/campaigns/{campaign_code}/activation-requests",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/campaigns/{campaign_code}/lifecycle-commands",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/campaigns/{campaign_code}/referral-codes",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/campaigns/{campaign_code}/referrals/validate",
        ),
        ("POST", "/v1/referral-saas/accounts/{account_ref}/membership-invitations"),
        (
            "PATCH",
            "/v1/referral-saas/accounts/{account_ref}/membership-invitations/{membership_ref}",
        ),
        (
            "DELETE",
            "/v1/referral-saas/accounts/{account_ref}/membership-invitations/{membership_ref}",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/membership-invitations/{membership_ref}/delivery",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/membership-invitations/{membership_ref}/acceptance-token",
        ),
        ("POST", "/v1/referral-saas/membership-acceptance/validate"),
        ("POST", "/v1/referral-saas/membership-acceptance/accept"),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/memberships/{membership_ref}/activation",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/memberships/{membership_ref}/access-provisioning",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/memberships/{membership_ref}/login-completion-intents",
        ),
        ("PUT", "/v1/referral-saas/accounts/{account_ref}/integrations/configuration"),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/integrations/api-access/verification",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/integrations/webhooks/test-dispatch",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/integrations/message-providers/test-check",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/integrations/credential-requests",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/integrations/credential-requests/{credential_request_ref}/review-decisions",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/integrations/credential-requests/{credential_request_ref}/execution-checks",
        ),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/integrations/credential-requests/{credential_request_ref}/provider-vault-executions",
        ),
        ("POST", "/v1/referral-saas/accounts/{account_ref}/activation-requests"),
        ("POST", "/v1/referral-saas/accounts/{account_ref}/reports/{report_type}/exports"),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/reports/{report_type}/exports/{export_request_id}/file",
        ),
        ("DELETE", "/v1/referral-saas/accounts/{account_ref}/exports/{export_request_id}"),
        (
            "POST",
            "/v1/referral-saas/accounts/{account_ref}/reports/{report_type}/delivery-schedules",
        ),
        ("PATCH", "/v1/referral-saas/accounts/{account_ref}/delivery-schedules/{schedule_id}"),
        ("POST", "/v1/referral-saas/reports/{report_type}/exports/preview"),
        ("POST", "/v1/referral-saas/reports/{report_type}/exports/validate"),
        ("POST", "/v1/referral-saas/referral-codes"),
        ("POST", "/v1/referral-saas/public/referrals/validate"),
        ("POST", "/v1/referral-saas/referrals/{referral_track_id}/referee-ucn"),
    }


def test_referral_saas_has_no_commercial_finance_write_routes():
    mounted = _mounted_routes()
    commercial_finance_terms = {
        "billing",
        "invoice",
        "payment",
        "payout",
        "funding",
        "settlement",
        "wallet",
        "treasury",
        "commission",
    }

    finance_writes = {
        (method, path)
        for method, path in mounted
        if path.startswith("/v1/referral-saas")
        and method != "GET"
        and any(term in path.lower() for term in commercial_finance_terms)
    }

    assert finance_writes == set()
