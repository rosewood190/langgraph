from app.services.memory import append_turn, clear_memory, get_memory_text, save_memory_lines


def test_memory_append_and_load() -> None:
    save_memory_lines([])
    append_turn("你好", "你好，我是助手")
    text = get_memory_text()
    assert "User: 你好" in text
    assert "Assistant: 你好，我是助手" in text


def test_memory_clear() -> None:
    append_turn("测试", "测试回复")
    clear_memory()
    assert get_memory_text() == "无历史上下文。"
