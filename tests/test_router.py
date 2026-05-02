from __future__ import annotations

from app.router import route_after_orchestrator, route_after_verifier
from app.state import GraphState


def _make_state(**kwargs) -> GraphState:
    defaults: GraphState = {
        "messages": [],
        "problem_text": "demo problem",
        "analysis": None,
        "strategy": None,
        "pseudocode": None,
        "code_result": None,
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


def test_route_after_orchestrator_chat() -> None:
    state = _make_state(orchestrator_route="chat")
    assert route_after_orchestrator(state) == "chat"


def test_route_after_orchestrator_analyst() -> None:
    state = _make_state(orchestrator_route="analyst")
    assert route_after_orchestrator(state) == "analyst"


def test_route_after_orchestrator_followup() -> None:
    state = _make_state(orchestrator_route="followup")
    assert route_after_orchestrator(state) == "followup"


def test_route_after_orchestrator_planner() -> None:
    state = _make_state(orchestrator_route="planner")
    assert route_after_orchestrator(state) == "planner"


def test_route_after_orchestrator_pseudocode() -> None:
    state = _make_state(orchestrator_route="pseudocode")
    assert route_after_orchestrator(state) == "pseudocode"


def test_route_after_orchestrator_coder() -> None:
    state = _make_state(orchestrator_route="coder")
    assert route_after_orchestrator(state) == "coder"


def test_route_after_orchestrator_default_when_unknown() -> None:
    state = _make_state(orchestrator_route="unknown_value")
    assert route_after_orchestrator(state) == "analyst"


def test_route_after_verifier_passed() -> None:
    state = _make_state(verification={"passed": True, "issues": [], "rollback_target": "", "improvement_suggestions": []})
    assert route_after_verifier(state) == "formatter"


def test_route_after_verifier_no_verification() -> None:
    state = _make_state(verification=None)
    assert route_after_verifier(state) == "formatter"


def test_route_after_verifier_retry_to_coder() -> None:
    state = _make_state(
        verification={"passed": False, "issues": [], "rollback_target": "coder", "improvement_suggestions": []},
        retry_count=1,
        max_retry=1,
    )
    assert route_after_verifier(state) == "coder"


def test_route_after_verifier_retry_to_planner() -> None:
    state = _make_state(
        verification={"passed": False, "issues": [], "rollback_target": "planner", "improvement_suggestions": []},
        retry_count=1,
        max_retry=1,
    )
    assert route_after_verifier(state) == "planner"


def test_route_after_verifier_exceeds_max_retry() -> None:
    state = _make_state(
        verification={"passed": False, "issues": [], "rollback_target": "coder", "improvement_suggestions": []},
        retry_count=3,
        max_retry=1,
    )
    assert route_after_verifier(state) == "formatter"
