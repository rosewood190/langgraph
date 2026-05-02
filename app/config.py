from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE, override=False)


class Settings:
    model_name: str = os.getenv("MODEL_NAME", "qwen-plus")
    api_key: str = os.getenv("OPENAI_API_KEY", "")
    base_url: str = os.getenv(
        "OPENAI_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    temperature: float = float(os.getenv("MODEL_TEMPERATURE", "0"))
    max_retry: int = int(os.getenv("MAX_RETRY", "1"))
    langsmith_tracing: bool = os.getenv("LANGSMITH_TRACING", "false").strip().lower() in {"1", "true", "yes", "on"}
    langsmith_api_key: str = os.getenv("LANGSMITH_API_KEY", "")
    langsmith_endpoint: str = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
    langsmith_project: str = os.getenv("LANGSMITH_PROJECT", "algo-agent-mvp")
    code_runner_base_url: str = os.getenv("CODE_RUNNER_BASE_URL", "https://wandbox.org/api/compile.json")
    code_runner_timeout: float = float(os.getenv("CODE_RUNNER_TIMEOUT", "20"))


settings = Settings()
