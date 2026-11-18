# 基于 Docker 与 Apptainer 配置 OVITO

本机用图形界面检查结构，或者在独立 Python 环境里批处理，通常已经够用。如果分析脚本要在 Linux 集群运行，而节点上的系统库装不到当前环境，可以在有 Docker 的 Linux 机器上准备镜像，再交给集群的 Apptainer。下面沿用[两原子配位脚本](OVITOPython批量分析.md)，让两种运行环境都用同一份输入验收。

## 一、把 Python 和系统库装进镜像

在有 Docker 构建权限的 Linux 环境中准备 `Dockerfile`。下面保留 Ubuntu 24.04 和 Python 3.12 的构建记录，按目标节点的 CPU 架构选择构建环境。需要复现同一分析环境时，记下实际装入的 OVITO 版本，并保存使用的镜像。

```dockerfile
FROM ubuntu:24.04

# 避免 systemd 相关问题
ENV DEBIAN_FRONTEND=noninteractive
ENV INITRD=No
ENV container=docker

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

# 安装 Python 3.12
RUN apt install -y python3.12 python3.12-dev python3.12-venv && \
    ln -s /usr/bin/python3.12 /usr/local/bin/python && \
    ln -s /usr/bin/python3.12 /usr/local/bin/python3

RUN python3.12 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN /opt/venv/bin/python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    /opt/venv/bin/pip install ovito -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    /opt/venv/bin/pip install ase -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    /opt/venv/bin/pip install pymatgen -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    /opt/venv/bin/pip install matplotlib -i https://pypi.tuna.tsinghua.edu.cn/simple

# 验证环境
RUN python -c "import ovito; print('OVITO版本:', ovito.version)" && \
    ldd --version | head -n 1

# 设置工作目录
WORKDIR /app

# 启动命令（示例）
CMD ["bash"]
```

在 `Dockerfile` 所在目录运行：

```bash
docker build -t ovito_python_3.12 .
```

构建中的 `import ovito` 用来发现解释器或系统库加载问题。导入通过后，还应读取实际格式并执行修改器。将基础篇的 `two-atoms.dump` 与批处理篇的 `analyze.py` 放到同一个练习目录。先在这个目录运行：

```bash
docker run --rm --mount "type=bind,source=$PWD,target=/app" ovito_python_3.12 \
  python /app/analyze.py /app/two-atoms.dump /app/docker-coordination.csv --cutoff 2.5
```

`/app` 是容器内路径，对应宿主机当前目录。脚本使用独占创建方式写 CSV，重跑时换一个输出名。Docker 的挂载规则见[官方文档](https://docs.docker.com/engine/storage/bind-mounts/)。

## 二、将构建产物交给 Apptainer

在 Docker 主机导出刚验证过的镜像：

```bash
docker save -o ovito_python_3.12.tar ovito_python_3.12
```

将归档传到集群上自己可读写的目录。按站点说明加载 Apptainer，并在归档所在目录构建 SIF。已有同名 SIF 时，可为本次构建使用新文件名。

```bash
module load apptainer
apptainer build ovito_python.sif "docker-archive://$PWD/ovito_python_3.12.tar"
```

归档 URI 需要指向实际文件。站点允许的构建位置、权限与临时空间按当地环境确认。构建入口见 [Apptainer 文档](https://apptainer.org/docs/user/latest/cli/apptainer_build.html)。

## 三、用同一帧核对容器结果

把 SIF 放到同一个练习目录，或在命令中替换为镜像的实际路径。运行：

```bash
apptainer exec --bind "$PWD:/app" ovito_python.sif \
  /opt/venv/bin/python /app/analyze.py /app/two-atoms.dump /app/sif-coordination.csv --cutoff 2.5
```

两个 CSV 都应有一行数据：帧号 0、原子数 2、平均配位数 1。若容器能导入 OVITO 却读不到文件，先检查绑定目录和脚本所用的容器内路径。若能读入但写不出 CSV，检查输出是否已存在、挂载目录是否可写。小例通过后，再把相同命令和输入路径放进批处理脚本，记录镜像与分析参数。
