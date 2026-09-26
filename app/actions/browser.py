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
        self._context = None
        self._page = None
        self._results = []
        self._user_data_dir = os.path.join(
            os.path.expanduser("~"),
            ".kritam",
            "browser-profile",
        )

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
            os.startfile(
                "https://www.google.com/search?q="
                + urllib.parse.quote_plus(query)
            )
            return True
        except (OSError, ValueError):
            return False

    def handle_search_web(self, intent):
        return self.search_web(intent.get("query", ""))

    def play_music(self, platform, query):
        query = query.strip()
        platform = platform.lower().strip()
        if not query:
            return False

        # Music commands can run from worker threads. Do not reuse the
        # shared Playwright objects here because Playwright is thread-bound.
        try:
            if platform == "youtube":
                search_url = (
                    "https://www.youtube.com/results?search_query="
                    + urllib.parse.quote_plus(query)
                )
                try:
                    import re
                    import urllib.request

                    request = urllib.request.Request(
                        search_url,
                        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
                    )
                    with urllib.request.urlopen(request, timeout=6) as response:
                        html = response.read().decode("utf-8", errors="ignore")

                    match = re.search(r'"videoId":"([A-Za-z0-9_-]{11})"', html)
                    if match:
                        os.startfile(
                            "https://www.youtube.com/watch?v=" + match.group(1)
                        )
                        return True
                except Exception:
                    pass

                # If scraping fails or YouTube blocks bot requests, still open search results
                os.startfile(search_url)
                return True

            if platform == "spotify":
                url = "https://open.spotify.com/search/" + urllib.parse.quote(
                    query, safe=""
                )
                os.startfile(url)
                return True

        except (OSError, ValueError):
            return False

        return False

    def handle_play_music(self, intent):
        return self.play_music(intent.get("platform", ""), intent.get("query", ""))

    def _ensure_browser(self):
        if self._page is not None:
            return True

        try:
            from playwright.sync_api import sync_playwright

            os.makedirs(self._user_data_dir, exist_ok=True)
            self._playwright = sync_playwright().start()
            self._context = self._playwright.chromium.launch_persistent_context(
                self._user_data_dir,
                headless=False,
            )
            pages = self._context.pages
            self._page = pages[0] if pages else self._context.new_page()
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
                "https://www.google.com/search?q="
                + urllib.parse.quote_plus(query),
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
                self._results.append({
                    "index": index + 1,
                    "title": title,
                    "href": href,
                })
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
            self._page.wait_for_load_state(
                "domcontentloaded",
                timeout=10000,
            )
            return True
        except Exception as error:
            print(f"Browser result error: {error}")
            return False

    def handle_open_result(self, intent):
        return self.open_result(int(intent.get("number", 0)))

    def open_result_by_text(self, text):
        if self._page is None or not text.strip():
            return False

        target = text.lower().strip()

        for result in self._results:
            if target in result["title"].lower():
                try:
                    self._page.goto(
                        result["href"],
                        wait_until="domcontentloaded",
                        timeout=10000,
                    )
                    return True
                except Exception as error:
                    print(f"Browser result text error: {error}")
                    return False

        return False

    def handle_open_result_by_text(self, intent):
        return self.open_result_by_text(intent.get("text", ""))

    def go_back(self):
        if self._page is None:
            return False
        try:
            self._page.go_back(
                wait_until="domcontentloaded",
                timeout=10000,
            )
            return True
        except Exception as error:
            print(f"Browser back error: {error}")
            return False

    def handle_go_back(self, intent):
        return self.go_back()

    def new_tab(self):
        if not self._ensure_browser():
            return False
        try:
            self._page = self._context.new_page()
            return True
        except Exception as error:
            print(f"New tab error: {error}")
            return False

    def handle_new_tab(self, intent):
        return self.new_tab()

    def close_tab(self):
        if self._page is None:
            return False
        try:
            self._page.close()
            pages = self._context.pages if self._context else []
            self._page = pages[-1] if pages else None
            return True
        except Exception as error:
            print(f"Close tab error: {error}")
            return False

    def handle_close_tab(self, intent):
        return self.close_tab()

    def _close_browser(self):
        try:
            if self._context:
                self._context.close()
        except Exception:
            pass
        try:
            if self._playwright:
                self._playwright.stop()
        except Exception:
            pass
        self._context = None
        self._playwright = None
        self._page = None
        self._results = []
