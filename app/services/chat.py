from __future__ import annotations

from pydantic import BaseModel

from app.prompts.chat import CHAT_PROMPT, ROUTER_PROMPT
from app.services.llm import get_llm_service


class ChatRoute(BaseModel):
    route: str
    reason: str = ""


def classify_user_input(user_input: str, memory_text: str) -> ChatRoute:
    llm = get_llm_service()
    payload = f"历史上下文：\n{memory_text}\n\n当前用户输入：\n{user_input}"
    return llm.invoke_structured(ROUTER_PROMPT, payload, ChatRoute, agent_name="router")


def reply_casual_message(user_input: str, memory_text: str) -> str:
    llm = get_llm_service()
    payload = (
        f"历史上下文：\n{memory_text}\n\n"
        f"当前用户输入：\n{user_input}\n\n"
        "请直接给出自然、友好的中文回复。"
    )
    return llm.invoke_text(CHAT_PROMPT, payload)
