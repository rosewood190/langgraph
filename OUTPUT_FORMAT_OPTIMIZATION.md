# 输出格式优化 - 方案 C 实施文档

## 背景

原有的输出格式过于僵化，存在以下问题：
1. 强制要求 `input_format` 和 `output_format`，但有些题目（如八皇后）没有输入
2. formatter 中的拼接方式生硬，像是在填模板
3. 信息冗余或缺失，不够灵活自然

## 方案选择

采用**方案 C：混合模式**
- 结构化数据 + 自然语言总结，两者结合
- 既有结构化数据支持后续处理（追问、重讲）
- 又有自然流畅的输出，像真正的老师在讲解

## 实施内容

### 1. 数据模型重构 (`app/state.py`)

#### ProblemAnalysis（题意分析）
```python
class ProblemAnalysis(BaseModel):
    # 主要输出：自然语言讲解
    explanation: str  # 完整的分析讲解（自然语言）
    
    # 辅助字段：用于后续处理
    problem_type: str  # 题型
    key_points: list[str]  # 3-5个关键观察点
    has_input: bool  # 是否有输入
    has_constraints: bool  # 是否有约束
    need_clarification: bool
    clarification_question: str
```

**改进点：**
- 用 `explanation` 替代 `summary`, `input_format`, `output_format` 等僵化字段
- LLM 可以根据题目特点自由组织语言
- 保留 `problem_type` 和 `key_points` 用于后续处理

#### StrategyPlan（策略规划）
```python
class StrategyPlan(BaseModel):
    # 主要输出：自然语言讲解
    explanation: str  # 完整的策略讲解
    
    # 辅助字段
    strategy_name: str
    time_complexity: str
    space_complexity: str
    key_steps: list[str]  # 主要步骤
```

**改进点：**
- 用 `explanation` 替代 `core_idea`, `selected_reason`, `steps`, `edge_cases` 等
- 保留复杂度信息用于显示
- 用 `key_steps` 替代 `steps`，更简洁

#### PseudocodeResult（伪代码）
```python
class PseudocodeResult(BaseModel):
    # 主要输出：自然语言讲解
    explanation: str  # 讲解伪代码的组织方式
    
    # 辅助字段
    pseudocode: str  # 伪代码文本
    key_points: list[str]  # 实现注意点
```

**改进点：**
- 用 `explanation` 替代 `state_definition`, `initialization`, `transition`, `traversal_order`
- 更自然流畅

### 2. Prompt 优化

#### Analyst Prompt
```python
ANALYST_PROMPT = """
你是算法题题意分析智能体，像一位经验丰富的算法老师。

任务：
- 用自然、口语化的方式讲解题意，就像在面对面教学
- 说清楚题目在问什么、输入输出是什么样的（如果有）、有哪些约束条件
- 指出这道题的类型
- 分享你观察到的关键点
- 语言要流畅自然，不要生硬地列举字段，要像在对话

注意：
- 有些题目可能没有输入（如八皇后问题），这很正常，说明即可
- 有些题目约束条件不明确，也可以指出

输出必须是 JSON，对应字段：
{
  "explanation": str,  // 完整的自然语言讲解，2-4段，流畅连贯
  "problem_type": str,
  "key_points": [str],
  "has_input": bool,
  "has_constraints": bool,
  "need_clarification": bool,
  "clarification_question": str
}

示例 explanation 风格：
"我们先不急着写代码，先把题目本身拆开来看。这道题要求我们在8×8的棋盘上放置8个皇后，
任意两个皇后不能互相攻击。注意这道题没有输入，输出是一个整数，表示所有可能的摆放方案数。

从题型上看，这是一个经典的回溯问题。我们需要逐行放置皇后，每次放置时检查是否与之前的皇后冲突。

这里比较关键的观察有：每行只能放一个皇后；列、主对角线、副对角线都需要检查冲突；
可以用集合来快速判断某个位置是否可用。"
"""
```

**改进点：**
- 强调"自然、口语化"
- 给出具体的示例风格
- 明确说明特殊情况（如无输入）的处理方式

#### Planner 和 Pseudocode Prompt
类似的优化思路，都强调自然语言和对话风格。

### 3. Formatter 简化 (`app/agents/formatter.py`)

**核心改进：**
- `analysis_only` 模式：直接输出 `analysis.explanation` + 引导语
- `strategy_only` 模式：直接输出 `strategy.explanation` + 引导语
- `implementation_only` 模式：输出 `pseudocode.explanation` + 伪代码块 + 代码

**代码示例：**
```python
if response_mode == "analysis_only":
    explanation = analysis.get("explanation", "")
    closing = "\n\n如果这一步你已经清楚了，我可以继续讲我会怎么选策略..."
    response_text = explanation + closing
```

**改进点：**
- 不再拼接模板化的文本
- LLM 生成的内容直接使用
- formatter 只负责添加引导语和组织结构

### 4. 测试更新

更新了 `tests/test_direct_code_pipeline.py` 中的 FakeLLMService，使用新的字段结构。

## 效果对比

### 旧格式（模板化）
```
我们先不急着写代码，先把题目本身拆开来看。完全背包最大价值。

输入是 第一行 N 和 V，接下来 N 行 vi 和 wi。，输出是 最大价值。。

从题型上看，它更接近 完全背包动态规划。

这里比较关键的观察有：每种物品无限件。
```

**问题：**
- 生硬的拼接
- 重复的标点
- 不自然的语序

### 新格式（自然语言）
```
我们先不急着写代码，先把题目本身拆开来看。这道题是完全背包问题，
要求我们在给定N种物品和容量为V的背包的情况下，求出最大价值。

输入格式是第一行两个整数N和V，接下来N行每行两个整数vi和wi，
分别表示第i种物品的体积和价值。输出是一个整数，表示最大价值。
约束条件是N和V都不超过1000。

从题型上看，这是完全背包动态规划问题。关键观察是每种物品有无限件可用，
这意味着我们在枚举容量时需要正序遍历，而不是01背包的逆序。
```

**优点：**
- 流畅自然
- 像真正的老师在讲解
- 灵活适应不同题目

## 测试结果

```bash
pytest tests/ -v
# 37 passed in 1.42s ✓
```

所有测试通过，包括：
- 路由测试
- 意图识别测试
- 直接代码管道测试
- LLM 服务测试
- 验证器测试

## 优势总结

1. **灵活性**：适应各种题目特点，不再受固定字段限制
2. **自然性**：输出像真正的老师在讲解，不是填模板
3. **可维护性**：prompt 更简洁，formatter 逻辑更清晰
4. **可扩展性**：保留了结构化字段用于后续功能（追问、重讲）
5. **向后兼容**：所有测试通过，没有破坏现有功能

## 后续建议

1. **追问功能增强**：利用 `key_points` 和 `key_steps` 实现更精准的追问定位
2. **重讲功能优化**：可以针对特定的 key_point 进行重点讲解
3. **多模式支持**：teaching/contest/interview 模式可以调整 explanation 的详细程度
4. **用户反馈收集**：观察实际使用中的效果，持续优化 prompt

## 文件清单

修改的文件：
- `app/state.py` - 数据模型
- `app/prompts/analyst.py` - Analyst prompt
- `app/prompts/planner.py` - Planner prompt
- `app/prompts/pseudocode.py` - Pseudocode prompt
- `app/agents/formatter.py` - Formatter 逻辑
- `tests/test_direct_code_pipeline.py` - 测试更新

未修改但相关的文件：
- `app/agents/analyst.py` - 使用新的数据模型
- `app/agents/planner.py` - 使用新的数据模型
- `app/agents/pseudocode.py` - 使用新的数据模型
