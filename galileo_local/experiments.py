"""Named runs over traces that are already stored.

A run recomputes scores. It does not call the chat model and it does
not store a rehydrated answer. An unknown request id refuses the whole batch.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from pydantic import BaseModel, ConfigDict, Field, field_validator

from galileo_local.pii_oracle import find_clear_pii


class MissingTrace(LookupError):
    """One request id in the batch is not stored."""


class DuplicateRun(Exception):
    """The run name is already stored."""


class ExperimentCreate(BaseModel):
    """Body of ``POST /v1/experiments``."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    request_ids: list[str] = Field(min_length=1)

    @field_validator("name")
    @classmethod
    def name_is_a_label(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if not cleaned:
            raise ValueError("run name is empty")
        kinds = find_clear_pii(cleaned)
        if kinds:
            raise ValueError("clear personal data in run (" + ", ".join(kinds) + ")")
        return cleaned

    @field_validator("request_ids")
    @classmethod
    def ids_are_opaque(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        for item in value:
            if not item or not item.strip():
                raise ValueError("request_id is empty")
            kinds = find_clear_pii(item)
            if kinds:
                raise ValueError("clear personal data in run (" + ", ".join(kinds) + ")")
            cleaned.append(item)
        return cleaned


def public_score(
    request_id: str,
    span_index: int,
    metric_id: str,
    score: float,
    passed: int | bool,
    rationale: str,
    status: str,
) -> dict[str, Any]:
    """One stored score. An error row is never returned as a pass."""
    item: dict[str, Any] = {
        "request_id": request_id,
        "span_index": span_index,
        "metric_id": metric_id,
        "rationale": rationale,
    }
    if status == "error":
        item["score"] = 0.0
        item["passed"] = False
        item["status"] = "error"
        return item
    item["score"] = float(score)
    item["passed"] = bool(passed)
    return item


def pair_scores(
    left_name: str,
    right_name: str,
    left_scores: Sequence[Mapping[str, Any]],
    right_scores: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """One row per metric occurrence, with the score from each run.

    A metric present on only one run stays empty on the other side. The empty
    side is not filled with a copy of the score that does exist.
    """
    left_map = {_key(row): row for row in left_scores}
    right_map = {_key(row): row for row in right_scores}
    ordered: list[tuple[str, int, str]] = []
    seen: set[tuple[str, int, str]] = set()
    for row in list(left_scores) + list(right_scores):
        key = _key(row)
        if key in seen:
            continue
        seen.add(key)
        ordered.append(key)
    metrics: list[dict[str, Any]] = []
    for request_id, span_index, metric_id in ordered:
        key = (request_id, span_index, metric_id)
        metrics.append(
            {
                "metric_id": metric_id,
                "request_id": request_id,
                "span_index": span_index,
                "left": _side(left_map.get(key)),
                "right": _side(right_map.get(key)),
            }
        )
    return {"left": left_name, "right": right_name, "metrics": metrics}


def _key(row: Mapping[str, Any]) -> tuple[str, int, str]:
    return (str(row["request_id"]), int(row["span_index"]), str(row["metric_id"]))


def _side(row: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    side: dict[str, Any] = {
        "score": row["score"],
        "passed": bool(row["passed"]),
        "rationale": row["rationale"],
    }
    if row.get("status") == "error":
        side["score"] = 0.0
        side["passed"] = False
        side["status"] = "error"
    return side
