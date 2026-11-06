# PBS 作业管理系统使用

**适用环境：Linux 集群。下面以 Torque 风格 PBS 为例，PBS Pro / OpenPBS 的资源语法需按本集群说明调整。**

PBS 负责排队、分配计算节点和运行作业。登录节点用于准备输入、提交与查看日志；计算任务通过作业脚本交给计算节点运行。

## 开始前

先向管理员申请集群账号，索取 VPN、SSH 地址和本集群的 PBS 使用说明，再按 [Mac](新生入门（Mac）.md)或 [Windows](新生入门（Windows）.md)教程登录。下文命令都在 SSH 登录后的 Linux 终端执行。

PBS 客户端通常由集群统一提供，个人 Mac / Windows 无需先下载安装 PBS。登录后如果找不到 `qsub`，向管理员确认初始化脚本或命令路径。保存脚本可用 `vi hello.pbs`，按 `i` 粘贴代码、`Esc` 后输入 `:wq` 保存，详见 [Linux 文本编辑](linux/Linux命令行使用与常用命令.md#四编辑文本)。

## 一、提交前先看资源

在集群终端执行：

```bash
command -v qsub
qstat -q
qstat -Qf
qstat -u "$USER"
```

确认队列名称、核数范围、内存和最长运行时间。如果非交互 SSH 找不到命令，使用管理员确认过的 PBS 绝对路径。某些队列有最小 CPU 数量，即使只是测试也要满足限制。

旧笔记中的 `batch`、24 核和软件安装路径只是当时环境，不代表当前可用配置。不要直接按历史脚本申请资源；集群队列、账号配额和 GPU 申请方式以当前查询和管理员说明为准。

## 二、先提交一个小测试

下面是 Torque 的资源写法。保存为 `hello.pbs`，将 `YOUR_QUEUE`、核数和内存改为本队列允许的值：

```bash
#!/bin/bash
#PBS -N hello-pbs
#PBS -q YOUR_QUEUE
#PBS -l nodes=1:ppn=32
#PBS -l walltime=00:05:00
#PBS -l mem=2gb
#PBS -j oe
#PBS -S /bin/bash

set -eu
cd "${PBS_O_WORKDIR:?}"
printf 'job=%s queue=%s\n' "$PBS_JOBID" "$PBS_QUEUE"
hostname
date
wc -l "$PBS_NODEFILE"
```

`#PBS` 指令放在脚本开头、可执行命令之前。`nodes=1:ppn=32` 表示申请一个节点的 32 个 CPU 槽位；`walltime` 是实际经过的时间上限，不是 CPU 时间之和。`mem` 的作用范围按本集群资源定义核对，多节点作业尤其要确认。

```bash
qsub hello.pbs
# 假设返回 12345.server；后续替换为自己的完整作业 ID
qstat -f 12345.server
```

不要用 `bash hello.pbs` 代替提交，这会忽略 `#PBS` 指令并在当前节点运行。默认输出通常是提交目录下的 `hello-pbs.o作业号`，实际位置看 `qstat -f` 的 `Output_Path`。

## 三、常用查询与取消

| 命令 | 用途 |
| --- | --- |
| `qstat -u "$USER"` | 查看自己的作业 |
| `qstat -f 12345.server` | 查看资源、路径、状态和调度备注 |
| `qstat -q` | 查看队列摘要 |
| `pbsnodes -a` | 查看可见节点状态与属性 |
| `qdel 12345.server` | 取消这个作业，执行前确认账号和作业 ID |

常见状态：`Q` 排队，`R` 运行，`H` 挂起，`E` 正在退出，`C` 完成（是否保留完成记录取决于配置）。`E` 不等于计算出错，`C` 也不保证程序结果正确。`showq`、`checkjob` 通常属于配套调度器，不是所有 PBS 系统都提供。

作业一直排队时先看资源申请和 `comment`，再检查队列时限与账号配额。不要连续重复提交同一个任务。

## 四、运行 MPI / OpenMP 软件

在资源指令之后、运行程序之前，按 [Module 使用](Module使用.md)加载与该软件匹配的环境。下面是 MPI 段落示例，软件与 MPI 模块名称要从当前集群确认：

```bash
# 先在此处加载已确认的软件模块
export OMP_NUM_THREADS=1
NP=$(wc -l < "$PBS_NODEFILE")
EXEC=/absolute/path/to/program
mpirun -np "$NP" -machinefile "$PBS_NODEFILE" "$EXEC" > program.out 2> program.err
```

这个启动参数仅适用于支持该写法的 MPI，优先使用集群已经验证的模板。OpenMPI、Intel MPI、MPICH 的集成方式不能随意混用。

纯 OpenMP 程序按实际申请的 CPU 槽位设置线程；混合并行时，**每节点 MPI 进程数 × 每进程线程数**不超过该节点分配的 CPU 槽位。不要拿总核数同时作为每个进程的线程数。

PBS Pro / OpenPBS 常见另一种写法为 `select=1:ncpus=32:mpiprocs=32:ompthreads=1`，这是替换 Torque 资源行的示例，不应与 `nodes/ppn` 原样混在同一脚本。完整参数参考 [Torque 资源申请手册](https://docs.adaptivecomputing.com/torque/6-1-1/adminGuide/Content/topics/torque/2-jobs/requestingRes.htm)及本集群手册。

## 五、检查结果与后续操作

作业从 `qstat` 消失后，检查调度日志、错误输出、退出状态以及程序自己的完成标记。保留历史记录的系统可在作业退出后短时间内用 `qstat -f` 查看 `exit_status`；记录已清除时，按管理员提供的 accounting 方法查询。

以 VASP 为例，程序正常退出后还要检查电子步和离子步是否达到预期收敛条件；得到一个输出文件不等于计算成功。修改输入后建新目录再提交，避免覆盖前一次结果。

软件脚本见 [PBS 输入模板](../inputs/pbs/README.md)，批量工作见 [VASP 批量计算](../notes/VASP/基础与准备/VASP批量计算.md)。模板里的队列、路径和历史版本仍需逐项替换。

## 六、几个实用的作业管理技巧

### 1. qmove：排队时换一个合适的队列

作业还在 `Q` 状态，发现原队列不适合时，可以先检查目标队列，再尝试迁移，不必先取消重交。下面的 `TARGET_QUEUE` 和作业号都要替换：

```bash
qstat -f 12345.server
qstat -Qf TARGET_QUEUE
qmove TARGET_QUEUE 12345.server
qstat -f 12345.server
```

参数顺序是“目标队列 → 作业 ID”。检查迁移后的 `queue`、`job_state` 和 `Resource_List`，确认仍符合预期。这里采用同一服务器内换队列的用法。

Torque 不允许移动运行、转移或退出中的作业。目标队列还要接受当前账号及资源申请；换队列不会自动把核数、内存和时限改成合适的值，也不保证更快启动。遇到拒绝先看错误和队列限制，不能用换队列绕过配额。

语法见 [Torque qmove 手册](https://docs.adaptivecomputing.com/torque/6-1-3/adminGuide/torqueAdminGuide-6.1.3.pdf)中的 qmove 条目；其他 PBS 实现按各自手册和站点策略确认。

### 2. qalter：修改尚未运行作业的属性

例如排队时发现申请时间过长，确认实际所需时间后可以修改：

```bash
qalter -l walltime=02:00:00 12345.server
qstat -f 12345.server
```

这会修改服务器保存的作业属性，不会改本地 `.pbs` 文件；本地模板也要同步记录，避免下次又用旧值。已运行作业能改哪些属性由权限和策略决定，不能把上述例子当作通用的运行中续时命令。详见 [qalter 手册](https://docs.adaptivecomputing.com/torque/6-1-0/adminGuide/Content/topics/torque/commands/qalter.htm)。

### 3. afterok：前一步成功后再启动下一步

以结构优化之后做静态计算为例，先分别准备两个目录的输入和作业脚本，再逐步提交：

```bash
cd "$HOME/projects/GeTe/relax"
qsub relax.pbs
# 记录返回的完整作业 ID，例如 12345.server
cd "$HOME/projects/GeTe/static"
qsub -W depend=afterok:12345.server static.pbs
```

第二个作业等待前一个以退出状态 `0` 结束。它不会自动复制优化后的结构，也不判断物理收敛；后一步脚本应先检查完成标记，再从已确认的位置复制所需结果。

前一步脚本也要正确返回失败状态，不能让程序失败后被末尾的成功命令掩盖。依赖语法见 [qsub 手册](https://docs.adaptivecomputing.com/torque/6-1-0/adminGuide/Content/topics/torque/commands/qsub.htm)的 `-W depend` 说明。

### 4. 改了脚本，不等于改了已提交的作业

`qsub` 提交时就把脚本交给服务器。之后编辑本地 `.pbs`，不会替换服务器中的脚本；工作目录里的输入文件则可能仍会被作业启动时读取。排队期间不要随手改同一目录的输入，最好每次提交对应独立目录。

追踪日志可以用 `tail -f program.out`，按 `Ctrl+C` 只结束查看。查询任务不必每秒刷新，通常隔几十秒或几分钟查一次即可；队列中消失后仍按第五节检查结果。
