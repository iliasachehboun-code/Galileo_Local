"""Simple Agno chat that records one clear-text trace per message."""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field

from galileo_local.models import Span, SpanType, Trace
from galileo_local.settings import (
    CHAT_TRACE_NAME,
    DEFAULT_MODEL,
    LOG_STREAM,
    PROJECT_NAME,
    is_usable_api_key,
    openai_api_key,
)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    session_id: str = Field(default="", max_length=128)


class ChatResponse(BaseModel):
    reply: str
    request_id: str
    session_id: str
    trace_url: str


def build_chat_trace(*, message: str, reply: str, session_id: str, model_id: str) -> Trace:
    request_id = uuid.uuid4().hex
    return Trace(
        project=PROJECT_NAME,
        log_stream=LOG_STREAM,
        session_id=session_id,
        request_id=request_id,
        name=CHAT_TRACE_NAME,
        spans=[
            Span(
                name="agent",
                type=SpanType.AGENT,
                input_masked=message,
                output_masked=reply,
                metadata={"role": "assistant"},
            ),
            Span(
                name="llm",
                type=SpanType.LLM,
                input_masked=message,
                output_masked=reply,
                metadata={"model": model_id},
            ),
        ],
    )


def run_chat(
    message: str, *, session_id: str = "", model: Any | None = None
) -> tuple[ChatResponse, Trace]:
    """Call the Agno agent, then return the reply and the trace to store."""
    text = message.strip()
    if not text:
        raise ValueError("empty message")
    sid = session_id.strip() or uuid.uuid4().hex
    model_id = DEFAULT_MODEL
    if model is None:
        key = openai_api_key()
        if not is_usable_api_key(key):
            raise RuntimeError("OPENAI_API_KEY is missing or unusable")
        from agno.models.openai import OpenAIChat

        model = OpenAIChat(id=model_id, api_key=key, temperature=0.2)
    else:
        model_id = str(getattr(model, "id", model_id) or model_id)
    from agno.agent import Agent

    agent = Agent(
        name="galileo-chat",
        model=model,
        instructions=(
            "You are a helpful assistant for the local Galileo demo. "
            "Answer clearly and briefly in the user's language."
        ),
        telemetry=False,
        store_events=False,
        markdown=True,
    )
    result = agent.run(text, stream=False)
    reply = _reply_text(result)
    trace = build_chat_trace(message=text, reply=reply, session_id=sid, model_id=model_id)
    return ChatResponse(
        reply=reply,
        request_id=trace.request_id,
        session_id=sid,
        trace_url=f"/logs/traces/{trace.request_id}",
    ), trace


def _reply_text(result: Any) -> str:
    content = getattr(result, "content", None)
    if content is None:
        return str(result)
    if isinstance(content, str):
        return content.strip() or "(empty reply)"
    return str(content).strip() or "(empty reply)"
