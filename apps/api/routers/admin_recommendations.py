import logging

from fastapi import APIRouter, Depends, Path, Query, Request
from fastapi.responses import JSONResponse

from services.recommendation_service import compute_campaign_insights
from utils.db import get_async_connection
from utils.security import require_admin_key
from utils.tenant_guard import require_valid_tenant

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin/recommendations",
    tags=["admin-recommendations"],
    dependencies=[Depends(require_admin_key)],
)


def _correlation_id(request: Request) -> str:
    return getattr(request.state, "correlation_id", "unknown")


def _error(
    request: Request,
    status_code: int,
    error_code: str,
    message: str,
):
    correlation_id = _correlation_id(request)

    return JSONResponse(
        status_code=status_code,
        content={
            "detail": {
                "error_code": error_code,
                "message": message,
                "correlation_id": correlation_id,
            }
        },
        headers={"X-Request-ID": correlation_id},
    )


@router.get("/campaigns/{campaign_code}")
async def campaign_insights(
    request: Request,
    campaign_code: str = Path(..., description="Campaign code"),
    sticker: str | None = Query(None),
    tenant_code: str | None = Query(
        None,
        description="Optional tenant code filter",
    ),
    prefer_cache: bool = Query(True),
):
    validated_tenant_code = None

    if tenant_code:
        validated_tenant_code = require_valid_tenant(
            tenant_code
        )

    if prefer_cache:
        try:
            async with get_async_connection() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT
                        metrics,
                        generated_at,
                        ttl_seconds
                    FROM campaign_insights_cache
                    WHERE campaign_code = $1
                    """,
                    campaign_code,
                )

            if row:
                return {
                    "campaignCode": campaign_code,
                    "tenantCode": validated_tenant_code,
                    "metrics": row["metrics"],
                    "cachedAt": row["generated_at"],
                    "ttlSeconds": int(
                        row["ttl_seconds"] or 0
                    ),
                    "source": "cache",
                }

        except Exception:
            logger.exception(
                (
                    "Failed to fetch campaign "
                    "insights cache | "
                    "correlation_id=%s | "
                    "campaign_code=%s | "
                    "tenant_code=%s"
                ),
                _correlation_id(request),
                campaign_code,
                validated_tenant_code,
            )

            return _error(
                request,
                500,
                "INTERNAL_ERROR",
                "An unexpected error occurred",
            )

    try:
        entry = await compute_campaign_insights(
            campaign_code,
            sticker=sticker,
            tenant=validated_tenant_code,
        )

        return {
            "campaignCode": campaign_code,
            "tenantCode": validated_tenant_code,
            "metrics": entry.get("metrics"),
            "source": "live",
        }

    except Exception:
        logger.exception(
            (
                "Failed to compute campaign "
                "insights | "
                "correlation_id=%s | "
                "campaign_code=%s | "
                "tenant_code=%s"
            ),
            _correlation_id(request),
            campaign_code,
            validated_tenant_code,
        )

        return _error(
            request,
            500,
            "INTERNAL_ERROR",
            "An unexpected error occurred",
        )