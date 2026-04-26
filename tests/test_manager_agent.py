from app.state import ManagerDecision


def test_manager_fallback_when_no_pending_algorithm(monkeypatch) -> None:
    from app.agents import manager as manager_module

    monkeypatch.setattr(
        manager_module,
        "get_llm_service",
        lambda: type(
            "FakeService",
            (),
            {
                "invoke_structured": staticmethod(
                    lambda system_prompt, user_payload, schema, agent_name='manager': ManagerDecision(
                        decision="continue_algorithm",
                        target_agent="pending_algorithm",
                        reason="误判继续",
                    )
                )
            },
        )(),
    )

    state = type(
        "StateStub",
        (),
        {
            "memory_text": "无历史上下文。",
            "has_pending_algorithm": False,
            "last_algorithm_question": "",
            "last_strategy_text": "",
            "last_complexity_text": "",
            "raw_question": "继续",
        },
    )()

    result = manager_module.run_manager(state)

    decision = result["manager_decision"]
    assert decision.decision == "casual"
    assert decision.target_agent == "chat"
