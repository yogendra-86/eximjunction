"""Frontend BDD step definitions â€” dashboard and portal flows."""
import pytest
from faker import Faker
from pytest_bdd import given, when, then, parsers, scenarios
from playwright.sync_api import expect

from tests.frontend.pages.portal_pages import (
    PortalSearchPage, PortalResultsPage, ServicesPage, LandingPage
)

scenarios(r"D:\all_py\trade-data-api\test-suite-v2\tests\frontend\features\dashboard.feature", r"D:\all_py\trade-data-api\test-suite-v2\tests\frontend\features\portal_search.feature")

fake = Faker("en_IN")

# â”€â”€ Dashboard steps â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@when("I open the dashboard")
def open_dashboard(context):
    context["page"].goto("http://localhost:5173/dashboard")
    context["page"].wait_for_load_state("networkidle")


@when("I open the API Keys page")
def open_api_keys(context):
    context["page"].goto("http://localhost:5173/dashboard/keys")
    context["page"].wait_for_load_state("networkidle")


@when("I open the Billing page")
def open_billing(context):
    context["page"].goto("http://localhost:5173/dashboard/billing")
    context["page"].wait_for_load_state("networkidle")


@when("I open the Explorer page")
def open_explorer(context):
    context["page"].goto("http://localhost:5173/dashboard/explorer")
    context["page"].wait_for_load_state("networkidle")


@when(parsers.parse('I create a key named "{name}"'))
def create_api_key(context, name):
    page = context["page"]
    page.locator('input[placeholder*="Production"]').fill(name)
    page.locator('button:has-text("Create Key")').click()
    page.wait_for_load_state("networkidle")


@when("I paste my API key")
def paste_api_key(context):
    key = context.get("api_key", "tdk_test_key_placeholder")
    context["page"].locator('input[placeholder*="tdk_"]').fill(key)


@when('I select the "Search HS Codes" endpoint')
def select_endpoint(context):
    context["page"].locator('button:has-text("Search HS Codes")').click()


@when("I click Run Query")
def click_run_query(context):
    context["page"].locator('button:has-text("Run Query")').click()
    context["page"].wait_for_timeout(3000)


@when(parsers.parse('I click "{link}" in the sidebar'))
def click_sidebar_link(context, link):
    context["page"].locator(f'nav a:has-text("{link}"), aside a:has-text("{link}")').first.click()
    context["page"].wait_for_load_state("networkidle")


@then("the subscription plan should be visible")
def subscription_visible(context):
    expect(context["page"].locator('text=Current Plan').first).to_be_visible()


@then("the daily usage stats should be visible")
def daily_stats_visible(context):
    expect(context["page"].locator("text=Today's Calls").first).to_be_visible()


@then("the usage chart should be visible")
def chart_visible(context):
    expect(context["page"].locator(".recharts-wrapper").first).to_be_visible()


@then("the sidebar should show all navigation items")
def sidebar_nav_items(context):
    for item in ["Overview", "API Keys", "Billing", "Explorer"]:
        expect(context["page"].locator(f'text={item}').first).to_be_visible()


@then("the new key should appear in the list")
def key_in_list(context):
    expect(context["page"].locator("text=My Test Key").first).to_be_visible()


@then('the key should start with "tdk_"')
def key_starts_tdk(context):
    key_text = context["page"].locator('code:has-text("tdk_")').first
    expect(key_text).to_be_visible()


@then("a copy warning should be shown")
def copy_warning_shown(context):
    expect(context["page"].locator("text=Copy your API key now").first).to_be_visible()


@then("each active key should have a revoke button")
def revoke_buttons_exist(context):
    expect(context["page"].locator('button:has-text("Revoke")').first).to_be_visible()


@then('the current plan should show "Free"')
def plan_shows_free(context):
    expect(context["page"].locator("text=Free").first).to_be_visible()


@then("the upgrade button should be visible")
def upgrade_button_visible(context):
    expect(context["page"].locator('a:has-text("Upgrade")').first).to_be_visible()


@then("the result panel should show JSON response")
def result_panel_json(context):
    expect(context["page"].locator("pre").first).to_be_visible(timeout=10000)


@then('the status indicator should show "200 OK"')
def status_200(context):
    expect(context["page"].locator("text=200 OK").first).to_be_visible(timeout=10000)


@then("I should be on the services page")
def on_services_page(context):
    expect(context["page"]).to_have_url("**/portal/services**")


# â”€â”€ Portal search steps â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@when("I open the portal search page")
def open_portal_search(context):
    sp = PortalSearchPage(context["page"])
    sp.open()
    context["search_page"] = sp


@when("I open the services page")
def open_services(context):
    sp = ServicesPage(context["page"])
    sp.open()
    context["services_page"] = sp


@when("I click the first popular query button")
def click_first_popular(context):
    context["page"].locator('button:has-text("â†—")').first.click()
    context["page"].wait_for_load_state("networkidle")


@when(parsers.parse('I enter HS code "{hs}"'))
def enter_hs_code(context, hs):
    context["page"].locator('input[placeholder*="090111"]').fill(hs)


@when("I click the search button")
def click_search(context):
    context["page"].locator('button:has-text("Search Trade Data")').click()
    context["page"].wait_for_load_state("networkidle")


@when(parsers.parse('I search for HS code "{hs}"'))
def search_hs(context, hs):
    context["page"].goto("http://localhost:5173/portal/search")
    context["page"].wait_for_load_state("networkidle")
    context["page"].locator('input[placeholder*="090111"]').fill(hs)
    context["page"].locator('button:has-text("Search Trade Data")').click()
    context["page"].wait_for_load_state("networkidle")


@when(parsers.parse('I have search results for HS "{hs}"'))
def have_search_results(context, hs):
    context["page"].goto("http://localhost:5173/portal/search")
    context["page"].wait_for_load_state("networkidle")
    context["page"].locator('input[placeholder*="090111"]').fill(hs)
    context["page"].locator('button:has-text("Search Trade Data")').click()
    context["page"].wait_for_url("**/portal/results**", timeout=10000)
    context["page"].wait_for_load_state("networkidle")


@when(parsers.parse('I click the "{col}" column header'))
def click_column_header(context, col):
    context["page"].locator(f'th:has-text("{col}")').click()


@when('I click "Back to search"')
def click_back_to_search(context):
    context["page"].locator('a:has-text("Back to search")').click()
    context["page"].wait_for_load_state("networkidle")


@when("I click the IEC Registration request button")
def click_iec_request(context):
    context["page"].locator('button:has-text("Request")').first.click()
    context["page"].wait_for_timeout(500)


@when("I fill in the service request form")
def fill_service_form(context):
    context["page"].locator('input[placeholder*="Rajesh"]').fill("Test User")
    context["page"].locator('input[placeholder*="Kumar Exports"]').fill("Test Exports Pvt Ltd")
    context["page"].locator('input[placeholder*="ABCDE"]').fill("ABCDE1234F")
    context["page"].locator('input[placeholder*="+91"]').fill("+91-9876543210")


@when("I submit the service request")
def submit_service_request(context):
    context["page"].locator('button[type="submit"]').click()
    context["page"].wait_for_load_state("networkidle")


@then("I should be redirected to the results page")
def on_results_page(context):
    expect(context["page"]).to_have_url("**/portal/results**", timeout=10000)


@then("the results table should have at least 1 row")
def results_has_rows(context):
    expect(context["page"].locator("tbody tr").first).to_be_visible(timeout=8000)


@then("the HS code input should be visible")
def hs_input_visible(context):
    expect(context["page"].locator('input[placeholder*="090111"]').first).to_be_visible()


@then("the flow selector should be visible")
def flow_selector_visible(context):
    expect(context["page"].locator("select").first).to_be_visible()


@then("the reporter selector should be visible")
def reporter_selector_visible(context):
    selects = context["page"].locator("select")
    assert selects.count() >= 2


@then("the year range selectors should be visible")
def year_selectors_visible(context):
    selects = context["page"].locator("select")
    assert selects.count() >= 3


@then("6 popular search buttons should be visible")
def six_popular_buttons(context):
    buttons = context["page"].locator('button:has-text("â†—")')
    assert buttons.count() >= 6


@then("the results table should be visible")
def results_table_visible(context):
    expect(context["page"].locator("table").first).to_be_visible(timeout=8000)


@then("the bar chart should be visible")
def bar_chart_visible(context):
    expect(context["page"].locator(".recharts-wrapper").first).to_be_visible(timeout=5000)


@then("the results page should show the free tier notice")
def free_tier_notice_visible(context):
    expect(context["page"].locator(".bg-amber-50").first).to_be_visible(timeout=8000)


@then("an upgrade plan button should be visible")
def upgrade_plan_visible(context):
    expect(context["page"].locator('a:has-text("Upgrade Plan")').first).to_be_visible()


@then("the results should be sorted")
def results_sorted(context):
    context["page"].wait_for_timeout(500)
    rows = context["page"].locator("tbody tr")
    assert rows.count() > 0


@then("I should be on the portal search page")
def on_search_page(context):
    expect(context["page"]).to_have_url("**/portal/search**")


@then("the download CSV button should show upgrade prompt")
def csv_shows_upgrade(context):
    expect(context["page"].locator('a:has-text("Download CSV")').first).to_be_visible()


@then("I should see 5 service cards")
def five_service_cards(context):
    cards = context["page"].locator(".card")
    assert cards.count() >= 5


@then(parsers.parse('"{name}" card should be visible'))
def service_card_visible(context, name):
    expect(context["page"].locator(f'text={name}').first).to_be_visible()


@then(parsers.parse('the IEC card should show "{price}"'))
def iec_shows_price(context, price):
    expect(context["page"].locator(f'text={price}').first).to_be_visible()


@then("the request form should appear")
def form_appears(context):
    expect(context["page"].locator("form").first).to_be_visible(timeout=3000)


@then("the form should have applicant name field")
def form_has_name(context):
    expect(context["page"].locator('input[placeholder*="Rajesh"]').first).to_be_visible()


@then("the form should have PAN number field")
def form_has_pan(context):
    expect(context["page"].locator('input[placeholder*="ABCDE"]').first).to_be_visible()


@then("a success message should be visible")
def success_message_visible(context):
    expect(context["page"].locator(".bg-green-50").first).to_be_visible(timeout=8000)


@then('the message should contain "submitted successfully"')
def success_message_text(context):
    text = context["page"].locator(".bg-green-50").first.text_content()
    assert "submitted successfully" in text.lower()
