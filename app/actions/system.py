import os
from datetime import datetime

from PIL import ImageGrab


class SystemManager:

    def take_screenshot(self):
        try:
            screenshots_dir = os.path.join(
                os.path.expanduser("~"),
                "Pictures",
                "Kritam Screenshots",
            )
            os.makedirs(screenshots_dir, exist_ok=True)

            filename = datetime.now().strftime(
                "screenshot_%Y%m%d_%H%M%S.png"
            )
            path = os.path.join(screenshots_dir, filename)

            ImageGrab.grab().save(path)
            return True

        except Exception as error:
            print(f"Screenshot error: {error}")
            return False

    def handle_screenshot(self, intent):
        return self.take_screenshot()
