from __future__ import annotations

from decimal import Decimal

from services.distribution.routing_service import score_distributor_for_opportunity


def test_score_distributor_for_opportunity_full_match():
    result = score_distributor_for_opportunity(
        opportunity={
            "distributor_types": ["AGENCY"],
            "target_segments": ["MASS_MARKET"],
            "target_regions": ["ZA-GP"],
            "target_channels": ["FIELD"],
        },
        distributor={
            "distributor_type": "AGENCY",
            "segments": ["MASS_MARKET", "SME"],
            "regions": ["ZA-GP"],
            "channels": ["FIELD", "WHATSAPP"],
        },
    )

    assert result == {
        "eligible": True,
        "route_score": Decimal("100"),
        "route_reasons": [
            "distributor_type: matched AGENCY",
            "segment: matched MASS_MARKET",
            "region: matched ZA-GP",
            "channel: matched FIELD",
        ],
    }


def test_score_distributor_for_opportunity_blocks_required_miss():
    result = score_distributor_for_opportunity(
        opportunity={
            "distributor_types": ["AGENCY"],
            "target_segments": ["MASS_MARKET"],
            "target_regions": ["ZA-GP"],
            "target_channels": ["FIELD"],
        },
        distributor={
            "distributor_type": "CALL_CENTRE",
            "segments": ["MASS_MARKET"],
            "regions": ["ZA-GP"],
            "channels": ["FIELD"],
        },
    )

    assert result["eligible"] is False
    assert result["route_score"] == Decimal("70")
    assert "distributor_type: no match" in result["route_reasons"]


def test_score_distributor_for_opportunity_treats_empty_targets_as_wildcards():
    result = score_distributor_for_opportunity(
        opportunity={
            "distributor_types": [],
            "target_segments": [],
            "target_regions": [],
            "target_channels": [],
        },
        distributor={
            "distributor_type": "AGENCY",
            "segments": [],
            "regions": [],
            "channels": [],
        },
    )

    assert result["eligible"] is True
    assert result["route_score"] == Decimal("100")
    assert result["route_reasons"] == [
        "distributor_type: wildcard",
        "segment: wildcard",
        "region: wildcard",
        "channel: wildcard",
    ]
