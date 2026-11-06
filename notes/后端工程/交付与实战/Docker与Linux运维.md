# Docker 与 Linux 运维

**适用环境：容器内和运维命令以 Linux 为主；macOS 使用 Docker Desktop，Windows 使用 WSL／Docker Desktop。本机安装按对应系统进行。**

## Docker 解决什么问题

镜像保存应用与用户态依赖，容器是镜像启动后的进程及隔离环境。同一镜像能减少“我的电脑能运行”的环境差异，但宿主架构、内核、设备、网络与数据卷仍会影响行为。Linux 容器共享宿主提供的 Linux 内核；Docker Desktop 通常借助 Linux 虚拟机运行它们。

镜像层适合保存代码与固定依赖，容器可写层应视为可替换；数据库与上传文件用命名卷或外部存储。`EXPOSE` 只是描述容器监听端口，`-p` 才把端口映射到宿主。

安装见 [Mac Docker](../../../getting-started/Docker安装与使用（Mac）.md)或 [Windows／WSL Docker](../../../getting-started/WSL与Docker安装使用（Windows）.md)。下面命令在本机 Demo 目录执行。

## 读懂 Dockerfile

配套 [Dockerfile](../../../examples/backend/agent-demo/Dockerfile) 的主要步骤是：

```dockerfile
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY requirements.lock.txt ./
RUN pip install --no-cache-dir -r requirements.lock.txt \
    && groupadd --gid 10001 demo \
    && useradd --uid 10001 --gid demo --create-home demo
COPY --chown=demo:demo demo ./demo
USER demo
EXPOSE 8000
CMD ["uvicorn", "demo.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

先复制依赖锁文件再复制代码，可以在代码变化时复用依赖层。使用非 root 用户减少权限，JSON 形式 CMD 让服务直接接收停止信号。`.dockerignore` 限定构建上下文，避免把 `.env`、虚拟环境、私钥与数据拷进镜像。[Dockerfile 官方介绍](https://docs.docker.com/build/concepts/dockerfile/)解释了各指令与构建层。

```bash
docker build -t handbook-agent:local .
docker run --rm handbook-agent:local python -m demo.concurrency
```

启动 HTTP 容器需要配置数据库／Redis。完整服务优先使用下一节 Compose。如果只练习单容器启动、尚不调用依赖数据库的接口，可以：

```bash
docker run --rm --name handbook-agent-api -p 127.0.0.1:8000:8000 handbook-agent:local
# 另开终端；这里只确认 API 进程存活，ready 会因依赖未配置而失败。
curl --fail http://127.0.0.1:8000/health/live
docker stop handbook-agent-api
```

服务在容器内监听 `0.0.0.0`，宿主发布到 `127.0.0.1`。容器中的 `localhost` 指向该容器自己，不能用来连接另一个数据库容器。

## Compose 管理多个服务

Demo 的 [compose.yaml](../../../examples/backend/agent-demo/compose.yaml) 包含 `api`、`worker`、`dispatcher`、一次性 `init`、`db` 与 `redis`。API／worker 使用相同代码镜像，启动命令不同；容器间通过服务名 `db` 和 `redis` 通信。

```bash
cp .env.example .env
# 编辑 .env，填入自己生成的 POSTGRES_PASSWORD；不要提交。
docker compose config --quiet
docker compose up -d --build
docker compose run --rm init python -m demo.manage user --username student
docker compose ps
docker compose logs --tail=100 -f api worker dispatcher
```

`.env` 插值数据库 URL 时，口令中的 `@`、`:`、`/` 等字符需要 URL 编码；教学练习可使用足够长的十六进制随机口令。Compose 的明文环境变量仍可被有管理权限的人读取；生产应改用密钥文件或密钥服务，应用显式支持读取，参考 [Compose secrets](https://docs.docker.com/compose/how-tos/use-secrets/)。

`depends_on` 默认只保证启动顺序，不能保证数据库可接受连接。Demo 用 `service_healthy` 等待数据库／Redis，用 `service_completed_successfully` 等待空库初始化。服务启动后依赖仍可能故障，应用需要超时与重连。说明见 [Compose 启停顺序](https://docs.docker.com/compose/how-tos/startup-order/)。

```bash
docker compose exec api python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/health/ready').status)"
docker compose stats --no-stream
docker compose restart worker
docker compose stop
# 停止并删除本练习的容器与网络，保留命名卷中的数据库。
docker compose down
```

`down -v` 会删除命名卷中的数据，不作为日常重启命令。迁移与备份要独立管理；改变 PostgreSQL 大版本标签前，应按数据库官方方式升级数据，不能直接复用不兼容的数据目录。

Demo 使用内存、CPU、PID 上限、只读应用根文件系统、临时目录、移除 capabilities 和禁止提权。它们是服务资源约束，不能证明任意用户代码已经安全隔离。基础镜像标签仍会变化，生产构建可固定 digest，同时定期更新与重新验证安全补丁。

## Linux 常用检查

以下命令在**运行服务的 Linux 主机／容器**执行。Docker 极简镜像可能没有 `ps`、`ss`、`top`，优先从宿主检查，或在专门的调试环境安装工具。

| 目标 | 命令 | 看什么 |
| --- | --- | --- |
| 当前目录和文件 | `pwd`、`ls -lah`、`stat filename` | 路径、权限、大小、时间 |
| 建目录、复制与移动 | `mkdir -p data`、`cp -i input.txt backup.txt`、`mv -i old.txt new.txt` | 使用自己的练习文件，检查目标是否覆盖 |
| 查找文件 | `find ./logs -type f -name '*.log'` | 明确搜索根目录 |
| 查找日志关键词 | `rg -n 'ERROR\|run_id' ./logs` | 未安装 rg 时使用 `grep -nE` |
| 持续看日志 | `tail -n 100 -F ./logs/api.log` | `-F` 适应轮转后的新文件 |
| 查进程 | `ps -ef`、`pgrep -af uvicorn` | PID、启动参数、父子进程 |
| 查端口 | `ss -ltnp` | 监听地址、端口、所属进程；权限影响显示 |
| 查 HTTP | `curl -i --max-time 3 http://127.0.0.1:8000/health/live` | 状态码、响应头、超时 |
| CPU 与负载 | `top`、`uptime`、`ps -eo pid,ppid,%cpu,%mem,args --sort=-%cpu` | CPU、负载、线程／进程数量 |
| 内存 | `free -h` | available 比单独看 free 更有意义 |
| 磁盘 | `df -h`、`du -sh ./data`、`df -i` | 容量、目录大小、inode 是否耗尽 |
| systemd 服务 | `systemctl status your-api.service`、`journalctl -u your-api.service -n 100 --no-pager` | 替换为实际服务名；需该主机有 systemd |
| 结束自己的进程 | `kill -TERM <PID>` | 先核对 PID，让服务完成清理；必要时再考虑强制结束 |

Linux `ss`、`free` 和 GNU `ps --sort` 不能直接照搬到 macOS。Mac 端口可用 `lsof -nP -iTCP:8000 -sTCP:LISTEN`，内存用活动监视器或 `vm_stat`。更完整命令见 [Linux 入门](../../../getting-started/linux/Linux命令行使用与常用命令.md)。

## 健康检查与故障定位

存活检查回答“进程是否还能响应”，就绪检查回答“当前是否适合接收流量”。Demo 的 `/health/live` 不依赖数据库；`/health/ready` 检查数据库和 Redis。依赖短暂故障时就绪失败可以停止接收流量，不能让存活检查反复杀进程造成雪崩。

worker 与 dispatcher 需要各自的监控：最后心跳、队列积压、最老任务等待时间、任务失败率、过期 running 数和补投失败数。定期提交一个无副作用的小任务并等到成功，才能覆盖 broker 到 worker 到结果存储的整条链路。

按层排查：先看端口是否监听，再看 `/health/live`，再看 `/health/ready`，再验证真实登录和带权限的接口，最后提交任务并检查终态与结果。`200 OK` 不能替代跨用户隔离测试。

## 代理与流式响应

公网部署通常由反向代理终止 TLS，并限制请求大小、登录速率、连接数量和响应超时。以下是 Nginx 的局部教学配置，放入已有 server 块并根据实际域名与证书配置 HTTPS：

```nginx
location /api/ {
    client_max_body_size 128k;
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_buffering off;
    proxy_read_timeout 60s;
}
```

后端心跳应短于代理空闲超时；不要无限放大超时来掩盖 worker 卡死。只信任受控代理提供的转发头，避免用户伪造来源 IP 绕过限流。密钥轮换、备份恢复、磁盘容量和日志轮转应与应用发布一起演练。

## 把 Compose 中的一段配置读透

[compose.yaml](../../../examples/backend/agent-demo/compose.yaml) 的应用公共配置含以下真实内容（锚点 `app` 被 api／worker／dispatcher／init 合并引用）：

```yaml
x-app: &app
  image: handbook-agent:local
  build: .
  environment:
    DEMO_DATABASE_URL: postgresql+psycopg://demo:${POSTGRES_PASSWORD:?请在 .env 中填写数据库口令}@db:5432/demo
    DEMO_BROKER_URL: redis://redis:6379/0
  read_only: true
  tmpfs:
    - /tmp:size=16m,mode=1777
  cap_drop: [ALL]
  security_opt: [no-new-privileges:true]
  mem_limit: 512m
  cpus: 1.0
  pids_limit: 128
```

`build: .` 的点是 Dockerfile 构建上下文，不是宿主全部文件；`.dockerignore` 决定哪些文件能进入上下文。`read_only` 使应用根文件系统不可写，multipart 临时文件放到有大小上限的 tmpfs。数据库不写到应用镜像中，而是由 db 服务使用自己的命名卷。

`${POSTGRES_PASSWORD:?...}` 在 Compose 解析时检查变量非空，早于容器启动。如果漏填口令，`docker compose config --quiet` 就应失败。它不验证该口令是否与已有数据库卷一致，也不负责把 URL 中的特殊字符转义。

### 根据修改类型决定下一步命令

| 修改 | 操作 | 为什么 |
| --- | --- | --- |
| Python 源码／依赖锁 | `docker compose up -d --build` | 镜像中的 COPY 内容需要重新构建 |
| environment、端口、资源上限 | `docker compose up -d` | 让 Compose 按新配置重新创建相应容器 |
| 仅服务暂时卡住且无配置变化 | 核对日志后 `docker compose restart worker` | restart 使用现有容器配置 |
| 表结构 | 先备份并执行版本化迁移，再启动新代码 | init/create_all 不会升级已有列 |
| PostgreSQL 大版本 | 独立的数据升级与恢复演练 | 不是简单重建应用镜像 |

只运行 `restart` 不会把新环境变量或新镜像内容自动应用到旧容器。排查时可以用 `docker compose images` 看实际镜像，避免把磁盘上的源码和正在运行的镜像混为一谈。

## 逐层排查一个“页面一直等待”的任务

### 1. 先看 HTTP 服务

```bash
curl -i --max-time 3 http://127.0.0.1:8000/health/live
curl -i --max-time 3 http://127.0.0.1:8000/health/ready
docker compose ps
```

连接被拒绝说明地址／端口无监听或映射不对；live 200 而 ready 503 表示应用能响应但依赖检查失败。401 则说明已连到受保护接口，应检查凭据而非盲目开放防火墙。

### 2. 看依赖与队列消费者

```bash
docker compose exec db pg_isready -U demo -d demo
docker compose exec redis redis-cli PING
docker compose exec worker celery -A demo.worker:celery_app inspect ping --timeout=3
docker compose logs --tail=100 dispatcher worker
```

Redis PONG 不代表 worker 存活；inspect ping 也不代表工具调用一定能成功。若 run 保持 queued，检查 dispatcher 是否持续工作、worker 是否连接到同一 broker；若已 running，检查执行期限和工具日志。目标环境中以一个无副作用任务跑到 succeeded 作为链路探针。

### 3. 查看数据库中的执行事实

Compose 内可运行：

```bash
docker compose exec db psql -U demo -d demo -c 'SELECT id,status,attempt,error_code FROM runs ORDER BY created_at DESC LIMIT 10;'
```

不要用 Celery 的内部 Redis 键直接推断业务完成状态。运行报告包含 run_id 后，再到事件表关联 phase 和 attempt；若数据库已 succeeded 而页面仍等待，重点查 SSE 代理、前端解码和游标。

### 4. 区分“没有输出”与“输出被缓冲”

```bash
# auth_header 是自己登录后生成、权限为 600 的请求头文件。
curl --fail-with-body -N -H @"$auth_header" "http://127.0.0.1:8000/api/runs/$run_id/events"
```

已完成任务的重放可能一口气返回，这是正常现象；观察实时输出时需要在任务尚未完成时订阅。直连后端正常、经代理延迟成整块输出时，检查代理缓冲、压缩和 CDN 策略，而非把模型速度当作唯一原因。

## 用进程、端口和资源证据定位 Linux 故障

在运行服务的 Linux 主机执行：

```bash
pgrep -af 'uvicorn|celery|demo.manage'
ss -ltnp | grep -E ':8000|:5432|:6379'
ps -eo pid,ppid,%cpu,%mem,args --sort=-%cpu | head -15
free -h
df -h
df -i
```

高 CPU 且事件循环无响应，检查是否在 async 路由里跑了纯 Python 计算；进程内存持续涨，检查是否把全部上传或全部历史保存在内存；磁盘尚有空间但写文件失败，要看 inode 和权限。容器因 OOM 被终止时还需要对照容器状态与宿主日志。

```bash
docker compose stats --no-stream
docker compose ps -a
docker compose logs --since=10m --tail=200 worker
```

`docker stats` 展示的是容器资源，`free -h` 是所在 Linux 环境资源；Docker Desktop 虚拟机的内存与 macOS 总内存也不是同一个数值。定位问题时先写清楚命令运行在哪一层。

## 备份、迁移与恢复要连成一步完整练习

在宿主终端执行以下命令，备份自己的教学 Compose 项目：

```bash
umask 077
backup_file=$(mktemp /tmp/agent-demo-backup.XXXXXX)
docker compose exec -T db pg_dump -U demo -d demo -Fc > "$backup_file"
ls -lh "$backup_file"
```

备份成功不等于可恢复；应在**另一个空数据库**中用匹配版本的 pg_restore 恢复，并检查用户、会话数、任务状态和历史消息。不要直接把恢复命令指向正在使用的库，也不要把测试恢复当作普通启动步骤。文件／对象存储和解密密钥若不在 PostgreSQL 中，也要分别备份并验证配套关系。

正式发布可以按“配置校验 → 备份 → 迁移 → 启动 → ready → 登录／越权检查 → 小任务成功 → 观察错误率”安排。失败回滚同时考虑代码版本与数据结构兼容性；不能只把镜像标签回退就假设数据自动兼容。
