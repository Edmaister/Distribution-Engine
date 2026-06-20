from __future__ import annotations

import datetime
import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from utils.db import db_connection

logger = logging.getLogger(__name__)

DEFAULT_POLICY_CODE = "DEFAULT_RECOMMENDATION_POLICY"
DEFAULT_POLICY_VERSION = "2026-04-08"


@dataclass
class RecommendationContext:
    referral_track_id: str
    status: str
    next_milestone: Optional[str]
    product: Optional[str]
    sub_product: Optional[str]
    progress_percent: Optional[int]
    is_complete: bool
    completed_at: Optional[datetime.datetime]
    journey_code: Optional[str] = None
    journey_version: Optional[str] = None
    reward_preview_amount: Optional[int] = None
    is_credit_related: bool = False


def _utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def _normalise_text(value: Optional[str]) -> str:
    return (value or "").strip()


def _milestone_to_display(value: Optional[str]) -> str:
    return _normalise_text(value).replace("_", " ").title()


def _to_json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, default=str)


async def _fetch_referral_context(
    referral_track_id: str,
) -> Optional[RecommendationContext]:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                referral_track_id,
                status,
                next_milestone,
                product,
                sub_product,
                journey_code,
                journey_version,
                progress_percent,
                is_complete,
                completed_at
            FROM referral_instances
            WHERE referral_track_id = $1
            """,
            referral_track_id,
        )

    if not row:
        return None

    next_milestone = row["next_milestone"]
    reward_preview_amount = _infer_reward_preview_amount(
        next_milestone=next_milestone,
    )

    return RecommendationContext(
        referral_track_id=str(row["referral_track_id"]),
        status=row["status"] or "VALIDATED",
        next_milestone=next_milestone,
        product=row["product"],
        sub_product=row["sub_product"],
        journey_code=row.get("journey_code"),
        journey_version=row.get("journey_version"),
        progress_percent=row["progress_percent"],
        is_complete=bool(row["is_complete"]),
        completed_at=row["completed_at"],
        reward_preview_amount=reward_preview_amount,
        is_credit_related=False,
    )


def _infer_reward_preview_amount(
    next_milestone: Optional[str],
) -> Optional[int]:
    if next_milestone in {"SALARY_SWITCHED", "DEBIT_ORDER_SWITCHED"}:
        return 200

    if next_milestone == "FIRST_TRANSACTION_COMPLETED":
        return 100

    if next_milestone in {"POLICY_ISSUED", "FIRST_PREMIUM_PAID"}:
        return 250

    return None


def _default_policy() -> Dict[str, Any]:
    return {
        "policy_code": DEFAULT_POLICY_CODE,
        "policy_version": DEFAULT_POLICY_VERSION,
        "banned_phrases": [
            "do this now",
            "must do",
            "guaranteed reward",
            "best option for you",
            "you should choose",
            "earn now",
            "instant cash",
        ],
        "advisory_markers": [
            "best for you",
            "suitable for you",
            "recommended for your needs",
            "based on your circumstances",
        ],
        "pressure_markers": [
            "now",
            "immediately",
            "urgent",
            "don't miss out",
            "last chance",
        ],
        "blocked_ctas": [
            "Claim now",
            "Earn now",
            "Take offer now",
        ],
        "allowed_ctas": [
            "Learn more",
            "View details",
            "See eligibility",
            "Start application",
            "View progress",
        ],
    }


async def _get_active_policy(
    policy_code: str = DEFAULT_POLICY_CODE,
) -> Dict[str, Any]:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                policy_code,
                policy_version,
                banned_phrases,
                advisory_markers,
                pressure_markers,
                blocked_ctas,
                allowed_ctas
            FROM recommendation_compliance_policies
            WHERE policy_code = $1
              AND is_active = TRUE
            ORDER BY created_at DESC
            LIMIT 1
            """,
            policy_code,
        )

    if row:
        return dict(row)

    return _default_policy()


async def _get_template(
    template_code: str,
) -> Optional[Dict[str, Any]]:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                template_code,
                category,
                title_template,
                body_template,
                cta_label,
                cta_action,
                is_credit_related,
                requires_disclaimer,
                regulatory_tags,
                template_version
            FROM recommendation_templates
            WHERE template_code = $1
              AND is_active = TRUE
            ORDER BY created_at DESC
            LIMIT 1
            """,
            template_code,
        )

    return dict(row) if row else None


async def _get_disclosures(
    disclosure_codes: List[str],
) -> List[str]:
    if not disclosure_codes:
        return []

    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT disclosure_code, disclosure_text
            FROM disclosure_library
            WHERE disclosure_code = ANY($1::text[])
              AND is_active = TRUE
            ORDER BY disclosure_code
            """,
            disclosure_codes,
        )

    text_by_code = {
        row["disclosure_code"]: row["disclosure_text"]
        for row in rows or []
    }

    return [
        text_by_code[code]
        for code in disclosure_codes
        if code in text_by_code
    ]


async def _record_display_audit(
    referral_track_id: str,
    recommendation: Dict[str, Any],
    channel: str,
) -> None:
    async with db_connection() as conn:
        async with conn.transaction():
            await conn.execute(
                """
                INSERT INTO recommendation_display_audit (
                    referral_track_id,
                    recommendation_id,
                    template_code,
                    template_version,
                    policy_version,
                    category,
                    title,
                    body,
                    cta_label,
                    cta_action,
                    reward_preview_json,
                    compliance_json,
                    disclosures_json,
                    channel,
                    shown_at
                )
                VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                    $11::jsonb, $12::jsonb, $13::jsonb, $14, NOW()
                )
                """,
                referral_track_id,
                recommendation["recommendationId"],
                recommendation["templateCode"],
                recommendation["templateVersion"],
                recommendation["policyVersion"],
                recommendation["category"],
                recommendation["title"],
                recommendation["body"],
                recommendation["ctaLabel"],
                recommendation["ctaAction"],
                _to_json(recommendation.get("rewardPreview")),
                _to_json(recommendation.get("compliance")),
                _to_json(recommendation.get("disclosures", [])),
                channel,
            )


def _build_candidates(
    context: RecommendationContext,
) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []

    if context.is_complete:
        items.append(
            {
                "recommendationId": (
                    "insurance_progress_complete_info"
                    if context.journey_code == "INSURANCE_POLICY"
                    else "progress_complete_info"
                ),
                "templateCode": (
                    "INSURANCE_POLICY_COMPLETE_INFO"
                    if context.journey_code == "INSURANCE_POLICY"
                    else "PROGRESS_COMPLETE_INFO"
                ),
                "category": "INFO",
                "priority": 5,
            }
        )
        return items

    if context.journey_code == "INSURANCE_POLICY":
        if context.next_milestone == "QUOTE_ACCEPTED":
            items.append(
                {
                    "recommendationId": "insurance_quote_acceptance_info",
                    "templateCode": "INSURANCE_QUOTE_ACCEPTANCE_INFO",
                    "category": "NEXT_BEST_ACTION",
                    "priority": 1,
                }
            )

        if context.next_milestone in {"POLICY_ISSUED", "FIRST_PREMIUM_PAID"}:
            items.append(
                {
                    "recommendationId": "insurance_policy_activation_info",
                    "templateCode": "INSURANCE_POLICY_ACTIVATION_INFO",
                    "category": "NEXT_BEST_ACTION",
                    "priority": 1,
                }
            )

        items.append(
            {
                "recommendationId": "insurance_progress_info",
                "templateCode": "INSURANCE_PROGRESS_INFO",
                "category": "INFO",
                "priority": 10,
            }
        )

        return items

    if context.next_milestone == "SALARY_SWITCHED":
        items.append(
            {
                "recommendationId": "salary_switch_info",
                "templateCode": "SALARY_SWITCH_INFO",
                "category": "NEXT_BEST_ACTION",
                "priority": 1,
            }
        )

    if context.next_milestone == "DEBIT_ORDER_SWITCHED":
        items.append(
            {
                "recommendationId": "debit_order_switch_info",
                "templateCode": "DEBIT_ORDER_SWITCH_INFO",
                "category": "NEXT_BEST_ACTION",
                "priority": 1,
            }
        )

    if context.next_milestone == "FIRST_TRANSACTION_COMPLETED":
        items.append(
            {
                "recommendationId": "first_transaction_info",
                "templateCode": "FIRST_TRANSACTION_INFO",
                "category": "NEXT_BEST_ACTION",
                "priority": 2,
            }
        )

    if context.status in {
        "VALIDATED",
        "UCN_CAPTURED",
        "ACCOUNT_OPENED",
        "ACCOUNT_ACTIVATED",
        "FUNDED",
    }:
        items.append(
            {
                "recommendationId": "progress_info",
                "templateCode": "PROGRESS_INFO",
                "category": "INFO",
                "priority": 10,
            }
        )

    return items


async def _render_candidate(
    candidate: Dict[str, Any],
    context: RecommendationContext,
) -> Optional[Dict[str, Any]]:
    template = await _get_template(candidate["templateCode"])

    if not template:
        logger.warning(
            "recommendation_template_missing template_code=%s",
            candidate["templateCode"],
        )
        return None

    next_milestone_display = _milestone_to_display(context.next_milestone)

    title = template["title_template"].format(
        next_milestone=next_milestone_display,
        reward_amount=context.reward_preview_amount or 0,
    )

    body = template["body_template"].format(
        next_milestone=next_milestone_display.lower(),
        reward_amount=context.reward_preview_amount or 0,
    )

    return {
        "recommendationId": candidate["recommendationId"],
        "category": candidate["category"],
        "title": title,
        "body": body,
        "ctaLabel": template["cta_label"],
        "ctaAction": template["cta_action"],
        "priority": candidate["priority"],
        "rewardPreview": _reward_preview(context),
        "disclosures": [],
        "compliance": {},
        "templateCode": template["template_code"],
        "templateVersion": template["template_version"],
        "policyVersion": DEFAULT_POLICY_VERSION,
    }


def _reward_preview(
    context: RecommendationContext,
) -> Optional[Dict[str, Any]]:
    if not context.reward_preview_amount:
        return None

    condition = "qualifying requirements are met successfully"

    if context.next_milestone == "SALARY_SWITCHED":
        condition = "salary switch is completed successfully"
    elif context.next_milestone == "DEBIT_ORDER_SWITCHED":
        condition = "debit order switch is completed successfully"
    elif context.next_milestone == "FIRST_TRANSACTION_COMPLETED":
        condition = "first qualifying transaction is completed successfully"

    return {
        "amount": context.reward_preview_amount,
        "currency": "ZAR",
        "isConditional": True,
        "conditionSummary": f"Reward applies only after {condition}",
    }


def _classify_risk(
    recommendation: Dict[str, Any],
    policy: Dict[str, Any],
) -> Dict[str, Any]:
    combined_text = " ".join(
        [
            recommendation.get("title", ""),
            recommendation.get("body", ""),
            recommendation.get("ctaLabel", ""),
        ]
    ).lower()

    banned_phrases = [
        str(x).lower()
        for x in (policy.get("banned_phrases") or [])
    ]
    advisory_markers = [
        str(x).lower()
        for x in (policy.get("advisory_markers") or [])
    ]
    pressure_markers = [
        str(x).lower()
        for x in (policy.get("pressure_markers") or [])
    ]
    blocked_ctas = [
        str(x).lower()
        for x in (policy.get("blocked_ctas") or [])
    ]

    for phrase in banned_phrases:
        if phrase and phrase in combined_text:
            return {
                "blocked": True,
                "blockedReason": f"banned_phrase:{phrase}",
                "isAdvice": False,
                "pressureScore": 0,
            }

    for phrase in advisory_markers:
        if phrase and phrase in combined_text:
            return {
                "blocked": True,
                "blockedReason": f"advice_marker:{phrase}",
                "isAdvice": True,
                "pressureScore": 0,
            }

    if recommendation.get("ctaLabel", "").lower() in blocked_ctas:
        return {
            "blocked": True,
            "blockedReason": f"blocked_cta:{recommendation.get('ctaLabel')}",
            "isAdvice": False,
            "pressureScore": 0,
        }

    pressure_score = sum(
        1
        for marker in pressure_markers
        if marker and marker in combined_text
    )

    return {
        "blocked": False,
        "blockedReason": None,
        "isAdvice": False,
        "pressureScore": pressure_score,
    }


def _rewrite_to_safe_language(
    recommendation: Dict[str, Any],
) -> Dict[str, Any]:
    body = recommendation.get("body", "")
    title = recommendation.get("title", "")

    replacements = {
        "Do this now": "This option is available",
        "do this now": "this option is available",
        "must do": "may choose to",
        "Guaranteed reward": "You may qualify for a reward",
        "guaranteed reward": "you may qualify for a reward",
        "Earn now": "You may qualify for a reward",
        "earn now": "you may qualify for a reward",
        "urgent": "available",
        "immediately": "",
        "best option for you": "available option",
        "you should choose": "you may choose to consider",
    }

    for source, target in replacements.items():
        title = title.replace(source, target)
        body = body.replace(source, target)

    recommendation["title"] = " ".join(title.split())
    recommendation["body"] = " ".join(body.split())
    recommendation["ctaLabel"] = "Learn more"
    recommendation["ctaAction"] = "OPEN_INFO"

    return recommendation


def _build_compliance_metadata(
    context: RecommendationContext,
    risk: Dict[str, Any],
) -> Dict[str, Any]:
    disclaimer_codes = ["GENERAL_INFO_ONLY"]
    regulatory_tags = ["TCF", "FAIS", "MARKET_CONDUCT", "BANKING_CODE"]

    if context.reward_preview_amount:
        disclaimer_codes.append("REWARD_CONDITIONAL")

    if context.journey_code == "INSURANCE_POLICY":
        disclaimer_codes.append("INSURANCE_PRODUCT_INFO")
        regulatory_tags = ["TCF", "FAIS", "MARKET_CONDUCT", "INSURANCE_CONDUCT"]

    if context.is_credit_related:
        disclaimer_codes.append("CREDIT_DISCLOSURE")
        regulatory_tags.append("NCA")

    pressure_score = int(risk.get("pressureScore", 0))
    fairness_score = max(0, 100 - (pressure_score * 10))
    transparency_score = 95 if context.reward_preview_amount else 98

    return {
        "isAdvice": bool(risk.get("isAdvice", False)),
        "isCreditRelated": context.is_credit_related,
        "requiresDisclaimer": True,
        "disclaimerCodes": disclaimer_codes,
        "regulatoryTags": regulatory_tags,
        "pressureScore": pressure_score,
        "fairnessScore": fairness_score,
        "transparencyScore": transparency_score,
        "blocked": False,
        "blockedReason": None,
    }


async def generate_recommendations_for_referral(
    referral_track_id: str,
    channel: str = "API",
    audit: bool = True,
) -> List[Dict[str, Any]]:
    context = await _fetch_referral_context(referral_track_id)

    if not context:
        return []

    policy = await _get_active_policy()
    candidates = _build_candidates(context)

    output: List[Dict[str, Any]] = []

    for candidate in candidates:
        rendered = await _render_candidate(candidate, context)

        if not rendered:
            continue

        risk = _classify_risk(rendered, policy)

        if risk["blocked"]:
            rendered = _rewrite_to_safe_language(rendered)
            risk = _classify_risk(rendered, policy)

        if risk["blocked"]:
            logger.warning(
                "recommendation_blocked referral_track_id=%s recommendation_id=%s reason=%s",
                referral_track_id,
                rendered.get("recommendationId"),
                risk.get("blockedReason"),
            )
            continue

        compliance = _build_compliance_metadata(context, risk)
        disclosures = await _get_disclosures(compliance["disclaimerCodes"])

        rendered["compliance"] = compliance
        rendered["disclosures"] = disclosures
        rendered["policyVersion"] = policy.get(
            "policy_version",
            DEFAULT_POLICY_VERSION,
        )

        if audit:
            await _record_display_audit(
                referral_track_id=referral_track_id,
                recommendation=rendered,
                channel=channel,
            )

        output.append(rendered)

    output.sort(
        key=lambda item: (
            item["priority"],
            item["recommendationId"],
        )
    )

    return output
