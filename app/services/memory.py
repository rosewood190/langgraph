from __future__ import annotations

from pathlib import Path
from typing import Iterable


MEMORY_DIR = Path(__file__).resolve().parent.parent / "memory"
MEMORY_FILE = MEMORY_DIR / "conversation_memory.txt"


def ensure_memory_file() -> None:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    if not MEMORY_FILE.exists():
        MEMORY_FILE.write_text("", encoding="utf-8")


def load_memory() -> list[str]:
    ensure_memory_file()
    content = MEMORY_FILE.read_text(encoding="utf-8").strip()
    if not content:
        return []
    return [line for line in content.splitlines() if line.strip()]


def save_memory_lines(lines: Iterable[str]) -> None:
    ensure_memory_file()
    cleaned = [line.rstrip() for line in lines if line.strip()]
    MEMORY_FILE.write_text("\n".join(cleaned) + ("\n" if cleaned else ""), encoding="utf-8")


def clear_memory() -> None:
    save_memory_lines([])


def append_turn(user_input: str, assistant_output: str) -> None:
    history = load_memory()
    history.append(f"User: {user_input}")
    history.append(f"Assistant: {assistant_output}")
    save_memory_lines(history)


def get_memory_text() -> str:
    history = load_memory()
    if not history:
        return "无历史上下文。"
    return "\n".join(history)
