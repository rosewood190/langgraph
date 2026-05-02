from __future__ import annotations

from langchain_core.messages import HumanMessage

from app.agents import analyst, code_runner, coder, planner, pseudocode, verifier
from app.graph import build_graph


class FakeLLMService:
    def invoke_structured(self, system_prompt, user_payload, schema, agent_name="unknown"):
        if agent_name == "analyst":
            return schema(
                explanation="这道题是完全背包问题。输入是第一行N和V，接下来N行每行vi和wi。输出是最大价值。约束条件是N,V<=1000。从题型上看，这是完全背包动态规划。关键观察是每种物品有无限件可用。",
                problem_type="完全背包动态规划",
                key_points=["每种物品无限件", "需要正序枚举容量"],
                has_input=True,
                has_constraints=True,
                need_clarification=False,
                clarification_question="",
            )
        if agent_name == "planner":
            return schema(
                explanation="我会用一维完全背包DP来做。核心想法是dp[j]表示容量不超过j的最大价值。之所以选这个方法，是因为物品无限件，容量需要正序枚举。主要步骤是：初始化dp为0，枚举物品，正序枚举容量并转移。时间复杂度O(NV)，空间复杂度O(V)。",
                strategy_name="一维完全背包 DP",
                time_complexity="O(NV)",
                space_complexity="O(V)",
                key_steps=["初始化 dp 为 0", "枚举物品", "正序枚举容量并转移"],
            )
        if agent_name == "pseudocode":
            return schema(
                explanation="状态定义是dp[j]表示容量j内的最大价值。初始化时dp全部为0。转移方程是dp[j]=max(dp[j],dp[j-vi]+wi)。遍历顺序是外层物品，内层容量从vi到V正序。",
                pseudocode="for item in items: for j from v to V: update dp[j]",
                key_points=["容量正序枚举"],
            )
        if agent_name == "coder":
            return schema(
                language="C++",
                cpp_code="#include <bits/stdc++.h>\nusing namespace std;\nint main(){int N,V;cin>>N>>V;vector<int> dp(V+1);for(int i=0,v,w;i<N;i++){cin>>v>>w;for(int j=v;j<=V;j++)dp[j]=max(dp[j],dp[j-v]+w);}cout<<dp[V]<<'\\n';return 0;}",
                compile_ready=True,
            )
        if agent_name == "verifier":
            return schema(passed=True, issues=[], rollback_target="", improvement_suggestions=[])
        raise AssertionError(f"unexpected agent: {agent_name}")


def test_direct_code_problem_runs_full_pipeline_and_outputs_code_only(monkeypatch) -> None:
    fake_llm = FakeLLMService()
    monkeypatch.setattr(analyst, "get_llm_service", lambda: fake_llm)
    monkeypatch.setattr(planner, "get_llm_service", lambda: fake_llm)
    monkeypatch.setattr(pseudocode, "get_llm_service", lambda: fake_llm)
    monkeypatch.setattr(coder, "get_llm_service", lambda: fake_llm)
    monkeypatch.setattr(verifier, "get_llm_service", lambda: fake_llm)
    monkeypatch.setattr(
        code_runner,
        "_post_to_wandbox",
        lambda payload: {
            "status": "0",
            "signal": "",
            "compiler_output": "",
            "compiler_error": "",
            "compiler_message": "",
            "program_output": "",
            "program_error": "",
            "program_message": "",
        },
    )

    graph = build_graph()
    user_text = """直接给我C++代码
题目描述
有 N 种物品和一个容量为 V 的背包，每种物品都有无限件可用。
输入格式
第一行输入两个整数 N 和 V。
输出格式
输出一个整数，表示最大价值。"""
    result = graph.invoke(
        {
            "messages": [HumanMessage(content=user_text)],
            "orchestrator_route": "analyst",
            "retry_count": 0,
            "max_retry": 1,
            "mode": "teaching",
            "teaching_stage": "analysis",
            "awaiting_user_feedback": False,
            "response_mode": "analysis_only",
            "response_text": "",
        },
        config={"configurable": {"thread_id": "direct-code-regression"}},
    )

    assert result["response_mode"] == "code_only"
    assert result["analysis"] is not None
    assert result["strategy"] is not None
    assert result["pseudocode"] is not None
    assert result["code_result"]["cpp_code"]
    assert result["agent_trace"] == ["orchestrator", "analyst", "planner", "pseudocode", "coder", "code_runner", "verifier", "formatter"]
    assert result["response_text"].startswith("analyst->planner->pseudocode->coder->code_runner->verifier->formatter\n\n```cpp")
    # 新的格式不再包含这些模板化的文本
    assert "```cpp" in result["response_text"]
