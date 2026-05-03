from __future__ import annotations

from langchain_core.messages import AIMessage

from app.agents.trace import append_agent_trace, prepend_agent_trace
from app.state import GraphState


LANGUAGE_FENCE_MAP = {
    "C++": "cpp",
    "Python": "python",
    "Java": "java",
    "Go": "go",
    "JavaScript": "javascript",
    "TypeScript": "typescript",
    "Rust": "rust",
}


def _join_non_empty(parts: list[str]) -> str:
    return "\n\n".join(part for part in parts if part.strip())


def run_formatter(state: GraphState) -> dict:
    state = {**state, "agent_trace": append_agent_trace(state, "formatter")}
    analysis = state.get("analysis") or {}
    strategy = state.get("strategy") or {}
    pseudocode = state.get("pseudocode") or {}
    code_result = state.get("code_result") or {}
    code_execution = state.get("code_execution") or {}
    verification = state.get("verification") or {}
    response_mode = state.get("response_mode", "analysis_only")
    mode = state.get("mode", "teaching")

    language = code_result.get("language", "C++")
    code_text = code_result.get("cpp_code", "")
    fence = LANGUAGE_FENCE_MAP.get(language, "text")

    # code_only 模式：只输出代码和检查结果
    if response_mode == "code_only":
        execution_lines: list[str] = []
        if code_execution:
            if code_execution.get("compile_passed") and code_execution.get("run_passed"):
                if mode == "contest":
                    execution_lines.append("✓ 代码格式符合 LeetCode 标准")
                else:
                    execution_lines.append("在线检查：代码已通过编译或语法检查，并完成了一次空输入运行。")
            else:
                if mode == "contest":
                    execution_lines.append("✗ " + code_execution.get("message", "编译或运行检查未通过"))
                else:
                    execution_lines.append("在线检查：" + code_execution.get("message", "未通过编译运行检查。"))
                if code_execution.get("stderr"):
                    execution_lines.append("错误信息：" + code_execution.get("stderr", ""))
        execution_text = "\n\n" + "\n\n".join(execution_lines) if execution_lines else ""
        
        # 竞赛模式添加提交说明
        if mode == "contest":
            submission_note = "\n\n提交说明：以上代码为 LeetCode/力扣标准格式，可直接提交。"
            execution_text += submission_note
        
        response_text = (
            f"```{fence}\n{code_text}\n```"
            f"{execution_text}"
        )
        response_text = prepend_agent_trace(response_text, state)
        return {
            "agent_trace": state["agent_trace"],
            "response_text": response_text,
            "messages": [AIMessage(content=response_text)],
            "awaiting_user_feedback": True,
            "teaching_stage": "implementation",
            "last_teaching_node": "implementation",
        }

    # analysis_only 模式：只输出题意分析（使用自然语言 explanation）
    if response_mode == "analysis_only":
        explanation = analysis.get("explanation", "")
        
        # 根据模式调整引导语
        if mode == "contest":
            closing = "\n\n确认题意理解无误后，可继续进行算法设计。"
        else:
            closing = "\n\n如果这一步你已经清楚了，我可以继续讲我会怎么选策略；如果你觉得哪里还不够明白，也可以直接告诉我，我换种方式再讲一遍。"
        
        # 如果需要澄清
        if analysis.get("need_clarification") and analysis.get("clarification_question"):
            if mode == "contest":
                closing = "\n\n需要确认：" + analysis.get("clarification_question", "")
            else:
                closing = "\n\n不过在继续之前，我还想先确认一下：" + analysis.get("clarification_question", "")
        
        response_text = explanation + closing
        response_text = prepend_agent_trace(response_text, state)
        return {
            "agent_trace": state["agent_trace"],
            "response_text": response_text,
            "messages": [AIMessage(content=response_text)],
        }

    # strategy_only 模式：只输出策略规划（使用自然语言 explanation）
    if response_mode == "strategy_only":
        explanation = strategy.get("explanation", "")
        
        # 根据模式调整引导语
        if mode == "contest":
            closing = "\n\n算法设计完成，可继续查看代码实现。"
        else:
            closing = "\n\n如果这个思路你已经接受了，我下一步可以继续把实现过程展开，包括伪代码和代码；如果你想让我比较一下别的做法，也可以直接问我。"
        
        response_text = explanation + closing
        response_text = prepend_agent_trace(response_text, state)
        return {
            "agent_trace": state["agent_trace"],
            "response_text": response_text,
            "messages": [AIMessage(content=response_text)],
        }

    # implementation_only / full_solution 模式：输出完整实现
    parts: list[str] = []
    
    # 如果有伪代码讲解（使用自然语言 explanation）
    if pseudocode and pseudocode.get("explanation"):
        if mode == "contest":
            # 竞赛模式：更简洁专业的表述
            parts.append("算法实现思路：" + pseudocode.get("explanation", ""))
        else:
            parts.append(pseudocode.get("explanation", ""))
        
        # 伪代码块
        pseudocode_block = pseudocode.get("pseudocode", "")
        if pseudocode_block.strip():
            if mode == "contest":
                parts.append("核心逻辑伪代码：\n" + pseudocode_block)
            else:
                parts.append("伪代码大概可以写成这样：\n" + pseudocode_block)
        
        # 关键点
        key_points = pseudocode.get("key_points", [])
        if key_points:
            if mode == "contest":
                parts.append("实现要点：" + "；".join(key_points) + "。")
            else:
                parts.append("实现时有几点特别需要注意：" + "；".join(key_points) + "。")

    # 代码
    if code_text.strip():
        if mode == "contest":
            parts.append(f"{language} 标准实现：\n```{fence}\n{code_text}\n```")
        else:
            parts.append(f"对应的 {language} 代码如下：\n```{fence}\n{code_text}\n```")

    # 复杂度
    time_complexity = strategy.get("time_complexity", "")
    space_complexity = strategy.get("space_complexity", "")
    if time_complexity or space_complexity:
        complexity_lines = []
        if time_complexity:
            complexity_lines.append(f"时间复杂度：{time_complexity}")
        if space_complexity:
            complexity_lines.append(f"空间复杂度：{space_complexity}")
        if mode == "contest":
            parts.append("复杂度分析：" + "，".join(complexity_lines) + "。")
        else:
            parts.append("复杂度方面，" + "，".join([line.replace("：", "是 ") for line in complexity_lines]) + "。")

    # 在线检查结果
    if code_execution:
        if code_execution.get("compile_passed") and code_execution.get("run_passed"):
            if mode == "contest":
                parts.append("✓ 代码格式符合 LeetCode 标准。")
            else:
                parts.append("在线检查方面，代码已经通过编译或语法检查，并完成了一次空输入运行。")
        else:
            execution_message = code_execution.get("message", "在线编译运行检查未通过。")
            stderr = code_execution.get("stderr", "")
            detail = f"错误信息：{stderr}" if stderr else ""
            if mode == "contest":
                parts.append(_join_non_empty([f"✗ {execution_message}", detail]))
            else:
                parts.append(_join_non_empty([f"在线检查方面，{execution_message}", detail]))

    # 验证结果
    if verification:
        if verification.get("passed", False):
            if mode == "contest":
                parts.append("✓ 代码实现已通过验证。")
            else:
                parts.append("我也顺手帮你检查过一遍了，目前这版实现是通过的。")
        else:
            issues = verification.get("issues", [])
            rollback_target = verification.get("rollback_target", "") or "未指定"
            if mode == "contest":
                parts.append(
                    "✗ 发现以下问题："
                    + ("；".join(issues) if issues else "当前实现未完全通过验证，建议人工复核。")
                    + f"。需要回退到 {rollback_target} 阶段进行修正。"
                )
            else:
                parts.append(
                    "不过我检查后发现这版实现还有一些问题："
                    + ("；".join(issues) if issues else "当前结果未完全通过审核，请人工复核。")
                    + f"。如果继续修，我会优先回到 {rollback_target} 这个阶段处理。"
                )

    # 结束语
    if mode == "contest":
        parts.append("以上代码为 LeetCode/力扣标准格式，可直接提交。如需其他语言实现或进一步优化，请告知。")
    else:
        parts.append("如果你愿意，我接下来可以继续陪你逐行解释代码，或者帮你把它改成 Python、Java 之类的其他语言版本。")
    
    response_text = _join_non_empty(parts)
    response_text = prepend_agent_trace(response_text, state)

    return {
        "agent_trace": state["agent_trace"],
        "response_text": response_text,
        "messages": [AIMessage(content=response_text)],
    }
