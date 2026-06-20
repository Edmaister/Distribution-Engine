from __future__ import annotations

"""
apps/api/routers/campaigns.py
"""

import json
import logging
from typing import Any, Dict, Tuple, Union

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse

from apps.api.schemas.campaigns import (
    CampaignCreateRequest,
    CampaignCreateResponse,
    CampaignPolicyUpsertRequest,
    CampaignTrackUpdateRequest,
    CampaignTrackUpdateResponse,
    CampaignValidateRequest,
    CampaignValidateResponse,
)
from services.campaign_policy_service import get_effective_policy
from services.campaign_service import (
    create_campaign,
    update_campaign_track_status,
    validate_campaign_and_create_track,
)
from utils.db import db_connection
from utils.security import require_admin_key, require_partner_key
from utils.tenant_guard import require_valid_tenant

logger = logging.getLogger(__name__)

public_router = APIRouter(prefix="/campaigns", tags=["Campaigns - Public"])

router = APIRouter(
    prefix="/campaigns",
    tags=["Campaigns"],
)


def _correlation_id(request: Request) -> str:
    return getattr(request.state, "correlation_id", "unknown")


def _error(request: Request, status_code: int, error_code: str, message: str):
    return JSONResponse(
        status_code=status_code,
        content={
            "detail": {
                "error_code": error_code,
                "message": message,
                "correlation_id": _correlation_id(request),
            }
        },
        headers={"X-Request-ID": _correlation_id(request)},
    )


def _unwrap_service_result(
    res: Union[Dict[str, Any], Tuple[Dict[str, Any], int]]
) -> Tuple[Dict[str, Any], int]:
    if isinstance(res, tuple) and len(res) == 2 and isinstance(res[0], dict):
        return res[0], int(res[1])

    if isinstance(res, dict):
        return res, int(res.get("status", 200))

    return {
        "error_code": "INTERNAL_ERROR",
        "message": "Service returned unexpected type",
    }, 500


def _row_get(row: Any, key_or_index: Any, default: Any = None) -> Any:
    try:
        return row[key_or_index]
    except Exception:
        return default


@router.post("", response_model=CampaignCreateResponse, status_code=201)
async def create_campaign_api(
    req: CampaignCreateRequest,
    response: Response,
    request: Request,
    identity=Depends(require_admin_key),
) -> Any:
    try:
        res = await create_campaign(
            tenant_code=require_valid_tenant(req.tenant_code),
            segment=req.segment,
            name=req.name,
            campaign_code=getattr(req, "campaign_code", None),
            starts_at=req.starts_at,
            ends_at=req.ends_at,
            max_uses=req.max_uses,
            attributes=req.attributes,
        )

        body, status_code = _unwrap_service_result(res)

        if body.get("ok") is False:
            return _error(
                request,
                status_code,
                body.get("error_code", "ERROR"),
                body.get("message", "Request failed"),
            )

        campaign_code = (
            body.get("campaign_code")
            or body.get("campaignCode")
            or (body.get("campaign") or {}).get("campaign_code")
            or (body.get("campaign") or {}).get("campaignCode")
        )

        if not campaign_code:
            return _error(request, 500, "INTERNAL_ERROR", "Service response invalid")

        response.status_code = status_code

        return CampaignCreateResponse(
            campaignCode=campaign_code,
            mode=body.get("mode") or body.get("create_mode"),
        )

    except ValueError as exc:
        return _error(request, 400, "VALIDATION_ERROR", str(exc))
    except Exception:
        logger.exception("Unexpected error creating campaign")
        return _error(request, 500, "INTERNAL_ERROR", "An unexpected error occurred")


@public_router.post("/validate", response_model=CampaignValidateResponse)
async def validate_campaign_api(
    req: CampaignValidateRequest,
    response: Response,
    request: Request,
) -> Any:
    try:
        res = await validate_campaign_and_create_track(
            tenant_code=require_valid_tenant(req.tenant_code),
            campaign_code=req.campaign_code,
            user_ucn_encrypted=req.user_ucn_encrypted,
            device_fingerprint=req.device_fingerprint,
            ip_address=req.ip_address,
            qr_payload=req.qr_payload,
            source_channel=req.source_channel,
            metadata=req.metadata,
        )

        body, status_code = _unwrap_service_result(res)
        response.status_code = status_code

        if "error_code" in body and "message" in body and body.get("ok") is False:
            return _error(
                request,
                status_code,
                body.get("error_code", "ERROR"),
                body.get("message", "Validation failed"),
            )

        return CampaignValidateResponse(**body)

    except ValueError as exc:
        return _error(request, 400, "VALIDATION_ERROR", str(exc))
    except Exception:
        logger.exception("Unexpected error validating campaign")
        return _error(request, 500, "INTERNAL_ERROR", "An unexpected error occurred")


@router.patch("/tracks/{campaign_track_id}", response_model=CampaignTrackUpdateResponse)
async def update_campaign_track_api(
    campaign_track_id: str,
    req: CampaignTrackUpdateRequest,
    response: Response,
    request: Request,
    identity=Depends(require_partner_key),
) -> Any:
    try:
        res = await update_campaign_track_status(
            campaign_track_id=campaign_track_id,
            status=req.status,
        )

        body, status_code = _unwrap_service_result(res)
        response.status_code = status_code

        if body.get("ok") is False or "error_code" in body:
            return _error(
                request,
                status_code,
                body.get("error_code", "ERROR"),
                body.get("message", "Track update failed"),
            )

        track_id = (
            body.get("campaignTrackId")
            or body.get("campaign_track_id")
            or campaign_track_id
        )
        new_status = (
            body.get("newStatus")
            or body.get("new_status")
            or body.get("status")
        )

        if not new_status:
            return _error(request, 500, "INTERNAL_ERROR", "Service response invalid")

        return CampaignTrackUpdateResponse(
            campaignTrackId=track_id,
            newStatus=new_status,
        )

    except ValueError as exc:
        return _error(request, 400, "VALIDATION_ERROR", str(exc))
    except Exception:
        logger.exception("Unexpected error updating campaign track")
        return _error(request, 500, "INTERNAL_ERROR", "An unexpected error occurred")


@router.get("/{campaign_code}/policy")
async def get_campaign_policy_api(
    campaign_code: str,
    response: Response,
    request: Request,
    identity=Depends(require_partner_key),
) -> Any:
    try:
        tenant_code = identity["tenant_code"]

        response.status_code = 200
        return await get_effective_policy(
            tenant=tenant_code,
            campaign_code=campaign_code,
        )

    except ValueError as exc:
        return _error(request, 400, "VALIDATION_ERROR", str(exc))
    except Exception:
        logger.exception("Unexpected error fetching campaign policy")
        return _error(request, 500, "INTERNAL_ERROR", "An unexpected error occurred")


@router.put("/{campaign_code}/policy")
async def upsert_campaign_policy_api(
    campaign_code: str,
    req: CampaignPolicyUpsertRequest,
    response: Response,
    request: Request,
    identity=Depends(require_admin_key),
) -> Any:
    try:
        tenant_code = require_valid_tenant(req.tenant_code)

        async with db_connection() as conn:
            async with conn.transaction():
                row = await conn.fetchrow(
                    """
                    INSERT INTO marketing_campaign_policies
                      (
                        campaign_code,
                        tenant_code,
                        version,
                        is_active,
                        rolling_window_days,
                        rules_json,
                        product_windows_json,
                        reward_amounts_json,
                        product_rules_json,
                        updated_at
                      )
                    VALUES
                      ($1, $2, $3, $4,
                       $5, $6::jsonb, $7::jsonb,
                       $8::jsonb, $9::jsonb, NOW())
                    ON CONFLICT (campaign_code, tenant_code, version)
                    DO UPDATE SET
                      is_active = EXCLUDED.is_active,
                      rolling_window_days = EXCLUDED.rolling_window_days,
                      rules_json = EXCLUDED.rules_json,
                      product_windows_json = EXCLUDED.product_windows_json,
                      reward_amounts_json = EXCLUDED.reward_amounts_json,
                      product_rules_json = EXCLUDED.product_rules_json,
                      updated_at = NOW()
                    RETURNING
                      campaign_code,
                      tenant_code,
                      version,
                      is_active,
                      rolling_window_days,
                      rules_json,
                      product_windows_json,
                      reward_amounts_json,
                      product_rules_json,
                      updated_at
                    """,
                    campaign_code,
                    tenant_code,
                    req.version,
                    req.is_active,
                    req.rolling_window_days,
                    json.dumps(req.rules_json or []),
                    json.dumps(req.product_windows_json or {}),
                    json.dumps(req.reward_amounts_json or {}),
                    json.dumps(req.product_rules_json or {}),
                )

        response.status_code = 200

        updated_at = _row_get(row, "updated_at", _row_get(row, 9))

        return {
            "campaign_code": _row_get(row, "campaign_code", _row_get(row, 0)),
            "tenant_code": _row_get(row, "tenant_code", _row_get(row, 1)),
            "version": _row_get(row, "version", _row_get(row, 2)),
            "is_active": _row_get(row, "is_active", _row_get(row, 3)),
            "rolling_window_days": _row_get(
                row,
                "rolling_window_days",
                _row_get(row, 4),
            ),
            "rules_json": _row_get(row, "rules_json", _row_get(row, 5)),
            "product_windows_json": _row_get(
                row,
                "product_windows_json",
                _row_get(row, 6),
            ),
            "reward_amounts_json": _row_get(
                row,
                "reward_amounts_json",
                _row_get(row, 7),
            ),
            "product_rules_json": _row_get(
                row,
                "product_rules_json",
                _row_get(row, 8),
            ),
            "updated_at": updated_at.isoformat() if updated_at else None,
        }

    except ValueError as exc:
        return _error(request, 400, "VALIDATION_ERROR", str(exc))
    except Exception:
        logger.exception("Unexpected error upserting campaign policy")
        return _error(request, 500, "INTERNAL_ERROR", "An unexpected error occurred")