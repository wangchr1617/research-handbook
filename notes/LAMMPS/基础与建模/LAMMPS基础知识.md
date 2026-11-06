# LAMMPS 基础知识

**适用环境：Linux + PBS 运行计算；Windows/macOS 可使用对应程序，输入与分析流程通用。**

初次阅读可先看软件定位与文件规则，再按“[先选模型，再选计算命令](#先选模型再选计算命令) → [一个不依赖外部势文件的完整小例](#一个不依赖外部势文件的完整小例) → [从短测试走到可解释的结果](#从短测试走到可解释的结果) → [续算脚本应重新声明什么](#续算脚本应重新声明什么)”学习；已有运行经验时，可直接查并行、内存与排错部分。

## 软件定位、方法与任务

LAMMPS 是开源、可扩展的粒子模拟程序，常用于经典分子动力学、分子静力学和粗粒化模拟。它根据所选势函数计算能量与力，再积分牛顿运动方程；使用机器学习势也不等于运行时求解电子结构。

| 类型 | 常见任务 |
| --- | --- |
| 热力学与输运 | NVE/NVT/NPT、扩散、热导、黏度、相变 |
| 固体与界面 | 拉伸、缺陷、位错、裂纹、纳米颗粒 |
| 分子与粗粒化 | 聚合物、液体、电解液、介观颗粒 |
| 扩展方法 | NEB、增强采样、反应势、ML 势等，依相应 package 而定 |

优势是模型覆盖广、脚本灵活、易于构建非标准材料问题；局限是输入组合自由度大，势函数的适用性往往比程序设置更决定结果。普通非反应力场不能描述任意成键断键，也不能直接输出 DFT 能带。[VASP](../../VASP/基础与准备/VASP基础知识.md)/[CP2K](../../CP2K/基础与准备/CP2K基础知识.md) 可提供小体系第一性原理参照；生物分子标准工作流可对照 [GROMACS](../../GROMACS/基础与平衡/GROMACS基础知识.md)。功能以[官方手册](https://docs.lammps.org/Manual.html)为准。

## 输入规则、单位与势文件

主脚本名称任意，常用 `in.lammps`；命令按顺序执行，先定义再引用。`#` 为注释，`&` 可续行；变量用 `${name}` 或即时表达式等形式，展开时机需要区分。

| 输入部分 | 要检查的内容 |
| --- | --- |
| `units`、`atom_style`、`boundary` | 单位、每原子的属性和边界条件 |
| `read_data/create_atoms` | 原子类型、盒子、分子拓扑、质量与电荷 |
| `pair/bond/angle/..._style` | 模型形式；带电体系还可能需要 `kspace_style` |
| `*_coeff`、外部势文件 | 参数、类型与元素映射；顺序必须与数据一致 |
| `fix/compute/dump/run` | 时间积分、温控、观测量、输出和运行长度 |

`units metal` 常用 Å、ps、eV、bar；`real` 常用 Å、fs、kcal/mol、atm；`lj` 是约化单位。输入脚本改了单位，参数文件未必随之自动换算。特别是 LJ 下的 `lattice` 数值表示数密度，见[晶格扫描](../结构与热力学/LAMMPS晶格常数与凝聚能.md)。

EAM、MEAM、Tersoff、ReaxFF 和 ML 势有不同文件结构与类型映射规则；LJ 等简单势可直接在脚本中给参数。势必须适合元素组合、相态、温压和目标物性，不能仅凭扩展名或元素齐全就使用。记录来源、版本和单位，保留相关引用。

## 一般流程与输入辅助

1. 用 Atomsk、ASE、Moltemplate、TopoTools 或 Packmol 建结构/拓扑，核对转换后的类型和单位。
2. 检查短程重叠、边界、势映射；先最小化并运行短步数测试。
3. 平衡温度、压力与结构，再建立生产采样和周期重启。
4. 同时检查数值稳定性与统计收敛，用 OVITO、MDAnalysis 或脚本分析。

Packmol 主要生成坐标，不会自动补齐完整力场拓扑。`fix nvt/npt` 自带时间积分，不能在同组上再叠加 `fix nve`；`fix langevin` 通常需要另配积分器。完整小例见[最小案例目录](../../../examples/lammps/minimal)。

## 版本、并行与线程

`lmp`、`lmp_mpi`、`lmp_serial` 等名称由安装决定；支持的势与加速功能见 `lmp -h` 的构建信息和 package/style 列表。OPENMP、KOKKOS、GPU、INTEL 等是不同加速路径，不能只改环境变量就获得未编译的功能。见[加速包说明](https://docs.lammps.org/Speed_packages.html)。

主要 MPI 并行方式是空间分解，邻域通过 ghost 原子通信；体系过小、真空太多或几何细长时，进程过多反而低效。已分配 8 核且具备 OPENMP package，可从下列布局测试：

```bash
export OMP_NUM_THREADS=2
mpirun -np 4 lmp -sf omp -pk omp 2 -in in.lammps > run.out 2>&1
```

不是每个 style 都有 `/omp` 实现；KOKKOS/GPU 需要各自的 `-k/-pk/-sf` 设置。以日志末尾的 Pair、Neigh、Comm 等计时和 ns/day 判断瓶颈。运行机制见[官方基础](https://docs.lammps.org/Run_basics.html)。

## 内存与输出控制

没有适用于所有 style 的总内存硬上限关键词。占用来自本地/ghost 原子、邻居表、长程网格、逐原子数组、势和 ML 模型。日志中的每进程内存统计不是所有库和 GPU 显存的完整总和；PBS 申请内存与程序配置要分别考虑。过密结构或异常邻居数先检查模型，不要直接增大内存掩盖错误。

`thermo` 管日志频率，`thermo_style/thermo_modify` 管物理量、格式与归一化；`dump/dump_modify` 管轨迹内容和频率，`fix ave/time` 等管统计。需要逐原子身份连续性时保存 id；计算扩散时还需展开坐标或正确镜像信息。采样频率应服务于分析，而不是每步输出全部数据。

## 排错、结果与续算

| 现象 | 优先检查 |
| --- | --- |
| `Unknown ... style` | package 是否编译、名字是否存在于当前版本 |
| `Lost atoms`、NaN、能量突跳 | 初始重叠、单位、时间步长、边界和势参数 |
| 邻居表/内存错误 | 结构密度、邻域范围和所需数组，而非仅看 MPI 最后一行 |
| `ERROR`、进程被杀 | `log.lammps`、重定向输出及 PBS 错误记录中的最早原因 |

短测试应同时看温度、能量、压力、原子数与结构；正常跑完不等于平衡或采样充分。

用 `restart` 定期写二进制检查点，或用 `write_restart` 主动保存；通过 `read_restart` 续算。部分 fix 状态需要用相同 id/style 重新声明才能接续，compute、dump 等也要重建；不是所有命令和外部势数据都会被完整保存。二进制文件尽量由同一程序版本读取；`write_data/read_data` 更便携，却不能替代完整动力学检查点。细节见[重启手册](https://docs.lammps.org/read_restart.html)。

## 先选模型，再选计算命令

### 势函数能回答什么问题

| 模型 | 常见用途 | 需要特别核对 |
| --- | --- | --- |
| LJ 等简单成对势 | 方法学习、简化流体与模型固体 | 约化单位与模型适用范围 |
| EAM/MEAM | 金属结构、缺陷与力学 | 元素组合、相结构和缺陷训练/验证范围 |
| Tersoff、Stillinger–Weber 等 | 部分共价材料 | 参数版本、适用配位与相态 |
| 固定拓扑分子力场 | 有机分子、聚合物与液体 | 原子类型、键角二面角、非键规则 |
| ReaxFF 等反应势 | 指定参数集覆盖的反应过程 | 电荷平衡、反应类型与参数质量 |
| 机器学习势 | 训练域内的原子势能面 | 元素、能量零点、训练域与外推风险 |

相同元素的势也可能有不同目标：某个势能较好再现晶格常数，不代表能可靠预测熔点、表面能和裂纹。选势时先阅读来源与验证物性，再用小模型核对本研究所需的量。

### 系综、时间积分和温压控制

NVE 不主动控制温度，适合检查积分稳定性和部分动力学性质；NVT 约束温度而固定盒子；NPT 允许盒子按压力耦合变化。压力涨落在小体系中可能很大，应看足够长的平均和误差，不能要求每一步等于设定压力。

`fix nve/nvt/npt` 是积分器；`fix langevin` 加入阻尼与随机力，通常与 `fix nve` 配合。温控阻尼时间与时间步是两个量：前者描述耦合时间尺度，后者控制积分离散。重复积分同一组原子会改变动力学；同样，过强温控可能影响要测量的输运过程。

## 一个不依赖外部势文件的完整小例

下例建立周期 LJ 晶体，最小化后以 NVT 短时运行。它用于理解输入顺序和输出，不代表已经完成平衡与统计采样。

```text
# LJ约化单位：长度sigma、能量epsilon、质量m。
units lj
atom_style atomic
boundary p p p
lattice fcc 0.8442
region box block 0 5 0 5 0 5
create_box 1 box
create_atoms 1 box
mass 1 1.0

pair_style lj/cut 2.5
pair_coeff 1 1 1.0 1.0 2.5
neighbor 0.3 bin
neigh_modify delay 0 every 1 check yes

thermo 100
thermo_style custom step atoms temp pe ke etotal press vol
thermo_modify norm no
minimize 1.0e-8 1.0e-8 1000 10000

reset_timestep 0
velocity all create 0.7 928374 mom yes rot no dist gaussian
timestep 0.005
fix integrator all nvt temp 0.7 0.7 1.0

dump trajectory all custom 100 trajectory.lammpstrj id type xu yu zu
dump_modify trajectory sort id
restart 1000 restart.*
run 5000
write_restart final.restart
write_data final.data
```

`lattice fcc 0.8442` 在 LJ 单位中给数密度，盒子边长则按晶格单位建立，不能把 0.8442 当成 Å。`pair_coeff` 的两个 1.0 分别为 epsilon 与 sigma；2.5 为截断。[`thermo_modify norm no`](https://docs.lammps.org/thermo_modify.html) 使此处广延量按整体输出，而非自动按原子数归一化；和文献比较时需明确是总能还是每原子能。

`minimize` 不生成热平衡轨迹；`velocity create` 设置初速度也不等于已平衡。5000 步仅是演示长度，生产任务需检查温度、能量、结构以及目标量的统计稳定性。

### 怎样从小例迁移到真实材料

换成 Cu EAM 时，不只是改 `pair_style`：单位通常改为 `metal`，质量、时间步、温度、势文件映射和分析单位都要一起检查。换成分子体系时，还可能要用包含分子、电荷、键角等属性的 `atom_style`，并准备拓扑和长程相互作用。

Atomsk 适合晶体和缺陷建模；分子体系可用 Moltemplate、TopoTools 等处理拓扑，Packmol 装填坐标。完成转换后用 OVITO 检查盒子、类型、键和边界，再运行 `run 0` 检查初始化与当前能量；`run 0` 能通过并不证明动力学稳定。

## 从短测试走到可解释的结果

### 最小化、平衡与生产分开

1. 最小化消除不合理接触，检查最大力和结构是否符合预期。
2. 选择合适系综平衡，观察密度、能量与结构是否仍有系统漂移。
3. 丢弃平衡段，开始生产统计；根据相关时间而非总帧数估计独立样本。
4. 用分块或独立重复计算误差，并检查尺寸、时间步和采样长度影响。

平均温度正确只是必要条件之一。扩散要检查 MSD 的线性时间区间和周期展开；RDF 要检查归一化与组分定义；热导和黏度还依赖相关函数、时间窗口与有限尺寸。可顺次学习[扩散案例](../扩散与输运/LAMMPS均方位移与扩散系数.md)、[RDF 案例](../结构与热力学/LAMMPS固液结构与径向分布函数.md)和[热响应案例](../结构与热力学/LAMMPS热膨胀与定容热容.md)。

### 输出为什么不能越多越好

保存频率应由分析时间尺度决定。缓慢结构变化不需要每步写坐标；速度自相关等快速动力学分析则可能需要更密采样。`dump` 的周期是步数，物理时间间隔等于该周期乘时间步。

| 目标 | 建议保留 | 常见问题 |
| --- | --- | --- |
| 结构与缺陷 | id、type、盒子、坐标 | 未保存类型或原子身份，后续难追踪 |
| MSD/扩散 | 展开坐标，或坐标与镜像信息 | 对包裹坐标直接作位移 |
| 局域应力/能量 | 所需逐原子 compute 与定义 | 把逐原子 virial 直接当宏观压力 |
| 热力学平均 | 时间、温度、能量、体积等 | 平衡段混入生产平均 |
| 动力学续算 | 二进制 restart 及所需外部数据 | 以轨迹或 data 文件代替完整状态 |

## 续算脚本应重新声明什么

对于上面的例子，可使用同版本程序读取 `final.restart`：

```text
read_restart final.restart
thermo 100
thermo_style custom step temp pe ke etotal press vol
thermo_modify norm no
fix integrator all nvt temp 0.7 0.7 1.0
dump trajectory all custom 100 continued.lammpstrj id type xu yu zu
dump_modify trajectory sort id
restart 1000 continued.restart.*
run 5000
```

这里重新创建了输出与积分 fix，并沿用原 fix 的 id 和 style，以便恢复它已保存的状态。其他模型可能还要重新指定未存入 restart 的势系数或外部文件；具体查[保存内容与限制](https://docs.lammps.org/read_restart.html)。随机过程、并行布局和浮点累加顺序变化可能导致轨迹逐步分离，不能把逐位相同当作所有续算的默认保证。

## 诊断错误的顺序

遇到 `Lost atoms`，先查看异常前的温度、压力和能量，再用更密的短轨迹检查坏接触、边界或过大时间步。若初始势能极高，优先修复结构和单位。若 `Unknown pair style`，先用 `lmp -h` 核对编译包；这属于功能缺失，不是势文件数值问题。

邻居表溢出时，检查密度、截断与结构是否合理，再考虑调整相关存储参数。性能不佳时，查看 Pair、Neigh、Comm 计时：通信占比高可减少 MPI 进程，力计算占比高则考虑适用的加速包。任何性能比较都应在相同模型和精度下进行。

## 第三方库、插件与资源

MPI 支撑进程并行；FFT 库服务于相关长程算法；Kokkos、CUDA/HIP 等用于相应加速。PLUMED、COLVARS、DeepMD、ML-IAP 等接口或包按构建和版本提供，调用前先查所需安装方式与支持的势/命令。

OVITO 用于缺陷和轨迹可视化，ASE/Atomsk 用于建模，MDAnalysis 用于轨迹统计。参数与语法查询优先看与运行版本匹配的[命令索引](https://docs.lammps.org/Commands_all.html)，安装和主题导航见 [LAMMPS 目录](../README.md)。
