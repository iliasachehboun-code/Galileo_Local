"""Runtime settings for the standalone galileo-local app."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_NAME = "galileo-local"
LOG_STREAM = "chat"
CHAT_TRACE_NAME = "chat_agent"
DEFAULT_MODEL = "gpt-4o-mini"
BIND_HOST = os.environ.get("GALILEO_BIND_HOST", "127.0.0.1")
BIND_PORT = int(os.environ.get("GALILEO_BIND_PORT", "8090"))


def _env_file() -> Path:
    return Path(__file__).resolve().parent.parent / ".env"


_KEY_NAMES = frozenset({"OPENAI_API_KEY", "GALILEO_OPENAI_API_KEY"})


def load_dotenv() -> None:
    path = _env_file()
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        name, value = stripped.split("=", 1)
        name = name.strip()
        cleaned = value.strip().strip('"').strip("'")
        # Keys from .env win over a stale User/Machine OPENAI_API_KEY.
        if name in _KEY_NAMES:
            if is_usable_api_key(cleaned):
                os.environ[name] = cleaned
            continue
        if name in os.environ:
            continue
        os.environ[name] = cleaned


def openai_api_key() -> str:
    load_dotenv()
    file_key = ""
    path = _env_file()
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("OPENAI_API_KEY=") or stripped.startswith(
                "GALILEO_OPENAI_API_KEY="
            ):
                candidate = stripped.split("=", 1)[1].strip().strip('"').strip("'")
                if is_usable_api_key(candidate):
                    file_key = candidate
                    break
    if file_key:
        return file_key
    return (
        os.environ.get("OPENAI_API_KEY", "").strip()
        or os.environ.get("GALILEO_OPENAI_API_KEY", "").strip()
    )


def is_usable_api_key(key: str) -> bool:
    text = (key or "").strip()
    lowered = text.lower()
    if len(text) < 20 or not text.startswith("sk-"):
        return False
    if any(
        marker in lowered
        for marker in ("replace", "your_openai", "your-api-key", "changeme", "example")
    ):
        return False
    return not (lowered.endswith("_key") and lowered.startswith("sk-"))
