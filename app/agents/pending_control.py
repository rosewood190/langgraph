from __future__ import annotations

from app.state import GraphState


def run_pending_control(state: GraphState) -> dict:
    pending_question = state.pending_question.strip()
    if not pending_question:
        return {
            "response_text": "我没有找到上一道待继续的问题，请重新输入题目。",
            "response_mode": "stop",
            "current_step": "pending_control_completed",
        }

    return {
        "raw_question": pending_question,
        "response_mode": "full_solution",
        "current_step": "pending_control_completed",
    }
