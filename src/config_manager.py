import json
import os
import sys


def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


DEFAULT_CONFIG = {
    "pixel_size": 8,
    "num_colors": 16,
    "grid_lines": False,
    "outline": False,
    "image_format": "PNG",
    "video_format": "MP4",
    "theme": "Catppuccin Mocha",
    "output_dir": "",
    "last_open_dir": "",
}


class ConfigManager:
    def __init__(self):
        self.base_dir = get_base_dir()
        self.config_path = os.path.join(self.base_dir, "config.json")
        self.config = dict(DEFAULT_CONFIG)
        if not self.config["output_dir"]:
            self.config["output_dir"] = os.path.join(self.base_dir, "output")
        self.load()

    def load(self):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                self.config.update(saved)
        except (json.JSONDecodeError, IOError):
            pass
        self._ensure_dirs()

    def save(self):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except IOError:
            pass

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save()

    def set_many(self, updates):
        self.config.update(updates)
        self.save()

    def _ensure_dirs(self):
        for d in [self.config["output_dir"], os.path.join(self.base_dir, "tmp")]:
            os.makedirs(d, exist_ok=True)
