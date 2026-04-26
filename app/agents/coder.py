from __future__ import annotations

from app.prompts.coder import CODER_PROMPT
from app.services.llm import get_llm_service
from app.state import CodeResult, GraphState


def run_coder(state: GraphState) -> dict:
    llm = get_llm_service()
    suggestions = []
    if state.verification and state.verification.improvement_suggestions:
        suggestions = state.verification.improvement_suggestions

    user_payload = (
        f"题目原文：\n{state.raw_question}\n\n"
        f"题意分析：\n{state.analysis.model_dump_json(indent=2, ensure_ascii=False) if state.analysis else '{}'}\n\n"
        f"算法策略：\n{state.strategy.model_dump_json(indent=2, ensure_ascii=False) if state.strategy else '{}'}\n\n"
        f"伪代码：\n{state.pseudocode.model_dump_json(indent=2, ensure_ascii=False) if state.pseudocode else '{}'}\n\n"
        f"改进建议：\n{suggestions}"
    )
    code_result = llm.invoke_structured(
        CODER_PROMPT,
        user_payload,
        CodeResult,
        agent_name="coder",
    )
    return {
        "code_result": code_result,
        "current_step": "coder_completed",
    }
