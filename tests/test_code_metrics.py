"""Code metrics are stored with a trace. Judges and SQL stay out."""

import inspect
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import galileo_local.code_metrics as code_metrics
from galileo_local.app import create_app
from galileo_local.catalog import METRICS
from galileo_local.code_metrics import (
    code_scores,
    pii_score,
    precision_at_k_score,
    tool_error_score,
)
from galileo_local.console import FIXTURE_REQUEST_ID, fixture_gateway_trace
from galileo_local.models import Span, SpanType, Trace
from galileo_local.pii_oracle import find_clear_pii

_CLEAR_EMAIL = "marie.dupont@cimr.ma"
_QUESTION = "Question sur le dossier [CIMR_CIN_abcd1234]."
_ANSWER = "La liquidation suit [CIMR_PROCEDURE_aa11]."
_FIELDS = {"span_index", "metric_id", "score", "passed", "rationale"}


def _client(db_path: Path):
    return TestClient(create_app(db_path))


def _rows(client: TestClient, request_id: str) -> list[dict]:
    response = client.get(f"/v1/traces/{request_id}/scores")
    assert response.status_code == 200
    body = response.json()
    assert body["request_id"] == request_id
    return body["scores"]


def _by_span(scores: list[dict]) -> dict[int, list[dict]]:
    grouped: dict[int, list[dict]] = {}
    for row in scores:
        grouped.setdefault(row["span_index"], []).append(row)
    return grouped


def test_active_code_metrics_are_the_catalog_trio() -> None:
    enabled = {metric.id for metric in METRICS if metric.cimr_stream and metric.kind == "code"}
    assert enabled == {"pii", "tool_error", "precision_at_k"}
    assert "build_metric_judge" not in inspect.getsource(code_metrics)
    assert "agno" not in inspect.getsource(code_metrics)


def test_posted_fixture_pii_scores_pass(tmp_path: Path) -> None:
    payload = fixture_gateway_trace().model_dump(mode="json")
    with _client(tmp_path / "galileo.db") as client:
        created = client.post("/v1/traces", json=payload)
        assert created.status_code == 200
        assert created.json() == payload
        assert client.get(f"/v1/traces/{FIXTURE_REQUEST_ID}").json() == payload

        scores = _rows(client, FIXTURE_REQUEST_ID)
        assert len(scores) == len(payload["spans"])
        assert {row["metric_id"] for row in scores} == {"pii"}
        seen = set()
        for row in scores:
            assert set(row) == _FIELDS
            assert row["score"] == 1.0
            assert 0 <= row["score"] <= 1
            assert row["passed"] is True
            assert row["rationale"]
            assert find_clear_pii(row["rationale"]) == []
            assert _QUESTION not in row["rationale"]
            assert _ANSWER not in row["rationale"]
            seen.add(row["span_index"])
        assert seen == set(range(len(payload["spans"])))


def test_tool_error_reads_status_and_precision_needs_labels(tmp_path: Path) -> None:
    trace = Trace(
        project="cimr-gpt",
        log_stream="gateway",
        session_id="sess_metrics",
        request_id="req_metrics",
        name="cimr_gateway",
        spans=[
            Span(
                name="web_search",
                type=SpanType.TOOL,
                input_masked="conditions de liquidation",
                output_masked="ok",
                metadata={"status": "ok"},
            ),
            Span(
                name="web_search_failed",
                type=SpanType.TOOL,
                input_masked="conditions de liquidation",
                output_masked="échec outil",
                metadata={"status": "error"},
            ),
            Span(
                name="web_search_quiet",
                type=SpanType.TOOL,
                input_masked="conditions de liquidation",
                output_masked="error",
                metadata={"count": "1"},
            ),
            Span(
                name="knowledge",
                type=SpanType.RETRIEVER,
                input_masked="liquidation",
                output_masked=_ANSWER,
                metadata={"chunk_count": "3"},
            ),
            Span(
                name="knowledge_labeled",
                type=SpanType.RETRIEVER,
                input_masked="liquidation",
                output_masked=_ANSWER,
                metadata={"labels": "1,0,1", "k": "3"},
            ),
            Span(
                name="llm_completion",
                type=SpanType.LLM,
                input_masked=_QUESTION,
                output_masked="réponse masquée",
                metadata={"layer": "6"},
            ),
        ],
    )
    disabled = {metric.id for metric in METRICS if not metric.cimr_stream}
    judges = {metric.id for metric in METRICS if metric.kind == "llm_judge"}
    with _client(tmp_path / "galileo.db") as client:
        assert client.post("/v1/traces", json=trace.model_dump(mode="json")).status_code == 200
        grouped = _by_span(_rows(client, "req_metrics"))

    ok = {row["metric_id"]: row for row in grouped[0]}
    assert ok["tool_error"]["score"] == 1.0
    assert ok["tool_error"]["passed"] is True
    assert ok["pii"]["passed"] is True

    failed = {row["metric_id"]: row for row in grouped[1]}
    assert failed["tool_error"]["score"] == 0.0
    assert failed["tool_error"]["passed"] is False
    assert "échec outil" not in failed["tool_error"]["rationale"]

    quiet = {row["metric_id"] for row in grouped[2]}
    assert quiet == {"pii"}

    unlabeled = {row["metric_id"]: row for row in grouped[3]}
    assert "precision_at_k" not in unlabeled
    assert unlabeled["pii"]["score"] == 1.0

    labeled = {row["metric_id"]: row for row in grouped[4]}
    assert labeled["precision_at_k"]["score"] == pytest.approx(2 / 3)
    assert labeled["precision_at_k"]["score"] != 1.0
    assert labeled["precision_at_k"]["passed"] is False
    assert _ANSWER not in labeled["precision_at_k"]["rationale"]

    completion = {row["metric_id"] for row in grouped[5]}
    assert completion == {"pii"}

    present = {row["metric_id"] for rows in grouped.values() for row in rows}
    assert present <= {"pii", "tool_error", "precision_at_k"}
    assert present.isdisjoint(disabled)
    assert present.isdisjoint(judges)


def test_missing_scores_do_not_create_a_database(tmp_path: Path) -> None:
    db_path = tmp_path / "galileo.db"
    with _client(db_path) as client:
        missing = client.get("/v1/traces/req_absent/scores")
        assert missing.status_code == 404
        assert not db_path.exists()


def test_clear_email_is_refused_before_a_score_is_stored(tmp_path: Path) -> None:
    db_path = tmp_path / "galileo.db"
    payload = {
        "project": "cimr-gpt",
        "log_stream": "gateway",
        "session_id": "sess_metrics",
        "request_id": "req_clear_metric",
        "name": "cimr_gateway",
        "spans": [
            {
                "name": "llm_completion",
                "type": "llm",
                "input_masked": f"Contacter {_CLEAR_EMAIL}",
                "output_masked": "ok",
            }
        ],
    }
    with _client(db_path) as client:
        created = client.post("/v1/traces", json=payload)
        assert created.status_code == 200
        scores = client.get("/v1/traces/req_clear_metric/scores").json()["scores"]
        assert any(row["metric_id"] == "pii" and row["passed"] is False for row in scores)


def test_pii_score_is_zero_when_the_oracle_finds_clear_text() -> None:
    span = Span.model_construct(
        name="llm_completion",
        type=SpanType.LLM,
        input_masked=f"Contacter {_CLEAR_EMAIL}",
        output_masked="ok",
        metadata={},
    )
    score = pii_score(span)
    assert score.metric_id == "pii"
    assert score.score == 0.0
    assert score.passed is False
    assert "email" in score.rationale
    assert _CLEAR_EMAIL not in score.rationale
    assert find_clear_pii(score.rationale) == []


def test_tool_error_ignores_output_and_unknown_status() -> None:
    quiet = Span(
        name="web_search",
        type=SpanType.TOOL,
        input_masked="q",
        output_masked="error",
        metadata={"count": "1"},
    )
    assert tool_error_score(quiet) is None

    unknown = Span(
        name="web_search",
        type=SpanType.TOOL,
        input_masked="q",
        output_masked="ok",
        metadata={"status": "banana"},
    )
    assert tool_error_score(unknown) is None

    coded = Span(
        name="web_search",
        type=SpanType.TOOL,
        input_masked="q",
        output_masked="ok",
        metadata={"status_code": "500"},
    )
    failed = tool_error_score(coded)
    assert failed is not None
    assert failed.score == 0.0
    assert failed.passed is False

    succeeded = tool_error_score(
        Span(
            name="web_search",
            type=SpanType.TOOL,
            input_masked="q",
            output_masked="error",
            metadata={"status_code": "200"},
        )
    )
    assert succeeded is not None
    assert succeeded.score == 1.0
    assert succeeded.passed is True


def test_precision_at_k_does_not_invent_a_perfect_score() -> None:
    unlabeled = Span(
        name="knowledge",
        type=SpanType.RETRIEVER,
        input_masked="liquidation",
        output_masked=_ANSWER,
        metadata={"chunk_count": "3"},
    )
    assert precision_at_k_score(unlabeled) is None

    short = Span(
        name="knowledge",
        type=SpanType.RETRIEVER,
        input_masked="liquidation",
        output_masked=_ANSWER,
        metadata={"labels": "1,0", "k": "5"},
    )
    assert precision_at_k_score(short) is None

    perfect = precision_at_k_score(
        Span(
            name="knowledge",
            type=SpanType.RETRIEVER,
            input_masked="liquidation",
            output_masked=_ANSWER,
            metadata={"labels": "1,1"},
        )
    )
    assert perfect is not None
    assert perfect.score == 1.0
    assert perfect.passed is True

    partial = precision_at_k_score(
        Span(
            name="knowledge",
            type=SpanType.RETRIEVER,
            input_masked="liquidation",
            output_masked=_ANSWER,
            metadata={"labels": "[1, 0, 1, 0]", "k": "2"},
        )
    )
    assert partial is not None
    assert partial.score == pytest.approx(0.5)
    assert partial.passed is False
    assert partial.metric_id == "precision_at_k"


def test_code_scores_skip_sql_even_on_a_tool_span() -> None:
    trace = Trace(
        project="cimr-gpt",
        log_stream="gateway",
        session_id="sess_metrics",
        request_id="req_sql",
        name="cimr_gateway",
        spans=[
            Span(
                name="web_search",
                type=SpanType.TOOL,
                input_masked="q",
                output_masked="ok",
                metadata={"status": "ok"},
            )
        ],
    )
    ids = {row.metric_id for row in code_scores(trace)}
    assert ids == {"pii", "tool_error"}
    assert "sql_injection" not in ids
    assert "sql_correctness" not in ids
    assert "visual_quality" not in ids
