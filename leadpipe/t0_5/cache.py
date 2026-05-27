from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


class EnrichmentCache:
    def __init__(self, path: str | Path | None = None, ttl_seconds: int = 30 * 24 * 60 * 60) -> None:
        self.path = Path(path) if path else None
        self.ttl_seconds = ttl_seconds
        self._data: dict[str, dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        if not self.path or not self.path.exists():
            return
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            payload = {}
        if isinstance(payload, dict):
            self._data = payload

    def _save(self) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    def get(self, key: str) -> dict[str, Any] | None:
        entry = self._data.get(key)
        if not entry:
            return None
        created_at = float(entry.get("created_at") or 0)
        if time.time() - created_at > self.ttl_seconds:
            return None
        value = entry.get("value")
        return value if isinstance(value, dict) else None

    def set(self, key: str, value: dict[str, Any]) -> None:
        self._data[key] = {"created_at": time.time(), "value": value}
        self._save()
