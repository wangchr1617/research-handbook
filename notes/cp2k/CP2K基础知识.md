# CP2K 基础知识

**适用环境：输入与分析通用；Linux + PBS 运行计算，Windows 可通过 WSL，macOS 可使用对应构建。**


初次阅读可先看软件定位与文件规则，再按“[怎样选择计算方案](#怎样选择计算方案) → [读懂一个水分子输入](#读懂一个水分子输入) → [从单点扩展到优化与动力学](#从单点扩展到优化与动力学) → [文件保存与续算的具体判断](#文件保存与续算的具体判断)”学习；已有运行经验时，可直接查并行、内存与排错部分。

## 软件定位、方法与任务

CP2K 是面向分子、溶液、界面和周期材料的开源模拟软件。Quickstep 常用 GPW 方法：用局域高斯轨道展开波函数，用平面波辅助表示电子密度；GAPW 可进一步处理核附近的密度。它不同于 VASP、QE 的纯平面波轨道展开，基组与密度网格需要分别收敛。

| 类型 | 常见任务 |
| --- | --- |
| 电子结构 | DFT 单点、DFT+U、杂化泛函、电荷与轨道分析 |
| 原子运动 | 几何/晶胞优化、AIMD、NEB、约束 MD、Metadynamics |
| 响应与激发 | 振动、线性响应、TDDFPT 等，具体实现依模块而定 |
| 多尺度 | 经典力场、DFTB/半经验方法、QM/MM 等 |

优势是周期与非周期体系覆盖广、AIMD 和多尺度流程丰富；局限是输入层级和方法组合较多，金属、空带较多或高精度激发态计算未必适合直接套用常见的 OT 基态设置。分子高精度波函数关联可对照 [ORCA](../orca/ORCA基础知识.md)，长时间经典采样则可考虑 [LAMMPS](../lammps/LAMMPS基础知识.md) 或 [GROMACS](../gromacs/GROMACS基础知识.md)。功能总览见[官方 Features](https://www.cp2k.org/features)。

## 输入、基组与势文件

输入通常为任意名称的 `.inp`：`&SECTION` 与 `&END SECTION` 成对，关键词所在层级决定含义；`#` 或 `!` 可注释。名称和值中的文件路径仍应按真实大小写填写。预处理可用 `@INCLUDE`、`@SET` 等，拆分输入时要保留依赖文件。

| 部分 | 管理内容 |
| --- | --- |
| `GLOBAL` | `PROJECT` 前缀、`RUN_TYPE`、日志级别 |
| `FORCE_EVAL/DFT` | 电子结构、SCF、XC、网格、泊松边界 |
| `FORCE_EVAL/SUBSYS` | 晶胞、坐标、`KIND` 与元素数据 |
| `MOTION` | 优化、MD、约束及自由能采样 |

常见 `BASIS_MOLOPT` 存高斯基组，`GTH_POTENTIALS` 存 GTH 赝势；在 `KIND` 中用名称选择，并通过 `BASIS_SET_FILE_NAME`、`POTENTIAL_FILE_NAME` 定位。基组、赝势的价电子数、元素与泛函应相容，不能只把另一软件的势文件改名使用。全电子 GAPW、辅助基组和色散参数另有相应数据。改用 FIST 经典力场或 DFTB 时，需要相应的拓扑/势参数或 DFTB 参数集，不能继续把 GTH 数据当作同一种模型输入。

坐标通常用 Å，`CUTOFF/REL_CUTOFF` 用 Ry，MD 步长常用 fs，总能通常输出 Hartree；不同关键词的默认单位不同。详见[输入参考](https://manual.cp2k.org/trunk/CP2K_INPUT.html)和[本仓库入门](CP2K入门.md)。

## 一般流程

1. 用 Multiwfn、ASE 或结构编辑器建立输入，检查电荷、自旋、周期性和晶胞。
2. 分别收敛轨道基组、密度网格、k 点和 SCF；先跑小规模单点。
3. 优化结构后执行目标计算；保存输入、数据文件版本和输出。
4. 分开检查程序结束、电子收敛和任务目标，再分析物性。

从[水分子单点案例](../../examples/cp2k/minimal/single-point/)开始；输入骨架可用[Multiwfn 辅助创建](用Multiwfn生成CP2K输入文件.md)。

## 程序版本、并行与线程

常见 `cp2k.psmp` 支持 MPI + OpenMP；`cp2k.ssmp` 不使用 MPI，支持 OpenMP。旧名 `popt/sopt` 在一些安装中是兼容入口或别名，不宜只凭名称判断实际构建。GPU 支持也是构建特性，不一定有统一的另一套文件名。参见[官方 MPI/OpenMP 说明](https://www.cp2k.org/faq:mpi_vs_openmp)与[构建说明](CP2K编译与部署.md)。

在已申请 8 个 CPU 核且支持混合并行的作业环境中，例如：

```bash
export OMP_NUM_THREADS=2
mpirun -np 4 cp2k.psmp -i system.inp -o system.out 2>system.err
```

MPI 进程数乘每进程线程数不得超过分配的核数。观察输出实际 MPI/线程数量，比较不同组合的耗时与内存；别把串行程序用 `mpirun` 启动成多份独立作业。BLAS 库还可能自行开线程，应检查 MKL/OpenBLAS 的设置，避免嵌套超额并行。

## 内存与输出控制

CP2K 没有一个适用于全部模块的全局内存硬上限。PBS 申请量是调度资源，程序内参数则约束特定工作区；减少每节点 MPI 数、使用线程共享部分数据，有时比继续增加进程更省内存，但需实测。

杂化泛函的 `DFT/XC/HF/MEMORY/MAX_MEMORY` 单位为 MiB，按每个 MPI 进程预算 HFX 模块内存，不是整个作业预算。该参数也不能覆盖其他模块的全部占用，见[官方 MEMORY](https://manual.cp2k.org/trunk/CP2K_INPUT/FORCE_EVAL/DFT/XC/HF/MEMORY.html)。

`GLOBAL/PRINT_LEVEL` 控制日志详细度；各模块 `PRINT` 下的开关、`EACH` 和文件名控制轨迹、力、cube、restart 等。只降低 `PRINT_LEVEL` 不会自动关闭所有大文件。按分析需求保存波函数、轨迹与密度，检查 scratch 空间和配额。

## 排错与重启

| 现象 | 优先查看 |
| --- | --- |
| 输入或基组名称错误 | `system.err`、主输出的 `ABORT` 及其上方调用信息 |
| SCF 不收敛 | 每一步收敛历史，而非只找最后一个能量；参见[SCF 收敛](CP2K自洽收敛.md) |
| `Killed`、进程异常退出 | PBS 标准错误、内存限制、磁盘、MPI 库兼容性 |
| 程序正常结束但结果不完整 | 优化是否达阈值、MD 是否达计划步数、响应计算是否收敛 |

电子重启可用 `SCF_GUESS RESTART` 与匹配的 `WFN_RESTART_FILE_NAME`；几何/MD 续算则读取 `.restart` 输入，或通过 `EXT_RESTART/RESTART_FILE_NAME` 恢复选定状态。MD 还涉及速度、温控/压控和偏置历史，不能只拿最后一帧坐标续跑。保留同一 `PROJECT` 对应的数据并核对实际读取记录。参考 [EXT_RESTART](https://manual.cp2k.org/trunk/CP2K_INPUT/EXT_RESTART.html)和[官方排错](https://manual.cp2k.org/trunk/getting-started/troubleshooting.html)。

## 怎样选择计算方案

### 从研究问题确定方法

如果关注水溶液中的结构、反应或界面动力学，通常先考虑 Quickstep DFT，再决定是否需要色散、杂化泛函和增强采样。如果只需更长时间、更大体系的构型统计，且已有可信势函数，可以选择经典 MD。QM/MM 则把反应区域放在量子区、环境放在经典区；量子区边界、电荷和耦合方式本身也是模型的一部分。

GPW 中存在两套独立的数值表示：高斯基组决定轨道的表达能力，辅助网格决定密度、势及相关积分的数值精度。因此，增加 `CUTOFF` 不能补偿缺少极化或弥散函数，也不能把 DZVP 自动变成 TZV2P。

| 要解决的问题 | 主要选择 | 怎样判断是否足够 |
| --- | --- | --- |
| 轨道表达不够灵活 | 基组层级、极化/弥散函数 | 目标能量差、几何和受力随基组变化是否稳定 |
| 网格积分不够精确 | `CUTOFF` 与 `REL_CUTOFF` | 能量、力、压力分别检查，不能只看总能 |
| 周期采样不足 | 超胞与 k 点 | 物性随超胞和 k 网格是否稳定 |
| 弱相互作用描述不足 | 适合体系的色散修正 | 比较吸附距离、结合能及相应参考数据 |
| 自相互作用或能隙问题 | DFT+U、杂化泛函等 | 说明参数/方法依据，同时检查磁态和结构 |

孤立分子也需要晶胞。`CELL/PERIODIC` 与 `POISSON/PERIODIC` 应一致；只把原子放入大盒子，并不会自动关闭周期静电作用。表面、线状体系和带电体系应单独考虑边界条件，不能一律套用三维周期设置。

### OT 与对角化怎样选

OT 直接优化占据轨道，常用于有能隙体系的基态和 AIMD；它通常不按常规方式生成大量空轨道。金属、部分占据以及需要较多空带的任务，应考虑对角化、混合与展宽方案。对角化也不是“更高级”，它解决的是不同的占据与求解需求。

SCF 振荡时先查看几何、电荷、自旋和占据，再调整求解器。单纯增加 `MAX_SCF` 只允许迭代更久；如果能量与残差持续振荡，应处理初猜、混合或占据问题。具体设置见[自洽收敛笔记](CP2K自洽收敛.md)。

## 读懂一个水分子输入

下面以非周期水分子 PBE 单点为例，展示完整层级。运行前需使 `BASIS_MOLOPT`、`GTH_POTENTIALS` 可由数据路径找到；这组参数用于理解输入，实际任务应另做精度测试。

```text
&GLOBAL
  PROJECT water
  RUN_TYPE ENERGY_FORCE
  PRINT_LEVEL MEDIUM
&END GLOBAL
&FORCE_EVAL
  METHOD Quickstep
  &DFT
    BASIS_SET_FILE_NAME BASIS_MOLOPT
    POTENTIAL_FILE_NAME GTH_POTENTIALS
    CHARGE 0
    MULTIPLICITY 1
    &MGRID
      CUTOFF 400
      REL_CUTOFF 50
    &END MGRID
    &SCF
      EPS_SCF 1.0E-6
      MAX_SCF 100
      SCF_GUESS ATOMIC
      &OT
        MINIMIZER DIIS
        PRECONDITIONER FULL_SINGLE_INVERSE
      &END OT
    &END SCF
    &XC
      &XC_FUNCTIONAL PBE
      &END XC_FUNCTIONAL
    &END XC
    &POISSON
      PERIODIC NONE
      POISSON_SOLVER MT
    &END POISSON
  &END DFT
  &SUBSYS
    &CELL
      ABC 15 15 15
      PERIODIC NONE
    &END CELL
    &COORD
      O 7.500 7.500 7.500
      H 8.257 7.500 8.086
      H 6.743 7.500 8.086
    &END COORD
    &KIND O
      BASIS_SET DZVP-MOLOPT-SR-GTH
      POTENTIAL GTH-PBE-q6
    &END KIND
    &KIND H
      BASIS_SET DZVP-MOLOPT-SR-GTH
      POTENTIAL GTH-PBE-q1
    &END KIND
  &END SUBSYS
&END FORCE_EVAL
```

本例采用 MT 非周期泊松求解器，盒子应充分容纳局域电荷密度；其适用条件见[MT 说明](https://manual.cp2k.org/trunk/CP2K_INPUT/FORCE_EVAL/DFT/POISSON/MT.html)。

`ENERGY_FORCE` 计算当前结构的能量和力，不会优化原子。`EPS_SCF` 是电子收敛标准；几何优化中的最大力、均方根力和位移是另一组标准。`q6/q1` 对应赝势价电子数，结合总电荷决定电子数，而 `MULTIPLICITY` 决定目标自旋；开壳层还需相应启用自旋极化设置。

使用 Multiwfn 生成输入后，建议按上述四层逐项阅读，而不是只检查坐标。将输入与[完整单点案例](../../examples/cp2k/minimal/single-point/)对照，可以进一步看到运行、提取和绘图如何衔接。

## 从单点扩展到优化与动力学

| 后续任务 | 需要增加或改变 | 应检查的结果 |
| --- | --- | --- |
| 几何优化 | `RUN_TYPE GEO_OPT`、`MOTION/GEO_OPT` | 受力与位移阈值、最终结构，见[几何优化](CP2K几何优化.md) |
| 晶胞优化 | `CELL_OPT`、晶胞自由度与目标压力 | 压力、晶格及网格引起的应力误差，见[晶胞优化](CP2K晶胞优化.md) |
| AIMD | `MD`、步长、系综、温压控制 | 能量漂移、温度与结构统计，见[分子动力学](CP2K分子动力学.md) |
| 振动 | 位移/响应与精度设置 | 虚频模式、位移收敛，见[振动频率](CP2K振动频率.md) |

优化结构时，SCF 数值噪声应低于要辨别的力变化。做 AIMD 时，先完成结构预处理和短时间稳定性测试，再决定时间步；温控器可以把温度拉回目标值，却不能证明积分误差小。NVE 能量漂移测试有助于识别时间步和电子收敛问题。

### 资源怎样估计

例如单节点分配 16 核、64 GiB，可比较 16 MPI×1 线程、8×2、4×4 三种布局，在相同输入下记录每步时间和峰值内存。小分子通常不能有效利用很多进程；大型稀疏矩阵、精确交换和 FFT 的瓶颈也不同。

若 HFX 设置 `MAX_MEMORY 2000`，8 个 MPI 进程对应约 16000 MiB 的 HFX 模块预算，还要容纳其余矩阵、网格与库开销。不能把节点 64 GiB 直接填成每进程 64000。比较布局时同时看节点总内存，不能只看单个进程 RSS。

## 文件保存与续算的具体判断

| 文件 | 用途 | 保存建议 |
| --- | --- | --- |
| 主 `.out` 与输入 | 方法、收敛、计时和参数依据 | 与数据文件版本一起保存 |
| `*-RESTART.wfn` | 波函数初猜 | 后续相容电子计算会用到 |
| `*.restart` | 可读的任务状态输入 | 结合波函数和外部依赖保存 |
| `*-pos-*.xyz`、能量记录 | 几何/MD 轨迹与统计 | 按分析时间分辨率设置频率 |
| cube、Molden 等 | 密度、轨道与后处理 | 只输出目标分析需要的内容 |

继续被中断的 MD，应先核对 restart 中的步数、时间、坐标、速度与系综状态；带增强采样时还要保留偏置历史。若只是想用旧结构开始一个新温度的任务，就显式决定哪些状态继承、哪些重新初始化，避免由默认的 `EXT_RESTART` 选项把旧状态一并读入。[EXT_RESTART 参数表](https://manual.cp2k.org/trunk/CP2K_INPUT/EXT_RESTART.html)可以选择恢复的状态。

电子波函数重启与运动状态重启互不替代。更换基组、电子数或自旋后，应确认旧波函数能否合法读取；读到文件也要继续检查是否落入目标电子态。

## 第三方库与辅助程序

MPI、BLAS/LAPACK、FFT 和 DBCSR 支撑数值计算；Libint 服务于积分/HF 交换，Libxc 提供部分泛函，Libxsmm、ELPA 及 GPU 库用于相应加速路径。是否启用取决于构建，不要求用户逐个独立运行这些库。

Multiwfn 用于建输入、波函数和密度分析；VESTA 查看 cube/结构，ASE 管结构与批量任务，PLUMED 在相容构建中扩展增强采样。工具列表与入口可查[官方工具页](https://www.cp2k.org/tools)；本仓库具体任务见 [CP2K 目录](README.md)。
