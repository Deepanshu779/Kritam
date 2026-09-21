import os
import urllib.parse


class BrowserManager:

    WEBSITES = {
        "youtube": "https://www.youtube.com",
        "google": "https://www.google.com",
        "github": "https://github.com",
        "gmail": "https://mail.google.com",
    }

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
