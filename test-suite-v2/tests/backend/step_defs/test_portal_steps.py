"""Portal BDD step definitions â€” implements steps from portal.feature."""
import pytest
from pytest_bdd import given, when, then, parsers, scenarios
from faker import Faker

base = r"D:\all_py\trade-data-api\test-suite-v2\tests\backend\features\portal.feature"
scenarios(base)

fake = Faker("en_IN")


# â”€â”€ Shared helper â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _register_and_login(client, context):
    email    = f"portal_{fake.uuid4()[:8]}@example.com"
    password = "PortalPass@1234"
    r = client.post("/auth/signup", json={
        "email": email, "password": password,
        "full_name": fake.name(),
    })
    assert r.status_code == 201, f"Signup failed: {r.text}"
    token   = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    context["customer_email"]   = email
    context["customer_token"]   = token
    context["customer_headers"] = headers
    return email, token, headers


# â”€â”€ Givens â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@given("the API is running at base URL", target_fixture="api_up")
def api_running(client):
    assert client.get("/health").status_code == 200


@given("I am logged in as a registered customer")
def logged_in_customer(client, context):
    _register_and_login(client, context)


@given("I am on the free portal tier")
def free_portal_tier(client, context):
    # Free tier is the default â€” no subscription needed
    pass


@given("I have submitted a service request")
def submitted_service_request(client, context):
    r = client.post("/portal/services/request", params={
        "service_type":   "iec",
        "applicant_name": "Test User",
        "company_name":   "Test Exports Pvt Ltd",
        "pan_number":     "ABCDE1234F",
        "mobile":         "+91-9876543210",
    }, headers=context["customer_headers"])
    assert r.status_code == 201, f"Service request failed: {r.text}"
    context["service_request_id"] = r.json()["id"]


# â”€â”€ Whens â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@when(parsers.parse('I search the portal for HS code "{hs_code}" export flow'))
def portal_search_hs_export(client, context, hs_code):
    context["response"] = client.get("/portal/search", params={
        "hs_code":   hs_code,
        "flow":      "export",
        "year_from": 2019,
        "year_to":   2024,
    }, headers=context["customer_headers"])


@when(parsers.parse('I search the portal with keyword "{keyword}" export flow'))
def portal_search_keyword(client, context, keyword):
    context["response"] = client.get("/portal/search", params={
        "q":         keyword,
        "flow":      "export",
        "year_from": 2019,
        "year_to":   2024,
    }, headers=context["customer_headers"])


@when(parsers.parse('I search the portal for HS "{hs_code}" reporter "{reporter}" export flow'))
def portal_search_with_reporter(client, context, hs_code, reporter):
    context["response"] = client.get("/portal/search", params={
        "hs_code":   hs_code,
        "reporter":  reporter,
        "flow":      "export",
        "year_from": 2019,
        "year_to":   2024,
    }, headers=context["customer_headers"])


@when(parsers.parse('I search the portal for HS "{hs_code}" from {y_from:d} to {y_to:d}'))
def portal_search_year_range(client, context, hs_code, y_from, y_to):
    context["response"] = client.get("/portal/search", params={
        "hs_code":   hs_code,
        "flow":      "export",
        "year_from": y_from,
        "year_to":   y_to,
    }, headers=context["customer_headers"])


@when("I search the portal without a token")
def portal_search_no_token(client, context):
    context["response"] = client.get("/portal/search", params={
        "hs_code": "090111", "flow": "export",
    })


@when(parsers.parse('I request a CSV export for HS "{hs_code}"'))
def request_csv_export(client, context, hs_code):
    context["response"] = client.get("/portal/export", params={
        "hs_code": hs_code,
        "flow":    "export",
        "format":  "csv",
    }, headers=context["customer_headers"])


@when("I get the portal data status")
def get_data_status(client, context):
    context["response"] = client.get("/portal/data-status")


@when(parsers.parse('I get the portal product summary for HS "{hs_code}" year {year:d}'))
def get_product_summary(client, context, hs_code, year):
    context["response"] = client.get(
        f"/portal/product/{hs_code}/summary",
        params={"year": year},
        headers=context["customer_headers"],
    )


@when("I get the EXIM service catalogue")
def get_service_catalogue(client, context):
    context["response"] = client.get("/portal/services/catalogue")


@when("I submit an IEC service request with valid details")
def submit_iec_request(client, context):
    context["response"] = client.post("/portal/services/request", params={
        "service_type":   "iec",
        "applicant_name": "Rajesh Kumar",
        "company_name":   "Kumar Exports Pvt Ltd",
        "pan_number":     "ABCDE1234F",
        "mobile":         "+91-9876543210",
        "notes":          "New exporter registration",
    }, headers=context["customer_headers"])


@when(parsers.parse('I submit a service request with type "{service_type}"'))
def submit_invalid_service(client, context, service_type):
    context["response"] = client.post("/portal/services/request", params={
        "service_type":   service_type,
        "applicant_name": "Test User",
        "company_name":   "Test Co",
        "pan_number":     "ABCDE1234F",
        "mobile":         "+91-9876543210",
    }, headers=context["customer_headers"])


@when("I submit a service request without a token")
def submit_service_no_token(client, context):
    context["response"] = client.post("/portal/services/request", params={
        "service_type":   "iec",
        "applicant_name": "Test User",
        "company_name":   "Test Co",
        "pan_number":     "ABCDE1234F",
        "mobile":         "+91-9876543210",
    })


@when("I get my service requests")
def get_my_service_requests(client, context):
    context["response"] = client.get(
        "/portal/services/my-requests",
        headers=context["customer_headers"],
    )


@when("I get the portal plans")
def get_portal_plans(client, context):
    context["response"] = client.get("/portal/plans")


# â”€â”€ Thens â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@then(parsers.parse("the response status should be {status:d}"))
def check_status(context, status):
    got = context["response"].status_code
    assert got == status, \
        f"Expected {status}, got {got}: {context['response'].text[:300]}"


@then("the results list should not be empty")
def results_not_empty(context):
    data = context["response"].json()
    assert len(data.get("results", [])) > 0, "Results list is empty"


@then("each result should have hs_code and value_usd and year")
def results_have_required_fields(context):
    for r in context["response"].json().get("results", []):
        assert "hs_code"   in r, f"Missing hs_code in: {r}"
        assert "value_usd" in r, f"Missing value_usd in: {r}"
        assert "year"      in r, f"Missing year in: {r}"


@then(parsers.parse('the plan should be "{plan}"'))
def plan_is(context, plan):
    assert context["response"].json().get("plan") == plan, \
        f"Plan: {context['response'].json().get('plan')}, expected {plan}"


@then("can_export should be false")
def can_export_false(context):
    assert context["response"].json().get("can_export") is False


@then(parsers.parse("the results count should be at most {n:d}"))
def results_at_most(context, n):
    count = len(context["response"].json().get("results", []))
    assert count <= n, f"Got {count} results, expected <= {n}"


@then("has_more may be true")
def has_more_may_be_true(context):
    # This is informational â€” just verify the field exists
    assert "has_more" in context["response"].json()


@then(parsers.parse("tier_limit should be {n:d}"))
def tier_limit_is(context, n):
    assert context["response"].json().get("tier_limit") == n, \
        f"tier_limit: {context['response'].json().get('tier_limit')}, expected {n}"


@then(parsers.parse('all results reporter_iso should be "{iso}"'))
def all_reporter_iso(context, iso):
    for r in context["response"].json().get("results", []):
        assert r.get("reporter_iso") == iso, \
            f"reporter_iso: {r.get('reporter_iso')}, expected {iso}"


@then(parsers.parse("all result years should be between {y_from:d} and {y_to:d}"))
def all_years_in_range(context, y_from, y_to):
    for r in context["response"].json().get("results", []):
        yr = r.get("year", 0)
        assert y_from <= yr <= y_to, \
            f"Year {yr} not in range {y_from}â€“{y_to}"


@then(parsers.parse('the error should mention "{text}"'))
def error_mentions(context, text):
    detail = str(context["response"].json().get("detail", ""))
    assert text.lower() in detail.lower(), \
        f"'{text}' not in error: {detail}"


@then("total_trade_flow_records should be present")
def total_records_present(context):
    assert "total_trade_flow_records" in context["response"].json()


@then("hs_codes_covered should be present")
def hs_codes_present(context):
    assert "hs_codes_covered" in context["response"].json()


@then(parsers.parse('the hs_code should be "{hs_code}"'))
def hs_code_is(context, hs_code):
    assert context["response"].json().get("hs_code") == hs_code, \
        f"hs_code: {context['response'].json().get('hs_code')}, expected {hs_code}"


@then("top_exporters should not be empty")
def top_exporters_not_empty(context):
    exporters = context["response"].json().get("top_exporters", [])
    assert len(exporters) > 0, "top_exporters is empty"


@then("each exporter should have iso and name and value_usd")
def exporters_have_fields(context):
    for e in context["response"].json().get("top_exporters", []):
        assert "iso"       in e, f"Missing iso in: {e}"
        assert "name"      in e, f"Missing name in: {e}"
        assert "value_usd" in e, f"Missing value_usd in: {e}"


@then(parsers.parse('the catalogue should contain service "{code}"'))
def catalogue_has_service(context, code):
    codes = {s["code"] for s in context["response"].json()}
    assert code in codes, f"'{code}' not in catalogue: {codes}"


@then(parsers.parse("the IEC service price should be {price:d}"))
def iec_service_price(context, price):
    services = context["response"].json()
    iec = next((s for s in services if s["code"] == "iec"), None)
    assert iec and iec.get("price_inr") == price, \
        f"IEC price: {iec and iec.get('price_inr')}, expected {price}"


@then(parsers.parse('the service_type should be "{stype}"'))
def service_type_is(context, stype):
    assert context["response"].json().get("service_type") == stype


@then(parsers.parse('the status should be "{status}"'))
def status_is(context, status):
    assert context["response"].json().get("status") == status


@then("a reference ID should be returned")
def reference_id_returned(context):
    assert context["response"].json().get("id") is not None


@then("my submitted request should be in the list")
def submitted_request_in_list(context):
    requests = context["response"].json()
    assert len(requests) >= 1, "No service requests returned"
    ids = [r["id"] for r in requests]
    assert context.get("service_request_id") in ids, \
        f"Request ID {context.get('service_request_id')} not in {ids}"


@then(parsers.parse("the free plan records_per_search should be {n:d}"))
def free_records_per_search(context, n):
    plans = context["response"].json()
    free  = next((p for p in plans if p["code"] == "portal_free"), None)
    assert free and free.get("records_per_search") == n, \
        f"Free records_per_search: {free and free.get('records_per_search')}"


@then(parsers.parse("the starter plan records_per_search should be {n:d}"))
def starter_records_per_search(context, n):
    plans   = context["response"].json()
    starter = next((p for p in plans if p["code"] == "portal_starter"), None)
    assert starter and starter.get("records_per_search") == n, \
        f"Starter records_per_search: {starter and starter.get('records_per_search')}"


@then("the pro plan records_per_search should be null")
def pro_records_per_search_null(context):
    plans = context["response"].json()
    pro   = next((p for p in plans if p["code"] == "portal_pro"), None)
    assert pro and pro.get("records_per_search") is None, \
        f"Pro records_per_search: {pro and pro.get('records_per_search')}"


@then("the starter plan can_export_csv should be true")
def starter_can_export(context):
    plans   = context["response"].json()
    starter = next((p for p in plans if p["code"] == "portal_starter"), None)
    assert starter and starter.get("can_export_csv") is True


@then("the free plan can_export_csv should be false")
def free_cannot_export(context):
    plans = context["response"].json()
    free  = next((p for p in plans if p["code"] == "portal_free"), None)
    assert free and free.get("can_export_csv") is False


@then("the pro plan can_use_api should be true")
def pro_can_use_api(context):
    plans = context["response"].json()
    pro   = next((p for p in plans if p["code"] == "portal_pro"), None)
    assert pro and pro.get("can_use_api") is True
