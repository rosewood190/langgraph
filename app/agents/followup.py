from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage

from app.agents.trace import append_agent_trace, prepend_agent_trace
from app.services.llm import get_llm_service
from app.state import GraphState


def _stage_specific_prompt(stage: str) -> str:
    if stage == "analysis":
        return (
            "你正在扮演一位算法老师，当前处于题目拆解阶段。"
            "请优先帮助用户理解题意、输入输出、约束、关键观察和题型判断。"
            "如果用户说没懂，请换一种更通俗的方式解释，可以适当举小例子。"
            "不要直接跳到完整代码实现。"
        )
    if stage == "strategy":
        return (
            "你正在扮演一位算法老师，当前处于策略选择阶段。"
            "请优先解释为什么选这个算法、有没有替代方案、复杂度是否合理、为什么不是别的方法。"
            "如果用户说没懂，请从直觉、思路推导和方案比较角度重讲。"
            "不要直接展开整套完整题解。"
        )
    if stage == "implementation":
        return (
            "你正在扮演一位算法老师，当前处于代码实现阶段。"
            "请优先解释伪代码、实现细节、边界处理、复杂度和代码语言切换相关问题。"
            "如果用户说没懂，请更贴近日常沟通地解释实现过程。"
            "除非用户明确要完整代码，否则不要无条件重复整段代码。"
        )
    return (
        "你正在扮演一位算法老师，正在回答用户对当前算法题的追问。"
        "请结合已有上下文自然回答，不要无条件重新输出完整题解。"
    )


def _followup_guidance(stage: str) -> str:
    if stage == "analysis":
        return "如果现在题目本身已经清楚了，你可以回复“继续”，我就带你进入策略选择；如果还有哪里不明白，也可以继续追问这一部分。"
    if stage == "strategy":
        return "如果这个策略思路已经清楚了，你可以回复“继续”，我就带你进入伪代码和代码实现；如果你想比较别的做法，也可以继续问我。"
    if stage == "implementation":
        return "如果实现部分已经清楚了，你可以让我逐行解释代码、换一种语言实现，或者继续问具体细节。"
    return "如果你觉得这部分已经清楚了，可以回复“继续”，我会根据当前进度带你往下走。"


def _build_messages_for_followup(state: GraphState) -> list[tuple[str, str]]:
    messages = state.get("messages", [])
    stage = state.get("teaching_stage", "analysis")
    result: list[tuple[str, str]] = [("system", _stage_specific_prompt(stage))]
    for msg in messages:
        if isinstance(msg, HumanMessage):
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            result.append(("human", content))
        elif isinstance(msg, AIMessage):
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            result.append(("assistant", content))
    return result


def run_followup(state: GraphState) -> dict:
    llm = get_llm_service()
    stage = state.get("teaching_stage", "analysis")
    chat_messages = _build_messages_for_followup(state)
    raw_llm = llm.llm
    response = raw_llm.invoke(chat_messages)
    reply = response.content if isinstance(response.content, str) else str(response.content)
    state = {**state, "agent_trace": append_agent_trace(state, "followup")}
    reply_with_guidance = f"{reply.strip()}\n\n{_followup_guidance(stage)}"
    reply_with_guidance = prepend_agent_trace(reply_with_guidance, state)
    return {
        "agent_trace": state["agent_trace"],
        "response_text": reply_with_guidance,
        "messages": [AIMessage(content=reply_with_guidance)],
        "awaiting_user_feedback": True,
        "response_mode": "followup",
    }
