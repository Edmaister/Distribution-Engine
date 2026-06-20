from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from utils.security import require_admin_key
from services.tenant_service import create_tenant, get_tenant

router = APIRouter(
    prefix="/admin/tenants",
    tags=["admin-tenants"],
    dependencies=[Depends(require_admin_key)],
)


# -----------------------------
# Request Models
# -----------------------------
class TenantCreateRequest(BaseModel):
    tenant_code: str = Field(..., min_length=2, max_length=20)
    tenant_name: str = Field(..., min_length=2, max_length=100)
    industry: str = Field(..., min_length=2, max_length=50)


# -----------------------------
# Create Tenant
# -----------------------------
@router.post("/")
def create_new_tenant(request: TenantCreateRequest):
    tenant_code = request.tenant_code.strip().upper()
    tenant_name = request.tenant_name.strip()
    industry = request.industry.strip().lower()

    if not tenant_code:
        raise HTTPException(status_code=400, detail="tenant_code is required")

    create_tenant(tenant_code, tenant_name, industry)

    return {
        "status": "created",
        "tenant_code": tenant_code,
    }


# -----------------------------
# Fetch Tenant
# -----------------------------
@router.get("/{tenant_code}")
def fetch_tenant(tenant_code: str):
    normalized_tenant_code = tenant_code.strip().upper()

    tenant = get_tenant(normalized_tenant_code)

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return {
        "tenant_code": tenant[0],
        "tenant_name": tenant[1],
        "industry": tenant[2],
        "currency": tenant[3],
        "locale": tenant[4],
        "is_active": tenant[5] if len(tenant) > 5 else True,
    }