# Docker 安装与使用（Mac）

**适用环境：macOS（Apple Silicon / Intel），Docker Desktop 运行 Linux 容器。**

Docker 适合固定软件依赖和复现运行环境。Mac 上的 Linux 容器实际运行在 Docker Desktop 管理的 Linux 虚拟机中，不能把容器里的路径直接当作 Mac 路径。

## 开始前

先在苹果菜单 → 关于本机查看芯片和 macOS 版本，再打开“终端”（`Cmd+空格` 搜索“终端”）。本篇使用图形安装包，不要求预先安装 Homebrew、Python、WSL 或 Linux。

Docker 软件与 Docker Hub 镜像账号是不同对象；先完成 Desktop 安装，再看首次启动的登录提示。自己的使用场景是否需要付费订阅，按下面官方安装页的条款确认。

## 一、安装并验证

打开 [Docker 官方安装与下载页](https://docs.docker.com/desktop/setup/install/mac-install/)，点击 **Mac with Apple silicon** 或 **Mac with Intel chip** 对应下载。打开 `.dmg`，把 Docker 拖到“应用程序”，再从“应用程序”启动 Docker。

按首次启动向导确认条款和安装选项；如需注册或登录，使用 [Docker 账号入口](https://hub.docker.com/)。等待 Docker Desktop 显示引擎运行后，再打开终端执行下面的验证。系统支持范围和使用条款按官方下载页核对。

```bash
docker --version
docker version
docker run --rm hello-world
```

`docker --version` 只说明客户端存在；`docker version` 应同时显示 Client 和 Server，`hello-world` 成功才说明拉取及运行链路可用。提示不能连接 daemon 时，先确认 Docker Desktop 已启动，再看 `docker context ls`，不要直接重装。

## 二、镜像与容器

镜像是运行环境模板，容器是它的一个运行实例。下面在 Mac 终端执行：

```bash
docker pull python:3.12-slim
docker run --rm python:3.12-slim python --version
docker images
docker ps
docker ps -a
```

`--rm` 在容器退出后删除该容器，不删除镜像。Apple Silicon 优先使用支持 `linux/arm64` 的镜像；仅有 x86 版本时可尝试 `--platform linux/amd64`，但模拟运行可能更慢，也可能不兼容。Mac Docker Desktop 不能提供 NVIDIA CUDA GPU 运行环境，GPU 计算应放到对应的 Linux GPU 主机。

## 三、挂载工作目录

以运行一个 Python 后处理脚本为例：

```bash
mkdir -p "$HOME/projects/docker-demo"
cd "$HOME/projects/docker-demo"
printf 'print("hello from container")\n' > hello.py
docker run --rm --mount "type=bind,source=$PWD,target=/work" \
  -w /work python:3.12-slim python hello.py
```

`/work` 是容器内路径，指向 Mac 当前目录；容器对它的写入会落到 Mac。`--rm` 不会撤销挂载目录的修改。只读分析可在挂载参数末尾加 `,readonly`。

数据库等持久数据可使用命名卷：

```bash
docker volume create research-data
docker volume ls
```

命名卷独立于容器生命周期，见 [Docker 数据持久化](https://docs.docker.com/get-started/docker-concepts/running-containers/persisting-container-data/)。删除容器之前先确认数据究竟在容器内部、绑定目录还是命名卷。

## 四、构建自己的环境

在一个新的演示目录中，用 VSCode 或纯文本编辑器新建名为 `Dockerfile` 的文件（无扩展名），粘贴并保存以下内容。终端用 `cd` 进入该文件所在目录后，再运行后面的构建命令：

```dockerfile
FROM python:3.12-slim
WORKDIR /work
RUN python -m pip install --no-cache-dir ase==3.22.1
CMD ["python", "-c", "import ase; print(ase.__version__)"]
```

然后构建和检查：

```bash
docker build -t research-ase:demo .
docker run --rm research-ase:demo
```

以 ASE 为例，输出应为所固定的版本。正式复现还需要记录基础镜像 digest、所有依赖版本和构建条件；只有一个 Dockerfile 不等于环境永远不变。用 `.dockerignore` 排除 `.git`、密钥、`.env` 和大型计算输出。

## 五、服务、日志与退出

以临时静态网页为例：

```bash
docker run -d --name handbook-web -p 127.0.0.1:8080:80 nginx:stable-alpine
docker logs --tail 30 handbook-web
curl -I http://127.0.0.1:8080
docker stop handbook-web
docker rm handbook-web
```

`8080:80` 把本机端口映射到容器端口；指定 `127.0.0.1` 只供本机访问。名称已存在时先 `docker ps -a` 检查，不直接删掉同名容器。

## 六、代理与资源

拉取镜像失败时检查 Docker Desktop → Settings 中的代理设置，见 [Docker Desktop 设置](https://docs.docker.com/desktop/settings-and-maintenance/settings/)。Mac 终端的 `http_proxy` 不一定控制 Docker daemon 的下载。

容器内的 localhost 指容器自身。访问 Mac 服务通常使用 `host.docker.internal`，但代理端口是否可用还取决于监听地址和网络。先用一次连通测试确认，再把代理参数写进自己的运行命令。

在 Settings → Resources 中按本机内存设置 CPU、内存和磁盘上限，给 macOS 留出余量。清理时先查看 `docker system df`，只删除确认不需要的对象；带卷的清理会影响持久数据。
