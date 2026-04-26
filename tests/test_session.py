from app.services.session import clear_session_state, load_session_state, save_session_state


def test_session_state_save_and_clear() -> None:
    save_session_state({"pending_algorithm": True, "question": "01背包"})
    state = load_session_state()
    assert state.get("pending_algorithm") is True
    assert state.get("question") == "01背包"

    clear_session_state()
    cleared = load_session_state()
    assert cleared == {}
