"""End-to-end tests for trade data + auth + billing flows."""

PREFIX = "/api/v1"


# ========== Health (open) ==========

def test_health(client):
    r = client.get(f"{PREFIX}/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    body = r.json()
    assert body["version"] == "0.3.0"


# ========== Data endpoints (require API key) ==========

def test_countries_requires_key(client):
    r = client.get(f"{PREFIX}/countries")
    assert r.status_code == 401


def test_countries_works_with_key(client, auth_headers):
    r = client.get(f"{PREFIX}/countries", headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()) >= 30


def test_products_search(client, auth_headers):
    r = client.get(f"{PREFIX}/products/search", params={"q": "coffee"}, headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()) > 0


def test_products_detail_with_hierarchy(client, auth_headers):
    r = client.get(f"{PREFIX}/products/090111", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == "090111"
    assert [a["code"] for a in body["ancestors"]] == ["09", "0901"]


def test_top_partners(client, auth_headers):
    r = client.get(
        f"{PREFIX}/products/090111/top-partners",
        params={"reporter": "IN", "flow": "export", "year": 2024, "limit": 5},
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.json()["partners"][0]["country"]["iso_alpha2"] == "US"


def test_trade_flow_trend(client, auth_headers):
    r = client.get(
        f"{PREFIX}/trade-flows",
        params={
            "reporter": "IN", "partner": "US", "hs_code": "090111",
            "flow": "export", "year_from": 2019, "year_to": 2024,
        },
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body["points"]) == 6
    assert body["growth_rate_pct"] is not None


def test_tariffs(client, auth_headers):
    r = client.get(
        f"{PREFIX}/tariffs",
        params={"reporter": "US", "hs_code": "610910", "year": 2024},
        headers=auth_headers,
    )
    assert r.status_code == 200
    rows = r.json()
    mfn = next(t for t in rows if t["rate_type"] == "MFN")
    assert mfn["ad_valorem_rate"] == 16.5


def test_compliance(client, auth_headers):
    r = client.get(
        f"{PREFIX}/compliance",
        params={"reporter": "IN", "partner": "US", "hs_code": "300490"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    names = [d["document_name"] for d in r.json()["documents"]]
    assert any("FDA" in n for n in names)


# ========== API key auth edge cases ==========

def test_invalid_api_key_returns_401(client):
    r = client.get(
        f"{PREFIX}/products/search",
        params={"q": "coffee"},
        headers={"X-API-Key": "tdk_bogus"},
    )
    assert r.status_code == 401


def test_revoked_key_returns_401(client, keys):
    r = client.get(
        f"{PREFIX}/products/search",
        params={"q": "coffee"},
        headers={"X-API-Key": keys["revoked"]},
    )
    assert r.status_code == 401


def test_key_via_query_param(client, keys):
    r = client.get(
        f"{PREFIX}/products/search",
        params={"q": "coffee", "api_key": keys["pro"]},
    )
    assert r.status_code == 200


# ========== Admin login ==========

def test_admin_login_success(client):
    from tests.conftest import TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD
    r = client.post(
        f"{PREFIX}/auth/admin/login",
        json={"email": TEST_ADMIN_EMAIL, "password": TEST_ADMIN_PASSWORD},
    )
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_admin_login_wrong_password(client):
    from tests.conftest import TEST_ADMIN_EMAIL
    r = client.post(
        f"{PREFIX}/auth/admin/login",
        json={"email": TEST_ADMIN_EMAIL, "password": "wrong"},
    )
    assert r.status_code == 401


def test_admin_me(client, admin_headers):
    from tests.conftest import TEST_ADMIN_EMAIL
    r = client.get(f"{PREFIX}/auth/admin/me", headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["email"] == TEST_ADMIN_EMAIL


# ========== Customer signup & login ==========

def test_customer_signup(client):
    r = client.post(
        f"{PREFIX}/auth/signup",
        json={
            "email": "newuser@example.com",
            "password": "secure-password-123",
            "full_name": "New User",
            "company_name": "Acme Trading",
        },
    )
    assert r.status_code == 201
    assert "access_token" in r.json()


def test_customer_signup_duplicate_email(client):
    from tests.conftest import TEST_CUSTOMER_EMAIL
    r = client.post(
        f"{PREFIX}/auth/signup",
        json={"email": TEST_CUSTOMER_EMAIL, "password": "another-password"},
    )
    assert r.status_code == 409


def test_customer_login_success(client):
    from tests.conftest import TEST_CUSTOMER_EMAIL, TEST_CUSTOMER_PASSWORD
    r = client.post(
        f"{PREFIX}/auth/login",
        json={"email": TEST_CUSTOMER_EMAIL, "password": TEST_CUSTOMER_PASSWORD},
    )
    assert r.status_code == 200


def test_customer_me(client, customer_headers):
    from tests.conftest import TEST_CUSTOMER_EMAIL
    r = client.get(f"{PREFIX}/auth/me", headers=customer_headers)
    assert r.status_code == 200
    assert r.json()["email"] == TEST_CUSTOMER_EMAIL


# ========== Customer API key management ==========

def test_create_api_key(client, customer_headers):
    r = client.post(
        f"{PREFIX}/auth/keys",
        json={"name": "New key"},
        headers=customer_headers,
    )
    assert r.status_code == 201
    body = r.json()
    assert body["plaintext_key"].startswith("tdk_")
    # Customer is on free plan, so new key should be free tier
    assert body["tier"] == "free"


def test_list_api_keys(client, customer_headers):
    r = client.get(f"{PREFIX}/auth/keys", headers=customer_headers)
    assert r.status_code == 200
    assert len(r.json()) >= 4  # 4 tier keys + revoked from fixtures


def test_revoke_api_key(client, customer_headers):
    # Create a key, then revoke
    r = client.post(
        f"{PREFIX}/auth/keys",
        json={"name": "To revoke"},
        headers=customer_headers,
    )
    key_id = r.json()["id"]
    plaintext = r.json()["plaintext_key"]

    r2 = client.delete(f"{PREFIX}/auth/keys/{key_id}", headers=customer_headers)
    assert r2.status_code == 204

    r3 = client.get(
        f"{PREFIX}/products/search",
        params={"q": "coffee"},
        headers={"X-API-Key": plaintext},
    )
    assert r3.status_code == 401


def test_signup_creates_free_subscription_and_key(client):
    """After signup, customer should have an active free sub + a default API key."""
    r = client.post(
        f"{PREFIX}/auth/signup",
        json={"email": "fresh@example.com", "password": "secure-pwd-1234"},
    )
    assert r.status_code == 201
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    sub = client.get(f"{PREFIX}/billing/subscription", headers=headers).json()
    assert sub is not None
    assert sub["status"] == "active"
    assert sub["plan"]["code"] == "free"

    keys = client.get(f"{PREFIX}/auth/keys", headers=headers).json()
    assert len(keys) == 1
    assert keys[0]["tier"] == "free"


# ========== Billing plans ==========

def test_list_plans_public(client):
    """Plans are public (no auth needed)."""
    r = client.get(f"{PREFIX}/billing/plans")
    assert r.status_code == 200
    plans = r.json()
    codes = {p["code"] for p in plans}
    assert {"free", "starter", "pro", "enterprise"}.issubset(codes)

    starter = next(p for p in plans if p["code"] == "starter")
    assert starter["price_inr"] == 99900
    assert starter["price_display"] == "₹999/month"


def test_my_subscription(client, customer_headers):
    r = client.get(f"{PREFIX}/billing/subscription", headers=customer_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "active"
    assert body["plan"]["code"] == "free"


# ========== Checkout flow (mock mode) ==========

def test_checkout_creates_order(client, customer_headers):
    r = client.post(
        f"{PREFIX}/billing/checkout",
        json={"plan_code": "starter"},
        headers=customer_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["razorpay_order_id"].startswith("order_mock_")
    assert body["amount_paise"] == 99900
    assert body["mock_mode"] is True
    assert body["customer_email"] == "customer@example.com"


def test_checkout_free_plan_rejected(client, customer_headers):
    r = client.post(
        f"{PREFIX}/billing/checkout",
        json={"plan_code": "free"},
        headers=customer_headers,
    )
    assert r.status_code == 400


def test_checkout_unknown_plan(client, customer_headers):
    r = client.post(
        f"{PREFIX}/billing/checkout",
        json={"plan_code": "platinum"},
        headers=customer_headers,
    )
    assert r.status_code == 404


def test_mock_payment_success_activates_subscription(client, customer_headers):
    # Step 1: Create checkout for pro plan
    r = client.post(
        f"{PREFIX}/billing/checkout",
        json={"plan_code": "pro"},
        headers=customer_headers,
    )
    assert r.status_code == 200
    order_id = r.json()["razorpay_order_id"]
    sub_id = r.json()["subscription_id"]

    # Step 2: Simulate successful payment
    r2 = client.post(
        f"{PREFIX}/billing/mock-success/{order_id}",
        headers=customer_headers,
    )
    assert r2.status_code == 200
    body = r2.json()
    assert body["status"] == "active"
    assert body["plan"]["code"] == "pro"

    # Step 3: Verify current subscription is now pro
    r3 = client.get(f"{PREFIX}/billing/subscription", headers=customer_headers)
    assert r3.json()["plan"]["code"] == "pro"


def test_pro_subscription_upgrades_existing_keys(client, customer_headers):
    """After paying for pro, the customer's existing free keys should become pro."""
    # Note: this test uses a fresh customer to avoid interference
    r = client.post(
        f"{PREFIX}/auth/signup",
        json={"email": "upgrader@example.com", "password": "secure-pwd-1234"},
    )
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Confirm initial key is free tier
    keys_before = client.get(f"{PREFIX}/auth/keys", headers=headers).json()
    assert keys_before[0]["tier"] == "free"

    # Upgrade to pro
    co = client.post(f"{PREFIX}/billing/checkout", json={"plan_code": "pro"}, headers=headers)
    order_id = co.json()["razorpay_order_id"]
    client.post(f"{PREFIX}/billing/mock-success/{order_id}", headers=headers)

    # Existing keys should now be pro tier
    keys_after = client.get(f"{PREFIX}/auth/keys", headers=headers).json()
    assert keys_after[0]["tier"] == "pro"


def test_payment_history(client, customer_headers):
    # Create a checkout to ensure there's payment history
    r = client.post(
        f"{PREFIX}/billing/checkout",
        json={"plan_code": "starter"},
        headers=customer_headers,
    )
    assert r.status_code == 200

    r2 = client.get(f"{PREFIX}/billing/payments", headers=customer_headers)
    assert r2.status_code == 200
    payments = r2.json()
    assert len(payments) >= 1
    assert payments[0]["amount_paise"] > 0
