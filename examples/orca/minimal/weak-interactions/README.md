# 水二聚体的 IGMH 片段分析

**适用环境：Windows、macOS、Linux；已有 ORCA、Multiwfn 及绘图依赖。**

本例用自行构造的六原子平面水二聚体说明波函数、片段、空间网格、等值面及原子对指标的对应关系。O···O 为 `2.9 Å`，几何未经优化；计算层级为 PBE0/def2-SVP、中性闭壳层单点。完整方法见[IGMH 教程](../../../../notes/计算化学/Multiwfn的IGMH片段分析.md)。

## 输入与运行

在独立工作目录放入 [orca.inp](orca.inp)、[structure.xyz](structure.xyz)和 [multiwfn.in](multiwfn.in)。下列命令在该工作目录执行，软件名需在路径中可用：

```bash
orca orca.inp > orca.out
orca_2mkl orca -molden
multiwfn orca.molden.input < multiwfn.in > multiwfn.out
```

先确认 ORCA 正常结束，Molden 含 20 个电子和正确的六原子顺序。Multiwfn 操作文件依次进入 `20 → 11`，定义片段 `1-3`、`4-6`，选择包围六个原子并外扩 `2 Å` 的网格，间距 `0.20 Bohr`；导出 Cube 后计算原子对指标，积分网格为 `75×434`，最后正常退出。自动输入按 Multiwfn 2026.7.15 编写，其他版本先按屏幕核对菜单和额外提示。

本例保留结果所用的 `IGMvdwscl=2.0` 筛选条件，实际值从 `multiwfn.out` 检查。配置文件被读取与否、程序版本或构建差异可能改变默认值；使用不同筛选时，保存相应条件并重新生成结果。程序没有导出的完整 `dg`、`dg_intra` 不作为本例数据使用。

## 数据提取与重绘

使用已具备[依赖](requirements.txt)的 Python 环境，把 [analyze.py](analyze.py)和 [plot.py](plot.py)放到同一工作目录，执行：

```bash
python analyze.py --grid-dir . --orca-output orca.out \
  --multiwfn-output multiwfn.out --wavefunction orca.molden.input
python plot.py --data-dir . --output interaction.png
```

`analyze.py` 检查两个 Cube 的结构、网格与有限数值，提取 \(\delta g_{inter}=0.006\) a.u. 表面，并在相同位置插值着色场。它同时保留最接近 `z=0` 的实际网格层，未把该切片插值成精确的零平面。脚本限于本例的正交单标量 Cube；换成斜晶胞时需要相应几何处理。

[interaction-data.npz](interaction-data.npz)保存小型表面顶点、三角面、颜色及切片数据，[interaction-analysis.json](interaction-analysis.json)记录几何、计算条件、网格、阈值、原子对表和源文件摘要。已有这两个文件时，可只运行 `plot.py` 重绘。完整波函数、ORCA 日志和三维 Cube 留在计算工作目录，仓库保留可重建图像所需的小型派生数据。

## 结果怎样检查

原子 2 是指向另一水分子的供体 H，原子 4 是受体 O。图中两者之间出现接触表面；它描述给定几何下的空间分布。细网格的有限盒子、筛选后片段间积分约为 `0.084623 e/Bohr`，所有跨片段原子对指标和约为 `0.155499 e/Bohr`，H2···O4 的原子对指标占后者 `47.21%`。这几项量有不同定义，不能用该百分比表示氢键能量贡献。

改变网格间距、外扩范围、等值面和筛选条件时分别检查效果。原子对积分有独立的径向/角向网格，也要做精度检查。进一步判断结构与结合能，见[相互作用能与 BSSE](../../../../notes/计算化学/相互作用能与BSSE校正.md)。

## RDG 与 IRI 对照

复用同一个 `orca.molden.input`，建立 `rdg/`、`iri/`、`density-gradient/` 和 `promolecular/` 四个分析目录，分别保存独立网格，避免同名 `func1.cub`、`func2.cub` 互相覆盖。四份菜单文件都放在这些目录的上一级。

| 在哪个目录运行 | 输入文件与菜单 | 输出的两个函数 |
| --- | --- | --- |
| `rdg/` | 波函数；[rdg.in](rdg.in) | 实际密度着色场、默认筛选 RDG |
| `iri/` | 同一波函数；[iri.in](iri.in) | 实际密度着色场、IRI |
| `density-gradient/` | 同一波函数；[density-gradient.in](density-gradient.in) | 实际密度、梯度模 |
| `promolecular/` | `structure.xyz`；[promolecular.in](promolecular.in) | 准分子着色场、准分子 RDG |

例如在 `rdg/` 内执行 `multiwfn ../orca.molden.input < ../rdg.in > multiwfn.out`。其余目录依次替换菜单文件；准分子路线改用 `multiwfn ../structure.xyz < ../promolecular.in > multiwfn.out`。这些操作不再运行 ORCA，也不修改其波函数。

回到上一级工作目录，用 [compare_fields.py](compare_fields.py)核对并提取数据，再用 [plot_fields.py](plot_fields.py)重绘：

```bash
python compare_fields.py --fields-root . --wavefunction orca.molden.input
python plot_fields.py --data-dir . --output fields.png
```

两个脚本与 `analyze.py` 放在一起，复用同一 Cube 读取器。脚本按本例的实际默认条件核对：`RDG_maxrho=0.05`、`RDGprodens_maxrho=0.1`、IRI 指数 `1.1`、`IRI_rhocut=5e-5`，不一致时应检查并按实际条件调整分析。[fields-analysis.json](fields-analysis.json)记录科学条件、阈值与源文件摘要，[fields-data.npz](fields-data.npz)保存表面与显示范围内的散点；已有两文件即可只运行绘图脚本。

RDG 和 IRI 的 `output.txt` 是五列坐标/函数数据；IGMH 的散点导出布局不同，不能混用列号。完整读图见[NCI/RDG](../../../../notes/计算化学/NCI与RDG的网格、筛选和散点图.md)和 [IRI](../../../../notes/计算化学/IRI与反应路径电子结构读图.md)。

## 完整场、mIGM 与表面测量

IGMH 快捷入口可能启用网格筛选。为核对其影响，可在本次会话中定义两个片段，并用用户函数 `91` 直接计算完整的片段间场；这不改写配置文件。以下各目录与原始波函数/结构位于同一级，分别运行对应菜单：

| 分析目录 | 程序载入文件 | 菜单文件 | 结果 |
| --- | --- | --- | --- |
| `igmh-full-020/` | `../orca.molden.input` | [igmh-full-020.in](igmh-full-020.in) | 完整着色场及 IGMH，间距 `0.20 Bohr` |
| `igmh-full-025/` | 同上 | [igmh-full-025.in](igmh-full-025.in) | 完整场，间距 `0.25 Bohr` |
| `migm/` | `../structure.xyz` | [migm.in](migm.in) | 几何 mIGM 与准分子着色场 |
| `surface-grid/` | `../orca.molden.input` | [igmh-surface-grid.in](igmh-surface-grid.in) | 对完整细网格 Cube 测面积/体积 |
| `surface/` | 同上 | [igmh-surface.in](igmh-surface.in) | 从实空间函数重新生成表面并测量 |

例如在 `igmh-full-020/` 内执行 `multiwfn ../orca.molden.input < ../igmh-full-020.in > multiwfn.out`，其余任务替换输入和菜单。先完成完整网格，再运行引用该 Cube 的 `surface-grid/`。菜单通过 `iu → 91` 选择会话函数，原波函数不变。

把 [measure_surfaces.py](measure_surfaces.py)、[plot_surface_metrics.py](plot_surface_metrics.py)和 `analyze.py` 放在上一级工作目录，原 IGMH 快捷任务的 `dg_inter.cub` 也保留在这里。完成各任务后运行：

```bash
python measure_surfaces.py --full-fine igmh-full-020/func2.cub \
  --full-coarse igmh-full-025/func2.cub --screened dg_inter.cub \
  --migm migm/dg_inter.cub --surface-log surface-grid/multiwfn.out
python plot_surface_metrics.py --output surface-metrics.png
```

脚本按本例 H/O 半径、六原子顺序和非周期正交网格重建筛选，对阈值 `0.003`、`0.006`、`0.012` a.u. 计算面积/体积，同时检查表面边的闭合与方向。原始筛选场应匹配本例实际系数 `2`，条件不符时会提示核对。[surface-metrics.json](surface-metrics.json)保存各项条件与指标，[surface-metrics.dat](surface-metrics.dat)提供简明表格，已有 JSON 即可重绘。

本例说明三种误差应分别检查：显示筛选可以保持某个等值面却改变积分；阈值改变可明显改变面积/体积；相同 Cube 的不同表面算法也会有小差异。详见[等值面测量](../../../../notes/计算化学/等值面面积、体积与网格收敛.md)。

## IRI 域积分、轨道体积与 Hirshfeld 表面

继续复用同一波函数。IRI 域内电子数、轨道阈值包围体积和 HS 接触面积分别针对不同区域定义，不应相互换算。先完成前面的 `iri/` 与 `density-gradient/` 粗网格任务，再在工作目录中建立以下目录：

```bash
mkdir -p domain-fields/fields-010 domain-fields/iri-010 \
  domain-fields/domain-020 orbital hirshfeld
```

五份新增菜单放在波函数所在的工作目录，各任务在表中目录执行。表中命令假设 `multiwfn` 已在路径中；输出日志名也供后处理脚本读取。

| 在哪个目录运行 | 命令 |
| --- | --- |
| `domain-fields/fields-010/` | `multiwfn ../../orca.molden.input < ../../domain-density-sign.in > multiwfn.out` |
| `domain-fields/iri-010/` | `multiwfn ../../orca.molden.input < ../../iri-fine.in > multiwfn.out` |
| `domain-fields/domain-020/` | `multiwfn ../../iri/func2.cub < ../../domain-cube.in > multiwfn.out` |
| `orbital/` | `multiwfn ../orca.molden.input < ../orbital-volume.in > multiwfn.out` |
| `hirshfeld/` | `multiwfn ../orca.molden.input < ../hirshfeld-contact.in > multiwfn.out` |

[domain-density-sign.in](domain-density-sign.in)输出实际密度与 $\mathrm{sign}(\lambda_2)\rho$，[iri-fine.in](iri-fine.in)输出着色场与 IRI；二者都使用 `0.10 Bohr` 网格。[domain-cube.in](domain-cube.in)在 Multiwfn 2026.7.15 中从已有粗网格生成 IRI 域，并从配对的密度 Cube 积分；它不使用新版描述符快捷入口。

[orbital-volume.in](orbital-volume.in)先保存第 10 号 HOMO 的带符号 `MOvalue.cub`，再对内存取绝对值，以 `0.05` 阈值测量并导出 `surf.cub`。[hirshfeld-contact.in](hirshfeld-contact.in)以中心水 `1-3` 和环境 `4-6` 建立 HS，映射 `d_norm`，导出权重 Cube、表面点、两列指纹距离及元素对接触面积。两种任务的 `surf.cub` 含义不同，保持目录分开。

这里的轨道体积由 $|\psi|$ 阈值定义；轨道振幅的阈值单位为 $\mathrm{Bohr}^{-3/2}$，不是电子密度单位。它不规定固定的电子包围比例，也不等于轨道占据电子的总体积。HS 则由中心片段与环境的准分子密度权重划分，接触面积占比描述该表面上的几何归属，不是相互作用能占比。

把 [analyze_domains.py](analyze_domains.py)、[plot_domains.py](plot_domains.py)、`analyze.py` 与 `measure_surfaces.py` 放在工作目录。在上一级工作目录运行：

```bash
python analyze_domains.py --coarse-root . --fine-root domain-fields \
  --orbital-dir orbital --hs-dir hirshfeld --output-dir .
python plot_domains.py --data-dir . --output domain-metrics.png
```

提取脚本默认读取 `multiwfn.out`；若日志使用其它名字，通过 `--log-name` 指定。所有原始日志保留在计算工作目录。

[domain-analysis.json](domain-analysis.json)记录域的空间中心、格点数、半开分箱积分、轨道测量与 HS 条件，[domain-plot-data.npz](domain-plot-data.npz)保存小型指纹数据。已有两份数据时只需绘图脚本即可重绘。该提取脚本限定本例非周期正交网格、两个水的原子顺序与 H/O 半径，采用 26 邻接和格点计数积分；细网格与粗网格的域按空间位置对应，不能假定域号相同。

H2···O4 区域的积分在 `0.20 → 0.10 Bohr` 后由 `0.00310425` 变为 `0.00359576 e`，体积由 `0.0201531` 变为 `0.0238577 Å³`，说明小域仍需检查网格敏感性。轨道的正负波瓣经绝对值统一纳入，独立三角网格测量闭合且方向一致。HS 在孤立二聚体中开放，脚本只给表面积，闭合体积留空；其指纹与面积占比依赖当前盒子。

`d_norm` 的常规定义无量纲，而本例 Multiwfn 2026.7.15 实现额外乘 `b2a`；脚本按本版输出核对，并区分 PQR 坐标舍入造成的最近原子身份歧义。图中指纹使用 Å 距离，不使用 `d_norm` 色标。

HS 的几何表面与映射颜色是两个设置。同一 HS 可以映射 `d_norm`、准分子密度等不同函数；红色斑块的含义应随实际函数及色标说明，不能把密度着色图直接按短接触图解释。指纹图的两轴是到内部与外部最近原子的距离 $d_i,d_e$，本例以 Å 表示；它们不是原子间完整距离，也不是表面权重。

按内部／外部元素划分接触时，`H–O` 与 `O–H` 是两个有方向的归属；合并为同一类前记录规则，并检查互斥、完备分组的面积和。百分比最大的接触类型只表示所占表面份额最大，不保证单个接触最强或总结合能贡献最大。

## Hirshfeld 轨道成分与 ODI

在波函数旁建立 `odi/` 目录，用 [odi.in](odi.in)继续分析同一组轨道：

```bash
cd odi
multiwfn ../orca.molden.input < ../odi.in > multiwfn.out
cd ..
python analyze_odi.py --directory odi --output odi-analysis.json
python plot_odi.py --data odi-analysis.json --output odi.png
```

菜单使用 `8 → 8 → 1` 的内置原子密度 Hirshfeld 分区，定义第一水 `1-3`，输出 1–10 号占据空间轨道的整体/片段 ODI、完整原子成分表和 HOMO 单轨道信息。默认自动积分为每原子 9060 点；原子成分、ODI 与轨道占据数分开解释。

[analyze_odi.py](analyze_odi.py)从 `orbcomp.txt` 重建整体 ODI 并核对原生日志，片段权重小于 1% 时不从这份只保留三位小数的百分比表重建条件 ODI。[odi-analysis.json](odi-analysis.json)保留原生指标、舍入成分、有效原子数和数值条件，[plot_odi.py](plot_odi.py)可仅凭 JSON 重绘。这个 1% 是本例避免舍入放大的报告规则，不能当作轨道参与某过程的物理阈值。

HOMO 整体 ODI 为 78.79，第一水权重 99.691%，条件 ODI 为 79.28；第 6 号轨道的整体 ODI 为 39.48。
