# Anaconda、Miniconda、Mamba 安装与使用

**适用环境：Windows、macOS、Linux；安装器必须匹配系统和 CPU 架构。**

Conda 既能管理环境，也能安装 Python 和科学计算依赖。以 ASE、pymatgen 的后处理环境为例，单独建一个环境，比把所有软件都装进 base 容易维护。

## 一、几个名字的区别

| 工具 | 用途 |
| --- | --- |
| Anaconda Distribution | 带 Conda 和大量预装包的发行版，下载和占用较大 |
| Miniconda | 只带 Conda、Python 等基本组件，按需安装其他包 |
| Miniforge | 面向 conda-forge 的精简发行版，包含 Conda 和 Mamba |
| Mamba | 与 Conda 类似的环境与包管理工具，不是 Python 发行版 |

普通科研环境可先选 Miniconda 或 Miniforge；已有 Anaconda 正常工作时，不必为了换名字再装一套。发行版下载见 [Conda 安装说明](https://docs.conda.io/projects/conda/en/stable/user-guide/install/index.html)与 [Miniforge 官网](https://conda-forge.org/download/)，各软件源的使用条款按自己的机构情况核对。

## 二、安装

先从下面选择一个入口，不需要三个都安装：

| 选择 | 下载入口 | 第一次怎样选 |
| --- | --- | --- |
| Anaconda | [官方安装包](https://www.anaconda.com/download/success) | 想随发行版获取一批常用包时选择 |
| Miniconda | [官方安装指引](https://www.anaconda.com/docs/getting-started/installation)、[安装包归档](https://repo.anaconda.com/miniconda/) | 按系统和架构找 Miniconda 安装器 |
| Miniforge | [官方 Releases](https://github.com/conda-forge/miniforge/releases/latest) | 在 Assets 中选择对应平台的 Miniforge3 安装器 |

Windows 在“设置 → 系统 → 系统信息”查看系统类型，Mac 在“关于本机”查看芯片，Linux 执行 `uname -m`。Linux 安装前还要用 `ldd --version` 查看 glibc，旧系统先核对安装器最低要求，不直接运行最新版。不确定时先核对系统与架构，再下载。

Windows 下载 `.exe`，选择个人用户安装，优先从安装器提供的 Prompt 打开，不需要管理员终端，也不必把整套路径手动加入系统 PATH。已有 Windows 图解见 [Anaconda 安装与虚拟环境](../notes/python/Anaconda安装与虚拟环境.md)，日常操作以本篇为准。

Mac / Linux 从官方页面下载安装脚本并核对校验值。Apple Silicon 使用 macOS arm64，Intel Mac 使用 macOS x86_64；Linux x86_64 安装器不能在 Mac 直接运行。

下面以 Mac arm64 的 Miniforge 安装器为例，文件路径按自己的下载位置修改：

```bash
bash "$HOME/Downloads/Miniforge3-MacOSX-arm64.sh"
```

按提示阅读条款并选择未使用的个人安装目录，例如 `~/Software/miniforge3`，当询问是否初始化 shell 时按需确认。已有同名目录时不要覆盖。

Linux x86_64 用户从同一 Releases 页面下载 `Miniforge3-Linux-x86_64.sh`。集群不能直接下载时，可先在本机下载 Linux 安装器，再按 [Mac](新生入门（Mac）.md#三连接集群与传文件)或 [Windows](新生入门（Windows）.md)的方法上传到个人目录，随后在 Linux 运行：

```bash
bash "$HOME/Miniforge3-Linux-x86_64.sh"
```

安装后重新打开终端。若没有自动初始化，按真实安装目录执行其中一种：

```bash
# Mac 默认 zsh
"$HOME/Software/miniforge3/bin/conda" init zsh
# Linux 默认 Bash；只执行与自己 shell 匹配的一行
"$HOME/Software/miniforge3/bin/conda" init bash
```

关闭并重新打开终端后检查：

```bash
conda --version
conda info --base
conda info --envs
```

Linux 集群安装前还要查看 `uname -m` 和 `ldd --version`，旧系统可能达不到新安装器的 glibc 要求。按软件部署文档选择受支持版本，不通过替换系统 glibc 解决个人软件安装。

## 三、创建与使用环境

下面在已经初始化 Conda 的终端执行：

```bash
conda create -n materials -c conda-forge python=3.12 ase pymatgen
conda activate materials
python -c "import sys, ase; print(sys.executable); print(ase.__version__)"
conda list
conda deactivate
```

`materials` 是环境名，`python=3.12` 指定 Python 系列。已有同名环境时先查看内容，再决定复用还是换名。

`conda activate` 报错时，按所用 shell 执行 `conda init zsh` 或 `conda init bash` 并重新打开终端。只把 `bin` 放进 PATH 不一定能完成环境激活。

## 四、Mamba 与软件源

Miniforge 安装后可用：

```bash
mamba --version
mamba create -n materials-fast -c conda-forge python=3.12 ase
conda activate materials-fast
```

Mamba 和 Conda 管理的环境通常可共用，不要在同一环境里同时运行两个安装进程。现代 Conda 也有 libmamba 求解器，遇到慢安装时先分清是解依赖慢，还是网络下载慢。

尽量沿用一套一致的软件源。先执行 `conda config --show-sources` 检查已有配置；项目可用 `environment.yml` 声明 channel，避免随手修改全局 `.condarc` 影响其他任务。

## 五、Conda 与 pip 配合

先用 Conda 装可用的依赖，再用当前环境的 Python 安装剩余包：

```bash
conda activate materials
python -m pip --version
python -m pip install dpdata
python -m pip check
```

不要在同一终端同时激活 Conda 和另一套 `.venv`。用过 pip 后再大量改变 Conda 依赖可能引入不一致，复杂环境优先修改环境说明后重建。

## 六、记录与复现

```bash
conda env export --from-history > environment.yml
conda env export > environment-full.yml
conda list --explicit > explicit-spec.txt
```

`--from-history` 主要保留手动请求的 Conda 包，跨平台更容易调整，但不完整记录 pip 安装项；完整导出更详细，也更依赖平台。`explicit-spec.txt` 主要用于同平台 Conda 包复现，pip 项需另行记录。分享前检查文件中的个人路径和带凭据的软件源地址。

```bash
conda env create -n materials-copy -f environment.yml
```

环境目录不能直接从 Mac 复制到 Linux 使用。离线环境也不能凭空创建：需要目标平台可用的缓存、离线源或预先打包的同平台环境；`--clone base` 只复制现有环境，不会得到指定的新 Python 版本。

删除前确认环境名，并先退出该环境：

```bash
conda deactivate
conda env remove -n materials-copy
```

集群批处理中的激活示例、软件安装节点要求，以本集群说明和 [PBS 笔记](PBS作业管理系统使用.md)为准。
