# GROMACS 基础知识

**适用环境：Linux + PBS 运行计算；Windows 可用 WSL，macOS 可使用对应构建，前后处理流程通用。**


初次阅读可先看软件定位与文件规则，再按“[从研究问题选择模型](#从研究问题选择模型) → [一套常见准备流程](#一套常见准备流程) → [读懂生产 MDP 的主要参数](#读懂生产-mdp-的主要参数) → [长任务、资源与故障定位](#长任务资源与故障定位)”学习；已有运行经验时，可直接查并行、内存与排错部分。

## 软件定位、方法与任务

GROMACS 是以高性能经典分子动力学见长的开源软件，常用于蛋白、膜、溶液和其他分子体系。它根据力场势能计算原子受力，不直接求电子波函数；拓扑和参数质量是模拟可靠性的基础。

| 类型 | 常见任务 |
| --- | --- |
| 准备与平衡 | 加氢、溶剂化、加离子、最小化、NVT/NPT |
| 生产采样 | 分子构象、膜/蛋白动力学、扩散与结构相关 |
| 自由能 | umbrella、alchemical 自由能、replica exchange 等 |
| 扩展耦合 | PLUMED 增强采样、特定 QM/MM 接口等，依构建支持 |

优势是生物分子工作流、轨迹分析和 CPU/GPU 性能成熟；局限是普通力场通常保持固定成键关系，金属配位、化学反应和新分子参数需额外处理。通用材料的复杂自定义加载可对照 [LAMMPS](../lammps/LAMMPS基础知识.md)，成键变化的小体系可对照 [CP2K](../cp2k/CP2K基础知识.md)。方法与教程见[官方手册](https://manual.gromacs.org/current/index.html)。

## 文件规则与力场数据

| 文件 | 用途 |
| --- | --- |
| `.gro/.pdb` | 坐标，可能带盒子和速度；必须与拓扑原子顺序一致 |
| `.top/.itp` | 分子拓扑与力场参数，`#include` 等预处理指令按顺序展开 |
| `.mdp` | `关键词 = 值` 的运行参数，`;` 注释 |
| `.tpr` | `grompp` 生成的二进制运行输入，包含结构、拓扑和参数 |
| `.cpt` | 带速度、耦合状态等信息的检查点 |
| `.xtc/.trr/.edr/.log` | 压缩/完整轨迹、能量记录和运行日志 |

常用单位为 nm、ps、kJ/mol；PDB 通常使用 Å，不能按 GRO 的单位直接解释。位置编号、分子数、电荷与水模型应一致；输入坐标本身并不定义完整的分子模型。

`.ff` 力场目录含原子类型、非键参数、残基和水/离子定义。AMBER、CHARMM、OPLS 等力场的组合规则、1–4 缩放与参数体系不同；不能只把配体 `.itp` include 进去就认为兼容。这里一般不使用电子结构意义的基组或赝势，力场参数也不能用 VASP `POTCAR` 替代。

## 一般流程与输入辅助

1. 明确质子化、末端、缺失原子、辅因子与参数来源。
2. 用 `pdb2gmx` 等建立适合的拓扑，定义盒子、溶剂和离子。
3. 能量最小化后逐级平衡，检查温度、密度、压力和结构。
4. 生成生产 `.tpr`，运行并保存检查点，最后按物理问题分析。

在已有相容输入时，预处理与执行示意为：

```bash
gmx grompp -f md.mdp -c equilibrated.gro -p topol.top -o md.tpr
gmx mdrun -deffnm md -ntmpi 2 -ntomp 4
```

`grompp` 的警告应逐条理解，不能把 `-maxwarn` 当作通用修复。CHARMM-GUI 可辅助标准体系准备，Packmol 可装填坐标，ACPYPE/ATB 等可辅助特定参数体系；仍须核对方法、力场兼容性和化学状态。

## 版本类型与并行设置

| 常见名称 | 主要区别 |
| --- | --- |
| `gmx` | 常见单节点入口，`mdrun` 可采用 thread-MPI + OpenMP |
| `gmx_mpi` | 外部 MPI 构建，用 MPI 启动器分配进程 |
| `gmx_d/gmx_mpi_d` | 常见双精度命名；默认常见构建为混合精度，不等于全部运算都用单精度 |

名称可由安装修改，先看 `gmx --version` 的 MPI、OpenMP、SIMD 和 GPU 配置信息。thread-MPI 不能用于跨节点；外部 MPI 作业的进程数由启动器管理，通常不再用 `-ntmpi`：

```bash
export OMP_NUM_THREADS=4
mpirun -np 2 gmx_mpi mdrun -deffnm md -ntomp 4
```

以上两种方式都对应 8 个 CPU 核的布局示例，需与 PBS 申请量一致。空间域分解、PME 通信和 GPU 任务分配共同决定性能，不能只把线程数调大。`-nb/-pme/-bonded/-update` 和 GPU 选择的可用组合依版本及算法而定，先用自动分配再看 `.log` 的负载与性能。见[官方性能指南](https://manual.gromacs.org/current/user-guide/mdrun-performance.html)。

## 内存与输出控制

没有类似 `%maxcore` 的通用作业内存开关。占用取决于原子数、邻居表、PME 网格、约束、域分解及 GPU 数据；MPI、线程和 GPU 显存需分别规划。先核对体系大小与构建，再根据小测试申请资源，不用降低物理精度来掩盖错误配置。

`.mdp` 中 `nstlog`、`nstenergy`、`nstxout-compressed` 及 `nstxout/nstvout/nstfout` 控制不同输出；`compressed-x-grps`、压缩精度影响保存内容。`mdrun -cpt` 控制检查点间隔。高频速度/力输出会明显增大文件；做扩散、动力学或振动分析时，又不能把采样间隔设得过大。详见 [MDP 选项](https://manual.gromacs.org/current/user-guide/mdp-options.html)。

## 排错与重启

`grompp` 输出、运行终端/PBS 错误与 `.log` 都要看；从首个 `Fatal error` 或异常数值向前检查。

| 现象 | 优先排查 |
| --- | --- |
| 坐标与拓扑数量不一致 | 原子顺序、分子数、溶剂/离子是否同步更新 |
| LINCS 警告 | 重叠、坏接触、时间步、拓扑和约束；不要只放宽警告阈值 |
| PME/域分解失败 | 盒子、截断、节点数与分解尺度是否相容 |
| `Killed` 或 GPU 异常 | 调度内存、显存、驱动与运行构建 |

续算通常使用：

```bash
gmx mdrun -deffnm md -cpi md.cpt
```

程序按检查点校验输出并尝试接续；改名或缺少旧输出时应理解追加规则，必要时使用 `-noappend` 分段保存。延长任务可先用 `gmx convert-tpr` 生成新的运行长度，再读取相容检查点。只用最后 `.gro` 重建且重新生成速度，不等于完整续算。参考[长期任务管理](https://manual.gromacs.org/current/user-guide/managing-simulations.html)。

## 从研究问题选择模型

### 力场、化学状态与水模型

GROMACS 通常采用固定拓扑的经典力场。蛋白质构象、膜、溶液和配体结合环境是常见应用；普通固定拓扑模型不能自动描述质子转移、成键断键和电子激发。需要反应过程时，应考虑专门参数化、反应模型或 QM/MM 等方法。

输入准备中最值得先确定的是质子化状态、互变异构、末端、二硫键、金属配位和配体参数。`pdb2gmx` 能按已有残基定义建立拓扑，但无法仅凭 PDB 坐标确定所有化学状态。

| 组成 | 要核对的兼容性 |
| --- | --- |
| 蛋白质/核酸 | 参数版本、残基命名、末端和氢原子处理 |
| 配体/辅因子 | 电荷、原子类型、拟合方法及母力场 |
| 水 | 与力场匹配的模型、约束和相互作用设置 |
| 离子 | 对应水模型与非键参数来源 |
| 膜/界面 | 脂质参数、盒子方向及压力耦合方式 |

不能因为所有 `.itp` 都能被解析，就认为模型物理相容。CHARMM-GUI 等成熟工具可减少标准体系搭建负担，但生成的 README、力场版本与运行阶段仍需读懂。

## 一套常见准备流程

下面展示普通蛋白质水溶液的命令链。各阶段需准备相容的 `.mdp`；交互中按所选力场选择水和离子。实际文件名、盒子尺寸与盐浓度按体系设置。

```bash
gmx pdb2gmx -f protein.pdb -o processed.gro -p topol.top
gmx editconf -f processed.gro -o boxed.gro -c -d 1.2 -bt dodecahedron
gmx solvate -cp boxed.gro -cs spc216.gro -o solvated.gro -p topol.top
gmx grompp -f ions.mdp -c solvated.gro -p topol.top -o ions.tpr
gmx genion -s ions.tpr -o solvated-ions.gro -p topol.top -pname NA -nname CL -neutral
gmx grompp -f em.mdp -c solvated-ions.gro -p topol.top -o em.tpr
gmx mdrun -deffnm em
```

`genion` 交互时选择可被离子替换的溶剂组；离子名必须存在于所用力场。`spc216.gro` 提供常用溶剂坐标，水的势能模型仍由拓扑定义。`solvate/genion` 会更新拓扑中的分子数，所以坐标与 `topol.top` 要成对保留。

完成最小化后，一般按所用力场推荐设置进行温度和压力平衡，再生成生产任务。位置限制需要相应参考坐标和预处理宏；哪些原子受限制、何时解除，应写清楚。膜体系等模型的压力耦合与普通各向同性水溶液不同。

## 读懂生产 MDP 的主要参数

以下是已平衡、常规三维周期原子体系的参数片段，**需按选定力场补全温压耦合和推荐非键设置**。它不是可直接用于所有力场的通用模板。

```text
; ps、nm、kJ/mol；2 fs × 500000步 = 1 ns。
integrator = md
dt = 0.002
nsteps = 500000
continuation = yes
gen-vel = no
constraints = h-bonds
cutoff-scheme = Verlet
coulombtype = PME
rcoulomb = 1.0
rvdw = 1.0
pbc = xyz
nstlog = 1000
nstenergy = 1000
nstxout-compressed = 5000
nstxout = 0
nstvout = 0
nstfout = 0
```

| 参数 | 判断思路 |
| --- | --- |
| `dt/constraints` | 时间步受最快自由度、约束与模型影响；2 fs 不是普遍安全值 |
| 非键截断与 PME | 遵循力场推荐，检查网格、截断平滑及色散处理 |
| 温度耦合 | 选择适合体系的分组与时间常数，避免无依据地分成许多小组 |
| 压力耦合 | 选择正确的系综与盒形自由度，区分预平衡和生产用途 |
| `continuation/gen-vel` | 继续已有速度/约束状态时不重新生成速度；仍需传入匹配检查点 |
| 输出间隔 | 此例压缩坐标每 10 ps、能量每 2 ps 保存，是否足够取决于分析 |

完整输入可查[MDP 参考](https://manual.gromacs.org/current/user-guide/mdp-options.html)。`grompp` 写出的 `mdout.mdp` 便于核对预处理后参数，`.tpr` 才是实际运行输入；修改原 `.mdp` 并不会自动改变已生成的 `.tpr`。

## 平衡后怎样开始生产

从 NPT 平衡段传入结构和检查点，可按下列方式生成生产输入；`md.mdp` 要与计划系综、继续状态一致。

```bash
gmx grompp -f md.mdp -c npt.gro -t npt.cpt -p topol.top -o md.tpr
gmx mdrun -deffnm md -ntmpi 2 -ntomp 4
```

平衡检查不能只看温度：还应检查密度、能量与结构是否持续漂移；压力瞬时值的巨大涨落不一定是错误。观察对象取决于问题，蛋白质 RMSD 稳定也不代表配体、膜或慢构象自由度都已充分采样。

| 阶段 | 主要检查 | 常见误判 |
| --- | --- | --- |
| 最小化 | 最大力、接触与结构 | 能量下降就说明结构合理 |
| 温度平衡 | 温度、势能、约束稳定性 | 目标温度到了就可开始统计 |
| 压力/密度平衡 | 体积、密度与结构变化 | 要求每步压力等于 1 bar |
| 生产 | 分块统计、独立重复和物理量稳定性 | 帧数很多就等于独立样本多 |

## 分析前先处理坐标含义

使用 `gmx energy` 提取温度、能量、密度等；使用 `trjconv` 处理周期边界、居中和拟合，再按目标运行 `rms/rmsf/gyrate/hbond/msd` 等分析。不同分析需要不同坐标处理，不能共用一个“看着好看”的轨迹解决全部问题。

- 看蛋白质构象或 RMSD 时，通常要处理跨盒分子并选定拟合参考组。
- 看扩散时，需要保证位移连续，不能因每帧重新居中而消除或制造位移。
- 看膜或界面时，需要定义法向、参考面及周期镜像关系。

VMD/ChimeraX 可视化，MDAnalysis/MDTraj 适合批量与自定义统计。曲线应标单位、平衡段和平均区间；慢过程尽量结合独立重复，避免用一条轨迹的微小波动给出过度精确结论。

## 长任务、资源与故障定位

### 完整续算与延长任务

同一任务被中断时，保留 `.tpr`、`.cpt` 和原输出，使用 `-cpi`。延长已结束的 1 ns 任务，例如再加 1 ns，可使用：

```bash
gmx convert-tpr -s md.tpr -extend 1000 -o md-extended.tpr
gmx mdrun -s md-extended.tpr -deffnm md -cpi md.cpt
```

`-extend` 单位是 ps。追加输出会核对文件及检查点中的校验信息；若要分段输出，应有意识地使用 `-noappend`。更换物理参数或重新生成速度属于新的运行阶段，应重新预处理并记录变化。[长期任务管理](https://manual.gromacs.org/current/user-guide/managing-simulations.html)详述这些区别。

### 怎样分配核与 GPU

单节点先让程序自动分配任务，再依据日志比较少 MPI、多线程和多 MPI、少线程的性能。粒子数太少时，域分解通信可能占主导；增加 PME 专用进程或 GPU 并非总是有利。多副独立模拟有时比给一个小体系分配全部设备更有效，但应先保证每个任务有独立输出目录。

LINCS 警告常由坏接触、时间步过大、参数错误或局部不稳定引起。先定位最早出现警告的位置并查看结构，不要只增加迭代次数或提高允许警告数。`grompp` 的拓扑数量错误，应回到组装和分子计数检查；运行中 OOM 则结合节点内存、GPU 显存和日志布局处理。

## 第三方库、辅助程序与资源

常见数值依赖包括 FFTW、MPI/OpenMP，GPU 构建使用相应 CUDA、SYCL 等后端；具体以后端支持表为准。PLUMED、QM/MM 等属于额外接口或扩展，不能假设任意 `gmx` 都已启用。

VMD、PyMOL、ChimeraX 用于结构和轨迹查看，MDAnalysis/MDTraj 用于统计，GROMACS 自带 `energy`、`trjconv`、`rms` 等分析命令。选分析时先处理周期成像和参考系，再解释 RMSD 或扩散。安装见[本仓库构建笔记](GROMACS编译.md)，命令参数以 `gmx 子命令 -h` 与相同版本官方手册为准。
