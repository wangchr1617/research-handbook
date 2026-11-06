"""在新建的练习目录运行 Agent 请求、状态与恢复案例，不需要 Redis／Docker。

用法：python scripts/backend/运行Agent案例.py --output-dir /tmp/agent-backend-lab
需先安装 examples/backend/agent-demo/requirements.lock.txt；输出目录必须不存在。
通过真实 FastAPI／SQLAlchemy 代码与本地 execute() 验证业务，不验证网络 broker。
"""
import argparse
import json
import os
import secrets
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "examples/backend/agent-demo"))


def run(output_dir):
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=False)
    os.chdir(output_dir)
    os.environ["DEMO_DATABASE_URL"] = "sqlite:///" + str(output_dir / "demo.db")
    os.environ["DEMO_BROKER_URL"] = "memory://"

    from demo import worker
    from demo.db import Base, Message, Run, User, engine, session
    from demo.jobs import StopRun, claim, dispatch_once, execute, finish, publish
    from demo.main import app
    from demo.security import passwords
    from fastapi.testclient import TestClient
    from sqlalchemy import func, select

    Base.metadata.create_all(engine())
    password = secrets.token_urlsafe(24)
    with session() as db:
        for name in ("reader_a", "reader_b"):
            db.add(User(username=name, password_hash=passwords.hash(password)))
        db.commit()
    sent = []
    worker.enqueue = sent.append
    inputs = ROOT / "inputs/backend"
    load = lambda name: json.loads((inputs / name).read_text())
    report = {"execution": "in_process_api_and_execute", "cases": {}}

    with TestClient(app) as client:
        def checked(method, path, expected=200, **kwargs):
            response = client.request(method, path, **kwargs)
            if response.status_code != expected:
                raise AssertionError(f"{method} {path}: {response.status_code} {response.text}")
            return response

        tokens = {name: checked("POST", "/api/auth/login", json={"username": name, "password": password}).json()
                  ["access_token"] for name in ("reader_a", "reader_b")}
        headers = {"Authorization": "Bearer " + tokens["reader_a"]}
        other = {"Authorization": "Bearer " + tokens["reader_b"]}
        cid = checked("POST", "/api/conversations", 201, headers=headers,
                      json=load("conversation.json")).json()["id"]
        file_data = (inputs / "研究笔记样例.md").read_bytes()
        aid = checked("POST", f"/api/conversations/{cid}/files", 201, headers=headers,
                      files={"file": ("研究笔记样例.md", file_data, "text/markdown")}).json()["id"]

        def submit(body):
            return checked("POST", f"/api/conversations/{cid}/runs", 202,
                           headers=headers, json=body).json()["id"]

        def state(rid):
            return checked("GET", f"/api/runs/{rid}", headers=headers).json()

        invalid = checked("POST", f"/api/conversations/{cid}/runs", 422, headers=headers,
                          json=load("run-invalid.json")).json()
        report["cases"]["invalid"] = {"status_code": 422, "code": invalid["code"], "fields": invalid["fields"]}

        body = {**load("run-normal.json"), "attachment_id": aid}
        rid = submit(body)
        execute(rid)
        assert submit(body) == rid
        execute(rid)
        conflict = {**body, "prompt": "同一个键对应不同内容"}
        checked("POST", f"/api/conversations/{cid}/runs", 409, headers=headers, json=conflict)
        events = checked("GET", f"/api/runs/{rid}/events", headers=headers).text
        (output_dir / "normal-events.sse").write_text(events)
        history = checked("GET", f"/api/conversations/{cid}/messages", headers=headers).json()
        assert len(history) == 2 and history[-1]["role"] == "assistant"
        input_text = body["prompt"] + "\n" + file_data.decode("utf-8")
        report["cases"]["normal"] = {**state(rid), "messages": len(history),
            "input_characters": len(input_text), "input_words": len(input_text.split()),
            "output": history[-1]["content"], "attachment_bytes": len(file_data), "idempotency": "same_run"}
        checked("GET", f"/api/runs/{rid}", 404, headers=other)
        checked("GET", f"/api/conversations/{cid}/messages", 404, headers=other)
        report["cases"]["other_user"] = {"run_status_code": 404, "messages_status_code": 404}

        retry_id = submit(load("run-retry.json"))
        execute(retry_id)
        retry_first = state(retry_id)
        assert retry_first["status"] == "retry_wait"
        with session() as db:
            due = db.get(Run, retry_id).next_at
        time.sleep(max(0, due - time.time()) + .02)
        sent.clear()
        dispatch_once(sent.append)
        assert retry_id in sent
        execute(retry_id)
        report["cases"]["retry"] = {"first_status": retry_first["status"], **state(retry_id)}
        assert report["cases"]["retry"]["attempt"] == 2

        for filename, expected in [("run-timeout.json", "timed_out"), ("run-failure.json", "failed")]:
            task_id = submit(load(filename))
            execute(task_id)
            report["cases"][filename] = state(task_id)
            assert state(task_id)["status"] == expected

        cancel_id = submit({**load("run-normal.json"), "client_key": "backend-cancel-001"})
        checked("POST", f"/api/runs/{cancel_id}/cancel", 202, headers=headers)
        execute(cancel_id)
        report["cases"]["cancel_queued"] = state(cancel_id)
        assert state(cancel_id)["status"] == "cancelled" and state(cancel_id)["attempt"] == 0

        recovery_id = submit({**load("run-normal.json"), "client_key": "backend-recovery-001"})
        lease = claim(recovery_id)
        # 只在这个新建练习库中模拟“worker 消失且期限过期”，不冒充真实崩溃实验。
        with session() as db:
            db.get(Run, recovery_id).deadline = time.time() - 1
            db.commit()
        dispatch_once(sent.append)
        try:
            publish(recovery_id, lease, "delta", {"text": "late worker"})
        except StopRun as exc:
            assert str(exc) == "lease_lost"
        else:
            raise AssertionError("stale worker was not fenced")
        finish(recovery_id, lease, "succeeded", output="late worker")
        report["cases"]["expired_worker"] = {**state(recovery_id), "late_write": "rejected"}
        assert state(recovery_id)["status"] == "timed_out"

        with session() as db:
            report["totals"] = {"runs": db.scalar(select(func.count()).select_from(Run)),
                                "messages": db.scalar(select(func.count()).select_from(Message))}
        checked("POST", "/api/auth/logout", 204, headers=headers)
        checked("GET", "/api/conversations", 401, headers=headers)
        report["cases"]["logout"] = {"next_request_status_code": 401}
    engine().dispose()
    (output_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"数据库与事件文件：{output_dir}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path, help="新建的练习输出目录，必须不存在")
    args = parser.parse_args()
    run(args.output_dir)


if __name__ == "__main__":
    main()
