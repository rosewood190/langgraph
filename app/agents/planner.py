from __future__ import annotations

from app.prompts.planner import PLANNER_PROMPT
from app.services.llm import get_llm_service
from app.state import GraphState, StrategyPlan


def run_planner(state: GraphState) -> dict:
    llm = get_llm_service()
    user_payload = (
        f"题目原文：\n{state.raw_question}\n\n"
        f"题意分析：\n{state.analysis.model_dump_json(indent=2, ensure_ascii=False) if state.analysis else '{}'}"
    )
    strategy = llm.invoke_structured(
        PLANNER_PROMPT,
        user_payload,
        StrategyPlan,
        agent_name="planner",
    )
    return {
        "strategy": strategy,
        "current_step": "planner_completed",
    }
