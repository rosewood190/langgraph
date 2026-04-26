from __future__ import annotations

from app.services.chat import reply_casual_message
from app.state import GraphState


PENDING_ALGORITHM_CHAT_NOTE = "\n\n如果你之后还想继续刚才那道算法题，直接回复“继续”就可以。"
STOP_ALGORITHM_REPLY = "好的，那我先停在问题分析这一步。你之后如果想继续要算法策略、伪代码或 C++ 代码，可以直接告诉我继续。"


def run_chat(state: GraphState) -> dict:
    decision = state.manager_decision.decision if state.manager_decision else "casual"

    if decision == "stop_algorithm":
        return {
            "response_text": STOP_ALGORITHM_REPLY,
            "response_mode": "stop",
            "current_step": "chat_completed",
        }

    reply = reply_casual_message(state.raw_question, state.memory_text)
    if state.has_pending_algorithm:
        reply = f"{reply}{PENDING_ALGORITHM_CHAT_NOTE}"

    return {
        "response_text": reply,
        "response_mode": "chat",
        "current_step": "chat_completed",
    }
