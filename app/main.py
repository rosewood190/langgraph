from __future__ import annotations

import argparse
import uuid

from langchain_core.messages import HumanMessage

from app.config import settings
from app.graph import build_graph
from app.services.langsmith import build_langsmith_config
from app.services.llm import StructuredOutputError
from app.services.progress import progress_indicator

try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.key_binding import KeyBindings
except ImportError:  # pragma: no cover
    PromptSession = None
    KeyBindings = None

WELCOME_MESSAGE = (
    "你好，我是你的算法设计多智能体助手。\n"
    "我会像老师一样分阶段陪你做题：先拆题，再讲策略，最后再落到实现。\n"
    "每一步讲完我都会停下来等你反馈，你可以让我继续、重讲，或者直接切换到代码。输入 exit 可退出对话。"
)
MULTILINE_HINT = "支持长文本输入：Enter 提交，Esc+Enter 插入换行。若终端支持，也可使用 Shift+Enter 换行。"


def _extract_response_text(result: dict) -> str:
    return result.get("response_text", "") or "我已处理了你的请求，但暂时没有可展示的内容。"


def build_multiline_session() -> PromptSession | None:
    if PromptSession is None or KeyBindings is None:
        return None
    bindings = KeyBindings()

    @bindings.add("enter")
    def submit_input(event) -> None:
        buffer = event.current_buffer
        if buffer.complete_state:
            buffer.apply_completion(buffer.complete_state.current_completion)
            return
        buffer.validate_and_handle()

    @bindings.add("escape", "enter")
    def insert_newline(event) -> None:
        event.current_buffer.insert_text("\n")

    try:
        @bindings.add("s-enter")
        def insert_newline_shift(event) -> None:
            event.current_buffer.insert_text("\n")
    except ValueError:
        pass
    return PromptSession(multiline=True, key_bindings=bindings)


def read_user_input(session: PromptSession | None) -> str:
    return input("\nUser> ").strip() if session is None else session.prompt("\nUser> ").strip()


def _initial_state(user_text: str, mode: str) -> dict:
    return {
        "messages": [HumanMessage(content=user_text)],
        "max_retry": settings.max_retry,
        "mode": mode,
        "retry_count": 0,
        "teaching_stage": "analysis",
        "awaiting_user_feedback": False,
        "last_teaching_node": "analyst",
        "response_mode": "analysis_only",
        "problem_text": user_text,
        "response_text": "",
        "orchestrator_route": "analyst",
        "agent_trace": [],
    }


def _next_turn_state(user_text: str) -> dict:
    return {
        "messages": [HumanMessage(content=user_text)],
    }


def interactive_chat(mode: str) -> None:
    graph = build_graph()
    session = build_multiline_session()
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    is_first_turn = True

    langsmith_cfg = build_langsmith_config(
        run_name="algo_agent_graph",
        tags=["algo-agent", "langgraph", mode],
        metadata={"mode": mode},
    )
    if langsmith_cfg:
        config.update(langsmith_cfg)

    print(WELCOME_MESSAGE)
    print(MULTILINE_HINT)

    while True:
        try:
            user_input = read_user_input(session)
        except (EOFError, KeyboardInterrupt):
            print("\n已退出对话。")
            break
        if not user_input:
            continue
        if user_input.lower() == "exit":
            print("已退出对话。")
            break

        try:
            turn_state = _initial_state(user_input, mode) if is_first_turn else _next_turn_state(user_input)
            with progress_indicator("Agent 正在思考"):
                result = graph.invoke(turn_state, config=config)
                answer = _extract_response_text(result)
            is_first_turn = False
            print(f"\nAgent>\n{answer}")
        except StructuredOutputError as exc:
            print("\nAgent>")
            print(f"当前请求处理失败：{exc}")
            print("这通常表示模型返回了不合法的结构化 JSON。你可以重试一次，或缩短问题描述后再试。")
        except Exception as exc:
            print("\nAgent>")
            print(f"当前请求处理失败：{exc}")
            print("请检查 .env 中是否已正确填写 OPENAI_API_KEY，或稍后重试。")


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-agent algorithm design system")
    parser.add_argument("question", nargs="?", type=str, help="Algorithm problem statement. If omitted, starts interactive chat.")
    parser.add_argument("--mode", choices=["teaching", "contest", "interview"], default="teaching", help="Output mode")
    args = parser.parse_args()

    if args.question:
        graph = build_graph()
        thread_id = str(uuid.uuid4())
        config: dict = {"configurable": {"thread_id": thread_id}}
        langsmith_cfg = build_langsmith_config(
            run_name="algo_agent_graph",
            tags=["algo-agent", "langgraph", args.mode],
            metadata={"mode": args.mode},
        )
        if langsmith_cfg:
            config.update(langsmith_cfg)

        try:
            with progress_indicator("Agent 正在思考"):
                result = graph.invoke(_initial_state(args.question, args.mode), config=config)
            print(_extract_response_text(result))
        except StructuredOutputError as exc:
            print(f"请求处理失败：{exc}")
        except Exception as exc:
            print(f"请求处理失败：{exc}")
        return

    interactive_chat(args.mode)


__all__ = ["build_multiline_session", "interactive_chat", "main"]

if __name__ == "__main__":
    main()
