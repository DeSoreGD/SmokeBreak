from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_STATS: dict[str, Any] = {
    "date": "",
    "took_break_count": 0,
    "skipped_count": 0,
    "delay_count": 0,
    "last_break_time": None,
}


class StatsStore:
    def __init__(self, data_dir: Path) -> None:
        self.path = data_dir / "stats.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self.load()
        self.ensure_today()

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            data = self.blank_today()
            self.save_data(data)
            return data
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(loaded, dict):
                raise ValueError("stats root must be an object")
            return {**DEFAULT_STATS, **loaded}
        except (OSError, json.JSONDecodeError, ValueError):
            self.backup_corrupt_file()
            data = self.blank_today()
            self.save_data(data)
            return data

    def blank_today(self) -> dict[str, Any]:
        data = dict(DEFAULT_STATS)
        data["date"] = self.today_key()
        return data

    @staticmethod
    def today_key() -> str:
        return datetime.now().date().isoformat()

    def ensure_today(self) -> None:
        if self.data.get("date") != self.today_key():
            self.data = self.blank_today()
            self.save()

    def increment(self, field: str) -> None:
        self.ensure_today()
        self.data[field] = int(self.data.get(field, 0)) + 1
        if field == "took_break_count":
            self.data["last_break_time"] = datetime.now().isoformat(timespec="seconds")
        self.save()

    def save(self) -> None:
        self.save_data(self.data)

    def save_data(self, data: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def backup_corrupt_file(self) -> None:
        if not self.path.exists():
            return
        backup = self.path.with_suffix(f".corrupt-{datetime.now():%Y%m%d%H%M%S}.json")
        try:
            self.path.replace(backup)
        except OSError:
            pass
