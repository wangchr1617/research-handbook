# Codex 连接科研集群（macOS）

**适用环境：macOS（本机）+ Linux（集群端）。**

采用“本机 Codex → SSH → PBS”：Mac 负责准备输入、提交、查询和下载，集群负责计算。Codex 保持在本机运行，集群无需安装 Codex。

下文地址、账号和端口均为示例，请替换成自己的配置。实际连接信息保存在本机，密码和私钥不要放进共享仓库。

## 配置 SSH

需要校园 VPN 时，先用学校提供的客户端（如 EasyConnect）登录。确认 VPN 已连接，再配置 SSH。

为集群创建独立密钥；已有同名文件时换一个名称，避免覆盖：

```bash
mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"
ssh-keygen -t ed25519 -f "$HOME/.ssh/id_ed25519_lab" -C "lab-cluster"
```

按提示设置密钥口令。将公钥 `id_ed25519_lab.pub` 加入远端个人账号的 `~/.ssh/authorized_keys`，保留已有条目；私钥 `id_ed25519_lab` 留在本机。远端 `.ssh` 目录和 `authorized_keys` 的权限分别设为 `700` 和 `600`。

编辑本机 `~/.ssh/config`，在通用的 `Host *` 配置之前加入：

```sshconfig
Host lab-cluster
    HostName login.cluster.example.org
    Port 22
    User YOUR_CLUSTER_USER
    IdentityFile ~/.ssh/id_ed25519_lab
    IdentitiesOnly yes
    AddKeysToAgent yes
    ServerAliveInterval 30
    ServerAliveCountMax 3
    ForwardAgent no
    StrictHostKeyChecking ask
```

替换 `HostName`、`Port`、`User` 和密钥路径。`lab-cluster` 是本机别名；需要跳板机时，按管理员说明添加 `ProxyJump`。配置项见 [OpenSSH 手册](https://man.openbsd.org/ssh_config)。

在 Mac 终端设置权限，并将带口令的密钥加入钥匙串与 agent：

```bash
chmod 600 "$HOME/.ssh/config" "$HOME/.ssh/id_ed25519_lab"
/usr/bin/ssh-add --apple-use-keychain "$HOME/.ssh/id_ed25519_lab"
```

## 验证连接

先检查配置，再交互登录：

```bash
ssh -G lab-cluster
ssh lab-cluster
```

`ssh -G` 只显示配置，不连接集群。首次登录时，将主机密钥指纹与管理员提供的指纹核对后再确认；登录后运行 `id -un` 和 `hostname` 检查账号与主机，用 `exit` 返回 Mac。

随后在 Mac 验证免交互登录：

```bash
ssh -n -o BatchMode=yes -o ConnectTimeout=5 lab-cluster 'id -un; hostname'
```

直接返回预期结果后，再让 Codex 使用同一命令。`BatchMode=yes` 禁止密码提示，`-n` 避免读取标准输入；免交互依靠已解锁的密钥，不要求私钥没有口令。

## 在 Codex 中操作

可以先给 Codex 一个只读任务：

```text
请通过 SSH 别名 lab-cluster 检查当前账号与主机，并查询我自己的 PBS 作业。
本次不提交或取消作业；需要权限时说明用途并按当前策略处理。
```

如果终端能连接而 Codex 不能，检查 Codex 会话的 SSH agent、运行用户和网络权限。按需授权即可，相关设置见 [OpenAI 权限说明](https://learn.chatgpt.com/docs/agent-approvals-security)。远端操作权限由集群账号决定，本机工作区隔离不能保护远端目录。

将实际工作目录、PBS 命令路径和可用队列记在仓库外的私人速查中，供后续任务读取。

## 提交作业与下载结果

计算和耗资源的后处理通过 PBS 执行，参考 [PBS 模板](../../inputs/pbs/README.md)。以下命令在 Mac 运行，替换账号、PBS 路径和项目目录：

```bash
# 查询自己的作业
ssh -n -o BatchMode=yes lab-cluster \
  '/path/to/pbs/bin/qstat -u YOUR_CLUSTER_USER'

# 确认输入、队列、核数和时限后提交
ssh -n -o BatchMode=yes lab-cluster \
  'cd /absolute/path/to/project && /path/to/pbs/bin/qsub job.pbs'

# 下载结果
mkdir -p "$HOME/Downloads/project-results"
scp -r lab-cluster:/absolute/path/to/project/results/. \
  "$HOME/Downloads/project-results/"
```

记录提交返回的作业 ID。连接中断后，先查作业和日志再决定是否重试，避免重复提交。作业从队列消失后，还需检查退出状态、程序完成标记和预期输出。

## VPN 与定时监测

同一 VPN 账号在多设备间会互相挤下线时，约定按需切换设备。独立的 PBS 批处理作业提交后，通常可以断开 VPN；查询和下载时再连接。

定时监测需要 Mac 保持唤醒、Codex 与模型服务可用、VPN 在线、SSH 免交互。重启或锁屏后应重新检查。VPN 自动登录依赖桌面状态，遇到验证码或二次验证交由本人处理；不要让定时任务反复抢占另一台设备的 VPN 会话。

## 可选：远端使用本机代理

只有远端程序需要外网、且集群允许转发时才建立隧道。DOVE 等客户端的 HTTP 代理假设监听本机 `127.0.0.1:7890`，远端端口用 `18080` 举例：

```bash
ssh -N -T -o BatchMode=yes -o ExitOnForwardFailure=yes \
  -R 127.0.0.1:18080:127.0.0.1:7890 lab-cluster
```

保持 Mac 上该终端打开，在另一个终端登录集群后设置代理并测试：

```bash
export HTTP_PROXY=http://127.0.0.1:18080
export HTTPS_PROXY=http://127.0.0.1:18080
export http_proxy="$HTTP_PROXY"
export https_proxy="$HTTPS_PROXY"
curl -I --connect-timeout 5 --max-time 15 https://example.com
```

这是 HTTP 代理，因此 `HTTPS_PROXY` 的值也以 `http://` 开头。变量仅影响当前 shell 及其子进程，已提交的 PBS 作业不会自动使用它。

用完后在远端执行 `unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy`，再在隧道终端按 `Ctrl+C`。核对远端端口只监听回环地址；端口冲突时换端口，不终止他人的会话。Mac 休眠、VPN 断开或代理退出都会使隧道不可用。转发参数见 [OpenSSH 手册](https://man.openbsd.org/ssh)。

## 常见问题

| 现象 | 检查方向 |
| --- | --- |
| 连接超时 | VPN 状态、主机地址、SSH 端口、跳板机 |
| `Permission denied (publickey)` | 账号、所用密钥、公钥安装位置与权限 |
| 主机指纹校验失败 | 找管理员核对是否更换主机，不直接清空 `known_hosts` |
| Codex 无法连接 | 会话的 agent、运行用户、网络权限 |
| 找不到 `qstat` / `qsub` | 非交互 SSH 的 `PATH`，改用确认过的绝对路径 |
| 隧道已建立但无外网 | 本机代理状态、协议、端口和远端变量 |
