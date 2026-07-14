from pathlib import Path
import json


class SettingsManager:
    def __init__(self):
        self.settings_path = Path("config/settings.json")
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)

        self.defaults = {
            "theme": "dark",
            "projects_folder": "projects",
            "exports_folder": "exports",
            "voice": "male",
            "language": "en",
            "resolution": "1920x1080",
            "fps": 30
        }

        self.settings = {}
        self.load()

    def load(self):
        if not self.settings_path.exists():
            self.settings = self.defaults.copy()
            self.save()
            return

        with open(self.settings_path, "r") as f:
            self.settings = json.load(f)

    def save(self):
        with open(self.settings_path, "w") as f:
            json.dump(self.settings, f, indent=4)

    def get(self, key):
        return self.settings.get(key)

    def set(self, key, value):
        self.settings[key] = value
        self.save()