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
        ("POST", "/v1/progress"),
    }

    assert read_only_smoke_routes <= mounted
    assert seeded_write_smoke_routes <= mounted


def test_referral_saas_product_wrapper_routes_remain_unimplemented():
    mounted_paths = {path for _method, path in _mounted_routes()}

    assert not any(path.startswith("/v1/referral-saas") for path in mounted_paths)
