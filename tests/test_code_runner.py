from __future__ import annotations

from typing import Any

from app.agents import code_runner
from app.agents.code_runner import run_code_runner
from app.state import GraphState


def _make_state(code: str, language: str = "C++") -> GraphState:
    return {
        "messages": [],
        "problem_text": "demo problem",
        "analysis": None,
        "strategy": None,
        "pseudocode": None,
        "code_result": {
            "language": language,
            "cpp_code": code,
            "compile_ready": True,
        },
        "code_execution": None,
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


def test_online_code_runner_passes_compile_and_run(monkeypatch) -> None:
    captured_payload: dict[str, Any] = {}

    def fake_post(payload: dict[str, Any]) -> dict[str, Any]:
        captured_payload.update(payload)
        return {
            "status": "0",
            "signal": "",
            "compiler_output": "",
            "compiler_error": "",
            "compiler_message": "",
            "program_output": "ok\n",
            "program_error": "",
            "program_message": "ok\n",
        }

    monkeypatch.setattr(code_runner, "_post_to_wandbox", fake_post)

    result = run_code_runner(_make_state('#include <iostream>\nint main(){std::cout << "ok\\n";}\n'))["code_execution"]

    assert captured_payload["compiler"] == "gcc-head"
    assert captured_payload["stdin"] == ""
    assert result["language"] == "C++"
    assert result["supported"] is True
    assert result["compile_passed"] is True
    assert result["run_passed"] is True
    assert result["exit_code"] == 0
    assert result["stdout"].strip() == "ok"
    assert result["error_stage"] == ""


def test_online_code_runner_reports_compile_error(monkeypatch) -> None:
    def fake_post(payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "status": "1",
            "signal": "",
            "compiler_output": "",
            "compiler_error": "main.cpp:1: error: expected ';'",
            "compiler_message": "main.cpp:1: error: expected ';'",
            "program_output": "",
            "program_error": "",
            "program_message": "",
        }

    monkeypatch.setattr(code_runner, "_post_to_wandbox", fake_post)

    result = run_code_runner(_make_state("int main( { return 0; }\n"))["code_execution"]

    assert result["language"] == "C++"
    assert result["supported"] is True
    assert result["compile_passed"] is False
    assert result["run_passed"] is False
    assert result["error_stage"] == "compile"
    assert "expected" in result["stderr"]


def test_code_runner_reports_unsupported_language() -> None:
    result = run_code_runner(_make_state("print('ok')\n", language="Ruby"))["code_execution"]

    assert result["language"] == "Ruby"
    assert result["supported"] is False
    assert result["compile_passed"] is False
    assert result["run_passed"] is False
    assert result["error_stage"] == "prepare"
