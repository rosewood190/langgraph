from __future__ import annotations

from app.state import GraphState


def route_after_orchestrator(state: GraphState) -> str:
    route = state.get("orchestrator_route", "analyst")
    if route in {"chat", "followup", "analyst", "planner", "pseudocode", "coder"}:
        return route
    return "analyst"


def route_after_verifier(state: GraphState) -> str:
    verification = state.get("verification")
    if verification is None:
        return "formatter"

    if verification.get("passed", False):
        return "formatter"

    retry_count = state.get("retry_count", 0)
    max_retry = state.get("max_retry", 1)
    if retry_count > max_retry:
        return "formatter"

    target = (verification.get("rollback_target", "") or "coder").strip().lower()
    if target == "planner":
        return "planner"
    return "coder"
