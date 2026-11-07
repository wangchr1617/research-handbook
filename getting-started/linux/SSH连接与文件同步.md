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

## 五、大型计算文件的压缩与归档

VASP 的文本输出、CP2K 的文本 restart、Molden、Cube 和 XYZ 轨迹往往适合无损压缩；已经压缩过的文件再次压缩，通常收益较小。二进制文件也可能有可压缩空间，不能仅凭“文本/二进制”决定。先选代表文件比较压缩后大小、耗时、内存和接收端兼容性，再选择已有工具；不必为少量传输安装新的压缩程序。

打包与压缩是两件事：tar 将多个文件组织为一个归档，gzip、xz、zstd 等再压缩字节流；ZIP 等容器也可包含多个文件。无损压缩解压后应恢复原文件字节。

减少轨迹小数位、抽帧、删掉空轨道或降低 Cube 网格则改变了科学数据，即使体积更小，也应另存为派生数据并记录处理方式，不能称为原始数据的无损归档。

先确认计算已结束或取得一致的文件快照，再归档输入、关键日志和需要保留的结果。检查归档内的文件列表，在独立目录试解包，并比较关键文件的大小或内容校验和；只有列出文件名并不证明所有数据可恢复。跨机器传输后再次验证，验证通过前保留原文件。解包位置应与现有计算目录分开，避免同名文件被覆盖。

大型 `WAVECAR`、CP2K 电子重启文件及完整轨迹是否长期保留，取决于续算和分析需求。公开仓库优先保存小型输入、代表数据、生成脚本与必要说明，大文件另放合适的数据存储，并记录版本、校验和及访问方法。压缩包不是独立备份；同一磁盘上的原文件和压缩副本仍有共同失效风险。并行压缩还需限制线程与内存，按可用资源运行，不能默认占用全部核心。
