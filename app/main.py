from __future__ import annotations

import argparse

from app.agents.chat_agent import STOP_ALGORITHM_REPLY
from app.config import settings
from app.graph import build_graph
from app.services.llm import StructuredOutputError
from app.services.memory import append_turn, clear_memory, get_memory_text
from app.services.progress import progress_indicator
from app.services.session import clear_session_state, load_session_state, save_session_state
from app.state import GraphState

try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.key_binding import KeyBindings
except ImportError:  # pragma: no cover
    PromptSession = None
    KeyBindings = None


WELCOME_MESSAGE = (
    "你好，我是你的算法设计多智能体助手。\n"
    "你可以直接输入算法题目，我会先给出问题分析；如果你愿意，我再继续给出算法策略、伪代码和 C++ 实现。\n"
    "也可以和我正常聊天。输入 exit 可退出对话。"
)

MULTILINE_HINT = "支持长文本输入：Enter 提交，Esc+Enter 插入换行。若终端支持，也可使用 Shift+Enter 换行。"


def run_agent_graph(graph, user_input: str, mode: str) -> dict:
    session_state = load_session_state()
    initial_state = GraphState(
        raw_question=user_input,
        mode=mode,
        max_retry=settings.max_retry,
        memory_text=get_memory_text(),
        has_pending_algorithm=bool(session_state.get("pending_algorithm")),
        pending_question=str(session_state.get("question", "")).strip(),
        last_algorithm_question=str(session_state.get("last_algorithm_question", "")).strip(),
        last_analysis_text=str(session_state.get("last_analysis_text", "")).strip(),
        last_strategy_text=str(session_state.get("last_strategy_text", "")).strip(),
        last_pseudocode_text=str(session_state.get("last_pseudocode_text", "")).strip(),
        last_cpp_code_text=str(session_state.get("last_cpp_code_text", "")).strip(),
        last_complexity_text=str(session_state.get("last_complexity_text", "")).strip(),
    )
    return graph.invoke(initial_state)


def build_user_response(result: dict) -> str:
    response_text = result.get("response_text") if isinstance(result, dict) else None
    if isinstance(response_text, str) and response_text.strip():
        return response_text

    final_answer = result.get("final_answer") if isinstance(result, dict) else None
    response_mode = result.get("response_mode") if isinstance(result, dict) else None
    if final_answer:
        if response_mode == "full_solution":
            return (
                "二、算法策略\n"
                f"{final_answer.strategy_text}\n\n"
                f"三、伪代码\n{final_answer.pseudocode_text}\n\n"
                f"四、C++ 实现\n```cpp\n{final_answer.cpp_code_text}\n```\n\n"
                f"五、复杂度分析\n{final_answer.complexity_text}\n\n"
                f"六、审核摘要\n{final_answer.verifier_summary_text or '无'}"
            )
        return (
            "一、问题分析\n"
            f"{final_answer.analysis_text}\n\n"
            "如果你愿意，我可以继续给出这个问题的算法策略、伪代码，以及最终可执行的 C++ 代码。"
        )

    return "我已经处理了你的请求，但暂时未能生成可展示的结果。"


def sync_session_state_after_response(result: dict) -> None:
    response_mode = result.get("response_mode") if isinstance(result, dict) else None
    raw_question = str(result.get("raw_question", "")).strip() if isinstance(result, dict) else ""

    base_state = {
        "pending_algorithm": False,
        "question": "",
        "last_algorithm_question": str(result.get("last_algorithm_question", "")).strip() if isinstance(result, dict) else "",
        "last_analysis_text": str(result.get("last_analysis_text", "")).strip() if isinstance(result, dict) else "",
        "last_strategy_text": str(result.get("last_strategy_text", "")).strip() if isinstance(result, dict) else "",
        "last_pseudocode_text": str(result.get("last_pseudocode_text", "")).strip() if isinstance(result, dict) else "",
        "last_cpp_code_text": str(result.get("last_cpp_code_text", "")).strip() if isinstance(result, dict) else "",
        "last_complexity_text": str(result.get("last_complexity_text", "")).strip() if isinstance(result, dict) else "",
    }

    if response_mode == "analysis_only" and raw_question:
        base_state["pending_algorithm"] = True
        base_state["question"] = raw_question

    save_session_state(base_state)


def clear_runtime_state() -> None:
    clear_memory()
    clear_session_state()


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
    if session is None:
        return input("\nUser> ").strip()
    return session.prompt("\nUser> ").strip()


def interactive_chat(mode: str) -> None:
    graph = build_graph()
    session = build_multiline_session()
    print(WELCOME_MESSAGE)
    print(MULTILINE_HINT)

    while True:
        try:
            user_input = read_user_input(session)
        except (EOFError, KeyboardInterrupt):
            clear_runtime_state()
            print("\n已退出对话。")
            break

        if not user_input:
            continue

        if user_input.lower() == "exit":
            clear_runtime_state()
            print("已退出对话。")
            break

        try:
            with progress_indicator("Agent 正在思考"):
                result = run_agent_graph(graph, user_input, mode)
                sync_session_state_after_response(result)
                answer = build_user_response(result)
            append_turn(user_input, answer)
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
    parser = argparse.ArgumentParser(description="Multi-agent algorithm design MVP")
    parser.add_argument(
        "question",
        nargs="?",
        type=str,
        help="Algorithm problem statement. If omitted, starts interactive chat.",
    )
    parser.add_argument(
        "--mode",
        choices=["teaching", "contest", "interview"],
        default="teaching",
        help="Output mode",
    )
    args = parser.parse_args()

    if args.question:
        graph = build_graph()
        try:
            with progress_indicator("Agent 正在思考"):
                result = run_agent_graph(graph, args.question, args.mode)
                sync_session_state_after_response(result)
                answer = build_user_response(result)
            append_turn(args.question, answer)
            print(answer)
        except StructuredOutputError as exc:
            print(f"请求处理失败：{exc}")
        except Exception as exc:
            print(f"请求处理失败：{exc}")
        finally:
            clear_runtime_state()
        return

    interactive_chat(args.mode)


__all__ = [
    "STOP_ALGORITHM_REPLY",
    "build_user_response",
    "clear_runtime_state",
    "run_agent_graph",
    "sync_session_state_after_response",
]


if __name__ == "__main__":
    main()
