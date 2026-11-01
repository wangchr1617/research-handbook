# pip 与 uv 安装与使用

**适用环境：macOS、Linux、Windows；激活虚拟环境时区分 shell。**

`pip` 安装 Python 包，`uv` 还提供 Python 版本、虚拟环境和项目依赖管理。先选一种环境管理方式，确认 Python 路径，再装包。

## 开始前

还没有 Python 时，先选一条路线：

- 做科学计算、需要 Conda 包：按 [Anaconda、Miniconda、Mamba](Anaconda、Miniconda、Mamba安装与使用.md)安装并创建环境，后续用这个环境的 Python。
- 普通 Python 项目：打开 [Python 官网下载页](https://www.python.org/downloads/)，Windows 选择对应安装器、Mac 选择 macOS 安装包，按向导安装；Linux 按发行版或管理员说明安装 Python 与 venv。
- 准备用 uv 管理项目：直接跳到第三节安装 uv，再用 `uv python install 3.12` 准备 Python。

Windows 用开始菜单打开 PowerShell；Mac 用 Spotlight 搜索“终端”。不要先执行后续安装命令，再猜它会装到哪个 Python。

## 一、pip：明确装到哪个 Python

已有 Python 时先检查：

```bash
python --version
python -m pip --version
```

有些系统命令是 `python3`，把后续命令中的 `python` 相应替换。使用 `python -m pip` 可以明确 pip 属于这个解释器，避免裸 `pip` 指向另一套环境。

Mac / Linux 项目中创建虚拟环境：

```bash
mkdir -p ~/projects/ase-demo
cd ~/projects/ase-demo
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Windows PowerShell 对应：

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip --version
```

如果执行策略禁止激活，可以直接用 `.\.venv\Scripts\python.exe -m pip`，不必为此放宽全局执行策略。Linux 缺少 `venv` / `ensurepip` 时，按发行版或管理员提供的方法安装组件，或使用 Conda 环境。

## 二、安装、检查和记录

以 ASE 为例：

```bash
python -m pip install ase==3.22.1
python -c "import sys, ase; print(sys.executable); print(ase.__version__)"
python -m pip check
python -m pip freeze > requirements.txt
```

`pip check` 检查已声明依赖是否冲突，不验证数值计算结果。`requirements.txt` 记录当前 Python 包版本，通常不包含系统库和编译器信息。

需要临时镜像时，可对单次命令指定：

```bash
python -m pip install ase -i https://pypi.tuna.tsinghua.edu.cn/simple
```

镜像只是下载来源，不是 TLS 报错的通用修复。`--no-deps` 会跳过依赖安装，应仅在已确认依赖齐全时使用。安装到受系统管理的 Python 报错时，改用虚拟环境，不执行 `sudo pip` 或强行覆盖系统包。

## 三、安装 uv

Mac 已有 Homebrew 时：

```bash
brew install uv
uv --version
```

没有 Homebrew 的 Mac / Linux 可先下载官方脚本，再执行：

```bash
curl -LsSf https://astral.sh/uv/install.sh -o /tmp/uv-install.sh
less /tmp/uv-install.sh
sh /tmp/uv-install.sh
```

Windows PowerShell 可使用官方文档列出的 WinGet 方式：

```powershell
winget install --id=astral-sh.uv -e
```

重新打开终端执行 `uv --version`。没有 `winget` 时，从 [uv 官方安装文档](https://docs.astral.sh/uv/getting-started/installation/)选 PowerShell 安装器或 Releases 安装包；不要为了运行示例去改变全局执行策略。

需要由 uv 提供 Python 时再执行：

```bash
uv python install 3.12
```

这一步会下载解释器，需要网络。Homebrew 和 WinGet 安装分别由 `brew upgrade uv`、`winget upgrade --id=astral-sh.uv -e` 更新。

## 四、uv 的两种用法

### 1. 只管理虚拟环境与安装包

在一个新的项目目录执行：

```bash
uv venv --python 3.12
uv pip install --python .venv/bin/python ase
.venv/bin/python -c "import ase; print(ase.__version__)"
uv pip check --python .venv/bin/python
```

Windows 将解释器路径换成 `.venv\Scripts\python.exe`。uv 在需要时可能下载受管理的 Python，断网或受限集群应提前准备可用解释器。使用已有解释器可写 `uv venv --python /absolute/path/to/python`。

`uv pip` 是 uv 的命令接口，不代表该环境已安装 pip。环境选择规则见 [uv 环境说明](https://docs.astral.sh/uv/pip/environments/)。

### 2. 管理完整项目

在另一个新目录演示：

```bash
uv init materials-demo
cd materials-demo
uv add ase
uv run python -c "import ase; print(ase.__version__)"
uv sync --locked
```

`uv add` 更新 `pyproject.toml` 和 `uv.lock`；`uv run` 在项目环境运行程序；`uv sync --locked` 要求现有锁文件与项目声明一致。团队协作时提交这两个文件，`.venv/` 不提交。

`uv sync` 默认会使环境与项目声明保持一致，可能移除未声明的包；不要把它指向仍需手工维护的混合环境。详见 [uv 项目指南](https://docs.astral.sh/uv/guides/projects/)。

## 五、离线集群与编译依赖

可以在与目标 Linux、CPU 架构和 Python 版本匹配的联网环境准备 wheel：

```bash
python -m pip download --only-binary=:all: -r requirements.txt -d wheelhouse
```

上传后，在集群的目标虚拟环境执行：

```bash
python -m pip install --no-index --find-links=wheelhouse -r requirements.txt
python -m pip check
```

缺少对应 wheel 时该下载会失败，需要另行处理编译或兼容版本；不能把 Mac 的 wheel 直接带到 Linux 使用。目标系统 glibc 版本也会影响 wheel 兼容性。

科学计算包报编译错误时，先确认 Python、编译器和系统库要求，再考虑源码构建，见 [高性能计算软件编译常识](高性能计算软件编译常识.md)。pip 的详细选项见 [官方用户指南](https://pip.pypa.io/en/stable/user_guide/)。
