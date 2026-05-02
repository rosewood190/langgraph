from __future__ import annotations

import json

from langchain_core.messages import HumanMessage

from app.agents.trace import append_agent_trace
from app.prompts.coder import CODER_PROMPT
from app.services.llm import get_llm_service
from app.state import GraphState, CodeResult


TARGET_LANGUAGES = {
    "python": "Python",
    "py": "Python",
    "python3": "Python",
    "java": "Java",
    "c++": "C++",
    "cpp": "C++",
    "cxx": "C++",
    "golang": "Go",
    "go": "Go",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "typescript": "TypeScript",
    "ts": "TypeScript",
    "rust": "Rust",
}


def _get_latest_user_input(state: GraphState) -> str:
    messages = state.get("messages", [])
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            return msg.content if isinstance(msg.content, str) else str(msg.content)
    return ""


def _detect_target_language(user_input: str, current_language: str) -> str:
    normalized = user_input.lower().replace(" ", "")
    for token, language in TARGET_LANGUAGES.items():
        if token in normalized:
            return language
    return current_language or "C++"


def run_coder(state: GraphState) -> dict:
    llm = get_llm_service()
    analysis = state.get("analysis")
    strategy = state.get("strategy")
    pseudocode = state.get("pseudocode")
    verification = state.get("verification")
    code_execution = state.get("code_execution")
    existing_code = state.get("code_result") or {}
    user_input = _get_latest_user_input(state)

    suggestions = []
    if verification and verification.get("improvement_suggestions"):
        suggestions = verification.get("improvement_suggestions", [])

    repair_context = {
        "has_previous_code": bool(existing_code),
        "previous_code_language": existing_code.get("language", ""),
        "online_check_passed": bool(code_execution and code_execution.get("compile_passed") and code_execution.get("run_passed")),
        "online_error_stage": (code_execution or {}).get("error_stage", ""),
        "online_error_message": (code_execution or {}).get("message", ""),
        "online_stderr": (code_execution or {}).get("stderr", ""),
        "verification_passed": bool(verification and verification.get("passed")),
        "rollback_target": (verification or {}).get("rollback_target", ""),
    }

    target_language = _detect_target_language(user_input, existing_code.get("language", "C++"))
    direct_code_request = bool(user_input) and any(token in user_input.lower() for token in ["代码", "code", "实现", "改成", "python", "java", "c++", "cpp", "go", "rust", "javascript", "typescript"])

    user_payload = (
        f"用户当前请求：\n{user_input}\n\n"
        f"目标语言：{target_language}\n\n"
        f"题意分析：\n{json.dumps(analysis, ensure_ascii=False, indent=2) if analysis else '{}'}\n\n"
        f"算法策略：\n{json.dumps(strategy, ensure_ascii=False, indent=2) if strategy else '{}'}\n\n"
        f"伪代码：\n{json.dumps(pseudocode, ensure_ascii=False, indent=2) if pseudocode else '{}'}\n\n"
        f"已有代码：\n{json.dumps(existing_code, ensure_ascii=False, indent=2) if existing_code else '{}'}\n\n"
        f"上一次在线编译运行检查结果：\n{json.dumps(code_execution, ensure_ascii=False, indent=2) if code_execution else '{}'}\n\n"
        f"审核修复上下文：\n{json.dumps(repair_context, ensure_ascii=False, indent=2)}\n\n"
        f"改进建议：\n{json.dumps(suggestions, ensure_ascii=False)}"
    )
    code_result = llm.invoke_structured(
        CODER_PROMPT,
        user_payload,
        CodeResult,
        agent_name="coder",
    )
    code_result_dict = code_result.model_dump()
    code_result_dict["language"] = target_language
    return {
        "agent_trace": append_agent_trace(state, "coder"),
        "code_result": code_result_dict,
        "response_mode": "code_only" if direct_code_request else state.get("response_mode", "implementation_only"),
    }
