import ctypes
import os
from datetime import datetime

from PIL import ImageGrab


USER32 = ctypes.windll.user32

VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
VK_MEDIA_PLAY_PAUSE = 0xB3


class SystemManager:

    def _press_key(self, virtual_key):
        try:
            USER32.keybd_event(virtual_key, 0, 0, 0)
            USER32.keybd_event(virtual_key, 0, 2, 0)
            return True
        except Exception as error:
            print(f"Keyboard action error: {error}")
            return False

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

            # Capture the full Windows desktop. Newer Pillow versions support
            # all_screens/include_layered_windows; keep fallbacks for older
            # Pillow builds so the command still works reliably.
            try:
                image = ImageGrab.grab(
                    all_screens=True,
                    include_layered_windows=True,
                )
            except Exception:
                try:
                    image = ImageGrab.grab(all_screens=True)
                except Exception:
                    image = ImageGrab.grab()

            if image is None or image.width <= 0 or image.height <= 0:
                return False

            image.save(path, "PNG")

            # Verify that Windows actually received a non-empty file.
            return os.path.isfile(path) and os.path.getsize(path) > 0

        except Exception as error:
            print(f"Screenshot error: {error}")
            return False

    def volume_up(self):
        return self._press_key(VK_VOLUME_UP)

    def volume_down(self):
        return self._press_key(VK_VOLUME_DOWN)

    def volume_mute(self):
        return self._press_key(VK_VOLUME_MUTE)

    def media_play_pause(self):
        return self._press_key(VK_MEDIA_PLAY_PAUSE)

    def minimize_window(self):
        try:
            hwnd = USER32.GetForegroundWindow()
            if not hwnd:
                return False
            USER32.ShowWindow(hwnd, 6)
            return True
        except Exception as error:
            print(f"Window minimize error: {error}")
            return False

    def maximize_window(self):
        try:
            hwnd = USER32.GetForegroundWindow()
            if not hwnd:
                return False
            USER32.ShowWindow(hwnd, 3)
            return True
        except Exception as error:
            print(f"Window maximize error: {error}")
            return False

    def handle_screenshot(self, intent):
        return self.take_screenshot()

    def handle_volume_up(self, intent):
        return self.volume_up()

    def handle_volume_down(self, intent):
        return self.volume_down()

    def handle_volume_mute(self, intent):
        return self.volume_mute()

    def handle_media_play_pause(self, intent):
        return self.media_play_pause()

    def handle_minimize_window(self, intent):
        return self.minimize_window()

    def handle_maximize_window(self, intent):
        return self.maximize_window()
