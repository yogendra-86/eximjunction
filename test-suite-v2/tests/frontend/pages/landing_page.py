"""Landing Page Object Model."""
from playwright.sync_api import Page
from .base_page import BasePage


class LandingPage(BasePage):
    HERO_HEADING  = 'h1'
    DEMO_SECTION  = 'section:has-text("Try it right now")'
    NAV_LINKS     = 'nav a'
    SIGNUP_BTN    = 'a:has-text("Get Started Free")'
    PRODUCT_CARDS = '.card'

    def open(self):
        self.navigate("/")
        self.wait_for_load()
        return self

    def is_hero_visible(self) -> bool:
        return self.page.locator(self.HERO_HEADING).first.is_visible()

    def is_demo_visible(self) -> bool:
        return self.page.locator(self.DEMO_SECTION).first.is_visible()

    def click_navbar(self, text: str):
        self.page.locator(f'nav a:has-text("{text}")').first.click()

    def click_signup(self):
        self.page.locator(self.SIGNUP_BTN).first.click()
