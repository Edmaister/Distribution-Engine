from scripts import referral_saas_service_target_calendar_release_check as release_check


def test_calendar_release_check_is_bounded_and_cleanup_is_fk_safe():
    statements = release_check.cleanup_statements()
    assert release_check.RUN_PREFIX == "TASK443_RELEASE_PROOF"
    assert release_check.JURISDICTIONS == ("ZA", "BW")
    assert statements.index(
        "DELETE FROM referral_saas_operational_service_target_clocks WHERE correlation_id LIKE $1"
    ) < statements.index(
        "DELETE FROM referral_saas_service_target_calendar_versions WHERE calendar_code = $1"
    )
    assert statements[-2:] == (
        "DELETE FROM platform_accounts WHERE account_code LIKE $1",
        "DELETE FROM tenants WHERE tenant_code LIKE $1",
    )
