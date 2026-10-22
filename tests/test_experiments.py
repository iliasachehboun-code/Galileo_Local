"""Experiment runs recompute stored traces and compare two score sets."""

import re
from pathlib import Path

from fastapi.testclient import TestClient

from galileo_local.app import create_app
from galileo_local.catalog import METRICS
from galileo_local.models import Span, SpanType, Trace
from galileo_local.pii_oracle import find_clear_pii

_QUESTION = "Question sur le dossier [CIMR_CIN_abcd1234]."
_ANSWER = "La liquidation suit [CIMR_PROCEDURE_aa11]."
_CLEAR_EMAIL = "marie.dupont@cimr.ma"
_CODE_IDS = {metric.id for metric in METRICS if metric.kind == "code" and metric.cimr_stream}
_JUDGE_IDS = {metric.id for metric in METRICS if metric.kind == "llm_judge" and metric.cimr_stream}
_DISABLED = {metric.id for metric in METRICS if not metric.cimr_stream}


def _client(db_path: Path, model=None):
    return TestClient(create_app(db_path, judge_model=model))


def _fixture(request_id: str) -> dict:
    trace = Trace(
        project="cimr-gpt",
        log_stream="gateway",
        session_id="sess_exp",
        request_id=request_id,
        name="cimr_gateway",
        spans=[
            Span(
                name="layer_3_sanitisation",
                type=SpanType.WORKFLOW,
                input_masked=_QUESTION,
                output_masked="masked",
                metadata={"layer": "3", "outcome": "ok"},
            ),
            Span(
                name="web_search",
                type=SpanType.TOOL,
                input_masked="conditions de liquidation",
                output_masked="ok",
                metadata={"status": "error"},
            ),
            Span(
                name="knowledge",
                type=SpanType.RETRIEVER,
                input_masked="liquidation",
                output_masked=_ANSWER,
                metadata={"labels": "1,0,1", "k": "3"},
            ),
        ],
    )
    return trace.model_dump(mode="json")


def _store_lot(client: TestClient) -> list[str]:
    ids = ["req_exp_a", "req_exp_b"]
    for request_id in ids:
        created = client.post("/v1/traces", json=_fixture(request_id))
        assert created.status_code == 200
        assert created.json() == _fixture(request_id)
    return ids


def _table_rows(html: str) -> list[tuple[str, str, str]]:
    body = html.split('id="run-comparison"', 1)[1]
    body = body.split("<tbody>", 1)[1].split("</tbody>", 1)[0]
    parsed: list[tuple[str, str, str]] = []
    for chunk in body.split("<tr>")[1:]:
        cells = re.findall(r"<t[dh](?: [^>]*)?>(.*?)</t[dh]>", chunk, flags=re.DOTALL)
        assert len(cells) == 3
        parsed.append((cells[0], cells[1], cells[2]))
    return parsed


def test_two_runs_on_the_same_fixture_have_identical_code_metrics(tmp_path: Path) -> None:
    db_path = tmp_path / "galileo.db"
    with _client(db_path) as client:
        ids = _store_lot(client)
        before = {
            request_id: client.get(f"/v1/traces/{request_id}").json()
            for request_id in ids
        }
        scores_before = {
            request_id: client.get(f"/v1/traces/{request_id}/scores").json()["scores"]
            for request_id in ids
        }
        created = client.post("/v1/experiments", json={"name": "run-a", "request_ids": ids})
        assert created.status_code == 200
        assert created.json()["name"] == "run-a"
        assert created.json()["request_ids"] == ids
        again = client.post(
            "/v1/experiments",
            json={"name": "run-b", "request_ids": list(reversed(ids)) + [ids[0]]},
        )
        assert again.status_code == 200
        assert again.json()["request_ids"] == list(reversed(ids))

        compared = client.get("/v1/experiments", params={"left": "run-a", "right": "run-b"})
        assert compared.status_code == 200
        body = compared.json()
        assert body["left"] == "run-a"
        assert body["right"] == "run-b"
        assert body["metrics"]
        seen = {row["metric_id"] for row in body["metrics"]}
        assert _CODE_IDS <= seen
        assert seen.isdisjoint(_JUDGE_IDS)
        assert seen.isdisjoint(_DISABLED)
        for row in body["metrics"]:
            assert row["metric_id"] in _CODE_IDS
            assert row["left"]["score"] == row["right"]["score"]
            assert row["left"]["passed"] == row["right"]["passed"]
            assert "status" not in row["left"]
            assert "status" not in row["right"]
            assert _QUESTION not in row["left"]["rationale"]
            assert _ANSWER not in row["right"]["rationale"]
            assert find_clear_pii(row["left"]["rationale"]) == []
            assert find_clear_pii(row["right"]["rationale"]) == []
            original = next(
                item
                for item in scores_before[row["request_id"]]
                if item["span_index"] == row["span_index"] and item["metric_id"] == row["metric_id"]
            )
            assert row["left"]["score"] == original["score"]
            assert row["left"]["passed"] == original["passed"]
        for request_id in ids:
            assert client.get(f"/v1/traces/{request_id}").json() == before[request_id]
            assert client.get(f"/v1/traces/{request_id}/scores").json()["scores"] == scores_before[request_id]


def test_unknown_request_does_not_create_a_partial_run(tmp_path: Path) -> None:
    db_path = tmp_path / "galileo.db"
    with _client(db_path) as client:
        ids = _store_lot(client)
        missing = client.post(
            "/v1/experiments",
            json={"name": "partial", "request_ids": [ids[0], "req_absent"]},
        )
        assert missing.status_code == 404
        assert missing.json()["detail"] == "trace not found"
        assert "req_absent" not in missing.text
        assert client.get("/v1/experiments/partial").status_code == 404
        created = client.post(
            "/v1/experiments",
            json={"name": "partial", "request_ids": [ids[0]]},
        )
        assert created.status_code == 200
        assert created.json()["name"] == "partial"
        assert created.json()["request_ids"] == [ids[0]]


def test_unknown_batch_does_not_create_a_database(tmp_path: Path) -> None:
    db_path = tmp_path / "galileo.db"
    with _client(db_path) as client:
        missing = client.post(
            "/v1/experiments",
            json={"name": "ghost", "request_ids": ["req_absent"]},
        )
        assert missing.status_code == 404
        assert "req_absent" not in missing.text
        email = client.post(
            "/v1/experiments",
            json={"name": "ghost", "request_ids": [_CLEAR_EMAIL]},
        )
        assert email.status_code == 422
        assert _CLEAR_EMAIL not in email.text
        named = client.get(f"/v1/experiments/{_CLEAR_EMAIL}")
        assert named.status_code == 404
        assert _CLEAR_EMAIL not in named.text
    assert not db_path.exists()


def test_a_missing_side_is_not_filled_with_the_other_score(tmp_path: Path) -> None:
    with _client(tmp_path / "galileo.db") as client:
        ids = _store_lot(client)
        assert client.post(
            "/v1/experiments",
            json={"name": "run-a", "request_ids": [ids[0]]},
        ).status_code == 200
        assert client.post(
            "/v1/experiments",
            json={"name": "run-b", "request_ids": ids},
        ).status_code == 200
        duplicate = client.post(
            "/v1/experiments",
            json={"name": "run-a", "request_ids": ids},
        )
        assert duplicate.status_code == 409
        body = client.get("/v1/experiments", params={"left": "run-a", "right": "run-b"}).json()
        extras = [row for row in body["metrics"] if row["request_id"] == ids[1]]
        assert extras
        for row in extras:
            assert row["left"] is None
            assert row["right"]["passed"] in (True, False)
            assert "score" in row["right"]


def test_console_link_opens_a_readable_comparison(tmp_path: Path) -> None:
    with _client(tmp_path / "galileo.db") as client:
        ids = _store_lot(client)
        assert client.post(
            "/v1/experiments",
            json={"name": "run-a", "request_ids": ids},
        ).status_code == 200
        assert client.post(
            "/v1/experiments",
            json={"name": "run-b", "request_ids": ids},
        ).status_code == 200
        home = client.get("/")
        assert home.status_code == 200
        assert 'href="/experiments"' in home.text
        page = client.get("/experiments")
        assert page.status_code == 200
        assert "expériences" in page.text
        assert "Les deux scores de chaque métrique." in page.text
        assert "pas calculé" not in page.text
        assert "<th>run-a</th>" in page.text
        assert "<th>run-b</th>" in page.text
        assert _QUESTION not in page.text
        assert _ANSWER not in page.text
        assert find_clear_pii(page.text) == []
        assert "<canvas" not in page.text
        assert "<script" not in page.text
        rows = _table_rows(page.text)
        assert rows
        labels = " ".join(metric for metric, _, _ in rows)
        assert "pii" in labels
        assert "tool_error" in labels
        assert "precision_at_k" in labels
        assert any("passed true" in left for _, left, _ in rows)
        assert any("passed false" in left for _, left, _ in rows)
        for _, left, right in rows:
            assert left == right
            assert "passed" in left


def test_experiments_page_does_not_create_a_database(tmp_path: Path) -> None:
    db_path = tmp_path / "galileo.db"
    with _client(db_path) as client:
        page = client.get("/experiments")
        assert page.status_code == 200
        assert "Deux runs sont nécessaires" in page.text
        assert 'id="run-comparison"' not in page.text
        missing = client.get("/v1/experiments", params={"left": "run-a", "right": "run-b"})
        assert missing.status_code == 404
    assert not db_path.exists()


class _ColdModel:
    """No temperature, so a judge call cannot leave the process or pass."""


def test_a_failed_judge_is_not_stored_as_a_pass(tmp_path: Path) -> None:
    with _client(tmp_path / "galileo.db", model=_ColdModel()) as client:
        ids = _store_lot(client)
        created = client.post("/v1/experiments", json={"name": "run-a", "request_ids": ids})
        assert created.status_code == 200
        client.post("/v1/experiments", json={"name": "run-b", "request_ids": ids})
        body = client.get("/v1/experiments", params={"left": "run-a", "right": "run-b"}).json()
        judges = [row for row in body["metrics"] if row["metric_id"] in _JUDGE_IDS]
        codes = [row for row in body["metrics"] if row["metric_id"] in _CODE_IDS]
        assert judges
        assert codes
        for row in judges:
            assert row["left"]["status"] == "error"
            assert row["right"]["status"] == "error"
            assert row["left"]["passed"] is False
            assert row["right"]["passed"] is False
            assert row["left"]["score"] == 0.0
            assert row["right"]["score"] == 0.0
            assert row["left"]["score"] == row["right"]["score"]
        for row in codes:
            assert row["left"]["score"] == row["right"]["score"]
            assert row["left"]["passed"] == row["right"]["passed"]
            assert "status" not in row["left"]
