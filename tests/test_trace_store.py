"""A client can store a clear chat trace and read it back. Layer 8 stays empty."""

import json
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from galileo_local.app import create_app
from galileo_local.models import Span, SpanType, Trace, rehydration_span
from galileo_local.settings import BIND_HOST, BIND_PORT, LOG_STREAM, PROJECT_NAME
from galileo_local.store import TraceStore, default_db_path

_CLEAR_EMAIL = "marie.dupont@cimr.ma"


def _chat_trace() -> dict:
    trace = Trace(
        project=PROJECT_NAME,
        log_stream=LOG_STREAM,
        session_id="sess_7f3a",
        request_id="req_01",
        name="chat_agent",
        spans=[
            Span(
                name="agent",
                type=SpanType.AGENT,
                input_masked="Quelle est la procédure de liquidation ?",
                output_masked="Voici les étapes principales.",
                metadata={"role": "assistant"},
            ),
            Span(
                name="llm",
                type=SpanType.LLM,
                input_masked="Quelle est la procédure de liquidation ?",
                output_masked="Voici les étapes principales.",
                metadata={"model": "gpt-4o-mini"},
            ),
            rehydration_span(token_count=2, status="ok"),
        ],
    )
    return trace.model_dump(mode="json")


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "galileo.db"


@pytest.fixture
def client(db_path: Path):
    with TestClient(create_app(db_path)) as test_client:
        yield test_client


def test_default_database_lives_under_data() -> None:
    path = default_db_path()
    assert path.parent.name == "data"
    assert path.name == "galileo.db"


def test_bind_address_is_local_port_8090() -> None:
    assert BIND_HOST == "127.0.0.1"
    assert BIND_PORT == 8090


def test_post_then_get_returns_the_same_trace(client: TestClient, db_path: Path) -> None:
    payload = _chat_trace()
    created = client.post("/v1/traces", json=payload)
    assert created.status_code == 200
    assert created.json() == payload

    fetched = client.get("/v1/traces/req_01")
    assert fetched.status_code == 200
    assert fetched.json() == payload
    assert fetched.json()["spans"][-1]["output_masked"] == ""
    assert fetched.json()["spans"][-1]["metadata"]["token_count"] == "2"

    with sqlite3.connect(db_path) as conn:
        projects = conn.execute("SELECT name FROM projects ORDER BY name").fetchall()
        streams = conn.execute(
            "SELECT project, name FROM log_streams ORDER BY project, name"
        ).fetchall()
    assert projects == [(PROJECT_NAME,)]
    assert streams == [(PROJECT_NAME, LOG_STREAM)]


def test_clear_email_in_span_text_is_stored(client: TestClient, db_path: Path) -> None:
    payload = {
        "project": PROJECT_NAME,
        "log_stream": LOG_STREAM,
        "session_id": "sess_7f3a",
        "request_id": "req_clear_email",
        "name": "chat_agent",
        "spans": [
            {
                "name": "llm_completion",
                "type": "llm",
                "input_masked": f"Contacter {_CLEAR_EMAIL}",
                "output_masked": "ok",
            }
        ],
    }
    created = client.post("/v1/traces", json=payload)
    assert created.status_code == 200
    fetched = client.get("/v1/traces/req_clear_email")
    assert fetched.status_code == 200
    assert _CLEAR_EMAIL in fetched.text
    scores = client.get("/v1/traces/req_clear_email/scores").json()["scores"]
    assert any(row["metric_id"] == "pii" and row["passed"] is False for row in scores)


def test_forbidden_metadata_key_is_refused(client: TestClient, db_path: Path) -> None:
    payload = _chat_trace()
    payload["request_id"] = "req_meta_key"
    payload["spans"][0]["metadata"] = {"email": "ok"}
    refused = client.post("/v1/traces", json=payload)
    assert refused.status_code == 422
    assert "forbidden" in refused.text
    assert not db_path.exists()


def test_layer8_span_with_text_is_refused(client: TestClient, db_path: Path) -> None:
    payload = _chat_trace()
    payload["request_id"] = "req_layer8_text"
    payload["spans"][-1]["input_masked"] = "Question claire."
    payload["spans"][-1]["output_masked"] = "La liquidation suit la procédure citée."

    refused = client.post("/v1/traces", json=payload)
    assert refused.status_code == 422
    assert "layer 8" in refused.text
    assert "La liquidation suit la procédure citée." not in refused.text
    assert not db_path.exists()

    span = rehydration_span(token_count=2, status="ok")
    with pytest.raises(ValidationError, match="layer 8"):
        span.output_masked = "La liquidation suit la procédure citée."
    assert span.output_masked == ""


_RESTORED = "La réponse réhydratée part vers le collaborateur."


@pytest.mark.parametrize("mutate", ["status", "token_count", "name"])
def test_layer8_labels_cannot_carry_restored_text(
    client: TestClient, db_path: Path, mutate: str
) -> None:
    payload = _chat_trace()
    payload["request_id"] = f"req_layer8_{mutate}"
    layer8 = payload["spans"][-1]
    if mutate == "status":
        layer8["metadata"]["status"] = _RESTORED
    elif mutate == "token_count":
        layer8["metadata"]["token_count"] = _RESTORED
    else:
        layer8["name"] = _RESTORED
        layer8["metadata"]["layer"] = "8"

    refused = client.post("/v1/traces", json=payload)
    assert refused.status_code == 422
    assert "layer 8" in refused.text
    assert _RESTORED not in refused.text
    assert not db_path.exists()


@pytest.mark.parametrize(
    "status",
    [
        "reponse_envoyee_a_marie",
        "la_reponse_rehydratee_part_vers",
        "reponse_pour_marie_dupont",
        "ma64011519000001205000530121",
    ],
)
def test_layer8_status_is_a_closed_vocabulary(
    client: TestClient, db_path: Path, status: str
) -> None:
    payload = _chat_trace()
    payload["request_id"] = "req_layer8_status"
    payload["spans"][-1]["metadata"]["status"] = status

    refused = client.post("/v1/traces", json=payload)
    assert refused.status_code == 422
    assert status not in refused.text
    assert "layer 8" in refused.text
    assert not db_path.exists()


@pytest.mark.parametrize(
    "name,layer",
    [
        ("layer_8_rehydration", "8\n"),
        ("layer_8_rehydration", "8 "),
        ("layer_8_rehydration", "08"),
        ("layer_8_rehydration\n", "8"),
        ("layer_8_rehydration\n", "8\n"),
        ("layer_8_rehydration\n", "08"),
    ],
)
def test_disguised_layer8_marker_does_not_store_text(
    client: TestClient, db_path: Path, name: str, layer: str
) -> None:
    payload = _chat_trace()
    payload["request_id"] = "req_layer8_disguise"
    layer8 = payload["spans"][-1]
    layer8["name"] = name
    layer8["metadata"]["layer"] = layer
    layer8["output_masked"] = "La reponse rehydratee part vers le collaborateur."

    refused = client.post("/v1/traces", json=payload)
    assert refused.status_code == 422
    assert "La reponse rehydratee part vers le collaborateur." not in refused.text
    assert not db_path.exists()


def test_layer8_status_assignment_is_not_stored(db_path: Path) -> None:
    span = rehydration_span(token_count=2, status="ok")
    with pytest.raises(ValidationError, match="layer 8"):
        span.metadata = {
            "layer": "8",
            "token_count": "2",
            "status": _RESTORED,
        }
    assert span.metadata["status"] == "ok"

    object.__setattr__(
        span,
        "metadata",
        {"layer": "8", "token_count": "2", "status": _RESTORED},
    )
    trace = Trace.model_construct(
        project=PROJECT_NAME,
        log_stream=LOG_STREAM,
        session_id="sess_7f3a",
        request_id="req_layer8_bypass",
        name="chat_agent",
        spans=[span],
    )
    with pytest.raises(ValueError, match="layer 8") as caught:
        TraceStore(db_path).save(trace)
    assert _RESTORED not in str(caught.value)
    assert not db_path.exists()


def test_clear_email_can_be_assigned_and_stored(db_path: Path) -> None:
    trace = Trace.model_validate(_chat_trace())
    trace.spans[0].input_masked = f"Contacter {_CLEAR_EMAIL}"
    TraceStore(db_path).save(trace)
    stored = json.dumps(TraceStore(db_path).get(trace.request_id), ensure_ascii=False)
    assert _CLEAR_EMAIL in stored
