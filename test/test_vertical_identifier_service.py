from services.vertical_identifier_service import validate_event_identifiers


def test_insurance_requires_policy_number_for_first_premium():
    ok, errors = validate_event_identifiers(
        journey_code="INSURANCE_POLICY",
        journey_version="v1",
        event_type="FIRST_PREMIUM_PAID",
        payload={"meta": {}},
    )

    assert ok is False
    assert errors == ["policyNumber is required for FIRST_PREMIUM_PAID"]


def test_insurance_accepts_policy_number_from_meta():
    ok, errors = validate_event_identifiers(
        journey_code="INSURANCE_POLICY",
        journey_version="v1",
        event_type="FIRST_PREMIUM_PAID",
        payload={"meta": {"policyNumber": "POL-123"}},
    )

    assert ok is True
    assert errors == []


def test_insurance_quote_accepts_customer_reference():
    ok, errors = validate_event_identifiers(
        journey_code="INSURANCE_POLICY",
        journey_version="v1",
        event_type="QUOTE_REQUESTED",
        payload={"customerReference": "CUST-1"},
    )

    assert ok is True
    assert errors == []
