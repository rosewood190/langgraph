from __future__ import annotations

from app.state import GraphState

HIDDEN_TRACE_NODES = {"orchestrator"}


def append_agent_trace(state: GraphState, node_name: str) -> list[str]:
    trace = list(state.get("agent_trace", []))
    trace.append(node_name)
    return trace


def format_agent_trace(state: GraphState) -> str:
    trace = [node for node in state.get("agent_trace", []) if node not in HIDDEN_TRACE_NODES]
    return "->".join(trace)


def prepend_agent_trace(response_text: str, state: GraphState) -> str:
    trace_text = format_agent_trace(state)
    if not trace_text:
        return response_text
    return f"{trace_text}\n\n{response_text}"
