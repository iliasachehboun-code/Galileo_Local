"""Galileo Log stream console: table, aggregations, and trace detail."""

from __future__ import annotations

from html import escape
from typing import Any, Mapping, Sequence
from urllib.parse import quote

from galileo_local.catalog import METRICS, metrics_for_cimr_stream
from galileo_local.models import Span, SpanType, Trace, rehydration_span
from galileo_local.pii_oracle import find_clear_pii
from galileo_local.settings import LOG_STREAM, PROJECT_NAME
from galileo_local.store import TraceStore
from galileo_local.ui_shell import (
    breadcrumb_logs,
    breadcrumb_plain,
    render_shell,
)

_METRIC_NAMES = {metric.id: metric.name for metric in METRICS}
_TABLE_METRICS = (
    "completeness",
    "correctness",
    "instruction_adherence",
    "reasoning_coherence",
    "pii",
)
_FAMILY_LABELS = {
    "agentic": "Agentic",
    "expression": "Expression & readability",
    "response_quality": "Output quality",
    "rag_retrieval": "RAG retrieval",
    "rag_generation": "RAG generation",
    "safety": "Safety & compliance",
    "multimodal": "Multimodal",
    "text_to_sql": "Text-to-SQL",
}
_PANELS = (
    ("Output Quality", ("correctness", "instruction_adherence", "reasoning_coherence")),
    ("RAG Quality", ("completeness", "context_adherence")),
    ("Safety Metrics", ("pii", "sexism", "toxicity", "tone", "prompt_injection", "unsafe_output")),
    (
        "Agentic",
        (
            "action_advancement",
            "action_completion",
            "agent_efficiency",
            "agent_flow",
            "conversation_quality",
            "tool_selection_quality",
            "tool_error",
            "user_intent_change",
        ),
    ),
)
_PAGE_SIZE = 25

GATEWAY_PROJECT = PROJECT_NAME
GATEWAY_STREAM = LOG_STREAM
FIXTURE_REQUEST_ID = "req_console_fixture"
REHYDRATION_LABEL = "texte réhydraté non stocké"
_QUESTION = "Explique en une phrase ce qu'est une pension de retraite."
_ANSWER = "Une pension de retraite est un revenu versé après la fin de l'activité professionnelle."


def fixture_gateway_trace() -> Trace:
    """Clear-text chat trace for the console tour."""
    return Trace(
        project=GATEWAY_PROJECT,
        log_stream=GATEWAY_STREAM,
        session_id="sess_console",
        request_id=FIXTURE_REQUEST_ID,
        name="chat_agent",
        spans=[
            Span(
                name="agent",
                type=SpanType.AGENT,
                input_masked=_QUESTION,
                output_masked=_ANSWER,
                metadata={"role": "assistant"},
            ),
            Span(
                name="llm",
                type=SpanType.LLM,
                input_masked=_QUESTION,
                output_masked=_ANSWER,
                metadata={"model": "gpt-4o-mini"},
            ),
            Span(
                name="workflow_prepare",
                type=SpanType.WORKFLOW,
                input_masked=_QUESTION,
                output_masked="ready",
                metadata={"step": "prepare"},
            ),
            rehydration_span(token_count=2, status="ok"),
        ],
    )


def order_scores(scores: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    def rank(item: Mapping[str, Any]) -> int:
        if str(item.get("metric_id", "")) == "pii" and _score_number(item.get("score")) == 0:
            return 0
        return 1

    return sorted(scores, key=rank)


def render_score_list(scores: Sequence[Mapping[str, Any]]) -> str:
    items: list[str] = []
    for score in order_scores(scores):
        metric = escape(str(score.get("metric_id", "")))
        number = escape(_format_unit_score(score.get("score")))
        passed = "true" if score.get("passed") is True else "false"
        items.append(f"<li>{metric} {number} passed {passed}</li>")
    return '<ol class="score-list">' + "".join(items) + "</ol>"


def render_console(
    store: TraceStore,
    *,
    selected: str | None = None,
    span: int | None = None,
    level: str = "traces",
    q: str = "",
    page: int = 1,
) -> str:
    """Compat entry: selected opens detail; otherwise Log stream table."""
    if selected:
        return render_trace_detail(store, selected, span=span)
    return render_logs(store, level=level, q=q, page=page)


def render_logs(
    store: TraceStore,
    *,
    level: str = "traces",
    q: str = "",
    page: int = 1,
) -> str:
    level = level if level in {"sessions", "traces", "spans"} else "traces"
    if q and find_clear_pii(q):
        q = ""
    stored = _load_stream(store)
    score_map = {
        item["trace"].request_id: _scores(store, item["trace"].request_id) for item in stored
    }
    counts = _counts(stored)
    table_metrics = _table_metric_ids(store)
    rows = _rows_for_level(stored, score_map, level, table_metrics)
    if q.strip():
        needle = q.strip().lower()
        rows = [row for row in rows if needle in _search_blob(row)]
    total = len(rows)
    page = max(1, page)
    start = (page - 1) * _PAGE_SIZE
    page_rows = rows[start : start + _PAGE_SIZE]
    pages = max(1, (total + _PAGE_SIZE - 1) // _PAGE_SIZE)

    main = (
        _logs_tabs()
        + _toolbar(level, counts, q)
        + _table(page_rows, level, table_metrics)
        + _pager(level, q, page, pages)
    )
    return render_shell(
        title=f"Galileo · Logs: {LOG_STREAM}",
        active="logs",
        breadcrumb=breadcrumb_logs(),
        main=main,
    )


def render_trace_detail(
    store: TraceStore,
    request_id: str,
    *,
    span: int | None = None,
) -> str:
    if find_clear_pii(request_id):
        return render_logs(store)
    stored = _load_stream(store)
    for item in stored:
        trace: Trace = item["trace"]
        if trace.request_id == request_id:
            scores = _scores(store, request_id)
            if span is not None and span < 0:
                span = None
            body = (
                '<p class="back"><a href="/logs">← Logs</a></p>'
                + _session(trace, scores, span, store.enabled_metric_ids())
            )
            return render_shell(
                title=f"Galileo · {trace.name}",
                active="logs",
                breadcrumb=breadcrumb_logs(),
                main=body,
            )
    body = (
        '<p class="back"><a href="/logs">← Logs</a></p>'
        f'<div id="trace-detail"><p>Trace not found: {escape(request_id)}</p></div>'
    )
    return render_shell(
        title="Galileo · Trace",
        active="logs",
        breadcrumb=breadcrumb_logs(),
        main=body,
    )


def render_session_detail(store: TraceStore, session_id: str) -> str:
    if find_clear_pii(session_id):
        return render_logs(store, level="sessions")
    stored = [
        item
        for item in _load_stream(store)
        if item["trace"].session_id == session_id
    ]
    if not stored:
        body = (
            '<p class="back"><a href="/logs?level=sessions">← Logs</a></p>'
            f"<p>Session not found.</p>"
        )
        return render_shell(
            title="Galileo · Session",
            active="logs",
            breadcrumb=breadcrumb_logs(),
            main=body,
        )
    score_map = {
        item["trace"].request_id: _scores(store, item["trace"].request_id) for item in stored
    }
    table_metrics = _table_metric_ids(store)
    rows = _rows_for_level(stored, score_map, "traces", table_metrics)
    body = (
        '<p class="back"><a href="/logs?level=sessions">← Logs</a></p>'
        f"<h1>Session {escape(session_id)}</h1>"
        + _table(rows, "traces", table_metrics)
    )
    return render_shell(
        title="Galileo · Session",
        active="logs",
        breadcrumb=breadcrumb_logs(),
        main=body,
    )


def render_overview(store: TraceStore) -> str:
    stored = _load_stream(store)
    counts = _counts(stored)
    last = "—"
    if stored:
        last = str(stored[-1].get("created_at") or "—")
    body = (
        "<h1>Overview</h1>"
        '<div class="counters">'
        f'<div class="counter"><div class="n">{counts["sessions"]}</div>'
        '<div class="l">Sessions</div></div>'
        f'<div class="counter"><div class="n">{counts["traces"]}</div>'
        '<div class="l">Traces</div></div>'
        f'<div class="counter"><div class="n">{counts["spans"]}</div>'
        '<div class="l">Spans</div></div>'
        "</div>"
        f'<p style="margin-top:1.25rem;color:var(--gal-muted)">Last event: {escape(last)}</p>'
        '<p><a class="btn-primary" href="/logs">Open Logs</a></p>'
    )
    return render_shell(
        title="Galileo · Overview",
        active="overview",
        breadcrumb=breadcrumb_plain("Overview"),
        main=body,
    )


def render_trends(store: TraceStore) -> str:
    """System Metrics chrome matching Galileo Trends (counts from local stream)."""
    counts = _counts(_load_stream(store))
    cards = (
        ("API Failures", 0, "COUNT"),
        ("Traces Count", counts["traces"], "COUNT"),
        ("Sessions", counts["sessions"], "COUNT"),
        ("Spans", counts["spans"], "COUNT"),
        ("Input Tokens", "—", "SUM"),
        ("Agent Cost", "—", "SUM"),
    )
    grid = "".join(
        '<div class="trend-card">'
        f'<div class="title">{escape(title)}</div>'
        f'<div class="value">{escape(str(value))}'
        f'<span class="pill">{escape(agg)}</span></div>'
        f'<div class="spark" aria-hidden="true">{_sparkline(i)}</div>'
        "</div>"
        for i, (title, value, agg) in enumerate(cards)
    )
    main = (
        _logs_tabs(active="trends")
        + '<div class="toolbar">'
        '<a class="chip" href="/logs/trends">Default View</a>'
        '<span class="chip">Last month</span>'
        '<span class="chip">Group by</span>'
        '<span class="chip">Filters</span>'
        '<div class="search-wrap">'
        '<button type="button" class="btn-ghost is-disabled" disabled>Manual</button>'
        "</div></div>"
        '<div class="subtabs">'
        '<span class="on">System Metrics</span>'
        "<span>RAG Quality</span><span>Custom Metrics</span>"
        "<span>Safety Metrics</span><span>Security</span>"
        "<span>Output Quality</span></div>"
        f'<div class="trends-grid">{grid}</div>'
    )
    return render_shell(
        title=f"Galileo · Trends: {LOG_STREAM}",
        active="trends",
        breadcrumb=breadcrumb_logs(),
        main=main,
    )


def render_metrics_page(
    store: TraceStore,
    *,
    saved: bool = False,
) -> str:
    enabled = store.enabled_metric_ids()
    by_family: dict[str, list] = {}
    for metric in metrics_for_cimr_stream():
        by_family.setdefault(metric.family, []).append(metric)

    sections: list[str] = []
    for family, metrics in by_family.items():
        rows = "".join(
            '<label class="metric-toggle">'
            f'<input type="checkbox" name="metric" value="{escape(metric.id)}" '
            f'{"checked" if metric.id in enabled else ""}>'
            '<span class="metric-toggle-ui" aria-hidden="true"></span>'
            '<span class="metric-toggle-body">'
            f'<strong>{escape(metric.name)}</strong>'
            f'<span class="na">{escape(metric.id)} · {escape(metric.kind)}</span>'
            "</span></label>"
            for metric in metrics
        )
        label = escape(_FAMILY_LABELS.get(family, family.replace("_", " ").title()))
        sections.append(
            f'<section class="metric-family"><h2>{label}</h2>'
            f'<div class="metric-toggles">{rows}</div></section>'
        )

    n_on = len(enabled)
    n_all = len(list(metrics_for_cimr_stream()))
    banner = (
        '<p class="metrics-saved">Preferences saved. New traces will use this set.</p>'
        if saved
        else ""
    )
    body = (
        "<h1>Configure Metrics</h1>"
        f"<p>Enable or disable metrics on log stream "
        f"<strong>{escape(LOG_STREAM)}</strong>. "
        f"Currently <strong>{n_on}</strong> / {n_all} active. "
        "Changes apply to newly scored traces.</p>"
        f"{banner}"
        '<form class="metrics-form" method="post" action="/metrics">'
        '<div class="metrics-actions">'
        '<button type="button" class="btn-ghost" onclick="'
        "document.querySelectorAll('.metrics-form input[type=checkbox]')"
        ".forEach(c=>c.checked=true)\">Select all</button>"
        '<button type="button" class="btn-ghost" onclick="'
        "document.querySelectorAll('.metrics-form input[type=checkbox]')"
        ".forEach(c=>c.checked=false)\">Disable all</button>"
        '<button type="submit" class="btn-primary">Save metrics</button>'
        "</div>"
        + "".join(sections)
        + '<div class="metrics-actions">'
        '<button type="submit" class="btn-primary">Save metrics</button>'
        "</div></form>"
    )
    return render_shell(
        title="Galileo · Metrics",
        active="metrics",
        breadcrumb=breadcrumb_plain("Configure Metrics"),
        main=body,
        header_action='<a class="btn-primary" href="/logs">Back to Logs</a>',
    )


def render_experiments(
    store: TraceStore,
    *,
    left: str | None = None,
    right: str | None = None,
) -> str:
    if _query_is_blocked(left) or _query_is_blocked(right):
        inner = _experiments_message("Run not found.")
    else:
        chosen = _chosen_runs(store, left, right)
        if chosen is None:
            inner = _experiments_message("Deux runs sont nécessaires pour comparer les scores.")
        else:
            left_name, right_name = chosen
            compared = store.compare_experiments(left_name, right_name)
            if compared is None:
                inner = _experiments_message("Run not found.")
            else:
                inner = _experiments_message(_comparison_table(compared), lead=True)
    return render_shell(
        title="Galileo · Experiments",
        active="experiments",
        breadcrumb=breadcrumb_plain("Experiments"),
        main=inner,
        header_action='<a class="btn-primary" href="/logs">Open Logs</a>',
    )


def _query_is_blocked(value: str | None) -> bool:
    return bool(value) and bool(find_clear_pii(value))


def _chosen_runs(
    store: TraceStore,
    left: str | None,
    right: str | None,
) -> tuple[str, str] | None:
    left_name = " ".join(left.split()) if left else ""
    right_name = " ".join(right.split()) if right else ""
    if left_name and right_name:
        return left_name, right_name
    if left_name or right_name:
        return None
    names = store.experiment_names()
    if len(names) < 2:
        return None
    return names[-2], names[-1]


def _experiments_message(text: str, *, lead: bool = False) -> str:
    body = text if lead else f"<p>{escape(text)}</p>"
    return (
        '<div id="experiments">'
        "<h1>expériences</h1>"
        f"{body}"
        '<p><a href="/logs">retour aux traces</a></p>'
        "</div>"
    )


def _comparison_table(compared: Mapping[str, Any]) -> str:
    left = escape(str(compared.get("left", "")))
    right = escape(str(compared.get("right", "")))
    rows: list[str] = []
    for metric in compared.get("metrics", []):
        label = escape(str(metric.get("metric_id", "")))
        where = escape(_metric_where(metric, compared.get("metrics", [])))
        rows.append(
            "<tr>"
            f'<th scope="row">{label}<small>{where}</small></th>'
            f"{_score_cell(metric.get('left'))}"
            f"{_score_cell(metric.get('right'))}"
            "</tr>"
        )
    return (
        "<p>Les deux scores de chaque métrique.</p>"
        '<table id="run-comparison">'
        "<thead><tr>"
        "<th>métrique</th>"
        f"<th>{left}</th>"
        f"<th>{right}</th>"
        "</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table>"
    )


def _metric_where(metric: Mapping[str, Any], metrics: Sequence[Mapping[str, Any]]) -> str:
    request_ids: list[str] = []
    for item in metrics:
        request_id = str(item.get("request_id", ""))
        if request_id and request_id not in request_ids:
            request_ids.append(request_id)
    place = f"span {metric.get('span_index')}"
    if len(request_ids) > 1:
        return f"{metric.get('request_id', '')} · {place}"
    return place


def _score_cell(side: object) -> str:
    if not isinstance(side, Mapping):
        return "<td>—</td>"
    number = escape(_format_unit_score(side.get("score")))
    passed = "true" if side.get("passed") is True else "false"
    suffix = " erreur" if side.get("status") == "error" else ""
    return f"<td>{number} passed {passed}{suffix}</td>"


def _load_stream(store: TraceStore) -> list[dict[str, Any]]:
    loaded: list[dict[str, Any]] = []
    for item in store.list_traces(project=GATEWAY_PROJECT, log_stream=GATEWAY_STREAM):
        try:
            trace = Trace.model_validate(item["trace"])
        except ValueError:
            continue
        loaded.append({"created_at": item.get("created_at"), "trace": trace})
    return loaded


def _scores(store: TraceStore, request_id: str) -> list[dict[str, Any]]:
    found = store.scores_for(request_id)
    return list(found or [])


def _counts(stored: list[dict[str, Any]]) -> dict[str, int]:
    sessions = {item["trace"].session_id for item in stored}
    spans = sum(len(item["trace"].spans) for item in stored)
    return {"sessions": len(sessions), "traces": len(stored), "spans": spans}


def _table_metric_ids(store: TraceStore) -> tuple[str, ...]:
    enabled = store.enabled_metric_ids()
    return tuple(metric_id for metric_id in _TABLE_METRICS if metric_id in enabled)


def _rows_for_level(
    stored: list[dict[str, Any]],
    score_map: Mapping[str, Sequence[Mapping[str, Any]]],
    level: str,
    table_metrics: Sequence[str],
) -> list[dict[str, Any]]:
    if level == "sessions":
        return _session_rows(stored, score_map, table_metrics)
    if level == "spans":
        return _span_rows(stored, score_map, table_metrics)
    return [
        _trace_row(item, score_map.get(item["trace"].request_id, []), table_metrics)
        for item in stored
    ]


def _trace_row(
    item: dict[str, Any],
    scores: Sequence[Mapping[str, Any]],
    table_metrics: Sequence[str],
) -> dict[str, Any]:
    trace: Trace = item["trace"]
    row: dict[str, Any] = {
        "href": "/logs/traces/" + quote(trace.request_id, safe=""),
        "created_at": str(item.get("created_at") or "—"),
        "name": trace.name,
        "input": _chat_input(trace),
        "output": _chat_output(trace),
        "external_id": trace.request_id,
        "request_id": trace.request_id,
    }
    for metric_id in table_metrics:
        row[metric_id] = _metric_summary(scores, metric_id)
    return row


def _session_rows(
    stored: list[dict[str, Any]],
    score_map: Mapping[str, Sequence[Mapping[str, Any]]],
    table_metrics: Sequence[str],
) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for item in stored:
        groups.setdefault(item["trace"].session_id, []).append(item)
    rows: list[dict[str, Any]] = []
    for session_id, items in groups.items():
        first = items[0]
        last = items[-1]
        scores = score_map.get(last["trace"].request_id, [])
        row: dict[str, Any] = {
            "href": "/logs/sessions/" + quote(session_id, safe=""),
            "created_at": str(first.get("created_at") or "—"),
            "name": f"session ({len(items)})",
            "input": _chat_input(first["trace"]),
            "output": _chat_output(last["trace"]),
            "external_id": session_id,
            "request_id": last["trace"].request_id,
        }
        for metric_id in table_metrics:
            row[metric_id] = _metric_summary(scores, metric_id)
        rows.append(row)
    return rows


def _span_rows(
    stored: list[dict[str, Any]],
    score_map: Mapping[str, Sequence[Mapping[str, Any]]],
    table_metrics: Sequence[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in stored:
        trace: Trace = item["trace"]
        scores = score_map.get(trace.request_id, [])
        by_span = _scores_by_span(scores)
        for index, span in enumerate(trace.spans):
            row: dict[str, Any] = {
                "href": f"/logs/traces/{quote(trace.request_id, safe='')}?span={index}",
                "created_at": str(item.get("created_at") or "—"),
                "name": span.name,
                "input": _truncate(span.input_masked),
                "output": _truncate(span.output_masked) or "—",
                "external_id": f"{trace.request_id}#{index}",
                "request_id": trace.request_id,
            }
            for metric_id in table_metrics:
                row[metric_id] = _metric_summary(by_span.get(index, []), metric_id)
            rows.append(row)
    return rows


def _search_blob(row: Mapping[str, Any]) -> str:
    parts = [
        str(row.get("name", "")),
        str(row.get("input", "")),
        str(row.get("output", "")),
        str(row.get("external_id", "")),
        str(row.get("request_id", "")),
    ]
    return " ".join(parts).lower()


def _logs_tabs(*, active: str = "logs") -> str:
    def tab(key: str, href: str, label: str, ico: str) -> str:
        klass = "active" if active == key else ""
        return (
            f'<a class="{klass}" href="{href}">'
            f'<span class="tab-ico" aria-hidden="true">{ico}</span>{escape(label)}</a>'
        )

    return (
        '<div class="page-tabs">'
        + tab("logs", "/logs", "Logs", "☰")
        + tab("trends", "/logs/trends", "Trends", "↗")
        + '<span class="disabled"><span class="tab-ico" aria-hidden="true">◈</span>'
        "Agent graph</span>"
        '<span class="disabled"><span class="tab-ico" aria-hidden="true">◉</span>'
        "Signals</span>"
        '<span class="disabled"><span class="tab-ico" aria-hidden="true">⚙</span>'
        "Controls</span>"
        '<span class="disabled"><span class="tab-ico" aria-hidden="true">⚠</span>'
        "Alerts</span>"
        "</div>"
    )


def _toolbar(level: str, counts: Mapping[str, int], q: str) -> str:
    def chip(key: str, label: str, n: int) -> str:
        active = "active" if level == key else ""
        return (
            f'<a class="chip {active}" href="/logs?level={key}">'
            f'{escape(label)} <span class="count">{n}</span></a>'
        )

    return (
        '<form class="toolbar" method="get" action="/logs">'
        f'<input type="hidden" name="level" value="{escape(level)}">'
        '<a class="chip" href="/logs">Default View ▾</a>'
        + chip("sessions", "Sessions", counts["sessions"])
        + chip("traces", "Traces", counts["traces"])
        + chip("spans", "Spans", counts["spans"])
        + '<span class="chip">Last month</span>'
        + '<span class="chip">Filters</span>'
        + '<div class="search-wrap">'
        + '<input class="search" type="search" name="q" '
        f'placeholder="Search logs" value="{escape(q)}">'
        + '<button type="button" class="btn-ghost is-disabled" disabled>'
        "Compute Metrics</button>"
        + "</div></form>"
    )


def _table(
    rows: list[dict[str, Any]],
    level: str,
    table_metrics: Sequence[str],
) -> str:
    if not rows:
        return (
            '<div class="surface empty" id="trace-list">'
            "<p>No events on this log stream yet.</p>"
            '<p><a class="btn-primary" href="/chat">Open Chat to create a trace</a></p>'
            "</div>"
        )
    head = "".join(
        f'<th><span class="ai" aria-hidden="true"></span>'
        f"{escape(_METRIC_NAMES[metric_id])}"
        '<span class="sort" aria-hidden="true">↕</span>'
        '<span class="agg">AVG</span></th>'
        for metric_id in table_metrics
    )
    body: list[str] = []
    for row in rows:
        href = escape(str(row["href"]))
        recorded = escape(str(row["created_at"]))
        cells = [
            '<td><input type="checkbox" disabled aria-label="Select row"></td>',
            f'<td><a class="row-link" href="{href}">'
            f'<time datetime="{recorded}">{recorded}</time></a></td>',
            f'<td class="clip"><a class="row-link" href="{href}">'
            f'{escape(str(row["name"]))}</a></td>',
            f'<td class="clip" title="{escape(str(row["input"]))}">'
            f'{escape(str(row["input"]))}</td>',
            f'<td class="clip" title="{escape(str(row["output"]))}">'
            f'{escape(str(row["output"])) or "—"}</td>',
            '<td class="na">—</td>',
            f'<td class="clip">{escape(str(row["external_id"]))}</td>',
        ]
        for metric_id in table_metrics:
            text, kind = row[metric_id]
            cells.append(f"<td>{_pill(text, kind)}</td>")
        body.append(f'<tr data-level="{escape(level)}">' + "".join(cells) + "</tr>")
    return (
        '<div class="surface">'
        '<table id="trace-list" class="logs">'
        "<thead><tr>"
        "<th></th>"
        '<th>Created<span class="sort" aria-hidden="true">↕</span></th>'
        '<th>Name<span class="sort" aria-hidden="true">↕</span></th>'
        "<th>Input</th><th>Output</th>"
        "<th>Error Message</th><th>External Id</th>"
        f"{head}"
        "</tr></thead>"
        f"<tbody>{''.join(body)}</tbody>"
        "</table>"
        "</div>"
    )


def _pager(level: str, q: str, page: int, pages: int) -> str:
    if pages <= 1:
        return ""
    q_param = f"&q={quote(q)}" if q else ""
    prev_href = f"/logs?level={level}&page={page - 1}{q_param}" if page > 1 else ""
    next_href = f"/logs?level={level}&page={page + 1}{q_param}" if page < pages else ""
    prev = (
        f'<a href="{prev_href}">‹ Previous</a>' if prev_href else "<span>‹ Previous</span>"
    )
    nxt = f'<a href="{next_href}">Next ›</a>' if next_href else "<span>Next ›</span>"
    nums = "".join(
        f'<span class="current">{i}</span>'
        if i == page
        else f'<a href="/logs?level={level}&page={i}{q_param}">{i}</a>'
        for i in range(1, pages + 1)
    )
    return f'<div class="pager">{prev}{nums}{nxt}</div>'


def _sparkline(seed: int) -> str:
    """Decorative SVG path for Trends cards (not live time-series)."""
    points = []
    y = 40 - (seed * 3) % 18
    for x in range(0, 101, 8):
        y = max(8, min(48, y + ((x + seed * 7) % 11) - 5))
        points.append(f"{x},{y}")
    path = " ".join(points)
    return (
        '<svg viewBox="0 0 100 56" preserveAspectRatio="none">'
        '<polyline fill="none" stroke="#6366f1" stroke-width="1.6" '
        f'points="{path}"/></svg>'
    )


def _session(
    trace: Trace,
    scores: Sequence[Mapping[str, Any]],
    span: int | None,
    enabled: frozenset[str],
) -> str:
    chosen = span if span is not None and 0 <= span < len(trace.spans) else None
    visible = scores if chosen is None else _scores_by_span(scores).get(chosen, [])
    return (
        '<div class="detail-layout session">'
        + _tree(trace, chosen)
        + '<div id="trace-detail" class="panel">'
        + _interaction(trace, chosen)
        + "</div>"
        + _metric_panel(visible, enabled)
        + "</div>"
    )


def _tree(trace: Trace, chosen: int | None) -> str:
    items = [
        f'<li><a href="/logs/traces/{quote(trace.request_id, safe="")}"'
        f'{" aria-current=\"true\"" if chosen is None else ""}>'
        f"{escape(trace.name)}</a></li>"
    ]
    for index, span in enumerate(trace.spans):
        current = ' aria-current="true"' if chosen == index else ""
        href = f"/logs/traces/{quote(trace.request_id, safe='')}?span={index}"
        items.append(
            f'<li><a href="{href}"{current}>{escape(span.name)}</a></li>'
        )
    return (
        '<div class="panel">'
        "<h2>Spans</h2>"
        f'<ul class="span-tree">{"".join(items)}</ul>'
        "</div>"
    )


def _interaction(trace: Trace, chosen: int | None) -> str:
    if chosen is None:
        return (
            f"<h2>{escape(trace.name)}</h2>"
            "<h3>Input</h3>"
            f"<pre>{escape(_chat_input(trace))}</pre>"
            "<h3>Output</h3>"
            f"<pre>{escape(_chat_output(trace)) or '—'}</pre>"
        )
    span = trace.spans[chosen]
    layer = _layer_number(span)
    layer_attr = "" if layer is None else f' data-layer="{layer}"'
    blocks = [
        f'<article data-name="{escape(span.name)}"{layer_attr}>',
        f"<h2>{escape(span.name)}</h2>",
        f"<p>type {escape(span.type.value)}</p>",
        "<h3>Input</h3>",
        f"<pre>{escape(span.input_masked) or '—'}</pre>",
        "<h3>Output</h3>",
        f"<pre>{escape(span.output_masked) or '—'}</pre>",
    ]
    if _is_layer8(span):
        count = escape(span.metadata.get("token_count", ""))
        status = escape(span.metadata.get("status", ""))
        blocks.append(f"<p>compteur de tokens <span class=\"token-count\">{count}</span></p>")
        blocks.append(f"<p>statut <span class=\"layer-status\">{status}</span></p>")
        blocks.append(f"<p>{REHYDRATION_LABEL}</p>")
    blocks.append("</article>")
    return "".join(blocks)


def _metric_panel(
    scores: Sequence[Mapping[str, Any]],
    enabled: frozenset[str],
) -> str:
    by_id = {str(row.get("metric_id")): row for row in scores}
    sections: list[str] = [
        "<h2>Metrics</h2>",
        '<p class="na">A dash means this metric was not judged on this interaction. '
        'Disabled metrics are hidden — configure them under Metrics.</p>',
    ]
    for title, metric_ids in _PANELS:
        active_ids = [metric_id for metric_id in metric_ids if metric_id in enabled]
        if not active_ids:
            continue
        sections.append(f"<h3>{escape(title)}</h3><ul class=\"metric-list\">")
        for metric_id in active_ids:
            name = _METRIC_NAMES.get(metric_id, metric_id)
            row = by_id.get(metric_id)
            if row is None:
                sections.append(f"<li>{escape(name)} <span class=\"na\">—</span></li>")
                continue
            text, kind = _metric_summary([row], metric_id)
            rationale = escape(str(row.get("rationale", "")))
            sections.append(
                f"<li>{escape(name)} {_pill(text, kind)}"
                f'<span class="rationale">{rationale}</span></li>'
            )
        sections.append("</ul>")
    other = [
        row
        for row in scores
        if str(row.get("metric_id")) in enabled
        and str(row.get("metric_id")) not in {m for _, ids in _PANELS for m in ids}
    ]
    if other:
        sections.append("<h3>Other</h3><ul class=\"metric-list\">")
        for row in other:
            metric_id = str(row.get("metric_id"))
            name = _METRIC_NAMES.get(metric_id, metric_id)
            text, kind = _metric_summary([row], metric_id)
            rationale = escape(str(row.get("rationale", "")))
            sections.append(
                f"<li>{escape(name)} {_pill(text, kind)}"
                f'<span class="rationale">{rationale}</span></li>'
            )
        sections.append("</ul>")
    return '<div class="panel" id="metrics">' + "".join(sections) + "</div>"


def _chat_input(trace: Trace) -> str:
    for span in trace.spans:
        if span.type in {SpanType.AGENT, SpanType.LLM} and span.input_masked.strip():
            return _truncate(span.input_masked)
    for span in trace.spans:
        if span.input_masked.strip():
            return _truncate(span.input_masked)
    return "—"


def _chat_output(trace: Trace) -> str:
    for span in reversed(trace.spans):
        if _is_layer8(span):
            continue
        if span.type in {SpanType.AGENT, SpanType.LLM} and span.output_masked.strip():
            return _truncate(span.output_masked)
    for span in reversed(trace.spans):
        if _is_layer8(span):
            continue
        if span.output_masked.strip():
            return _truncate(span.output_masked)
    return "—"


def _truncate(value: str, limit: int = 72) -> str:
    text = " ".join(value.split())
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def _metric_summary(
    scores: Sequence[Mapping[str, Any]],
    metric_id: str,
) -> tuple[str, str]:
    rows = [row for row in scores if str(row.get("metric_id")) == metric_id]
    if not rows:
        return ("—", "na")
    row = rows[0]
    if row.get("status") == "error":
        return ("error", "bad")
    score = _score_number(row.get("score"))
    passed = row.get("passed") is True
    if metric_id == "pii":
        return ("true" if passed else "false", "ok" if passed else "bad")
    if score is None:
        return ("—", "na")
    if metric_id in {"completeness", "context_adherence"} or (
        isinstance(score, float) and score not in {0.0, 1.0}
    ):
        pct = f"{int(round(score * 100))}%"
        return (pct, "ok" if passed or score >= 0.8 else "bad")
    label = "true" if passed else "false"
    return (label, "ok" if passed else "bad")


def _pill(text: str, kind: str) -> str:
    if kind == "na" or text in {"—", "-", "N/A"}:
        return f'<span class="na">{escape(text)}</span>'
    klass = {
        "ok": "badge badge-ok",
        "bad": "badge badge-bad",
        "neutral": "badge badge-neutral",
    }.get(kind, "badge badge-neutral")
    return f'<span class="{klass}">{escape(text)}</span>'


def _scores_by_span(
    scores: Sequence[Mapping[str, Any]],
) -> dict[int, list[Mapping[str, Any]]]:
    grouped: dict[int, list[Mapping[str, Any]]] = {}
    for row in scores:
        index = row.get("span_index")
        if isinstance(index, bool) or not isinstance(index, int):
            continue
        grouped.setdefault(index, []).append(row)
    return grouped


def _is_layer8(span: Span) -> bool:
    return span.name.strip() == "layer_8_rehydration" or _layer_number(span) == 8


def _layer_number(span: Span) -> int | None:
    compact = "".join(span.metadata.get("layer", "").split())
    if compact.isdigit():
        return int(compact)
    return None


def _score_number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _format_unit_score(value: object) -> str:
    number = _score_number(value)
    if number is None or number < 0 or number > 1:
        raise ValueError("score out of range")
    text = f"{number:.6f}".rstrip("0").rstrip(".")
    return text or "0"
