# WSL 及 Docker 安装

**适用环境：Windows + WSL 2（Ubuntu）。**

## 一、WSL 2 安装

WSL 2 在 Windows 中提供 Linux 环境。下面以 Ubuntu 为例，先跑通 WSL，再决定要不要用代理和 Docker。若只需远程登录集群，按[Windows 新生入门](新生入门（Windows）.md)配置 SSH 客户端即可。

先查看 [微软 WSL 官方安装指南](https://learn.microsoft.com/en-us/windows/wsl/install)，确认 Windows 版本满足要求。在开始菜单搜索 PowerShell，右键“以管理员身份运行”，执行：

```powershell
wsl --install
```

按提示重启，打开新安装的 Ubuntu，创建 Linux 用户名和密码（不要求与 Windows 相同，输入密码时不显示字符）。再在 PowerShell 检查并更新：

```powershell
wsl --update
wsl -l -v
```

默认安装会启用所需组件，不要求先手工勾选完整 Hyper-V。缺少虚拟化支持时按微软文档检查 BIOS / UEFI 设置。

**再次启动 WSL 时，只需要在终端内键入 `wsl` 即可。**

> 如果 Linux 文件系统不想安装在 C 盘，可以从 [网址](https://cloud-images.ubuntu.com/releases/focal/release/) 下载所需发行版的 `.tar.gz` 文件。
> 假设 `.tar.gz` 文件位于 `D:\Ubuntu` 文件夹下，并且你希望将其导入到 `D:\Ubuntu\Ubuntu-20.04` 路径下，运行：
>
> ```powershell
> wsl --import MyUbuntu D:\Ubuntu\MyUbuntu D:\Ubuntu\ubuntu-20.04.tar.gz
> ```
>
> 执行后，WSL 会将 `ubuntu-20.04.tar.gz` 导入到 `D:\Ubuntu\MyUbuntu` 文件夹，并创建该路径下的 Linux 文件系统。
> 可以使用 `wsl --set-default MyUbuntu` 将新的发行版设置为默认。

WSL 安装完成后记得使用 `wsl -l -v` 确保 Ubuntu 发行版已更新为 WSL 2。

首次创建账户成功后可以使用命令 `sudo apt update && sudo apt upgrade -y` 更新软件源并升级所有包；
并使用命令 `sudo apt install -y git curl wget vim` 安装开发常用基础工具。

MobaXterm 提供了对 WSL 的直接支持，无需复杂配置。
打开 MobaXterm，点击顶部工具栏的 "Session" 按钮，在弹出的对话框中选择 "WSL"（在右侧的选项中），点击 OK，MobaXterm 将打开对应的 WSL 终端。

---

## 二、WSL 中配置代理（Windows 端运行 Clash）

还没有代理服务时，先按 [DOVE 注册、购买与安装](DOVE加速器配置与使用技巧.md#一注册购买和安装)在 Windows 跑通客户端。下面是已有 Clash 用户的历史配置；使用 DOVE 时以客户端实际的协议、地址和端口替换，不照搬 `7890`。

支持镜像网络的系统可在 `WSL Settings` 检查 `Mirrored` 模式；该模式与 NAT 模式的宿主机地址取法不同。

勾选 clash `允许局域网`，查看端口号（默认是 7890）。
然后在 cmd 中使用命令 `ipconfig` 查看以太网适配器 `vEthernet (WSL (Hyper-V firewall))` 的 IPv4 地址（一般是以 172 开头，例如：172.31.0.1）。

先检查代理监听和防火墙。镜像网络可尝试 `127.0.0.1`；NAT 网络按实际宿主机地址设置，只开放确实需要的访问范围。HTTP 代理不要求默认将 DNS 监听改成 `0.0.0.0:53`。

在 WSL 的 Shell 配置文件（如 ~/.bashrc）中添加代理设置：

```bash
export host_ip="172.31.0.1"
export HTTP_PROXY="http://$host_ip:7890"
export HTTPS_PROXY="http://$host_ip:7890"
export ALL_PROXY="socks5://$host_ip:7890"
```

运行以下命令，即可临时禁用代理环境变量：

```bash
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY
```

---

## 三、先选 Docker 后端，再跑通最小容器

如果日常在 Windows 上开发，且环境允许安装 Docker Desktop，可启用 WSL 2 后端，并在 Docker Desktop 的 WSL Integration 中选择自己的 Ubuntu 发行版。若要在自己的 Ubuntu 发行版内直接维护 Docker Engine，按 Ubuntu 版本和架构使用官方安装说明。先选定一个后端。已有镜像、容器或卷时，切换前确认数据保存在哪个后端。 [Docker Desktop 的 WSL 2 说明](https://docs.docker.com/desktop/features/wsl/) · [Docker Engine 的 Ubuntu 安装说明](https://docs.docker.com/engine/install/ubuntu/)

在已经启用集成的 Ubuntu 终端验证：

```bash
docker context show
docker version
docker run --rm hello-world
```

`docker version` 应能取得客户端和服务端信息。只有客户端信息时，先查 Docker Desktop 是否运行、当前发行版是否已开启集成，以及 context 指向哪里。直接用 Docker Engine 的环境按本机配置决定是否需要 `sudo`。后文保留了 Engine 路线的 `sudo docker` 示例，Desktop 集成下通常直接使用 `docker`。

`hello-world` 会拉取镜像并启动一个短容器。服务端已连通却拉取失败时，再检查镜像地址、网络和 Docker 后端的代理设置。终端能下载文件说明的是该终端的网络，Docker 后端下载镜像时可能用另一份配置。

## 四、搜索 Docker 镜像

我们可以从叫做 [Docker hub](https://hub.docker.com/) 的 Docker 官方库获得镜像，或者我们也可以制作自己的镜像。

使用 `docker search` 命令搜索 Docker 镜像，例如：

```bash
sudo docker search ubuntu
```

---

## 五、下载 Docker 镜像

使用 `docker pull` 命令下载 Docker 镜像，例如：

```bash
sudo docker pull ubuntu:20.04 # 指定 Ubuntu 镜像版本是 20.04
```

此 Linux Docker Engine 示例使用默认数据目录 `/var/lib/docker`；实际存储位置以运行服务的配置为准。

使用 `docker images` 命令查看所有已下载的 Docker 镜像，输出如下：

```text
wchr@LAPTOP-SPENR6IJ:/mnt/c/Users/wangchangrui$ docker images
REPOSITORY   TAG       IMAGE ID       CREATED       SIZE
ubuntu       20.04     b7bab04fd9aa   6 weeks ago   72.8MB
```

---

## 六、运行 Docker 容器

基于 Docker 镜像的标签（TAG）或者 ID（Image ID），我们可以使用 `docker run` 命令创建并启动一个新的容器，例如：

```bash
sudo docker run -it ubuntu:20.04 /bin/bash # 使用 --name 参数给创建的容器命名
sudo docker run -it b7bab04fd9aa /bin/bash
```

启动容器后，会自动进入容器的 shell（命令行）。

在容器中，可以使用 `exit` 命令终止容器的运行并脱离。
或者按住 `CTRL + P` 然后 `CTRL + Q` 脱离但不关闭容器。

脱离后，使用 `docker ps -a` 命令可以看到当前容器仍在运行（Up）。

```text
wchr@LAPTOP-SPENR6IJ:/mnt/c/Users/wangchangrui$ docker ps
CONTAINER ID   IMAGE          COMMAND       CREATED         STATUS         PORTS     NAMES
2105f3ec080a   ubuntu:20.04   "/bin/bash"   3 minutes ago   Up 3 minutes             hardcore_austin
```

当一个新容器被创建后，会自动分配一个唯一的 ID 和 Name。
注意，容器 ID 和 Docker 镜像 ID 是不同的。

我们可以使用 `docker attach` 命令连接到正在运行的容器：

```bash
sudo docker attach 2105f3ec080a # 基于容器 ID
```

同样按住 `CTRL + P` 然后 `CTRL + Q` 从容器脱离。

使用下面的命令从 Docker 的主机系统中终止正在运行的容器：

```bash
sudo docker stop 2105f3ec080a # 用空格隔开 ID 可以同时退出多个容器
sudo docker kill 2105f3ec080a # 强制关闭，谨慎使用
```

如果需要启动一个已停止的容器（不创建新容器），使用 `docker start` 命令。

---

## 七、构建自定义 Docker 镜像

我们可以创建自定义的 Docker 镜像，避免不同系统、软件间的环境冲突。

### Dockerfile 构建镜像（以 Ovito 为例）

通过文本文件（Dockerfile）定义镜像的构建步骤，包括基础镜像、依赖安装、文件复制、环境变量配置等。

在一个空目录下，新建一个名为 Dockerfile 文件，并在文件内添加以下内容：

```shell
# 指定基础镜像，用于后续的指令构建。
FROM ubuntu:24.04

# 在容器内部设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV INITRD=No
ENV container=docker

# 使用 RUN 在镜像中执行 shell 命令。
RUN apt update && apt upgrade -y && \
    apt install -y \
    wget \
    curl \
    git \
    build-essential \
    zlib1g-dev \
    libffi-dev \
    libssl-dev \
    libsqlite3-dev \
    libbz2-dev \
    liblzma-dev \
    libreadline-dev \
    vim

# 安装 Qt6 图形库
RUN apt install -y --no-install-recommends \
    libqt6core6 \
    libqt6gui6 \
    libqt6widgets6 \
    libgl1-mesa-dev

# 安装 Python
RUN apt install -y python3.12 python3.12-dev python3.12-venv && \
    ln -s /usr/bin/python3.12 /usr/local/bin/python && \
    ln -s /usr/bin/python3.12 /usr/local/bin/python3

# 使用轻量级包管理工具 venv
RUN python3.12 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN /opt/venv/bin/python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    /opt/venv/bin/pip install ovito -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    /opt/venv/bin/pip install ase -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    /opt/venv/bin/pip install pymatgen -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    /opt/venv/bin/pip install matplotlib -i https://pypi.tuna.tsinghua.edu.cn/simple

# 验证安装是否成功
RUN python -c "import ovito; print('OVITO版本:', ovito.version)" && ldd --version | head -n 1

# 设置后续指令的工作目录。
WORKDIR /app

# 指定容器创建时的默认命令。
CMD ["bash"]
```

`CMD` 类似于 `RUN` 指令，用于运行程序，但二者运行的时间点不同：

- `CMD` 在 `docker run` 时运行（如果 Dockerfile 中存在多个 CMD 指令，仅最后一个生效）。
- `RUN` 是在 `docker build` 时运行。

组织 Dockerfile 时同时考虑依赖缓存和镜像体积；相关安装命令可用 `&&` 连接，便于在同一步处理依赖。

在 Dockerfile 文件的存放目录下，执行构建命令：

```bash
docker build -t ovito_python_3.12:v1 . # （镜像名称:镜像标签）
```

### 直接构建自定义镜像（以 QMCPACK 为例）

首先 `docker pull ghcr.io/qmcpack/ubuntu22-openmpi:latest` 拉取镜像，使用 `docker images` 获取镜像 ID。

启动名为 qmcpack-4.1.0 的临时容器：

```bash
docker run -it --user root --name qmcpack-4.1.0 ghcr.io/qmcpack/ubuntu22-openmpi:latest /bin/bash
```

克隆 QMCPACK 源代码：

```bash
git clone https://github.com/QMCPACK/qmcpack.git
```

或者上传下载到本地的 QMCPACK 源代码并解压：

```bash
docker cp /mnt/e/qmcpack-4.1.0.tar.gz 04cc6d9f0259:/opt/
docker attach 04cc6d9f0259
cd /opt/
tar -xzvf qmcpack-4.1.0.tar.gz
```

编译 QMCPACK

```bash
cd qmcpack-4.1.0/build
cmake -GNinja -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_C_COMPILER=mpicc -DCMAKE_CXX_COMPILER=mpicxx -DQMC_COMPLEX=0 ..
ninja
ninja install
```

测试 QMCPACK 是否编译成功：

```text
ctest -VV -R deterministic-unit_test_wavefunction_trialwf
ctest -L deterministic
```

按住 `CTRL + P` 然后 `CTRL + Q` 脱离容器，
使用命令 `docker commit qmcpack-4.1.0 qmcpack:v4.1.0` 重建镜像。

然后 `docker save -o qmcpack-4.1.0.tar qmcpack:v4.1.0` 保存镜像为 `.tar` 文件。
注意，镜像名称需与重建的镜像一致，生成的 `qmcpack-4.1.0.tar` 文件即为镜像归档文件。

删除镜像命令是 `docker rmi [镜像 ID]`。

---

### 通过 apptainer 在计算节点上配置（以 QMCPACK 为例）

上传 `.tar` 文件到个人目录。下面保留历史权限命令，实际只授予运行账号所需的读取权限，不使用全员可写权限：

```text
chmod 777 qmcpack-4.1.0.tar
```

通过 Apptainer 将其转换为 `.sif` 镜像：

```bash
module load apptainer
apptainer build --sandbox qmcpack-sandbox docker-archive:///home/your-user/Software/qmcpack/qmcpack-4.1.0.tar
apptainer build qmcpack.sif qmcpack-sandbox
```

QMCPACK 程序已编译并固化到镜像中，输入、输出和工作目录仍需在容器中可访问。

运行形式为 `apptainer exec qmcpack.sif qmcpack <参数>` 即可。
