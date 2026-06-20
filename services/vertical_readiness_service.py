from __future__ import annotations

from typing import Any

from services.journey_definitions import JOURNEY_DEFINITIONS
from services.progress_definitions import PROGRESS_DEFINITIONS
from services.vertical_catalog_service import list_vertical_configs
from services.vertical_identifier_service import get_identifier_requirements
from services.vertical_regulatory_overlay_service import get_regulatory_overlay


def get_vertical_readiness() -> dict[str, Any]:
    items = []

    for vertical in list_vertical_configs():
        vertical_data = vertical.as_dict()
        journey_key = vertical.journey_key
        journey_definition = JOURNEY_DEFINITIONS.get(journey_key)
        progress_definition = PROGRESS_DEFINITIONS.get(journey_key)
        has_journey = journey_definition is not None
        has_progress = progress_definition is not None
        has_identifier_validation = bool(
            get_identifier_requirements(vertical.journey_code, vertical.journey_version)
        )
        has_reward_policy = bool(vertical.reward_policy)
        has_leaderboard_scoring = bool(vertical.leaderboard_code)
        has_fulfilment_route = bool(vertical.fulfilment_route.provider_key)
        regulatory_overlay = get_regulatory_overlay(vertical.journey_code, vertical.journey_version)
        has_regulatory_overlay = regulatory_overlay is not None
        configured = (
            has_journey
            and has_progress
            and has_identifier_validation
            and has_reward_policy
            and has_leaderboard_scoring
            and has_fulfilment_route
            and has_regulatory_overlay
        )
        missing_components = [
            label
            for label, present in [
                ("journey_definition", has_journey),
                ("progress_definition", has_progress),
                ("identifier_validation", has_identifier_validation),
                ("reward_policy", has_reward_policy),
                ("leaderboard_scoring", has_leaderboard_scoring),
                ("fulfilment_route", has_fulfilment_route),
                ("regulatory_overlay", has_regulatory_overlay),
            ]
            if not present
        ]

        items.append(
            {
                "vertical_code": vertical.vertical_code,
                "name": vertical.name,
                "product": vertical.product,
                "journey_code": vertical.journey_code,
                "journey_version": vertical.journey_version,
                "configured": configured,
                "status": "CONFIGURED" if configured else "INCOMPLETE",
                "commercial_status": "CONFIGURED" if has_reward_policy and has_leaderboard_scoring else "INCOMPLETE",
                "identifier_validation_configured": has_identifier_validation,
                "reward_policy": vertical.reward_policy,
                "leaderboard_code": vertical.leaderboard_code,
                "fulfilment_route": vertical_data["fulfilment_route"],
                "fulfilment_route_configured": has_fulfilment_route,
                "regulatory_overlay_configured": has_regulatory_overlay,
                "regulatory_policy_code": regulatory_overlay.policy_code if regulatory_overlay else None,
                "regulatory_disclosure_codes": list(regulatory_overlay.disclosure_codes) if regulatory_overlay else [],
                "regulatory_template_codes": list(regulatory_overlay.template_codes) if regulatory_overlay else [],
                "regulatory_tags": list(regulatory_overlay.regulatory_tags) if regulatory_overlay else [],
                "reward_policy_configured": has_reward_policy,
                "leaderboard_scoring_configured": has_leaderboard_scoring,
                "identifier_model": vertical.identifier_model,
                "regulatory_overlay": vertical.regulatory_overlay,
                "missing_components": missing_components,
                "configuration_source": "vertical_catalog",
                "journey_steps": journey_definition.core_sequence if journey_definition else [],
                "completion_events": sorted(journey_definition.completion_events) if journey_definition else [],
                "progress_milestones": list(progress_definition.milestones.keys()) if progress_definition else [],
            }
        )

    configured_count = sum(1 for item in items if item["configured"])

    return {
        "vertical_count": len(items),
        "configured_count": configured_count,
        "agnostic_ready": configured_count >= 2,
        "configuration_source": "vertical_catalog",
        "items": items,
    }
