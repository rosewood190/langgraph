from __future__ import annotations

from app.prompts.pseudocode import PSEUDOCODE_PROMPT
from app.services.llm import get_llm_service
from app.state import GraphState, PseudocodeResult


def run_pseudocode(state: GraphState) -> dict:
    llm = get_llm_service()
    user_payload = (
        f"题意分析：\n{state.analysis.model_dump_json(indent=2, ensure_ascii=False) if state.analysis else '{}'}\n\n"
        f"算法策略：\n{state.strategy.model_dump_json(indent=2, ensure_ascii=False) if state.strategy else '{}'}"
    )
    pseudocode = llm.invoke_structured(
        PSEUDOCODE_PROMPT,
        user_payload,
        PseudocodeResult,
        agent_name="pseudocode",
    )
    return {
        "pseudocode": pseudocode,
        "current_step": "pseudocode_completed",
    }
