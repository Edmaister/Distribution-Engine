from __future__ import annotations

import json

import pytest

from scripts import referral_saas_account_setup_ui_physical_check as script
from services.onboarding.onboarding_state_projection_service import SECTION_DEFINITIONS


def test_build_ui_setup_sections_covers_all_required_onboarding_fields():
    sections = script.build_ui_setup_sections(
        external_tenant_ref="task-208-fnb",
        organisation_ref="org-task-208-fnb",
        organisation_name="Task 208 Account",
        admin_contact="setup@example.test",
    )

    assert tuple(sections) == script.REQUIRED_SECTION_KEYS
    assert set(sections) == set(SECTION_DEFINITIONS)
    for section_name, definition in SECTION_DEFINITIONS.items():
        section = sections[section_name]
        for field in definition["fields"]:
            assert section.get(field) not in (None, "", [])


def test_build_ui_setup_sections_do_not_include_unsafe_or_internal_fields():
    sections = script.build_ui_setup_sections(
        external_tenant_ref="task-208-fnb",
        organisation_ref="org-task-208-fnb",
        organisation_name="Task 208 Account",
        admin_contact="setup@example.test",
    )
    rendered = json.dumps(sections, sort_keys=True).lower()

    assert "tenant_code" not in rendered
    assert "tenantcode" not in rendered
    assert "api_key" not in rendered
    assert "client_secret" not in rendered
    assert "wallet" not in rendered
    assert "settlement" not in rendered
    assert "activate_go_live" not in rendered
    assert "send_invite" not in rendered


def test_complete_ui_sections_rejects_missing_backend_evidence_section():
    sections = script.build_ui_setup_sections(
        external_tenant_ref="task-208-fnb",
        organisation_ref="org-task-208-fnb",
        organisation_name="Task 208 Account",
        admin_contact="setup@example.test",
    )
    sections.pop("campaign_opportunity")

    with pytest.raises(RuntimeError, match="Unexpected UI section keys"):
        script.assert_complete_ui_sections(sections)


def test_forbidden_product_payload_detection_blocks_unsafe_terms():
    script.assert_no_forbidden_product_payload(
        {"account": {"accountId": "acct-1", "externalRef": "task-208"}}
    )

    with pytest.raises(RuntimeError, match="tenant_code"):
        script.assert_no_forbidden_product_payload({"account": {"tenant_code": "FNB"}})

    with pytest.raises(RuntimeError, match="client_secret"):
        script.assert_no_forbidden_product_payload(
            {"credential": {"client_secret": "hidden"}}
        )


def test_parse_args_uses_safe_local_defaults():
    args = script.parse_args([])

    assert args.base_url == "http://127.0.0.1:8000"
    assert args.admin_key == "test-admin-key"
    assert args.internal_tenant_code == "FNB"
