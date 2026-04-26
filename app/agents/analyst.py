from __future__ import annotations

from app.prompts.analyst import ANALYST_PROMPT
from app.services.llm import get_llm_service
from app.state import GraphState, ProblemAnalysis


def run_analyst(state: GraphState) -> dict:
    llm = get_llm_service()
    analysis = llm.invoke_structured(
        ANALYST_PROMPT,
        state.raw_question,
        ProblemAnalysis,
        agent_name="analyst",
    )
    return {
        "analysis": analysis,
        "current_step": "analyst_completed",
    }
