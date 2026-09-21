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
        self._results = []

    def open_website(self, name):
        url = self.WEBSITES.get(name.lower().strip())
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
        try:
            os.startfile("https://www.google.com/search?q=" + urllib.parse.quote_plus(query))
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
            self._page.goto(
                "https://www.google.com/search?q=" + urllib.parse.quote_plus(query),
                wait_until="domcontentloaded",
                timeout=15000,
            )
            self._page.wait_for_timeout(1000)
            links = self._page.locator("a:has(h3)")
            self._results = []

            for index in range(min(5, links.count())):
                link = links.nth(index)
                title = link.locator("h3").inner_text()
                href = link.get_attribute("href")
                self._results.append({"index": index + 1, "title": title, "href": href})
                print(f"{index + 1}. {title} -> {href}")

            return bool(self._results)
        except Exception as error:
            print(f"Browser search error: {error}")
            return False

    def handle_browser_search(self, intent):
        return self.browser_search(intent.get("query", ""))

    def open_result(self, number):
        if self._page is None or not 1 <= number <= len(self._results):
            return False
        try:
            links = self._page.locator("a:has(h3)")
            links.nth(number - 1).click()
            self._page.wait_for_load_state("domcontentloaded", timeout=10000)
            return True
        except Exception as error:
            print(f"Browser result error: {error}")
            return False

    def open_first_result(self):
        return self.open_result(1)

    def handle_open_first_result(self, intent):
        return self.open_first_result()

    def handle_open_result(self, intent):
        return self.open_result(int(intent.get("number", 0)))

    def go_back(self):
        if self._page is None:
            return False
        try:
            self._page.go_back(wait_until="domcontentloaded", timeout=10000)
            return True
        except Exception as error:
            print(f"Browser back error: {error}")
            return False

    def handle_go_back(self, intent):
        return self.go_back()

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
        self._results = []
