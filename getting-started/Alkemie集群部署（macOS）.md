# Alkemie 集群部署（macOS）

**适用环境：macOS（SSH 与浏览器）+ Linux（Alkemie 服务端与计算集群）。**

Mac 负责上传代码、建立隧道和访问网页，Alkemie 服务运行在管理员允许的 Linux 服务节点。下面以个人账号、单用户 `local` profile 为例；计算任务仍通过 PBS 提交。

## 开始前

第一次部署先按顺序准备：

1. 按 [Mac 新生入门](新生入门（Mac）.md)安装 Git、确认终端可用。
2. 向集群管理员申请个人账号、VPN 和常驻服务许可，按 [SSH 配置教程](../notes/getting-started/Codex连接科研集群（macOS）.md)创建 `lab-cluster` 别名，并确认 `ssh lab-cluster` 能登录。
3. 没有源码时，从第二节的 `git clone` 开始，不先执行 `/path/to/Alkemie` 这个占位路径。
4. 在 Linux 服务端按 [Conda 安装](Anaconda、Miniconda、Mamba安装与使用.md#二安装)准备环境，再继续第三节。Mac 上安装的 Conda 不会自动出现在集群上。

## 一、确认版本与部署位置

以下流程适用于 Alkemie `46bd5523` 版本：使用根目录 `.env.example` 与 `backend/deploy.sh` 部署，实时服务采用 Uvicorn / ASGI Socket.IO。其他版本的配置项与部署脚本应按对应文档调整。

部署前阅读目标版本的 [Alkemie 部署文档](https://github.com/hfood02/Alkemie/blob/main/docs/deployment.md)。确认集群允许常驻服务、安装依赖和前端构建；登录节点不允许这些操作时，改用获准的服务节点或构建环境。

下面假设已配置 SSH 别名 `lab-cluster`，见 [Mac 集群连接](../notes/getting-started/Codex连接科研集群（macOS）.md)。服务端口以 `8445` 为例，不代表它在你的机器上空闲。

## 二、Mac 准备源码并上传

已有项目时进入实际目录，先看状态和版本，不直接覆盖部署目录；`/path/to/Alkemie` 需要替换为自己的路径：

```bash
cd /path/to/Alkemie
git status --short
git rev-parse HEAD
```

没有源码时，可从项目仓库获取：

```bash
git clone https://github.com/hfood02/Alkemie.git
cd Alkemie
```

下面只打包当前提交中已跟踪的源码，不包含未提交修改、未跟踪文件和依赖目录。需要部署本地修改时，应先检查并形成明确的提交，再打包。

```bash
git archive --format=tar -o ../alkemie-source.tar HEAD
tar -tf ../alkemie-source.tar
scp ../alkemie-source.tar lab-cluster:~/
```

上传前检查归档列表没有凭据和私人数据。Mac 的 `node_modules`、Conda 环境和二进制包不直接复制到 Linux 使用。

## 三、Linux 服务端准备环境

从这里开始，命令在远端 Linux 执行。首次部署使用新目录；如果目录已经存在，先按第七节处理更新。

```bash
ssh lab-cluster
uname -m
ldd --version | head -n 1
mkdir -p "$HOME/Software"
mkdir "$HOME/Software/Alkemie"
cd "$HOME/Software/Alkemie"
tar -xf "$HOME/alkemie-source.tar"
```

本例假设兼容的 Conda 已安装，见 [Conda 与 Mamba](Anaconda、Miniconda、Mamba安装与使用.md)。Alkemie 当前文档要求 Python 3.12，并给出了旧 glibc 系统的专用安装器方案；安装前核对目标版本文档，不直接在旧系统运行最新版安装器。

```bash
conda create -n alkemie python=3.12
conda activate alkemie
conda install -c conda-forge 'nodejs>=20.19,<21' faiss-cpu tiktoken
python --version
node --version
```

这些 Node.js 条件来自上述 Alkemie 版本，不是所有项目的通用要求。断网集群需先准备同平台依赖或按 [DOVE 隧道](DOVE加速器配置与使用技巧.md)临时联网；`--offline` 不能替你补齐尚未安装的依赖。

## 四、配置与部署

首次部署在源码根目录执行，已有 `.env` 时保留并逐项合并新配置：

```bash
cp .env.example .env
chmod 600 .env
vi .env
```

个人单用户部署至少核对：

```ini
ALKEMIE_DEPLOYMENT_PROFILE=local
ALKEMIE_HOST=127.0.0.1
ALKEMIE_WORKSPACES_ROOT=/absolute/path/to/alkemie-workspaces
ALKEMIE_SCHEDULER_TYPE=pbs
```

工作区用真实绝对路径，队列、核数和时限依据当前 PBS 配置填写，不能照搬模板中的历史 `batch` 默认值。需要 AI 功能时再配置自己的供应商地址、模型和密钥；没有配置模型时，单独检查哪些功能可用。

```bash
cd backend
bash deploy.sh --help
bash deploy.sh --cn-mirror --port 8445 --skip-ssl
```

本例不启用 nginx，绑定远端回环地址，通过 SSH 访问 HTTP；`--skip-ssl` 仅适用于本例这种受控隧道访问，外网公开服务应另配 TLS、身份与执行隔离。共享服务的 `shared` / `cluster` profile、PostgreSQL 和 Gateway 需要按项目文档单独部署，不能仅把 `local` 改名就视为完成隔离。

部署脚本会安装依赖、构建前端、生成服务脚本，并根据环境选择服务管理方式。记录脚本打印的实际工作区、服务目录、管理方式和日志路径；失败后从日志定位，不手工拼凑另一套依赖版本继续覆盖。

## 五、Mac 建立隧道并检查

在 Mac 新开终端：

```bash
ssh -N -T -o ExitOnForwardFailure=yes \
  -L 127.0.0.1:8445:127.0.0.1:8445 lab-cluster
```

终端保持运行是正常现象，但没有输出不代表后端已健康。另开 Mac 终端检查：

```bash
curl --fail --show-error http://127.0.0.1:8445/api/server/health
```

浏览器打开 `http://127.0.0.1:8445`。如果采用目标项目默认的 TLS 部署方式，访问协议应改为 HTTPS，并按部署文档处理证书。

本机 `8445` 被占用时，可将 `-L` 第一个端口改成 `18445`，浏览器相应使用 `http://127.0.0.1:18445`；远端端口无需因此更改。

## 六、部署后验证与停止

先检查健康接口、静态页面和浏览器 WebSocket 连接；再登录并检查项目、文件访问和预期权限。目标源码提供只读验证入口，可在 Linux 源码根目录运行：

```bash
npm run test:deployment -- --base-url http://127.0.0.1:8445
```

需要真实计算时，再用小输入核对生成的 PBS 脚本、提交账号、作业 ID 和程序结果。健康接口成功不能代替登录、WebSocket 和 PBS 验证。带 `--agents --write` 的回归会创建临时对象并可能消耗模型额度，按目标项目说明另行运行。

服务管理以部署输出为准：使用 systemd user service 时查看对应服务状态和日志；手工模式则使用实际服务目录生成的 `start.sh`、`stop.sh`。默认服务目录结构是 `工作区根目录/alkemie-server/`，先核对再执行。

停止本次 SSH 隧道，在 Mac 对应终端按 `Ctrl+C`。这不会自动停止远端 Alkemie，更不会取消独立的 PBS 作业。端口冲突先检查进程所有者、命令和目录，不使用按端口强杀的方式清场。

## 七、更新现有部署

先记录代码版本、服务状态和现有未提交修改，备份 `.env`、数据库以及实际工作区文件（包括附件）。数据库要用对应数据库工具一致性备份，不把运行中的数据库文件随手复制当作完整备份。

在独立源码目录准备更新，保留原 `ALKEMIE_WORKSPACES_ROOT`、数据库连接、账号、团队、项目和权限；合并新配置项后按目标版本说明重新部署。更新后重复健康、登录、WebSocket 和小作业检查。失败时按备份与版本记录回退，不重新初始化数据库代替修复。
