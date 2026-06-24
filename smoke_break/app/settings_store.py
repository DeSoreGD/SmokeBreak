from __future__ import annotations

import json
import sys
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_SETTINGS: dict[str, Any] = {
    "default_timer_minutes": 90,
    "presets": {
        "short": 30,
        "normal": 90,
        "long": 120,
    },
    "selected_audio_path": "",
    "volume": 70,
    "fade_in_enabled": True,
    "fade_in_seconds": 3,
    "play_mode": "play_once",
    "play_duration_minutes": 5,
    "daily_limit_enabled": False,
    "daily_limit": 5,
    "start_minimized_to_tray": False,
    "always_on_top": True,
}


def app_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def merge_settings(defaults: dict[str, Any], loaded: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(defaults)
    for key, value in loaded.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_settings(merged[key], value)
        else:
            merged[key] = value
    return merged


class SettingsStore:
    def __init__(self, data_dir: Path) -> None:
        self.path = data_dir / "settings.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self.load()

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            data = deepcopy(DEFAULT_SETTINGS)
            self.save_data(data)
            return data

        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(loaded, dict):
                raise ValueError("settings root must be an object")
            data = merge_settings(DEFAULT_SETTINGS, loaded)
            return self.sanitize(data)
        except (OSError, json.JSONDecodeError, ValueError):
            self.backup_corrupt_file()
            data = deepcopy(DEFAULT_SETTINGS)
            self.save_data(data)
            return data

    def sanitize(self, data: dict[str, Any]) -> dict[str, Any]:
        data["default_timer_minutes"] = clamp_int(data.get("default_timer_minutes"), 1, 1440, 90)
        presets = data.setdefault("presets", {})
        presets["short"] = clamp_int(presets.get("short"), 1, 1440, 30)
        presets["normal"] = clamp_int(presets.get("normal"), 1, 1440, 90)
        presets["long"] = clamp_int(presets.get("long"), 1, 1440, 120)
        data["volume"] = clamp_int(data.get("volume"), 0, 100, 70)
        data["fade_in_seconds"] = clamp_int(data.get("fade_in_seconds"), 0, 60, 3)
        data["play_mode"] = data.get("play_mode") if data.get("play_mode") in {"play_once", "play_for_duration"} else "play_once"
        data["play_duration_minutes"] = clamp_int(data.get("play_duration_minutes"), 1, 180, 5)
        data["daily_limit"] = clamp_int(data.get("daily_limit"), 1, 99, 5)
        data["fade_in_enabled"] = bool(data.get("fade_in_enabled", True))
        data["daily_limit_enabled"] = bool(data.get("daily_limit_enabled", False))
        data["start_minimized_to_tray"] = bool(data.get("start_minimized_to_tray", False))
        data["always_on_top"] = bool(data.get("always_on_top", True))
        data["selected_audio_path"] = str(data.get("selected_audio_path", ""))
        return data

    def save(self) -> None:
        self.data = self.sanitize(self.data)
        self.save_data(self.data)

    def save_data(self, data: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def reset(self) -> None:
        self.data = deepcopy(DEFAULT_SETTINGS)
        self.save()

    def backup_corrupt_file(self) -> None:
        if not self.path.exists():
            return
        backup = self.path.with_suffix(f".corrupt-{datetime.now():%Y%m%d%H%M%S}.json")
        try:
            self.path.replace(backup)
        except OSError:
            pass


def clamp_int(value: Any, minimum: int, maximum: int, fallback: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = fallback
    return max(minimum, min(maximum, parsed))
