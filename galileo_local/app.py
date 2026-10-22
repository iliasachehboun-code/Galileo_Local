"""Local Galileo API, chat, and console.

``POST /v1/traces`` accepts a ``Trace``.
``POST /v1/chat`` and ``POST /chat`` run the Agno agent and store a clear-text trace.
``GET /`` serves the log stream console. ``GET /chat`` serves the chat page.
"""

from __future__ import annotations

import queue
import threading
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, FastAPI, Form, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse

from galileo_local.chat import ChatRequest, run_chat
from galileo_local.chat_page import render_chat_page
from galileo_local.console import render_console, render_experiments
from galileo_local.experiments import DuplicateRun, ExperimentCreate, MissingTrace
from galileo_local.models import Trace
from galileo_local.pii_oracle import find_clear_pii
from galileo_local.settings import (
    BIND_HOST,
    BIND_PORT,
    LOG_STREAM,
    PROJECT_NAME,
    is_usable_api_key,
    openai_api_key,
)
from galileo_local.store import TraceStore, default_db_path

router = APIRouter(prefix="/v1")


def get_store(request: Request) -> TraceStore:
    return request.app.state.store


StoreDep = Annotated[TraceStore, Depends(get_store)]


@router.post("/traces")
def post_trace(trace: Trace, request: Request, store: StoreDep) -> Trace:
    judge_later = bool(request.app.state.judge_async and request.app.state.judge_model is not None)
    store.save(trace, model=None if judge_later else request.app.state.judge_model)
    if judge_later:
        request.app.state.judge_queue.put(trace.request_id)
    return trace


@router.post("/chat")
def post_chat_api(body: ChatRequest, request: Request, store: StoreDep) -> dict[str, Any]:
    response, trace = _chat_turn(body.message, body.session_id, request)
    store.save(trace, model=None if request.app.state.judge_async else request.app.state.judge_model)
    if request.app.state.judge_async and request.app.state.judge_model is not None:
        request.app.state.judge_queue.put(trace.request_id)
    return response.model_dump()


@router.get("/traces/{request_id}/scores")
def get_trace_scores(request_id: str, store: StoreDep) -> dict[str, Any]:
    scores = store.scores_for(request_id)
    if scores is None:
        raise HTTPException(status_code=404, detail="trace not found")
    return {"request_id": request_id, "scores": scores}


@router.post("/experiments")
def post_experiment(body: ExperimentCreate, request: Request, store: StoreDep) -> dict[str, Any]:
    try:
        return store.create_experiment(
            body.name,
            list(body.request_ids),
            model=request.app.state.judge_model,
        )
    except MissingTrace:
        raise HTTPException(status_code=404, detail="trace not found") from None
    except DuplicateRun:
        raise HTTPException(status_code=409, detail="run already exists") from None
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None


@router.get("/experiments")
def get_experiment_comparison(
    store: StoreDep,
    left: str,
    right: str,
) -> dict[str, Any]:
    if not left.strip() or not right.strip():
        raise HTTPException(status_code=422, detail="two runs are required")
    body = store.compare_experiments(left, right)
    if body is None:
        raise HTTPException(status_code=404, detail="run not found")
    return body


@router.get("/experiments/{name}")
def get_experiment(name: str, store: StoreDep) -> dict[str, Any]:
    body = store.get_experiment(name)
    if body is None:
        raise HTTPException(status_code=404, detail="run not found")
    return body


@router.get("/traces/{request_id}")
def get_trace(request_id: str, store: StoreDep) -> Trace:
    body = store.get(request_id)
    if body is None:
        raise HTTPException(status_code=404, detail="trace not found")
    return Trace.model_validate(body)


def _public_loc(loc: object) -> list[Any]:
    items = list(loc) if isinstance(loc, (list, tuple)) else []
    return [item for item in items if not (isinstance(item, str) and find_clear_pii(item))]


def _validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
    detail: list[dict[str, Any]] = []
    for err in exc.errors():
        detail.append(
            {
                "type": err.get("type"),
                "loc": _public_loc(err.get("loc", ())),
                "msg": err.get("msg"),
            }
        )
    return JSONResponse(status_code=422, content={"detail": detail})


def _chat_turn(message: str, session_id: str, request: Request):
    try:
        return run_chat(message, session_id=session_id, model=request.app.state.chat_model)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def create_app(
    db_path: Path | None = None,
    *,
    judge_model: Any | None = None,
    chat_model: Any | None = None,
    judge_async: bool = False,
) -> FastAPI:
    application = FastAPI(title="galileo-local")
    application.state.store = TraceStore(db_path or default_db_path())
    application.state.judge_model = judge_model
    application.state.chat_model = chat_model
    application.state.judge_async = judge_async
    application.state.judge_queue = queue.Queue()
    application.add_exception_handler(RequestValidationError, _validation_error)
    application.include_router(router)

    @application.get("/", response_class=HTMLResponse)
    def console_index(trace: str | None = None, span: int | None = None) -> HTMLResponse:
        return HTMLResponse(
            render_console(application.state.store, selected=trace, span=span)
        )

    @application.get("/chat", response_class=HTMLResponse)
    def chat_get() -> HTMLResponse:
        return HTMLResponse(render_chat_page())

    @application.post("/chat", response_class=HTMLResponse)
    def chat_post(
        request: Request,
        store: StoreDep,
        message: str = Form(...),
        session_id: str = Form(""),
    ) -> HTMLResponse:
        try:
            response, trace = _chat_turn(message, session_id, request)
        except HTTPException as exc:
            return HTMLResponse(
                render_chat_page(error=str(exc.detail), message=message, session_id=session_id),
                status_code=exc.status_code,
            )
        store.save(trace, model=None if request.app.state.judge_async else request.app.state.judge_model)
        if request.app.state.judge_async and request.app.state.judge_model is not None:
            request.app.state.judge_queue.put(trace.request_id)
        return HTMLResponse(
            render_chat_page(
                reply=response.reply,
                message=message,
                session_id=response.session_id,
                trace_url=response.trace_url,
            )
        )

    @application.get("/experiments", response_class=HTMLResponse)
    def experiments_page(left: str | None = None, right: str | None = None) -> HTMLResponse:
        return HTMLResponse(
            render_experiments(application.state.store, left=left, right=right)
        )

    return application


app = create_app()


def _live_openai_model(*, temperature: float) -> Any | None:
    key = openai_api_key()
    if not is_usable_api_key(key):
        return None
    from agno.models.openai import OpenAIChat

    from galileo_local.settings import DEFAULT_MODEL

    return OpenAIChat(id=DEFAULT_MODEL, api_key=key, temperature=temperature)


def _judge_worker(application: FastAPI) -> None:
    store: TraceStore = application.state.store
    model = application.state.judge_model
    while True:
        request_id = application.state.judge_queue.get()
        try:
            body = store.get(request_id)
            if body is None:
                continue
            store.write_scores(Trace.model_validate(body), model, only_substantive=True)
        except Exception as exc:
            print(f"judge failed: {type(exc).__name__}", flush=True)
        finally:
            application.state.judge_queue.task_done()


def main() -> None:
    import uvicorn

    judge = _live_openai_model(temperature=0)
    chat = _live_openai_model(temperature=0.2)
    app.state.judge_model = judge
    app.state.chat_model = chat
    app.state.judge_async = judge is not None
    if judge is not None:
        threading.Thread(target=_judge_worker, args=(app,), daemon=True).start()
        stored = app.state.store.list_traces(project=PROJECT_NAME, log_stream=LOG_STREAM)
        for item in stored[-3:]:
            app.state.judge_queue.put(item["trace"]["request_id"])
    uvicorn.run(app, host=BIND_HOST, port=BIND_PORT)


if __name__ == "__main__":
    main()
