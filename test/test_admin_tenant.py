from fastapi.testclient import TestClient

from apps.api.main import app

client = TestClient(app)


def _override_admin_dependencies():
    from apps.api.routers import admin_tenants as router

    for route in router.router.routes:
        for dependency in getattr(route, "dependant", None).dependencies:
            app.dependency_overrides[dependency.call] = lambda: True


def _clear_overrides():
    app.dependency_overrides.clear()


def test_create_tenant_success(monkeypatch):
    from apps.api.routers import admin_tenants as router

    _override_admin_dependencies()

    calls = []

    monkeypatch.setattr(
        router,
        "create_tenant",
        lambda tenant_code, tenant_name, industry: calls.append(
            (tenant_code, tenant_name, industry)
        ),
    )

    response = client.post(
        "/admin/tenants/",
        json={
            "tenant_code": " fnb ",
            "tenant_name": " First National Bank ",
            "industry": " Banking ",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "created",
        "tenant_code": "FNB",
    }
    assert calls == [("FNB", "First National Bank", "banking")]

    _clear_overrides()


def test_create_tenant_validation_error():
    _override_admin_dependencies()

    response = client.post(
        "/admin/tenants/",
        json={
            "tenant_code": "A",
            "tenant_name": "F",
            "industry": "B",
        },
    )

    assert response.status_code == 422

    _clear_overrides()


def test_fetch_tenant_success(monkeypatch):
    from apps.api.routers import admin_tenants as router

    _override_admin_dependencies()

    monkeypatch.setattr(
        router,
        "get_tenant",
        lambda tenant_code: (
            tenant_code,
            "First National Bank",
            "banking",
            "ZAR",
            "en-ZA",
            True,
        ),
    )

    response = client.get("/admin/tenants/fnb")

    assert response.status_code == 200
    assert response.json() == {
        "tenant_code": "FNB",
        "tenant_name": "First National Bank",
        "industry": "banking",
        "currency": "ZAR",
        "locale": "en-ZA",
        "is_active": True,
    }

    _clear_overrides()


def test_fetch_tenant_not_found(monkeypatch):
    from apps.api.routers import admin_tenants as router

    _override_admin_dependencies()

    monkeypatch.setattr(router, "get_tenant", lambda tenant_code: None)

    response = client.get("/admin/tenants/missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "Tenant not found"

    _clear_overrides()


def test_create_tenant_requires_admin_key():
    _clear_overrides()

    response = client.post(
        "/admin/tenants/",
        json={
            "tenant_code": "FNB",
            "tenant_name": "First National Bank",
            "industry": "Banking",
        },
    )

    assert response.status_code in (401, 403)