"""Trace and span contract for the local Galileo console.

Spans store the text the metrics will judge. Clear chat is allowed: the PII
oracle scores presence of personal data, it does not refuse the write.
Layer 8 (legacy rehydration) stays metadata only when that span name is used.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator

from galileo_local.pii_oracle import forbidden_metadata_keys

_LAYER8_NAME = "layer_8_rehydration"
_LAYER8_METADATA = frozenset({"layer", "token_count", "status"})
_LAYER8_STATUSES = frozenset({"ok"})
_TOKEN_COUNT = re.compile(r"^[0-9]{1,11}$")


class SpanType(str, Enum):
    WORKFLOW = "workflow"
    AGENT = "agent"
    LLM = "llm"
    RETRIEVER = "retriever"
    TOOL = "tool"


class Span(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    name: str = Field(min_length=1)
    type: SpanType
    input_masked: str = ""
    output_masked: str = ""
    metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("name", "input_masked", "output_masked")
    @classmethod
    def reject_layer8_text(cls, value: str, info: ValidationInfo) -> str:
        if _rejects_layer8_text(value, info):
            raise ValueError("layer 8 span must be token_count and status only")
        return value

    @field_validator("metadata")
    @classmethod
    def reject_forbidden_metadata(cls, value: dict[str, str], info: ValidationInfo) -> dict[str, str]:
        bad_keys = forbidden_metadata_keys(list(value))
        if bad_keys:
            raise ValueError("forbidden metadata keys: " + ", ".join(bad_keys))
        if _metadata_breaks_layer8(value, info):
            raise ValueError("layer 8 span must be token_count and status only")
        return value

    @model_validator(mode="after")
    def reject_layer8_body(self) -> Span:
        bad_keys = forbidden_metadata_keys(list(self.metadata))
        if bad_keys:
            raise ValueError("forbidden metadata keys: " + ", ".join(bad_keys))
        if _is_layer8(self) and _layer8_has_text(self):
            raise ValueError("layer 8 span must be token_count and status only")
        return self


class Trace(BaseModel):
    """One chat or gateway request. ``session_id`` groups the turns of a conversation."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    project: str = Field(min_length=1)
    log_stream: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    spans: list[Span] = Field(default_factory=list)


def _is_layer8_name(name: object) -> bool:
    return isinstance(name, str) and name.strip() == _LAYER8_NAME


def _is_layer8_marker(layer: object) -> bool:
    """``8``, ``08`` and the same digits wrapped in whitespace are layer 8."""
    if not isinstance(layer, str):
        return False
    compact = "".join(layer.split())
    return bool(compact) and compact.isdigit() and int(compact) == 8


def _marked_layer8(name: object, layer: object) -> bool:
    return _is_layer8_name(name) or _is_layer8_marker(layer)


def _is_layer8(span: Span) -> bool:
    return _marked_layer8(span.name, span.metadata.get("layer"))


def _count_and_status_are_labels(metadata: dict[str, str]) -> bool:
    """A count is digits. Status is the closed set, never a free sentence."""
    return bool(_TOKEN_COUNT.fullmatch(metadata.get("token_count", ""))) and (
        metadata.get("status") in _LAYER8_STATUSES
    )


def _rejects_layer8_text(value: str, info: ValidationInfo) -> bool:
    """Refuse text on layer 8 before the assignment sticks."""
    field = info.field_name
    metadata = info.data.get("metadata") or {}
    if field in {"input_masked", "output_masked"} and value:
        return _marked_layer8(info.data.get("name"), metadata.get("layer"))
    if field != "name":
        return False
    if _is_layer8_marker(metadata.get("layer")) and value != _LAYER8_NAME:
        return True
    if _is_layer8_name(value) and value != _LAYER8_NAME:
        return True
    if value == _LAYER8_NAME and (info.data.get("input_masked") or info.data.get("output_masked")):
        return True
    return False


def _metadata_breaks_layer8(value: dict[str, str], info: ValidationInfo) -> bool:
    name = info.data.get("name")
    if not _marked_layer8(name, value.get("layer")):
        return False
    if name != _LAYER8_NAME:
        return True
    if info.data.get("input_masked") or info.data.get("output_masked"):
        return True
    if set(value) != _LAYER8_METADATA or value.get("layer") != "8":
        return True
    return not _count_and_status_are_labels(value)


def _layer8_has_text(span: Span) -> bool:
    """Layer 8 keeps a digit count and a closed status. No restored answer."""
    if span.name != _LAYER8_NAME:
        return True
    if span.input_masked or span.output_masked:
        return True
    if set(span.metadata) != _LAYER8_METADATA or span.metadata.get("layer") != "8":
        return True
    return not _count_and_status_are_labels(span.metadata)


def rehydration_span(*, token_count: int, status: str) -> Span:
    """Layer 8 span. Counts and status only, never the restored text."""
    return Span(
        name=_LAYER8_NAME,
        type=SpanType.WORKFLOW,
        input_masked="",
        output_masked="",
        metadata={
            "layer": "8",
            "token_count": str(token_count),
            "status": status,
        },
    )


def public_trace_view(trace: Trace) -> dict[str, Any]:
    """JSON shape the console and the experiments runner will persist."""
    return trace.model_dump(mode="json")
