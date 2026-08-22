from __future__ import annotations

from scripts import referral_saas_service_target_release_check as release_check


def test_release_check_cleanup_order_respects_foreign_keys():
    statements = release_check.cleanup_statements()
    assert "audit" in statements[0]
    assert "pause_events" in statements[1]
    assert "clocks" in statements[2]
    assert "support_cases" in statements[3]
    assert "policies" in statements[4]
    assert "platform_accounts" in statements[5]
    assert "tenants" in statements[6]


def test_release_check_is_bounded_to_two_jurisdictions_and_unique_evidence():
    assert release_check.JURISDICTIONS == ("NA", "ZM")
    assert release_check.RUN_PREFIX == "TASK436_RELEASE_PROOF"
    assert release_check._evidence_key("run", "action") != release_check._evidence_key("run", "other")
