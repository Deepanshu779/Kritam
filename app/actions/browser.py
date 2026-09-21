import os
import urllib.parse


class BrowserManager:

    WEBSITES = {
        "youtube": "https://www.youtube.com",
        "google": "https://www.google.com",
        "github": "https://github.com",
        "gmail": "https://mail.google.com",
    }

    def __init__(self):
        self._playwright = None
        self._browser = None
        self._page = None

    def open_website(self, name):
        name = name.lower().strip()
        url = self.WEBSITES.get(name)
        if not url:
            return False
        try:
            os.startfile(url)
            return True
        except (OSError, ValueError):
            return False

    def handle_open_website(self, intent):
        return self.open_website(intent.get("website", ""))

    def search_web(self, query):
        query = query.strip()
        if not query:
            return False
        url = "https://www.google.com/search?q=" + urllib.parse.quote_plus(query)
        try:
            os.startfile(url)
            return True
        except (OSError, ValueError):
            return False

    def handle_search_web(self, intent):
        return self.search_web(intent.get("query", ""))

    def _ensure_browser(self):
        if self._page is not None:
            return True
        try:
            from playwright.sync_api import sync_playwright
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(headless=False)
            self._page = self._browser.new_page()
            return True
        except Exception as error:
            print(f"Browser automation error: {error}")
            print("Run: python -m playwright install chromium")
            self._close_browser()
            return False

    def browser_search(self, query):
        query = query.strip()
        if not query or not self._ensure_browser():
            return False
        try:
            url = "https://www.google.com/search?q=" + urllib.parse.quote_plus(query)
            self._page.goto(url, wait_until="domcontentloaded", timeout=15000)
            self._page.wait_for_timeout(1200)
            results = self._page.locator("a:has(h3)")
            count = results.count()
            if count == 0:
                print("Kritam Browser: No search results found.")
                return False
            print("Kritam Browser Results:")
            for index in range(min(count, 5)):
                link = results.nth(index)
                title = link.locator("h3").inner_text()
                href = link.get_attribute("href")
                print(f"{index + 1}. {title} -> {href}")
            return True
        except Exception as error:
            print(f"Browser search error: {error}")
            return False

    def handle_browser_search(self, intent):
        return self.browser_search(intent.get("query", ""))

    def open_first_result(self):
        if self._page is None:
            return False
        try:
            results = self._page.locator("a:has(h3)")
            if results.count() == 0:
                return False
            results.first.click()
            self._page.wait_for_load_state("domcontentloaded", timeout=10000)
            return True
        except Exception as error:
            print(f"Browser result error: {error}")
            return False

    def handle_open_first_result(self, intent):
        return self.open_first_result()

    def _close_browser(self):
        try:
            if self._browser:
                self._browser.close()
        except Exception:
            pass
        try:
            if self._playwright:
                self._playwright.stop()
        except Exception:
            pass
        self._browser = None
        self._playwright = None
        self._page = None
