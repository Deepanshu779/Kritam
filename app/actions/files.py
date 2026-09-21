import os


class FileManager:

    FOLDERS = {
        "downloads": lambda: os.path.join(os.path.expanduser("~"), "Downloads"),
        "documents": lambda: os.path.join(os.path.expanduser("~"), "Documents"),
        "desktop": lambda: os.path.join(os.path.expanduser("~"), "Desktop"),
        "pictures": lambda: os.path.join(os.path.expanduser("~"), "Pictures"),
    }

    def open_folder(self, name):
        name = name.lower().strip()
        resolver = self.FOLDERS.get(name)

        if not resolver:
            return False

        path = resolver()

        if not os.path.isdir(path):
            return False

        try:
            os.startfile(path)
            return True
        except (OSError, ValueError):
            return False

    def handle_open_folder(self, intent):
        return self.open_folder(intent.get("folder", ""))
