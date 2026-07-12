from __future__ import annotations

import pytest

from services.referral_saas_safe_status_service import (
    project_referral_saas_safe_status,
)

SUBJECT = {
    "type": "referral",
    "safe_ref": "referral:track:11111111-1111-4111-8111-111111111111",
}


@pytest.mark.parametrize(
    ("source_status", "safe_status", "product_status", "action_category"),
    [
        ("VALIDATED", "PENDING", "WAITING", "WAITING_FOR_EVENT"),
        ("UCN_CAPTURED", "IN_PROGRESS", "IN_PROGRESS", "NONE"),
        ("ACCOUNT_OPENED", "IN_PROGRESS", "IN_PROGRESS", "NONE"),
        ("FUNDED", "QUALIFIED", "QUALIFIED", "NONE"),
        ("COMPLETED", "FULFILLED", "COMPLETED", "NONE"),
        ("CANCELLED", "ACTION_REQUIRED", "ACTION_NEEDED", "CONTACT_SUPPORT"),
    ],
)
def test_referral_saas_outcome_statuses_project_to_product_status(
    source_status,
    safe_status,
    product_status,
    action_category,
):
    result = project_referral_saas_safe_status(
        viewer_role="referrer",
        subject=SUBJECT,
        evidence={
            "source_family": "outcome",
            "status": source_status,
            "source_confidence": "HIGH",
        },
        redactions=["referrer_ucn", "tenant_code"],
    )

    projected = result["safe_status"]
    assert projected["status"] == safe_status
    assert projected["product_status"] == product_status
    assert projected["action_category"] == action_category
    assert projected["source_families"] == ["outcome"]
    assert "referrer_ucn" in projected["redactions"]
    assert "tenant_code" in projected["redactions"]
    if source_status != product_status:
        assert source_status not in str(result)


@pytest.mark.parametrize(
    ("family", "source_status", "safe_status", "product_status"),
    [
        ("validation", "REJECTED_TERMS_REQUIRED", "ACTION_REQUIRED", "ACTION_NEEDED"),
        ("validation", "REJECTED_CODE_NOT_FOUND", "UNAVAILABLE", "UNAVAILABLE"),
        ("progress", "RECORDED", "IN_PROGRESS", "IN_PROGRESS"),
        ("progress", "DEDUPED", "IN_PROGRESS", "IN_PROGRESS"),
        ("progress", "FAILED_TO_QUEUE", "UNAVAILABLE", "UNAVAILABLE"),
        ("attribution", "COMPLETE", "QUALIFIED", "QUALIFIED"),
        ("attribution", "INCONSISTENT", "ACTION_REQUIRED", "ACTION_NEEDED"),
        ("link_code", "EXPIRED", "EXPIRED", "EXPIRED"),
    ],
)
def test_referral_saas_non_outcome_statuses_are_projected_as_bounded_outcome(
    family,
    source_status,
    safe_status,
    product_status,
):
    result = project_referral_saas_safe_status(
        viewer_role="customer",
        subject=SUBJECT,
        evidence={"source_family": family, "status": source_status},
    )

    projected = result["safe_status"]
    assert projected["status"] == safe_status
    assert projected["product_status"] == product_status
    assert projected["source_families"] == ["outcome"]
    if source_status != product_status:
        assert source_status not in str(result)


def test_referral_saas_projection_keeps_adjacent_role_money_evidence_unavailable():
    result = project_referral_saas_safe_status(
        viewer_role="customer",
        subject=SUBJECT,
        evidence={"source_family": "settlement", "status": "SETTLED"},
    )

    assert result["safe_status"]["status"] == "UNAVAILABLE"
    assert result["safe_status"]["product_status"] == "UNAVAILABLE"
    assert result["safe_status"]["action_category"] == "NOT_AVAILABLE"
    assert "SETTLED" not in str(result)


def test_referral_saas_projection_rejects_sensitive_evidence():
    with pytest.raises(ValueError, match="must not expose"):
        project_referral_saas_safe_status(
            viewer_role="referrer",
            subject=SUBJECT,
            evidence={
                "source_family": "outcome",
                "status": "ACCOUNT_OPENED",
                "tenant_code": "FNB",
            },
        )
