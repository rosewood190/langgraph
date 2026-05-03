from __future__ import annotations

import json

from app.agents.trace import append_agent_trace
from app.prompts.planner import PLANNER_PROMPT
from app.services.llm import get_llm_service
from app.state import GraphState, StrategyPlan


def run_planner(state: GraphState) -> dict:
    llm = get_llm_service()
    analysis = state.get("analysis")
    problem_text = state.get("problem_text", "")
    response_mode = state.get("response_mode", "strategy_only")
    mode = state.get("mode", "teaching")
    
    user_payload = (
        f"输出模式：{mode}\n\n"
        f"题目原文：\n{problem_text}\n\n"
        f"题意分析：\n{json.dumps(analysis, ensure_ascii=False, indent=2) if analysis else '{}'}"
    )
    strategy = llm.invoke_structured(
        PLANNER_PROMPT,
        user_payload,
        StrategyPlan,
        agent_name="planner",
    )
    return {
        "agent_trace": append_agent_trace(state, "planner"),
        "strategy": strategy.model_dump(),
        "teaching_stage": "strategy",
        "awaiting_user_feedback": response_mode == "strategy_only",
        "last_teaching_node": "planner",
        "response_mode": response_mode,
    }
