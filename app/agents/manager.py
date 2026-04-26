from __future__ import annotations

from app.prompts.manager import MANAGER_PROMPT
from app.services.llm import get_llm_service
from app.state import GraphState, ManagerDecision


def run_manager(state: GraphState) -> dict:
    llm = get_llm_service()
    payload = (
        f"历史上下文：\n{state.memory_text}\n\n"
        f"当前是否存在待继续算法题：\n{state.has_pending_algorithm}\n\n"
        f"最近算法题：\n{state.last_algorithm_question or '无'}\n\n"
        f"最近算法策略摘要：\n{state.last_strategy_text or '无'}\n\n"
        f"最近复杂度摘要：\n{state.last_complexity_text or '无'}\n\n"
        f"当前用户输入：\n{state.raw_question}"
    )
    decision = llm.invoke_structured(
        MANAGER_PROMPT,
        payload,
        ManagerDecision,
        agent_name="manager",
    )

    if not state.has_pending_algorithm and decision.decision in {"continue_algorithm", "stop_algorithm"}:
        decision = ManagerDecision(
            decision="casual",
            target_agent="chat",
            reason="当前不存在待继续算法题，已回退为普通聊天处理。",
        )

    return {
        "manager_decision": decision,
        "current_step": "manager_completed",
    }
