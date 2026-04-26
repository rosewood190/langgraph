import pytest
from pydantic import BaseModel

from app.services.llm import LLMService, StructuredOutputError


class DemoSchema(BaseModel):
    name: str
    count: int


def test_parse_plain_json() -> None:
    service = object.__new__(LLMService)
    data = service._parse_structured_content('{"name": "demo", "count": 1}', "planner")
    assert data == {"name": "demo", "count": 1}


def test_parse_markdown_wrapped_json() -> None:
    service = object.__new__(LLMService)
    content = '```json\n{"name": "demo", "count": 2}\n```'
    data = service._parse_structured_content(content, "coder")
    assert data == {"name": "demo", "count": 2}


def test_parse_json_with_prefix_suffix() -> None:
    service = object.__new__(LLMService)
    content = '下面是结果：\n{"name": "demo", "count": 3}\n请查收'
    data = service._parse_structured_content(content, "verifier")
    assert data == {"name": "demo", "count": 3}


def test_parse_invalid_json_raises_structured_output_error() -> None:
    service = object.__new__(LLMService)
    content = '{"name": "demo"\n"count": 4}'
    with pytest.raises(StructuredOutputError) as exc_info:
        service._parse_structured_content(content, "pseudocode")

    assert "pseudocode 节点结构化输出解析失败" in str(exc_info.value)
    assert exc_info.value.agent_name == "pseudocode"
    assert exc_info.value.raw_content == content
