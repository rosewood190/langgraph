# Algo Agent MVP

一个基于 LangGraph 的多智能体算法题求解与聊天 CLI MVP。它会像算法老师一样分阶段处理题目：先拆题，再讲策略，最后展开伪代码和代码实现；同时也支持普通聊天、追问解释、请求直接看代码或切换代码语言。

## 功能

- 基于 LangGraph 的多节点工作流编排
- orchestrator 统一识别新题、继续、停止、重讲、追问、要代码、完整题解和普通聊天等用户意图并分发到对应节点
- 算法题意分析：题意摘要、输入输出、约束、题型和关键观察
- 算法策略规划：核心思路、选择理由、步骤、复杂度和边界情况
- 伪代码生成
- 多语言代码生成：默认 C++，也可根据用户请求生成 Python、Java、Go、JavaScript、TypeScript、Rust 等
- **两种输出模式**：
  - **教学模式（teaching）**：默认模式，口语化表述，生成标准输入输出的完整可执行代码，适合学习理解
  - **竞赛模式（contest）**：专业严谨表述，生成 LeetCode/力扣标准类方法格式代码，适合竞赛刷题
- code_runner 调用免费的 Wandbox 在线 API 对生成代码进行编译或语法检查，并尝试空输入运行
- 竞赛模式下，由于 LeetCode 格式代码无法直接运行，跳过在线验证
- verifier 结合在线编译运行检查结果审核代码与策略，并按需回退到 `planner` 或 `coder`，最多重试 `MAX_RETRY` 次
- 当在线检查发现编译、语法、运行或超时错误时，verifier 会确定性回退到 coder，并把错误输出作为修复反馈
- formatter 将结构化结果整理成面向不同模式的自然语言回复
- followup 节点结合当前教学阶段回答追问或重讲
- 普通聊天与问候应答
- 交互式 CLI 支持多轮对话和长文本输入
- CLI 思考中进度提示
- 可选 LangSmith tracing
- 支持导出 LangGraph 架构图 PNG 或 Mermaid 源码

## 目录

- `app/main.py`：CLI 入口，支持交互模式、单次提问模式和 `--mode` 参数
- `app/graph.py`：LangGraph 工作流构建与内存 checkpointer 配置
- `app/router.py`：orchestrator 与 verifier 后的条件路由逻辑
- `app/state.py`：共享 `GraphState`、结构化输出模型和状态类型定义
- `app/config.py`：环境变量配置读取
- `app/agents/`：各工作流节点实现
  - `orchestrator.py`：基于规则和打分识别新题、继续、停止、重讲、追问、直接要代码、完整题解和普通聊天
  - `analyst.py`：题意分析，根据模式调整表述风格
  - `planner.py`：算法策略规划，根据模式调整表述风格
  - `pseudocode.py`：伪代码生成，根据模式调整表述风格
  - `coder.py`：代码生成与目标语言识别，竞赛模式生成 LeetCode 格式
  - `code_runner.py`：调用 Wandbox 在线 API 做编译、语法检查和空输入运行检查
  - `verifier.py`：结合代码执行结果审核并给出回退建议
  - `formatter.py`：最终回复组织，根据模式选择展示不同风格的输出
  - `followup.py`：阶段内追问与重讲
  - `chat_agent.py`：普通聊天
- `app/prompts/`：各 agent 的系统提示词
- `app/services/llm.py`：LLM 统一封装、结构化 JSON 解析与修复
- `app/services/langsmith.py`：LangSmith tracing 配置
- `app/services/progress.py`：CLI 进度提示
- `tests/`：路由与 LLM 结构化解析相关测试
- `export_graph_png.py`：导出当前 LangGraph 架构图
- `agent_graph.png`：已导出的架构图文件
- `pyproject.toml`：项目元数据与依赖配置

## 安装

要求 Python 3.11 或更高版本。

```bash
pip install -e .
```

如需运行测试，安装开发依赖：

```bash
pip install -e .[dev]
```

## 配置

在项目根目录创建 `.env`，至少填入：

```env
OPENAI_API_KEY=你的 API Key
```

默认使用阿里云 DashScope 的 OpenAI 兼容地址和 `qwen-plus` 模型。可选配置如下：

```env
MODEL_NAME=qwen-plus
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
MODEL_TEMPERATURE=0
MAX_RETRY=1
CODE_RUNNER_BASE_URL=https://wandbox.org/api/compile.json
CODE_RUNNER_TIMEOUT=20
```

如果使用其他 OpenAI 兼容服务，可相应修改 `OPENAI_BASE_URL` 和 `MODEL_NAME`。

代码检查默认使用免费的 Wandbox 公共在线 API，不需要本地安装 `g++`、`javac`、`node` 等编译器，也不需要 API Key。`CODE_RUNNER_BASE_URL` 可改为兼容的 Wandbox `compile.json` 地址；`CODE_RUNNER_TIMEOUT` 用于控制在线请求和执行超时时间。

如需开启 LangSmith trace，可额外配置：

```env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=你的 LangSmith Key
LANGSMITH_PROJECT=algo-agent-mvp
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
```

开启后：

- 每次 LangGraph 主流程会记录为一个 trace run
- 每个 agent 的 LLM 调用会带上对应 `run_name`、`tags` 和 `metadata`
- 可在 LangSmith 控制台按项目查看整条调用链

## 运行

### 交互模式（推荐）

```bash
python -m app.main
```

启动后会引导你选择输出模式：
```
你好，我是你的算法设计多智能体助手。
我支持两种输出模式：
  1. 教学模式 - 口语化表述，适合学习理解
  2. 竞赛模式 - 专业严谨表述，生成 LeetCode 标准格式代码

请选择你想使用的模式（输入 1 或 2，默认为教学模式）：
```

选择模式后，持续等待用户输入；输入 `exit` 结束对话。

CLI 支持长文本输入：
- `Enter`：提交当前输入
- `Esc+Enter`：插入换行
- 若终端支持，也可使用 `Shift+Enter` 插入换行

### 单次提问模式

```bash
python -m app.main "给定 n 个物品，每个物品有重量和价值，背包容量为 W，求最大总价值，每个物品最多选一次。"
```

### 指定输出模式

```bash
# 教学模式
python -m app.main --mode teaching

# 竞赛模式
python -m app.main --mode contest

# 单次提问 + 竞赛模式
python -m app.main --mode contest "两数之和问题"
```

## 输出模式详解

### 教学模式（teaching）

**特点**：
- 表述风格：口语化、亲切，像老师在面对面教学
- 代码格式：标准输入输出的完整可执行代码
- 引导语：鼓励互动，如"如果你愿意，我接下来可以继续陪你逐行解释代码"
- 在线验证：通过 Wandbox 进行编译和运行检查

**适用场景**：
- 算法学习
- 概念理解
- 逐步推导
- 需要详细解释

**示例输出**：
```
我们先不急着写代码，先把题目本身拆开来看...

好，那我们继续看策略。按照我现在的理解，我会用动态规划来做这道题...

对应的 C++ 代码如下：
```cpp
#include <iostream>
#include <vector>
using namespace std;

int main() {
    int n, W;
    cin >> n >> W;
    // ...
}
```

复杂度方面，时间复杂度是 O(nW)，空间复杂度是 O(nW)。

在线检查方面，代码已经通过编译或语法检查，并完成了一次空输入运行。
```

### 竞赛模式（contest）

**特点**：
- 表述风格：专业严谨，简洁高效
- 代码格式：LeetCode/力扣标准类方法格式
  - C++: `class Solution { public: ... };`
  - Python: `class Solution: def ...`
  - Java: `class Solution { ... }`
- 引导语：简洁专业，如"以上代码为 LeetCode/力扣标准格式，可直接提交"
- 在线验证：跳过（LeetCode 格式无法直接运行）
- 默认语言：C++（除非用户明确指定其他语言）

**适用场景**：
- LeetCode/力扣刷题
- 算法竞赛准备
- OJ 平台提交
- 快速获取标准格式代码

**示例输出**：
```
题目要求：在8×8棋盘上放置8个皇后，任意两个皇后不能互相攻击...

算法选择：回溯法。核心思路：逐行放置皇后，每次检查列和对角线冲突...

C++ 标准实现：
```cpp
class Solution {
public:
    int totalNQueens(int n) {
        unordered_set<int> cols, diag1, diag2;
        return backtrack(0, n, cols, diag1, diag2);
    }
    
private:
    int backtrack(int row, int n, unordered_set<int>& cols, 
                  unordered_set<int>& diag1, unordered_set<int>& diag2) {
        // ...
    }
};
```

复杂度分析：时间复杂度：O(N!)，空间复杂度：O(N)。

✓ 代码格式符合 LeetCode 标准。

以上代码为 LeetCode/力扣标准格式，可直接提交。
```

### 模式对比

| 特性 | 教学模式 | 竞赛模式 |
|------|----------|----------|
| 表述风格 | 口语化、亲切 | 专业严谨 |
| 代码格式 | 标准输入输出 | LeetCode 类方法 |
| 在线验证 | ✓ Wandbox | ✗ 跳过 |
| 默认语言 | C++ | C++ |
| 引导语 | 互动式 | 简洁专业 |
| 复杂度表述 | "复杂度方面，时间复杂度是..." | "复杂度分析：时间复杂度：..." |
| 适用场景 | 学习理解 | 刷题提交 |

## 分阶段算法回答

当用户输入看起来像新的算法题时，系统会先进入 `analyst` 节点，只返回题目分析。随后会等待用户反馈。

如果用户表示继续，例如：

- `继续`
- `可以`
- `好的`
- `懂了`
- `明白了`
- `下一步`
- `继续讲`
- `好，继续`
- `继续吧`

系统会从当前阶段进入下一阶段：

1. `analysis` 阶段继续后进入 `planner`，返回策略说明
2. `strategy` 阶段继续后进入 `pseudocode -> coder -> code_runner -> verifier -> formatter`，返回伪代码、代码、复杂度和审核结果

如果用户表示没懂或要求重讲，例如：

- `没懂`
- `不懂`
- `再讲一遍`
- `重讲`
- `换种方式`
- `举个例子`
- `详细一点`
- `没太懂`

系统会进入 `followup` 节点，结合当前阶段换一种方式解释。

用户也可以直接请求代码或指定语言，例如：

- `直接给代码`
- `给我 Python 实现`
- `改成 Java`
- `用 Go 写一版`

系统会进入 `coder -> code_runner -> verifier -> formatter`，并尽量按请求语言输出实现。

## 工作流

主流程从 `orchestrator` 开始：

```text
START -> orchestrator
```

orchestrator 可路由到：

```text
chat -> END
followup -> END
analyst -> formatter -> END
planner -> formatter -> END
pseudocode -> coder -> code_runner -> verifier -> formatter -> END
coder -> code_runner -> verifier -> formatter -> END
```

当代码生成完成后，`code_runner` 会调用免费的 Wandbox 在线 API，按目标语言尝试编译或语法检查，并在通过后执行一次空输入运行。检查结果会写入 `code_execution`，再交给 `verifier` 综合判断。

**竞赛模式特殊处理**：由于 LeetCode 格式代码（类方法）无法直接在 Wandbox 上运行，竞赛模式下会跳过在线验证，直接标记为通过。

如果 `code_execution` 显示编译失败、语法错误、运行失败或超时，`verifier` 会不依赖模型、直接生成失败审核结果，设置 `rollback_target=coder`，并把在线错误输出写入 `improvement_suggestions`。随后路由会回到 `coder`，coder 会带着已有代码、在线检查结果和 verifier 建议重新生成修复后的完整代码。

verifier 未通过时会根据 `rollback_target` 回退：

```text
verifier -> planner
verifier -> coder
verifier -> formatter
```

当审核失败且 `retry_count <= max_retry` 时，verifier 会写入审核反馈消息并让流程回退修正；超过最大重试次数后直接进入 formatter 展示当前结果和问题。

## 状态与上下文

当前版本不再使用独立的本地 `services/memory.py` 或 `services/session.py`。多轮上下文由 LangGraph 的 `MemorySaver` checkpointer 和同一 `thread_id` 下的消息状态维护。

关键状态字段包括：

- `problem_text`：当前算法题原文
- `analysis`：题意分析结构化结果
- `strategy`：策略规划结构化结果
- `pseudocode`：伪代码结构化结果
- `code_result`：代码生成结果
- `code_execution`：在线编译、语法检查和空输入运行结果
- `verification`：审核结果
- `mode`：当前输出模式（teaching/contest）
- `teaching_stage`：当前教学阶段，可能是 `analysis`、`strategy`、`implementation`、`done`
- `awaiting_user_feedback`：是否正在等待用户继续或追问
- `response_mode`：当前回复模式，如 `analysis_only`、`strategy_only`、`implementation_only`、`code_only`、`followup`、`chat`

## 测试

安装开发依赖后运行：

```bash
pytest
```

当前测试覆盖：

- orchestrator 后路由
- orchestrator 用户意图识别：新题、继续、停止、重讲、追问、代码请求、完整题解和普通聊天
- verifier 后路由与回退逻辑
- verifier 与 coder 在编译/运行错误场景下的自动修复闭环
- code_runner 对 Wandbox 在线 API 结果的归一化、编译错误识别和不支持语言处理
- LLM 结构化 JSON 解析
- markdown 包裹 JSON、前后缀文本、字符串内原始换行等容错场景
- 结构化输出修复流程

## 导出架构图

运行：

```bash
python export_graph_png.py
```

脚本会尝试生成 `agent_graph.png`。如果 PNG 渲染失败，则导出 Mermaid 源码到 `agent_graph.mmd`。
