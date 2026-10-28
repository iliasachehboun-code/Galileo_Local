"""Chat page inside the Galileo console shell."""

from __future__ import annotations

from html import escape

from galileo_local.ui_shell import breadcrumb_plain, render_shell


def render_chat_page(
    *,
    error: str = "",
    reply: str = "",
    message: str = "",
    session_id: str = "",
    trace_url: str = "",
) -> str:
    err = f'<p class="error">{escape(error)}</p>' if error else ""
    out = ""
    if reply:
        link = ""
        if trace_url:
            href = escape(trace_url)
            if href.startswith("/?trace="):
                rid = href.split("trace=", 1)[1]
                href = f"/logs/traces/{rid}"
            link = f'<p><a href="{href}">View in Logs</a></p>'
        out = (
            '<section class="panel turn" style="margin-top:1rem">'
            f"<h2>You</h2><pre>{escape(message)}</pre>"
            f"<h2>Agent</h2><pre>{escape(reply)}</pre>"
            f"{link}"
            "</section>"
        )
    main = (
        "<h1>Chat</h1>"
        "<p>Generate traffic for the Log stream. Each message stores a scored trace.</p>"
        f"{err}"
        '<form class="chat-form panel" method="post" action="/chat">'
        f'<input type="hidden" name="session_id" value="{escape(session_id)}">'
        f'<label for="message">Message</label>'
        f'<textarea id="message" name="message" required>'
        f'{escape(message if not reply else "")}</textarea>'
        '<button class="btn-primary" type="submit">Send</button>'
        "</form>"
        f"{out}"
    )
    return render_shell(
        title="Galileo · Chat",
        active="chat",
        breadcrumb=breadcrumb_plain("Chat"),
        main=main,
        header_action='<a class="btn-primary" href="/logs">View in Logs</a>',
    )
