from __future__ import annotations

import json
from pathlib import Path
from typing import Any


MEMORY_DIR = Path(__file__).resolve().parent.parent / "memory"
SESSION_FILE = MEMORY_DIR / "session_state.json"


def ensure_session_file() -> None:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    if not SESSION_FILE.exists():
        SESSION_FILE.write_text("{}", encoding="utf-8")


def load_session_state() -> dict[str, Any]:
    ensure_session_file()
    content = SESSION_FILE.read_text(encoding="utf-8").strip()
    if not content:
        return {}
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def save_session_state(state: dict[str, Any]) -> None:
    ensure_session_file()
    SESSION_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def clear_session_state() -> None:
    save_session_state({})
