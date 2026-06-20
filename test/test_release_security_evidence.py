from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_release_security_checklist_links_controls_to_evidence():
    source = (ROOT / "docs" / "RELEASE_SECURITY_CHECKLIST.md").read_text(
        encoding="utf-8"
    )

    for heading in (
        "## Auth And Scope",
        "## Secrets",
        "## PII And Data Handling",
        "## Audit And Monitoring",
        "## Sign-Off",
    ):
        assert heading in source

    for evidence in (
        "test/test_permissions.py",
        "test/test_consumer_experience_api.py",
        "test/test_core_role_journey_smoke.py",
        "test/test_data_quality_service.py",
        "scripts/core_role_journey_smoke.py",
        "scripts/target_state_smoke.py",
        "scripts/admin_audit_smoke.py",
        "docs/ONBOARDING_RUNBOOK.md",
        "docs/DATA_CLASIFICATION.md",
        "admin_audit_writes_total",
        "bff_aggregate_requests_total",
    ):
        assert evidence in source


def test_production_runbook_references_release_security_checklist():
    source = (ROOT / "docs" / "PRODUCTION_RUNBOOK.md").read_text(encoding="utf-8")

    assert "docs/RELEASE_SECURITY_CHECKLIST.md" in source
    assert "docs/ONBOARDING_RUNBOOK.md" in source
