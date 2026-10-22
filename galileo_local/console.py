"""Gateway console: chat history, metric judgments, and one interaction.

The history table shows the masked user text, the masked model answer when the
trace kept one, and one cell per headline metric. A click opens that
interaction: the span tree, the selected text, and the judgments. Layer 8
shows a token count, a status, and a fixed label. The rehydrated answer is
not a field here.
"""

from __future__ import annotations

from html import escape
from typing import Any, Mapping, Sequence
from urllib.parse import quote

from galileo_local.catalog import METRICS
from galileo_local.models import Span, SpanType, Trace, rehydration_span
from galileo_local.pii_oracle import find_clear_pii
from galileo_local.settings import LOG_STREAM, PROJECT_NAME
from galileo_local.store import TraceStore

_METRIC_NAMES = {metric.id: metric.name for metric in METRICS}
_TABLE_METRICS = (
    "completeness",
    "correctness",
    "instruction_adherence",
    "reasoning_coherence",
    "pii",
)
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
_ANSWER_ABSENT = "La réponse du modèle n'est pas enregistrée dans la trace."

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
    """A ``pii`` score of 0 comes first. Judges keep their relative order."""

    def rank(item: Mapping[str, Any]) -> int:
        if str(item.get("metric_id", "")) == "pii" and _score_number(item.get("score")) == 0:
            return 0
        return 1

    return sorted(scores, key=rank)


def render_score_list(scores: Sequence[Mapping[str, Any]]) -> str:
    """Numbers from 0 to 1 and the ``passed`` boolean. Empty when there are none."""
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
    selected: str | None,
    span: int | None = None,
) -> str:
    """History of gateway traces. A click opens one interaction."""
    if selected and find_clear_pii(selected):
        selected = None
    if span is not None and span < 0:
        span = None
    stored = _load_gateway(store)
    by_id = {
        item["trace"].request_id: _selected_scores(store, item["trace"].request_id)
        for item in stored
    }
    rows = [_row(item, by_id.get(item["trace"].request_id, [])) for item in stored]
    chosen = by_id.get(selected, []) if selected else []
    detail = _detail_for(stored, selected, chosen, span)
    history = _list_html(rows, selected)
    body = detail + history if selected else history
    return _shell(body)


def render_experiments(
    store: TraceStore,
    *,
    left: str | None = None,
    right: str | None = None,
) -> str:
    """Comparison of two runs. The header link on ``/`` opens this page.

    With no names, the two latest runs are shown. The table is the whole
    comparison: metric, then the two scores. No chart.
    """
    if _query_is_blocked(left) or _query_is_blocked(right):
        return _shell(_experiments_message("Run introuvable."))
    chosen = _chosen_runs(store, left, right)
    if chosen is None:
        return _shell(_experiments_message("Deux runs sont nécessaires pour comparer les scores."))
    left_name, right_name = chosen
    compared = store.compare_experiments(left_name, right_name)
    if compared is None:
        return _shell(_experiments_message("Run introuvable."))
    return _shell(_experiments_message(_comparison_table(compared), lead=True))


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
    if lead:
        body = text
    else:
        body = f"<p>{escape(text)}</p>"
    return (
        '<div id="experiments">'
        "<h1>Expériences</h1>"
        f"{body}"
        '<p><a href="/">retour aux traces</a></p>'
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
    body = "".join(rows)
    return (
        "<p>Les deux scores de chaque métrique.</p>"
        '<table id="run-comparison">'
        "<thead><tr>"
        "<th>métrique</th>"
        f"<th>{left}</th>"
        f"<th>{right}</th>"
        "</tr></thead>"
        f"<tbody>{body}</tbody>"
        "</table>"
    )


def _metric_where(metric: Mapping[str, Any], metrics: Sequence[Mapping[str, Any]]) -> str:
    request_ids: list[str] = []
    for item in metrics:
        request_id = str(item.get("request_id", ""))
        if request_id and request_id not in request_ids:
            request_ids.append(request_id)
    span = metric.get("span_index")
    place = f"span {span}"
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


def _load_gateway(store: TraceStore) -> list[dict[str, Any]]:
    loaded: list[dict[str, Any]] = []
    for item in store.list_traces(project=GATEWAY_PROJECT, log_stream=GATEWAY_STREAM):
        try:
            trace = Trace.model_validate(item["trace"])
        except ValueError:
            continue
        loaded.append({"created_at": item.get("created_at"), "trace": trace})
    return loaded


def _row(item: dict[str, Any], scores: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    trace: Trace = item["trace"]
    recorded = item.get("created_at") or "—"
    row: dict[str, Any] = {
        "request_id": trace.request_id,
        "name": trace.name,
        "recorded_at": str(recorded),
        "status": _trace_status(trace),
        "intent": _trace_intent(trace),
        "input": _chat_input(trace),
        "output": _chat_output(trace),
    }
    for metric_id in _TABLE_METRICS:
        row[metric_id] = _metric_summary(scores, metric_id)
    return row


def _trace_intent(trace: Trace) -> str:
    for span in trace.spans:
        intent = span.metadata.get("intent", "").strip()
        if intent:
            return intent
    return "—"


def _trace_status(trace: Trace) -> str:
    for span in trace.spans:
        if _is_layer8(span):
            return span.metadata.get("status", "").strip() or "—"
    return "—"


def _selected_scores(store: TraceStore, selected: str | None) -> list[dict[str, Any]]:
    """Scores of the open trace. A missing database file stays missing."""
    if not selected:
        return []
    found = store.scores_for(selected)
    return list(found or [])


def _detail_for(
    stored: list[dict[str, Any]],
    selected: str | None,
    scores: Sequence[Mapping[str, Any]],
    span: int | None,
) -> str:
    if not selected:
        return ""
    for item in stored:
        trace: Trace = item["trace"]
        if trace.request_id == selected:
            return _session(trace, scores, span)
    safe = escape(selected)
    return f'<div id="trace-detail"><p>Trace introuvable : {safe}</p></div>'


def _list_html(rows: list[dict[str, Any]], selected: str | None) -> str:
    if not rows:
        return (
            '<table id="trace-list"><tbody><tr>'
            "<td>Aucune trace sur le stream gateway.</td>"
            "</tr></tbody></table>"
        )
    head = "".join(f"<th>{escape(_METRIC_NAMES[metric_id])}</th>" for metric_id in _TABLE_METRICS)
    body: list[str] = []
    for row in rows:
        current = ' aria-current="true"' if row["request_id"] == selected else ""
        href = "/?trace=" + quote(str(row["request_id"]), safe="")
        recorded = escape(str(row["recorded_at"]))
        cells = [
            f'<td><a href="{href}"{current}>'
            f'<span class="heure">heure <time datetime="{recorded}">{recorded}</time></span>'
            f'<span class="request-id">identifiant {escape(str(row["request_id"]))}</span>'
            f'<span class="trace-name">{escape(str(row["name"]))}</span>'
            f'<span class="trace-status">statut {escape(str(row["status"]))}</span>'
            f'<span class="intent">intent {escape(str(row["intent"]))}</span>'
            "</a></td>",
            f'<td class="clip">{escape(str(row["input"]))}</td>',
            f'<td class="clip">{escape(str(row["output"])) or "—"}</td>',
        ]
        for metric_id in _TABLE_METRICS:
            text, kind = row[metric_id]
            cells.append(f'<td>{_pill(text, kind)}</td>')
        body.append("<tr>" + "".join(cells) + "</tr>")
    return (
        '<table id="trace-list">'
        "<thead><tr>"
        "<th>Trace</th><th>Input</th><th>Output</th>"
        f"{head}"
        "</tr></thead>"
        f'<tbody>{"".join(body)}</tbody>'
        "</table>"
    )


def _session(trace: Trace, scores: Sequence[Mapping[str, Any]], span: int | None) -> str:
    chosen = span if span is not None and 0 <= span < len(trace.spans) else None
    visible = scores if chosen is None else _scores_by_span(scores).get(chosen, [])
    return (
        '<div class="session">'
        + _tree(trace, chosen)
        + '<div id="trace-detail">'
        + _interaction(trace, chosen)
        + "</div>"
        + _metric_panel(visible)
        + "</div>"
    )


def _grouped(trace: Trace) -> list[tuple[int | None, list[tuple[int, Span]]]]:
    def sort_key(pair: tuple[int, Span]) -> tuple[bool, int, int]:
        index, span = pair
        layer = _layer_number(span)
        if layer is None:
            return (True, 0, index)
        return (False, layer, index)

    groups: list[tuple[int | None, list[tuple[int, Span]]]] = []
    for index, span in sorted(enumerate(trace.spans), key=sort_key):
        layer = _layer_number(span)
        if not groups or groups[-1][0] != layer:
            groups.append((layer, []))
        groups[-1][1].append((index, span))
    return groups


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


def _tree(trace: Trace, selected_span: int | None) -> str:
    href = "/?trace=" + quote(trace.request_id, safe="")
    root_current = ' aria-current="true"' if selected_span is None else ""
    items = [
        f'<a class="tree-root" href="{href}"{root_current}>{escape(trace.name)}</a>',
        '<ol class="tree">',
    ]
    for _layer, spans in _grouped(trace):
        for index, span in spans:
            current = ' aria-current="true"' if index == selected_span else ""
            items.append(
                "<li>"
                f'<a href="{href}&amp;span={index}"{current} data-span="{index}">'
                f"{escape(span.name)}</a>"
                "</li>"
            )
    items.append("</ol>")
    return '<nav id="span-tree">' + "".join(items) + "</nav>"


def _interaction(trace: Trace, span_index: int | None) -> str:
    if span_index is None:
        incoming = _chat_input(trace)
        outgoing = _chat_output(trace)
        blocks = [
            f'<article data-name="{escape(trace.name)}">',
            f"<h2>{escape(trace.name)}</h2>",
            _masked("Input", incoming),
            _masked("Output", outgoing),
        ]
        if not outgoing:
            blocks.append(f"<p>{_ANSWER_ABSENT}</p>")
    else:
        span = trace.spans[span_index]
        layer = _layer_number(span)
        layer_attr = "" if layer is None else f' data-layer="{layer}"'
        blocks = [
            f'<article data-name="{escape(span.name)}"{layer_attr}>',
            f"<h2>{escape(span.name)}</h2>",
            f"<p>type {escape(span.type.value)}</p>",
            _masked("Input", span.input_masked),
            _masked("Output", span.output_masked),
        ]
        if _is_layer8(span):
            count = escape(span.metadata.get("token_count", ""))
            status = escape(span.metadata.get("status", ""))
            blocks.append(
                f'<p>compteur de tokens <span class="token-count">{count}</span></p>'
            )
            blocks.append(f'<p>statut <span class="layer-status">{status}</span></p>')
            blocks.append(f"<p>{REHYDRATION_LABEL}</p>")
        elif not span.output_masked.strip():
            blocks.append(f"<p>{_ANSWER_ABSENT}</p>")
    blocks.append("</article>")
    return "".join(blocks)


def _metric_panel(scores: Sequence[Mapping[str, Any]]) -> str:
    shown: set[str] = set()
    groups: list[str] = []
    for title, metric_ids in _PANELS:
        shown.update(metric_ids)
        groups.append(_metric_group(title, metric_ids, scores))
    extra = [
        str(row.get("metric_id", ""))
        for row in scores
        if str(row.get("metric_id", "")) and str(row.get("metric_id")) not in shown
    ]
    if extra:
        groups.append(_metric_group("Autres", tuple(dict.fromkeys(extra)), scores))
    note = (
        "<p>Un tiret signifie que cette métrique n'a pas été jugée "
        "sur cette interaction.</p>"
    )
    return '<aside id="metrics"><h2>Metrics</h2>' + note + "".join(groups) + "</aside>"


def _metric_group(
    title: str,
    metric_ids: Sequence[str],
    scores: Sequence[Mapping[str, Any]],
) -> str:
    items: list[str] = []
    for metric_id in metric_ids:
        text, kind = _metric_summary(scores, metric_id)
        label = escape(_METRIC_NAMES.get(metric_id, metric_id))
        reasons = _rationales(scores, metric_id)
        reason = "".join(f'<p class="jugement">{escape(item)}</p>' for item in reasons)
        items.append(
            "<li>"
            f'<span class="metric-name">{label}</span>'
            f"{_pill(text, kind)}"
            f"{reason}"
            "</li>"
        )
    return (
        '<section class="metric-group">'
        f"<h3>{escape(title)}</h3>"
        f'<ul>{"".join(items)}</ul>'
        "</section>"
    )


def _rationales(scores: Sequence[Mapping[str, Any]], metric_id: str) -> list[str]:
    found: list[str] = []
    for row in scores:
        if str(row.get("metric_id", "")) != metric_id or row.get("status") == "error":
            continue
        text = str(row.get("rationale", "")).strip()
        if text and text not in found:
            found.append(text)
    return found


def _pill(text: str, kind: str) -> str:
    return f'<span class="pill {escape(kind)}">{escape(text)}</span>'


def _metric_summary(
    scores: Sequence[Mapping[str, Any]],
    metric_id: str,
) -> tuple[str, str]:
    rows = [row for row in scores if str(row.get("metric_id", "")) == metric_id]
    ok = [row for row in rows if row.get("status") != "error"]
    if not ok:
        if rows:
            return ("erreur de juge", "error")
        return ("—", "empty")
    if metric_id in {"completeness", "context_adherence"}:
        numbers = [
            number
            for number in (_score_number(row.get("score")) for row in ok)
            if number is not None
        ]
        if not numbers:
            return ("—", "empty")
        percent = round(sum(numbers) / len(numbers) * 100)
        kind = "true" if percent >= 50 else "false"
        return (f"{percent}%", kind)
    if any(row.get("passed") is False for row in ok):
        return ("false", "false")
    if all(row.get("passed") is True for row in ok):
        return ("true", "true")
    return ("—", "empty")


def _chat_input(trace: Trace) -> str:
    for span in trace.spans:
        if _layer_number(span) == 3 and span.input_masked.strip():
            return span.input_masked
    for span in trace.spans:
        if span.input_masked.strip() and not _is_layer8(span):
            return span.input_masked
    return ""


def _chat_output(trace: Trace) -> str:
    for span in trace.spans:
        if span.type == SpanType.AGENT and span.output_masked.strip():
            return span.output_masked
    return ""


def _masked(label: str, value: str) -> str:
    shown = value if value.strip() else "—"
    return f"<h2>{escape(label)}</h2><pre class=\"masked\">{escape(shown)}</pre>"


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


def _shell(main: str) -> str:
    return (
        "<!DOCTYPE html>"
        '<html lang="fr">'
        "<head>"
        '<meta charset="utf-8">'
        f"<title>{GATEWAY_PROJECT} · {GATEWAY_STREAM}</title>"
        "<style>"
        "body{margin:0;background:#f7f7f8;color:#1c1c1c;"
        "font:15px/1.45 'Segoe UI',sans-serif;}"
        "header{display:flex;gap:1.5rem;align-items:center;padding:.8rem 1.25rem;"
        "background:#fff;border-bottom:1px solid #e6e6e6;}"
        "header p{margin:0;}"
        "a{color:#5b21b6;}"
        ".layout{display:flex;flex-direction:column;gap:1rem;padding:1rem 1.25rem;}"
        "#trace-list{width:100%;border-collapse:collapse;background:#fff;"
        "border:1px solid #e6e6e6;border-radius:8px;}"
        "#trace-list th,#trace-list td{padding:.65rem .75rem;border-bottom:1px solid #eee;"
        "text-align:left;vertical-align:top;}"
        "#trace-list thead th{font-size:12px;color:#555;}"
        "#trace-list a{color:inherit;text-decoration:none;}"
        "#trace-list .heure{display:block;font-weight:600;color:#111;}"
        "#trace-list .intent{display:block;color:#5b21b6;font-size:12px;}"
        "#trace-list .request-id,#trace-list .trace-name,#trace-list .trace-status{"
        "position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0);}"
        '#trace-list a[aria-current="true"] .heure{color:#5b21b6;}'
        ".clip{max-width:18rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}"
        ".session{display:grid;grid-template-columns:16rem minmax(0,1fr) 22rem;"
        "gap:1rem;align-items:start;}"
        "#span-tree,#trace-detail,#metrics{background:#fff;border:1px solid #e6e6e6;"
        "border-radius:8px;padding:.9rem 1rem;}"
        "#span-tree a{display:block;padding:.28rem .4rem;border-radius:6px;"
        "text-decoration:none;color:#333;}"
        '#span-tree a[aria-current="true"]{background:#efeaff;color:#5b21b6;}'
        "ol.tree{list-style:none;margin:.4rem 0 0;padding:0;}"
        ".pill{display:inline-block;border-radius:999px;padding:.05rem .55rem;font-size:13px;}"
        ".pill.true{background:#e7f6ee;color:#137333;}"
        ".pill.false{background:#fde8e8;color:#b42318;}"
        ".pill.empty{background:#f4f1ea;color:#666;}"
        ".pill.error{background:#fff4e5;color:#8a4b08;}"
        ".metric-group ul{list-style:none;margin:0;padding:0;}"
        ".metric-group li{padding:.45rem 0;border-bottom:1px solid #f0f0f0;}"
        ".metric-name{display:inline-block;min-width:11rem;}"
        ".jugement{margin:.25rem 0 0;color:#333;font-size:13px;}"
        "pre.masked{white-space:pre-wrap;background:#fff;border:1px solid #e6e6e6;"
        "border-radius:8px;padding:.75rem;min-height:2.2rem;}"
        "#experiments{flex:1;background:#fff;border:1px solid #d9d3c7;padding:1rem 1.25rem;}"
        "#run-comparison{width:100%;border-collapse:collapse;font-size:1.35rem;}"
        "#run-comparison th,#run-comparison td{padding:.75rem 1rem;"
        "border-bottom:1px solid #d9d3c7;text-align:left;vertical-align:top;}"
        "#run-comparison thead th{background:#e7f0ea;}"
        "#run-comparison small{display:block;font-size:.75em;font-weight:normal;color:#333;}"
        "</style>"
        "</head>"
        "<body>"
        "<header>"
        f"<p>projet {GATEWAY_PROJECT}</p>"
        f"<p>stream {GATEWAY_STREAM}</p>"
        '<p><a href="/chat">chat</a></p>'
        '<p><a href="/experiments">expériences</a></p>'
        "</header>"
        f'<div class="layout">{main}</div>'
        "</body></html>"
    )
