from app.agents.chat_agent import PENDING_ALGORITHM_CHAT_NOTE
from app.main import build_user_response, clear_runtime_state, sync_session_state_after_response
from app.services.memory import append_turn, get_memory_text, load_memory, save_memory_lines
from app.services.session import load_session_state, save_session_state


def test_memory_without_line_limit() -> None:
    save_memory_lines([])
    for i in range(30):
        append_turn(f"u{i}", f"a{i}")

    history = load_memory()
    assert len(history) == 60
    assert history[0] == "User: u0"
    assert history[-1] == "Assistant: a29"


def test_clear_runtime_state() -> None:
    append_turn("你好", "你好")
    save_session_state({"pending_algorithm": True, "question": "测试题"})

    clear_runtime_state()

    assert get_memory_text() == "无历史上下文。"
    assert load_session_state() == {}


def test_build_user_response_for_chat() -> None:
    answer = build_user_response({"response_text": f"今天天气不错{PENDING_ALGORITHM_CHAT_NOTE}"})
    assert answer == f"今天天气不错{PENDING_ALGORITHM_CHAT_NOTE}"


def test_build_user_response_for_analysis_only() -> None:
    answer = build_user_response(
        {
            "response_mode": "analysis_only",
            "final_answer": type(
                "FinalAnswerStub",
                (),
                {"analysis_text": "题目摘要：01背包", "strategy_text": "", "pseudocode_text": "", "cpp_code_text": "", "complexity_text": ""},
            )(),
        }
    )
    assert "一、问题分析" in answer
    assert "题目摘要：01背包" in answer


def test_sync_session_state_after_analysis_only() -> None:
    sync_session_state_after_response(
        {
            "response_mode": "analysis_only",
            "raw_question": "01背包",
            "last_algorithm_question": "01背包",
            "last_analysis_text": "题目摘要：01背包",
            "last_strategy_text": "",
            "last_pseudocode_text": "",
            "last_cpp_code_text": "",
            "last_complexity_text": "",
        }
    )
    state = load_session_state()
    assert state.get("pending_algorithm") is True
    assert state.get("question") == "01背包"
    assert state.get("last_algorithm_question") == "01背包"


def test_sync_session_state_after_followup_response() -> None:
    save_session_state({"pending_algorithm": True, "question": "01背包"})
    sync_session_state_after_response(
        {
            "response_mode": "followup",
            "response_text": "可以有别的解法",
            "last_algorithm_question": "01背包",
            "last_analysis_text": "题目摘要：01背包",
            "last_strategy_text": "方案：动态规划",
            "last_pseudocode_text": "...",
            "last_cpp_code_text": "...",
            "last_complexity_text": "时间复杂度：O(NW)",
        }
    )
    state = load_session_state()
    assert state.get("pending_algorithm") is False
    assert state.get("last_algorithm_question") == "01背包"
    assert state.get("last_strategy_text") == "方案：动态规划"
