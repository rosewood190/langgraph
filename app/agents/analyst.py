from __future__ import annotations

from langchain_core.messages import HumanMessage

from app.agents.trace import append_agent_trace
from app.prompts.analyst import ANALYST_PROMPT
from app.services.llm import get_llm_service
from app.state import GraphState, ProblemAnalysis


def _get_latest_user_input(state: GraphState) -> str:
    messages = state.get("messages", [])
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            return msg.content if isinstance(msg.content, str) else str(msg.content)
    return ""


def _get_problem_text(state: GraphState) -> str:
    return state.get("problem_text") or _get_latest_user_input(state)


def run_analyst(state: GraphState) -> dict:
    llm = get_llm_service()
    problem_text = _get_problem_text(state)
    response_mode = state.get("response_mode", "analysis_only")
    
    analysis = llm.invoke_structured(
        ANALYST_PROMPT,
        problem_text,
        ProblemAnalysis,
        agent_name="analyst",
    )
    return {
        "agent_trace": append_agent_trace(state, "analyst"),
        "problem_text": problem_text,
        "analysis": analysis.model_dump(),
        "strategy": None,
        "pseudocode": None,
        "code_result": None,
        "code_execution": None,
        "verification": None,
        "retry_count": 0,
        "teaching_stage": "analysis",
        "awaiting_user_feedback": response_mode == "analysis_only",
        "last_teaching_node": "analyst",
        "response_mode": response_mode,
    }
