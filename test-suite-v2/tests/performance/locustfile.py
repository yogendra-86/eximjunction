"""
EximJunction — Locust Performance Test Suite
============================================

Scenarios:
  1. API Load Test       — sustained normal load on trade data endpoints
  2. Portal Load Test    — business user browsing and searching
  3. Spike Test          — sudden traffic surge (5x normal)
  4. Soak Test           — low-level sustained load over long period
  5. Rate Limit Stress   — verify rate limiting holds under pressure

Run commands:
  # Basic load test (web dashboard at http://localhost:8089)
  locust -f tests/performance/locustfile.py --host http://localhost:8000

  # Headless API load test
  locust -f tests/performance/locustfile.py --host http://localhost:8000 \
    --users 50 --spawn-rate 5 --run-time 2m --headless \
    --html tests/performance/reports/api_load_report.html

  # Spike test
  locust -f tests/performance/locustfile.py \
    --host http://localhost:8000 \
    -u 200 -r 50 -t 1m --headless \
    --html tests/performance/reports/spike_report.html

  # Soak test (2 hours)
  locust -f tests/performance/locustfile.py \
    --host http://localhost:8000 \
    -u 10 -r 1 -t 2h --headless \
    --html tests/performance/reports/soak_report.html
"""
import json
import random
import time
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner

# ── Test data ─────────────────────────────────────────────────────────────────

HS_CODES = [
    "090111", "090121", "100630", "270900", "300490",
    "610910", "710231", "851712", "854231", "870323",
]
COUNTRIES  = ["IN", "US", "CN", "DE", "JP", "GB", "AE", "SA", "VN", "KR"]
YEARS      = [2019, 2020, 2021, 2022, 2023, 2024]
KEYWORDS   = ["coffee", "mobile", "pharma", "rice", "crude oil", "diamond", "car"]

# Shared state — populated at startup by one user
_api_keys  = []
_jwt_tokens= []


def _register_and_get_key(client, suffix: str) -> dict:
    """Register a customer and create an API key. Returns {token, api_key}."""
    email    = f"perf_{suffix}_{random.randint(1000,9999)}@loadtest.com"
    password = "LoadTest@1234"
    r = client.post("/api/v1/auth/signup", json={
        "email": email, "password": password, "full_name": "Load Tester"
    })
    if r.status_code != 201:
        return {}
    token = r.json()["access_token"]
    r2 = client.post("/api/v1/auth/keys",
        json={"name": "Load Test Key"},
        headers={"Authorization": f"Bearer {token}"},
    )
    if r2.status_code != 201:
        return {}
    return {"token": token, "api_key": r2.json()["plaintext_key"]}


# ── User 1: API Power User ────────────────────────────────────────────────────

class APIUser(HttpUser):
    """
    Simulates a developer/technical user hammering the trade data API.
    Realistic mix: search 40%, partners 25%, trade flow 20%, tariffs 10%, compliance 5%.
    Wait time: 1–3 seconds between requests (realistic human pacing).
    """
    wait_time  = between(1, 3)
    weight     = 3  # 3x more API users than portal users

    def on_start(self):
        """Called once per simulated user at startup. Get credentials."""
        creds = _register_and_get_key(self.client, "api")
        self.api_key = creds.get("api_key", "")
        self.token   = creds.get("token", "")
        self.headers = {"X-API-Key": self.api_key}
        self.auth_headers = {"Authorization": f"Bearer {self.token}"}

    @task(40)
    def search_hs_code(self):
        """Most common operation — HS code keyword search."""
        keyword = random.choice(KEYWORDS)
        with self.client.get(
            f"/api/v1/products/search",
            params={"q": keyword, "limit": 20},
            headers=self.headers,
            name="/api/v1/products/search",
            catch_response=True,
        ) as r:
            if r.status_code == 200:
                r.success()
            elif r.status_code == 401:
                r.failure("API key rejected")
            elif r.status_code == 429:
                r.failure("Rate limit hit")
            else:
                r.failure(f"Unexpected {r.status_code}: {r.text[:100]}")

    @task(25)
    def get_top_partners(self):
        """Get top trading partners for a random product."""
        hs   = random.choice(HS_CODES)
        flow = random.choice(["export", "import"])
        year = random.choice(YEARS)
        with self.client.get(
            f"/api/v1/products/{hs}/top-partners",
            params={"flow": flow, "year": year, "limit": 10},
            headers=self.headers,
            name="/api/v1/products/{hs_code}/top-partners",
            catch_response=True,
        ) as r:
            if r.status_code in (200, 404):
                r.success()
            else:
                r.failure(f"Status {r.status_code}")

    @task(20)
    def get_trade_flow(self):
        """Trade flow trend between random country pair."""
        reporter = random.choice(COUNTRIES)
        partner  = random.choice([c for c in COUNTRIES if c != reporter])
        hs       = random.choice(HS_CODES)
        with self.client.get(
            "/api/v1/trade-flows",
            params={
                "reporter": reporter, "partner": partner,
                "hs_code": hs, "flow": "export",
                "year_from": 2019, "year_to": 2024,
            },
            headers=self.headers,
            name="/api/v1/trade-flows",
            catch_response=True,
        ) as r:
            if r.status_code in (200, 404):
                r.success()
            else:
                r.failure(f"Status {r.status_code}")

    @task(10)
    def get_tariffs(self):
        reporter = random.choice(COUNTRIES)
        hs       = random.choice(HS_CODES)
        with self.client.get(
            "/api/v1/tariffs",
            params={"reporter": reporter, "hs_code": hs, "year": 2024},
            headers=self.headers,
            name="/api/v1/tariffs",
            catch_response=True,
        ) as r:
            if r.status_code in (200, 404):
                r.success()
            else:
                r.failure(f"Status {r.status_code}")

    @task(5)
    def get_compliance(self):
        reporter = random.choice(COUNTRIES)
        partner  = random.choice([c for c in COUNTRIES if c != reporter])
        with self.client.get(
            "/api/v1/compliance",
            params={"reporter": reporter, "partner": partner},
            headers=self.headers,
            name="/api/v1/compliance",
            catch_response=True,
        ) as r:
            if r.status_code in (200, 404):
                r.success()
            else:
                r.failure(f"Status {r.status_code}")

    @task(3)
    def check_subscription(self):
        """Simulates dashboard load — check billing status."""
        with self.client.get(
            "/api/v1/billing/subscription",
            headers=self.auth_headers,
            name="/api/v1/billing/subscription",
            catch_response=True,
        ) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Status {r.status_code}")

    @task(2)
    def list_api_keys(self):
        """Dashboard API keys page load."""
        with self.client.get(
            "/api/v1/auth/keys",
            headers=self.auth_headers,
            name="/api/v1/auth/keys",
            catch_response=True,
        ) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Status {r.status_code}")


# ── User 2: Portal Browser ────────────────────────────────────────────────────

class PortalUser(HttpUser):
    """
    Simulates a business user using the Data Portal (search + export).
    Slower pacing — human browsing through the UI.
    """
    wait_time = between(3, 8)
    weight    = 1  # fewer portal users

    def on_start(self):
        creds = _register_and_get_key(self.client, "portal")
        self.token        = creds.get("token", "")
        self.api_key      = creds.get("api_key", "")
        self.auth_headers = {"Authorization": f"Bearer {self.token}"}
        self.key_headers  = {"X-API-Key": self.api_key}

    @task(40)
    def portal_search(self):
        """Main portal search — most common portal action."""
        hs   = random.choice(HS_CODES)
        flow = random.choice(["export", "import"])
        with self.client.get(
            "/api/v1/portal/search",
            params={"hs_code": hs, "flow": flow, "year_from": 2019, "year_to": 2024},
            headers=self.auth_headers,
            name="/api/v1/portal/search",
            catch_response=True,
        ) as r:
            if r.status_code == 200:
                data = r.json()
                if "results" not in data:
                    r.failure("Missing results key")
                else:
                    r.success()
            elif r.status_code == 401:
                r.failure("Auth failed")
            else:
                r.failure(f"Status {r.status_code}")

    @task(20)
    def portal_product_summary(self):
        hs = random.choice(HS_CODES)
        with self.client.get(
            f"/api/v1/portal/product/{hs}/summary",
            params={"year": 2024},
            headers=self.auth_headers,
            name="/api/v1/portal/product/{hs_code}/summary",
            catch_response=True,
        ) as r:
            if r.status_code in (200, 404):
                r.success()
            else:
                r.failure(f"Status {r.status_code}")

    @task(15)
    def view_portal_plans(self):
        """Pricing page equivalent."""
        with self.client.get(
            "/api/v1/portal/plans",
            name="/api/v1/portal/plans",
            catch_response=True,
        ) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Status {r.status_code}")

    @task(10)
    def view_service_catalogue(self):
        with self.client.get(
            "/api/v1/portal/services/catalogue",
            name="/api/v1/portal/services/catalogue",
            catch_response=True,
        ) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Status {r.status_code}")

    @task(5)
    def check_data_status(self):
        """Portal data freshness widget."""
        with self.client.get(
            "/api/v1/portal/data-status",
            name="/api/v1/portal/data-status",
            catch_response=True,
        ) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Status {r.status_code}")


# ── User 3: Unauthenticated Visitor ──────────────────────────────────────────

class VisitorUser(HttpUser):
    """
    Simulates anonymous website visitor hitting public endpoints.
    High frequency — bots, scrapers, marketing campaigns.
    """
    wait_time = between(1, 2)
    weight    = 2

    @task(50)
    def check_health(self):
        with self.client.get("/api/v1/health", name="/api/v1/health", catch_response=True) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Health check failed: {r.status_code}")

    @task(30)
    def view_plans(self):
        with self.client.get("/api/v1/billing/plans", name="/api/v1/billing/plans", catch_response=True) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Status {r.status_code}")

    @task(20)
    def attempt_data_without_key(self):
        """Verifies unauthenticated requests are blocked efficiently."""
        with self.client.get(
            "/api/v1/products/search",
            params={"q": "coffee"},
            name="/api/v1/products/search [no key]",
            catch_response=True,
        ) as r:
            if r.status_code == 401:
                r.success()  # Expected — correctly blocked
            elif r.status_code == 200:
                r.failure("SECURITY: Data returned without API key!")
            else:
                r.failure(f"Unexpected {r.status_code}")


# ── Spike test user (use with --tags spike) ───────────────────────────────────

class SpikeUser(HttpUser):
    """
    Used for spike testing — no wait time, hammers a single endpoint.
    Run with: locust -f locustfile.py SpikeUser --users 200 --spawn-rate 100
    """
    wait_time = between(0, 0.5)
    weight    = 0  # Not included in default runs

    def on_start(self):
        creds = _register_and_get_key(self.client, "spike")
        self.headers = {"X-API-Key": creds.get("api_key", "")}

    @task
    def spike_search(self):
        self.client.get(
            "/api/v1/products/search",
            params={"q": "coffee"},
            headers=self.headers,
            name="/api/v1/products/search [spike]",
        )


# ── Performance thresholds (checked in CI) ────────────────────────────────────

THRESHOLDS = {
    # endpoint_name: (max_p95_ms, max_failure_rate_pct)
    "/api/v1/health":                            (100,  0.1),
    "/api/v1/products/search":                   (500,  1.0),
    "/api/v1/products/{hs_code}/top-partners":   (800,  2.0),
    "/api/v1/trade-flows":                       (800,  2.0),
    "/api/v1/tariffs":                           (600,  2.0),
    "/api/v1/compliance":                        (600,  2.0),
    "/api/v1/portal/search":                     (1000, 2.0),
    "/api/v1/billing/subscription":              (300,  1.0),
}


@events.quitting.add_listener
def check_thresholds(environment, **kwargs):
    """
    After the test run, check if any endpoint breached performance thresholds.
    Exits with code 1 if thresholds are breached (fails CI pipeline).
    """
    failures = []
    stats    = environment.runner.stats

    for endpoint, (max_p95, max_fail_pct) in THRESHOLDS.items():
        entry = stats.get(endpoint, "GET")
        if not entry or entry.num_requests == 0:
            continue

        p95      = entry.get_response_time_percentile(0.95)
        fail_pct = (entry.num_failures / entry.num_requests) * 100

        if p95 > max_p95:
            failures.append(
                f"❌ {endpoint}: p95={p95:.0f}ms exceeds threshold {max_p95}ms"
            )
        if fail_pct > max_fail_pct:
            failures.append(
                f"❌ {endpoint}: failure_rate={fail_pct:.1f}% exceeds threshold {max_fail_pct}%"
            )

    if failures:
        print("\n⚠️  PERFORMANCE THRESHOLD VIOLATIONS:")
        for f in failures:
            print(f"   {f}")
        environment.process_exit_code = 1
    else:
        print("\n✅ All performance thresholds passed")
