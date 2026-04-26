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


settings = Settings()
