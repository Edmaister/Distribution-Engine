from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, Field, HttpUrl

from services import partner_seam_service
from utils.security import require_partner_identity, require_system_admin_key


router = APIRouter(tags=["Partner Seam"])


class PartnerClientCreateRequest(BaseModel):
    tenant_code: str = Field(..., min_length=2, max_length=20)
    client_name: str = Field(..., min_length=2, max_length=120)
    scopes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TokenRequest(BaseModel):
    grant_type: str = Field("client_credentials")
    client_id: str
    client_secret: str
    scope: str | None = None


class WebhookSubscriptionCreateRequest(BaseModel):
    event_type: str = Field(..., min_length=2, max_length=120)
    target_url: HttpUrl
    metadata: dict[str, Any] = Field(default_factory=dict)


class WebhookDeliveryQueueRequest(BaseModel):
    tenant_code: str = Field(..., min_length=2, max_length=20)
    event_type: str = Field(..., min_length=2, max_length=120)
    payload: dict[str, Any] = Field(default_factory=dict)


@router.post("/oauth/token")
async def issue_token(request: TokenRequest) -> dict[str, Any]:
    if request.grant_type != "client_credentials":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only client_credentials grant_type is supported",
        )

    return await partner_seam_service.issue_client_credentials_token(
        client_id=request.client_id,
        client_secret=request.client_secret,
        scope=request.scope,
    )


@router.get("/partner/me")
async def get_partner_identity(
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    identity = await partner_seam_service.authenticate_partner_access_token(
        authorization
    )
    return {
        "status": "ok",
        "identity": identity,
    }


@router.get("/partner/integration")
async def get_partner_integration(
    identity: dict[str, Any] = Depends(require_partner_identity),
) -> dict[str, Any]:
    integration = await partner_seam_service.get_partner_integration_overview(identity)
    return {
        "status": "ok",
        "integration": integration,
    }


@router.get("/partner/readiness")
async def get_partner_readiness(
    identity: dict[str, Any] = Depends(require_partner_identity),
) -> dict[str, Any]:
    return {
        "status": "ok",
        "identity": {
            "tenant_code": identity.get("tenant_code") or identity.get("tenant"),
            "client_id": identity.get("client_id"),
            "role": identity.get("role"),
        },
        "readiness": partner_seam_service.get_partner_seam_production_readiness(),
    }


@router.post("/partner/clients")
async def create_partner_client_self_service(
    request: PartnerClientCreateRequest,
    identity: dict[str, Any] = Depends(require_partner_identity),
) -> dict[str, Any]:
    try:
        client = await partner_seam_service.create_partner_client_for_identity(
            identity=identity,
            client_name=request.client_name,
            scopes=request.scopes,
            metadata=request.metadata,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    return {
        "status": "created",
        "client": client,
        "guardrail": "Store client_secret securely. It is only returned once.",
    }


@router.post("/partner/webhooks")
async def create_partner_webhook(
    request: WebhookSubscriptionCreateRequest,
    identity: dict[str, Any] = Depends(require_partner_identity),
) -> dict[str, Any]:
    try:
        webhook = await partner_seam_service.create_partner_webhook_subscription(
            identity=identity,
            event_type=request.event_type,
            target_url=str(request.target_url),
            metadata=request.metadata,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    return {
        "status": "created",
        "webhook": webhook,
        "guardrail": "Store signing_secret securely. It is only returned once.",
    }


@router.post("/partner/webhooks/{webhook_id}/rotate-secret")
async def rotate_partner_webhook_secret(
    webhook_id: str,
    identity: dict[str, Any] = Depends(require_partner_identity),
) -> dict[str, Any]:
    webhook = await partner_seam_service.rotate_partner_webhook_signing_secret(
        identity=identity,
        webhook_id=webhook_id,
    )
    return {
        "status": "rotated",
        "webhook": webhook,
        "guardrail": "Replace the old endpoint secret with this new value before expecting signed deliveries.",
    }


@router.post("/partner/webhooks/rotate-legacy-secrets")
async def rotate_partner_legacy_webhook_secrets(
    limit: int = Query(default=25, ge=1, le=100),
    identity: dict[str, Any] = Depends(require_partner_identity),
) -> dict[str, Any]:
    rotation = await partner_seam_service.rotate_partner_legacy_webhook_secrets(
        identity=identity,
        limit=limit,
    )
    return {
        **rotation,
        "guardrail": "Store each returned signing_secret securely. These values are only returned once.",
    }


@router.get("/partner/webhook-deliveries/exceptions")
async def list_partner_webhook_exceptions(
    limit: int = Query(default=100, ge=1, le=500),
    identity: dict[str, Any] = Depends(require_partner_identity),
) -> dict[str, Any]:
    exceptions = await partner_seam_service.list_partner_webhook_exceptions(
        identity=identity,
        limit=limit,
    )
    return {
        "status": "ok",
        "count": len(exceptions),
        "items": exceptions,
        "guardrail": "Only failed or cancelled delivery rows are returned.",
    }


@router.get("/partner/webhook-deliveries/alerts")
async def get_partner_webhook_alerts(
    limit: int = Query(default=100, ge=1, le=500),
    identity: dict[str, Any] = Depends(require_partner_identity),
) -> dict[str, Any]:
    alerts = await partner_seam_service.get_partner_webhook_delivery_alerts(
        identity=identity,
        limit=limit,
    )
    return {
        "status": "ok",
        "count": len(alerts),
        "items": alerts,
        "guardrail": "Alerts are derived from failed and cancelled webhook delivery evidence.",
    }


@router.get("/partner/webhooks/secret-readiness")
async def get_partner_webhook_secret_readiness(
    identity: dict[str, Any] = Depends(require_partner_identity),
) -> dict[str, Any]:
    readiness = await partner_seam_service.get_partner_webhook_secret_readiness(
        identity=identity,
    )
    return {
        "status": "ok",
        "readiness": readiness,
        "guardrail": "Secret readiness reports protection state only; secret values are never returned.",
    }


@router.get("/partner/webhook-deliveries/dead-letter-export")
async def export_partner_webhook_dead_letters(
    limit: int = Query(default=500, ge=1, le=5000),
    identity: dict[str, Any] = Depends(require_partner_identity),
) -> dict[str, Any]:
    export = await partner_seam_service.export_partner_webhook_dead_letters(
        identity=identity,
        limit=limit,
    )
    return {
        "status": "ok",
        "export": export,
    }


@router.post("/partner/webhook-deliveries/{delivery_id}/retry")
async def retry_partner_webhook_delivery(
    delivery_id: str,
    identity: dict[str, Any] = Depends(require_partner_identity),
) -> dict[str, Any]:
    delivery = await partner_seam_service.mark_partner_webhook_delivery_for_retry(
        identity=identity,
        delivery_id=delivery_id,
    )
    return {
        "status": "queued",
        "delivery": delivery,
        "guardrail": "Retry is limited to failed or cancelled deliveries owned by this partner client.",
    }


admin_router = APIRouter(
    prefix="/admin/partners",
    tags=["Admin Partner Seam"],
    dependencies=[Depends(require_system_admin_key)],
)


@admin_router.post("/clients")
async def create_client(request: PartnerClientCreateRequest) -> dict[str, Any]:
    try:
        client = await partner_seam_service.create_partner_client(
            tenant_code=request.tenant_code,
            client_name=request.client_name,
            scopes=request.scopes,
            metadata=request.metadata,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    return {
        "status": "created",
        "client": client,
        "guardrail": "Store client_secret securely. It is only returned once.",
    }


@admin_router.get("/clients")
async def list_clients(
    tenant_code: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=500),
) -> dict[str, Any]:
    clients = await partner_seam_service.list_partner_clients(
        tenant_code=tenant_code,
        status_filter=status_filter,
        limit=limit,
    )
    return {
        "status": "ok",
        "count": len(clients),
        "items": clients,
    }


@admin_router.get("/readiness")
async def get_admin_partner_readiness() -> dict[str, Any]:
    return {
        "status": "ok",
        "readiness": partner_seam_service.get_partner_seam_production_readiness(),
    }


@admin_router.post("/clients/{client_id}/webhooks")
async def create_webhook(
    client_id: str,
    request: WebhookSubscriptionCreateRequest,
) -> dict[str, Any]:
    try:
        webhook = await partner_seam_service.create_webhook_subscription(
            client_id=client_id,
            event_type=request.event_type,
            target_url=str(request.target_url),
            metadata=request.metadata,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    return {
        "status": "created",
        "webhook": webhook,
        "guardrail": "Store signing_secret securely. It is only returned once.",
    }


@admin_router.post("/webhook-deliveries")
async def queue_delivery(request: WebhookDeliveryQueueRequest) -> dict[str, Any]:
    deliveries = await partner_seam_service.queue_webhook_deliveries(
        tenant_code=request.tenant_code,
        event_type=request.event_type,
        payload=request.payload,
    )
    return {
        "status": "queued",
        "count": len(deliveries),
        "items": deliveries,
    }


@admin_router.get("/webhook-deliveries")
async def list_deliveries(
    tenant_code: str | None = Query(default=None),
    client_id: str | None = Query(default=None),
    delivery_status: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=500),
) -> dict[str, Any]:
    deliveries = await partner_seam_service.list_webhook_deliveries(
        tenant_code=tenant_code,
        client_id=client_id,
        delivery_status=delivery_status,
        limit=limit,
    )
    return {
        "status": "ok",
        "count": len(deliveries),
        "items": deliveries,
    }


@admin_router.get("/webhook-deliveries/summary")
async def get_delivery_summary(
    tenant_code: str | None = Query(default=None),
    hours: int = Query(default=24, ge=1, le=168),
) -> dict[str, Any]:
    summary = await partner_seam_service.get_webhook_delivery_summary(
        tenant_code=tenant_code,
        hours=hours,
    )
    return {
        "status": "ok",
        "summary": summary,
    }


@admin_router.get("/webhook-deliveries/alerts")
async def get_admin_webhook_alerts(
    tenant_code: str | None = Query(default=None),
    client_id: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> dict[str, Any]:
    alerts = await partner_seam_service.get_admin_partner_webhook_delivery_alerts(
        tenant_code=tenant_code,
        client_id=client_id,
        limit=limit,
    )
    return {
        "status": "ok",
        "count": len(alerts),
        "items": alerts,
        "guardrail": "Alerts are derived from failed and cancelled webhook delivery evidence.",
    }


@admin_router.post("/webhook-deliveries/alerts/notify")
async def notify_admin_webhook_alerts(
    tenant_code: str | None = Query(default=None),
    client_id: str | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=100),
    channel: str = Query(default="IN_APP"),
) -> dict[str, Any]:
    try:
        return await partner_seam_service.notify_partner_webhook_delivery_alerts(
            tenant_code=tenant_code,
            client_id=client_id,
            limit=limit,
            channel=channel,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc


@admin_router.post("/webhook-deliveries/process")
async def process_deliveries(
    limit: int = Query(default=25, ge=1, le=100),
) -> dict[str, Any]:
    return await partner_seam_service.process_pending_webhook_deliveries(limit=limit)


@admin_router.post("/webhook-deliveries/{delivery_id}/retry")
async def retry_delivery(
    delivery_id: str,
    identity: dict[str, Any] = Depends(require_system_admin_key),
) -> dict[str, Any]:
    delivery = await partner_seam_service.mark_webhook_delivery_for_retry(
        delivery_id=delivery_id,
        identity=identity,
    )
    return {
        "status": "queued",
        "delivery": delivery,
        "guardrail": "Retry is audited and limited to failed or cancelled deliveries.",
    }
