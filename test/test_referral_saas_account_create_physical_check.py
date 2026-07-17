from __future__ import annotations

import json

import pytest

from scripts import referral_saas_account_create_physical_check as script
from services.onboarding.onboarding_state_projection_service import SECTION_DEFINITIONS


def test_build_seed_sections_covers_all_required_onboarding_fields():
    sections = script.build_seed_sections(
        external_tenant_ref="task-206-fnb",
        organisation_ref="org-task-206-fnb",
        producer_ref="producer-task-206",
        sponsor_ref="sponsor-task-206",
        distributor_ref="distributor-task-206",
        campaign_code="CMP-TASK-206",
        opportunity_ref="opp-task-206",
        organisation_name="Task 206 Account",
        admin_contact="setup@example.test",
    )

    assert set(sections) == set(SECTION_DEFINITIONS)
    for section_name, definition in SECTION_DEFINITIONS.items():
        section = sections[section_name]
        for field in definition["fields"]:
            assert section.get(field) not in (None, "", [])


def test_build_seed_sections_do_not_include_unsafe_or_internal_keys():
    sections = script.build_seed_sections(
        external_tenant_ref="task-206-fnb",
        organisation_ref="org-task-206-fnb",
        producer_ref="producer-task-206",
        sponsor_ref="sponsor-task-206",
        distributor_ref="distributor-task-206",
        campaign_code="CMP-TASK-206",
        opportunity_ref="opp-task-206",
        organisation_name="Task 206 Account",
        admin_contact="setup@example.test",
    )
    rendered = json.dumps(sections, sort_keys=True).lower()

    assert "tenant_code" not in rendered
    assert "tenantcode" not in rendered
    assert "api_key" not in rendered
    assert "client_secret" not in rendered
    assert "money_movement" not in rendered
    assert "activate_go_live" not in rendered


def test_product_payload_internal_tenant_leak_detection():
    script.assert_no_internal_tenant_identifier(
        {"account": {"accountId": "acct-1", "externalRef": "task-206"}}
    )

    with pytest.raises(RuntimeError, match="internal tenant identifier"):
        script.assert_no_internal_tenant_identifier(
            {"account": {"tenantCode": "FNB"}}
        )

    with pytest.raises(RuntimeError, match="internal tenant identifier"):
        script.assert_no_internal_tenant_identifier(
            {"account": {"tenant_code": "FNB"}}
        )


def test_parse_args_uses_safe_local_defaults():
    args = script.parse_args([])

    assert args.base_url == "http://127.0.0.1:8000"
    assert args.admin_key == "test-admin-key"
    assert args.internal_tenant_code == "FNB"
