# 从裸机规划到双节点 Slurm 集群

适用环境：Linux。下面的教学练习使用两台 Ubuntu 24.04 LTS 虚拟机与发行版 Slurm 软件包；正式集群按对应发行版和固定版本手册部署。macOS/Windows 在本机通过 SSH 管理，不执行服务端安装命令。

## 先确定角色与服务

案例集群中，管理节点运行 `slurmctld`，计算节点运行 `slurmd`，作业数据库由 `slurmdbd` 连接 MariaDB。登录节点提供 SSH、编辑和提交入口；共享盘提供软件、项目与家目录，计算节点本地盘承接临时 I/O。起步可合并部分服务，备份和故障影响仍按角色分别评估。

| 服务 | 上线前提 | 检查判据 |
| --- | --- | --- |
| 地址与名称 | 固定主机名、地址、DNS 或统一 hosts | 每节点解析同一名称得到预期地址 |
| 时钟 | chrony/systemd-timesyncd 等统一授时 | 时钟同步正常，认证不因漂移失效 |
| 身份 | 用户 UID/GID 一致，服务账号稳定 | 同一用户在所有节点看到相同文件属主 |
| 软件环境 | 同版本编译器、MPI、数学库与 modulefile | 相同输入在各节点运行、依赖路径一致 |
| 共享与本地盘 | 挂载点、权限、配额、scratch 策略 | 用户读写正常，挂载失败能被识别 |
| 调度与隔离 | 节点资源、队列、cgroup 与 GPU GRES | 申请资源与实际可用资源一致 |

跨节点程序通常显式分布数据；Slurm 负责分配资源，MPI 负责进程通信，NFS 负责共享文件，三者的职责分别验证。容器、Kubernetes 适合相应服务/容器工作负载，批量 MPI 计算可先采用 Slurm；引入 Kubernetes 时仍需解决 GPU、RDMA、存储、调度与权限，不会自动获得 HPC 环境。

## 裸机部署顺序

1. 完成[装机兼容检查](供电散热与装机兼容性.md)，记录 BMC、BIOS、网卡/磁盘固件和所有设备序列号。
2. 选定 OS 与驱动支持组合，安装一台样机，完成驱动、网络、时钟、用户、存储和软件基准。保存软件包版本与配置到受控仓库，密钥单独管理。
3. 用镜像/PXE、Kickstart/Autoinstall 或配置管理工具复制系统。为每台机器生成唯一主机标识、地址和 SSH host key，不能把母机身份完整克隆到所有节点。
4. 配置共享盘和工具链，验证单节点程序，再接入 Slurm；最后做多节点应用和并发验收。
5. 固定通过验证的版本，准备重装和回滚步骤，先在备用节点验证更新，再滚动维护。

可参考 [OpenHPC](https://openhpc.community/)的配套安装 recipe，选择其明确支持的发行版与发布版本，不混拼多个发行版的包和服务路径。

## 两台虚拟机的完整基础练习

练习拓扑：`head` 为控制/提交端，`c01` 为计算端；两台均 2 vCPU、4 GiB 内存，位于彼此可达的私网。使用新建、无正式数据的虚拟机，先保存快照。该练习只验证非 MPI 的 Slurm 调度与资源约束，后续扩展再加入共享文件、GPU 与跨节点 MPI。

### 1. 准备名称、账号与软件

在两台虚拟机分别设置正确主机名，并配置静态地址及名称解析。例如 `/etc/hosts` 的教学片段如下，地址替换成实际私网地址，不覆盖文件中的 localhost 等条目：

```text
192.168.50.10 head
192.168.50.11 c01
```

两端运行以下检查：

```bash
hostname -s
getent hosts head c01
timedatectl status
id student
```

提前创建教学账号 `student`，两端 UID/GID 相同，并确保其家目录可写；这个例子不要求用户免密 SSH。时钟同步正常后，在两端安装发行版软件包：

```bash
sudo apt update
sudo apt install slurm-wlm slurm-client munge
scontrol --version
id slurm
```

两端 `scontrol --version` 应一致，记录 `apt-cache policy slurm-wlm`。发行版会创建服务账号；若实际包布局不同，按该包的文档和 systemd unit 查找配置位置。教学采用 `/etc/slurm`；不要同时启用两个来自不同安装前缀的 Slurm。

### 2. 建立认证

本练习采用 MUNGE，控制端与计算端共享同一 `/etc/munge/munge.key`，文件属主为 `munge:munge`，权限为 `0400`。使用系统包提供的密钥或 MUNGE 密钥生成工具创建一次，经受控加密通道复制到另一台；密钥不放入公开笔记、代码仓库或日志。两端启动并检查：

```bash
sudo systemctl enable --now munge
munge -n | unmunge
```

本机解码应为成功。还需从 head 执行 `munge -n | ssh c01 unmunge`，确认跨节点解码成功；SSH 使用当前有权限的测试账号。失败时依次查密钥一致性、权限、服务和时间，不能通过关闭认证来绕过。

### 3. 获取资源并编写配置

在 c01 执行 `slurmd -C`，得到实际 CPU 拓扑和内存。下面是 `/etc/slurm/slurm.conf` 的完整教学最小配置，复制到两端。`NodeName` 行中的资源必须按输出替换；示例将 4 GiB 虚拟机的可调度内存设为 3000 MiB，为 OS 留空间。

```ini
ClusterName=teaching
SlurmctldHost=head
SlurmUser=slurm
AuthType=auth/munge
StateSaveLocation=/var/lib/slurm/slurmctld
SlurmdSpoolDir=/var/lib/slurm/slurmd
SlurmctldPort=6817
SlurmdPort=6818
SwitchType=switch/none
MpiDefault=none
ProctrackType=proctrack/cgroup
TaskPlugin=task/cgroup,task/affinity
SelectType=select/cons_tres
SelectTypeParameters=CR_Core_Memory
ReturnToService=1
NodeName=c01 CPUs=2 Boards=1 SocketsPerBoard=1 CoresPerSocket=2 ThreadsPerCore=1 RealMemory=3000 State=UNKNOWN
PartitionName=cpu Nodes=c01 Default=YES MaxTime=01:00:00 State=UP
```

现代 systemd/cgroup v2 环境在两端建立 `/etc/slurm/cgroup.conf`，以安装版本支持的插件为准：

```ini
CgroupPlugin=autodetect
ConstrainCores=yes
ConstrainRAMSpace=yes
ConstrainDevices=yes
```

在 head 创建控制器状态目录，在 c01 创建计算守护进程目录：

```bash
# head，管理员执行
sudo install -d -o slurm -g slurm -m 0750 /var/lib/slurm/slurmctld
# c01，管理员执行
sudo install -d -o root -g root -m 0755 /var/lib/slurm/slurmd
```

私网防火墙仅允许必要节点访问控制与计算服务端口；作业步和 MPI 的额外通信按所选版本文档单独规划。生产环境还要设置提交用户、登录入口和服务权限边界。cgroup 配置读取后必须进行真实限制测试，不能仅以配置文件存在认定隔离生效。

### 4. 启动并排查节点状态

head 只启动 `slurmctld`，c01 只启动 `slurmd`；禁用软件包可能预设的非本机角色服务：

```bash
# head
sudo systemctl disable --now slurmd
sudo systemctl enable --now slurmctld
# c01
sudo systemctl disable --now slurmctld
sudo systemctl enable --now slurmd
```

然后在 head 执行：

```bash
scontrol ping
sinfo -Nel
scontrol show node c01
```

控制器应响应，节点在无任务时进入 IDLE。若为 DOWN/DRAIN，查看 `Reason`，两端用 `journalctl -u slurmctld -u slurmd -b` 查日志，核对资源、主机名、认证和 cgroup；修正原因后由管理员恢复节点，而非反复清除 DRAIN 掩盖故障。

### 5. 提交一个可核对结果的作业

以 student 在 head 保存 `hello.sbatch`，在其可写目录执行 `sbatch hello.sbatch`：

```bash
#!/bin/bash
#SBATCH --job-name=hello
#SBATCH --partition=cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=256M
#SBATCH --time=00:02:00
#SBATCH --chdir=/tmp
#SBATCH --output=/home/student/slurm-%j.out
set -eu
hostname
printf 'job=%s cpus=%s\n' "$SLURM_JOB_ID" "$SLURM_CPUS_PER_TASK"
grep Cpus_allowed_list /proc/self/status
sleep 10
```

Slurm 会传送脚本，`--chdir=/tmp` 避免依赖共享工作目录。输出路径位于 **c01 的** `/home/student/`，需按实际账号替换；运行后在 c01 查看对应文件，确认主机名、作业号和 CPU 允许列表。生产集群用同路径共享家目录或项目盘解决集中访问输出。提交端用 `squeue` 看排队和运行状态，`scontrol show job 作业号` 检查申请与退出信息；本练习未配置持久记账，`sacct` 不作为成功判据。

这个例子只运行单进程，不把 `srun hostname` 成功解释为 MPI 已验证。下一步可增加第二台计算虚拟机 c02，按同样流程接入并更新 `NodeName` 与分区，再用 `srun -N2 -n2 hostname` 检查两节点启动；真实 MPI 则按下面的兼容要求单独构建和测试。

## 从练习扩展到科研服务

| 扩展项 | 要做什么 | 如何确认 |
| --- | --- | --- |
| MPI | 按安装版检查 `srun --mpi=list`，编译匹配的 PMI/PMIx 与 MPI | 两节点 MPI 数值测试正确，通信后端符合预期 |
| GPU | `GresTypes=gpu`、节点 GRES 与 `gres.conf` 匹配实际设备；自动发现需相应插件依赖 | 单卡/多卡申请数量正确，未申请设备的进程确实被限制 |
| 记账 | 配置 slurmdbd、数据库、账号关联、采集插件和备份 | `sacct` 能查完成作业，资源字段与监控相符 |
| 公平使用 | 分区、QOS、账号上限、最长时限与公平份额 | 两用户并发时策略生效，超限申请被拒绝或等待 |
| 共享与软件 | NFS/并行盘、统一 UID/GID、Module、版本化工具链 | 输入、程序与结果均可追溯，节点依赖一致 |
| 可靠性 | 控制器状态、数据库、配置与密钥的备份，必要时备用控制器 | 停服和恢复演练成功，恢复点与时间符合要求 |

GPU 的 `CUDA_VISIBLE_DEVICES` 等可见性设置不等于设备权限隔离；结合 cgroup 在受控测试账号下验证。Slurm 资源约束也不提供针对互不信任用户的完整安全边界；这类服务需额外设计账号、主机与运行环境隔离。面向课题组的起步部署先限制在受管理用户与内网范围。

原有 PBS 用户可将队列理解为 Slurm 的 partition 附近概念，但资源表达不能机械替换。PBS 的 `select/ncpus/mpiprocs/ompthreads` 迁移时分别核对节点数、进程数和线程数；Slurm 的 CPU 计数还受 SMT 与配置影响。先迁移一份最小作业，对照实际拓扑和结果，再批量转换。

## 官方依据

- [Slurm 管理入门](https://slurm.schedmd.com/quickstart_admin.html)：角色、依赖、认证与安装。
- [slurm.conf](https://slurm.schedmd.com/slurm.conf.html)、[cgroup.conf](https://slurm.schedmd.com/cgroup.conf.html)：配置字段与版本限制。
- [cgroup 机制](https://slurm.schedmd.com/cgroups.html)、[GRES](https://slurm.schedmd.com/gres.html)：资源约束与 GPU 配置。
- [MPI 指南](https://slurm.schedmd.com/mpi_guide.html)、[sbatch](https://slurm.schedmd.com/sbatch.html)、[记账指南](https://slurm.schedmd.com/accounting.html)：并行启动、提交语义与资源记录。
- [Ubuntu slurm-wlm 包](https://packages.ubuntu.com/noble/slurm-wlm)：练习发行版的包入口。在线 Slurm 手册可能领先发行版，先查本机同版本 `man` 页面。
