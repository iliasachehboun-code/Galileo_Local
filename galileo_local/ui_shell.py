"""Shared Galileo console chrome: sidebar, tokens, page shell."""

from __future__ import annotations

from html import escape

from galileo_local.settings import LOG_STREAM, PROJECT_NAME

NavKey = str  # home | overview | logs | experiments | metrics | chat


def shell_css() -> str:
    return """
:root {
  --gal-bg: #f7f7fb;
  --gal-surface: #ffffff;
  --gal-sidebar: #ffffff;
  --gal-border: #e6e6ef;
  --gal-text: #1c1c28;
  --gal-muted: #6b6b7b;
  --gal-accent: #6d5efc;
  --gal-accent-soft: #eef0ff;
  --gal-row-hover: #f3f4fb;
  --gal-badge-ok-bg: #e7f8ef;
  --gal-badge-ok-fg: #0f7a45;
  --gal-badge-bad-bg: #fdecee;
  --gal-badge-bad-fg: #c62828;
  --gal-badge-neutral-bg: #eef0f4;
  --gal-badge-neutral-fg: #5c5c6a;
  --gal-na: #9a9aaa;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  min-height: 100vh;
  display: flex;
  background: var(--gal-bg);
  color: var(--gal-text);
  font: 14px/1.45 "IBM Plex Sans", "Segoe UI", system-ui, sans-serif;
}
a { color: var(--gal-accent); text-decoration: none; }
a:hover { text-decoration: underline; }
.sidebar {
  width: 240px;
  flex: none;
  background: var(--gal-sidebar);
  border-right: 1px solid var(--gal-border);
  display: flex;
  flex-direction: column;
  padding: 1rem 0.75rem;
  min-height: 100vh;
}
.brand {
  font-weight: 700;
  font-size: 1.15rem;
  letter-spacing: -0.02em;
  color: var(--gal-text);
  padding: 0.35rem 0.65rem 1rem;
}
.nav-section { margin-bottom: 0.75rem; }
.nav-label {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--gal-muted);
  padding: 0.4rem 0.65rem;
}
.nav a, .nav span.soon {
  display: block;
  padding: 0.45rem 0.65rem;
  border-radius: 8px;
  color: var(--gal-text);
  margin: 0.1rem 0;
}
.nav a.active {
  background: var(--gal-accent-soft);
  color: var(--gal-accent);
  font-weight: 600;
  text-decoration: none;
}
.nav span.soon {
  color: var(--gal-na);
  cursor: default;
}
.nav .project {
  font-weight: 600;
  padding: 0.35rem 0.65rem;
  color: var(--gal-text);
}
.sidebar-foot {
  margin-top: auto;
  padding: 0.75rem 0.65rem 0.25rem;
  border-top: 1px solid var(--gal-border);
}
.main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.85rem 1.5rem;
  background: var(--gal-surface);
  border-bottom: 1px solid var(--gal-border);
}
.breadcrumb {
  color: var(--gal-muted);
  font-size: 0.92rem;
}
.breadcrumb strong { color: var(--gal-text); font-weight: 600; }
.btn-primary {
  display: inline-block;
  background: var(--gal-accent);
  color: #fff !important;
  border: 0;
  border-radius: 8px;
  padding: 0.45rem 0.9rem;
  font: inherit;
  font-weight: 600;
  text-decoration: none !important;
  cursor: pointer;
}
.content { padding: 1.25rem 1.5rem 2rem; flex: 1; }
.page-tabs {
  display: flex;
  gap: 0.25rem;
  border-bottom: 1px solid var(--gal-border);
  margin-bottom: 1rem;
}
.page-tabs a, .page-tabs span {
  padding: 0.55rem 0.85rem;
  color: var(--gal-muted);
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
}
.page-tabs a.active {
  color: var(--gal-accent);
  border-bottom-color: var(--gal-accent);
  font-weight: 600;
  text-decoration: none;
}
.page-tabs span.disabled { color: var(--gal-na); }
.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
  margin-bottom: 0.85rem;
}
.chip {
  display: inline-block;
  padding: 0.35rem 0.7rem;
  border-radius: 8px;
  border: 1px solid var(--gal-border);
  background: var(--gal-surface);
  color: var(--gal-text);
  font: inherit;
  text-decoration: none;
}
.chip.active {
  background: var(--gal-accent-soft);
  border-color: #c9c5f5;
  color: var(--gal-accent);
  font-weight: 600;
}
.search {
  margin-left: auto;
  border: 1px solid var(--gal-border);
  border-radius: 8px;
  padding: 0.4rem 0.7rem;
  font: inherit;
  min-width: 14rem;
  background: var(--gal-surface);
}
.surface {
  background: var(--gal-surface);
  border: 1px solid var(--gal-border);
  border-radius: 10px;
  overflow: auto;
}
table.logs {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.92rem;
}
table.logs th {
  text-align: left;
  font-weight: 500;
  color: var(--gal-muted);
  padding: 0.65rem 0.85rem;
  border-bottom: 1px solid var(--gal-border);
  white-space: nowrap;
  background: #fafafc;
}
table.logs th .ai {
  color: var(--gal-accent);
  font-size: 0.75rem;
  margin-right: 0.25rem;
}
table.logs td {
  padding: 0.7rem 0.85rem;
  border-bottom: 1px solid var(--gal-border);
  vertical-align: middle;
  max-width: 16rem;
}
table.logs tbody tr { height: 52px; transition: background 0.12s ease; }
table.logs tbody tr:hover { background: var(--gal-row-hover); }
table.logs tbody tr[aria-current="true"] { background: var(--gal-accent-soft); }
table.logs a.row-link {
  color: inherit;
  text-decoration: none;
  display: block;
}
.clip {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 14rem;
}
.badge {
  display: inline-block;
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 600;
  line-height: 1.4;
}
.badge-ok { background: var(--gal-badge-ok-bg); color: var(--gal-badge-ok-fg); }
.badge-bad { background: var(--gal-badge-bad-bg); color: var(--gal-badge-bad-fg); }
.badge-neutral { background: var(--gal-badge-neutral-bg); color: var(--gal-badge-neutral-fg); }
.na { color: var(--gal-na); }
.empty {
  padding: 2.5rem 1.5rem;
  text-align: center;
  color: var(--gal-muted);
}
.empty a.btn-primary { margin-top: 0.75rem; }
.pager {
  display: flex;
  gap: 0.35rem;
  align-items: center;
  justify-content: flex-end;
  padding: 0.75rem 0.5rem 0;
  color: var(--gal-muted);
}
.pager a, .pager span {
  padding: 0.3rem 0.55rem;
  border-radius: 6px;
  border: 1px solid var(--gal-border);
  background: var(--gal-surface);
  color: var(--gal-text);
}
.pager span.current {
  background: var(--gal-accent-soft);
  color: var(--gal-accent);
  border-color: #c9c5f5;
}
.detail-layout {
  display: grid;
  grid-template-columns: minmax(12rem, 28%) 1fr minmax(14rem, 32%);
  gap: 1rem;
  align-items: start;
}
.panel {
  background: var(--gal-surface);
  border: 1px solid var(--gal-border);
  border-radius: 10px;
  padding: 0.85rem 1rem;
  min-height: 12rem;
}
.span-tree { list-style: none; margin: 0; padding: 0; }
.span-tree a {
  display: block;
  padding: 0.4rem 0.55rem;
  border-radius: 8px;
  color: var(--gal-text);
  margin: 0.15rem 0;
}
.span-tree a[aria-current="true"] {
  background: var(--gal-accent-soft);
  color: var(--gal-accent);
  font-weight: 600;
  text-decoration: none;
}
.panel h2 { margin: 0 0 0.65rem; font-size: 1rem; }
.panel h3 {
  margin: 1rem 0 0.4rem;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--gal-muted);
  font-weight: 600;
}
.panel pre {
  white-space: pre-wrap;
  background: #fafafc;
  border: 1px solid var(--gal-border);
  border-radius: 8px;
  padding: 0.65rem 0.75rem;
  margin: 0.35rem 0 0.75rem;
  max-height: 18rem;
  overflow: auto;
}
.metric-list { list-style: none; margin: 0; padding: 0; }
.metric-list li {
  padding: 0.55rem 0;
  border-bottom: 1px solid var(--gal-border);
}
.metric-list li:last-child { border-bottom: 0; }
.metric-list .rationale {
  display: block;
  color: var(--gal-muted);
  font-size: 0.85rem;
  margin-top: 0.25rem;
}
.back { margin-bottom: 0.75rem; font-size: 0.9rem; }
.counters {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}
.counter {
  background: var(--gal-surface);
  border: 1px solid var(--gal-border);
  border-radius: 10px;
  padding: 1rem 1.25rem;
  min-width: 9rem;
}
.counter .n { font-size: 1.6rem; font-weight: 700; }
.counter .l { color: var(--gal-muted); font-size: 0.85rem; }
.chat-form textarea {
  width: 100%;
  min-height: 6rem;
  border: 1px solid var(--gal-border);
  border-radius: 8px;
  padding: 0.75rem;
  font: inherit;
  background: var(--gal-surface);
}
.chat-form button { margin-top: 0.75rem; }
.error { color: var(--gal-badge-bad-fg); }
#run-comparison { width: 100%; border-collapse: collapse; }
#run-comparison th, #run-comparison td {
  border-bottom: 1px solid var(--gal-border);
  padding: 0.55rem 0.7rem;
  text-align: left;
}
"""


def render_shell(
    *,
    title: str,
    active: NavKey,
    breadcrumb: str,
    main: str,
    header_action: str = "",
) -> str:
    action = header_action or (
        '<a class="btn-primary" href="/metrics">Configure Metrics</a>'
    )
    return (
        "<!DOCTYPE html>"
        '<html lang="en">'
        "<head>"
        '<meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{escape(title)}</title>"
        f"<style>{shell_css()}</style>"
        "</head>"
        "<body>"
        f"{_sidebar(active)}"
        '<div class="main">'
        '<header class="topbar">'
        f'<div class="breadcrumb">{breadcrumb}</div>'
        f"{action}"
        "</header>"
        f'<div class="content">{main}</div>'
        "</div>"
        "</body></html>"
    )


def _sidebar(active: NavKey) -> str:
    def item(key: NavKey, href: str, label: str) -> str:
        klass = "active" if active == key else ""
        return f'<a class="{klass}" href="{href}">{escape(label)}</a>'

    return (
        '<aside class="sidebar">'
        '<div class="brand">Galileo</div>'
        '<nav class="nav">'
        f'{item("home", "/overview", "Home")}'
        f'<div class="project">{escape(PROJECT_NAME)}</div>'
        '<div class="nav-section">'
        f'{item("overview", "/overview", "Overview")}'
        f'{item("logs", "/logs", f"Logs: {LOG_STREAM}")}'
        '<span class="soon">Playgrounds</span>'
        f'{item("experiments", "/experiments", "Experiments")}'
        "</div>"
        '<div class="nav-label">Workspace</div>'
        '<div class="nav-section">'
        '<span class="soon">Datasets</span>'
        '<span class="soon">Prompts</span>'
        '<span class="soon">Annotation Queues</span>'
        f'{item("metrics", "/metrics", "Metrics")}'
        '<span class="soon">Dashboards</span>'
        '<span class="soon">Controls</span>'
        "</div>"
        "</nav>"
        '<div class="sidebar-foot">'
        f'{item("chat", "/chat", "Chat")}'
        "</div>"
        "</aside>"
    )


def breadcrumb_logs() -> str:
    return (
        f'{escape(PROJECT_NAME)} &gt; '
        f'<strong>Log Stream: {escape(LOG_STREAM)}</strong>'
    )


def breadcrumb_plain(label: str) -> str:
    return f'{escape(PROJECT_NAME)} &gt; <strong>{escape(label)}</strong>'
