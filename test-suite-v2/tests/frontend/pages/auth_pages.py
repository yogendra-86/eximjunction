"""Auth Page Objects — Signup and Login pages."""
from playwright.sync_api import Page, expect
from .base_page import BasePage


class SignupPage(BasePage):
    # Selectors
    EMAIL_INPUT    = 'input[name="email"]'
    PASSWORD_INPUT = 'input[name="password"]'
    NAME_INPUT     = 'input[name="full_name"]'
    COMPANY_INPUT  = 'input[name="company_name"]'
    PHONE_INPUT    = 'input[name="phone"]'
    SUBMIT_BUTTON  = 'button[type="submit"]'
    ERROR_BOX      = '.bg-red-50'

    def open(self):
        self.navigate("/signup")
        self.wait_for_load()
        return self

    def fill_form(self, email: str, password: str,
                  full_name: str = "", company: str = "", phone: str = ""):
        self.fill(self.EMAIL_INPUT, email)
        self.fill(self.PASSWORD_INPUT, password)
        if full_name:
            self.fill(self.NAME_INPUT, full_name)
        if company:
            self.fill(self.COMPANY_INPUT, company)
        if phone:
            self.fill(self.PHONE_INPUT, phone)
        return self

    def submit(self):
        self.click(self.SUBMIT_BUTTON)
        return self

    def signup(self, email: str, password: str,
               full_name: str = "Test User", company: str = "Test Co"):
        self.open()
        self.fill_form(email, password, full_name, company)
        self.submit()
        return self

    def get_error_message(self) -> str:
        loc = self.page.locator(self.ERROR_BOX)
        if loc.is_visible():
            return loc.text_content()
        return ""

    def expect_redirected_to_dashboard(self):
        self.wait_for_url("/dashboard")
        self.expect_url_contains("/dashboard")


class LoginPage(BasePage):
    EMAIL_INPUT    = 'input[name="email"]'
    PASSWORD_INPUT = 'input[name="password"]'
    SUBMIT_BUTTON  = 'button[type="submit"]'
    ERROR_BOX      = '.bg-red-50'
    SIGNUP_LINK    = 'a[href="/signup"]'

    def open(self):
        self.navigate("/login")
        self.wait_for_load()
        return self

    def login(self, email: str, password: str):
        self.open()
        self.fill(self.EMAIL_INPUT, email)
        self.fill(self.PASSWORD_INPUT, password)
        self.click(self.SUBMIT_BUTTON)
        return self

    def get_error_message(self) -> str:
        loc = self.page.locator(self.ERROR_BOX)
        if loc.is_visible():
            return loc.text_content()
        return ""

    def expect_redirected_to_dashboard(self):
        self.wait_for_url("/dashboard")

    def click_signup_link(self):
        self.click(self.SIGNUP_LINK)
        self.wait_for_url("/signup")
