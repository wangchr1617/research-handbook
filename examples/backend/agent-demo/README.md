# Agent 后端教学 Demo

**适用环境：Python 3.12；Linux、macOS 或 Windows WSL。Docker 路线使用 Linux 容器、Docker Compose v2；本机路线另需 Redis。**

参照 Archeos 的 FastAPI 分层方式，构建一个独立的小应用：用户登录后创建会话、上传文本、提交后台任务、逐段接收输出，并重新查看历史消息与执行事件。工程原理见[后端专题](../../../notes/后端工程/README.md)，实际项目对照见[源码阅读](../../../notes/后端工程/交付与实战/Archeos与ALKEMIE源码阅读.md)。

Agent 使用固定的文本统计工具模拟模型生成，无 API Key、外部 shell 或远程计算。`generate()` 是替换真实模型 SDK 的入口，其他认证、状态、追踪和事件存储可沿用。多个 run 的输入彼此独立；本 Demo 保存聊天历史，但不会自动将历史拼入模型上下文。

需要跟着输入和输出逐步练习时，阅读[请求、数据与恢复实操](请求与恢复实操.md)，配合[固定输入文件](../../../inputs/backend/README.md)与[运行脚本](../../../scripts/backend/README.md)。其中本机 HTTP 工具使用真实网络请求，独立于 Agent 的确定性输出链路。

## 服务和代码

```text
浏览器／curl → FastAPI → 数据库中的 run 与消息
                      → Redis broker → Celery worker → 事件与最终结果
独立 dispatcher → 扫描待投递任务／超时运行 → 补投或收敛终态
浏览器 SSE ← FastAPI 按游标读取数据库事件
```

| 文件 | 作用 |
| --- | --- |
| [demo/config.py](demo/config.py) | `DEMO_` 环境变量与范围校验 |
| [demo/schemas.py](demo/schemas.py) | Pydantic 2 输入模型 |
| [demo/db.py](demo/db.py) | 用户、会话、消息、附件、run 与事件表 |
| [demo/security.py](demo/security.py) | Argon2、令牌摘要、逐资源归属校验 |
| [demo/main.py](demo/main.py) | HTTP、上传、SSE、异常与请求日志 |
| [demo/concurrency.py](demo/concurrency.py) | TaskGroup、局部／整体超时与取消练习 |
| [demo/jobs.py](demo/jobs.py) | 条件领取、状态机、重试、取消与恢复 |
| [demo/worker.py](demo/worker.py) | Celery 配置与队列入口 |
| [demo/manage.py](demo/manage.py) | 空库初始化、创建用户、独立 dispatcher |
| [demo/static/index.html](demo/static/index.html) | 无构建依赖的浏览器界面 |
| [tests/test_demo.py](tests/test_demo.py) | API 与任务故障分支测试 |
| [Dockerfile](Dockerfile)、[compose.yaml](compose.yaml) | API／worker／dispatcher／数据库／broker |

## 路线一：Docker Compose

以下命令从仓库根目录开始，在本机或 WSL 执行。先确认 Docker 引擎正在运行，8000 端口未被占用。

```bash
cd examples/backend/agent-demo
cp .env.example .env
```

编辑 `.env`，将 `POSTGRES_PASSWORD` 填为自己生成的长随机口令。它会被插入连接 URL，练习可用十六进制字符，避免 `@`、`:` 等特殊字符的编码问题。例如用 `openssl rand -hex 24` 生成后写入；这是本机练习数据库口令，不是任何已有服务的账号。

```bash
docker compose config --quiet
docker compose up -d --build
docker compose run --rm init python -m demo.manage user --username student
docker compose ps
curl --fail http://127.0.0.1:8000/health/ready
```

创建用户时交互输入两次至少 12 字符的密码，已存在用户名不会覆盖。浏览器打开 [Demo](http://127.0.0.1:8000)，使用刚创建的账号登录。交互式接口文档在 [OpenAPI 页面](http://127.0.0.1:8000/docs)。

`init` 只为全新教学数据库创建表；真实项目用 Alembic 等迁移工具。数据库与 Redis 不向宿主发布端口，仅 API 发布到本机回环地址。

```bash
docker compose logs --tail=100 -f api worker dispatcher
docker compose stop
# 删除练习容器和网络，保留数据卷；再次 up 可继续使用历史。
docker compose down
```

不要把 `down -v` 当重启操作，它会删除此项目的数据卷。修改 PostgreSQL 初始化口令变量不会自动重设已有数据库卷中的角色口令。

## 路线二：本机 Python＋Redis

所有终端均在 `examples/backend/agent-demo` 目录下，使用同一 `.env` 和虚拟环境。本机练习数据库默认是 `./data/demo.db`；Redis 默认在 `127.0.0.1:6379`。不要连接共享或生产 Redis。

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.lock.txt
cp .env.example .env
source .venv/bin/activate
python -m demo.manage init
python -m demo.manage user --username student
```

本机 Redis 已安装时，在一个终端前台运行 `redis-server --bind 127.0.0.1 --port 6379`，另开终端运行 `redis-cli PING`，应返回 `PONG`。已使用本机 6379 时另选端口，并同时修改 `DEMO_BROKER_URL`；不要停止不属于本练习的服务。

也可仅用 Docker 启动本机练习的 Redis：

```bash
docker run --rm --name handbook-demo-redis -p 127.0.0.1:6379:6379 redis:7.4
```

依次在三个已激活虚拟环境的终端运行：

```bash
# 终端 A：API；不加 --reload 也可以。
uvicorn demo.main:app --host 127.0.0.1 --port 8000
```

```bash
# 终端 B：Linux／WSL worker。
celery -A demo.worker:celery_app worker -l INFO --concurrency=2
```

```bash
# 终端 C：每 5 秒补投与核对一次。
python -m demo.manage dispatch
```

macOS 本机教学可把终端 B 换为 `celery -A demo.worker:celery_app worker -l INFO --pool=solo --concurrency=1`。solo 池不提供与 Linux prefork 相同的软／硬超时保证，本 Demo 自身的 asyncio 与数据库期限仍有效；任意阻塞代码的硬终止应在目标 Linux worker 中验证。

## 浏览器练习

1. 登录，新建“研究笔记统计”会话。
2. 上传 UTF-8 `.txt` 或 `.md` 文件，最大 64 KiB。附件仅绑定当前会话。
3. 输入文字并执行，观察文本逐段出现，展开执行事件查看工具阶段。
4. 刷新页面并重新登录，选择旧会话，查看最近消息与执行记录；选择记录可从头重放事件。
5. 用 `retry_once` 模式观察 `retry_wait → running → succeeded`，dispatcher 需要保持运行。
6. 用 `slow` 观察超时；在运行过程中点取消，观察取消请求和最终状态的区别；用 `fail` 查看受控错误。

前端断开不会取消 worker。页面的“重连”清空当前文本后从头重放；接口支持 `after` 游标供后续实现增量续传。令牌只保存在页面内存，刷新后需要重新登录。

## 用 curl 跑完整链路

以下 Bash 命令需要 Python 3。密码从终端读取，先写入临时请求文件，避免出现在 curl 命令行中。练习账号和临时令牌只用于本机演示：

```bash
umask 077
login_body=$(mktemp)
login_result=$(mktemp)
auth_header=$(mktemp)
trap 'rm -f "$login_body" "$login_result" "$auth_header"' EXIT
python -c 'import getpass,json,sys; json.dump({"username":"student","password":getpass.getpass("密码：")},open(sys.argv[1],"w"))' "$login_body"
curl --fail-with-body -sS -H 'Content-Type: application/json' \
  --data-binary @"$login_body" http://127.0.0.1:8000/api/auth/login > "$login_result"
python -c 'import json,sys; print("Authorization: Bearer "+json.load(open(sys.argv[1]))["access_token"])' "$login_result" > "$auth_header"
conversation_id=$(curl --fail-with-body -sS -H @"$auth_header" -H 'Content-Type: application/json' \
  -d '{"title":"研究笔记统计"}' http://127.0.0.1:8000/api/conversations \
  | python -c 'import json,sys; print(json.load(sys.stdin)["id"])')
```

准备一个自己的 `note.txt`，上传并把附件 ID 写入任务输入：

```bash
attachment_id=$(curl --fail-with-body -sS -H @"$auth_header" -F 'file=@note.txt' \
  "http://127.0.0.1:8000/api/conversations/$conversation_id/files" \
  | python -c 'import json,sys; print(json.load(sys.stdin)["id"])')
run_body=$(mktemp)
trap 'rm -f "$login_body" "$login_result" "$auth_header" "$run_body"' EXIT
python -c 'import json,sys,uuid; json.dump({"prompt":"统计文本","client_key":str(uuid.uuid4()),"attachment_id":sys.argv[1]},open(sys.argv[2],"w"))' "$attachment_id" "$run_body"
run_id=$(curl --fail-with-body -sS -H @"$auth_header" -H 'Content-Type: application/json' \
  --data-binary @"$run_body" "http://127.0.0.1:8000/api/conversations/$conversation_id/runs" \
  | python -c 'import json,sys; print(json.load(sys.stdin)["id"])')
curl --fail-with-body -N -H @"$auth_header" "http://127.0.0.1:8000/api/runs/$run_id/events"
curl --fail-with-body -sS -H @"$auth_header" "http://127.0.0.1:8000/api/runs/$run_id"
curl --fail-with-body -sS -H @"$auth_header" "http://127.0.0.1:8000/api/conversations/$conversation_id/messages"
```

再次发送同一个 `$run_body` 应返回原 `run_id`，不会生成第二条用户消息。同一个 `client_key` 换不同输入会得到 `409`。取消接口是 `POST /api/runs/{run_id}/cancel`；退出接口是 `POST /api/auth/logout`。`curl -H @文件` 需要 curl 7.55+。

## 验证和故障练习

```bash
python -m demo.concurrency
python -m pytest -q
```

自动化测试在临时 SQLite 库中验证登录、上传、越权、幂等、事件重放、状态机、期限、取消与恢复，并启动 Celery consumer 使用进程内 memory transport。它不连接生产数据，也不证明 Redis 网络、PostgreSQL 竞争或 Linux 硬超时已正确配置。

Compose 环境中可先 `docker compose stop worker`，在网页提交 normal 任务，随后于 120 秒内 `docker compose start worker`，观察 queued 任务被补投完成。停 Redis 再提交可以观察持久化意图保留，恢复后由 dispatcher 补投。恢复流程会重复投递，条件领取防止重复执行；排队超过 120 秒会成为 `timed_out`。

超时 running 不自动重放，避免重复外部副作用。练习真实 worker 崩溃时，应检查 run 最终被 dispatcher 收敛，迟到 worker 不能写回成功。备份恢复、代理缓冲、数据库竞争和进程强制终止应在目标部署环境另行验收。

## 从教学应用继续扩展

依赖范围在 `requirements.txt`，精确版本与平台条件在 `requirements.lock.txt`。更新依赖后重新安装、运行测试和容器检查；锁文件可用 `uv pip compile requirements.txt --universal --python-version 3.12 -o requirements.lock.txt` 重新生成。

公开部署前增加 HTTPS、登录限流、请求体总量限制、用户与会话配额、事件清理和日志保留；将数据库密钥从环境变量迁到受控文件／密钥服务。健康检查只测依赖连通，需要增加真实执行探针和 worker／dispatcher 心跳。

大文件改成对象存储并做下载授权；解析器放入受限环境。接入真实模型时，在 `generate()` 读取模型流，按用户保存工具凭据，增加调用次数、tokens 和费用上限。模型工具不能绕过服务端权限，提交远程计算等有副作用动作要设计幂等和核对策略。
