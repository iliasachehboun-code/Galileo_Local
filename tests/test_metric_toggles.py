"""Users can enable and disable metrics on the log stream."""

from pathlib import Path

from fastapi.testclient import TestClient

from galileo_local.app import create_app
from galileo_local.catalog import default_enabled_ids
from galileo_local.code_metrics import code_scores
from galileo_local.console import fixture_gateway_trace
from galileo_local.settings import LOG_STREAM, PROJECT_NAME
from galileo_local.store import TraceStore


def _client(db_path: Path):
    return TestClient(create_app(db_path))


def test_metrics_page_lists_toggles_and_saves(tmp_path: Path) -> None:
    db_path = tmp_path / "galileo.db"
    with _client(db_path) as client:
        page = client.get("/metrics")
        assert page.status_code == 200
        assert "Configure Metrics" in page.text
        assert 'name="metric" value="pii"' in page.text
        assert "checked" in page.text
        assert "Save metrics" in page.text

        saved = client.post(
            "/metrics",
            data={"metric": ["pii", "completeness"]},
            follow_redirects=False,
        )
        assert saved.status_code == 303
        assert saved.headers["location"] == "/metrics?saved=1"

        store = TraceStore(db_path)
        enabled = store.enabled_metric_ids(PROJECT_NAME, LOG_STREAM)
        assert enabled == frozenset({"pii", "completeness"})

        again = client.get("/metrics?saved=1")
        assert again.status_code == 200
        assert "Preferences saved" in again.text
        assert 'value="pii" checked' in again.text.replace("\n", " ")
        assert 'value="toxicity"' in again.text
        # toxicity unchecked: no checked immediately after that value attribute
        assert 'value="toxicity" checked' not in again.text.replace("\n", " ")


def test_disabled_metric_is_not_scored_on_new_traces(tmp_path: Path) -> None:
    db_path = tmp_path / "galileo.db"
    store = TraceStore(db_path)
    store.set_enabled_metric_ids({"completeness"})
    assert "pii" not in store.enabled_metric_ids()

    trace = fixture_gateway_trace()
    enabled = store.enabled_metric_ids(trace.project, trace.log_stream)
    assert "pii" not in enabled
    scored = code_scores(trace, enabled=enabled)
    assert all(row.metric_id != "pii" for row in scored)
    assert any(row.metric_id == "pii" for row in code_scores(trace))

    store.save(trace)
    scores = store.scores_for(trace.request_id) or []
    assert not any(row["metric_id"] == "pii" for row in scores)


def test_default_enabled_matches_catalog() -> None:
    assert "pii" in default_enabled_ids()
    assert "visual_quality" not in default_enabled_ids()
    assert len(default_enabled_ids()) == 24
