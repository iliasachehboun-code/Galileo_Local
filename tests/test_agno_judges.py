"""Gateway llm-judge metrics are stored from a fake model, or as an error."""

from dataclasses import dataclass, field
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

pytest.importorskip("agno")
from agno.models.base import Model
from agno.models.response import ModelResponse

from galileo_local.app import create_app
from galileo_local.catalog import METRICS, metrics_for_span
from galileo_local.console import FIXTURE_REQUEST_ID, fixture_gateway_trace
from galileo_local.judge_metrics import JUDGE_ERROR, prepare_for_storage
from galileo_local.judges import METRIC_JUDGE_INSTRUCTIONS, MetricScore, metric_prompt
from galileo_local.models import Span, SpanType, Trace
from galileo_local.pii_oracle import find_clear_pii

_FIXED_RATIONALE = "Le span masqué tient."
_CLEAR_EMAIL = "marie.dupont@cimr.ma"


@dataclass
class FixedModel(Model):
    """Agno model that never leaves the process."""

    id: str = "fixed-judge"
    temperature: float = 1.0
    supports_native_structured_outputs: bool = False
    mode: str = "score"
    leak: str = ""
    prompts: list[str] = field(default_factory=list)
    temperatures: list[float] = field(default_factory=list)
    instructions: list[str] = field(default_factory=list)

    def invoke(self, *args, **kwargs) -> ModelResponse:
        self.temperatures.append(self.temperature)
        messages = kwargs.get("messages") or []
        metric_id = "tone"
        for message in messages:
            content = getattr(message, "content", "")
            if not isinstance(content, str):
                continue
            if "Never reconstruct" in content:
                self.instructions.append(content)
            if content.startswith("Metric: "):
                self.prompts.append(content)
                metric_id = content.split()[1]
        if self.mode == "down":
            raise ConnectionError(self.leak or "unreachable")
        if self.mode == "foreign":
            metric_id = "visual_quality"
        rationale = self.leak if self.mode == "leak" else _FIXED_RATIONALE
        score = 1.0 if self.mode == "leak" else 0.25
        body = MetricScore(
            metric_id=metric_id,
            score=score,
            passed=True,
            rationale=rationale,
        )
        return ModelResponse(role="assistant", content=body.model_dump_json())

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


class BareModel:
    """No temperature, so the judge must not call it."""

    def __init__(self) -> None:
        self.called = False

    def invoke(self, *args, **kwargs):
        self.called = True
        raise AssertionError("model was called")


def _client(db_path: Path, model):
    return TestClient(create_app(db_path, judge_model=model))


def _rows(client: TestClient, request_id: str) -> list[dict]:
    response = client.get(f"/v1/traces/{request_id}/scores")
    assert response.status_code == 200
    body = response.json()
    assert body["request_id"] == request_id
    return body["scores"]


def _applicable(span: Span) -> list[str]:
    return [
        metric.id
        for metric in metrics_for_span(span.type.value)
        if metric.kind == "llm_judge"
    ]


def _tool_trace() -> Trace:
    return Trace(
        project="cimr-gpt",
        log_stream="gateway",
        session_id="sess_judge",
        request_id="req_judge",
        name="cimr_gateway",
        spans=[
            Span(
                name="web_search",
                type=SpanType.TOOL,
                input_masked="conditions de liquidation",
                output_masked="ok",
                metadata={"status": "ok"},
            )
        ],
    )


def test_fixture_persists_each_applicable_judge_score(tmp_path: Path) -> None:
    trace = Trace(
        project="galileo-local",
        log_stream="chat",
        session_id="sess_judge",
        request_id="req_judge_fixture",
        name="chat_agent",
        spans=[
            Span(
                name="workflow_prepare",
                type=SpanType.WORKFLOW,
                input_masked="chercher la procédure",
                output_masked="prêt",
                metadata={"step": "prepare"},
            ),
            Span(
                name="llm_completion",
                type=SpanType.LLM,
                input_masked="Dossier [CIMR_CIN_abcd1234].",
                output_masked="Le dossier est en cours.",
                metadata={},
            ),
        ],
    )
    payload = trace.model_dump(mode="json")
    model = FixedModel()
    disabled = {metric.id for metric in METRICS if not metric.cimr_stream}
    expected_prompts = [
        metric_prompt(metric, span)
        for span in trace.spans
        for metric in metrics_for_span(span.type.value)
        if metric.kind == "llm_judge"
    ]
    db_path = tmp_path / "galileo.db"
    with _client(db_path, model) as client:
        created = client.post("/v1/traces", json=payload)
        assert created.status_code == 200
        assert created.json() == payload
        stored = client.get("/v1/traces/req_judge_fixture").json()
        assert stored == payload

        scores = _rows(client, "req_judge_fixture")
        grouped: dict[int, dict[str, dict]] = {}
        for row in scores:
            grouped.setdefault(row["span_index"], {})[row["metric_id"]] = row

        assert set(grouped) == set(range(len(trace.spans)))
        present = {row["metric_id"] for row in scores}
        assert present.isdisjoint(disabled)
        for index, span in enumerate(trace.spans):
            rows = grouped[index]
            assert set(rows) == {"pii", *_applicable(span)}
            assert rows["pii"]["passed"] is True
            assert rows["pii"]["score"] == 1.0
            assert "status" not in rows["pii"]
            for metric_id in _applicable(span):
                row = rows[metric_id]
                assert set(row) == {"span_index", "metric_id", "score", "passed", "rationale"}
                assert row["score"] == 0.25
                assert row["passed"] is True
                assert row["rationale"] == _FIXED_RATIONALE
                assert find_clear_pii(row["rationale"]) == []

    assert model.temperature == 0
    assert model.temperatures == [0.0] * len(expected_prompts)
    assert model.prompts == expected_prompts
    assert model.instructions
    assert all(METRIC_JUDGE_INSTRUCTIONS in text for text in model.instructions)
    assert "sess_judge" not in "\n".join(model.prompts)


def test_llm_span_does_not_score_disabled_judges(tmp_path: Path) -> None:
    trace = Trace(
        project="cimr-gpt",
        log_stream="gateway",
        session_id="sess_judge",
        request_id="req_llm_judge",
        name="cimr_gateway",
        spans=[
            Span(
                name="llm_completion",
                type=SpanType.LLM,
                input_masked="Dossier [CIMR_CIN_abcd1234].",
                output_masked="Le dossier est en cours.",
                metadata={"layer": "6"},
            )
        ],
    )
    with _client(tmp_path / "galileo.db", FixedModel()) as client:
        assert client.post("/v1/traces", json=trace.model_dump(mode="json")).status_code == 200
        scores = _rows(client, "req_llm_judge")
    present = {row["metric_id"] for row in scores}
    expected = {metric.id for metric in metrics_for_span("llm") if metric.kind == "llm_judge"}
    assert present == {"pii", *expected}
    assert "visual_quality" not in present
    assert "visual_fidelity" not in present
    assert "interruption_detection" not in present
    assert "sql_adherence" not in present
    assert "sql_efficiency" not in present


def test_unreachable_model_stores_an_error_and_keeps_the_trace(tmp_path: Path) -> None:
    trace = _tool_trace()
    payload = trace.model_dump(mode="json")
    model = FixedModel(mode="down", leak=_CLEAR_EMAIL)
    db_path = tmp_path / "galileo.db"
    with _client(db_path, model) as client:
        created = client.post("/v1/traces", json=payload)
        assert created.status_code == 200
        assert created.json() == payload
        assert _CLEAR_EMAIL not in created.text
        scores = _rows(client, "req_judge")
        assert _CLEAR_EMAIL not in client.get("/v1/traces/req_judge/scores").text

    assert _CLEAR_EMAIL.encode() not in db_path.read_bytes()
    by_id = {row["metric_id"]: row for row in scores}
    assert set(by_id) == {"pii", "tool_error", "tool_selection_quality"}
    assert by_id["pii"]["passed"] is True
    assert by_id["tool_error"]["passed"] is True
    assert "status" not in by_id["pii"]
    failed = by_id["tool_selection_quality"]
    assert failed["status"] == "error"
    assert failed["passed"] is False
    assert failed["score"] == 0.0
    assert failed["rationale"] == JUDGE_ERROR
    assert find_clear_pii(failed["rationale"]) == []
    assert model.temperatures == [0.0]


def test_foreign_metric_id_is_not_stored(tmp_path: Path) -> None:
    model = FixedModel(mode="foreign")
    with _client(tmp_path / "galileo.db", model) as client:
        assert client.post("/v1/traces", json=_tool_trace().model_dump(mode="json")).status_code == 200
        scores = _rows(client, "req_judge")
    present = {row["metric_id"] for row in scores}
    assert "visual_quality" not in present
    assert "not_a_metric" not in present
    failed = next(row for row in scores if row["metric_id"] == "tool_selection_quality")
    assert failed["status"] == "error"
    assert failed["passed"] is False
    assert failed["score"] == 0.0


@pytest.mark.parametrize(
    ("kind", "value"),
    [
        ("email", _CLEAR_EMAIL),
        ("phone", "0612345678"),
        ("iban", "MA64011519000001205000530121"),
    ],
)
def test_clear_pii_in_the_rationale_is_rejected(tmp_path: Path, kind: str, value: str) -> None:
    assert find_clear_pii(value) == [kind]
    model = FixedModel(mode="leak", leak=f"Voir {value} maintenant.")
    db_path = tmp_path / "galileo.db"
    with _client(db_path, model) as client:
        created = client.post("/v1/traces", json=_tool_trace().model_dump(mode="json"))
        assert created.status_code == 200
        assert value not in created.text
        scores = _rows(client, "req_judge")
        assert value not in client.get("/v1/traces/req_judge/scores").text

    assert value.encode() not in db_path.read_bytes()
    failed = next(row for row in scores if row["metric_id"] == "tool_selection_quality")
    assert failed["status"] == "error"
    assert failed["passed"] is False
    assert failed["score"] == 0.0
    assert value not in failed["rationale"]
    assert kind in failed["rationale"]
    assert find_clear_pii(failed["rationale"]) == []
    kept = {row["metric_id"]: row for row in scores}
    assert kept["pii"]["passed"] is True
    assert kept["tool_error"]["passed"] is True


def test_prepare_for_storage_rejects_an_email_rationale() -> None:
    score, passed, rationale, status = prepare_for_storage(
        metric_id="tone",
        score=1.0,
        passed=True,
        rationale=f"Contacter {_CLEAR_EMAIL}",
        status="ok",
    )
    assert score == 0.0
    assert passed is False
    assert status == "error"
    assert _CLEAR_EMAIL not in rationale
    assert "email" in rationale
    assert find_clear_pii(rationale) == []


def test_model_without_temperature_is_not_called(tmp_path: Path) -> None:
    model = BareModel()
    with _client(tmp_path / "galileo.db", model) as client:
        assert client.post("/v1/traces", json=_tool_trace().model_dump(mode="json")).status_code == 200
        scores = _rows(client, "req_judge")
    assert model.called is False
    failed = next(row for row in scores if row["metric_id"] == "tool_selection_quality")
    assert failed["status"] == "error"
    assert failed["passed"] is False


def test_no_model_does_not_invent_a_judge_score(tmp_path: Path) -> None:
    payload = fixture_gateway_trace().model_dump(mode="json")
    with _client(tmp_path / "galileo.db", None) as client:
        assert client.post("/v1/traces", json=payload).status_code == 200
        scores = _rows(client, FIXTURE_REQUEST_ID)
    assert {row["metric_id"] for row in scores} == {"pii"}
    assert all(row["passed"] is True for row in scores)
    assert all("status" not in row for row in scores)
