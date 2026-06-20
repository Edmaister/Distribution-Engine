"""Common dependencies for routers (DB, settings, auth placeholders)."""
from fastapi import Depends, Header, HTTPException
from .settings import get_settings, Settings

def get_tenant(settings: Settings = Depends(get_settings), x_tenant: str | None = Header(default=None)) -> str:
    """White-label tenant scoping via header; fallback to default."""
    return x_tenant or settings.tenant_default
