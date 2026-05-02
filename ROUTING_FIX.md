# 路由调度修复说明

## 问题描述

之前的路由逻辑存在问题：当用户输入普通算法问题时，系统没有正确地先进入 `analyst` 然后给出 `analysis` 并停止，而是错误地经过了完整的代码生成流程：`analyst -> planner -> pseudocode -> coder -> code_runner -> verifier -> formatter`，最终给出了代码而不是分析。

**根本原因有两个：**

1. **意图识别优先级问题**：题目描述中包含"请你编写程序"等词时，被误判为 `CODE_REQUEST`（代码请求），而不是 `NEW_PROBLEM`（新问题）
2. **条件路由逻辑问题**：`analyst` 和 `planner` 节点后没有根据 `response_mode` 正确路由

## 期望的路由行为

### 1. 普通算法问题（无关话题）
```
输入: 与算法无关的话题
路由: orchestrator -> chat -> END
```

### 2. 追问已存在的算法解答
```
输入: 对当前算法问题的追问
路由: orchestrator -> followup -> END
```

### 3. 正常输入算法问题
```
输入: 新的算法问题
路由: orchestrator -> analyst -> formatter -> END
状态: awaiting_user_feedback=True, response_mode="analysis_only"
```

### 4. 用户选择继续（从 analysis 阶段）
```
输入: "继续"、"下一步"等
路由: orchestrator -> planner -> formatter -> END
状态: awaiting_user_feedback=True, response_mode="strategy_only"
```

### 5. 用户选择继续（从 strategy 阶段）
```
输入: "继续"、"下一步"等
路由: orchestrator -> pseudocode -> coder -> code_runner -> verifier -> formatter -> END
状态: awaiting_user_feedback=False, response_mode="implementation_only"
```

### 6. 用户直接要求代码
```
输入: "直接给我代码"、"给我Python实现"等
路由: orchestrator -> analyst -> planner -> pseudocode -> coder -> code_runner -> verifier -> formatter -> END
状态: awaiting_user_feedback=False, response_mode="code_only"
关键: 不在 analyst 和 planner 后停顿
```

### 7. 用户要求完整题解
```
输入: "完整题解"、"一次性讲完"等
路由: orchestrator -> analyst -> planner -> pseudocode -> coder -> code_runner -> verifier -> formatter -> END
状态: awaiting_user_feedback=False, response_mode="full_solution"
关键: 不在 analyst 和 planner 后停顿
```

## 修复内容

### 1. `app/agents/orchestrator.py` - 修复意图识别优先级

**问题：** 题目描述中的"请你编写程序"被误判为代码请求

**修复：** 调整意图识别优先级，优先检查是否是新问题（完整题目描述），然后再检查是否是代码请求

```python
def classify_user_intent(state: GraphState) -> IntentResult:
    # ... 前面的检查 ...
    
    # 优先检查是否是新问题（完整题目描述）
    looks_like_problem = _looks_like_new_problem(stripped)
    has_full_solution_req = _has_explicit_full_solution_request(normalized)
    has_code_req = _has_explicit_code_request(normalized)

    # 如果看起来像新问题，且有明确的完整题解请求
    if looks_like_problem and has_full_solution_req:
        return IntentResult(UserIntent.FULL_SOLUTION, 0.9, "explicit full solution request")

    # 如果看起来像新问题，且有明确的代码请求
    if looks_like_problem and has_code_req:
        # 检查是否有强烈的直接代码请求信号
        strong_code_request = any(marker in normalized for marker in ("直接给", "直接写", "只要代码", "只给代码"))
        language_specified = any(lang in normalized for lang in ("python", "java", "c++", "cpp", "go", "rust", "javascript", "typescript"))
        
        if strong_code_request or language_specified:
            return IntentResult(UserIntent.CODE_REQUEST, 0.9, "explicit code or language request")
        else:
            # 题目描述中的"编写程序"不算代码请求
            return IntentResult(UserIntent.NEW_PROBLEM, 0.85, "problem-like structure")

    # 如果看起来像新问题，优先识别为新问题
    if looks_like_problem:
        return IntentResult(UserIntent.NEW_PROBLEM, 0.85, "problem-like structure")
    
    # ... 后续检查 ...
```

**关键改进：**
- 先判断是否是新问题（通过题目结构特征）
- 如果是新问题且包含代码相关词汇，进一步判断是否有**强烈的直接代码请求信号**：
  - "直接给"、"直接写"、"只要代码"等
  - 或明确指定编程语言（Python、Java等）
- 题目描述中常见的"请编写程序"不会被误判为代码请求

### 2. `app/graph.py` - 修复条件路由逻辑
修改了 `analyst` 和 `planner` 节点后的条件路由：

```python
# analyst 节点后的路由
workflow.add_conditional_edges(
    "analyst",
    lambda state: "formatter" if state.get("response_mode") == "analysis_only" else "planner",
    {
        "planner": "planner",
        "formatter": "formatter",
    },
)

# planner 节点后的路由
workflow.add_conditional_edges(
    "planner",
    lambda state: "formatter" if state.get("response_mode") == "strategy_only" else "pseudocode",
    {
        "pseudocode": "pseudocode",
        "formatter": "formatter",
    },
)
```

**关键逻辑：**
- `response_mode="analysis_only"` → `analyst` 后去 `formatter`（停顿）
- `response_mode="code_only"` 或 `"full_solution"` → `analyst` 后去 `planner`（继续）
- `response_mode="strategy_only"` → `planner` 后去 `formatter`（停顿）
- `response_mode="code_only"` 或 `"full_solution"` → `planner` 后去 `pseudocode`（继续）

### 3. `app/agents/orchestrator.py` - 确保正确设置状态
确保 `CODE_REQUEST` 和 `FULL_SOLUTION` 意图正确设置状态：

```python
if intent == UserIntent.CODE_REQUEST:
    return {
        "orchestrator_route": "analyst",  # 从 analyst 开始
        "response_mode": "code_only",     # 设置为 code_only
        "awaiting_user_feedback": False,  # 不等待用户反馈
        # ... 重置其他状态
    }

if intent == UserIntent.FULL_SOLUTION:
    return {
        "orchestrator_route": "analyst",     # 从 analyst 开始
        "response_mode": "full_solution",    # 设置为 full_solution
        "awaiting_user_feedback": False,     # 不等待用户反馈
        # ... 重置其他状态
    }
```

### 4. `app/agents/analyst.py`
根据 `response_mode` 设置 `awaiting_user_feedback`：

```python
def run_analyst(state: GraphState) -> dict:
    response_mode = state.get("response_mode", "analysis_only")
    # ... 执行分析
    return {
        # ...
        "awaiting_user_feedback": response_mode == "analysis_only",
        "response_mode": response_mode,
    }
```

### 5. `app/agents/planner.py`
根据 `response_mode` 设置 `awaiting_user_feedback`：

```python
def run_planner(state: GraphState) -> dict:
    response_mode = state.get("response_mode", "strategy_only")
    # ... 执行规划
    return {
        # ...
        "awaiting_user_feedback": response_mode == "strategy_only",
        "response_mode": response_mode,
    }
```

## 核心设计思想

通过 `response_mode` 状态字段控制工作流的停顿点：

- **`analysis_only`**: 只返回分析，在 `analyst` 后停顿
- **`strategy_only`**: 只返回策略，在 `planner` 后停顿
- **`implementation_only`**: 返回实现，不在中间停顿
- **`code_only`**: 返回代码，走完整流程但不在中间停顿
- **`full_solution`**: 返回完整题解，走完整流程但不在中间停顿

通过**意图识别优先级**避免误判：

1. 先检查是否是完整的题目描述（通过结构特征）
2. 如果是题目描述，再判断是否有**强烈的直接代码请求信号**
3. 题目中常见的"请编写程序"等表述不会被误判为代码请求

这样设计的好处：
1. 保持了教学的分阶段特性
2. 支持用户按需深入
3. 也支持直接获取完整解答
4. 路由逻辑清晰，易于维护
5. 避免了题目描述被误判的问题

## 测试验证

所有测试通过：
```bash
pytest tests/ -v
# 37 passed in 1.77s
```

关键测试：
- `test_orchestrator_intent.py`: 验证意图识别和路由正确性
- `test_router.py`: 验证条件路由逻辑
- `test_direct_code_pipeline.py`: 验证直接代码请求的完整流程
- `test_verifier_feedback.py`: 验证代码验证和回退逻辑

## 实际案例验证

### 案例：八皇后问题

**输入：**
```
题目描述

在 8×8 的国际象棋棋盘上放置 8 个皇后，使得任意两个皇后都不能互相攻击。
也就是说，任意两个皇后不能处于同一行、同一列或同一条对角线上。

请你编写程序，求出所有满足条件的摆放方案总数。

输入格式：无输入。
输出格式：输出一个整数，表示八皇后问题的所有不同摆放方案数量。
输出样例：92
```

**修复前：**
- 意图识别：`CODE_REQUEST`（错误）
- 路由：`analyst -> planner -> pseudocode -> coder -> code_runner -> verifier -> formatter`
- 结果：直接给出代码

**修复后：**
- 意图识别：`NEW_PROBLEM`（正确）
- 路由：`analyst -> formatter -> END`
- 结果：只给出题意分析，等待用户反馈

## 使用示例

### 示例 1: 分阶段学习
```
用户: 给定n个物品，背包容量W，求最大价值
系统: [返回题意分析] (停顿)

用户: 继续
系统: [返回算法策略] (停顿)

用户: 继续
系统: [返回伪代码和代码实现]
```

### 示例 2: 直接要代码
```
用户: 给定n个物品，背包容量W，直接给我Python代码
系统: [返回完整的分析、策略、伪代码和Python代码实现] (不停顿)
```

### 示例 3: 追问
```
用户: 为什么用动态规划？
系统: [针对当前阶段给出解释]
```
