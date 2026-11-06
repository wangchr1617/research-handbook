# SSH 连接与文件同步

**适用环境：macOS、Linux；Windows 可用 OpenSSH / MobaXterm，rsync 示例在 WSL 执行。**

SSH 用于远程登录，SCP、SFTP 或 rsync 用于传输文件。先确认账号和连接，再传一个小文件，最后同步完整计算目录。

## 一、准备连接

向管理员索取主机地址、端口、账号和主机密钥指纹。校园网外需要学校 VPN 时先连接。Mac 详细配置见 [SSH 与密钥](../Codex连接科研集群（macOS）.md)，Windows 见 [新生入门](../新生入门（Windows）.md)。

首次登录的基本形式：

```bash
ssh -p 2022 YOUR_USER@login.cluster.example.org
```

地址和账号均需替换，不能照抄示例。密码输入不显示字符；登录后检查 `id -un`、`hostname`、`pwd`，再用 `exit` 返回本机。

## 二、使用别名

在本机 `~/.ssh/config` 中加入，已有配置时保留原内容：

```sshconfig
Host lab-cluster
    HostName login.cluster.example.org
    User YOUR_USER
    Port 2022
    ServerAliveInterval 30
    ForwardAgent no
```

配置好后可用 `ssh lab-cluster`。首次连接仍需核对指纹；更换主机时向管理员确认，不直接清空 `known_hosts`。私钥留在本机，`.pub` 公钥才添加到远端个人账号。

## 三、先传一个小文件

先在远端个人目录建立 `~/projects/demo`。下面在本机运行：

```bash
scp ./input.inp lab-cluster:~/projects/demo/
mkdir -p ./downloaded
scp lab-cluster:~/projects/demo/input.inp ./downloaded/
cmp ./input.inp ./downloaded/input.inp
```

`cmp` 无输出并返回 `0` 说明往返文件内容一致。用别名时 SCP 会读取对应端口；不用别名时，SCP 指定端口为大写 `-P`，与 SSH 的小写 `-p` 不同。

## 四、重复同步用 rsync

先确认本机和远端都有 `rsync`，没有时使用 SCP / SFTP 即可。下载结果前先预览：

```bash
rsync -avhn lab-cluster:~/projects/demo/results/ ./results/
```

检查列表后再执行去掉 `n` 的命令：

```bash
rsync -avh lab-cluster:~/projects/demo/results/ ./results/
```

`-n` 是 dry-run，`-a` 保留常见文件属性，`-v` 显示过程，`-h` 使大小更易读。源路径末尾的 `/` 表示复制目录内容；没有它时目录层级可能不同，先用小目录练习。

默认同步不会删除目标端多出的文件，不把 `--delete` 放进新手常用命令。正在写入的轨迹或数据库不保证复制后内容一致；确认作业完成、文件写完，再下载最终结果。

独立 PBS 作业不随 SSH 退出而取消，查询与下载时再连接，见 [PBS](../PBS作业管理系统使用.md)。

参考：[OpenSSH 配置](https://man.openbsd.org/ssh_config)、[rsync 官方手册](https://download.samba.org/pub/rsync/rsync.1)。
