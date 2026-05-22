"""Root conftest — shared fixtures available to all tests."""
import os
import pytest
import httpx
from faker import Faker

# ── Configuration ─────────────────────────────────────────────────────────────
BASE_URL     = os.getenv("API_BASE_URL",      "http://localhost:8000/api/v1")
FRONTEND_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:5173")
ADMIN_EMAIL  = os.getenv("ADMIN_EMAIL",       "admin@example.com")
ADMIN_PASS   = os.getenv("ADMIN_PASSWORD",    "Admin@123456")

fake = Faker("en_IN")  # Indian locale for realistic test data


# ── HTTP client ───────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def client():
    """Shared HTTP client for all backend tests."""
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as c:
        yield c


@pytest.fixture(scope="session")
def async_client():
    """Async HTTP client for concurrent tests."""
    return httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)


# ── Auth helpers ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def admin_token(client):
    """Login as admin and return JWT token. Cached for entire session."""
    r = client.post("/auth/admin/login", json={
        "email": ADMIN_EMAIL, "password": ADMIN_PASS
    })
    assert r.status_code == 200, f"Admin login failed: {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def new_customer(client):
    """
    Create a fresh customer for each test that needs one.
    Uses Faker to generate unique email addresses.
    Yields (email, password, jwt_token). Cleanup is implicit (DB wipe between test runs).
    """
    email    = f"test_{fake.uuid4()[:8]}@example.com"
    password = "TestPass@1234"
    r = client.post("/auth/signup", json={
        "email":        email,
        "password":     password,
        "full_name":    fake.name(),
        "company_name": fake.company(),
        "phone":        f"+91{fake.numerify('##########')}",
    })
    assert r.status_code == 201, f"Customer signup failed: {r.text}"
    token = r.json()["access_token"]
    yield {"email": email, "password": password, "token": token,
           "headers": {"Authorization": f"Bearer {token}"}}


@pytest.fixture
def customer_with_api_key(client, new_customer):
    """Customer with a freshly created API key."""
    r = client.post("/auth/keys",
        json={"name": "Test Key"},
        headers=new_customer["headers"],
    )
    assert r.status_code == 201
    key = r.json()["plaintext_key"]
    return {**new_customer, "api_key": key, "key_headers": {"X-API-Key": key}}


# ── Context holders for BDD step sharing ─────────────────────────────────────

@pytest.fixture
def context():
    """Mutable dict for sharing state between BDD steps in a scenario."""
    return {}
