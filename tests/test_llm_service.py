import pytest
from pydantic import BaseModel

from app.services.llm import LLMService, StructuredOutputError


class DemoSchema(BaseModel):
    name: str
    count: int


class DemoInvokeResponse:
    def __init__(self, content) -> None:
        self.content = content


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


def test_parse_json_with_raw_newline_inside_string() -> None:
    service = object.__new__(LLMService)
    content = '{"name": "demo\nexample", "count": 4}'
    data = service._parse_structured_content(content, "analyst")
    assert data == {"name": "demo\nexample", "count": 4}


def test_invoke_structured_uses_repair_when_initial_parse_fails() -> None:
    service = object.__new__(LLMService)
    responses = iter(
        [
            DemoInvokeResponse('{"name": "demo"\n"count": 4}'),
            DemoInvokeResponse('{"name": "demo", "count": 4}'),
        ]
    )

    service.llm = type(
        "FakeLLM",
        (),
        {
            "invoke": staticmethod(lambda messages, config=None: next(responses)),
        },
    )()

    result = service.invoke_structured("system", "payload", DemoSchema, agent_name="analyst")
    assert result.name == "demo"
    assert result.count == 4


def test_parse_invalid_json_raises_structured_output_error() -> None:
    service = object.__new__(LLMService)
    content = '{"name": "demo"\n"count": 4}'
    with pytest.raises(StructuredOutputError) as exc_info:
        service._parse_structured_content(content, "pseudocode")

    assert "pseudocode 节点结构化输出解析失败" in str(exc_info.value)
    assert exc_info.value.agent_name == "pseudocode"
    assert exc_info.value.raw_content == content
