"""Base Page Object — shared methods for all pages."""
from playwright.sync_api import Page, expect
import os

BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:5173")


class BasePage:
    def __init__(self, page: Page):
        self.page = page
        self.base_url = BASE_URL

    def navigate(self, path: str = ""):
        self.page.goto(f"{self.base_url}{path}")

    def get_title(self) -> str:
        return self.page.title()

    def wait_for_load(self):
        self.page.wait_for_load_state("networkidle")

    def take_screenshot(self, name: str):
        self.page.screenshot(path=f"allure-results/screenshots/{name}.png")

    def is_visible(self, selector: str) -> bool:
        return self.page.locator(selector).is_visible()

    def click(self, selector: str):
        self.page.locator(selector).click()

    def fill(self, selector: str, value: str):
        self.page.locator(selector).fill(value)

    def get_text(self, selector: str) -> str:
        return self.page.locator(selector).text_content()

    def wait_for_url(self, url_pattern: str, timeout: int = 10000):
        self.page.wait_for_url(f"**{url_pattern}**", timeout=timeout)

    def expect_url_contains(self, path: str):
        expect(self.page).to_have_url(f"**{path}**")
