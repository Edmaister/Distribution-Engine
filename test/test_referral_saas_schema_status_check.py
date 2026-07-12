from __future__ import annotations

from scripts import referral_saas_schema_status_check as checker


def test_referral_saas_schema_status_dry_run_is_read_only_plan():
    payload = checker.build_dry_run()

    assert payload["ok"] is True
    assert payload["mode"] == "dry_run"
    assert "referrer_codes" in payload["requiredTables"]
    assert "referral_progress_events" in payload["requiredTables"]
    assert "campaign_attributions" in payload["requiredTables"]
    assert "enterprise_event_inbox" in payload["requiredTables"]
    assert (
        "ux_enterprise_event_inbox_dedupe_key"
        in payload["expectedIndexes"]["enterprise_event_inbox"]
    )
    assert any(
        item["table"] == "referral_progress_events"
        and item["field"] == "event_type"
        for item in payload["stateFields"]
    )
    assert all(query["category"] in {"schema", "state"} for query in payload["queryPlan"])
    assert all(
        not query["sql"].lstrip().upper().startswith(
            ("INSERT", "UPDATE", "DELETE", "ALTER", "DROP", "TRUNCATE")
        )
        for query in payload["queryPlan"]
    )


def test_referral_saas_schema_status_static_expectations_find_missing_items():
    findings = checker._evaluate_static_expectations(
        {
            "required_tables": [{"table_name": "referrer_codes"}],
            "constraints": [],
            "indexes": [],
        }
    )

    assert "missing table: referral_progress_events" in findings
    assert "missing constraint: referral_progress_events.chk_rpe_event_type" in findings
    assert "missing index: referral_progress_events.ux_progress_events_dedupe_key" in findings


def test_referral_saas_schema_status_rejects_unsafe_identifier():
    try:
        checker.build_query_plan('public; DROP TABLE tenants;')
    except ValueError as exc:
        assert "Unsafe SQL identifier" in str(exc)
    else:
        raise AssertionError("unsafe schema identifier was accepted")
