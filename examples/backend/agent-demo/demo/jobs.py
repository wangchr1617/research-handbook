"""持久化任务状态、事件与安全重试。运行入口见 manage.py 和 worker.py。"""
import asyncio
import json
import logging
import time

from sqlalchemy import select, update

from .concurrency import call_tools
from .db import Attachment, Message, Run, RunEvent, session, uid

logger = logging.getLogger("demo.jobs")
TERMINAL = {"succeeded", "failed", "cancelled", "timed_out"}


class StopRun(Exception):
    pass


class TransientToolError(Exception):
    pass


def add_event(db, run_id, kind, data):
    db.add(RunEvent(run_id=run_id, kind=kind, data=json.dumps(data, ensure_ascii=False)))


def claim(run_id):
    """条件更新领取；重复队列消息只有一个能把 queued 改成 running。"""
    now, lease = time.time(), uid()
    with session() as db:
        result = db.execute(update(Run).where(
            Run.id == run_id, Run.status.in_(["queued", "retry_wait"]), Run.next_at <= now,
            Run.cancel_requested.is_(False), Run.created_at > now - 120,
            Run.attempt < 3,
        ).values(status="running", lease=lease, attempt=Run.attempt + 1,
                 deadline=now + Run.timeout_seconds, error_code=None))
        if result.rowcount != 1:
            db.rollback()
            return None
        run = db.get(Run, run_id)
        add_event(db, run_id, "status", {"status": "running", "attempt": run.attempt})
        db.commit()
        return lease


def locked_run(db, run_id, lease):
    # 写入前同时检查状态与领取凭据；过期 worker 无法覆盖恢复后的状态。
    changed = db.execute(update(Run).where(
        Run.id == run_id, Run.lease == lease, Run.status == "running",
    ).values(lease=lease))
    return db.get(Run, run_id) if changed.rowcount == 1 else None


def publish(run_id, lease, kind, payload):
    with session() as db:
        run = locked_run(db, run_id, lease)
        if run is None:
            raise StopRun("lease_lost")
        if run.cancel_requested:
            raise StopRun("cancelled")
        if run.deadline <= time.time():
            raise StopRun("timed_out")
        add_event(db, run_id, kind, payload)
        db.commit()


def finish(run_id, lease, status, error=None, output=None):
    with session() as db:
        run = locked_run(db, run_id, lease)
        if run is None:
            return
        if run.cancel_requested:
            status, error, output = "cancelled", "cancelled", None
        elif run.deadline <= time.time():
            status, error, output = "timed_out", "deadline_exceeded", None
        run.status, run.error_code, run.lease = status, error, None
        if output is not None:
            db.add(Message(conversation_id=run.conversation_id, run_id=run.id,
                           role="assistant", content=output))
        add_event(db, run.id, "done", {"status": status, "error_code": error})
        db.commit()


def retry_later(run_id, lease):
    with session() as db:
        run = locked_run(db, run_id, lease)
        if run is None:
            return
        if run.cancel_requested or run.deadline <= time.time() or run.attempt >= 3:
            db.rollback()
            finish(run_id, lease, "failed", "retry_exhausted")
            return
        run.status, run.lease, run.deadline = "retry_wait", None, None
        run.next_at = time.time() + 2 ** run.attempt
        run.error_code = "tool_unavailable"
        add_event(db, run_id, "status", {"status": "retry_wait", "attempt": run.attempt})
        db.commit()


async def generate(run_id, lease):
    with session() as db:
        run = db.get(Run, run_id)
        mode, attempt, prompt, limit = run.mode, run.attempt, run.prompt, run.timeout_seconds
        attachment = db.get(Attachment, run.attachment_id) if run.attachment_id else None
        text = prompt + ("\n" + attachment.content if attachment else "")
    async with asyncio.timeout(limit):
        publish(run_id, lease, "trace", {"tool": "text_stats", "phase": "start"})
        if mode == "retry_once" and attempt == 1:
            raise TransientToolError()
        if mode == "fail":
            raise ValueError("controlled demo failure")
        if mode == "slow":
            await asyncio.sleep(limit + 1)
        results = await call_tools([("word_count", .05, 1), ("character_count", .05, 1)])
        publish(run_id, lease, "trace", {"tool": "text_stats", "phase": "end", "results": results})
        output = (f"教学 Agent：并发完成两个工具调用。输入共 {len(text)} 个字符，"
                  f"按空白分词为 {len(text.split())} 项。\n这是一段确定性输出，可在 generate 中接入模型 SDK。")
        for offset in range(0, len(output), 6):
            await asyncio.sleep(.03)
            publish(run_id, lease, "delta", {"text": output[offset:offset + 6]})
        finish(run_id, lease, "succeeded", output=output)


def execute(run_id):
    lease = claim(run_id)
    if lease is None:
        return
    with session() as db:
        run = db.get(Run, run_id)
        request_id, attempt = run.request_id, run.attempt
    logger.info("run_started request_id=%s run_id=%s attempt=%s", request_id, run_id, attempt)
    try:
        asyncio.run(generate(run_id, lease))
    except TransientToolError:
        retry_later(run_id, lease)
    except TimeoutError:
        finish(run_id, lease, "timed_out", "deadline_exceeded")
    except StopRun as exc:
        if str(exc) != "lease_lost":
            finish(run_id, lease, str(exc), str(exc))
    except Exception:
        logger.exception("run_failed request_id=%s run_id=%s attempt=%s", request_id, run_id, attempt)
        finish(run_id, lease, "failed", "tool_failed")


def cancel(run_id):
    with session() as db:
        # 条件写先锁定该行，和 worker 完成写入形成确定的先后关系。
        changed = db.execute(update(Run).where(Run.id == run_id, Run.status.not_in(TERMINAL))
                             .values(cancel_requested=True))
        if changed.rowcount:
            run = db.get(Run, run_id)
            if run.status != "running":
                run.status, run.lease = "cancelled", None
                add_event(db, run_id, "done", {"status": "cancelled"})
            db.commit()


def dispatch_once(send):
    """扫描数据库未完成意图并补投；每 5 秒调用，send 接收 run_id。"""
    now = time.time()
    with session() as db:
        candidates = list(db.scalars(select(Run.id).where(Run.status.not_in(TERMINAL)).limit(100)))
    for run_id in candidates:
        with session() as db:
            run = db.get(Run, run_id)
            if run is None or run.status in TERMINAL:
                continue
            stale = run.status == "running" and run.deadline is not None and run.deadline <= now
            expired_queue = run.status != "running" and run.created_at <= now - 120
            if stale or expired_queue:
                status = "cancelled" if run.cancel_requested else "timed_out"
                error = "lease_expired" if stale else "queue_expired"
                # CAS 同时覆盖 PostgreSQL 和不支持 FOR UPDATE 的 SQLite。
                # 扫描后若 worker 已完成／另一次领取发生，本次更新应无效。
                changed = db.execute(update(Run).where(
                    Run.id == run.id, Run.status == run.status, Run.lease == run.lease,
                    Run.cancel_requested == run.cancel_requested,
                ).values(status=status, error_code=error, lease=None),
                    execution_options={"synchronize_session": False})
                if changed.rowcount == 1:
                    add_event(db, run.id, "done", {"status": status, "error_code": error})
                db.commit()
                continue
            ready = run.status in {"queued", "retry_wait"} and run.next_at <= now
        if ready:
            try:
                send(run_id)
            except Exception:
                # 数据库记录还在，下个扫描周期继续；不把 broker 错误返回为任务成功。
                logger.warning("dispatch_unavailable run_id=%s", run_id)
