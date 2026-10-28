"""The Galileo Log stream console lists traces and opens span detail."""

import re
from pathlib import Path

from fastapi.testclient import TestClient

from galileo_local.app import create_app
from galileo_local.console import (
    FIXTURE_REQUEST_ID,
    REHYDRATION_LABEL,
    fixture_gateway_trace,
    render_score_list,
)
from galileo_local.models import Span, SpanType, Trace
from galileo_local.settings import LOG_STREAM, PROJECT_NAME
from galileo_local.store import TraceStore

_QUESTION = "Explique en une phrase ce qu'est une pension de retraite."
_HOUR = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")


def _client(db_path: Path):
    return TestClient(create_app(db_path))


def _region(html: str, element_id: str, tag: str) -> str:
    marker = f'<{tag} id="{element_id}"'
    start = html.index(marker)
    end = html.index(f"</{tag}>", start)
    return html[start:end]


def _articles(html: str) -> list[str]:
    parts = html.split("<article")
    return ["<article" + part.split("</article>")[0] for part in parts[1:]]


def test_list_shows_chat_history_and_metric_columns(tmp_path: Path) -> None:
    db_path = tmp_path / "galileo.db"
    with _client(db_path) as client:
        payload = fixture_gateway_trace().model_dump(mode="json")
        assert client.post("/v1/traces", json=payload).status_code == 200
        other = fixture_gateway_trace().model_dump(mode="json")
        other["request_id"] = "req_other_chat"
        other["spans"][0]["metadata"]["role"] = "assistant"
        assert client.post("/v1/traces", json=other).status_code == 200
        outside = fixture_gateway_trace().model_dump(mode="json")
        outside["request_id"] = "req_other_stream"
        outside["log_stream"] = "lab"
        outside["spans"][0]["input_masked"] = "Question hors stream."
        assert client.post("/v1/traces", json=outside).status_code == 200

        home = client.get("/logs", follow_redirects=True)
        assert home.status_code == 200
        assert "Galileo" in home.text
        assert f"Logs: {LOG_STREAM}" in home.text
        assert f"Log Stream: {LOG_STREAM}" in home.text
        assert PROJECT_NAME in home.text
        assert 'href="/chat"' in home.text
        assert 'href="/experiments"' in home.text
        assert "Created" in home.text
        assert "External Id" in home.text
        assert "Sessions" in home.text
        assert "Traces" in home.text
        assert "Spans" in home.text
        listing = _region(home.text, "trace-list", "table")
        assert FIXTURE_REQUEST_ID in listing
        assert "req_other_chat" in listing
        assert "req_other_stream" not in listing
        assert _HOUR.search(listing)
        assert "pension de retraite" in listing
        assert "Completeness" in listing
        assert "Instruction Adherence" in listing
        assert "CIMR" not in home.text
        stored = TraceStore(db_path).list_traces(project=PROJECT_NAME, log_stream=LOG_STREAM)
        assert stored[0]["created_at"]

        root = client.get("/", follow_redirects=False)
        assert root.status_code in {307, 302}
        assert root.headers["location"] == "/logs"


def test_detail_shows_spans_and_layer8_label(tmp_path: Path) -> None:
    db_path = tmp_path / "galileo.db"
    with _client(db_path) as client:
        payload = fixture_gateway_trace().model_dump(mode="json")
        assert client.post("/v1/traces", json=payload).status_code == 200
        page = client.get(f"/logs/traces/{FIXTURE_REQUEST_ID}")
        assert page.status_code == 200
        detail = _region(page.text, "trace-detail", "div")
        assert "pension de retraite" in detail
        assert "Completeness" in page.text
        assert "Context Adherence" in page.text
        assert "layer_8_rehydration" in page.text
        assert "agent" in page.text
        assert "llm" in page.text
        assert "<li>pii 1 passed true</li>" not in page.text
        assert "oracle ne signale aucune valeur claire." in page.text
        assert "badge" in page.text

        opened = client.get(f"/logs/traces/{FIXTURE_REQUEST_ID}", params={"span": 3})
        layer8 = _articles(opened.text)[0]
        assert 'data-layer="8"' in layer8
        assert REHYDRATION_LABEL in layer8
        assert "compteur de tokens" in layer8
        assert "2" in layer8


def test_level_switch_changes_aggregation(tmp_path: Path) -> None:
    with _client(tmp_path / "galileo.db") as client:
        payload = fixture_gateway_trace().model_dump(mode="json")
        assert client.post("/v1/traces", json=payload).status_code == 200
        spans = client.get("/logs", params={"level": "spans"})
        assert spans.status_code == 200
        assert "agent" in spans.text
        assert "llm" in spans.text
        sessions = client.get("/logs", params={"level": "sessions"})
        assert sessions.status_code == 200
        assert "sess_console" in sessions.text


def test_clear_email_in_the_query_is_not_echoed(tmp_path: Path) -> None:
    with _client(tmp_path / "galileo.db") as client:
        page = client.get("/", params={"trace": "marie.dupont@cimr.ma"})
        assert page.status_code == 200
        assert "marie.dupont@cimr.ma" not in page.text


def test_experiments_link_does_not_list_traces(tmp_path: Path) -> None:
    with _client(tmp_path / "galileo.db") as client:
        client.post("/v1/traces", json=fixture_gateway_trace().model_dump(mode="json"))
        page = client.get("/experiments")
        assert page.status_code == 200
        assert "expériences" in page.text or "Experiments" in page.text
        assert "Galileo" in page.text
        assert _QUESTION not in page.text
        assert FIXTURE_REQUEST_ID not in page.text


def test_list_traces_does_not_create_a_database(tmp_path: Path) -> None:
    db_path = tmp_path / "galileo.db"
    assert TraceStore(db_path).list_traces(project=PROJECT_NAME, log_stream=LOG_STREAM) == []
    assert not db_path.exists()


def test_pii_zero_is_rendered_before_judges() -> None:
    html = render_score_list(
        [
            {"metric_id": "action_completion", "score": 0.25, "passed": True},
            {"metric_id": "pii", "score": 0, "passed": False},
            {"metric_id": "toxicity", "score": 1, "passed": True},
        ]
    )
    assert "<li>pii 0 passed false</li>" in html
    assert html.index("pii 0") < html.index("action_completion")


def test_recorded_span_shows_the_persisted_pii_score(tmp_path: Path) -> None:
    trace = Trace(
        project=PROJECT_NAME,
        log_stream=LOG_STREAM,
        session_id="sess_console",
        request_id="req_plain",
        name="chat_agent",
        spans=[
            Span(
                name="agent",
                type=SpanType.AGENT,
                input_masked="texte clair",
                output_masked="réponse claire",
                metadata={},
            )
        ],
    )
    with _client(tmp_path / "galileo.db") as client:
        assert client.post("/v1/traces", json=trace.model_dump(mode="json")).status_code == 200
        page = client.get("/logs/traces/req_plain").text
        assert "<h3>Scores</h3>" not in page
        assert "PII" in page
        assert "oracle ne signale aucune valeur claire." in page


def test_chat_page_is_served(tmp_path: Path) -> None:
    with _client(tmp_path / "galileo.db") as client:
        page = client.get("/chat")
        assert page.status_code == 200
        assert "Chat" in page.text
        assert "Galileo" in page.text
        assert 'action="/chat"' in page.text
        assert 'href="/logs"' in page.text
