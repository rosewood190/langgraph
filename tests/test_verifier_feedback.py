from __future__ import annotations

from app.agents import verifier
from app.agents.verifier import run_verifier
from app.router import route_after_verifier
from app.state import GraphState


def _make_state(**kwargs) -> GraphState:
    defaults: GraphState = {
        "messages": [],
        "problem_text": "demo problem",
        "analysis": None,
        "strategy": None,
        "pseudocode": None,
        "code_result": {
            "language": "C++",
            "cpp_code": "int main( { return 0; }",
            "compile_ready": True,
        },
        "code_execution": {
            "language": "C++",
            "supported": True,
            "compile_passed": False,
            "run_passed": False,
            "exit_code": 1,
            "stdout": "",
            "stderr": "main.cpp:1: error: expected ')'",
            "error_stage": "compile",
            "message": "代码未通过 Wandbox 在线编译或语法检查。",
        },
        "verification": None,
        "orchestrator_route": "coder",
        "retry_count": 0,
        "max_retry": 1,
        "mode": "teaching",
        "teaching_stage": "implementation",
        "awaiting_user_feedback": False,
        "last_teaching_node": "implementation",
        "response_mode": "implementation_only",
        "response_text": "",
    }
    defaults.update(kwargs)
    return defaults


def test_verifier_routes_execution_compile_error_back_to_coder(monkeypatch) -> None:
    def fail_if_called():
        raise AssertionError("LLM should not be called for deterministic execution failures")

    monkeypatch.setattr(verifier, "get_llm_service", fail_if_called)

    updates = run_verifier(_make_state())
    verification = updates["verification"]

    assert verification["passed"] is False
    assert verification["rollback_target"] == "coder"
    assert "expected" in "；".join(verification["issues"])
    assert "expected" in "；".join(verification["improvement_suggestions"])
    assert updates["retry_count"] == 1
    assert updates["messages"]

    routed_state = _make_state(verification=verification, retry_count=updates["retry_count"])
    assert route_after_verifier(routed_state) == "coder"


def test_verifier_does_not_force_network_error_to_fail(monkeypatch) -> None:
    class FakeLLMService:
        def invoke_structured(self, system_prompt, user_payload, schema, agent_name="unknown"):
            return schema(
                passed=True,
                issues=[],
                rollback_target="",
                improvement_suggestions=["在线服务异常已作为风险提示记录。"],
            )

    monkeypatch.setattr(verifier, "get_llm_service", lambda: FakeLLMService())

    state = _make_state(
        code_execution={
            "language": "C++",
            "supported": True,
            "compile_passed": False,
            "run_passed": False,
            "exit_code": None,
            "stdout": "",
            "stderr": "在线代码检查请求失败",
            "error_stage": "network",
            "message": "在线代码检查请求失败。",
        }
    )
    updates = run_verifier(state)

    assert updates["verification"]["passed"] is True
    assert route_after_verifier(_make_state(verification=updates["verification"])) == "formatter"
