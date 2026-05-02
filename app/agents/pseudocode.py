from __future__ import annotations

import json

from app.agents.trace import append_agent_trace
from app.prompts.pseudocode import PSEUDOCODE_PROMPT
from app.services.llm import get_llm_service
from app.state import GraphState, PseudocodeResult


def run_pseudocode(state: GraphState) -> dict:
    llm = get_llm_service()
    analysis = state.get("analysis")
    strategy = state.get("strategy")
    user_payload = (
        f"题意分析：\n{json.dumps(analysis, ensure_ascii=False, indent=2) if analysis else '{}'}\n\n"
        f"算法策略：\n{json.dumps(strategy, ensure_ascii=False, indent=2) if strategy else '{}'}"
    )
    pseudocode = llm.invoke_structured(
        PSEUDOCODE_PROMPT,
        user_payload,
        PseudocodeResult,
        agent_name="pseudocode",
    )
    return {
        "agent_trace": append_agent_trace(state, "pseudocode"),
        "pseudocode": pseudocode.model_dump(),
    }
