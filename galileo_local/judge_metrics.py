"""LLM-judge scores for the chat stream.

Active ``kind: llm_judge`` metrics are scored with ``build_metric_judge`` at
temperature 0, on spans whose type is listed in ``span_types``. A failure of
the judge is stored as an error. It is not stored as a pass. ``find_clear_pii``
is read again on the rationale before that rationale can be written.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from galileo_local.catalog import METRICS, metrics_for_span
from galileo_local.judges import MetricScore, build_metric_judge, metric_prompt
from galileo_local.models import Trace
from galileo_local.pii_oracle import find_clear_pii

JUDGE_ERROR = "erreur de juge"
_WITHHELD = "Rationale retenue par l'oracle."


class PersistedJudgeScore(BaseModel):
    """One stored judge score. The four metric fields match ``MetricScore``."""

    model_config = ConfigDict(extra="forbid")

    span_index: int = Field(ge=0)
    metric_id: str = Field(min_length=1)
    score: float = Field(ge=0.0, le=1.0)
    passed: bool
    rationale: str = Field(min_length=1, max_length=2000)
    status: str = "ok"

    @field_validator("metric_id")
    @classmethod
    def metric_is_active_judge(cls, value: str) -> str:
        if value not in _active_judge_ids():
            raise ValueError("metric is not an active llm judge")
        return value

    @field_validator("status")
    @classmethod
    def status_is_known(cls, value: str) -> str:
        if value not in {"ok", "error"}:
            raise ValueError("unknown judge status")
        return value

    @model_validator(mode="after")
    def error_is_not_a_pass(self) -> PersistedJudgeScore:
        if find_clear_pii(self.rationale):
            raise ValueError("clear personal data in rationale")
        if self.status == "error" and self.passed:
            raise ValueError("a judge error is not a pass")
        return self


def judge_scores(
    trace: Trace,
    model: Any,
    *,
    only_substantive: bool = False,
    enabled: frozenset[str] | None = None,
) -> list[PersistedJudgeScore]:
    """One row per active judge metric that applies to a span.

    ``model`` is the Agno model passed to ``build_metric_judge``. Temperature
    is forced to 0 before the agent is built and before each call. An exception,
    a foreign metric id, or a rationale the oracle rejects becomes an error row.
    The trace itself is left to the caller. ``only_substantive`` skips spans
    whose output is too short to be the model answer.
    When ``enabled`` is set, only those metric ids are scored.
    """
    pairs = [
        (index, metric)
        for index, span in enumerate(trace.spans)
        for metric in metrics_for_span(span.type.value, enabled=enabled)
        if metric.kind == "llm_judge"
        and (not only_substantive or _substantive_answer(span))
    ]
    rows: list[PersistedJudgeScore] = []
    for index, metric in pairs:
        try:
            _temperature_zero(model)
            agent = build_metric_judge(model)
            if getattr(agent, "model", None) is not model or model.temperature != 0:
                raise RuntimeError("judge temperature is not 0")
            result = agent.run(metric_prompt(metric, trace.spans[index]), stream=False)
            rows.append(_from_model(index, metric.id, _as_metric_score(result)))
        except Exception:
            rows.append(_error(index, metric.id))
    return rows


def prepare_for_storage(
    *,
    metric_id: str,
    score: float,
    passed: bool,
    rationale: str,
    status: str,
) -> tuple[float, bool, str, str]:
    """Rationale gate used immediately before the score is inserted.

    A judge rationale that contains a clear personal value is not written.
    The row becomes an error. The value itself is not copied. A code rationale
    is replaced by the withheld sentence and keeps the code score.
    """
    kinds = find_clear_pii(rationale)
    if kinds:
        if metric_id in _active_judge_ids():
            return 0.0, False, _oracle_line(kinds), "error"
        return float(score), bool(passed), _WITHHELD, "ok"
    if status == "error":
        return 0.0, False, rationale, "error"
    return float(score), bool(passed), rationale, "ok"


def _from_model(index: int, metric_id: str, score: MetricScore) -> PersistedJudgeScore:
    if score.metric_id != metric_id:
        return _error(index, metric_id)
    kinds = find_clear_pii(score.rationale)
    if kinds:
        return _oracle_error(index, metric_id, kinds)
    return PersistedJudgeScore(
        span_index=index,
        metric_id=metric_id,
        score=score.score,
        passed=score.passed,
        rationale=score.rationale,
        status="ok",
    )


def _oracle_error(index: int, metric_id: str, kinds: list[str]) -> PersistedJudgeScore:
    return PersistedJudgeScore(
        span_index=index,
        metric_id=metric_id,
        score=0.0,
        passed=False,
        rationale=_oracle_line(kinds),
        status="error",
    )


def _error(index: int, metric_id: str) -> PersistedJudgeScore:
    return PersistedJudgeScore(
        span_index=index,
        metric_id=metric_id,
        score=0.0,
        passed=False,
        rationale=JUDGE_ERROR,
        status="error",
    )


def _oracle_line(kinds: list[str]) -> str:
    line = "L'oracle signale : " + ", ".join(kinds) + "."
    if find_clear_pii(line):
        return JUDGE_ERROR
    return line


def _as_metric_score(result: Any) -> MetricScore:
    content = getattr(result, "content", None)
    if isinstance(content, MetricScore):
        return content
    if isinstance(content, dict):
        return MetricScore.model_validate(content)
    if isinstance(content, str):
        return MetricScore.model_validate_json(content)
    raise TypeError("judge did not return a MetricScore")


def _substantive_answer(span: Any) -> bool:
    if getattr(getattr(span, "type", None), "value", "") not in {"agent", "llm"}:
        return False
    return len(span.output_masked.strip()) >= 40


def _temperature_zero(model: Any) -> None:
    if not hasattr(model, "temperature"):
        raise AttributeError("judge model has no temperature")
    model.temperature = 0
    if model.temperature != 0:
        raise RuntimeError("judge temperature is not 0")


def _active_judge_ids() -> set[str]:
    return {
        metric.id
        for metric in METRICS
        if metric.kind == "llm_judge" and metric.cimr_stream
    }
