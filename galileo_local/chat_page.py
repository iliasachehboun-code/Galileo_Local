"""Minimal chat page for the standalone Agno agent."""

from __future__ import annotations

from html import escape

from galileo_local.settings import PROJECT_NAME


def render_chat_page(*, error: str = "", reply: str = "", message: str = "", session_id: str = "", trace_url: str = "") -> str:
    err = f'<p class="error">{escape(error)}</p>' if error else ""
    out = ""
    if reply:
        link = f'<p><a href="{escape(trace_url)}">Voir la trace et les métriques</a></p>' if trace_url else ""
        out = (
            '<section class="turn">'
            f"<h2>Vous</h2><pre>{escape(message)}</pre>"
            f"<h2>Agent</h2><pre>{escape(reply)}</pre>"
            f"{link}"
            "</section>"
        )
    return (
        "<!DOCTYPE html>"
        '<html lang="fr">'
        "<head>"
        '<meta charset="utf-8">'
        f"<title>{escape(PROJECT_NAME)} · chat</title>"
        "<style>"
        "body{margin:0;background:#f7f7f8;color:#1c1c1c;font:16px/1.45 'Segoe UI',sans-serif;}"
        "header{display:flex;gap:1.25rem;align-items:center;padding:.8rem 1.25rem;"
        "background:#fff;border-bottom:1px solid #e6e6e6;}"
        "header p{margin:0;}a{color:#5b21b6;}"
        "main{max-width:44rem;margin:1.5rem auto;padding:0 1rem;}"
        "form{background:#fff;border:1px solid #e6e6e6;border-radius:8px;padding:1rem;}"
        "textarea{width:100%;min-height:6rem;box-sizing:border-box;padding:.75rem;"
        "border:1px solid #d0d0d0;border-radius:8px;font:inherit;}"
        "button{margin-top:.75rem;background:#5b21b6;color:#fff;border:0;border-radius:8px;"
        "padding:.55rem 1rem;font:inherit;cursor:pointer;}"
        ".turn{margin-top:1.25rem;background:#fff;border:1px solid #e6e6e6;"
        "border-radius:8px;padding:1rem;}"
        "pre{white-space:pre-wrap;background:#fafafa;border:1px solid #eee;"
        "border-radius:8px;padding:.75rem;}"
        ".error{color:#b42318;}"
        "</style>"
        "</head>"
        "<body>"
        "<header>"
        f"<p>{escape(PROJECT_NAME)}</p>"
        '<p><a href="/">traces</a></p>'
        '<p><a href="/experiments">expériences</a></p>'
        "</header>"
        "<main>"
        "<h1>Chat</h1>"
        "<p>Un agent Agno. Chaque message crée une trace scorée sur la console.</p>"
        f"{err}"
        '<form method="post" action="/chat">'
        f'<input type="hidden" name="session_id" value="{escape(session_id)}">'
        f'<label for="message">Message</label>'
        f'<textarea id="message" name="message" required>{escape(message if not reply else "")}</textarea>'
        "<button type=\"submit\">Envoyer</button>"
        "</form>"
        f"{out}"
        "</main>"
        "</body></html>"
    )
