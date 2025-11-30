"""JSON persistence helpers for Action Menu."""
from __future__ import annotations

from pathlib import Path
from typing import Optional
import json

from models import AppState


class StorageManager:
    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> AppState:
        if not self.file_path.exists():
            return AppState()
        try:
            with self.file_path.open("r", encoding="utf-8") as fh:
                raw = json.load(fh)
        except json.JSONDecodeError:
            return AppState()
        return AppState.from_dict(raw)

    def save(self, state: AppState) -> None:
        with self.file_path.open("w", encoding="utf-8") as fh:
            json.dump(state.to_dict(), fh, indent=2, ensure_ascii=False)


def get_default_store_path() -> Path:
    return Path(__file__).with_name("action_menu_state.json")
