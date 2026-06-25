from __future__ import annotations

import pytest

from services.partner_customer_safe_status_service import (
    project_partner_customer_safe_status,
    project_safe_statuses,
)

SUBJECT = {"type": "outcome", "safe_ref": "outcome:referral-track-safe-1"}


@pytest.mark.parametrize(
    "viewer_role",
    ["partner", "distributor", "sponsor", "producer", "referrer", "customer"],
)
def test_projects_role_safe_status_for_supported_roles(viewer_role):
    family = "outcome" if viewer_role not in {"sponsor", "producer"} else "funding"
    status = "COMPLETED" if family == "outcome" else "RESERVED"

    result = project_partner_customer_safe_status(
        viewer_role=viewer_role,
        subject=SUBJECT,
        evidence={
            "source_family": family,
            "status": status,
            "source_confidence": "HIGH",
        },
    )

    assert result["viewer_role"] == viewer_role
    assert result["subject"] == SUBJECT
    assert result["safe_status"]["status"] in {"FULFILLED", "APPROVED"}
    assert result["safe_status"]["action_category"] == "NONE"
    assert result["safe_status"]["source_confidence"] == "HIGH"


def test_uses_external_safe_fulfilment_mapping():
    result = project_partner_customer_safe_status(
        viewer_role="customer",
        subject=SUBJECT,
        evidence={"source_family": "fulfilment", "status": "FAILED_RETRYABLE"},
    )

    safe_status = result["safe_status"]
    assert safe_status["status"] == "IN_PROGRESS"
    assert safe_status["action_category"] == "RETRY_LATER"
    assert safe_status["action_required"] is False
    assert safe_status["source_families"] == ["fulfilment"]
    assert "FAILED_RETRYABLE" not in str(result)


def test_uses_external_safe_settlement_mapping():
    result = project_partner_customer_safe_status(
        viewer_role="distributor",
        subject=SUBJECT,
        evidence={"source_family": "settlement", "status": "DISPUTED"},
    )

    safe_status = result["safe_status"]
    assert safe_status["status"] == "ACTION_REQUIRED"
    assert safe_status["action_category"] == "REVIEW_DISPUTE"
    assert safe_status["action_required"] is True
    assert "DISPUTED" not in str(result)


@pytest.mark.parametrize(
    ("family", "source_status", "expected_status", "expected_action"),
    [
        ("reward", "APPLIED", "APPROVED", "NONE"),
        ("reward", "EARNED", "QUALIFIED", "NONE"),
        ("reward", "PENDING_FULFILMENT", "IN_PROGRESS", "NONE"),
        ("reward", "FAILED", "ACTION_REQUIRED", "CONTACT_SUPPORT"),
        ("reward", "REVERSED", "ADJUSTED", "NONE"),
        ("commission", "CALCULATED", "APPROVED", "NONE"),
        ("commission", "CREDITED", "FULFILLED", "NONE"),
        ("commission", "REVERSED", "ADJUSTED", "REVIEW_DISPUTE"),
        ("funding", "RESERVED", "APPROVED", "NONE"),
        ("funding", "FAILED", "ACTION_REQUIRED", "VERIFY_PAYMENT_DETAILS"),
        ("webhook", "ACTIVE", "APPROVED", "NONE"),
        ("webhook", "SENT", "FULFILLED", "NONE"),
        ("webhook", "FAILED", "ACTION_REQUIRED", "CONTACT_SUPPORT"),
        ("webhook", "CANCELLED", "ADJUSTED", "NONE"),
    ],
)
def test_maps_source_families_to_safe_statuses(
    family, source_status, expected_status, expected_action
):
    role = "partner" if family in {"reward", "webhook"} else "distributor"
    if family == "funding":
        role = "sponsor"

    result = project_partner_customer_safe_status(
        viewer_role=role,
        subject=SUBJECT,
        evidence={"source_family": family, "status": source_status},
    )

    assert result["safe_status"]["status"] == expected_status
    assert result["safe_status"]["action_category"] == expected_action


def test_missing_evidence_is_bounded_and_can_override_status():
    result = project_partner_customer_safe_status(
        viewer_role="partner",
        subject=SUBJECT,
        evidence={"source_family": "outcome", "status": "PENDING"},
        missing_evidence=[
            {
                "section": "outcome",
                "code": "JOIN_AMBIGUOUS",
                "severity": "WARNING",
                "message": "internal join text is not exposed",
                "source": "internal_table",
            }
        ],
    )

    safe_status = result["safe_status"]
    assert safe_status["status"] == "UNAVAILABLE"
    assert safe_status["action_category"] == "NOT_AVAILABLE"
    assert safe_status["missing_evidence"] == [
        {"code": "JOIN_AMBIGUOUS", "severity": "WARNING", "section": "outcome"}
    ]
    assert "internal_table" not in str(result)
    assert "internal join text" not in str(result)


def test_unknown_source_status_is_unavailable_without_raw_status_leakage():
    result = project_partner_customer_safe_status(
        viewer_role="partner",
        subject=SUBJECT,
        evidence={"source_family": "reward", "status": "FAILED_FINAL_PROVIDER_42"},
    )

    assert result["safe_status"]["status"] == "UNAVAILABLE"
    assert result["safe_status"]["action_category"] == "NOT_AVAILABLE"
    assert "FAILED_FINAL_PROVIDER_42" not in str(result)
    assert "provider_42" not in str(result).lower()


def test_role_scope_hides_adjacent_role_families():
    result = project_partner_customer_safe_status(
        viewer_role="customer",
        subject=SUBJECT,
        evidence={"source_family": "settlement", "status": "SETTLED"},
    )

    safe_status = result["safe_status"]
    assert safe_status["status"] == "UNAVAILABLE"
    assert safe_status["action_category"] == "NOT_AVAILABLE"
    assert safe_status["redactions"] == [
        "private_identifier",
        "provider_payload",
        "raw_status",
        "role_scope",
    ]
    assert "SETTLED" not in str(result)


@pytest.mark.parametrize(
    "evidence",
    [
        {"source_family": "reward", "tenant_code": "FNB"},
        {"source_family": "reward", "raw_ucn": "900007"},
        {"source_family": "reward", "provider_payload": {"error": "boom"}},
        {"source_family": "settlement", "settlement_internal_note": "hidden"},
        {"source_family": "webhook", "signing_secret": "secret"},
        {"source_family": "webhook", "access_token": "token"},
    ],
)
def test_rejects_sensitive_evidence_fields(evidence):
    with pytest.raises(ValueError, match="must not expose"):
        project_partner_customer_safe_status(
            viewer_role="partner",
            subject=SUBJECT,
            evidence=evidence,
        )


def test_rejects_sensitive_subject_fields():
    with pytest.raises(ValueError, match="must not expose"):
        project_partner_customer_safe_status(
            viewer_role="partner",
            subject={"type": "outcome", "safe_ref": "safe", "tenant_code": "FNB"},
            evidence={"source_family": "outcome", "status": "PENDING"},
        )


def test_projects_multiple_statuses_without_mutation():
    evidence = [
        {"source_family": "reward", "status": "APPLIED"},
        {"source_family": "fulfilment", "status": "SUCCESS"},
    ]

    result = project_safe_statuses(
        viewer_role="referrer",
        subject=SUBJECT,
        evidence_items=evidence,
    )

    assert [item["safe_status"]["status"] for item in result] == [
        "APPROVED",
        "FULFILLED",
    ]
    assert evidence == [
        {"source_family": "reward", "status": "APPLIED"},
        {"source_family": "fulfilment", "status": "SUCCESS"},
    ]


def test_requires_supported_role_and_safe_subject():
    with pytest.raises(ValueError, match="Unsupported viewer_role"):
        project_partner_customer_safe_status(
            viewer_role="operator",
            subject=SUBJECT,
            evidence={"source_family": "outcome", "status": "PENDING"},
        )

    with pytest.raises(ValueError, match="subject.type and subject.safe_ref"):
        project_partner_customer_safe_status(
            viewer_role="partner",
            subject={"type": "outcome"},
            evidence={"source_family": "outcome", "status": "PENDING"},
        )
