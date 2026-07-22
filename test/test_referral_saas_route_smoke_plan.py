from __future__ import annotations

from scripts import referral_saas_route_smoke_plan as smoke_plan


def test_referral_saas_route_smoke_plan_defaults_to_read_only():
    plan = smoke_plan.build_plan()

    assert plan["mode"] == "dry_run"
    assert plan["safety"]["productionRule"] == "production smoke must stay read-only"
    assert plan["omittedSeededWriteRoutes"] == [
        "referral_code_issue",
        "referral_saas_referral_code_issue",
        "referral_saas_account_create_from_draft",
        "referral_saas_account_profile_update",
        "referral_saas_account_campaign_setup_create",
        "referral_saas_account_campaign_policy_settings",
        "referral_saas_account_campaign_review_submission",
        "referral_saas_account_campaign_review_decision",
        "referral_saas_membership_invitation_intent",
        "referral_saas_membership_invitation_delivery_request",
        "referral_saas_membership_activation_request",
        "public_referral_validate",
        "referral_saas_public_referral_validate",
        "referral_saas_referee_ucn_capture",
        "progress_ingest",
    ]
    assert all(route["smoke_class"] == "read_only" for route in plan["routes"])
    assert {route["path"] for route in plan["routes"]} == {
        "/admin/campaigns/{campaign_code}/readiness",
        "/admin/links/inspect",
        "/admin/outcomes/{referral_track_id}/trace",
        "/admin/analytics/reports/{report_type}",
        "/v1/referral-saas/operator/links/inspect",
        "/v1/referral-saas/operator/outcomes/{referral_track_id}/trace",
        "/v1/referral-saas/operator/referrals/{referral_track_id}/progress-status",
        "/v1/referral-saas/accounts",
        "/v1/referral-saas/accounts/resolve",
        "/v1/referral-saas/accounts/membership-posture",
        "/v1/referral-saas/accounts/{account_ref}/membership-activation-readiness",
        "/v1/referral-saas/accounts/{account_ref}/technical-setup-readiness",
        "/v1/referral-saas/accounts/{account_ref}/campaigns",
        "/v1/referral-saas/accounts/{account_ref}/campaigns/{campaign_code}",
        "/v1/referral-saas/accounts/{account_ref}/campaigns/{campaign_code}/readiness",
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
        "referral_saas_referral_code_issue",
        "referral_saas_account_create_from_draft",
        "referral_saas_account_profile_update",
        "referral_saas_account_campaign_setup_create",
        "referral_saas_account_campaign_policy_settings",
        "referral_saas_account_campaign_review_submission",
        "referral_saas_account_campaign_review_decision",
        "referral_saas_membership_invitation_intent",
        "referral_saas_membership_invitation_delivery_request",
        "referral_saas_membership_activation_request",
        "public_referral_validate",
        "referral_saas_public_referral_validate",
        "referral_saas_referee_ucn_capture",
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
        "/v1/referral-saas/operator/links/inspect",
        "/v1/referral-saas/operator/outcomes/{referral_track_id}/trace",
        "/v1/referral-saas/operator/referrals/{referral_track_id}/progress-status",
        "/v1/referral-saas/accounts",
        "/v1/referral-saas/accounts/resolve",
        "/v1/referral-saas/accounts/membership-posture",
        "/v1/referral-saas/accounts/{account_ref}/membership-activation-readiness",
        "/v1/referral-saas/accounts/{account_ref}/technical-setup-readiness",
        "/v1/referral-saas/accounts/{account_ref}/campaigns",
        "/v1/referral-saas/accounts/{account_ref}/campaigns/{campaign_code}",
        "/v1/referral-saas/accounts/{account_ref}/campaigns/{campaign_code}/readiness",
        "/v1/referral-saas/reports/{report_type}",
        "/v1/referral-saas/reports/{report_type}/exports/validate",
        "/v1/referral-saas/reports/{report_type}/exports/preview",
        "/v1/referral-saas/referral-codes",
        "/v1/referral-saas/accounts/from-draft",
        "/v1/referral-saas/accounts/{account_ref}/profile",
        "/v1/referral-saas/accounts/{account_ref}/campaigns",
        "/v1/referral-saas/accounts/{account_ref}/campaigns/{campaign_code}/policy-settings",
        "/v1/referral-saas/accounts/{account_ref}/campaigns/{campaign_code}/review-submissions",
        "/v1/referral-saas/accounts/{account_ref}/campaigns/{campaign_code}/review-decisions",
        "/v1/referral-saas/accounts/{account_ref}/membership-invitations",
        "/v1/referral-saas/accounts/{account_ref}/membership-invitations/{membership_ref}/delivery",
        "/v1/referral-saas/accounts/{account_ref}/memberships/{membership_ref}/activation",
        "/v1/referral-saas/public/referrals/validate",
        "/v1/referral-saas/referrals/{referral_track_id}/referee-ucn",
    ]
