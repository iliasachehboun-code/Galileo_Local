"""Shared Galileo console chrome: sidebar, tokens, page shell."""

from __future__ import annotations

from html import escape

from galileo_local.settings import LOG_STREAM, PROJECT_NAME

NavKey = str  # home | overview | logs | experiments | metrics | chat | trends


def shell_css() -> str:
    return """
@import url("https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap");
:root {
  --gal-bg: #f4f5f8;
  --gal-surface: #ffffff;
  --gal-sidebar: #fafafb;
  --gal-border: #e8e8ee;
  --gal-border-strong: #d8d8e2;
  --gal-text: #111827;
  --gal-muted: #6b7280;
  --gal-accent: #6d28d9;
  --gal-accent-hover: #5b21b6;
  --gal-accent-soft: #f3eefe;
  --gal-accent-edge: #8b5cf6;
  --gal-nav-active-bg: #eef2ff;
  --gal-nav-active-border: #6366f1;
  --gal-row-hover: #f9fafb;
  --gal-badge-ok-bg: #def7ec;
  --gal-badge-ok-fg: #03543f;
  --gal-badge-bad-bg: #fde8e8;
  --gal-badge-bad-fg: #9b1c1c;
  --gal-badge-neutral-bg: #f3f4f6;
  --gal-badge-neutral-fg: #4b5563;
  --gal-na: #9ca3af;
  --gal-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
}
* { box-sizing: border-box; }
body {
  margin: 0;
  min-height: 100vh;
  display: flex;
  background: var(--gal-bg);
  color: var(--gal-text);
  font: 13.5px/1.45 "IBM Plex Sans", "Segoe UI", system-ui, sans-serif;
  -webkit-font-smoothing: antialiased;
}
a { color: var(--gal-accent); text-decoration: none; }
a:hover { text-decoration: underline; }
.sidebar {
  width: 232px;
  flex: none;
  background: var(--gal-sidebar);
  border-right: 1px solid var(--gal-border);
  display: flex;
  flex-direction: column;
  padding: 0.85rem 0.55rem 0.75rem;
  min-height: 100vh;
  position: sticky;
  top: 0;
  align-self: flex-start;
  max-height: 100vh;
  overflow: auto;
}
.brand {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 700;
  font-size: 1.05rem;
  letter-spacing: -0.03em;
  color: var(--gal-text);
  padding: 0.4rem 0.7rem 0.95rem;
}
.brand-mark {
  width: 18px;
  height: 18px;
  border-radius: 5px;
  background: linear-gradient(135deg, #ef4444 0%, #f97316 55%, #a855f7 100%);
  box-shadow: 0 0 0 1px rgba(0,0,0,0.06);
  flex: none;
}
.nav-section { margin-bottom: 0.35rem; }
.nav-label {
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--gal-muted);
  padding: 0.65rem 0.7rem 0.25rem;
  font-weight: 600;
}
.nav a, .nav span.soon {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.42rem 0.7rem;
  border-radius: 7px;
  color: var(--gal-text);
  margin: 0.08rem 0.15rem;
  border-left: 3px solid transparent;
  font-weight: 500;
}
.nav a:hover { background: #f3f4f6; text-decoration: none; }
.nav a.active {
  background: var(--gal-nav-active-bg);
  color: var(--gal-nav-active-border);
  font-weight: 600;
  text-decoration: none;
  border-left-color: var(--gal-nav-active-border);
  border-radius: 0 7px 7px 0;
  margin-left: 0;
  padding-left: calc(0.7rem + 3px);
}
.nav span.soon {
  color: var(--gal-na);
  cursor: default;
  font-weight: 400;
}
.nav .project {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
  padding: 0.35rem 0.7rem 0.2rem;
  color: var(--gal-text);
  font-size: 0.92rem;
}
.nav .project .chev {
  color: var(--gal-muted);
  font-size: 0.7rem;
}
.sidebar-foot {
  margin-top: auto;
  padding: 0.75rem 0.45rem 0.15rem;
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
  padding: 0.7rem 1.35rem;
  background: var(--gal-surface);
  border-bottom: 1px solid var(--gal-border);
  position: sticky;
  top: 0;
  z-index: 20;
}
.topbar-right {
  display: flex;
  align-items: center;
  gap: 0.65rem;
}
.breadcrumb {
  color: var(--gal-muted);
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 0.35rem;
  flex-wrap: wrap;
}
.breadcrumb strong { color: var(--gal-text); font-weight: 600; }
.breadcrumb .stream-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  border: 1px solid transparent;
  border-radius: 6px;
  padding: 0.1rem 0.25rem;
}
.user-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  color: var(--gal-muted);
  font-size: 0.8rem;
  padding: 0.25rem 0.45rem;
  border-radius: 999px;
  border: 1px solid var(--gal-border);
  background: #fff;
}
.user-avatar {
  width: 20px;
  height: 20px;
  border-radius: 999px;
  background: #ede9fe;
  color: var(--gal-accent);
  display: grid;
  place-items: center;
  font-size: 0.65rem;
  font-weight: 700;
}
.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  background: var(--gal-accent);
  color: #fff !important;
  border: 0;
  border-radius: 8px;
  padding: 0.48rem 0.95rem;
  font: inherit;
  font-weight: 600;
  text-decoration: none !important;
  cursor: pointer;
  box-shadow: var(--gal-shadow);
}
.btn-primary:hover { background: var(--gal-accent-hover); }
.btn-ghost {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  border: 1px solid var(--gal-border);
  background: #fff;
  color: var(--gal-text);
  border-radius: 8px;
  padding: 0.42rem 0.75rem;
  font: inherit;
  font-weight: 500;
  text-decoration: none;
  cursor: pointer;
}
.btn-ghost:hover { background: #f9fafb; text-decoration: none; }
.btn-ghost[disabled], .btn-ghost.is-disabled {
  opacity: 0.45;
  cursor: not-allowed;
  pointer-events: none;
}
.content { padding: 0.85rem 1.25rem 1.75rem; flex: 1; }
.page-tabs {
  display: flex;
  gap: 0.1rem;
  border-bottom: 1px solid var(--gal-border);
  margin-bottom: 0.85rem;
  overflow-x: auto;
}
.page-tabs a, .page-tabs span {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.65rem 0.8rem;
  color: var(--gal-muted);
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  white-space: nowrap;
  font-weight: 500;
}
.page-tabs a:hover { color: var(--gal-text); text-decoration: none; }
.page-tabs a.active {
  color: var(--gal-accent);
  border-bottom-color: var(--gal-accent);
  font-weight: 600;
}
.page-tabs span.disabled { color: #c4c4d0; }
.tab-ico { font-size: 0.85rem; opacity: 0.85; }
.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  align-items: center;
  margin-bottom: 0.75rem;
}
.chip {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.38rem 0.7rem;
  border-radius: 8px;
  border: 1px solid var(--gal-border-strong);
  background: var(--gal-surface);
  color: var(--gal-text);
  font: inherit;
  font-weight: 500;
  text-decoration: none;
  box-shadow: var(--gal-shadow);
}
.chip:hover { background: #fafafa; text-decoration: none; }
.chip.active {
  background: var(--gal-accent-soft);
  border-color: #d8cfff;
  color: var(--gal-accent);
  font-weight: 600;
}
.chip .count {
  color: var(--gal-muted);
  font-weight: 500;
  font-size: 0.85em;
}
.chip.active .count { color: var(--gal-accent); }
.search-wrap {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 0.45rem;
}
.search {
  border: 1px solid var(--gal-border-strong);
  border-radius: 8px;
  padding: 0.4rem 0.75rem 0.4rem 2rem;
  font: inherit;
  min-width: 16rem;
  background: var(--gal-surface) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='14' fill='none' stroke='%239ca3af' stroke-width='2' viewBox='0 0 24 24'%3E%3Ccircle cx='11' cy='11' r='7'/%3E%3Cpath d='M20 20l-3-3'/%3E%3C/svg%3E") 0.6rem 50% no-repeat;
  box-shadow: var(--gal-shadow);
}
.surface {
  background: var(--gal-surface);
  border: 1px solid var(--gal-border);
  border-radius: 10px;
  overflow: auto;
  box-shadow: var(--gal-shadow);
}
table.logs {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  font-size: 0.86rem;
}
table.logs th {
  text-align: left;
  font-weight: 600;
  color: #4b5563;
  padding: 0.55rem 0.7rem;
  border-bottom: 1px solid var(--gal-border);
  white-space: nowrap;
  background: #fcfcfd;
  position: sticky;
  top: 0;
  z-index: 5;
  font-size: 0.78rem;
}
table.logs th .sort {
  color: #d1d5db;
  margin-left: 0.2rem;
  font-size: 0.65rem;
}
table.logs th .ai {
  display: inline-block;
  width: 12px;
  height: 12px;
  margin-right: 0.28rem;
  vertical-align: -1px;
  background: radial-gradient(circle at 30% 30%, #c4b5fd, #7c3aed 70%);
  border-radius: 3px;
  box-shadow: 0 0 0 1px rgba(109, 40, 217, 0.2);
}
table.logs th .agg {
  display: block;
  font-size: 0.65rem;
  font-weight: 500;
  color: var(--gal-na);
  margin-top: 0.1rem;
}
table.logs td {
  padding: 0.55rem 0.7rem;
  border-bottom: 1px solid #f0f0f5;
  vertical-align: middle;
  max-width: 15rem;
  color: #1f2937;
}
table.logs tbody tr { height: 48px; transition: background 0.1s ease; }
table.logs tbody tr:hover { background: var(--gal-row-hover); }
table.logs tbody tr[aria-current="true"] { background: #f5f3ff; }
table.logs a.row-link {
  color: inherit;
  text-decoration: none;
  display: block;
}
table.logs input[type="checkbox"] {
  width: 14px;
  height: 14px;
  accent-color: var(--gal-accent);
}
.clip {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 13rem;
}
.badge {
  display: inline-block;
  padding: 0.12rem 0.5rem;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 600;
  line-height: 1.35;
  letter-spacing: 0.01em;
}
.badge-ok { background: var(--gal-badge-ok-bg); color: var(--gal-badge-ok-fg); }
.badge-bad { background: var(--gal-badge-bad-bg); color: var(--gal-badge-bad-fg); }
.badge-neutral { background: var(--gal-badge-neutral-bg); color: var(--gal-badge-neutral-fg); }
.na { color: var(--gal-na); }
.empty {
  padding: 3rem 1.5rem;
  text-align: center;
  color: var(--gal-muted);
}
.empty a.btn-primary { margin-top: 0.85rem; }
.pager {
  display: flex;
  gap: 0.3rem;
  align-items: center;
  justify-content: center;
  padding: 0.9rem 0.5rem 0.2rem;
  color: var(--gal-muted);
}
.pager a, .pager span {
  min-width: 2rem;
  text-align: center;
  padding: 0.28rem 0.5rem;
  border-radius: 7px;
  border: 1px solid var(--gal-border);
  background: var(--gal-surface);
  color: var(--gal-text);
  font-weight: 500;
}
.pager a:hover { background: #f9fafb; text-decoration: none; }
.pager span.current {
  background: var(--gal-accent);
  color: #fff;
  border-color: var(--gal-accent);
}
.detail-layout {
  display: grid;
  grid-template-columns: minmax(12rem, 24%) 1fr minmax(15rem, 30%);
  gap: 0.85rem;
  align-items: start;
}
.panel {
  background: var(--gal-surface);
  border: 1px solid var(--gal-border);
  border-radius: 10px;
  padding: 0.85rem 1rem;
  min-height: 12rem;
  box-shadow: var(--gal-shadow);
}
.span-tree { list-style: none; margin: 0; padding: 0; }
.span-tree a {
  display: block;
  padding: 0.4rem 0.55rem;
  border-radius: 7px;
  color: var(--gal-text);
  margin: 0.12rem 0;
  font-weight: 500;
}
.span-tree a:hover { background: #f3f4f6; text-decoration: none; }
.span-tree a[aria-current="true"] {
  background: var(--gal-nav-active-bg);
  color: var(--gal-nav-active-border);
  font-weight: 600;
  text-decoration: none;
}
.panel h2 { margin: 0 0 0.65rem; font-size: 0.98rem; }
.panel h3 {
  margin: 1rem 0 0.4rem;
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
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
  font-size: 0.85rem;
}
.metric-list { list-style: none; margin: 0; padding: 0; }
.metric-list li {
  padding: 0.55rem 0;
  border-bottom: 1px solid #f0f0f5;
}
.metric-list li:last-child { border-bottom: 0; }
.metric-list .rationale {
  display: block;
  color: var(--gal-muted);
  font-size: 0.82rem;
  margin-top: 0.25rem;
}
.metrics-form { max-width: 52rem; }
.metrics-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
  margin: 0.75rem 0 1rem;
}
.metrics-saved {
  background: var(--gal-badge-ok-bg);
  color: var(--gal-badge-ok-fg);
  border-radius: 8px;
  padding: 0.55rem 0.85rem;
  font-weight: 600;
}
.metric-family {
  background: var(--gal-surface);
  border: 1px solid var(--gal-border);
  border-radius: 10px;
  padding: 0.85rem 1rem 0.55rem;
  margin-bottom: 0.85rem;
  box-shadow: var(--gal-shadow);
}
.metric-family h2 {
  margin: 0 0 0.65rem;
  font-size: 0.95rem;
}
.metric-toggles { display: grid; gap: 0.35rem; }
.metric-toggle {
  display: grid;
  grid-template-columns: 42px 1fr;
  gap: 0.65rem;
  align-items: center;
  padding: 0.45rem 0.35rem;
  border-radius: 8px;
  cursor: pointer;
}
.metric-toggle:hover { background: #f9fafb; }
.metric-toggle input {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}
.metric-toggle-ui {
  width: 40px;
  height: 22px;
  border-radius: 999px;
  background: #d1d5db;
  position: relative;
  transition: background 0.15s ease;
}
.metric-toggle-ui::after {
  content: "";
  position: absolute;
  top: 2px;
  left: 2px;
  width: 18px;
  height: 18px;
  border-radius: 999px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(0,0,0,0.15);
  transition: transform 0.15s ease;
}
.metric-toggle input:checked + .metric-toggle-ui {
  background: var(--gal-accent);
}
.metric-toggle input:checked + .metric-toggle-ui::after {
  transform: translateX(18px);
}
.metric-toggle-body {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}
.metric-toggle-body strong { font-weight: 600; }
.back { margin-bottom: 0.75rem; font-size: 0.88rem; }
.counters {
  display: flex;
  gap: 0.85rem;
  flex-wrap: wrap;
}
.counter {
  background: var(--gal-surface);
  border: 1px solid var(--gal-border);
  border-radius: 10px;
  padding: 1rem 1.15rem;
  min-width: 9rem;
  box-shadow: var(--gal-shadow);
}
.counter .n { font-size: 1.55rem; font-weight: 700; letter-spacing: -0.02em; }
.counter .l { color: var(--gal-muted); font-size: 0.82rem; margin-top: 0.15rem; }
.trends-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.85rem;
}
.trend-card {
  background: var(--gal-surface);
  border: 1px solid var(--gal-border);
  border-radius: 10px;
  padding: 0.9rem 1rem 0.75rem;
  box-shadow: var(--gal-shadow);
}
.trend-card .title { font-weight: 600; font-size: 0.88rem; }
.trend-card .value {
  font-size: 1.35rem;
  font-weight: 700;
  margin: 0.35rem 0 0.55rem;
  display: flex;
  align-items: baseline;
  gap: 0.4rem;
}
.trend-card .value .pill {
  font-size: 0.65rem;
  font-weight: 600;
  color: var(--gal-muted);
  background: #f3f4f6;
  border-radius: 999px;
  padding: 0.12rem 0.4rem;
}
.spark {
  height: 56px;
  border-radius: 6px;
  background:
    linear-gradient(180deg, transparent 0%, transparent 49%, #eef2ff 49%, #eef2ff 51%, transparent 51%),
    linear-gradient(90deg, #e5e7eb 1px, transparent 1px);
  background-size: 100% 100%, 20% 100%;
  position: relative;
  overflow: hidden;
}
.spark svg { width: 100%; height: 100%; display: block; }
.subtabs {
  display: flex;
  gap: 1rem;
  margin: 0.35rem 0 0.95rem;
  color: var(--gal-muted);
  font-weight: 500;
}
.subtabs .on { color: var(--gal-text); font-weight: 700; }
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
@media (max-width: 1100px) {
  .trends-grid { grid-template-columns: 1fr 1fr; }
  .detail-layout { grid-template-columns: 1fr; }
}
@media (max-width: 720px) {
  body { flex-direction: column; }
  .sidebar { width: 100%; max-height: none; position: static; }
  .trends-grid { grid-template-columns: 1fr; }
  .search { min-width: 10rem; }
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
        '<div class="topbar-right">'
        f"{action}"
        '<span class="user-chip" title="Local console">'
        '<span class="user-avatar">G</span>local</span>'
        "</div>"
        "</header>"
        f'<div class="content">{main}</div>'
        "</div>"
        "</body></html>"
    )


def _sidebar(active: NavKey) -> str:
    def item(key: NavKey, href: str, label: str, ico: str = "") -> str:
        klass = "active" if active == key else ""
        prefix = f'<span class="tab-ico" aria-hidden="true">{ico}</span>' if ico else ""
        return f'<a class="{klass}" href="{href}">{prefix}{escape(label)}</a>'

    logs_active = active in {"logs", "trends"}
    logs_klass = "active" if logs_active else ""

    return (
        '<aside class="sidebar">'
        '<div class="brand"><span class="brand-mark" aria-hidden="true"></span>Galileo</div>'
        '<nav class="nav">'
        f'{item("home", "/overview", "Home", "⌂")}'
        f'<div class="project">{escape(PROJECT_NAME)}'
        '<span class="chev" aria-hidden="true">▾</span></div>'
        '<div class="nav-section">'
        f'{item("overview", "/overview", "Overview")}'
        f'<a class="{logs_klass}" href="/logs">'
        f'<span class="tab-ico" aria-hidden="true">☰</span>'
        f'Logs: {escape(LOG_STREAM)}</a>'
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
        f'{item("chat", "/chat", "Chat", "💬")}'
        "</div>"
        "</aside>"
    )


def breadcrumb_logs() -> str:
    return (
        f'<span>{escape(PROJECT_NAME)}</span>'
        '<span aria-hidden="true">›</span>'
        f'<span class="stream-pill"><strong>Log Stream: {escape(LOG_STREAM)}</strong>'
        '<span aria-hidden="true">▾</span></span>'
    )


def breadcrumb_plain(label: str) -> str:
    return (
        f'<span>{escape(PROJECT_NAME)}</span>'
        '<span aria-hidden="true">›</span>'
        f'<strong>{escape(label)}</strong>'
    )
