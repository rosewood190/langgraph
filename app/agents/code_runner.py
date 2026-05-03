from __future__ import annotations

from typing import Any

import requests

from app.agents.trace import append_agent_trace
from app.config import settings
from app.state import GraphState

MAX_OUTPUT_CHARS = 4000


WANDBOX_LANGUAGE_CONFIG = {
    "C++": {"compiler": "gcc-head", "options": "warning,c++17"},
    "Python": {"compiler": "cpython-head", "options": ""},
    "Java": {"compiler": "openjdk-head", "options": ""},
    "Go": {"compiler": "go-head", "options": ""},
    "JavaScript": {"compiler": "nodejs-head", "options": ""},
    "Rust": {"compiler": "rust-head", "options": ""},
}


class OnlineCodeRunnerError(RuntimeError):
    pass


def _clip(text: str) -> str:
    if len(text) <= MAX_OUTPUT_CHARS:
        return text
    return text[:MAX_OUTPUT_CHARS] + "\n...（输出已截断）"


def _failure_result(language: str, stage: str, message: str, *, supported: bool | None = None) -> dict:
    return {
        "language": language,
        "supported": language in WANDBOX_LANGUAGE_CONFIG if supported is None else supported,
        "compile_passed": False,
        "run_passed": False,
        "exit_code": None,
        "stdout": "",
        "stderr": message,
        "error_stage": stage,
        "message": message,
    }


def _post_to_wandbox(payload: dict[str, Any]) -> dict[str, Any]:
    response = requests.post(settings.code_runner_base_url, json=payload, timeout=settings.code_runner_timeout)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict):
        raise OnlineCodeRunnerError("在线代码执行服务返回了非 JSON 对象。")
    return data


def _normalize_wandbox_result(language: str, data: dict[str, Any]) -> dict:
    status = str(data.get("status", ""))
    signal = str(data.get("signal", ""))
    compiler_output = _clip(str(data.get("compiler_output") or ""))
    compiler_error = _clip(str(data.get("compiler_error") or ""))
    compiler_message = _clip(str(data.get("compiler_message") or ""))
    program_output = _clip(str(data.get("program_output") or ""))
    program_error = _clip(str(data.get("program_error") or ""))
    program_message = _clip(str(data.get("program_message") or ""))

    compile_text = _clip("".join([compiler_output, compiler_error, compiler_message]))
    run_error_text = _clip("".join([program_error]))
    stdout = program_output or program_message

    if compile_text.strip():
        return {
            "language": language,
            "supported": True,
            "compile_passed": False,
            "run_passed": False,
            "exit_code": int(status) if status.lstrip("-").isdigit() else None,
            "stdout": "",
            "stderr": compile_text,
            "error_stage": "compile",
            "message": "代码未通过 Wandbox 在线编译或语法检查。",
        }

    run_passed = status == "0" and not signal and not run_error_text.strip()
    return {
        "language": language,
        "supported": True,
        "compile_passed": True,
        "run_passed": run_passed,
        "exit_code": int(status) if status.lstrip("-").isdigit() else None,
        "stdout": stdout,
        "stderr": run_error_text,
        "error_stage": "" if run_passed else "run",
        "message": "代码已通过 Wandbox 在线编译并完成一次空输入运行。" if run_passed else "代码通过 Wandbox 在线编译，但运行阶段返回异常。",
    }


def run_code_runner(state: GraphState) -> dict:
    code_result = state.get("code_result") or {}
    language = code_result.get("language", "C++")
    code_text = code_result.get("cpp_code", "")
    mode = state.get("mode", "teaching")

    # 竞赛模式下，LeetCode 格式代码无法直接在 Wandbox 运行，跳过在线验证
    if mode == "contest":
        return {
            "agent_trace": append_agent_trace(state, "code_runner"),
            "code_execution": {
                "language": language,
                "supported": True,
                "compile_passed": True,
                "run_passed": True,
                "exit_code": 0,
                "stdout": "",
                "stderr": "",
                "error_stage": "",
                "message": "竞赛模式：代码格式为 LeetCode 标准，跳过在线验证。",
            },
        }

    if not code_text.strip():
        return {
            "agent_trace": append_agent_trace(state, "code_runner"),
            "code_execution": _failure_result(language, "prepare", "没有可执行的代码内容。"),
        }

    config = WANDBOX_LANGUAGE_CONFIG.get(language)
    if config is None:
        return {
            "agent_trace": append_agent_trace(state, "code_runner"),
            "code_execution": _failure_result(language, "prepare", f"Wandbox 暂不支持对 {language} 进行在线编译或运行检查。", supported=False),
        }

    payload = {
        "code": code_text,
        "compiler": config["compiler"],
        "options": config["options"],
        "stdin": "",
        "compiler-option-raw": "",
        "runtime-option-raw": "",
        "save": False,
    }

    try:
        data = _post_to_wandbox(payload)
    except requests.Timeout:
        return {
            "agent_trace": append_agent_trace(state, "code_runner"),
            "code_execution": _failure_result(language, "timeout", f"在线代码检查超过 {settings.code_runner_timeout} 秒超时。", supported=True),
        }
    except requests.RequestException as exc:
        return {
            "agent_trace": append_agent_trace(state, "code_runner"),
            "code_execution": _failure_result(language, "network", f"在线代码检查请求失败：{exc}", supported=True),
        }
    except Exception as exc:
        return {
            "agent_trace": append_agent_trace(state, "code_runner"),
            "code_execution": _failure_result(language, "prepare", f"在线代码检查过程异常：{exc}", supported=True),
        }

    return {
        "agent_trace": append_agent_trace(state, "code_runner"),
        "code_execution": _normalize_wandbox_result(language, data),
    }
