from __future__ import annotations

from app.prompts.chat import CHAT_PROMPT
from app.services.llm import get_llm_service
from app.state import GraphState


def run_algorithm_followup(state: GraphState) -> dict:
    llm = get_llm_service()
    payload = (
        f"历史上下文：\n{state.memory_text}\n\n"
        f"最近算法题：\n{state.last_algorithm_question or '无'}\n\n"
        f"最近问题分析：\n{state.last_analysis_text or '无'}\n\n"
        f"最近策略：\n{state.last_strategy_text or '无'}\n\n"
        f"最近伪代码：\n{state.last_pseudocode_text or '无'}\n\n"
        f"最近 C++ 代码：\n{state.last_cpp_code_text or '无'}\n\n"
        f"最近复杂度：\n{state.last_complexity_text or '无'}\n\n"
        f"当前用户追问：\n{state.raw_question}\n\n"
        "请基于最近算法题上下文，用自然、清晰、对话式中文回答，不要重新输出固定模板标题。"
    )
    reply = llm.invoke_text(CHAT_PROMPT, payload)
    return {
        "response_text": reply,
        "response_mode": "followup",
        "current_step": "algorithm_followup_completed",
    }
