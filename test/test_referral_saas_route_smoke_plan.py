from __future__ import annotations

from scripts import referral_saas_route_smoke_plan as smoke_plan


def test_referral_saas_route_smoke_plan_defaults_to_read_only():
    plan = smoke_plan.build_plan()

    assert plan["mode"] == "dry_run"
    assert plan["safety"]["productionRule"] == "production smoke must stay read-only"
    assert plan["omittedSeededWriteRoutes"] == [
        "referral_code_issue",
        "public_referral_validate",
        "progress_ingest",
    ]
    assert all(route["smoke_class"] == "read_only" for route in plan["routes"])
    assert {route["path"] for route in plan["routes"]} == {
        "/admin/campaigns/{campaign_code}/readiness",
        "/admin/links/inspect",
        "/admin/outcomes/{referral_track_id}/trace",
        "/admin/analytics/reports/{report_type}",
        "/v1/referral-saas/reports/{report_type}",
        "/v1/referral-saas/reports/{report_type}/exports/preview",
        "/v1/referral-saas/reports/{report_type}/exports/validate",
    }


def test_referral_saas_route_smoke_plan_seeded_writes_are_explicit():
    plan = smoke_plan.build_plan(include_seeded_writes=True)

    seeded_routes = [
        route for route in plan["routes"] if route["smoke_class"] == "seeded_write"
    ]

    assert plan["omittedSeededWriteRoutes"] == []
    assert {route["name"] for route in seeded_routes} == {
        "referral_code_issue",
        "public_referral_validate",
        "progress_ingest",
    }
    assert all(
        "local/staging" in route["environment_rule"] for route in seeded_routes
    )
    assert all(route["expected_state_change"] != "none" for route in seeded_routes)


def test_referral_saas_route_smoke_plan_product_wrapper_surface_is_bounded():
    plan = smoke_plan.build_plan(include_seeded_writes=True)

    assert [
        route["path"]
        for route in plan["routes"]
        if route["path"].startswith("/v1/referral-saas")
    ] == [
        "/v1/referral-saas/reports/{report_type}",
        "/v1/referral-saas/reports/{report_type}/exports/validate",
        "/v1/referral-saas/reports/{report_type}/exports/preview",
    ]
