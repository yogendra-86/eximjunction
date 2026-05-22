"""Backend test conftest — BDD fixtures and shared state."""
import pytest
import httpx
import os

BASE_URL    = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL",  "admin@example.com")
ADMIN_PASS  = os.getenv("ADMIN_PASSWORD","Admin@123456")


@pytest.fixture(scope="session")
def client():
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as c:
        yield c


@pytest.fixture(scope="session")
def admin_token(client):
    r = client.post("/auth/admin/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
    assert r.status_code == 200, f"Admin login failed: {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def context():
    """Shared mutable state between BDD steps within one scenario."""
    return {}
