# 路由调度修复总结

## 问题根源

用户输入八皇后问题时，系统直接给出了代码，而不是先给出题意分析。经过调查发现有两个根本问题：

### 1. 意图识别误判
题目描述中的"请你编写程序"被误判为 `CODE_REQUEST`（代码请求），而不是 `NEW_PROBLEM`（新问题）。

**原因：** 意图识别的优先级顺序有问题，先检查代码请求，后检查新问题。

### 2. 条件路由缺失
即使意图识别正确，`analyst` 和 `planner` 节点后也没有根据 `response_mode` 进行条件路由。

## 修复方案

### 修复 1：调整意图识别优先级

**文件：** `app/agents/orchestrator.py`

**策略：**
1. 优先检查是否是完整的题目描述（通过结构特征：输入/输出格式、约束条件等）
2. 如果是题目描述，再判断是否有**强烈的直接代码请求信号**：
   - "直接给"、"直接写"、"只要代码"等明确词汇
   - 或明确指定编程语言（Python、Java、C++等）
3. 题目中常见的"请编写程序"等表述不会被误判为代码请求

### 修复 2：添加条件路由

**文件：** `app/graph.py`

**策略：**
- `analyst` 节点后：
  - `response_mode="analysis_only"` → `formatter`（停顿）
  - 其他 → `planner`（继续）
- `planner` 节点后：
  - `response_mode="strategy_only"` → `formatter`（停顿）
  - 其他 → `pseudocode`（继续）

### 修复 3：状态管理

**文件：** `app/agents/analyst.py`, `app/agents/planner.py`, `app/agents/orchestrator.py`

确保各节点正确设置和传递 `response_mode` 和 `awaiting_user_feedback` 状态。

## 验证结果

### 测试通过
```bash
pytest tests/ -v
# 37 passed in 1.77s ✓
```

### 实际案例验证

**输入：** 八皇后问题（包含"请你编写程序"）

**修复前：**
- 意图：`CODE_REQUEST` ❌
- 路由：完整代码生成流程
- 输出：直接给出代码

**修复后：**
- 意图：`NEW_PROBLEM` ✓
- 路由：`analyst -> formatter -> END`
- 输出：只给出题意分析，等待用户反馈

## 现在的完整路由行为

1. **普通算法问题** → `analyst -> formatter -> END`（停顿）
2. **用户说"继续"（analysis阶段）** → `planner -> formatter -> END`（停顿）
3. **用户说"继续"（strategy阶段）** → `pseudocode -> coder -> ... -> END`
4. **直接要代码**（如"直接给我Python代码"）→ 完整流程不停顿
5. **完整题解**（如"一次性讲完"）→ 完整流程不停顿
6. **普通聊天** → `chat -> END`
7. **追问** → `followup -> END`

## 关键改进点

✅ 题目描述中的"编写程序"不再被误判为代码请求
✅ 分阶段教学正常工作，每个阶段后正确停顿
✅ 支持用户按需深入或直接获取完整解答
✅ 所有测试通过，没有破坏现有功能
