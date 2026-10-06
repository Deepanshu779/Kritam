import html
import os
import queue
import re
import threading
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class SearchResult:
    index: int
    title: str
    url: str
    snippet: str = ""

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)


class BrowserExecutor(threading.Thread):
    """Dedicated background worker thread guaranteeing Playwright thread affinity."""

    def __init__(self):
        super().__init__(name="KritamBrowserWorker", daemon=True)
        self.tasks: queue.Queue = queue.Queue()
        self.start()

    def run(self):
        while True:
            item = self.tasks.get()
            if item is None:
                break
            func, args, kwargs, holder = item
            try:
                holder["result"] = func(*args, **kwargs)
                holder["success"] = True
            except Exception as exc:
                holder["error"] = exc
                holder["success"] = False
            finally:
                holder["done"].set()
                self.tasks.task_done()

    def call(self, func, *args, timeout: float = 20.0, **kwargs) -> Any:
        done = threading.Event()
        holder: Dict[str, Any] = {"done": done, "success": False, "result": None, "error": None}
        self.tasks.put((func, args, kwargs, holder))
        if not done.wait(timeout=timeout):
            return None
        if not holder["success"]:
            return None
        return holder["result"]

    def stop(self):
        self.tasks.put(None)


class BrowserManager:

    WEBSITES = {
        "youtube": "https://www.youtube.com",
        "google": "https://www.google.com",
        "github": "https://github.com",
        "gmail": "https://mail.google.com",
    }

    def __init__(self):
        self._executor = BrowserExecutor()
        self._playwright = None
        self._context = None
        self._page = None
        self._results: List[SearchResult] = []
        self._last_search_query: str = ""
        self._user_data_dir = os.path.join(
            os.path.expanduser("~"),
            ".kritam",
            "browser-profile",
        )

    def open_website(self, name: str) -> bool:
        url = self.WEBSITES.get(name.lower().strip())
        if not url:
            return False
        return self._open_url_in_session(url)

    def handle_open_website(self, intent: Dict[str, Any]) -> bool:
        return self.open_website(intent.get("website", ""))

    def _fetch_search_results(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Fetch and normalize clean search results from DuckDuckGo."""
        query = query.strip()
        if not query:
            return []

        q = urllib.parse.quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={q}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                )
            },
        )
        results: List[SearchResult] = []
        try:
            with urllib.request.urlopen(req, timeout=6) as resp:
                content = resp.read().decode("utf-8", errors="ignore")

            blocks = re.findall(
                r'<div[^>]+class=[\'"][^\'"]*result\s+results_links[^\'"]*[\'"][^>]*>(.*?)(?=<div[^>]+class=[\'"][^\'"]*result\s+results_links|\Z)',
                content,
                re.DOTALL,
            )
            for block in blocks:
                match = re.search(
                    r'<h2[^>]*>\s*<a[^>]+href=[\'"]([^\'"]+)[\'"][^>]*>(.*?)</a>',
                    block,
                    re.DOTALL,
                )
                if match:
                    raw_href = match.group(1)
                    raw_title = match.group(2)
                    if any(bad in raw_href for bad in ["duckduckgo.com/y.js", "bing.com/aclick", "bingv7aa"]):
                        continue
                    clean_title = re.sub(r"<[^>]+>", "", raw_title)
                    clean_title = html.unescape(clean_title).strip()
                    dest_url = raw_href
                    if "uddg=" in raw_href:
                        parsed = urllib.parse.parse_qs(urllib.parse.urlparse(raw_href).query)
                        if "uddg" in parsed and parsed["uddg"]:
                            dest_url = parsed["uddg"][0]
                    if any(bad in dest_url for bad in ["duckduckgo.com/y.js", "bing.com/aclick", "bingv7aa"]):
                        continue
                    if dest_url.startswith("http") and clean_title:
                        results.append(
                            SearchResult(
                                index=len(results) + 1,
                                title=clean_title,
                                url=dest_url,
                            )
                        )
                        if len(results) >= max_results:
                            break
        except Exception as exc:
            print(f"[Kritam Browser] Search fetch notice: {exc}")

        return results

    def search(self, query: str) -> bool:
        """Search the web, normalize and store results, and navigate the active browser."""
        query = query.strip()
        if not query:
            return False

        self._last_search_query = query
        results = self._fetch_search_results(query)
        self._results = results

        search_url = (
            "https://www.google.com/search?q="
            + urllib.parse.quote_plus(query)
        )
        self._open_url_in_session(search_url)
        return True

    def search_web(self, query: str) -> bool:
        return self.search(query)

    def handle_search_web(self, intent: Dict[str, Any]) -> bool:
        return self.search(intent.get("query", ""))

    def browser_search(self, query: str) -> bool:
        return self.search(query)

    def handle_browser_search(self, intent: Dict[str, Any]) -> bool:
        return self.search(intent.get("query", ""))

    def play_music(self, platform: str, query: str) -> bool:
        query = query.strip()
        platform = platform.lower().strip()
        if not query:
            return False

        try:
            if platform == "youtube":
                search_url = (
                    "https://www.youtube.com/results?search_query="
                    + urllib.parse.quote_plus(query)
                )
                try:
                    request = urllib.request.Request(
                        search_url,
                        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
                    )
                    with urllib.request.urlopen(request, timeout=6) as response:
                        html_content = response.read().decode("utf-8", errors="ignore")

                    match = re.search(r'"videoId":"([A-Za-z0-9_-]{11})"', html_content)
                    if match:
                        os.startfile(
                            "https://www.youtube.com/watch?v=" + match.group(1)
                        )
                        return True
                except Exception:
                    pass

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

    def handle_play_music(self, intent: Dict[str, Any]) -> bool:
        return self.play_music(intent.get("platform", ""), intent.get("query", ""))

    def _ensure_browser_locked(self) -> bool:
        """Internal helper executed on the dedicated BrowserExecutor thread."""
        if self._page is not None and not getattr(self._page, "is_closed", lambda: False)():
            return True

        try:
            from playwright.sync_api import sync_playwright

            os.makedirs(self._user_data_dir, exist_ok=True)
            if self._playwright is None:
                self._playwright = sync_playwright().start()
            if self._context is None:
                self._context = self._playwright.chromium.launch_persistent_context(
                    self._user_data_dir,
                    headless=False,
                )
            pages = self._context.pages
            self._page = pages[0] if pages else self._context.new_page()
            return True

        except Exception as error:
            print(f"[Kritam Browser] Playwright notice: {error}")
            self._close_browser_locked()
            return False

    def _ensure_browser(self) -> bool:
        return bool(self._executor.call(self._ensure_browser_locked))

    def _open_url_in_session(self, url: str) -> bool:
        """Open a target URL within the persistent Playwright session or via OS browser."""
        def _nav():
            if self._ensure_browser_locked():
                try:
                    self._page.goto(url, wait_until="domcontentloaded", timeout=12000)
                    return True
                except Exception:
                    pass
            return False

        opened = self._executor.call(_nav)
        if not opened:
            try:
                os.startfile(url)
                opened = True
            except (OSError, ValueError):
                opened = False
        return bool(opened)

    def open_result(self, number: int) -> bool:
        """Open the result at 1-based index from the currently active search results."""
        if not self._results or not (1 <= number <= len(self._results)):
            return False

        result = self._results[number - 1]
        target_url = result["url"] if isinstance(result, dict) else result.url
        return self._open_url_in_session(target_url)

    def handle_open_result(self, intent: Dict[str, Any]) -> bool:
        try:
            num = int(intent.get("number", 1))
        except (ValueError, TypeError):
            num = 1
        return self.open_result(num)

    def open_result_by_text(self, text: str) -> bool:
        """Open the result whose title matches the requested text."""
        if not self._results or not text.strip():
            return False

        target = text.lower().strip()
        for result in self._results:
            title = result["title"] if isinstance(result, dict) else result.title
            if target in title.lower():
                target_url = result["url"] if isinstance(result, dict) else result.url
                return self._open_url_in_session(target_url)

        return False

    def handle_open_result_by_text(self, intent: Dict[str, Any]) -> bool:
        return self.open_result_by_text(intent.get("text", ""))

    def go_back(self) -> bool:
        def _back():
            if self._page is not None:
                try:
                    self._page.go_back(wait_until="domcontentloaded", timeout=10000)
                    return True
                except Exception:
                    pass
            return False
        return bool(self._executor.call(_back))

    def handle_go_back(self, intent: Dict[str, Any]) -> bool:
        return self.go_back()

    def new_tab(self) -> bool:
        def _tab():
            if self._ensure_browser_locked():
                try:
                    self._page = self._context.new_page()
                    return True
                except Exception:
                    pass
            return False
        return bool(self._executor.call(_tab))

    def handle_new_tab(self, intent: Dict[str, Any]) -> bool:
        return self.new_tab()

    def close_tab(self) -> bool:
        def _close():
            if self._page is not None:
                try:
                    self._page.close()
                    pages = self._context.pages if self._context else []
                    self._page = pages[-1] if pages else None
                    return True
                except Exception:
                    pass
            return False
        return bool(self._executor.call(_close))

    def handle_close_tab(self, intent: Dict[str, Any]) -> bool:
        return self.close_tab()

    def _close_browser_locked(self):
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

    def _close_browser(self):
        self._executor.call(self._close_browser_locked)

    def close(self):
        self._close_browser()
        self._executor.stop()
