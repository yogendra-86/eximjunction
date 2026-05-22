"""Portal Page Objects — Search, Results, Services pages."""
from playwright.sync_api import Page, expect
from .base_page import BasePage


class PortalSearchPage(BasePage):
    HS_INPUT         = 'input[placeholder*="090111"]'
    KEYWORD_INPUT    = 'input[placeholder*="coffee"]'
    FLOW_SELECT      = 'select'
    SEARCH_BUTTON    = 'button:has-text("Search Trade Data")'
    POPULAR_BUTTONS  = 'button:has-text("↗")'
    PLAN_INFO        = '.grid.grid-cols-2'
    ERROR_BOX        = '.text-red-600'
    LOADING_TEXT     = 'button:has-text("Searching")'

    def open(self):
        self.navigate("/portal/search")
        self.wait_for_load()
        return self

    def search_by_hs(self, hs_code: str, flow: str = "export"):
        self.fill(self.HS_INPUT, hs_code)
        self.search()
        return self

    def search_by_keyword(self, keyword: str):
        self.fill(self.KEYWORD_INPUT, keyword)
        self.search()
        return self

    def search(self):
        self.click(self.SEARCH_BUTTON)
        return self

    def click_popular(self, index: int = 0):
        self.page.locator(self.POPULAR_BUTTONS).nth(index).click()
        return self

    def get_error(self) -> str:
        loc = self.page.locator(self.ERROR_BOX)
        return loc.text_content() if loc.is_visible() else ""

    def is_searching(self) -> bool:
        return self.page.locator(self.LOADING_TEXT).is_visible()

    def expect_redirected_to_results(self):
        self.wait_for_url("/portal/results")


class PortalResultsPage(BasePage):
    TABLE_ROWS      = 'tbody tr'
    CHART           = '.recharts-wrapper'
    EXPORT_BUTTON   = 'button:has-text("Download CSV")'
    UPGRADE_BUTTON  = 'a:has-text("Upgrade Plan")'
    BACK_LINK       = 'a:has-text("Back to search")'
    FREE_NOTICE     = '.bg-amber-50'
    SORT_HEADERS    = 'th'
    RECORD_COUNT    = 'text=/\\d+ records shown/'

    def open(self):
        self.navigate("/portal/results")
        self.wait_for_load()
        return self

    def get_row_count(self) -> int:
        return self.page.locator(self.TABLE_ROWS).count()

    def is_chart_visible(self) -> bool:
        return self.page.locator(self.CHART).is_visible()

    def is_export_available(self) -> bool:
        return self.page.locator(self.EXPORT_BUTTON).is_visible()

    def is_upgrade_prompt_visible(self) -> bool:
        return self.page.locator(self.UPGRADE_BUTTON).is_visible()

    def is_free_tier_notice_visible(self) -> bool:
        return self.page.locator(self.FREE_NOTICE).is_visible()

    def click_export(self):
        self.click(self.EXPORT_BUTTON)

    def click_back(self):
        self.click(self.BACK_LINK)
        self.wait_for_url("/portal/search")

    def sort_by_column(self, column_index: int):
        self.page.locator(self.SORT_HEADERS).nth(column_index).click()

    def get_first_row_hs_code(self) -> str:
        return self.page.locator('tbody tr:first-child td:first-child').text_content()


class ServicesPage(BasePage):
    SERVICE_CARDS    = '.card'
    IEC_CARD         = 'div:has-text("IEC Registration")'
    REQUEST_BUTTONS  = 'button:has-text("Request")'
    FORM             = 'form'
    NAME_INPUT       = 'input[placeholder*="Rajesh"]'
    COMPANY_INPUT    = 'input[placeholder*="Kumar Exports"]'
    PAN_INPUT        = 'input[placeholder*="ABCDE"]'
    MOBILE_INPUT     = 'input[placeholder*="+91"]'
    SUBMIT_BUTTON    = 'button[type="submit"]'
    SUCCESS_BOX      = '.bg-green-50'
    ERROR_BOX        = '.bg-red-50'

    def open(self):
        self.navigate("/portal/services")
        self.wait_for_load()
        return self

    def get_service_count(self) -> int:
        return self.page.locator('.card').count()

    def select_service(self, service_name: str):
        self.page.locator(f'button:has-text("Request"):near(:has-text("{service_name}"))').first.click()
        return self

    def fill_request_form(self, name: str, company: str, pan: str, mobile: str):
        self.fill(self.NAME_INPUT, name)
        self.fill(self.COMPANY_INPUT, company)
        self.fill(self.PAN_INPUT, pan)
        self.fill(self.MOBILE_INPUT, mobile)
        return self

    def submit_request(self):
        self.click(self.SUBMIT_BUTTON)
        return self

    def is_success_visible(self) -> bool:
        return self.page.locator(self.SUCCESS_BOX).is_visible()

    def get_success_message(self) -> str:
        return self.page.locator(self.SUCCESS_BOX).text_content()


class LandingPage(BasePage):
    HERO_HEADING    = 'h1:has-text("Global Trade Data")'
    DEMO_SECTION    = '#demo, section:has-text("Try it right now")'
    DEMO_BUTTONS    = 'button:has-text("India")'
    RESULT_PANEL    = 'pre'
    NAV_PORTAL      = 'a:has-text("Data Portal")'
    NAV_SERVICES    = 'a:has-text("EXIM Services")'
    NAV_PRICING     = 'a:has-text("Pricing")'
    SIGNUP_BTN      = 'a:has-text("Get Started Free")'
    PORTAL_CARD     = 'a:has-text("Open Portal")'
    SERVICES_CARD   = 'a:has-text("View Services")'

    def open(self):
        self.navigate("/")
        self.wait_for_load()
        return self

    def is_hero_visible(self) -> bool:
        return self.page.locator(self.HERO_HEADING).is_visible()

    def is_demo_section_visible(self) -> bool:
        return self.page.locator(self.DEMO_SECTION).is_visible()

    def click_demo_query(self, index: int = 0):
        self.page.locator(self.DEMO_BUTTONS).nth(index).click()

    def wait_for_demo_result(self):
        self.page.locator(self.RESULT_PANEL).wait_for(state="visible", timeout=10000)

    def navigate_to_portal(self):
        self.click(self.NAV_PORTAL)
        self.wait_for_url("/portal/search")

    def navigate_to_pricing(self):
        self.click(self.NAV_PRICING)
        self.wait_for_url("/pricing")

    def navigate_to_signup(self):
        self.click(self.SIGNUP_BTN)
        self.wait_for_url("/signup")

    def click_api_docs(self):
        self.page.locator('a:has-text("API Docs")').click()
