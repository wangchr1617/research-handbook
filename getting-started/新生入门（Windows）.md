
# 新生入门第一步

**适用环境：Windows（MobaXterm 客户端）+ Linux（集群端）。**

## 开始前

先向课题组管理员申请个人集群账号，并索取登录地址、SSH 端口、初始密码和主机指纹。校园外访问通常还需学校 VPN，安装包和使用说明从学校信息化部门获取；VPN 登录与集群登录可能是不同账号。

下面从下载 MobaXterm 开始，不要求先安装 Linux、WSL 或 Docker。下载或模型服务访问需要代理时，可先看 [DOVE 注册、购买与安装](DOVE加速器配置与使用技巧.md#一注册购买和安装)。

## MobaXterm 安装及使用

先开通个人集群账号，再用 SSH 客户端连接。下面以 Windows 上的 MobaXterm 为例，介绍登录、传文件和 Linux 基础操作。

> 如果你觉得集群账号没有管理员权限不方便，可以自己在 Windows 里面安装一个 Linux 子系统 WSL2。

SSH 客户端市面上有挺多，我此前使用的 XShell，后面也跟着师兄、师姐转投了 MobaXterm。

访问 [MobaXterm官网](https://mobaxterm.mobatek.net/download.html) 下载 MobaXterm 的安装包，解压后双击 `.msi` 文件根据提示安装。
打开软件后，点击左上角的 Session (会话控制)，在弹出的窗口中选择 SSH，输入 `Remote host`、`Specify username` 和 `Port=2022`，如图所示：

<div align="left">
<img src="assets/first-steps/mobaxterm-001.png" width = "50%" />
</div>

首次登录时，需要输入管理员给的初始密码（输入密码时屏幕不显示字符），然后 Enter 确认进入个人账号。
登录成功后，第一件事是键入 `passwd` 命令根据提示修改密码。首次登录一定要修改初始密码，否则下次用初始密码登录时可能会提示 `access denied`。

MobaXterm 界面分为文件区（左）和终端区。
勾选左下角的 `Follow terminal folder` 可以让两个区块的路径保持一致。
文件传输和下载可以采用直接拖拽的方式。

MobaXterm 一个常用的功能是，在文件区选中两个文件 A 和 B，右键 `Compare text files` 可以直观地比较它们的异同并修改（比命令 `diff A B` 好用很多），如图所示：

<div align="left">
<img src="assets/first-steps/mobaxterm-002.png" width = "50%" />
</div>

---

## 接下来学什么

登录与传输跑通后，分别阅读 [Linux 命令行](Linux命令行使用与常用命令.md)、[PBS 作业管理](PBS作业管理系统使用.md)和 [Module 使用](Module使用.md)。下面保留此前集群环境中的例子，具体队列、软件路径与版本以当前查询为准，不直接作为新账号的默认配置。

## Linux 的基本命令

Linux 命令行是一个强大的工具，它允许用户通过输入特定的命令来执行操作，管理文件和目录，配置网络和系统，以及执行许多其他任务。
对于初学者来说，掌握一些基本的 Linux 命令是非常重要的，这些命令包括文件操作、目录导航、权限设置和文件编辑等。

不熟悉 Linux 命令时，可以参考 [Linux 基础命令教程](../notes/linux/Linux命令参考.chm)（需使用 CHM 阅读器打开）。
可以使用 `man command` 查看 `command` 手册（例如，`man ls` 显示 `ls` 命令的详细介绍），并使用 `q` 退出手册。

先掌握下面这些常用命令：
- `pwd` 是查看当前目录的绝对路径；
- `cd dir/` 是访问 `dir/` 文件夹；
- `ls dir/` 是查看 `dir/` 文件夹列表；
- `mkdir dir/` 是新建文件夹 `dir/`，**注意路径中最好不要出现中文**；
- `cp A B` 是把 `A` 复制为 `B`；
- `cp -r dir1/ dir2/` 是把文件夹 `dir1/` 复制为 `dir2/`；
- `mv A B` 是把 `A` 移动为 `B`；
- `rm A` 是删除文件 `A`；
- `rmdir dir/` 是删除空文件夹；非空目录先核对内容，再决定如何删除；
- `vi A` 是使用 VIM 文本编辑器编辑文件 `A`；
- `cat A` 是查看文件 `A` 的内容；
- `qsub run_vasp.pbs` 是提交运行 VASP 程序的 PBS 脚本；

Linux 最常用的文本编辑器是 VIM。
如前所述，键入命令 `vi XXX` 即可编辑 `XXX` 文件（可以省去 `touch XXX` 创建空文件这一步骤）。
VIM 文本编辑器常用模式有四个：

1. Normal-mode：初始模式，在该模式下可以使用 VIM 快捷键，如 `dd` 剪切光标所在行，`yy` 复制光标所在行，`p` 粘贴行，`u` 撤销上一步操作等等，熟练掌握快捷键能极大地提高你的工作效率；

2. Insert-mode：在初始模式下键入 `i`、`a` 或者 `o` 进入文本编辑模式，编辑完成后需要键入 `Esc` 返回初始模式；

3. Command-mode：在初始模式下键入 `:` 输入命令，`:wq` 保存退出，`:q!` 不保存退出，`:set nu` 显示行号，`:%s/旧文本/新文本/gc` 逐项确认替换。查找则在普通模式下输入 `/str`；

4. Visual-mode：在初始模式下键入 `v` 进入，`Esc` 退出；

在 `~/.vimrc` 中写入 `set number` 即可在 VIM 文本编辑器中显示行号。

> **ps**：
> 除了使用 VIM 文本编辑器，也可以使用命令 `sed` 或 `awk` 实现文本替换。
> 例如命令 `sed "s/A/B/g" XXX > XXX.new` 是替换文本并另存到新文件，检查后再决定是否替换原文件；
> 又如命令 `awk '{ gsub(/dft_forces/, "forces"); print $0 }' train.xyz > out.xyz` 是替换文本中的 `dft_forces` 为 `forces` 并输出到 `out.xyz` 文件中。
> 熟练掌握 VIM 编辑器后可以试一试，效率翻倍！

> **ps**：
> 使用别名 `alias` 可以极大提升工作效率。
> 例如，设置一个别名 `alias ll='ls -al'` 即可键入 `ll` 列出所有文件包括隐藏文件的详细信息。
> 如果要永久使用该别名，可以将该命令写入 `~/.bashrc` 配置文件（文件名前面加一个点表示隐藏文件）里面，然后 `source ~/.bashrc` 加载配置文件即可。
> 单独键入 `alias` 可以列出系统中已设置的所有别名。
> 下面给出我个人的历史 `~/.bashrc` 别名设置，仅供参考；包含删除输出的别名，不建议新手整段复制，先看清每个通配符匹配的文件：
>
> ```shell
> # User specific aliases and functions
> cdls(){
>     \cd "${1}";
>     ls;
> }
> alias cd='cdls'
> alias CD='cd'
> alias LS='ls'
> alias ..='cd ..'
> alias ...='cd ../..'
> alias ....='cd ../../..'
> alias ~='cd ~'
> alias ll='ls -al'
> alias untgz='tar -zxvf'
> alias untar='tar -xvf'
> alias s='qstat -u changruiwang-ICME'
> alias sq='qstat -q'
> alias spath='qstat -f | grep -A 1 Output_Path'
> alias q='showq'
> alias cp='cp -r'
> alias rmvasp='rm C* D* E* O* PC* R* W* X* output vasprun.xml IBZKPT *.[eo]1*'
> alias rmcp2k='rm cp2k.[eo]* cp2k[-_]*'
> alias rmgpumd='rm nep_*.txt nep.restart dump.xyz movie.xyz *.out output gpumd.[eo]* *.png'
>
> alias dush='du -sh ./'                                   # 查看磁盘空间
> alias gpcm='grep cm-1 OUTCAR'                            # 查看 VASP 频率
> alias gpfi='grep f/i OUTCAR'                             # 查看 VASP 虚频
> alias gpdisp='grep Edisp OUTCAR | tail -1'               # 查看 VASP 色散矫正的能量
> alias gpfermi='grep E-fermi OUTCAR | tail -1'            # 查看 VASP 费米能级
> alias gpirr='grep irreducible OUTCAR'                    # 查看 VASP 体系的倒晶格基矢
> alias gpenmax='grep ENMAX POTCAR'                        # 查看 VASP 各个元素的截断能
> alias gpvol='grep volume OUTCAR'                         # 查看 VASP 体积
> alias gprra='grep required OUTCAR'                       # 查看 VASP 是否收敛
> alias gpconv="grep F= OSZICAR | awk '{print \$1,\$5}'"   # 查看 VASP 能量收敛情况
> alias gptit='grep TIT POTCAR'                            # 查看 VASP 赝势元素
> alias gptot='grep TOT OUTCAR'                            # 查看 VASP 能量
> alias gpzval='grep ZVAL OUTCAR'                          # 查看 VASP 价电子
> alias gpela='grep -A9 "TOTAL ELASTIC MODULI" OUTCAR'     # 查看 VASP 弹性常数结果
> alias gphes='grep hessian vasprun.xml'                   # 查看 VASP hessian 矩阵
> alias gpstep='grep = OSZICAR | tail'                     # 查看 VASP AIMD 当前步
> alias gpstatus='grep STATUS ML_LOGFILE | tail'           # 查看 VASP AIMD_MLFF 当前步
> alias cp2kene='grep = cp2k-pos-1.xyz'                    # 查看 CP2K 结构优化每个离子步的能量
> alias cp2kforce='grep Max\.\ g cp2k.out'                 # 查看 CP2K 结构优化每个离子步的受力
> alias cp2kcell='grep CELL cp2k.out'                      # 查看 CP2K 晶胞优化结果
> alias dprun='nohup dpgen run param.json machine.json 1>log 2>err &' # 运行 DPGEN
> alias dpcol='dpgen collect ./ ./collect -p param.json'   # 收集 DPGEN 数据
> alias gpbestcorr="grep Objective_function bestcorr*.out | sort -n -k 2" # 查看 ATAT mcsqs 生成的随机结构
> ```

---

## PBS 作业基本命令

常用的 PBS 作业基本命令有：
- `qsub run.pbs` 提交一个指定脚本；多个脚本应逐个核对后分别提交；
- `qstat -u "$USER"` 查看自己的作业运行情况；
- `showq` 查看所有人的作业运行情况；
- `qdel jobid` 取消作业，`jobid` 通过 `qstat` 查看。

不常用的 PBS 作业命令例如：
- `qmove` 将作业移动到另一个队列；
- `pbsnodes` 列出集群中所有节点的状态和属性等。

PBS 脚本中 PBS 作业属性以 `#PBS` 的方式指定，其中
- `-N`：作业名称；
- `-l`：设定作业所需资源，`nodes` 设定作业所需节点资源，`ppn` 为节点的核数，`walltime` 设定作业所需的最大 wallclock 时间；
- `-q`：设定作业队列名称；
- `-S`：设定 `shell` 类型；
PBS 内置变量包括 `PBS_NODEFILE`（包含作业所用计算节点的文件名）、`PBS_O_WORKDIR`（执行 qsub 命令所在的绝对路径）、`PBS_QUEUE`（作业所执行的队列名称）、`PBS_JOBNAME`（用户指定的作业名称）等。

下面是集群 3 的历史 VASP 作业提交脚本 `run_vasp.pbs`，不是当前队列资源推荐值。
修改变量 `$EXEC` 可以执行不同的计算。

```shell
#PBS -N wchr
#PBS -l nodes=1:ppn=24
#PBS -l walltime=400:00:00
#PBS -q batch
#PBS -V
#PBS -S /bin/bash

source /opt/intel/compilers_and_libraries_2018/linux/bin/compilervars.sh intel64
source /opt/intel/mkl/bin/mklvars.sh intel64
source /opt/intel/impi/2018.1.163/bin64/mpivars.sh

NP=`cat $PBS_NODEFILE | wc -l`
NN=`cat $PBS_NODEFILE | sort | uniq | tee /tmp/nodes.$$ | wc -l`

cat $PBS_NODEFILE > /tmp/nodefile.$$
cd $PBS_O_WORKDIR
ulimit -s unlimited

EXEC=/opt/software/vasp/vasp6.4.0/bin/vasp_std
mpirun -machinefile $PBS_NODEFILE -np $NP $EXEC > output
```

批量提交作业请参考 [VASP 批量计算](../notes/vasp/VASP批量计算.md) 。

---

## 使用集群上已经安装好的软件

在 Linux 中，当同一款编辑器、运行库、软件存在多个版本且多个版本都需要在不同的场景或人员使用时，配置这些内容的环境变量是一个非常繁琐的过程，而 module 工具则提供了一个简单快速的方法。
换言之，通过 module 你可以使用集群上已经安装好的软件。

先用 `type module` 检查工具是否初始化。管理员确认模块目录为 `/opt/modulefiles` 时，用 `module use /opt/modulefiles` 增加搜索路径，不覆盖已有 `MODULEPATH`。

常用的 module 命令如下：
- `module avail`：显示可以使用的模块
- `module load`：加载模块
- `module unload`：卸载模块
- `module list`：显示已经加载的模块

> **ps**：
> 一个小技巧是在 `~/.bashrc` 中添加命令 `module load XXX`，即可自动加载 `XXX` 软件。但是一定要慎重设置，避免调用其它软件时出现环境冲突。

下面是集群 3 此前记录的软件列表，当前可用版本以 `module avail` 为准：

```text
------------------------------- /opt/modulefiles -------------------------------
abinit/8.10.3                   lapack/3.7.0
alamode/1.1.0                   lobster/3.0.0
anaconda/3-python3.7.3(default) lobster/4.1.0
apptainer/1.0.0(default)        lobster/5.0.0
bader/1.04                      python/python-3.6.3
calypso/6                       qe/6.7
calypso/7                       scalapack/2.0.2
cmake/3.15.1(default)           ShengBTE/1.2.0(default)
cmake/3.18.5                    spglib/1.12.2
cp2k/7.1                        spglib/2.0.1(default)
cp2k/9.1(default)               uspex/2022.1.1
fftw/3.3.4(default)             vasp/5.4.4
gcc/5.4                         vasp/5.4.4_ifort(default)
gcc/7.4                         vasp/5.4.4_neb
gcc/9.3                         vasp/5.4.4_phonon
gibbs2/2020.10.07               vasp/5.4.4_wannier
go/1.17.7                       vasp/6.2.1
imscli/7.1.0                    vasp/6.3.0
intel/2015.1.133(default)       vasp/6.4.0
intel/2020.1.217                vasp/6.4.0_wannier31
jdftx/1.7.0                     wannier90/3.1.0
julia/1.8.5                     wannier90/310_vasp642
lammps/2020.10.29               yambo/4.5.1.r165
```

集群上有的软件一般就不要自己再重复安装了（除非管理员没有更新）。

例如，想要使用 Anaconda 可以直接 `module load anaconda/3-python3.7.3`，然后 `conda create -n XXX python=*` 创建指定版本号为 `*` 的 Python 环境 XXX，对应的环境路径就会自动添加到 `~/.conda/envs` 中。
如果集群限制联网，创建环境可能因下载依赖失败而停住。
如果你要求不高 Python 3.7 也能将就，那么 `conda create -n XXX --clone base` 克隆 base 环境就好。
安装新发行版也不会自动解决离线依赖问题，环境准备见 [Anaconda、Miniconda、Mamba](Anaconda、Miniconda、Mamba安装与使用.md)。

---
