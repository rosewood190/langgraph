from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class ProblemAnalysis(BaseModel):
    summary: str = ""
    input_format: str = ""
    output_format: str = ""
    constraints: dict[str, str] = Field(default_factory=dict)
    problem_type: str = ""
    key_observations: list[str] = Field(default_factory=list)
    need_clarification: bool = False
    clarification_question: str = ""


class StrategyPlan(BaseModel):
    strategy_name: str = ""
    core_idea: str = ""
    selected_reason: str = ""
    steps: list[str] = Field(default_factory=list)
    time_complexity: str = ""
    space_complexity: str = ""
    edge_cases: list[str] = Field(default_factory=list)


class PseudocodeResult(BaseModel):
    state_definition: str = ""
    initialization: str = ""
    transition: str = ""
    traversal_order: str = ""
    pseudocode: str = ""
    key_points: list[str] = Field(default_factory=list)


class CodeResult(BaseModel):
    language: str = "C++"
    cpp_code: str = ""
    compile_ready: bool = True


class VerificationResult(BaseModel):
    passed: bool = False
    issues: list[str] = Field(default_factory=list)
    rollback_target: str = ""
    improvement_suggestions: list[str] = Field(default_factory=list)


class FinalAnswer(BaseModel):
    analysis_text: str = ""
    strategy_text: str = ""
    pseudocode_text: str = ""
    cpp_code_text: str = ""
    complexity_text: str = ""
    verifier_summary_text: str = ""
    full_response: str = ""


class ManagerDecision(BaseModel):
    decision: str = ""
    target_agent: str = ""
    reason: str = ""


class GraphState(BaseModel):
    raw_question: str
    analysis: Optional[ProblemAnalysis] = None
    strategy: Optional[StrategyPlan] = None
    pseudocode: Optional[PseudocodeResult] = None
    code_result: Optional[CodeResult] = None
    verification: Optional[VerificationResult] = None
    final_answer: Optional[FinalAnswer] = None
    manager_decision: Optional[ManagerDecision] = None
    memory_text: str = ""
    has_pending_algorithm: bool = False
    pending_question: str = ""
    last_algorithm_question: str = ""
    last_analysis_text: str = ""
    last_strategy_text: str = ""
    last_pseudocode_text: str = ""
    last_cpp_code_text: str = ""
    last_complexity_text: str = ""
    response_text: str = ""
    response_mode: Literal["analysis_only", "full_solution", "chat", "stop", "followup"] = "analysis_only"
    current_step: str = "start"
    retry_count: int = 0
    max_retry: int = 1
    mode: Literal["teaching", "contest", "interview"] = "teaching"
