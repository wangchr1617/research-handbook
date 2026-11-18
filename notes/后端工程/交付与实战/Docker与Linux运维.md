# Docker 与 Linux 运维

Agent Demo 在开发机上能跑，交给同学时还要交代三件事。用哪一版代码和依赖，哪些服务要一起启动，换机器时去哪找原来的任务记录。Docker 镜像回答第一件事，Compose 把服务和存储的配置放在一起。用这个 Demo 练习时，可以先从一次完整的启动开始，再分别排查代码版本和任务状态。

## 一、什么时候用 Docker，什么时候加 Compose

一次性的 Python 分析脚本，通常建个虚拟环境、装好依赖就能运行。开发 Demo 时，要单独检查提交、重试和会话隔离，也可以用临时 SQLite 库跑脚本。这种练习在进程内执行，连上 Redis 和独立 worker 后，还要验证任务能否跨进程投递。 [Demo 的本机运行路线](../../../examples/backend/agent-demo/README.md#路线二本机-pythonredis) · [请求与恢复实操](../../../examples/backend/agent-demo/请求与恢复实操.md)

要把应用交给别人启动，镜像能固定 Python、系统依赖和应用代码。只有一个服务时，可以先用 Docker 单独启动它。这个 Demo 还需要 PostgreSQL、Redis、worker 和 dispatcher，逐条运行容器容易漏掉网络、卷或启动顺序，所以整套演练用 Compose。团队如果只是交付到一台主机，先把 Compose 的发布和恢复练通即可。多节点调度和跨机器容错再看 Kubernetes。 [企业迁移部署的选型](Docker与Kubernetes企业迁移部署.md#一先按业务和团队条件选运行平台)

## 二、镜像、容器和卷分别保存什么

看 Demo 的 Dockerfile。它先拷贝锁文件并安装依赖，再拷贝 `demo/` 中的源码。只改源码时可以复用依赖层。重新构建会更新镜像，已经创建的容器仍绑定原来的镜像。PostgreSQL 的数据另挂到命名卷 `pgdata`，所以更新应用镜像可以保留原有任务记录。 [Dockerfile](../../../examples/backend/agent-demo/Dockerfile) · [Compose 配置和命名卷](../../../examples/backend/agent-demo/compose.yaml)

按 Demo 说明准备 `.env`，在 `examples/backend/agent-demo` 目录执行下面的命令。macOS 上先启动 Docker Desktop，Linux 上先确认 Docker 引擎已运行。 [Demo 的启动和账号创建步骤](../../../examples/backend/agent-demo/README.md#路线一docker-compose)

```bash
docker compose config --images | sort | uniq -c
```

```text
   4 handbook-agent:local
   1 postgres:17
   1 redis:7.4
```

`handbook-agent:local` 的计数是 4，分别来自 API、worker、dispatcher 和一次性初始化任务。它们共用一个镜像，各自的命令写在 Compose 里。API 用服务名 `db` 和 `redis` 连接依赖。在 API 容器里填 `localhost`，请求会发回它自己。宿主浏览器用的是另一处地址，也就是映射出来的 `127.0.0.1:8000`。

第一次启动时，先确认 8000 端口空闲，再在同一目录运行下面的命令。创建 `student` 账号时按提示设置密码。

```bash
docker compose up -d --build
docker compose run --rm init python -m demo.manage user --username student
docker compose ps -a
```

在 `ps -a` 里看到 `init` 以退出码 0 结束是正常的。接下来访问 `http://127.0.0.1:8000`，登录并提交一条普通任务，记住正常时页面如何显示结果，之后再做下面两次排障。

## 三、拿 Demo 练两次排障

### 改了代码，重启后还在跑旧版本

如果本机已经重新 build 过，先对比标签指向的镜像 ID 和 worker 创建时绑定的镜像 ID。第二条命令要求项目已创建一个 worker 容器。

```bash
docker image inspect --format '{{.Id}}' handbook-agent:local
docker inspect --type container --format '{{.Image}}' "$(docker compose ps -a -q worker)"
```

两个 ID 不同就执行 `docker compose up -d`，让 Compose 用新镜像重建受影响的服务。源码或依赖刚改过、还没构建镜像时，用 `docker compose up -d --build`。只改了端口或环境变量时，先用 `docker compose config --quiet` 检查配置，再执行 `docker compose up -d`。普通 `restart` 适合重启原来的容器，仍沿用它创建时的镜像和环境变量。 [Compose 重建规则](https://docs.docker.com/reference/cli/docker/compose/up/)

### 站点能登录，任务一直在排队

在自己的教学环境里执行 `docker compose stop worker`，然后从网页提交一条普通任务。下面的就绪接口仍可以返回 200，因为它只检查 API 能否访问 PostgreSQL 和 Redis。真正消费任务的 worker 已经停了，任务会停在 `queued`。

```bash
curl -i http://127.0.0.1:8000/health/ready
docker compose ps -a worker dispatcher
docker compose logs --tail=80 worker dispatcher
```

在提交后 120 秒内执行 `docker compose start worker`，给它留出时间领取原任务。超过排队期限后，dispatcher 会在扫描时将任务标为 `timed_out`，错误码是 `queue_expired`。若 API 已把同一个 `run_id` 标为 `succeeded`，网页却还在转圈，直连事件接口查 `done`。直连能收到时，接着查代理缓冲和页面对终止事件的处理。 [停 worker 练习](../../../examples/backend/agent-demo/README.md#验证和故障练习) · [提交任务和查看 SSE 的命令](../../../examples/backend/agent-demo/README.md#用-curl-跑完整链路)

## 四、换机器前最容易遗漏的两件事

**检查实际发布的镜像。** 本机可以用 `docker image ls handbook-agent:local` 找标签。要从 Apple Silicon 交付到 x86 Linux，还要去仓库确认发布的标签确实包含 `linux/amd64`。把下面的仓库地址和标签换成实际值。

```bash
docker image inspect --format '{{.Os}}/{{.Architecture}}' handbook-agent:local
docker buildx imagetools inspect registry.example.com/lab/handbook-agent:v1
```

第一条读本地，第二条读仓库。多平台镜像看输出中各项的 `Platform`，单平台镜像可加 `--format '{{json .Image}}'` 查看 `os` 和 `architecture`。核对完，把仓库给出的摘要记下来。上一步比较容器时查的是本地镜像 ID，部署记录里要保存的是仓库摘要。 [仓库镜像的检查方法](https://docs.docker.com/reference/cli/docker/buildx/imagetools/inspect/)

**确认数据怎么带过去。** Compose 在原机器上重建容器通常会保留命名卷，`down -v` 则会删除卷。仅把镜像推到另一台机器，不会把 PostgreSQL 数据或 Redis 卷带过去。迁移有历史数据的实例时，先安排备份恢复和切换，再发布应用。修改 `.env` 中的 PostgreSQL 初始口令也不会重设旧卷里已有角色的密码。 [Demo 的卷说明](../../../examples/backend/agent-demo/README.md#路线一docker-compose) · [有后台任务的服务怎么迁](Docker与Kubernetes企业迁移部署.md#三带附件的任务怎样试迁移)

## 五、把一次部署交给下一位同学

发布后，从新入口登录、提交一条小任务，等 worker 跑完，再打开它的结果。把这条任务的 `run_id` 和镜像摘要、运行平台、数据恢复位置放在同一份发布记录里。下次同学遇到“页面能打开，任务跑不通”，手里就有一条正常时的记录可以对照。
