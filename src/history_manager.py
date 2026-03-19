import json
import os
import time
from config_manager import get_base_dir

MAX_HISTORY = 10


class HistoryEntry:
    def __init__(self, input_path, output_path, timestamp=None, media_type="image"):
        self.input_path = input_path
        self.output_path = output_path
        self.timestamp = timestamp or time.time()
        self.media_type = media_type

    def to_dict(self):
        return {
            "input_path": self.input_path,
            "output_path": self.output_path,
            "timestamp": self.timestamp,
            "media_type": self.media_type,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            d.get("input_path", ""),
            d.get("output_path", ""),
            d.get("timestamp", 0),
            d.get("media_type", "image"),
        )


class HistoryManager:
    def __init__(self):
        self.base_dir = get_base_dir()
        self.history_path = os.path.join(self.base_dir, "history.json")
        self.entries: list[HistoryEntry] = []
        self.load()

    def load(self):
        try:
            if os.path.exists(self.history_path):
                with open(self.history_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.entries = [HistoryEntry.from_dict(e) for e in data]
        except (json.JSONDecodeError, IOError):
            self.entries = []

    def save(self):
        try:
            data = [e.to_dict() for e in self.entries]
            with open(self.history_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except IOError:
            pass

    def add(self, input_path, output_path, media_type="image"):
        entry = HistoryEntry(input_path, output_path, media_type=media_type)
        self.entries.insert(0, entry)
        if len(self.entries) > MAX_HISTORY:
            self.entries = self.entries[:MAX_HISTORY]
        self.save()
        return entry

    def get_all(self):
        return list(self.entries)

    def clear(self):
        self.entries.clear()
        self.save()
