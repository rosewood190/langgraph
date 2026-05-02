from __future__ import annotations

from typing import Annotated, Literal

from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from typing_extensions import NotRequired, TypedDict


class ProblemAnalysis(BaseModel):
    """题意分析结果 - 混合模式：自然语言 + 结构化元数据"""
    explanation: str = Field(
        default="",
        description="用自然、口语化的方式讲解题意，就像老师在面对面教学。"
        "应该包含：题目在问什么、输入输出是什么样的（如果有）、有哪些约束、"
        "这道题的类型、以及你观察到的关键点。语言要流畅自然，不要生硬地列举字段。"
    )
    problem_type: str = Field(default="", description="题型，如：动态规划、回溯、贪心、图论等")
    key_points: list[str] = Field(
        default_factory=list,
        description="3-5个关键观察点，用于后续追问定位"
    )
    has_input: bool = Field(default=True, description="题目是否有输入")
    has_constraints: bool = Field(default=True, description="题目是否有明确的数据范围约束")
    need_clarification: bool = Field(default=False, description="是否需要澄清")
    clarification_question: str = Field(default="", description="需要澄清的问题")


class StrategyPlan(BaseModel):
    """算法策略规划 - 混合模式：自然语言 + 结构化元数据"""
    explanation: str = Field(
        default="",
        description="用对话的方式讲解策略选择。"
        "应该包含：选什么方法、为什么选、大致怎么做、复杂度如何、要注意什么。"
        "语言要自然流畅，像是在和学生讨论，不要生硬地列举字段。"
    )
    strategy_name: str = Field(default="", description="策略名称，如：动态规划、回溯、贪心等")
    time_complexity: str = Field(default="", description="时间复杂度")
    space_complexity: str = Field(default="", description="空间复杂度")
    key_steps: list[str] = Field(
        default_factory=list,
        description="主要步骤（3-5步），用于后续追问定位"
    )


class PseudocodeResult(BaseModel):
    """伪代码生成结果 - 混合模式"""
    explanation: str = Field(
        default="",
        description="用自然语言讲解伪代码的组织方式和关键点。"
        "包括：状态如何定义、如何初始化、转移逻辑、遍历顺序等。"
    )
    pseudocode: str = Field(default="", description="伪代码文本")
    key_points: list[str] = Field(
        default_factory=list,
        description="实现时需要特别注意的点"
    )


class CodeResult(BaseModel):
    language: str = "C++"
    cpp_code: str = ""
    compile_ready: bool = True


class CodeExecutionResult(BaseModel):
    language: str = ""
    supported: bool = False
    compile_passed: bool = False
    run_passed: bool = False
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    error_stage: str = ""
    message: str = ""


class VerificationResult(BaseModel):
    passed: bool = False
    issues: list[str] = Field(default_factory=list)
    rollback_target: str = ""
    improvement_suggestions: list[str] = Field(default_factory=list)


class ProblemAnalysisState(TypedDict):
    explanation: str
    problem_type: str
    key_points: list[str]
    has_input: bool
    has_constraints: bool
    need_clarification: bool
    clarification_question: str


class StrategyPlanState(TypedDict):
    explanation: str
    strategy_name: str
    time_complexity: str
    space_complexity: str
    key_steps: list[str]


class PseudocodeResultState(TypedDict):
    explanation: str
    pseudocode: str
    key_points: list[str]


class CodeResultState(TypedDict):
    language: str
    cpp_code: str
    compile_ready: bool


class CodeExecutionResultState(TypedDict):
    language: str
    supported: bool
    compile_passed: bool
    run_passed: bool
    exit_code: int | None
    stdout: str
    stderr: str
    error_stage: str
    message: str


class VerificationResultState(TypedDict):
    passed: bool
    issues: list[str]
    rollback_target: str
    improvement_suggestions: list[str]


TeachingStage = Literal["analysis", "strategy", "implementation", "done"]
ResponseMode = Literal[
    "analysis_only",
    "strategy_only",
    "implementation_only",
    "code_only",
    "full_solution",
    "followup",
    "chat",
]
LastTeachingNode = Literal["analyst", "planner", "implementation"]
OrchestratorRoute = Literal["chat", "followup", "analyst", "planner", "pseudocode", "coder"]


class GraphState(TypedDict):
    messages: Annotated[list, add_messages]
    problem_text: NotRequired[str]
    analysis: NotRequired[ProblemAnalysisState | None]
    strategy: NotRequired[StrategyPlanState | None]
    pseudocode: NotRequired[PseudocodeResultState | None]
    code_result: NotRequired[CodeResultState | None]
    code_execution: NotRequired[CodeExecutionResultState | None]
    verification: NotRequired[VerificationResultState | None]
    orchestrator_route: OrchestratorRoute
    retry_count: int
    max_retry: int
    mode: Literal["teaching", "contest", "interview"]
    teaching_stage: TeachingStage
    awaiting_user_feedback: bool
    last_teaching_node: NotRequired[LastTeachingNode]
    response_mode: ResponseMode
    response_text: str
    agent_trace: NotRequired[list[str]]
