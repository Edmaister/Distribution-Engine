from services.vertical_regulatory_overlay_service import get_regulatory_overlay


def test_insurance_regulatory_overlay_is_configured():
    overlay = get_regulatory_overlay("INSURANCE_POLICY", "v1")

    assert overlay is not None
    assert overlay.policy_code == "DEFAULT_RECOMMENDATION_POLICY"
    assert "INSURANCE_PRODUCT_INFO" in overlay.disclosure_codes
    assert "INSURANCE_POLICY_ACTIVATION_INFO" in overlay.template_codes
    assert "INSURANCE_CONDUCT" in overlay.regulatory_tags


def test_missing_regulatory_overlay_returns_none():
    assert get_regulatory_overlay("UNKNOWN", "v1") is None
