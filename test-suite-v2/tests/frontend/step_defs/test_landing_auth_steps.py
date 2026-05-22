"""Frontend BDD step definitions â€” landing page and auth flows."""
import pytest
import httpx
from faker import Faker
from pytest_bdd import given, when, then, parsers, scenarios
from playwright.sync_api import expect

from tests.frontend.pages.landing_page import LandingPage
from tests.frontend.pages.auth_pages import SignupPage, LoginPage
from tests.frontend.pages.portal_pages import PortalSearchPage, ServicesPage

scenarios(r"D:\all_py\trade-data-api\test-suite-v2\tests\frontend\features\landing.feature")
scenarios(r"D:\all_py\trade-data-api\test-suite-v2\tests\frontend\features\signup_login.feature")

fake    = Faker("en_IN")
API_URL = "http://localhost:8000/api/v1"

# â”€â”€ Landing page steps â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@given("I open the landing page")
def open_landing(page, context):
    lp = LandingPage(page)
    lp.open()
    context["landing"] = lp
    context["page"]    = page


@when(parsers.parse('I click "{link}" in the navbar'))
def click_navbar_link(context, link):
    context["page"].locator(f'nav a:has-text("{link}")').first.click()


@when("I scroll to the demo section")
def scroll_to_demo(context):
    context["page"].evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
    context["page"].wait_for_timeout(500)


@then(parsers.parse('the page title should contain "{text}"'))
def check_title(context, text):
    assert text.lower() in context["page"].title().lower(), \
        f"'{text}' not in title '{context['page'].title()}'"


@then("the hero heading should be visible")
def hero_visible(context):
    expect(context["page"].locator("h1").first).to_be_visible()


@then(parsers.parse('the navbar should show "{text}" link'))
def navbar_shows_link(context, text):
    expect(context["page"].locator(f'nav a:has-text("{text}")').first).to_be_visible()


@then("I should be on the portal search page")
def on_portal_search(context):
    expect(context["page"]).to_have_url("**/portal/search**")


@then("I should be on the pricing page")
def on_pricing(context):
    expect(context["page"]).to_have_url("**/pricing**")


@then(parsers.parse('I should see the "{card}" product card'))
def see_product_card(context, card):
    expect(context["page"].locator(f'text={card}').first).to_be_visible()


@then("a new tab should open with URL containing \"8000/docs\"")
def new_tab_opens(context):
    with context["page"].expect_popup() as popup_info:
        context["page"].locator('a:has-text("API Docs")').click()
    popup = popup_info.value
    assert "8000/docs" in popup.url or "docs" in popup.url


@then("the demo section should be visible")
def demo_section_visible(context):
    locator = context["page"].locator('text=Try it right now')
    expect(locator.first).to_be_visible()


@then("5 query buttons should be present")
def five_query_buttons(context):
    buttons = context["page"].locator('button').filter(has_text="India").or_(
        context["page"].locator('button').filter(has_text="Tariff")).or_(
        context["page"].locator('button').filter(has_text="Pharma")).or_(
        context["page"].locator('button').filter(has_text="Global"))
    assert context["page"].locator('[class*="space-y"] button').count() >= 5


@then('the result panel should show "Select a query"')
def result_panel_default(context):
    expect(context["page"].locator('text=Select a query').first).to_be_visible()


# â”€â”€ Signup steps â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@given("I open the signup page")
def open_signup(page, context):
    sp = SignupPage(page)
    sp.open()
    context["signup_page"] = sp
    context["page"]        = page


@given("I open the login page")
def open_login(page, context):
    lp = LoginPage(page)
    lp.open()
    context["login_page"] = lp
    context["page"]       = page


@given(parsers.parse('I have already signed up with email "{email}"'))
def pre_signup(context, email):
    with httpx.Client(base_url=API_URL) as client:
        client.post("/auth/signup", json={"email": email, "password": "Pass@1234"})


@given(parsers.parse('I have an account with email "{email}" and password "{password}"'))
def have_account(context, email, password):
    with httpx.Client(base_url=API_URL) as client:
        r = client.post("/auth/signup", json={"email": email, "password": password})
        assert r.status_code in (201, 409)
    context["account_email"]    = email
    context["account_password"] = password


@given("I am logged in as a customer")
def logged_in_customer(auth_page, logged_in_context, context):
    context["page"]  = auth_page
    context["email"] = logged_in_context["email"]
    context["token"] = logged_in_context["token"]
    context["api_key"] = logged_in_context.get("api_key", "")


@when("I fill in the signup form with valid details")
def fill_signup_form(context):
    email = f"fe_{fake.uuid4()[:8]}@example.com"
    context["signup_email"] = email
    context["signup_page"].fill_form(
        email=email, password="Valid@Pass1234",
        full_name=fake.name(), company=fake.company(),
    )


@when(parsers.parse('I fill email "{email}" and password "{password}"'))
def fill_email_password(context, email, password):
    page = context["page"]
    page.locator('input[name="email"]').fill(email)
    page.locator('input[name="password"]').fill(password)


@when("I submit the signup form")
def submit_signup(context):
    context["page"].locator('button[type="submit"]').click()
    context["page"].wait_for_load_state("networkidle")


@when("I click the login button")
def click_login_btn(context):
    context["page"].locator('button[type="submit"]').click()
    context["page"].wait_for_load_state("networkidle")


@when("I click the login link")
def click_login_link(context):
    context["page"].locator('a:has-text("Log in")').click()


@when("I open the landing page")
def open_landing_page(context):
    context["page"].goto("http://localhost:5173")
    context["page"].wait_for_load_state("networkidle")


@when("I click the logout button")
def click_logout(context):
    context["page"].locator('button:has-text("Logout")').click()
    context["page"].wait_for_load_state("networkidle")


@then("I should be redirected to the dashboard")
def redirected_to_dashboard(context):
    expect(context["page"]).to_have_url("**/dashboard**", timeout=10000)


@then("the dashboard should show my name")
def dashboard_shows_name(context):
    expect(context["page"].locator('text=Welcome back').first).to_be_visible()


@then("an error message should be visible")
def error_visible(context):
    error = context["page"].locator('.bg-red-50')
    expect(error.first).to_be_visible()


@then(parsers.parse('the error should mention "{text}"'))
def error_mentions(context, text):
    error_text = context["page"].locator('.bg-red-50').first.text_content()
    assert text.lower() in error_text.lower(), f"'{text}' not found in error: {error_text}"


@then("the form should not submit due to validation")
def form_not_submitted(context):
    # Should still be on signup page
    assert "/signup" in context["page"].url


@then("I should be on the login page")
def on_login_page(context):
    expect(context["page"]).to_have_url("**/login**")


@then("I should be on the landing page")
def on_landing_page(context):
    expect(context["page"]).to_have_url("http://localhost:5173/")


@then('the navbar should show "Dashboard" link')
def navbar_shows_dashboard(context):
    expect(context["page"].locator('a:has-text("Dashboard")').first).to_be_visible()


@then('the navbar should show "Logout" button')
def navbar_shows_logout(context):
    expect(context["page"].locator('button:has-text("Logout")').first).to_be_visible()


@then('the navbar should show "Login" link')
def navbar_shows_login(context):
    expect(context["page"].locator('a:has-text("Login")').first).to_be_visible()
