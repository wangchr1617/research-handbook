"""FastAPI 入口：uvicorn demo.main:app --host 127.0.0.1 --port 8000。"""
import asyncio
import json
import logging
import time
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from sqlalchemy import delete, select, text
from sqlalchemy.exc import IntegrityError

from .config import settings
from .db import Attachment, Conversation, Login, Message, Run, RunEvent, session
from .jobs import TERMINAL, add_event, cancel
from .schemas import ConversationInput, Credentials, RunInput
from .security import CurrentUser, authenticate, digest, own_conversation

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("demo.api")
app = FastAPI(title="Agent 后端教学 Demo")


@app.middleware("http")
async def boundary(request: Request, call_next):
    request.state.request_id = uuid.uuid4().hex
    start = time.monotonic()
    # 快速拒绝显式大请求；chunked/multipart 的总量还需入口代理限制。
    length = request.headers.get("content-length")
    if length and (not length.isdigit() or int(length) > 131072):
        return JSONResponse({"code": "request_too_large"}, status_code=413)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store"
    logger.info("http request_id=%s method=%s status=%s duration_ms=%.1f",
                request.state.request_id, request.method, response.status_code,
                (time.monotonic() - start) * 1000)
    return response


@app.exception_handler(HTTPException)
async def http_error(request, exc):
    return JSONResponse({"code": exc.detail, "request_id": request.state.request_id},
                        status_code=exc.status_code, headers=exc.headers)


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    return JSONResponse({"code": "validation", "request_id": request.state.request_id,
                         "fields": [list(e["loc"]) for e in exc.errors()]}, status_code=422)


@app.exception_handler(Exception)
async def unexpected_error(request, exc):
    logger.error("unhandled request_id=%s", request.state.request_id,
                 exc_info=(type(exc), exc, exc.__traceback__))
    return JSONResponse({"code": "internal_error", "request_id": request.state.request_id}, status_code=500)


@app.get("/")
def index():
    return FileResponse(Path(__file__).with_name("static") / "index.html")


@app.get("/health/live")
def live():
    return {"status": "ok"}


@app.get("/health/ready")
def ready():
    try:
        with session() as db:
            db.execute(text("SELECT 1"))
        from redis import Redis
        Redis.from_url(settings().broker_url, socket_connect_timeout=1, socket_timeout=1).ping()
    except Exception:
        raise HTTPException(503, "dependency_unavailable") from None
    return {"status": "ready"}


@app.post("/api/auth/login")
def login(body: Credentials):
    return authenticate(body.username, body.password)


@app.post("/api/auth/logout", status_code=204)
def logout(request: Request, user: CurrentUser):
    token = request.headers["authorization"].split(" ", 1)[1]
    with session() as db:
        db.execute(delete(Login).where(Login.token_hash == digest(token), Login.user_id == user))
        db.commit()


@app.post("/api/conversations", status_code=201)
def create_conversation(body: ConversationInput, user: CurrentUser):
    with session() as db:
        item = Conversation(title=body.title, user_id=user)
        db.add(item)
        db.commit()
        return {"id": item.id, "title": item.title}


@app.get("/api/conversations")
def conversations(user: CurrentUser, before: float | None = None,
                  limit: Annotated[int, Query(ge=1, le=100)] = 20):
    with session() as db:
        query = select(Conversation).where(Conversation.user_id == user)
        if before is not None:
            query = query.where(Conversation.created_at < before)
        rows = db.scalars(query.order_by(Conversation.created_at.desc(), Conversation.id.desc()).limit(limit))
        return [{"id": row.id, "title": row.title, "created_at": row.created_at} for row in rows]


@app.get("/api/conversations/{conversation_id}/messages")
def messages(conversation_id: str, user: CurrentUser,
             before: Annotated[int | None, Query(ge=1)] = None,
             limit: Annotated[int, Query(ge=1, le=100)] = 50):
    with session() as db:
        own_conversation(db, conversation_id, user)
        query = select(Message).where(Message.conversation_id == conversation_id)
        if before is not None:
            query = query.where(Message.id < before)
        rows = list(db.scalars(query.order_by(Message.id.desc()).limit(limit)))
        return [{"id": row.id, "run_id": row.run_id, "role": row.role, "content": row.content}
                for row in reversed(rows)]


@app.post("/api/conversations/{conversation_id}/files", status_code=201)
def upload(conversation_id: str, user: CurrentUser, file: Annotated[UploadFile, File()]):
    with session() as db:
        own_conversation(db, conversation_id, user)
        # 文件名仅用于展示，不参与磁盘路径。只接收小型 UTF-8 文本。
        name = Path((file.filename or "").replace("\\", "/")).name
        if Path(name).suffix.lower() not in {".txt", ".md"} or len(name) > 120:
            raise HTTPException(415, "text_file_required")
        data = file.file.read(settings().upload_bytes + 1)
        if len(data) > settings().upload_bytes:
            raise HTTPException(413, "file_too_large")
        try:
            content = data.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(415, "utf8_required") from None
        if "\x00" in content:
            raise HTTPException(415, "text_file_required")
        item = Attachment(conversation_id=conversation_id, filename=name, content=content)
        db.add(item)
        db.commit()
        return {"id": item.id, "filename": item.filename, "bytes": len(data)}


def run_view(run):
    return {"id": run.id, "conversation_id": run.conversation_id, "status": run.status,
            "attempt": run.attempt, "error_code": run.error_code,
            "cancel_requested": run.cancel_requested}


@app.get("/api/conversations/{conversation_id}/runs")
def list_runs(conversation_id: str, user: CurrentUser):
    with session() as db:
        own_conversation(db, conversation_id, user)
        return [run_view(run) for run in db.scalars(select(Run)
                .where(Run.conversation_id == conversation_id).order_by(Run.created_at.desc()).limit(20))]


def checked_run(db, run_id, owner):
    run = db.get(Run, run_id)
    if run is None:
        raise HTTPException(404, "not_found")
    own_conversation(db, run.conversation_id, owner)
    return run


def same_request(run, body):
    return (run.prompt, run.attachment_id, run.timeout_seconds, run.mode) == (
        body.prompt, body.attachment_id, body.timeout_seconds, body.mode)


@app.post("/api/conversations/{conversation_id}/runs", status_code=202)
def submit(conversation_id: str, body: RunInput, request: Request, user: CurrentUser):
    with session() as db:
        own_conversation(db, conversation_id, user)
        if body.attachment_id:
            attachment = db.get(Attachment, body.attachment_id)
            if not attachment or attachment.conversation_id != conversation_id:
                raise HTTPException(404, "not_found")
        existing = db.scalar(select(Run).where(Run.conversation_id == conversation_id,
                                               Run.client_key == body.client_key))
        if existing:
            if not same_request(existing, body):
                raise HTTPException(409, "idempotency_conflict")
            return run_view(existing)
        run = Run(conversation_id=conversation_id, request_id=request.state.request_id, **body.model_dump())
        db.add(run)
        try:
            db.flush()
            db.add(Message(conversation_id=conversation_id, run_id=run.id, role="user", content=body.prompt))
            add_event(db, run.id, "status", {"status": "queued"})
            db.commit()
        except IntegrityError:
            db.rollback()
            existing = db.scalar(select(Run).where(Run.conversation_id == conversation_id,
                                                   Run.client_key == body.client_key))
            if existing is None or not same_request(existing, body):
                raise HTTPException(409, "idempotency_conflict") from None
            return run_view(existing)
        result = run_view(run)
    # 即使这里进程退出或 broker 暂不可用，dispatcher 也会按库内意图补投。
    try:
        from .worker import enqueue
        enqueue(run.id)
    except Exception:
        logger.warning("enqueue_deferred request_id=%s run_id=%s", request.state.request_id, run.id)
    return result


@app.get("/api/runs/{run_id}")
def get_run(run_id: str, user: CurrentUser):
    with session() as db:
        return run_view(checked_run(db, run_id, user))


@app.post("/api/runs/{run_id}/cancel", status_code=202)
def cancel_run(run_id: str, user: CurrentUser):
    with session() as db:
        checked_run(db, run_id, user)
    cancel(run_id)
    with session() as db:
        return run_view(checked_run(db, run_id, user))


def event_page(run_id, owner, token_hash, after):
    # 每轮重新创建短事务，同时复查登录是否被撤销；不跨 yield 持有数据库连接。
    with session() as db:
        login = db.get(Login, token_hash)
        if not login or login.expires_at <= time.time() or login.user_id != owner:
            return None
        run = checked_run(db, run_id, owner)
        rows = db.scalars(select(RunEvent).where(RunEvent.run_id == run_id, RunEvent.id > after)
                          .order_by(RunEvent.id).limit(100))
        return run.status, [(row.id, row.kind, row.data) for row in rows]


@app.get("/api/runs/{run_id}/events")
async def events(run_id: str, request: Request, user: CurrentUser,
                 after: Annotated[int, Query(ge=0)] = 0):
    token_hash = digest(request.headers["authorization"].split(" ", 1)[1])
    initial = await asyncio.to_thread(event_page, run_id, user, token_hash, after)
    if initial is None:
        raise HTTPException(401, "unauthenticated")

    async def chunks():
        cursor, last_heartbeat = after, time.monotonic()
        try:
            while not await request.is_disconnected():
                page = await asyncio.to_thread(event_page, run_id, user, token_hash, cursor)
                if page is None:
                    yield 'event: error\ndata: {"code":"unauthenticated"}\n\n'
                    return
                status, rows = page
                for event_id, kind, data in rows:
                    cursor = event_id
                    yield f"id: {event_id}\nevent: {kind}\ndata: {data}\n\n"
                # 最后一页不足 100 条时才结束，避免终态截掉待重放事件。
                if status in TERMINAL and len(rows) < 100:
                    return
                if time.monotonic() - last_heartbeat > 10:
                    yield ": heartbeat\n\n"
                    last_heartbeat = time.monotonic()
                await asyncio.sleep(.2)
        except asyncio.CancelledError:
            raise
    return StreamingResponse(chunks(), media_type="text/event-stream",
                             headers={"X-Accel-Buffering": "no", "Cache-Control": "no-store"})
