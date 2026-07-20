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
        ("GET", "/v1/referral-saas/operator/outcomes/{referral_track_id}/trace"),
        ("GET", "/v1/referral-saas/operator/referrals/{referral_track_id}/progress-status"),
        ("GET", "/v1/referral-saas/accounts"),
        ("GET", "/v1/referral-saas/accounts/resolve"),
        ("GET", "/v1/referral-saas/accounts/membership-posture"),
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
        ("PATCH", "/v1/referral-saas/accounts/{account_ref}/profile"),
        ("POST", "/v1/referral-saas/accounts/{account_ref}/membership-invitations"),
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
        ("GET", "/v1/referral-saas/operator/outcomes/{referral_track_id}/trace"),
        ("GET", "/v1/referral-saas/operator/referrals/{referral_track_id}/progress-status"),
        ("GET", "/v1/referral-saas/accounts"),
        ("GET", "/v1/referral-saas/accounts/resolve"),
        ("GET", "/v1/referral-saas/accounts/membership-posture"),
        ("POST", "/v1/referral-saas/accounts/from-draft"),
        ("PATCH", "/v1/referral-saas/accounts/{account_ref}/profile"),
        ("POST", "/v1/referral-saas/accounts/{account_ref}/membership-invitations"),
        ("POST", "/v1/referral-saas/reports/{report_type}/exports/preview"),
        ("POST", "/v1/referral-saas/reports/{report_type}/exports/validate"),
        ("POST", "/v1/referral-saas/referral-codes"),
        ("POST", "/v1/referral-saas/public/referrals/validate"),
        ("POST", "/v1/referral-saas/referrals/{referral_track_id}/referee-ucn"),
    }
