from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage

from app.agents.trace import append_agent_trace, prepend_agent_trace
from app.prompts.chat import CHAT_PROMPT
from app.services.llm import get_llm_service
from app.state import GraphState


def _build_messages_for_chat(state: GraphState) -> list[tuple[str, str]]:
    messages = state.get("messages", [])
    result: list[tuple[str, str]] = [("system", CHAT_PROMPT)]
    for msg in messages:
        if isinstance(msg, HumanMessage):
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            result.append(("human", content))
        elif isinstance(msg, AIMessage):
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            result.append(("assistant", content))
    return result


def run_chat(state: GraphState) -> dict:
    llm = get_llm_service()
    chat_messages = _build_messages_for_chat(state)
    raw_llm = llm.llm
    response = raw_llm.invoke(chat_messages)
    reply = response.content if isinstance(response.content, str) else str(response.content)
    state = {**state, "agent_trace": append_agent_trace(state, "chat")}
    reply = prepend_agent_trace(reply, state)
    return {
        "agent_trace": state["agent_trace"],
        "response_text": reply,
        "messages": [AIMessage(content=reply)],
    }
