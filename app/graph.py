from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.agents.analyst import run_analyst
from app.agents.chat_agent import run_chat
from app.agents.code_runner import run_code_runner
from app.agents.coder import run_coder
from app.agents.followup import run_followup
from app.agents.formatter import run_formatter
from app.agents.orchestrator import run_orchestrator
from app.agents.planner import run_planner
from app.agents.pseudocode import run_pseudocode
from app.agents.verifier import run_verifier
from app.router import route_after_orchestrator, route_after_verifier
from app.state import GraphState


def build_graph():
    memory = MemorySaver()
    workflow = StateGraph(GraphState)

    workflow.add_node("orchestrator", run_orchestrator)
    workflow.add_node("chat", run_chat)
    workflow.add_node("followup", run_followup)
    workflow.add_node("analyst", run_analyst)
    workflow.add_node("planner", run_planner)
    workflow.add_node("pseudocode", run_pseudocode)
    workflow.add_node("coder", run_coder)
    workflow.add_node("code_runner", run_code_runner)
    workflow.add_node("verifier", run_verifier)
    workflow.add_node("formatter", run_formatter)

    workflow.add_edge(START, "orchestrator")

    workflow.add_conditional_edges(
        "orchestrator",
        route_after_orchestrator,
        {
            "chat": "chat",
            "followup": "followup",
            "analyst": "analyst",
            "planner": "planner",
            "pseudocode": "pseudocode",
            "coder": "coder",
        },
    )

    workflow.add_edge("chat", END)
    workflow.add_edge("followup", END)
    workflow.add_conditional_edges(
        "analyst",
        lambda state: "formatter" if state.get("response_mode") == "analysis_only" else "planner",
        {
            "planner": "planner",
            "formatter": "formatter",
        },
    )
    workflow.add_conditional_edges(
        "planner",
        lambda state: "formatter" if state.get("response_mode") == "strategy_only" else "pseudocode",
        {
            "pseudocode": "pseudocode",
            "formatter": "formatter",
        },
    )
    workflow.add_edge("pseudocode", "coder")
    workflow.add_edge("coder", "code_runner")
    workflow.add_edge("code_runner", "verifier")

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

    return workflow.compile(checkpointer=memory)
