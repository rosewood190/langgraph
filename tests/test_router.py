from app.router import route_after_manager, route_after_pending_control, route_after_verifier
from app.state import GraphState, ManagerDecision, VerificationResult


def test_route_after_manager_to_chat() -> None:
    state = GraphState(raw_question="你好", manager_decision=ManagerDecision(decision="casual", target_agent="chat"))
    assert route_after_manager(state) == "chat"


def test_route_after_manager_to_pending_control() -> None:
    state = GraphState(raw_question="继续", manager_decision=ManagerDecision(decision="continue_algorithm", target_agent="pending_algorithm"))
    assert route_after_manager(state) == "pending_control"


def test_route_after_manager_to_algorithm_followup() -> None:
    state = GraphState(raw_question="刚刚那道题还有别的方法吗", manager_decision=ManagerDecision(decision="algorithm_followup", target_agent="algorithm_followup"))
    assert route_after_manager(state) == "algorithm_followup"


def test_route_after_manager_to_analyst() -> None:
    state = GraphState(raw_question="01背包", manager_decision=ManagerDecision(decision="new_algorithm", target_agent="algorithm_graph"))
    assert route_after_manager(state) == "analyst"


def test_route_after_pending_control_to_chat() -> None:
    state = GraphState(raw_question="继续", response_mode="stop")
    assert route_after_pending_control(state) == "chat"


def test_route_after_pending_control_to_analyst() -> None:
    state = GraphState(raw_question="继续", response_mode="full_solution")
    assert route_after_pending_control(state) == "analyst"


def test_route_after_verifier_passed() -> None:
    state = GraphState(raw_question="test")
    state.verification = VerificationResult(passed=True)
    assert route_after_verifier(state) == "formatter"


def test_route_after_verifier_retry_to_coder() -> None:
    state = GraphState(raw_question="test", retry_count=0, max_retry=1)
    state.verification = VerificationResult(passed=False, rollback_target="coder")
    assert route_after_verifier(state) == "coder"


def test_route_after_verifier_stop_when_exceeded() -> None:
    state = GraphState(raw_question="test", retry_count=2, max_retry=1)
    state.verification = VerificationResult(passed=False, rollback_target="planner")
    assert route_after_verifier(state) == "formatter"
