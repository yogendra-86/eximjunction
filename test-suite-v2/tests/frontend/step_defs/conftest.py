"""Frontend test conftest — Playwright fixtures, auth helpers, BDD setup."""
import os
import pytest
import httpx
from faker import Faker
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

FRONTEND_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:5173")
API_URL      = os.getenv("API_BASE_URL",      "http://localhost:8000/api/v1")
fake         = Faker("en_IN")


# ── Browser lifecycle ─────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def browser_instance():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=100)
        yield browser
        browser.close()


@pytest.fixture(scope="session")
def browser_context(browser_instance):
    context = browser_instance.new_context(
        viewport={"width": 1280, "height": 720},
        base_url=FRONTEND_URL,
        locale="en-IN",
        timezone_id="Asia/Kolkata",
    )
    yield context
    context.close()


@pytest.fixture
def page(browser_context):
    """Fresh page per test. Records video and trace on failure."""
    page = browser_context.new_page()
    yield page
    page.close()


@pytest.fixture(scope="session")
def logged_in_context(browser_instance):
    """
    Browser context with a pre-authenticated customer session.
    Shared across all frontend tests that need login.
    Avoids re-logging-in for every test.
    """
    email    = f"fe_{fake.uuid4()[:8]}@example.com"
    password = "FrontendPass@1234"

    # Create the customer via API
    with httpx.Client(base_url=API_URL) as client:
        r = client.post("/auth/signup", json={
            "email": email, "password": password,
            "full_name": "Frontend Test User",
            "company_name": "Test Exports",
        })
        assert r.status_code == 201, f"Signup failed: {r.text}"
        token = r.json()["access_token"]

        # Create an API key for Explorer tests
        r2 = client.post("/auth/keys",
            json={"name": "Frontend Test Key"},
            headers={"Authorization": f"Bearer {token}"},
        )
        api_key = r2.json()["plaintext_key"] if r2.status_code == 201 else ""

    # Inject token into browser localStorage
    context = browser_instance.new_context(
        viewport={"width": 1280, "height": 720},
        base_url=FRONTEND_URL,
        locale="en-IN",
    )
    page = context.new_page()
    page.goto(FRONTEND_URL)
    page.evaluate(f"""() => {{
        localStorage.setItem('token', '{token}');
        localStorage.setItem('user', JSON.stringify({{
            email: '{email}',
            full_name: 'Frontend Test User',
            company_name: 'Test Exports'
        }}));
    }}""")
    page.close()

    yield {"context": context, "email": email, "password": password,
           "token": token, "api_key": api_key}
    context.close()


@pytest.fixture
def auth_page(logged_in_context):
    """Page that is already authenticated."""
    page = logged_in_context["context"].new_page()
    yield page
    page.close()


@pytest.fixture
def context():
    """BDD step state container."""
    return {}
