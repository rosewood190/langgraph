from __future__ import annotations

from app.prompts.verifier import VERIFIER_PROMPT
from app.services.llm import get_llm_service
from app.state import GraphState, VerificationResult


def run_verifier(state: GraphState) -> dict:
    llm = get_llm_service()
    user_payload = (
        f"题目原文：\n{state.raw_question}\n\n"
        f"题意分析：\n{state.analysis.model_dump_json(indent=2, ensure_ascii=False) if state.analysis else '{}'}\n\n"
        f"算法策略：\n{state.strategy.model_dump_json(indent=2, ensure_ascii=False) if state.strategy else '{}'}\n\n"
        f"伪代码：\n{state.pseudocode.model_dump_json(indent=2, ensure_ascii=False) if state.pseudocode else '{}'}\n\n"
        f"代码结果：\n{state.code_result.model_dump_json(indent=2, ensure_ascii=False) if state.code_result else '{}'}"
    )
    verification = llm.invoke_structured(
        VERIFIER_PROMPT,
        user_payload,
        VerificationResult,
        agent_name="verifier",
    )

    next_retry_count = state.retry_count
    if not verification.passed:
        next_retry_count += 1

    return {
        "verification": verification,
        "retry_count": next_retry_count,
        "current_step": "verifier_completed",
    }
