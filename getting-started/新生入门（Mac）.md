# 新生入门（Mac）

**适用环境：macOS（本机）+ Linux（集群端）。**

Mac 自带终端和 SSH，不需要再装 MobaXterm。先把本机环境准备好，再连接集群、传文件，最后提交一个小作业。

## 开始前

按 `Cmd+空格` 打开 Spotlight，输入“终端”并回车。下文标为 `bash` 的代码块可在这个终端中运行；复制命令本身，不复制代码块围栏。首次使用先做本机安装，不需要先买集群或模型服务。

需要访问受网络限制的下载站时，先按 [DOVE 注册、购买与安装](DOVE加速器配置与使用技巧.md#一注册购买和安装)准备网络；集群访问还可能需要学校 VPN，两者用途不同。个人集群账号向课题组管理员申请，校园 VPN 的账号和安装包从学校信息化部门获取。

## 一、认识自己的 Mac

点击左上角苹果菜单 → 关于本机，查看芯片和系统版本。Apple Silicon（M 系列）下载 `arm64` / `aarch64` 安装包，Intel 下载 `x86_64` / `amd64` 安装包。`Universal` 应用通常同时支持两种架构。

打开“终端”，执行：

```bash
uname -m
sw_vers
pwd
```

`uname -m` 显示当前终端进程使用的架构；M 系列 Mac 如果显示 `x86_64`，检查是否通过 Rosetta 打开了终端。后续 Python、编译器和依赖尽量保持同一架构。

## 二、安装常用工具

先安装 Apple 命令行工具：

```bash
xcode-select --install
```

根据弹窗完成安装，已有工具时无需重复安装。然后打开 [Homebrew 官网](https://brew.sh/)，复制首页的安装命令到终端执行。安装器提示密码时输入 Mac 的登录密码，屏幕不显示字符是正常现象。

安装结束后找到 `Next steps`，执行其中给出的 `brew shellenv` 命令。Apple Silicon 通常安装到 `/opt/homebrew`，Intel 通常是 `/usr/local`，按安装器实际给出的路径配置，再重新打开终端。

```bash
brew --version
brew install git wget cmake
command -v git
```

VSCode、Python 环境和 Docker 分别参考：

- [VSCode、Claude Code 与 CC Switch 配置](VSCode、ClaudeCode与CC%20Switch配置（Mac）.md)
- [Anaconda、Miniconda、Mamba 安装与使用](Anaconda、Miniconda、Mamba安装与使用.md)
- [Docker 安装与使用](Docker安装与使用（Mac）.md)

不必一次把所有软件装齐；先装当前计算或项目需要的工具就好。

## 三、连接集群与传文件

先向管理员申请个人账号，确认地址、SSH 端口和校园 VPN 的使用方式。下面在 Mac 终端执行，地址和账号需要替换：

```bash
ssh -p 2022 YOUR_USER@login.cluster.example.org
```

首次连接时向管理员核对主机密钥指纹。密码输入时终端不显示字符，直接输入后回车即可。初始密码按管理员要求用 `passwd` 修改。登录后检查：

```bash
id -un
hostname
pwd
```

此时运行的是 Linux 命令。输入 `exit` 回到 Mac，再传文件：

```bash
# Mac → 集群：先在远端建立 ~/projects/demo 目录
scp -P 2022 ./input.inp YOUR_USER@login.cluster.example.org:~/projects/demo/

# 集群 → Mac：下载整个结果目录
mkdir -p "$HOME/Downloads/demo-results"
scp -P 2022 -r YOUR_USER@login.cluster.example.org:~/projects/demo/results/. \
  "$HOME/Downloads/demo-results/"
```

注意：`ssh` 用小写 `-p` 指定端口，`scp` 用大写 `-P`。配置 SSH 别名、独立密钥和免交互登录见 [Mac 集群连接](Codex连接科研集群（macOS）.md)。

## 四、跑通第一个作业

进入集群后，先学习 [Linux 命令行](linux/Linux命令行使用与常用命令.md)，用 [Module](Module使用.md) 加载已有软件，再按 [PBS 作业管理](PBS作业管理系统使用.md) 提交测试。计算和耗资源的后处理放到计算节点运行。

以 GeTe 为例，可以为结构优化、静态计算、能带计算分别建目录，保留每一步的输入、脚本和日志。先核对小体系的能量、单位和完成标记，再扩大规模。

> **ps**：Mac 终端默认多为 zsh，交互配置通常在 `~/.zshrc`；集群常用 Bash，对应 `~/.bashrc`。两台机器的配置文件各自生效，修改前先确认自己在哪台机器。

## 如何判断准备好了

本机工具能够返回版本；SSH 登录返回自己的账号；上传和下载的小文件内容一致；PBS 测试有完整日志并正常结束。最后阅读 [Git 入门](git/Git入门.md)，把可共享的输入和经验留在仓库，账号、密钥和计算大文件留在仓库外。
