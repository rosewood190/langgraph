from __future__ import annotations

import json

from langchain_core.messages import AIMessage

from app.agents.trace import append_agent_trace
from app.prompts.verifier import VERIFIER_PROMPT
from app.services.llm import get_llm_service
from app.state import GraphState, VerificationResult


EXECUTION_ERROR_STAGES = {"compile", "run", "timeout"}


def _build_execution_failure_verification(code_execution: dict) -> dict | None:
    if not code_execution:
        return None

    error_stage = (code_execution.get("error_stage") or "").strip().lower()
    compile_passed = bool(code_execution.get("compile_passed"))
    run_passed = bool(code_execution.get("run_passed"))
    if compile_passed and run_passed:
        return None

    if error_stage not in EXECUTION_ERROR_STAGES and error_stage not in {""}:
        return None

    stdout = code_execution.get("stdout") or ""
    stderr = code_execution.get("stderr") or ""
    message = code_execution.get("message") or "在线编译运行检查未通过。"
    issue_parts = [message]
    if error_stage:
        issue_parts.append(f"错误阶段：{error_stage}")
    if stderr:
        issue_parts.append(f"错误输出：{stderr}")
    if stdout and error_stage == "run":
        issue_parts.append(f"标准输出：{stdout}")

    suggestions = [
        "请根据在线编译运行检查结果修复代码，并保持算法策略不变。",
        "优先修复语法错误、缺失头文件、类型错误、输入输出格式错误或运行时异常。",
    ]
    if stderr:
        suggestions.append(f"错误输出原文：{stderr}")

    return {
        "passed": False,
        "issues": issue_parts,
        "rollback_target": "coder",
        "improvement_suggestions": suggestions,
    }


def _build_retry_feedback(verification_dict: dict, retry_count: int) -> AIMessage:
    issues = verification_dict.get("issues", [])
    suggestions = verification_dict.get("improvement_suggestions", [])
    issues_text = "；".join(issues) if issues else "存在潜在问题"
    suggestions_text = "；".join(suggestions) if suggestions else "请重新检查代码逻辑"
    return AIMessage(
        content=(
            f"[审核反馈 - 第 {retry_count} 次重试]\n"
            f"当前代码未通过审核。\n"
            f"发现的问题：{issues_text}\n"
            f"改进建议：{suggestions_text}\n"
            f"回退目标：{verification_dict.get('rollback_target') or 'coder'}"
        )
    )


def run_verifier(state: GraphState) -> dict:
    analysis = state.get("analysis")
    strategy = state.get("strategy")
    pseudocode = state.get("pseudocode")
    code_result = state.get("code_result")
    code_execution = state.get("code_execution")

    user_payload = (
        f"题目原文（从对话历史中提取）：请结合上下文理解。\n\n"
        f"题意分析：\n{json.dumps(analysis, ensure_ascii=False, indent=2) if analysis else '{}'}\n\n"
        f"算法策略：\n{json.dumps(strategy, ensure_ascii=False, indent=2) if strategy else '{}'}\n\n"
        f"伪代码：\n{json.dumps(pseudocode, ensure_ascii=False, indent=2) if pseudocode else '{}'}\n\n"
        f"代码结果：\n{json.dumps(code_result, ensure_ascii=False, indent=2) if code_result else '{}'}\n\n"
        f"在线编译运行检查结果：\n{json.dumps(code_execution, ensure_ascii=False, indent=2) if code_execution else '{}'}"
    )
    execution_failure = _build_execution_failure_verification(code_execution or {})
    if execution_failure is not None:
        verification_dict = execution_failure
    else:
        llm = get_llm_service()
        verification = llm.invoke_structured(
            VERIFIER_PROMPT,
            user_payload,
            VerificationResult,
            agent_name="verifier",
        )
        verification_dict = verification.model_dump()

    retry_count = state.get("retry_count", 0)
    max_retry = state.get("max_retry", 1)
    updates: dict = {
        "agent_trace": append_agent_trace(state, "verifier"),
        "verification": verification_dict,
        "teaching_stage": "implementation",
        "awaiting_user_feedback": True,
        "last_teaching_node": "implementation",
        "response_mode": state.get("response_mode", "implementation_only"),
    }

    if not verification_dict.get("passed", False) and retry_count <= max_retry:
        retry_count += 1
        updates["retry_count"] = retry_count
        updates["messages"] = [_build_retry_feedback(verification_dict, retry_count)]
    else:
        updates["retry_count"] = retry_count

    return updates
