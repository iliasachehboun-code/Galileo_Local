"""Code metrics computed when a trace is stored.

Active ``kind: code`` metrics on the chat stream are ``pii``,
``tool_error``, and ``precision_at_k``. Multimodal and text-to-SQL metrics
stay in the catalog and are not scored. Judge metrics are not called.
"""

from __future__ import annotations

import json

from pydantic import BaseModel, ConfigDict, Field, field_validator

from galileo_local.catalog import METRICS, metrics_for_span
from galileo_local.judges import MetricScore
from galileo_local.models import Span, Trace
from galileo_local.pii_oracle import find_clear_pii

_TOOL_OK = frozenset({"ok", "success", "succeeded"})
_TOOL_ERROR = frozenset({"error", "failed", "failure", "timeout", "exception"})
_RELEVANT = frozenset({"1", "true", "yes", "relevant"})
_IRRELEVANT = frozenset({"0", "false", "no", "irrelevant"})
_WITHHELD = "Rationale retenue par l'oracle."


class PersistedCodeScore(BaseModel):
    """One stored code score. The four metric fields match ``MetricScore``."""

    model_config = ConfigDict(extra="forbid")

    span_index: int = Field(ge=0)
    metric_id: str = Field(min_length=1)
    score: float = Field(ge=0.0, le=1.0)
    passed: bool
    rationale: str = Field(min_length=1, max_length=2000)

    @field_validator("metric_id")
    @classmethod
    def metric_is_active_code(cls, value: str) -> str:
        allowed = {
            metric.id
            for metric in METRICS
            if metric.kind == "code" and metric.cimr_stream
        }
        if value not in allowed:
            raise ValueError("metric is not an active code metric")
        return value


def code_scores(
    trace: Trace,
    *,
    enabled: frozenset[str] | None = None,
) -> list[PersistedCodeScore]:
    """Scores for every active code metric that applies and can be computed.

    ``precision_at_k`` is omitted when the retriever span has no labels.
    ``tool_error`` is omitted when the tool span has no readable status.
    Neither omission becomes a score of 1.
    When ``enabled`` is set, only those metric ids are scored.
    """
    rows: list[PersistedCodeScore] = []
    for index, span in enumerate(trace.spans):
        for metric in metrics_for_span(span.type.value, enabled=enabled):
            if metric.kind != "code":
                continue
            scored = _score_metric(metric.id, span)
            if scored is None:
                continue
            rows.append(
                PersistedCodeScore(
                    span_index=index,
                    metric_id=scored.metric_id,
                    score=scored.score,
                    passed=scored.passed,
                    rationale=scored.rationale,
                )
            )
    return rows


def pii_score(span: Span) -> MetricScore:
    """1 when the oracle is quiet, 0 when it names a clear-text kind.

    The rationale names the kind only. A clear value is never copied.
    """
    kinds: list[str] = []
    blobs = (
        span.name,
        span.input_masked,
        span.output_masked,
        *span.metadata.keys(),
        *span.metadata.values(),
    )
    for blob in blobs:
        kinds.extend(find_clear_pii(blob))
    found = sorted(set(kinds))
    if found:
        return _metric(
            "pii",
            0.0,
            False,
            "L'oracle signale : " + ", ".join(found) + ".",
        )
    return _metric("pii", 1.0, True, "L'oracle ne signale aucune valeur claire.")


def tool_error_score(span: Span) -> MetricScore | None:
    """Read the tool status. No judge, and no score when the status is absent.

    ``metadata['status']`` is the status word (``ok`` or ``error``).
    ``metadata['status_code']`` is the Galileo code (``200`` or another integer).
    The tool output is not a status.
    """
    outcome = _tool_outcome(span)
    if outcome is None:
        return None
    if outcome:
        return _metric("tool_error", 1.0, True, "Le statut du span tool n'est pas une erreur.")
    return _metric("tool_error", 0.0, False, "Le statut du span tool est une erreur.")


def precision_at_k_score(span: Span) -> MetricScore | None:
    """Precision of the top k labels. Absent when those labels are missing.

    Labels live in ``metadata['labels']``, in rank order. ``metadata['k']``
    cuts the list. A missing, empty, or short label list does not become 1.
    ``passed`` is true only when every chunk in the top k is relevant.
    """
    labels = _labels(span.metadata.get("labels", ""))
    if labels is None:
        return None
    cutoff = _cutoff(span.metadata, len(labels))
    if cutoff is None:
        return None
    relevant = sum(1 for flag in labels[:cutoff] if flag)
    score = relevant / cutoff
    return _metric(
        "precision_at_k",
        score,
        relevant == cutoff,
        f"Precision@{cutoff} = {relevant}/{cutoff}.",
    )


def _score_metric(metric_id: str, span: Span) -> MetricScore | None:
    if metric_id == _catalog_id("pii"):
        return pii_score(span)
    if metric_id == _catalog_id("tool_error"):
        return tool_error_score(span)
    if metric_id == _catalog_id("precision_at_k"):
        return precision_at_k_score(span)
    return None


def _catalog_id(metric_id: str) -> str:
    for metric in METRICS:
        if metric.id == metric_id:
            return metric.id
    raise KeyError(metric_id)


def _metric(metric_id: str, score: float, passed: bool, rationale: str) -> MetricScore:
    if find_clear_pii(rationale):
        rationale = _WITHHELD
    return MetricScore(
        metric_id=_catalog_id(metric_id),
        score=score,
        passed=passed,
        rationale=rationale,
    )


def _tool_outcome(span: Span) -> bool | None:
    """True when the status says success, False when it says error."""
    status = span.metadata.get("status", "").strip().lower()
    if status:
        if status in _TOOL_OK:
            return True
        if status in _TOOL_ERROR:
            return False
        return None
    code = span.metadata.get("status_code", "").strip()
    if code == "200":
        return True
    if code.isdigit():
        return False
    return None


def _labels(raw: str) -> list[bool] | None:
    text = raw.strip()
    if not text:
        return None
    if text.startswith("["):
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return None
        if not isinstance(parsed, list) or not parsed:
            return None
        tokens: list[object] = list(parsed)
    else:
        parts = [part.strip() for part in text.split(",")]
        if not parts or any(part == "" for part in parts):
            return None
        tokens = list(parts)
    flags: list[bool] = []
    for token in tokens:
        flag = _relevance(token)
        if flag is None:
            return None
        flags.append(flag)
    return flags


def _relevance(token: object) -> bool | None:
    if isinstance(token, bool):
        return token
    if isinstance(token, int) and token in (0, 1):
        return bool(token)
    if isinstance(token, float) and token in (0.0, 1.0):
        return bool(token)
    if isinstance(token, str):
        word = token.strip().lower()
        if word in _RELEVANT:
            return True
        if word in _IRRELEVANT:
            return False
    return None


def _cutoff(metadata: dict[str, str], count: int) -> int | None:
    if "k" not in metadata:
        return count
    raw = metadata["k"].strip()
    if not raw.isdigit():
        return None
    k = int(raw)
    if k < 1 or k > count:
        return None
    return k
