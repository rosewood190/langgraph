from __future__ import annotations

from app.state import FinalAnswer, GraphState


def run_formatter(state: GraphState) -> dict:
    analysis = state.analysis
    strategy = state.strategy
    pseudocode = state.pseudocode
    code_result = state.code_result
    verification = state.verification

    analysis_text = ""
    if analysis:
        analysis_text = "\n".join(
            [
                f"题目摘要：{analysis.summary}",
                f"输入：{analysis.input_format}",
                f"输出：{analysis.output_format}",
                f"题型：{analysis.problem_type}",
                "关键观察：" + ("；".join(analysis.key_observations) if analysis.key_observations else "无"),
            ]
        )

    strategy_text = ""
    complexity_text = ""
    if strategy:
        strategy_text = "\n".join(
            [
                f"方案：{strategy.strategy_name}",
                f"核心思想：{strategy.core_idea}",
                f"选择原因：{strategy.selected_reason}",
                "主要步骤：" + ("；".join(strategy.steps) if strategy.steps else "无"),
                "边界情况：" + ("；".join(strategy.edge_cases) if strategy.edge_cases else "无"),
            ]
        )
        complexity_text = (
            f"时间复杂度：{strategy.time_complexity}\n"
            f"空间复杂度：{strategy.space_complexity}"
        )

    pseudocode_text = ""
    if pseudocode:
        pseudocode_text = "\n".join(
            [
                f"状态定义：{pseudocode.state_definition}",
                f"初始化：{pseudocode.initialization}",
                f"状态转移：{pseudocode.transition}",
                f"遍历顺序：{pseudocode.traversal_order}",
                "伪代码：",
                pseudocode.pseudocode,
                "关键注意点：" + ("；".join(pseudocode.key_points) if pseudocode.key_points else "无"),
            ]
        )

    verifier_summary_text = ""
    verifier_note = ""
    if verification:
        if verification.passed:
            verifier_summary_text = "审核结果：通过"
        else:
            issues_text = "；".join(verification.issues) if verification.issues else "当前结果未完全通过审核，请人工复核。"
            rollback_text = verification.rollback_target or "无"
            verifier_summary_text = f"审核结果：未完全通过；建议回退节点：{rollback_text}；发现问题：{issues_text}"
            verifier_note = "\n七、审核提示\n" + "\n".join(verification.issues or ["当前结果未完全通过审核，请人工复核。"])

    cpp_code_text = code_result.cpp_code if code_result else ""

    full_response = (
        f"一、问题分析\n{analysis_text}\n\n"
        f"二、算法策略\n{strategy_text}\n\n"
        f"三、伪代码\n{pseudocode_text}\n\n"
        f"四、C++ 实现\n```cpp\n{cpp_code_text}\n```\n\n"
        f"五、复杂度分析\n{complexity_text}\n\n"
        f"六、审核摘要\n{verifier_summary_text or '无'}"
        f"{verifier_note}"
    )

    final_answer = FinalAnswer(
        analysis_text=analysis_text,
        strategy_text=strategy_text,
        pseudocode_text=pseudocode_text,
        cpp_code_text=cpp_code_text,
        complexity_text=complexity_text,
        verifier_summary_text=verifier_summary_text,
        full_response=full_response,
    )

    return {
        "final_answer": final_answer,
        "last_algorithm_question": state.raw_question,
        "last_analysis_text": analysis_text,
        "last_strategy_text": strategy_text,
        "last_pseudocode_text": pseudocode_text,
        "last_cpp_code_text": cpp_code_text,
        "last_complexity_text": complexity_text,
        "current_step": "done",
    }
