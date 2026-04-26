from __future__ import annotations

import json
import re
from json import JSONDecodeError
from typing import Any, Type

from pydantic import BaseModel

from app.config import settings

try:
    from langchain_openai import ChatOpenAI
except ImportError:  # pragma: no cover
    ChatOpenAI = None


class StructuredOutputError(ValueError):
    def __init__(self, agent_name: str, raw_content: str, original_error: Exception | None = None) -> None:
        self.agent_name = agent_name
        self.raw_content = raw_content
        self.original_error = original_error
        snippet = raw_content[:400].replace("\n", "\\n")
        message = f"{agent_name} 节点结构化输出解析失败。原始返回片段：{snippet}"
        if original_error is not None:
            message = f"{message}；底层错误：{original_error}"
        super().__init__(message)


class LLMService:
    def __init__(self) -> None:
        if ChatOpenAI is None:
            raise ImportError(
                "langchain-openai is not installed. Please install project dependencies first."
            )

        if not settings.api_key:
            raise ValueError(
                "未检测到 OPENAI_API_KEY。请确认项目根目录 .env 文件中已正确填写密钥。"
            )

        self.llm = ChatOpenAI(
            model=settings.model_name,
            api_key=settings.api_key,
            base_url=settings.base_url,
            temperature=settings.temperature,
        )

    def _extract_json_candidate(self, content: str) -> str:
        stripped = content.strip()
        fenced_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", stripped, re.IGNORECASE)
        if fenced_match:
            stripped = fenced_match.group(1).strip()

        if stripped.startswith("{") and stripped.endswith("}"):
            return stripped

        start = stripped.find("{")
        if start == -1:
            return stripped

        depth = 0
        in_string = False
        escape = False
        for index in range(start, len(stripped)):
            char = stripped[index]
            if in_string:
                if escape:
                    escape = False
                elif char == "\\":
                    escape = True
                elif char == '"':
                    in_string = False
                continue

            if char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return stripped[start:index + 1]

        return stripped[start:]

    def _parse_structured_content(self, content: str, agent_name: str) -> dict[str, Any]:
        candidate = self._extract_json_candidate(content)
        try:
            data = json.loads(candidate)
        except JSONDecodeError as exc:
            raise StructuredOutputError(agent_name, content, exc) from exc

        if not isinstance(data, dict):
            raise StructuredOutputError(agent_name, content)
        return data

    def invoke_structured(
        self,
        system_prompt: str,
        user_payload: str,
        schema: Type[BaseModel],
        agent_name: str = "unknown",
    ) -> BaseModel:
        format_prompt = (
            "请严格输出单个 JSON 对象，不要使用 markdown 代码块，不要输出额外解释。"
            "如果字段值里需要换行，请使用 JSON 字符串转义符 \\n。"
        )
        response = self.llm.invoke([
            ("system", system_prompt),
            ("human", f"{format_prompt}\n\n输入内容如下：\n{user_payload}"),
        ])
        content = response.content if isinstance(response.content, str) else json.dumps(response.content, ensure_ascii=False)
        data = self._parse_structured_content(content, agent_name)
        try:
            return schema.model_validate(data)
        except Exception as exc:
            raise StructuredOutputError(agent_name, content, exc) from exc

    def invoke_text(self, system_prompt: str, user_payload: str) -> str:
        response = self.llm.invoke([
            ("system", system_prompt),
            ("human", user_payload),
        ])
        content = response.content
        if isinstance(content, str):
            return content.strip()
        return json.dumps(content, ensure_ascii=False)


_llm_service: LLMService | None = None


def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
