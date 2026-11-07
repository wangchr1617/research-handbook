# Quantum ESPRESSO 基础知识

**适用环境：输入与分析通用；Linux + PBS 运行计算，Windows 可通过 WSL，macOS 可使用对应构建。**

Quantum ESPRESSO 的一次物性计算往往需要几个程序协作。先弄清各程序的分工，再看平面波、赝势与输入的关系，会更容易理解后面的计算流程。已有输入时，也可以直接查找相应的并行、文件或排错说明。

## 软件定位、方法与任务

Quantum ESPRESSO（QE）是一组开源电子结构程序，常用平面波基组、赝势/PAW 与 Kohn–Sham DFT。它与 VASP 的基本展开思路相近，常见任务由多个程序协作完成。

| 程序/组件 | 常见任务 |
| --- | --- |
| `pw.x` | SCF/NSCF、能带、结构/晶胞优化、Born–Oppenheimer MD |
| `ph.x` | DFPT 声子及相关响应，后续可用 `q2r.x/matdyn.x` |
| `pp.x/dos.x/projwfc.x/bands.x` | 电荷、DOS、投影与能带后处理 |
| `neb.x` | 反应路径和过渡态搜索 |
| `cp.x` | Car–Parrinello 等动力学路径，与 `pw.x` 的 MD 不能混用参数 |
| EPW、Wannier 等接口 | 电子声子、局域轨道及扩展工作流，需匹配安装 |

QE 的平面波、DFPT 和扩展工具较成熟，也便于查看和修改源码。使用时需要管理好程序之间的数据依赖，检验赝势与数值收敛，并考虑高阶任务的内存和 I/O 开销。大分子溶液 AIMD 可对照 [CP2K](../CP2K/基础与准备/CP2K基础知识.md)，局域轨道磁性/输运可对照 [OpenMX](../OpenMX/基础与结构/OpenMX基础知识.md)。功能入口见[QE 官网](https://www.quantum-espresso.org/)。

## 平面波、赝势和采样如何配合

### 两种截断分别控制什么

`ecutwfc` 限制轨道平面波的动能，`ecutrho` 限制密度与势的辅助表示。NC、USPP 和 PAW 的密度表示与增强项不同，对后者的需求也不同。因此应从所选赝势的建议值开始，逐步测试，不能把某个固定倍数当作所有势的保证。

SSSP 等经过一致性测试的势集合有助于选择，但测试目标仍要与研究问题匹配。应力、声子、能量差和高压结构对势与截断的敏感性可能不同。更换赝势后，价电子、能量零点和相对论处理都可能改变，不应把不同势计算的原始总能直接作差。

### SCF、NSCF 与能带

SCF 通过迭代更新电子密度，直到输入密度与求解得到的密度自洽。NSCF 使用已有的自洽势，在指定采样上求电子态，常用于 DOS 或后续接口；bands 则沿指定路径计算能带。三者使用的数据有关联，但承担不同任务。

金属常需占据展宽，绝缘体可使用固定占据等适用方案。k 点、`degauss` 与费米能附近物性应联合测试。`conv_thr` 是电子自洽阈值，离子受力和晶胞压力还有独立标准；调紧其中一个不会自动收敛另外两个。

## 输入规则、单位与赝势

`pw.x` 常用 `.in` 文本输入。前半部分为 Fortran namelist：`&CONTROL`、`&SYSTEM`、`&ELECTRONS`，必要时加 `&IONS/&CELL`，每段以 `/` 结束；后半部分为 `ATOMIC_SPECIES`、`ATOMIC_POSITIONS`、`K_POINTS`、`CELL_PARAMETERS` 等卡片。

| 项目 | 规则 |
| --- | --- |
| 字符串与逻辑值 | 字符串加引号，逻辑值用 `.true./.false.`；`!` 可注释 |
| 元素与坐标 | `nat/ntyp`、物种名称和每段行数应相互一致 |
| 晶格 | `ibrav=0` 时给晶格向量；避免同时给互相矛盾的晶格定义 |
| 单位 | 坐标/晶格卡片显式指定 `angstrom/bohr/crystal` 等适用选项 |
| 工作数据 | `prefix/outdir/pseudo_dir` 分别管理数据前缀、运行数据目录和势目录 |

`ATOMIC_SPECIES` 中给类型名、质量和 UPF 势文件名。QE 支持 NC、USPP、PAW 等方案；`UPF` 是容器格式，不能只看后缀判断方法和质量。泛函、价电子、相对论处理和元素组合应相容；SOC 通常还要求完全相对论赝势。

`ecutwfc` 与 `ecutrho` 的单位均为 Ry，具体含义见前面的截断说明。`degauss` 常以 Ry 表示，总能常为 Ry、力常为 Ry/bohr，注意与 VASP 的 eV 单位区分。输入细节见 [pw.x 参考](https://www.quantum-espresso.org/Doc/INPUT_PW.html)，势库可从[官方赝势入口](https://www.quantum-espresso.org/pseudopotentials/)查找 SSSP、PseudoDojo 等资源。

## 用硅原胞理解完整输入

下例给出 PBE 硅的 SCF 骨架。将所选相容 Si 赝势放入 `pseudo`，并把 `Si.UPF` 改为实际文件名；示例截断与网格需按该势测试。

```text
&CONTROL
 calculation = 'scf',
 prefix = 'si',
 pseudo_dir = './pseudo',
 outdir = './tmp',
 tprnfor = .true.,
 tstress = .true.,
/
&SYSTEM
 ibrav = 0,
 nat = 2,
 ntyp = 1,
 ecutwfc = 50.0,
 ecutrho = 400.0,
 occupations = 'fixed',
/
&ELECTRONS
 conv_thr = 1.0d-8,
 mixing_beta = 0.3,
/
ATOMIC_SPECIES
Si 28.085 Si.UPF
CELL_PARAMETERS angstrom
0.000 2.715 2.715
2.715 0.000 2.715
2.715 2.715 0.000
ATOMIC_POSITIONS crystal
Si 0.00 0.00 0.00
Si 0.25 0.25 0.25
K_POINTS automatic
6 6 6 0 0 0
```

`crystal` 为分数坐标；`CELL_PARAMETERS angstrom` 给出三个晶格向量，不能与 `alat` 下的无量纲数混淆。`ATOMIC_SPECIES` 名称必须与坐标中一致，同元素也可因模型需要分成不同类型。末行的三个 0 表示网格不沿相应方向偏移，不是第四到第六个 k 点数。

`mixing_beta` 控制电子密度混合，不控制离子步长。`1.0d-8` 是 Fortran 双精度指数写法。声子或高精度力计算可能需要更严格阈值，应根据目标量而不是代码中的小数位数判断。参数定义见[pw.x 输入手册](https://www.quantum-espresso.org/Doc/INPUT_PW.html)。

## 一般流程与输入辅助

1. 用 ASE、pymatgen、VESTA 等准备结构，结合同版本官方例子生成输入。
2. 选赝势与泛函，分别收敛截断、k 点、展宽和 SCF。
3. 先优化结构，再做一致精度的 SCF，随后执行 NSCF/能带/声子等分支。
4. 保留匹配的 `prefix.save` 及相关波函数，完成专用后处理。

坐标转换器生成的文件可能只包含结构，仍需补全电子计算参数。XCrySDen 可检查晶胞与路径，ASE 可辅助批量输入；图形输入器生成的设置也需对照任务和当前版本。实例见[结构优化](QE结构优化.md)与[声子谱](QE声子谱计算.md)。

## 从结构优化走向物性

### 固定晶胞与可变晶胞

`calculation='relax'` 通常优化原子位置，`'vc-relax'` 还允许晶胞自由度变化；相关 `&IONS`、`&CELL` 中指定算法和约束。从输出最后一个完整结构块提取最终坐标与晶胞，不要从中间离子步拷贝。晶胞收敛后可用最终结构再做静态 SCF，消除流程与保存数据上的歧义。

| 目标 | 典型程序链 | 关键依赖 |
| --- | --- | --- |
| DOS | `pw.x scf → pw.x nscf → dos.x` | 密集采样、占据/积分方式、同一数据前缀 |
| PDOS | `scf → nscf → projwfc.x` | 赝势的投影信息与投影定义 |
| 能带 | `scf → bands → bands.x` | 正确路径、带数和能量参考 |
| 声子 | `scf → ph.x → q2r.x → matdyn.x` | 电子/扰动收敛、q 网格与插值 |
| 密度/势 | `scf → pp.x` | 所选物理量与输出格式 |
| NEB | `neb.x` 及对应电子计算 | 端点、图像与每步 SCF |
| 电子声子 | QE/EPW/Wannier 相关流程 | 完整的匹配数据链与细网格收敛 |

表中的流程适用于对应常规任务；磁性、SOC、金属、杂化泛函及特殊边界会改变可用选项。具体例子可接着看[结构优化](QE结构优化.md)和[声子谱](QE声子谱计算.md)。声子虚频应结合结构、q 点/超胞、电子收敛和声学行为判断，不应只靠绘图时删除负值。

## 版本类型、并行与线程

程序名主要按任务区分。串行/MPI/OpenMP/GPU 是构建差异，通常不会统一生成 `pw_std/pw_gam/pw_ncl`；非共线/SOC 在 `pw.x` 输入中选择。`K_POINTS gamma` 可触发适用的 Γ 点优化实现，但不等同于任意单 k 点计算。

QE 的 MPI 层级包括 images、k 点 pools、能带、FFT/task groups 和线性代数分组，不同程序支持的选项有差异。已分配 8 核且支持混合并行时，可从下列布局测试：

```bash
export OMP_NUM_THREADS=2
mpirun -np 4 pw.x -nk 2 -in scf.in > scf.out 2>scf.err
```

`-nk 2` 是两个 k 点池，不是两个 k 点，也不是两个线程；应按实际不可约 k 点和每池工作量选择。进程数、线程数及各分组需相容。BLAS/FFT 库还可能有自己的线程设置，先确认输出中的实际并行布局。参见[并行层级](https://www.quantum-espresso.org/Doc/user_guide/node20.html)与[官方并行 FAQ](https://www.quantum-espresso.org/faq/parallel-execution/)。

同样是 32 个 MPI 进程，可以分为 4 个 k 点池、每池 8 个进程，也可以只用一个池让更多进程协作处理单个 k 点。前者适合有足够 k 点的工作，后者可能更适合 k 点很少但单个任务较大的情况。池数过多可能出现负载不均和数据复制。

| 资源瓶颈 | 先检查 | 再比较 |
| --- | --- | --- |
| 对角化工作区大 | 平面波数、带数与算法 | 合适的线性代数分组、算法与布局 |
| FFT 通信重 | 网格、每组进程与节点分布 | 减少跨节点通信或调整线程 |
| k 点分配不均 | 不可约 k 点数、池数 | 更少或可合理分配的池 |
| I/O 很慢 | `outdir`、波函数文件与共享存储 | 合适 scratch 和 `disk_io`，保留必要数据 |

## 内存、scratch 与输出控制

内存需求取决于平面波数、能带数、k 点和算法。`pw.x` 没有给整个作业设置内存硬上限的统一关键词；不同并行层级只分布部分数据，增加 k 点池也不会让全部内存按比例分摊。

输出的 RAM 估计应与 PBS 申请量、节点实测占用一起看。`diago_david_ndim`、`mixing_ndim` 影响特定工作区；`diagonalization='cg'` 通常更省内存但可能更慢。`disk_io` 在 RAM、磁盘和可续算性之间取舍，最低 I/O 不一定最省资源；这些都不是总内存预算，详见 [pw.x 输入参考](https://www.quantum-espresso.org/Doc/INPUT_PW.html)。

`verbosity` 控制输出详细度，`tprnfor/tstress` 控制相关力与应力输出；`disk_io` 管部分二进制数据保存，不等同于日志开关。各后处理程序另有输出控制。独立任务使用独立 `prefix/outdir`，避免覆盖或并发写同一数据目录。

## 工作目录、输出和续算

### 什么值得保存

`prefix` 是数据标识，`outdir` 是其位置。两个同时运行的独立任务不应写同一个 `prefix/outdir` 组合。`prefix.save` 常包含结构化数据、密度及势相关信息，波函数的布局还取决于版本、并行与 I/O 设置；只拷贝一个 XML 或终端输出不足以保证后处理可用。

| 数据 | 主要用途 | 检查方式 |
| --- | --- | --- |
| 输入与 `.out/.err` | 方法、实际参数、故障与收敛 | 找收敛信息、末尾计时与最早错误 |
| `prefix.save` 及关联波函数 | NSCF、响应、分析和重启 | 数据集完整，且与结构/版本相符 |
| 最终坐标和晶胞 | 新任务建模 | 提取最后完整、已确认收敛的结构 |
| 声子/响应中间数据 | 分段任务和后处理 | 确认所有扰动/q 点完成且来自同一方案 |
| DOS、投影、体网格 | 绘图与物理分析 | 单位、费米能和归一化 |

### 怎样区分三种“继续”

1. **原任务干净中断后接续**：保持完整 scratch 数据，按适用条件设 `restart_mode='restart'`，尽量保持原版本与布局。利用 `max_seconds` 预留退出写盘时间。
2. **已完成 SCF 后做 NSCF/能带**：这是新阶段，保留相同数据前缀，设置相应 `calculation` 与采样，而不是靠 restart 标志改变任务类型。
3. **只复用结构开始新研究**：复制最终晶胞和坐标，使用新的任务目录；根据新模型决定势、磁态和初猜，不要求继承旧任务的全部运行状态。

强制终止时文件可能不完整；先查输出是否正常保存状态，再尝试续算。过低的 `disk_io` 也可能不保存下游所需的波函数。波函数、密度与响应文件都要按同一数据集管理，避免不同计算的同名文件混在一起。具体选项见 [restart_mode](https://www.quantum-espresso.org/Doc/INPUT_PW.html)。

## 从错误信息回到原因

| 现象 | 优先查看 |
| --- | --- |
| `Error in routine ...`、`%%%%` 错误块 | `scf.out/scf.err` 中首个错误、namelist 拼写和卡片行数 |
| `davcio` 等 I/O 错误 | `outdir` 权限、容量、配额、共享文件系统和数据是否损坏 |
| SCF 失败或非正定矩阵 | 结构、势、电子占据、截断和混合历史 |
| 程序结束但任务没完成 | SCF 收敛、优化受力/压力、声子扰动是否逐项完成 |

`Error in routine` 附近通常比最后的 MPI abort 更有用。先区分读取阶段、SCF 阶段、离子阶段与文件写入阶段，再采取对应处理。

- 读取阶段失败：查 namelist 中逗号、斜杠、引号、物种拼写以及卡片行数。
- SCF 发散：查短距离接触、赝势、电子数和自旋，再调整占据、混合与求解器。
- `davcio`：查磁盘容量、配额、目录权限、共享存储及旧数据完整性。
- 优化不收敛：查电子力噪声、允许自由度、压力/受力标准和步长，而不只增加离子步数。

`JOB DONE.` 是正常终止信息，不代表每个目标都已充分收敛。不要只看输出最后一行；也要看 PBS 内存或超时退出。排错参见[官方故障指南](https://www.quantum-espresso.org/Doc/pw_user_guide/node21.html)。

## 第三方库、接口与资源

MPI、BLAS/LAPACK、FFT 是主要数值依赖，ScaLAPACK、ELPA、Libxc、HDF5 和 GPU 数值库按构建及功能选择。Wannier90、EPW、Yambo 等衔接不同的局域轨道、电子声子或激发态流程；不是任意 `pw.x` 安装都包含完整工具链。

用 XCrySDen/VESTA 看结构与体数据，用 ASE/脚本组织批量任务；密度数据转为相容格式后还可用 Multiwfn 分析。构建见[本仓库笔记](QE编译.md)，完整组件与版本信息以[官方文档](https://www.quantum-espresso.org/documentation/)为准。
