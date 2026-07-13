from __future__ import annotations

from services.referral_saas_validation_service import (
    build_referral_saas_validation_result,
    referral_saas_validation_recovery,
    referral_saas_validation_status,
)


def test_referral_saas_validation_result_maps_success_and_redacts_internal_attributes():
    result = build_referral_saas_validation_result(
        {
            "valid": True,
            "referral_track_id": "track-1",
            "alias": "customer-alias",
            "message": "Referral code validated",
            "error_code": None,
            "attributes": {
                "tenant_code": "FNB",
                "referrer_ucn": "5555555555",
                "referrer_ucn_hash": "secret-hash",
            },
        },
        200,
    )

    assert result == {
        "validationStatus": "VALIDATED",
        "valid": True,
        "referralTrackId": "track-1",
        "alias": "customer-alias",
        "errorCode": None,
        "message": "Referral code validated",
        "recovery": None,
    }
    assert "attributes" not in result
    assert "referrer_ucn" not in result
    assert "referrer_ucn_hash" not in result


def test_referral_saas_validation_status_maps_terms_required_recovery():
    result = build_referral_saas_validation_result(
        {
            "valid": False,
            "message": "Accepted terms are required",
            "error_code": "ACCEPTED_TERMS_REQUIRED",
        },
        400,
    )

    assert result["validationStatus"] == "REJECTED_TERMS_REQUIRED"
    assert result["valid"] is False
    assert result["recovery"] == {
        "action": "ACCEPT_TERMS_AND_RETRY",
        "safeMessage": "Accept the referral terms and try again.",
    }


def test_referral_saas_validation_status_maps_alias_errors_to_single_recovery():
    for error_code in (
        "ALIAS_REQUIRED",
        "ALIAS_TOO_SHORT",
        "ALIAS_TOO_LONG",
        "ALIAS_INVALID_FORMAT",
        "ALIAS_NOT_ALLOWED",
    ):
        assert referral_saas_validation_status({"error_code": error_code}, 400) == "REJECTED_ALIAS"

    assert referral_saas_validation_recovery("REJECTED_ALIAS") == {
        "action": "RETRY_WITH_VALID_ALIAS",
        "safeMessage": "Use a valid display alias and try again.",
    }


def test_referral_saas_validation_status_maps_missing_and_not_found_errors():
    assert (
        referral_saas_validation_status({"error_code": "TENANT_CODE_REQUIRED"}, 400)
        == "REJECTED_MISSING_TENANT"
    )
    assert (
        referral_saas_validation_status({"error_code": "REFERRAL_CODE_REQUIRED"}, 400)
        == "REJECTED_MISSING_CODE"
    )

    result = build_referral_saas_validation_result(
        {
            "valid": False,
            "message": "Referral code not found",
            "error_code": "REFERRAL_CODE_NOT_FOUND",
        },
        404,
    )

    assert result["validationStatus"] == "REJECTED_CODE_NOT_FOUND"
    assert result["recovery"] == {
        "action": "CHECK_CODE_AND_RETRY",
        "safeMessage": "Check the referral code and try again.",
    }


def test_referral_saas_validation_status_treats_logging_failure_as_recovery():
    result = build_referral_saas_validation_result(
        {
            "valid": True,
            "validation_outcome": "FAILED",
            "message": "Referral logging failed",
            "error_code": "REFERRAL_LOG_FAILED",
        },
        200,
    )

    assert result["validationStatus"] == "RECOVERY_REQUIRED_LOGGING"
    assert result["valid"] is False
    assert result["recovery"] == {
        "action": "RETRY_VALIDATION_OR_CONTACT_SUPPORT",
        "safeMessage": "We could not finish setting up this referral. Try again or contact support.",
    }


def test_referral_saas_validation_status_falls_back_to_failed_without_recovery():
    result = build_referral_saas_validation_result(
        {
            "valid": False,
            "message": "Unexpected validation failure",
            "errorCode": "UNKNOWN",
        },
        500,
    )

    assert result == {
        "validationStatus": "FAILED",
        "valid": False,
        "referralTrackId": None,
        "alias": None,
        "errorCode": "UNKNOWN",
        "message": "Unexpected validation failure",
        "recovery": None,
    }
