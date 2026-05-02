from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from langchain_core.messages import HumanMessage

from app.agents.trace import append_agent_trace
from app.state import GraphState


class UserIntent(str, Enum):
    NEW_PROBLEM = "new_problem"
    CONTINUE = "continue"
    STOP = "stop"
    REDO = "redo"
    CODE_REQUEST = "code_request"
    FULL_SOLUTION = "full_solution"
    FOLLOWUP = "followup"
    CHAT = "chat"


@dataclass(frozen=True)
class IntentResult:
    intent: UserIntent
    confidence: float
    reason: str = ""


CONTINUE_WORDS = {"继续", "可以", "好的", "懂了", "明白了", "下一步", "继续讲", "好，继续", "继续吧", "go on", "next", "yes"}
STOP_WORDS = {"不用", "不用了", "不需要", "不要", "停止", "先不用", "算了", "结束", "no", "stop"}
REDO_WORDS = {"没懂", "不懂", "再讲一遍", "重讲", "换种方式", "举个例子", "详细一点", "没太懂", "展开讲讲"}
CODE_REQUEST_HINTS = (
    "代码",
    "实现",
    "程序",
    "源码",
    "python",
    "java",
    "c++",
    "cpp",
    "go",
    "rust",
    "javascript",
    "typescript",
    "code",
)
FULL_SOLUTION_HINTS = ("完整题解", "完整解法", "完整答案", "全部讲完", "一次性", "直接给完整", "full solution")
FOLLOWUP_HINTS = (
    "为什么",
    "复杂度",
    "正确性",
    "证明",
    "怎么想到",
    "怎么理解",
    "能不能优化",
    "还能不能降",
    "边界",
    "样例",
    "举例",
    "解释",
    "什么意思",
    "区别",
)
NEW_PROBLEM_HINTS = (
    "给定",
    "输入",
    "输出",
    "请设计",
    "求",
    "有一个",
    "有 n 个",
    "有n个",
    "数组",
    "字符串",
    "树",
    "图",
    "背包",
    "动态规划",
    "最短路",
    "最大值",
    "最小值",
)
CHAT_HINTS = ("你好", "您好", "hello", "hi", "谢谢", "感谢", "你是谁", "介绍一下")
PROBLEM_STRUCTURAL_PATTERNS = (
    r"\b\d+\s*[<=]\s*[a-zA-Z]\b",
    r"\b[a-zA-Z]\s*[<=]\s*\d+\b",
    r"o\s*\(",
    r"时间复杂度",
    r"空间复杂度",
)


def _normalize(text: str) -> str:
    return "".join(text.lower().strip().split())


def _contains_any(normalized: str, words: tuple[str, ...] | set[str]) -> bool:
    return any(_normalize(word) in normalized for word in words)


def _get_latest_user_input(state: GraphState) -> str:
    messages = state.get("messages", [])
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            return msg.content if isinstance(msg.content, str) else str(msg.content)
    return ""


def _problem_score(text: str) -> int:
    stripped = text.strip()
    normalized = _normalize(stripped)
    score = 0

    if len(stripped) >= 20:
        score += 1
    if len(stripped) >= 60:
        score += 1
    if _contains_any(normalized, NEW_PROBLEM_HINTS):
        score += 2
    if "输入" in normalized and "输出" in normalized:
        score += 3
    if "约束" in normalized or "限制" in normalized or "数据范围" in normalized:
        score += 2
    if re.search(r"\b(n|m|k|v|w)\b", stripped, re.IGNORECASE) and any(token in normalized for token in ("求", "最大", "最小", "方案", "路径")):
        score += 1
    if any(re.search(pattern, normalized, re.IGNORECASE) for pattern in PROBLEM_STRUCTURAL_PATTERNS):
        score += 1
    return score


def _looks_like_new_problem(text: str) -> bool:
    normalized = _normalize(text)
    if _contains_any(normalized, CHAT_HINTS) and len(text.strip()) < 20:
        return False
    return _problem_score(text) >= 3


def _has_explicit_full_solution_request(normalized: str) -> bool:
    return _contains_any(normalized, FULL_SOLUTION_HINTS)


def _has_explicit_code_request(normalized: str) -> bool:
    if not _contains_any(normalized, CODE_REQUEST_HINTS):
        return False
    request_markers = (
        "直接",
        "给我",
        "给出",
        "输出",
        "写",
        "实现",
        "源码",
        "代码",
        "code",
        "用",
        "改成",
        "版本",
    )
    language_markers = ("python", "java", "c++", "cpp", "go", "rust", "javascript", "typescript")
    return _contains_any(normalized, request_markers) or _contains_any(normalized, language_markers)


def classify_user_intent(state: GraphState) -> IntentResult:
    text = _get_latest_user_input(state)
    stripped = text.strip()
    normalized = _normalize(stripped)
    awaiting_feedback = state.get("awaiting_user_feedback", False)

    if not stripped:
        return IntentResult(UserIntent.CHAT, 1.0, "empty input")

    if normalized in {_normalize(word) for word in STOP_WORDS}:
        return IntentResult(UserIntent.STOP, 0.95, "explicit stop")

    if normalized in {_normalize(word) for word in CONTINUE_WORDS}:
        return IntentResult(UserIntent.CONTINUE, 0.95, "explicit continue")

    if normalized in {_normalize(word) for word in REDO_WORDS} or _contains_any(normalized, REDO_WORDS):
        return IntentResult(UserIntent.REDO, 0.9, "redo explanation")

    # 优先检查是否是新问题（完整题目描述）
    # 这样可以避免题目中的"编写程序"等词被误判为代码请求
    looks_like_problem = _looks_like_new_problem(stripped)
    has_full_solution_req = _has_explicit_full_solution_request(normalized)
    has_code_req = _has_explicit_code_request(normalized)

    # 如果看起来像新问题，且有明确的完整题解请求
    if looks_like_problem and has_full_solution_req:
        return IntentResult(UserIntent.FULL_SOLUTION, 0.9, "explicit full solution request")

    # 如果看起来像新问题，且有明确的代码请求（如"直接给我代码"、"用Python写"）
    # 但要排除题目描述中常见的"请编写程序"这种表述
    if looks_like_problem and has_code_req:
        # 检查是否有强烈的直接代码请求信号
        strong_code_request = any(marker in normalized for marker in ("直接给", "直接写", "只要代码", "只给代码"))
        language_specified = any(lang in normalized for lang in ("python", "java", "c++", "cpp", "go", "rust", "javascript", "typescript"))
        
        if strong_code_request or language_specified:
            return IntentResult(UserIntent.CODE_REQUEST, 0.9, "explicit code or language request")
        else:
            # 题目描述中的"编写程序"不算代码请求
            return IntentResult(UserIntent.NEW_PROBLEM, 0.85, "problem-like structure")

    # 如果看起来像新问题，优先识别为新问题
    if looks_like_problem:
        return IntentResult(UserIntent.NEW_PROBLEM, 0.85, "problem-like structure")

    # 不像新问题，但有完整题解请求
    if has_full_solution_req:
        return IntentResult(UserIntent.FULL_SOLUTION, 0.9, "explicit full solution request")

    # 不像新问题，但有代码请求
    if has_code_req:
        return IntentResult(UserIntent.CODE_REQUEST, 0.9, "explicit code or language request")

    if _contains_any(normalized, FOLLOWUP_HINTS):
        return IntentResult(UserIntent.FOLLOWUP, 0.8, "followup question")

    if awaiting_feedback:
        return IntentResult(UserIntent.FOLLOWUP, 0.55, "awaiting feedback fallback")

    return IntentResult(UserIntent.CHAT, 0.7, "default chat")


def _next_route_for_stage(stage: str) -> str:
    if stage == "analysis":
        return "planner"
    if stage == "strategy":
        return "pseudocode"
    return "followup"


def run_orchestrator(state: GraphState) -> dict:
    state = {**state, "agent_trace": []}
    user_input = _get_latest_user_input(state)
    teaching_stage = state.get("teaching_stage", "analysis")
    intent_result = classify_user_intent(state)
    intent = intent_result.intent
    agent_trace = append_agent_trace(state, "orchestrator")

    if intent == UserIntent.NEW_PROBLEM:
        return {
            "orchestrator_route": "analyst",
            "agent_trace": agent_trace,
            "problem_text": user_input,
            "teaching_stage": "analysis",
            "awaiting_user_feedback": False,
            "last_teaching_node": "analyst",
            "response_mode": "analysis_only",
            "retry_count": 0,
            "analysis": None,
            "strategy": None,
            "pseudocode": None,
            "code_result": None,
            "code_execution": None,
            "verification": None,
        }

    if intent == UserIntent.CONTINUE:
        next_route = _next_route_for_stage(teaching_stage)
        next_mode = "strategy_only" if next_route == "planner" else "implementation_only"
        return {
            "orchestrator_route": next_route,
            "agent_trace": agent_trace,
            "awaiting_user_feedback": False,
            "response_mode": next_mode,
        }

    if intent == UserIntent.STOP:
        return {
            "orchestrator_route": "chat",
            "agent_trace": agent_trace,
            "awaiting_user_feedback": False,
            "teaching_stage": "done",
            "response_mode": "chat",
        }

    if intent == UserIntent.REDO:
        return {
            "orchestrator_route": "followup",
            "agent_trace": agent_trace,
            "awaiting_user_feedback": True,
            "response_mode": "followup",
        }

    if intent == UserIntent.FULL_SOLUTION:
        return {
            "orchestrator_route": "analyst",
            "agent_trace": agent_trace,
            "problem_text": user_input,
            "awaiting_user_feedback": False,
            "last_teaching_node": "analyst",
            "response_mode": "full_solution",
            "retry_count": 0,
            "analysis": None,
            "strategy": None,
            "pseudocode": None,
            "code_result": None,
            "code_execution": None,
            "verification": None,
        }

    if intent == UserIntent.CODE_REQUEST:
        return {
            "orchestrator_route": "analyst",
            "agent_trace": agent_trace,
            "problem_text": user_input,
            "awaiting_user_feedback": False,
            "last_teaching_node": "analyst",
            "response_mode": "code_only",
            "retry_count": 0,
            "analysis": None,
            "strategy": None,
            "pseudocode": None,
            "code_result": None,
            "code_execution": None,
            "verification": None,
        }

    if intent == UserIntent.FOLLOWUP:
        return {
            "orchestrator_route": "followup",
            "agent_trace": agent_trace,
            "response_mode": "followup",
        }

    return {
        "orchestrator_route": "chat",
        "agent_trace": agent_trace,
        "response_mode": "chat",
    }
