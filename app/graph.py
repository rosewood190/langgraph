from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.agents.algorithm_followup import run_algorithm_followup
from app.agents.analyst import run_analyst
from app.agents.chat_agent import run_chat
from app.agents.coder import run_coder
from app.agents.formatter import run_formatter
from app.agents.manager import run_manager
from app.agents.pending_control import run_pending_control
from app.agents.planner import run_planner
from app.agents.pseudocode import run_pseudocode
from app.agents.verifier import run_verifier
from app.router import route_after_manager, route_after_pending_control, route_after_verifier
from app.state import GraphState


def build_graph():
    workflow = StateGraph(GraphState)

    workflow.add_node("manager", run_manager)
    workflow.add_node("chat", run_chat)
    workflow.add_node("pending_control", run_pending_control)
    workflow.add_node("algorithm_followup", run_algorithm_followup)
    workflow.add_node("analyst", run_analyst)
    workflow.add_node("planner", run_planner)
    workflow.add_node("pseudocode", run_pseudocode)
    workflow.add_node("coder", run_coder)
    workflow.add_node("verifier", run_verifier)
    workflow.add_node("formatter", run_formatter)

    workflow.add_edge(START, "manager")
    workflow.add_conditional_edges(
        "manager",
        route_after_manager,
        {
            "chat": "chat",
            "pending_control": "pending_control",
            "algorithm_followup": "algorithm_followup",
            "analyst": "analyst",
        },
    )

    workflow.add_conditional_edges(
        "pending_control",
        route_after_pending_control,
        {
            "chat": "chat",
            "analyst": "analyst",
        },
    )

    workflow.add_edge("chat", END)
    workflow.add_edge("algorithm_followup", END)
    workflow.add_edge("analyst", "planner")
    workflow.add_edge("planner", "pseudocode")
    workflow.add_edge("pseudocode", "coder")
    workflow.add_edge("coder", "verifier")

    workflow.add_conditional_edges(
        "verifier",
        route_after_verifier,
        {
            "planner": "planner",
            "coder": "coder",
            "formatter": "formatter",
        },
    )

    workflow.add_edge("formatter", END)

    return workflow.compile()
