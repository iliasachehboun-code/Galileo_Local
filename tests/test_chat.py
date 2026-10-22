"""The chat endpoint stores a clear-text Agno turn as a scored trace."""

from dataclasses import dataclass, field
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

pytest.importorskip("agno")
from agno.models.base import Model
from agno.models.response import ModelResponse

from galileo_local.app import create_app
from galileo_local.settings import LOG_STREAM, PROJECT_NAME


@dataclass
class EchoModel(Model):
    id: str = "echo-chat"
    temperature: float = 0.2
    supports_native_structured_outputs: bool = False
    prompts: list[str] = field(default_factory=list)

    def invoke(self, *args, **kwargs) -> ModelResponse:
        messages = kwargs.get("messages") or []
        last = ""
        for message in messages:
            content = getattr(message, "content", "")
            if isinstance(content, str) and content.strip():
                last = content
        self.prompts.append(last)
        return ModelResponse(role="assistant", content=f"Echo: {last}")

    async def ainvoke(self, *args, **kwargs) -> ModelResponse:
        return self.invoke(*args, **kwargs)

    def invoke_stream(self, *args, **kwargs):
        yield self.invoke(*args, **kwargs)

    async def ainvoke_stream(self, *args, **kwargs):
        yield self.invoke(*args, **kwargs)

    def _parse_provider_response(self, response, **kwargs) -> ModelResponse:
        return ModelResponse(content="")

    def _parse_provider_response_delta(self, response) -> ModelResponse:
        return ModelResponse(content="")


def test_chat_api_stores_a_trace(tmp_path: Path) -> None:
    model = EchoModel()
    with TestClient(create_app(tmp_path / "galileo.db", chat_model=model)) as client:
        response = client.post(
            "/v1/chat",
            json={"message": "Bonjour Galileo", "session_id": "sess_demo"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["reply"].startswith("Echo:")
        assert body["session_id"] == "sess_demo"
        request_id = body["request_id"]
        trace = client.get(f"/v1/traces/{request_id}")
        assert trace.status_code == 200
        payload = trace.json()
        assert payload["project"] == PROJECT_NAME
        assert payload["log_stream"] == LOG_STREAM
        assert payload["name"] == "chat_agent"
        assert any(span["type"] == "agent" for span in payload["spans"])
        assert any(span["type"] == "llm" for span in payload["spans"])
        assert "Bonjour Galileo" in trace.text
        scores = client.get(f"/v1/traces/{request_id}/scores").json()["scores"]
        assert any(row["metric_id"] == "pii" for row in scores)
