from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.main import app


client = TestClient(app)


def test_get_recommendations_success(monkeypatch):
    from apps.api.routers import recommendations as router

    monkeypatch.setattr(
        router,
        "generate_recommendations_for_referral",
        lambda referral_track_id, tenant_code=None, channel="API", audit=True: [
            {
                "recommendationId": "salary_switch_info",
                "category": "NEXT_BEST_ACTION",
                "title": "Salary switch is available",
                "body": "If you choose to switch your salary, you may qualify for a reward once the switch is completed successfully.",
                "ctaLabel": "Learn more",
                "ctaAction": "OPEN_INFO",
                "priority": 1,
                "rewardPreview": {
                    "amount": 200,
                    "currency": "ZAR",
                    "isConditional": True,
                    "conditionSummary": "Reward applies only after salary switch is completed successfully",
                },
                "disclosures": [
                    "This is general information and not personal financial advice.",
                    "Rewards are conditional and are only applied when the qualifying requirements have been met successfully.",
                ],
                "compliance": {
                    "isAdvice": False,
                    "isCreditRelated": False,
                    "requiresDisclaimer": True,
                    "disclaimerCodes": ["GENERAL_INFO_ONLY", "REWARD_CONDITIONAL"],
                    "regulatoryTags": ["TCF", "FAIS", "MARKET_CONDUCT", "BANKING_CODE"],
                    "pressureScore": 0,
                    "fairnessScore": 100,
                    "transparencyScore": 95,
                    "blocked": False,
                    "blockedReason": None,
                },
                "templateCode": "SALARY_SWITCH_INFO",
                "templateVersion": "v1.0",
                "policyVersion": "2026-04-08",
            }
        ],
    )

    response = client.get("/v1/recommendations/track-123",
    headers={"x-api-key": "test-partner-key"},
)

    assert response.status_code == 200
    body = response.json()

    assert body["referralTrackId"] == "track-123"
    assert body["count"] == 1
    assert len(body["items"]) == 1

    item = body["items"][0]
    assert item["recommendationId"] == "salary_switch_info"
    assert item["category"] == "NEXT_BEST_ACTION"
    assert item["ctaLabel"] == "Learn more"
    assert item["ctaAction"] == "OPEN_INFO"
    assert item["templateCode"] == "SALARY_SWITCH_INFO"
    assert item["templateVersion"] == "v1.0"
    assert item["policyVersion"] == "2026-04-08"

    assert item["rewardPreview"]["amount"] == 200
    assert item["rewardPreview"]["currency"] == "ZAR"
    assert item["rewardPreview"]["isConditional"] is True

    assert item["compliance"]["isAdvice"] is False
    assert item["compliance"]["requiresDisclaimer"] is True
    assert "GENERAL_INFO_ONLY" in item["compliance"]["disclaimerCodes"]
    assert "REWARD_CONDITIONAL" in item["compliance"]["disclaimerCodes"]
    assert "FAIS" in item["compliance"]["regulatoryTags"]

    assert len(item["disclosures"]) == 2


def test_get_recommendations_passes_audit_flag(monkeypatch):
    from apps.api.routers import recommendations as router

    captured = {}

    def fake_generate(referral_track_id, tenant_code=None, channel="API", audit=True):
        captured["referral_track_id"] = referral_track_id
        captured["channel"] = channel
        captured["audit"] = audit
        return [
            {
                "recommendationId": "progress_info",
                "category": "INFO",
                "title": "Your referral progress is available",
                "body": "You can view your current progress and reward conditions.",
                "ctaLabel": "View progress",
                "ctaAction": "VIEW_PROGRESS",
                "priority": 10,
                "rewardPreview": None,
                "disclosures": [
                    "This is general information and not personal financial advice."
                ],
                "compliance": {
                    "isAdvice": False,
                    "isCreditRelated": False,
                    "requiresDisclaimer": True,
                    "disclaimerCodes": ["GENERAL_INFO_ONLY"],
                    "regulatoryTags": ["TCF", "BANKING_CODE"],
                    "pressureScore": 0,
                    "fairnessScore": 100,
                    "transparencyScore": 98,
                    "blocked": False,
                    "blockedReason": None,
                },
                "templateCode": "PROGRESS_INFO",
                "templateVersion": "v1.0",
                "policyVersion": "2026-04-08",
            }
        ]

    monkeypatch.setattr(router, "generate_recommendations_for_referral", fake_generate)

    response = client.get("/v1/recommendations/track-456?audit=false",
    headers={"x-api-key": "test-partner-key"},
)

    assert response.status_code == 200
    assert captured["referral_track_id"] == "track-456"
    assert captured["channel"] == "API"
    assert captured["audit"] is False


def test_get_recommendations_returns_404_when_empty(monkeypatch):
    from apps.api.routers import recommendations as router

    monkeypatch.setattr(
        router,
        "generate_recommendations_for_referral",
        lambda referral_track_id, tenant_code=None, channel="API", audit=True: [],
    )

    response = client.get("/v1/recommendations/missing-track",
    headers={"x-api-key": "test-partner-key"},
)
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Referral not found or no recommendations available"