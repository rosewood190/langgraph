from __future__ import annotations

from app.state import GraphState


def route_after_manager(state: GraphState) -> str:
    decision = state.manager_decision.decision if state.manager_decision else "new_algorithm"

    if decision == "continue_algorithm":
        return "pending_control"
    if decision == "algorithm_followup":
        return "algorithm_followup"
    if decision in {"stop_algorithm", "casual"}:
        return "chat"
    return "analyst"


def route_after_pending_control(state: GraphState) -> str:
    if state.response_mode == "stop":
        return "chat"
    return "analyst"


def route_after_verifier(state: GraphState) -> str:
    if not state.verification:
        return "formatter"

    if state.verification.passed:
        return "formatter"

    if state.retry_count > state.max_retry:
        return "formatter"

    target = state.verification.rollback_target.strip().lower()
    if target == "planner":
        return "planner"
    if target == "coder":
        return "coder"

    return "formatter"
