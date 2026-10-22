"""SQLite store for masked traces.

The file lives at ``data/galileo.db``. A project and a log stream are inserted
when the first trace names them. Clear personal data never reaches this layer:
callers pass a ``Trace``, and a ``Trace`` cannot be built when the oracle finds one.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from galileo_local.code_metrics import PersistedCodeScore, code_scores
from galileo_local.experiments import DuplicateRun, MissingTrace, pair_scores, public_score
from galileo_local.judge_metrics import PersistedJudgeScore, judge_scores, prepare_for_storage
from galileo_local.models import Trace, public_trace_view
from galileo_local.pii_oracle import find_clear_pii

_SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    name TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS log_streams (
    project TEXT NOT NULL,
    name TEXT NOT NULL,
    PRIMARY KEY (project, name),
    FOREIGN KEY (project) REFERENCES projects (name)
);

CREATE TABLE IF NOT EXISTS traces (
    request_id TEXT PRIMARY KEY,
    project TEXT NOT NULL,
    log_stream TEXT NOT NULL,
    body TEXT NOT NULL,
    created_at TEXT,
    FOREIGN KEY (project, log_stream) REFERENCES log_streams (project, name)
);

CREATE TABLE IF NOT EXISTS metric_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL,
    span_index INTEGER NOT NULL,
    metric_id TEXT NOT NULL,
    score REAL NOT NULL CHECK (score >= 0 AND score <= 1),
    passed INTEGER NOT NULL CHECK (passed IN (0, 1)),
    rationale TEXT NOT NULL CHECK (length(rationale) > 0),
    status TEXT NOT NULL DEFAULT 'ok' CHECK (status IN ('ok', 'error')),
    UNIQUE (request_id, span_index, metric_id),
    FOREIGN KEY (request_id) REFERENCES traces (request_id)
);

CREATE TABLE IF NOT EXISTS experiment_runs (
    name TEXT PRIMARY KEY,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS experiment_members (
    run_name TEXT NOT NULL,
    request_id TEXT NOT NULL,
    position INTEGER NOT NULL,
    PRIMARY KEY (run_name, request_id),
    FOREIGN KEY (run_name) REFERENCES experiment_runs (name),
    FOREIGN KEY (request_id) REFERENCES traces (request_id)
);

CREATE TABLE IF NOT EXISTS experiment_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_name TEXT NOT NULL,
    request_id TEXT NOT NULL,
    span_index INTEGER NOT NULL,
    metric_id TEXT NOT NULL,
    score REAL NOT NULL CHECK (score >= 0 AND score <= 1),
    passed INTEGER NOT NULL CHECK (passed IN (0, 1)),
    rationale TEXT NOT NULL CHECK (length(rationale) > 0),
    status TEXT NOT NULL DEFAULT 'ok' CHECK (status IN ('ok', 'error')),
    UNIQUE (run_name, request_id, span_index, metric_id),
    FOREIGN KEY (run_name) REFERENCES experiment_runs (name),
    FOREIGN KEY (request_id) REFERENCES traces (request_id)
);
"""


def _recorded_at() -> str:
    """Local clock time, second resolution, stored beside the trace body."""
    return datetime.now().astimezone().replace(microsecond=0).isoformat(sep=" ", timespec="seconds")


def _accepted(trace: Trace) -> Trace:
    """Re-run the Trace model. The refusal text cites kinds, not the value."""
    try:
        return Trace.model_validate(trace.model_dump(mode="python"))
    except ValidationError as exc:
        messages: list[str] = []
        for err in exc.errors():
            msg = str(err.get("msg", ""))
            if msg and msg not in messages:
                messages.append(msg)
        raise ValueError("; ".join(messages) or "clear personal data") from None


def default_db_path() -> Path:
    """Database path relative to the galileo-local project root."""
    return Path(__file__).resolve().parent.parent / "data" / "galileo.db"


class TraceStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def save(self, trace: Trace, *, model: Any | None = None) -> None:
        """Persist ``trace``. Creates the project and the log stream if needed.

        The model is validated again here. A later assignment must not reach SQLite
        when the oracle would refuse it. Nothing is written if that check fails.
        When ``model`` is set, each applicable llm-judge metric is scored at
        temperature 0. A judge failure still stores the trace, with an error row
        and no passing score. No model means no judge row is invented.
        """
        checked = _accepted(trace)
        scored: list[PersistedCodeScore | PersistedJudgeScore] = list(code_scores(checked))
        if model is not None:
            scored.extend(judge_scores(checked, model))
        self._write(checked, scored)

    def write_scores(self, trace: Trace, model: Any, *, only_substantive: bool = False) -> None:
        """Replace scores for a trace already stored. The trace body stays."""
        checked = _accepted(trace)
        scored: list[PersistedCodeScore | PersistedJudgeScore] = list(code_scores(checked))
        if model is not None:
            scored.extend(judge_scores(checked, model, only_substantive=only_substantive))
        with self._connect() as conn:
            self._replace_scores(conn, checked.request_id, scored)

    def _write(self, checked: Trace, scored: list[PersistedCodeScore | PersistedJudgeScore]) -> None:
        body = json.dumps(public_trace_view(checked), ensure_ascii=False)
        with self._connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO projects (name) VALUES (?)",
                (checked.project,),
            )
            conn.execute(
                "INSERT OR IGNORE INTO log_streams (project, name) VALUES (?, ?)",
                (checked.project, checked.log_stream),
            )
            conn.execute(
                """
                INSERT INTO traces (request_id, project, log_stream, body, created_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(request_id) DO UPDATE SET
                    project = excluded.project,
                    log_stream = excluded.log_stream,
                    body = excluded.body,
                    created_at = COALESCE(traces.created_at, excluded.created_at)
                """,
                (checked.request_id, checked.project, checked.log_stream, body, _recorded_at()),
            )
            self._replace_scores(conn, checked.request_id, scored)

    def get(self, request_id: str) -> dict[str, Any] | None:
        """Return the stored JSON for ``request_id``, or None when it is absent.

        A missing database file stays missing: a refused write must not create it.
        """
        if not self.path.is_file():
            return None
        with self._connect() as conn:
            row = conn.execute(
                "SELECT body FROM traces WHERE request_id = ?",
                (request_id,),
            ).fetchone()
        if row is None:
            return None
        return json.loads(row[0])

    def list_traces(self, *, project: str, log_stream: str) -> list[dict[str, Any]]:
        """Traces of one stream, oldest first.

        Each item is ``request_id``, ``created_at``, and the stored JSON.
        A missing database file stays missing.
        """
        if not self.path.is_file():
            return []
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT request_id, created_at, body
                FROM traces
                WHERE project = ? AND log_stream = ?
                ORDER BY created_at IS NULL, created_at, request_id
                """,
                (project, log_stream),
            ).fetchall()
        listed: list[dict[str, Any]] = []
        for request_id, created_at, body in rows:
            listed.append(
                {
                    "request_id": request_id,
                    "created_at": created_at,
                    "trace": json.loads(body),
                }
            )
        return listed

    def scores_for(self, request_id: str) -> list[dict[str, Any]] | None:
        """Scores stored for ``request_id``.

        ``None`` when the trace is absent. An empty list means the trace was
        stored and no score applied. A missing database file stays missing.
        A judge failure adds ``status: "error"`` and is not a pass.
        """
        if not self.path.is_file():
            return None
        with self._connect() as conn:
            found = conn.execute(
                "SELECT 1 FROM traces WHERE request_id = ?",
                (request_id,),
            ).fetchone()
            if found is None:
                return None
            rows = conn.execute(
                """
                SELECT span_index, metric_id, score, passed, rationale, status
                FROM metric_scores
                WHERE request_id = ?
                ORDER BY span_index, id
                """,
                (request_id,),
            ).fetchall()
        listed: list[dict[str, Any]] = []
        for span_index, metric_id, score, passed, rationale, status in rows:
            item = {
                "span_index": span_index,
                "metric_id": metric_id,
                "score": score,
                "passed": bool(passed),
                "rationale": rationale,
            }
            if status == "error":
                item["status"] = "error"
            listed.append(item)
        return listed

    def create_experiment(
        self,
        name: str,
        request_ids: list[str],
        *,
        model: Any | None = None,
    ) -> dict[str, Any]:
        """Recompute scores for stored traces and keep them on a named run.

        Every request id is checked before a row is inserted. An unknown id
        raises ``MissingTrace`` and leaves no run behind. No model means no
        judge row is invented. A judge failure is an error score, not a pass.
        The trace body is not rewritten.
        """
        kinds = find_clear_pii(name)
        if kinds:
            raise ValueError("clear personal data in run (" + ", ".join(kinds) + ")")
        ordered = list(dict.fromkeys(request_ids))
        if not ordered:
            raise ValueError("request_id is empty")
        for request_id in ordered:
            kinds = find_clear_pii(request_id)
            if kinds:
                raise ValueError("clear personal data in run (" + ", ".join(kinds) + ")")
        if not self.path.is_file():
            raise MissingTrace()
        with self._connect() as conn:
            placeholders = ",".join("?" for _ in ordered)
            found = {
                row[0]
                for row in conn.execute(
                    f"SELECT request_id FROM traces WHERE request_id IN ({placeholders})",
                    ordered,
                )
            }
            if any(request_id not in found for request_id in ordered):
                raise MissingTrace()
            taken = conn.execute(
                "SELECT 1 FROM experiment_runs WHERE name = ?",
                (name,),
            ).fetchone()
            if taken is not None:
                raise DuplicateRun()
            bodies = {
                request_id: body
                for request_id, body in conn.execute(
                    f"SELECT request_id, body FROM traces WHERE request_id IN ({placeholders})",
                    ordered,
                )
            }
            scored: list[tuple[str, list[PersistedCodeScore | PersistedJudgeScore]]] = []
            for request_id in ordered:
                trace = Trace.model_validate(json.loads(bodies[request_id]))
                rows: list[PersistedCodeScore | PersistedJudgeScore] = list(code_scores(trace))
                if model is not None:
                    rows.extend(judge_scores(trace, model))
                scored.append((request_id, rows))
            conn.execute(
                "INSERT INTO experiment_runs (name, created_at) VALUES (?, ?)",
                (name, _recorded_at()),
            )
            conn.executemany(
                """
                INSERT INTO experiment_members (run_name, request_id, position)
                VALUES (?, ?, ?)
                """,
                [(name, request_id, position) for position, request_id in enumerate(ordered)],
            )
            for request_id, rows in scored:
                if not rows:
                    continue
                conn.executemany(
                    """
                    INSERT INTO experiment_scores (
                        run_name, request_id, span_index, metric_id,
                        score, passed, rationale, status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [_experiment_score_tuple(name, request_id, row) for row in rows],
                )
            stored = self._read_run(conn, name)
        if stored is None:
            raise RuntimeError("run was not stored")
        return stored

    def get_experiment(self, name: str) -> dict[str, Any] | None:
        """One named run, or None when it is absent.

        A missing database file stays missing.
        """
        if find_clear_pii(name) or not self.path.is_file():
            return None
        with self._connect() as conn:
            return self._read_run(conn, name)

    def compare_experiments(self, left: str, right: str) -> dict[str, Any] | None:
        """Scores of two runs, paired by metric. None when either run is absent.

        A missing database file stays missing.
        """
        if find_clear_pii(left) or find_clear_pii(right) or not self.path.is_file():
            return None
        with self._connect() as conn:
            left_scores = self._read_score_list(conn, left)
            right_scores = self._read_score_list(conn, right)
        if left_scores is None or right_scores is None:
            return None
        return pair_scores(left, right, left_scores, right_scores)

    def experiment_names(self) -> list[str]:
        """Run names, oldest first. A missing database file stays missing."""
        if not self.path.is_file():
            return []
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT name FROM experiment_runs ORDER BY created_at, rowid"
            ).fetchall()
        return [row[0] for row in rows]

    def _read_run(self, conn: sqlite3.Connection, name: str) -> dict[str, Any] | None:
        found = conn.execute(
            "SELECT name FROM experiment_runs WHERE name = ?",
            (name,),
        ).fetchone()
        if found is None:
            return None
        members = conn.execute(
            """
            SELECT request_id FROM experiment_members
            WHERE run_name = ?
            ORDER BY position, request_id
            """,
            (name,),
        ).fetchall()
        scores = self._read_score_list(conn, name)
        return {
            "name": found[0],
            "request_ids": [row[0] for row in members],
            "scores": scores or [],
        }

    def _read_score_list(
        self,
        conn: sqlite3.Connection,
        name: str,
    ) -> list[dict[str, Any]] | None:
        found = conn.execute(
            "SELECT 1 FROM experiment_runs WHERE name = ?",
            (name,),
        ).fetchone()
        if found is None:
            return None
        rows = conn.execute(
            """
            SELECT s.request_id, s.span_index, s.metric_id, s.score,
                   s.passed, s.rationale, s.status
            FROM experiment_scores AS s
            JOIN experiment_members AS m
              ON m.run_name = s.run_name AND m.request_id = s.request_id
            WHERE s.run_name = ?
            ORDER BY m.position, s.span_index, s.id
            """,
            (name,),
        ).fetchall()
        return [public_score(*row) for row in rows]

    def _replace_scores(
        self,
        conn: sqlite3.Connection,
        request_id: str,
        scored: list[PersistedCodeScore | PersistedJudgeScore],
    ) -> None:
        conn.execute("DELETE FROM metric_scores WHERE request_id = ?", (request_id,))
        conn.executemany(
            """
            INSERT INTO metric_scores
                (request_id, span_index, metric_id, score, passed, rationale, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [_score_tuple(request_id, row) for row in scored],
        )

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(_SCHEMA)
        columns = {row[1] for row in conn.execute("PRAGMA table_info(traces)")}
        if "created_at" not in columns:
            conn.execute("ALTER TABLE traces ADD COLUMN created_at TEXT")
        score_columns = {row[1] for row in conn.execute("PRAGMA table_info(metric_scores)")}
        if score_columns and "status" not in score_columns:
            conn.execute(
                "ALTER TABLE metric_scores ADD COLUMN status TEXT NOT NULL DEFAULT 'ok'"
            )
        return conn


def _experiment_score_tuple(
    run_name: str,
    request_id: str,
    row: PersistedCodeScore | PersistedJudgeScore,
) -> tuple[str, str, int, str, float, int, str, str]:
    _, span_index, metric_id, score, passed, rationale, status = _score_tuple(request_id, row)
    return (run_name, request_id, span_index, metric_id, score, passed, rationale, status)


def _score_tuple(
    request_id: str,
    row: PersistedCodeScore | PersistedJudgeScore,
) -> tuple[str, int, str, float, int, str, str]:
    """Read the oracle on the rationale, then return the inserted values."""
    score, passed, rationale, status = prepare_for_storage(
        metric_id=row.metric_id,
        score=row.score,
        passed=row.passed,
        rationale=row.rationale,
        status=getattr(row, "status", "ok"),
    )
    return (request_id, row.span_index, row.metric_id, score, int(passed), rationale, status)
