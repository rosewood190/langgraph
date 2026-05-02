from __future__ import annotations

from app.agents.trace import append_agent_trace, format_agent_trace, prepend_agent_trace
from app.state import GraphState


def test_trace_formats_business_nodes_without_orchestrator() -> None:
    state: GraphState = {
        "messages": [],
        "orchestrator_route": "analyst",
        "retry_count": 0,
        "max_retry": 1,
        "mode": "teaching",
        "teaching_stage": "analysis",
        "awaiting_user_feedback": False,
        "response_mode": "analysis_only",
        "response_text": "",
        "agent_trace": ["orchestrator", "analyst", "planner"],
    }

    assert format_agent_trace(state) == "analyst->planner"
    assert prepend_agent_trace("正文", state) == "analyst->planner\n\n正文"


def test_append_agent_trace_does_not_mutate_input_state() -> None:
    state: GraphState = {
        "messages": [],
        "orchestrator_route": "analyst",
        "retry_count": 0,
        "max_retry": 1,
        "mode": "teaching",
        "teaching_stage": "analysis",
        "awaiting_user_feedback": False,
        "response_mode": "analysis_only",
        "response_text": "",
        "agent_trace": ["orchestrator"],
    }

    updated = append_agent_trace(state, "analyst")

    assert updated == ["orchestrator", "analyst"]
    assert state["agent_trace"] == ["orchestrator"]
