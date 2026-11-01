# Alkemie 集群部署（Windows）

**适用环境：Windows 10 / 11（PowerShell、OpenSSH、浏览器）+ Linux（服务端）。**

Windows 负责上传源码和打开浏览器，Alkemie 依赖及服务仍安装在 Linux 集群。本篇采用 PowerShell + OpenSSH，不要求先安装 WSL 或 Docker。

## 一、准备 SSH 与源码

先连接学校要求的 VPN。在 PowerShell 检查：

```powershell
Get-Command ssh, scp, tar, git
ssh -V
```

缺少 OpenSSH 时，打开 Windows 设置 → 应用 → 可选功能（不同系统版本位置可能不同），搜索并安装 **OpenSSH Client**，只连接远端不需要安装 Server。操作见 [微软 OpenSSH 安装说明](https://learn.microsoft.com/en-us/windows-server/administration/openssh/openssh_install_firstuse)。

Git 从 [Git for Windows 官方下载页](https://git-scm.com/downloads/win)下载安装，按安装向导完成后重新打开 PowerShell，执行 `git --version`。已有 MobaXterm 也可用其 SFTP 上传文件，见[新生入门（Windows）](新生入门（Windows）.md)。

先向管理员申请集群账号、VPN 和常驻服务许可。再在 PowerShell 创建 SSH 配置目录并打开配置文件：

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.ssh"
notepad "$env:USERPROFILE\.ssh\config"
```

在记事本中保存为没有 `.txt` 后缀的 `config` 文件。下面全部为示例，向管理员索取实际主机名、端口和账号后替换：

```sshconfig
Host lab-cluster
    HostName login.cluster.example.org
    Port 2022
    User YOUR_USER
    ServerAliveInterval 30
    ForwardAgent no
```

```powershell
ssh lab-cluster
```

首次连接核对主机指纹，登录后用 `id -un`、`hostname` 确认账号，`exit` 返回 PowerShell。使用公钥时，只上传 `.pub` 公钥，私钥保留在 Windows。

## 二、PowerShell 打包上传

没有源码时，先在 PowerShell 中创建个人项目目录，再克隆：

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\projects"
Set-Location "$env:USERPROFILE\projects"
git clone https://github.com/hfood02/Alkemie.git
Set-Location Alkemie
```

新克隆的项目已经在正确目录；已有源码时先用 `Set-Location` 进入自己的实际项目路径。然后检查并打包：

```powershell
git status --short
git rev-parse HEAD
git archive --format=tar -o ..\alkemie-source.tar HEAD
tar -tf ..\alkemie-source.tar
scp ..\alkemie-source.tar lab-cluster:~/
```

`git archive HEAD` 只包含当前提交中的文件；未提交修改不会被带过去。检查归档不含密钥、私人数据和本机依赖。

Windows 的 `node_modules`、Conda 环境与 `.exe` 不上传到 Linux 充当运行依赖；前端和后端按服务端环境构建。

## 三、Linux 部署

PowerShell 执行 `ssh lab-cluster` 后，当前终端就进入 Linux。按 [Alkemie 服务端准备](Alkemie集群部署（macOS）.md#三linux-服务端准备环境)完成解压、Conda 环境和依赖，再按[配置与部署](Alkemie集群部署（macOS）.md#四配置与部署)设置根目录 `.env` 并运行 `backend/deploy.sh`。

两种本机系统共用同一套 Linux 服务端步骤：本例是个人 `local` profile、远端 `127.0.0.1:8445`、不启用 nginx、通过 SSH 隧道访问 HTTP。Linux 命令中的 `$HOME`、`source`、`conda activate` 在远端 shell 执行，不粘贴进未登录的 PowerShell。

如果是更新现有部署，先按[更新说明](Alkemie集群部署（macOS）.md#七更新现有部署)备份并保留现有数据，不能用新建部署覆盖已有工作区。

## 四、Windows 隧道与浏览器

保持服务运行，在新的 PowerShell 窗口执行，命令写成一行：

```powershell
ssh -N -T -o ExitOnForwardFailure=yes -L 127.0.0.1:8445:127.0.0.1:8445 lab-cluster
```

这个窗口保持打开。再开 PowerShell 检查：

```powershell
curl.exe --fail --show-error http://127.0.0.1:8445/api/server/health
```

浏览器打开 `http://127.0.0.1:8445`，依次检查页面、登录和 WebSocket，再按[部署后验证](Alkemie集群部署（macOS）.md#六部署后验证与停止)检查 PBS。若选择 HTTPS 部署，则使用实际协议和端口。

本机端口被占用时，将转发命令第一个 `8445` 改为 `18445`，浏览器和 curl 同步改用 `18445`。不要直接结束占用端口的未知进程。

## 五、Windows 常见问题

| 问题 | 处理 |
| --- | --- |
| PowerShell 不认识 Bash 的换行 `\` | Windows 命令写成一行；Linux 多行命令在 SSH 登录后执行 |
| 脚本出现 `^M` 或 `bad interpreter` | 将远端 shell 脚本保存为 LF 换行，避免 CRLF |
| 浏览器能联网，远端安装依赖失败 | Windows 系统代理不会自动传入 Linux，检查 [DOVE 远端代理](DOVE加速器配置与使用技巧.md#五通过-ssh-给远端临时使用) |
| MobaXterm 连得上，PowerShell 连不上 | 两者的密钥、SSH 配置和 agent 可能不同，分别检查 |
| 隧道没退出但页面打不开 | 分别检查远端健康接口、隧道端口、服务协议和浏览器日志 |

用完在隧道窗口按 `Ctrl+C` 断开；远端服务如何停止，以部署输出的管理方式为准。
