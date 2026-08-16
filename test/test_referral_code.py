from contextlib import asynccontextmanager
import json

import pytest

import os

os.environ.setdefault(
    "REFERRAL_CODE_SECRET",
    "test-referral-secret-123456789"
)

import services.referral_code as rc


PROGRAMME_VERSION_ID = "11111111-1111-4111-8111-111111111111"
CUSTOMER_JOURNEY_VERSION_ID = "22222222-2222-4222-8222-222222222222"
CUSTOMER_PRODUCT_LINE_ID = "33333333-3333-4333-8333-333333333333"
CUSTOMER_PRODUCT_OFFERING_ID = "44444444-4444-4444-8444-444444444444"


# -----------------------
# Fake async DB
# -----------------------

class FakeTransaction:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None


class FakeAsyncConn:
    def __init__(self, fetchrow_values=None):
        self._fetchrow_values = list(fetchrow_values or [])
        self.executed = []

    def transaction(self):
        return FakeTransaction()

    async def fetchrow(self, sql, *params):
        self.executed.append((sql, params))
        if self._fetchrow_values:
            return self._fetchrow_values.pop(0)
        return None

    async def execute(self, sql, *params):
        self.executed.append((sql, params))
        return "EXECUTE 1"


def patch_async_db(monkeypatch, conn):
    @asynccontextmanager
    async def fake_db_connection():
        yield conn

    monkeypatch.setattr(rc, "db_connection", fake_db_connection)


# -----------------------
# Tests
# -----------------------

def test_generate_referral_code():
    code = rc._generate_referral_code()
    assert len(code) == 10


def test_handle_validation():
    assert rc._is_handle_valid("Valid_123")
    assert not rc._is_handle_valid("x")
    assert not rc._is_handle_valid("invalid space")


@pytest.mark.asyncio
async def test_get_or_create_missing_fields():
    body, status = await rc.get_or_create_referrer_code(
        referrer_ucn="",
        tenant="FNB",
        sticker="ST1",
        segment="PREMIER",
        accepted_terms=True,
    )

    assert status == 400
    assert body["error_code"] == "MISSING_FIELDS"


@pytest.mark.asyncio
async def test_get_or_create_requires_terms():
    body, status = await rc.get_or_create_referrer_code(
        referrer_ucn="123",
        tenant="FNB",
        sticker="ST1",
        segment="PREMIER",
        accepted_terms=False,
    )

    assert status == 400
    assert body["error_code"] == "ACCEPTED_TERMS_REQUIRED"


@pytest.mark.asyncio
async def test_get_or_create_existing(monkeypatch):
    conn = FakeAsyncConn(
        fetchrow_values=[
            {
                "referral_code": "CODE123",
                "gaming_handle": "Handle1",
            }
        ]
    )
    patch_async_db(monkeypatch, conn)

    monkeypatch.setattr(rc, "_identity_lookup_key", lambda x: "hash")

    body, status = await rc.get_or_create_referrer_code(
        referrer_ucn="123",
        tenant="FNB",
        sticker="ST1",
        segment="PREMIER",
        accepted_terms=True,
    )

    assert status == 200
    assert body["created"] is False
    assert body["referral_code"] == "CODE123"
    assert body["gaming_handle"] == "Handle1"


@pytest.mark.asyncio
async def test_get_or_create_new(monkeypatch):
    conn = FakeAsyncConn(fetchrow_values=[None])
    patch_async_db(monkeypatch, conn)

    monkeypatch.setattr(rc, "_identity_lookup_key", lambda x: "hash")
    monkeypatch.setattr(rc, "_generate_referral_code", lambda: "NEWCODE")

    async def fake_pick_handle(conn, preferred):
        return "HandleX"

    monkeypatch.setattr(rc, "_pick_handle", fake_pick_handle)

    body, status = await rc.get_or_create_referrer_code(
        referrer_ucn="123",
        tenant="FNB",
        sticker="ST1",
        segment="PREMIER",
        accepted_terms=True,
    )

    assert status == 201
    assert body["created"] is True
    assert body["referral_code"] == "NEWCODE"


@pytest.mark.asyncio
async def test_validate_referral_code_missing_inputs():
    body, status = await rc.validate_referral_code(
        tenant_code="",
        referral_code="",
        accepted_terms=False,
    )

    assert status == 400


@pytest.mark.asyncio
async def test_validate_referral_code_not_found(monkeypatch):
    conn = FakeAsyncConn(fetchrow_values=[None])
    patch_async_db(monkeypatch, conn)

    body, status = await rc.validate_referral_code(
        tenant_code="FNB",
        referral_code="ABC",
        accepted_terms=True,
    )

    assert status == 404
    assert body["valid"] is False


@pytest.mark.asyncio
async def test_validate_referral_code_success(monkeypatch):
    conn = FakeAsyncConn(
        fetchrow_values=[
            {
                "referrer_code_id": "code-id",
                "referrer_ucn": "123",
                "sticker": "CAMPAIGN-001",
            }
        ]
    )
    patch_async_db(monkeypatch, conn)

    monkeypatch.setattr(rc, "_normalize_alias", lambda x: "Alias1")
    monkeypatch.setattr(rc, "_validate_alias", lambda x: (True, None, "alias1"))

    body, status = await rc.validate_referral_code(
        tenant_code="FNB",
        referral_code="ABC",
        accepted_terms=True,
    )

    assert status == 200
    assert body["valid"] is True
    assert body["attributes"]["programmeRuntimeBinding"] == {
        "bound": False,
        "programmeVersionId": None,
    }


@pytest.mark.asyncio
async def test_validate_referral_code_binds_programme_runtime_context(monkeypatch):
    conn = FakeAsyncConn(
        fetchrow_values=[
            {
                "referrer_code_id": "code-id",
                "referrer_ucn": "123",
                "sticker": "CAMPAIGN-001",
            },
            {
                "attributes": {
                    "referral_saas_programme_binding": {
                        "programmeVersionId": PROGRAMME_VERSION_ID,
                        "programmeCode": "HOME_LOAN",
                        "programmeName": "Home Loan Referral",
                        "versionNumber": 2,
                        "customerJourneyVersionId": CUSTOMER_JOURNEY_VERSION_ID,
                        "rawConfig": {"must": "not leak"},
                    }
                }
            },
            {
                "programme_version_id": PROGRAMME_VERSION_ID,
                "programme_code": "HOME_LOAN",
                "programme_name": "Home Loan Referral",
                "version_number": 2,
                "version_status": "PUBLISHED",
                "customer_journey_version_id": CUSTOMER_JOURNEY_VERSION_ID,
                "operating_jurisdiction_code": "ZA",
                "customer_product_line_id": CUSTOMER_PRODUCT_LINE_ID,
                "customer_product_offering_id": CUSTOMER_PRODUCT_OFFERING_ID,
                "campaign_defaults_snapshot": {
                    "reward": {"type": "voucher"},
                    "attribution": {"model": "last-touch"},
                },
                "configuration_checksum": "programme-checksum",
                "safe_summary": {"label": "Home loan referral"},
                "retired_at": None,
                "external_product_line_ref": "HOME_LOANS",
                "product_line_name": "Home Loans",
                "product_line_category": "Banking and financial services",
                "external_offering_ref": "STANDARD_HOME_LOAN",
                "offering_name": "Standard Home Loan",
                "offering_family": "Mortgage",
                "product_offering_operating_jurisdiction_code": "ZA",
            },
        ]
    )
    patch_async_db(monkeypatch, conn)

    monkeypatch.setattr(rc, "_normalize_alias", lambda x: "Alias1")
    monkeypatch.setattr(rc, "_validate_alias", lambda x: (True, None, "alias1"))

    body, status = await rc.validate_referral_code(
        tenant_code="FNB",
        referral_code="ABC",
        accepted_terms=True,
    )

    assert status == 200
    assert body["attributes"]["programmeRuntimeBinding"] == {
        "bound": True,
        "programmeVersionId": PROGRAMME_VERSION_ID,
    }
    campaign_lookup = next(
        call for call in conn.executed if "FROM marketing_campaigns" in call[0]
    )
    assert campaign_lookup[1] == ("FNB", "CAMPAIGN-001")
    referral_insert = next(
        call for call in conn.executed if "INSERT INTO referral_instances" in call[0]
    )
    assert "programme_version_id" in referral_insert[0]
    assert "programme_runtime_context" in referral_insert[0]
    assert referral_insert[1][10] == PROGRAMME_VERSION_ID
    runtime_context = json.loads(referral_insert[1][11])
    assert runtime_context["programmeVersionId"] == PROGRAMME_VERSION_ID
    assert runtime_context["programmeCode"] == "HOME_LOAN"
    assert runtime_context["programmeName"] == "Home Loan Referral"
    assert runtime_context["versionNumber"] == 2
    assert runtime_context["customerJourneyVersionId"] == CUSTOMER_JOURNEY_VERSION_ID
    assert runtime_context["source"] == "CAMPAIGN_PUBLISHED_PROGRAMME_BINDING"
    assert "rawConfig" not in runtime_context
    snapshot = runtime_context["effectiveRuleSnapshot"]
    assert snapshot["snapshotType"] == "REFERRAL_SAAS_EFFECTIVE_RULE_CONTEXT"
    assert snapshot["customerProductBinding"] == {
        "customerProductLineId": CUSTOMER_PRODUCT_LINE_ID,
        "customerProductOfferingId": CUSTOMER_PRODUCT_OFFERING_ID,
        "externalProductLineRef": "HOME_LOANS",
        "productLineName": "Home Loans",
        "productLineCategory": "Banking and financial services",
        "externalOfferingRef": "STANDARD_HOME_LOAN",
        "offeringName": "Standard Home Loan",
        "offeringFamily": "Mortgage",
        "operatingJurisdictionCode": "ZA",
    }
    assert snapshot["programmeDefaultRules"]["ruleKeys"] == ["attribution", "reward"]
    assert snapshot["programmeDefaultRules"]["checksum"]
    assert snapshot["campaignOverrideRules"] == {
        "present": False,
        "approved": False,
        "overrideKeys": [],
        "overrideReasonPresent": False,
        "approvedAt": None,
        "checksum": rc._canonical_hash({}),
    }
    assert snapshot["effectiveRulesChecksum"]
    assert snapshot["configurationPayloadRedacted"] is True
    assert "rawConfig" not in json.dumps(snapshot)


@pytest.mark.asyncio
async def test_validate_referral_code_freezes_approved_campaign_override_snapshot(monkeypatch):
    conn = FakeAsyncConn(
        fetchrow_values=[
            {
                "referrer_code_id": "code-id",
                "referrer_ucn": "123",
                "sticker": "CAMPAIGN-001",
            },
            {
                "campaign_code": "CAMPAIGN-001",
                "attributes": {
                    "referral_saas_programme_binding": {
                        "programmeVersionId": PROGRAMME_VERSION_ID,
                        "programmeCode": "HOME_LOAN",
                        "programmeName": "Home Loan Referral",
                        "versionNumber": 2,
                        "customerJourneyVersionId": CUSTOMER_JOURNEY_VERSION_ID,
                    },
                    "referral_saas_campaign_override": {
                        "programmeVersionId": PROGRAMME_VERSION_ID,
                        "overrideStatus": "APPROVED",
                        "overridePayload": {
                            "reward": {"displayLabel": "Campaign launch reward"},
                            "audience": {"segment": "Premier"},
                        },
                        "overrideReason": "Launch incentive",
                        "approvedAt": "2026-08-01T00:00:00Z",
                        "secret": "must not leak",
                    },
                },
            },
            {
                "programme_version_id": PROGRAMME_VERSION_ID,
                "programme_code": "HOME_LOAN",
                "programme_name": "Home Loan Referral",
                "version_number": 2,
                "version_status": "PUBLISHED",
                "customer_journey_version_id": CUSTOMER_JOURNEY_VERSION_ID,
                "operating_jurisdiction_code": "ZA",
                "customer_product_line_id": CUSTOMER_PRODUCT_LINE_ID,
                "customer_product_offering_id": CUSTOMER_PRODUCT_OFFERING_ID,
                "campaign_defaults_snapshot": {"reward": {"type": "voucher"}},
                "configuration_checksum": "programme-checksum",
                "safe_summary": {"label": "Home loan referral"},
                "retired_at": None,
                "external_product_line_ref": "HOME_LOANS",
                "product_line_name": "Home Loans",
                "product_line_category": "Banking and financial services",
                "external_offering_ref": "STANDARD_HOME_LOAN",
                "offering_name": "Standard Home Loan",
                "offering_family": "Mortgage",
                "product_offering_operating_jurisdiction_code": "ZA",
            },
        ]
    )
    patch_async_db(monkeypatch, conn)

    monkeypatch.setattr(rc, "_normalize_alias", lambda x: "Alias1")
    monkeypatch.setattr(rc, "_validate_alias", lambda x: (True, None, "alias1"))

    body, status = await rc.validate_referral_code(
        tenant_code="FNB",
        referral_code="ABC",
        accepted_terms=True,
    )

    assert status == 200
    assert body["valid"] is True
    referral_insert = next(
        call for call in conn.executed if "INSERT INTO referral_instances" in call[0]
    )
    runtime_context = json.loads(referral_insert[1][11])
    snapshot = runtime_context["effectiveRuleSnapshot"]
    assert snapshot["campaignOverrideRules"]["present"] is True
    assert snapshot["campaignOverrideRules"]["approved"] is True
    assert snapshot["campaignOverrideRules"]["overrideKeys"] == ["audience", "reward"]
    assert snapshot["campaignOverrideRules"]["overrideReasonPresent"] is True
    assert snapshot["campaignOverrideRules"]["approvedAt"] == "2026-08-01T00:00:00Z"
    safe_snapshot_text = json.dumps(snapshot)
    assert "Campaign launch reward" not in safe_snapshot_text
    assert "Premier" not in safe_snapshot_text
    assert "must not leak" not in safe_snapshot_text


@pytest.mark.asyncio
async def test_validate_referral_code_fails_closed_for_missing_programme_binding(monkeypatch):
    conn = FakeAsyncConn(
        fetchrow_values=[
            {
                "referrer_code_id": "code-id",
                "referrer_ucn": "123",
                "sticker": "CAMPAIGN-001",
            },
            {
                "campaign_code": "CAMPAIGN-001",
                "attributes": {
                    "referral_saas_programme_binding": {
                        "programmeVersionId": PROGRAMME_VERSION_ID,
                        "programmeCode": "HOME_LOAN",
                        "programmeName": "Home Loan Referral",
                        "versionNumber": 2,
                        "customerJourneyVersionId": CUSTOMER_JOURNEY_VERSION_ID,
                    },
                },
            },
            None,
        ]
    )
    patch_async_db(monkeypatch, conn)

    monkeypatch.setattr(rc, "_normalize_alias", lambda x: "Alias1")
    monkeypatch.setattr(rc, "_validate_alias", lambda x: (True, None, "alias1"))

    body, status = await rc.validate_referral_code(
        tenant_code="FNB",
        referral_code="ABC",
        accepted_terms=True,
    )

    assert status == 200
    assert body["valid"] is True
    assert body["error_code"] == "REFERRAL_LOG_FAILED"
    assert not any("INSERT INTO referral_instances" in call[0] for call in conn.executed)


@pytest.mark.asyncio
async def test_capture_referee_ucn_missing():
    body, status = await rc.capture_referee_ucn(
        referral_track_id="",
        referee_ucn="",
        tenant_code="FNB",
    )

    assert status == 400


@pytest.mark.asyncio
async def test_capture_referee_ucn_not_found(monkeypatch):
    conn = FakeAsyncConn(fetchrow_values=[None])
    patch_async_db(monkeypatch, conn)

    body, status = await rc.capture_referee_ucn(
        referral_track_id="t1",
        referee_ucn="123",
        tenant_code="FNB",
    )

    assert status == 404


@pytest.mark.asyncio
async def test_capture_referee_ucn_success(monkeypatch):
    conn = FakeAsyncConn(
        fetchrow_values=[
            {
                "product": "Transactional",
                "sub_product": "DDA",
                "tenant_code": "FNB",
                "tenant_is_active": True,
            }
        ]
    )
    patch_async_db(monkeypatch, conn)

    async def fake_handle_progress_event(req, tenant_code=None):
        return {}, 200

    monkeypatch.setattr(
        rc,
        "_identity_lookup_key",
        lambda x: "hash",
    )

    monkeypatch.setattr(
        rc,
        "handle_progress_event",
        fake_handle_progress_event,
    )

    body, status = await rc.capture_referee_ucn(
        referral_track_id="t1",
        referee_ucn="123",
        tenant_code="FNB",
    )

    assert status == 200
    assert body["error_code"] is None
