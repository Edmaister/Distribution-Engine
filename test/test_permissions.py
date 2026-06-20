import pytest
from fastapi import HTTPException

from utils.permissions import (
    require_consumer_scope,
    require_distributor_scope,
    require_partner_tenant_scope,
    require_producer_scope,
    require_tenant_scope,
)


def test_require_tenant_scope_allows_admin_override():
    require_tenant_scope({"role": "ADMIN", "tenant_code": "INTERNAL"}, "FNB")


def test_require_tenant_scope_rejects_cross_tenant_access():
    with pytest.raises(HTTPException) as exc:
        require_tenant_scope({"role": "PARTNER", "tenant_code": "PNP"}, "FNB")

    assert exc.value.status_code == 403


def test_require_partner_tenant_scope_allows_partner_same_tenant():
    require_partner_tenant_scope({"role": "PARTNER", "tenant_code": "FNB"}, "fnb")


def test_require_partner_tenant_scope_rejects_consumer_role():
    with pytest.raises(HTTPException) as exc:
        require_partner_tenant_scope({"role": "CONSUMER", "tenant_code": "FNB"}, "FNB")

    assert exc.value.status_code == 403


def test_require_producer_scope_allows_matching_producer():
    require_producer_scope(
        {"role": "PRODUCER", "tenant_code": "FNB", "producer_code": "INSURECO"},
        tenant_code="FNB",
        producer_code="INSURECO",
    )


def test_require_producer_scope_rejects_wrong_producer():
    with pytest.raises(HTTPException) as exc:
        require_producer_scope(
            {"role": "PRODUCER", "tenant_code": "FNB", "producer_code": "OTHER"},
            tenant_code="FNB",
            producer_code="INSURECO",
        )

    assert exc.value.status_code == 403


def test_require_distributor_scope_allows_matching_distributor():
    require_distributor_scope(
        {
            "role": "DISTRIBUTOR",
            "tenant_code": "FNB",
            "distributor_code": "DIST-INSURANCE-ADVOCATE",
        },
        tenant_code="FNB",
        distributor_code="DIST-INSURANCE-ADVOCATE",
    )


def test_require_distributor_scope_rejects_wrong_distributor():
    with pytest.raises(HTTPException) as exc:
        require_distributor_scope(
            {
                "role": "DISTRIBUTOR",
                "tenant_code": "FNB",
                "distributor_code": "OTHER",
            },
            tenant_code="FNB",
            distributor_code="DIST-INSURANCE-ADVOCATE",
        )

    assert exc.value.status_code == 403


def test_require_consumer_scope_allows_consumer_same_tenant():
    require_consumer_scope({"role": "CONSUMER", "tenant_code": "FNB"}, tenant_code="fnb")


def test_require_consumer_scope_rejects_unrelated_role():
    with pytest.raises(HTTPException) as exc:
        require_consumer_scope({"role": "DISTRIBUTOR", "tenant_code": "FNB"}, tenant_code="FNB")

    assert exc.value.status_code == 403
