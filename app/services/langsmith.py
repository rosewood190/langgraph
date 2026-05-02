from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from app.config import settings


@lru_cache(maxsize=1)
def configure_langsmith() -> bool:
    if not settings.langsmith_tracing:
        return False

    if not settings.langsmith_api_key:
        raise ValueError("已启用 LANGSMITH_TRACING，但未设置 LANGSMITH_API_KEY。")

    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGSMITH_ENDPOINT"] = settings.langsmith_endpoint
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
    return True


def tracing_enabled() -> bool:
    return configure_langsmith()


def build_langsmith_config(*, run_name: str, tags: list[str] | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    if not tracing_enabled():
        return {}

    return {
        "run_name": run_name,
        "tags": tags or [],
        "metadata": metadata or {},
    }
