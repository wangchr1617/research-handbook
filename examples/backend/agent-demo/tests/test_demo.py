"""运行：python -m pytest -q。临时 SQLite 数据库；不接触原项目账号和数据。"""
import asyncio
import json
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, update

from demo.config import settings
from demo.db import Attachment, Base, Login, Message, Run, RunEvent, User, engine, session
from demo.jobs import StopRun, claim, dispatch_once, execute, finish, publish
from demo.main import app, event_page
from demo.security import digest, passwords


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("DEMO_DATABASE_URL", "sqlite:///" + str(tmp_path / "demo.db"))
    monkeypatch.setenv("DEMO_BROKER_URL", "memory://")
    settings.cache_clear()
    engine.cache_clear()
    Base.metadata.create_all(engine())
    with session() as db:
        for name in ["alice", "bobby"]:
            db.add(User(username=name, password_hash=passwords.hash("test-password-1234")))
        db.commit()
    from demo import worker
    sent = []
    monkeypatch.setattr(worker, "enqueue", sent.append)
    with TestClient(app) as client:
        tokens = {}
        for name in ["alice", "bobby"]:
            result = client.post("/api/auth/login", json={"username": name, "password": "test-password-1234"})
            assert result.status_code == 200
            tokens[name] = {"Authorization": "Bearer " + result.json()["access_token"]}
        yield client, tokens, sent
    engine().dispose()
    engine.cache_clear()
    settings.cache_clear()


def conversation(env, name="alice"):
    client, headers, _ = env
    result = client.post("/api/conversations", headers=headers[name], json={"title": "研究笔记"})
    assert result.status_code == 201
    return result.json()["id"]


def submit(env, conversation_id, **kwargs):
    client, headers, _ = env
    result = client.post(f"/api/conversations/{conversation_id}/runs", headers=headers["alice"],
                         json={"prompt": "hello science", "client_key": "request-0001", **kwargs})
    assert result.status_code == 202, result.text
    return result.json()["id"]


def test_login_logout_and_validation(env):
    client, headers, _ = env
    assert client.get("/api/conversations").status_code == 401
    assert client.post("/api/auth/login", json={"username": "alice", "password": "wrong-password-123"}).status_code == 401
    cid = conversation(env)
    for invalid in [{"timeout_seconds": "5"}, {"timeout_seconds": 100}, {"unknown": 1}]:
        result = client.post(f"/api/conversations/{cid}/runs", headers=headers["alice"],
                             json={"prompt": "hi", "client_key": "request-0001", **invalid})
        assert result.status_code == 422
        assert "input" not in result.json()
    assert client.post("/api/auth/logout", headers=headers["alice"]).status_code == 204
    assert client.get("/api/conversations", headers=headers["alice"]).status_code == 401


def test_resource_ownership(env):
    client, headers, _ = env
    cid = conversation(env)
    rid = submit(env, cid)
    for path in [f"/api/conversations/{cid}/messages", f"/api/conversations/{cid}/runs",
                 f"/api/runs/{rid}", f"/api/runs/{rid}/events"]:
        assert client.get(path, headers=headers["bobby"]).status_code == 404
    assert client.post(f"/api/runs/{rid}/cancel", headers=headers["bobby"]).status_code == 404
    assert client.post(f"/api/conversations/{cid}/files", headers=headers["bobby"],
                       files={"file": ("a.txt", b"abc")}).status_code == 404


def test_upload_and_attachment_scope(env):
    client, headers, _ = env
    cid = conversation(env)
    result = client.post(f"/api/conversations/{cid}/files", headers=headers["alice"],
                         files={"file": ("../../a.txt", "材料笔记".encode())})
    assert result.status_code == 201
    assert result.json()["filename"] == "a.txt"
    aid = result.json()["id"]
    other = conversation(env)
    response = client.post(f"/api/conversations/{other}/runs", headers=headers["alice"],
                           json={"prompt": "abc", "client_key": "request-0002", "attachment_id": aid})
    assert response.status_code == 404
    for filename, content, status in [("bad.py", b"print(1)", 415), ("bad.txt", b"\xff", 415),
                                       ("huge.txt", b"a" * 65537, 413), ("bad.txt", b"\x00", 415)]:
        assert client.post(f"/api/conversations/{cid}/files", headers=headers["alice"],
                           files={"file": (filename, content)}).status_code == status
    rid = submit(env, cid, attachment_id=aid)
    execute(rid)
    with session() as db:
        assert db.get(Run, rid).status == "succeeded"
        assert db.get(Attachment, aid).content == "材料笔记"


def test_idempotent_submission_and_duplicate_delivery(env):
    client, headers, _ = env
    cid = conversation(env)
    rid = submit(env, cid)
    assert submit(env, cid) == rid
    conflict = client.post(f"/api/conversations/{cid}/runs", headers=headers["alice"],
                           json={"prompt": "changed", "client_key": "request-0001"})
    assert conflict.status_code == 409
    execute(rid)
    execute(rid)
    with session() as db:
        assert db.scalar(select(func.count()).select_from(Run)) == 1
        assert db.scalar(select(func.count()).select_from(Message)) == 2
        assert db.get(Run, rid).attempt == 1


def test_history_and_sse_replay(env):
    client, headers, _ = env
    cid = conversation(env)
    rid = submit(env, cid)
    execute(rid)
    response = client.get(f"/api/runs/{rid}/events", headers=headers["alice"])
    assert response.status_code == 200
    frames = response.text.strip().split("\n\n")
    deltas = [json.loads(frame.split("data: ")[1])["text"] for frame in frames if "event: delta" in frame]
    history = client.get(f"/api/conversations/{cid}/messages", headers=headers["alice"]).json()
    assert [row["role"] for row in history] == ["user", "assistant"]
    assert "".join(deltas) == history[1]["content"]
    first_id = int(frames[0].splitlines()[0].split(": ")[1])
    replay = client.get(f"/api/runs/{rid}/events?after={first_id}", headers=headers["alice"]).text
    assert all(int(frame.splitlines()[0].split(": ")[1]) > first_id for frame in replay.strip().split("\n\n"))
    page = client.get(f"/api/conversations/{cid}/messages?before={history[1]['id']}&limit=1", headers=headers["alice"])
    assert page.json() == history[:1]


def test_sse_terminal_drains_multiple_pages(env):
    client, headers, _ = env
    rid = submit(env, conversation(env))
    with session() as db:
        db.add_all(RunEvent(run_id=rid, kind="trace", data='{"ok":true}') for _ in range(205))
        db.get(Run, rid).status = "failed"
        db.commit()
    response = client.get(f"/api/runs/{rid}/events", headers=headers["alice"])
    assert response.text.count("event: trace") == 205


def test_retry_and_dispatch(env):
    rid = submit(env, conversation(env), mode="retry_once")
    execute(rid)
    with session() as db:
        run = db.get(Run, rid)
        assert run.status == "retry_wait" and run.attempt == 1
        run.next_at = time.time() - 1
        db.commit()
    sent = []
    dispatch_once(sent.append)
    assert sent == [rid]
    execute(rid)
    with session() as db:
        run = db.get(Run, rid)
        assert run.status == "succeeded" and run.attempt == 2


@pytest.mark.parametrize("mode,expected", [("slow", "timed_out"), ("fail", "failed")])
def test_timeout_and_failure(env, mode, expected):
    rid = submit(env, conversation(env), mode=mode, timeout_seconds=1)
    execute(rid)
    with session() as db:
        assert db.get(Run, rid).status == expected
        assert db.scalar(select(func.count()).select_from(Message).where(Message.role == "assistant")) == 0


def test_cancel_queued_and_running(env):
    client, headers, _ = env
    cid = conversation(env)
    queued = submit(env, cid)
    assert client.post(f"/api/runs/{queued}/cancel", headers=headers["alice"]).json()["status"] == "cancelled"
    execute(queued)
    running = submit(env, cid, client_key="request-0002")
    lease = claim(running)
    response = client.post(f"/api/runs/{running}/cancel", headers=headers["alice"])
    assert response.json()["cancel_requested"] is True
    with pytest.raises(StopRun, match="cancelled"):
        publish(running, lease, "delta", {"text": "should not be saved"})
    finish(running, lease, "succeeded", output="must not be committed")
    with session() as db:
        assert db.get(Run, running).status == "cancelled"


def test_recovery_and_stale_worker_fencing(env):
    rid = submit(env, conversation(env))
    lease = claim(rid)
    assert claim(rid) is None
    with session() as db:
        db.get(Run, rid).deadline = time.time() - 1
        db.commit()
    dispatch_once(lambda _: pytest.fail("expired running task must not replay"))
    with pytest.raises(StopRun, match="lease_lost"):
        publish(rid, lease, "delta", {"text": "late"})
    finish(rid, lease, "succeeded", output="late")
    with session() as db:
        assert db.get(Run, rid).status == "timed_out"


def test_competing_workers_have_one_claim(env):
    rid = submit(env, conversation(env))
    barrier = Barrier(4)
    def contender(_):
        barrier.wait()
        return claim(rid)
    with ThreadPoolExecutor(max_workers=4) as pool:
        claims = list(pool.map(contender, range(4)))
    assert sum(value is not None for value in claims) == 1
    with session() as db:
        assert db.get(Run, rid).attempt == 1


def test_event_poll_rechecks_expired_or_revoked_login(env):
    _, headers, _ = env
    rid = submit(env, conversation(env))
    token_hash = digest(headers["alice"]["Authorization"].split(" ", 1)[1])
    with session() as db:
        login = db.get(Login, token_hash)
        owner = login.user_id
        login.expires_at = time.time() - 1
        db.commit()
    assert event_page(rid, owner, token_hash, 0) is None


def test_broker_outage_keeps_durable_intent(env, monkeypatch):
    from demo import worker
    def unavailable(_):
        raise ConnectionError("broker unavailable")
    monkeypatch.setattr(worker, "enqueue", unavailable)
    rid = submit(env, conversation(env))
    dispatch_once(unavailable)
    sent = []
    dispatch_once(sent.append)
    assert sent == [rid]
    with session() as db:
        db.get(Run, rid).created_at = time.time() - 121
        db.commit()
    dispatch_once(sent.append)
    with session() as db:
        assert db.get(Run, rid).error_code == "queue_expired"


def test_taskgroup_failure_timeout_and_cancel():
    from demo.concurrency import call_tools
    async def scenario():
        results = await call_tools([("ok", .01, .2), ("slow", .1, .02)])
        assert [row["status"] for row in results] == ["ok", "timeout"]
        with pytest.raises(ExceptionGroup):
            await call_tools([("broken", .01, 1), ("other", 1, 2)])
        with pytest.raises(TimeoutError):
            await call_tools([("slow", 1, 2)], total=.01)
        task = asyncio.create_task(call_tools([("slow", 1, 2)]))
        await asyncio.sleep(.01)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    asyncio.run(scenario())


def test_celery_consumer_with_memory_transport(env):
    # 真正启动 Celery consumer；memory transport 只在本进程传递，不等同 Redis 验证。
    from celery.contrib.testing.worker import start_worker
    from demo.worker import celery_app, run_task
    celery_app.conf.broker_url = "memory://"
    rid = submit(env, conversation(env))
    with start_worker(celery_app, pool="solo", perform_ping_check=False, shutdown_timeout=10):
        run_task.apply_async(args=[rid])
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            with session() as db:
                if db.get(Run, rid).status == "succeeded":
                    break
            time.sleep(.05)
        else:
            pytest.fail("Celery consumer did not complete the task")
