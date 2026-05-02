from __future__ import annotations

from langchain_core.messages import HumanMessage

from app.agents.orchestrator import UserIntent, classify_user_intent, run_orchestrator
from app.state import GraphState


def _make_state(user_text: str, **kwargs) -> GraphState:
    defaults: GraphState = {
        "messages": [HumanMessage(content=user_text)],
        "problem_text": "demo problem",
        "analysis": None,
        "strategy": None,
        "pseudocode": None,
        "code_result": None,
        "code_execution": None,
        "verification": None,
        "orchestrator_route": "analyst",
        "retry_count": 0,
        "max_retry": 1,
        "mode": "teaching",
        "teaching_stage": "analysis",
        "awaiting_user_feedback": False,
        "last_teaching_node": "analyst",
        "response_mode": "analysis_only",
        "response_text": "",
    }
    defaults.update(kwargs)
    return defaults


def test_classify_new_algorithm_problem() -> None:
    state = _make_state("给定 n 个物品，每个物品有重量和价值，背包容量为 V，求最大价值。输入包含 n 和 V，输出最大价值。")

    result = classify_user_intent(state)

    assert result.intent == UserIntent.NEW_PROBLEM


def test_classify_short_greeting_as_chat() -> None:
    result = classify_user_intent(_make_state("你好"))

    assert result.intent == UserIntent.CHAT


def test_continue_routes_by_stage() -> None:
    result = run_orchestrator(_make_state("继续", awaiting_user_feedback=True, teaching_stage="analysis"))

    assert result["orchestrator_route"] == "planner"
    assert result["response_mode"] == "strategy_only"


def test_continue_from_strategy_routes_to_implementation() -> None:
    result = run_orchestrator(_make_state("下一步", awaiting_user_feedback=True, teaching_stage="strategy"))

    assert result["orchestrator_route"] == "pseudocode"
    assert result["response_mode"] == "implementation_only"


def test_stop_clears_feedback_state() -> None:
    result = run_orchestrator(_make_state("不用了", awaiting_user_feedback=True, teaching_stage="strategy"))

    assert result["orchestrator_route"] == "chat"
    assert result["awaiting_user_feedback"] is False
    assert result["teaching_stage"] == "done"


def test_redo_routes_to_followup() -> None:
    result = run_orchestrator(_make_state("没太懂，换种方式", awaiting_user_feedback=True))

    assert result["orchestrator_route"] == "followup"
    assert result["response_mode"] == "followup"


def test_code_request_routes_to_analysis_pipeline_for_fresh_problem() -> None:
    result = run_orchestrator(_make_state("直接给我 C++ 代码"))

    assert result["orchestrator_route"] == "analyst"
    assert result["response_mode"] == "code_only"
    assert result["problem_text"] == "直接给我 C++ 代码"


def test_problem_with_direct_code_request_prefers_code_intent() -> None:
    user_text = """直接给我C++代码
题目描述
有 N 种物品和一个容量为 V 的背包，每种物品都有无限件可用。
输入格式
第一行输入两个整数 N 和 V。
输出格式
输出一个整数，表示最大价值。"""

    state = _make_state(user_text)
    classified = classify_user_intent(state)
    result = run_orchestrator(state)

    assert classified.intent == UserIntent.CODE_REQUEST
    assert result["orchestrator_route"] == "analyst"
    assert result["response_mode"] == "code_only"
    assert result["problem_text"] == user_text


def test_problem_with_full_solution_request_prefers_full_solution_intent() -> None:
    user_text = """直接给完整题解
给定 n 个物品，每个物品有重量和价值，背包容量为 V，求最大价值。
输入包含 n 和 V，输出最大价值。"""

    state = _make_state(user_text)
    classified = classify_user_intent(state)
    result = run_orchestrator(state)

    assert classified.intent == UserIntent.FULL_SOLUTION
    assert result["orchestrator_route"] == "analyst"
    assert result["response_mode"] == "full_solution"


def test_followup_question_routes_to_followup() -> None:
    result = run_orchestrator(_make_state("为什么这里时间复杂度是 O(nV)？"))

    assert result["orchestrator_route"] == "followup"
    assert result["response_mode"] == "followup"


def test_new_problem_resets_previous_solution_state() -> None:
    result = run_orchestrator(
        _make_state(
            "给定一个数组 nums，求连续子数组的最大和。输入 n 和数组，输出最大和。",
            analysis={"summary": "old"},
            strategy={"strategy_name": "old"},
            code_result={"language": "C++", "cpp_code": "old", "compile_ready": True},
            code_execution={"language": "C++", "supported": True, "compile_passed": True, "run_passed": True, "exit_code": 0, "stdout": "", "stderr": "", "error_stage": "", "message": ""},
        )
    )

    assert result["orchestrator_route"] == "analyst"
    assert result["analysis"] is None
    assert result["strategy"] is None
    assert result["code_result"] is None
    assert result["code_execution"] is None
