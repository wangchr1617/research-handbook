# SMD 半径、离子液体参数与 CM5 接口

**适用环境：ORCA 6.1、Multiwfn 2026.7.15；Python 3.10+、NumPy 与 Matplotlib 用于分析。**

本例分别用 Br⁻ 比较 SMD/SMD18 的空腔半径，用同一水分子几何比较内置水溶剂与自定义 GIL 参数，再由气相水波函数得到 CM5 数据。它展示模型参数与能量账目，计算条件和数据都可单独查看。

## 生成与运行六个任务

从仓库根目录运行，工作目录应尚不存在：

```bash
python examples/orca/minimal/solvation-parameters/prepare.py \
  --work-root /tmp/solvation-parameters
ORCA_EXEC=/path/to/orca bash /tmp/solvation-parameters/run-initial.sh

python examples/orca/minimal/solvation-parameters/prepare.py \
  --work-root /tmp/solvation-parameters --stage solvents
ORCA_EXEC=/path/to/orca bash /tmp/solvation-parameters/run-solvents.sh
```

将 `/path/to/orca` 换成当前环境可运行的驱动绝对路径。输入使用单进程、256 MB `MaxCore`，不在驱动前额外加 `mpirun`。各任务写入独立目录，生成器拒绝覆盖已有任务。

| 任务 | 计算条件 |
| --- | --- |
| `br-gas` | Br⁻，M06-2X/def2-TZVPD，气相单点 |
| `br-smd` | 同一原子与电子层级，SMD 乙腈 |
| `br-smd18` | 同上，原生 SMD18 开关 |
| `water-opt` | 中性水，气相 ORCA B3LYP/G、def2-TZVP，优化与频率 |
| `water-smd` | 水的最终气相几何，SMD 水单点 |
| `water-gil` | 同一水几何，GIL 平均物性及 `[EMIM][BF4]` 组成比例 |

水使用 ORCA 的 `B3LYP/G`，其局域相关变体与该程序的裸 `B3LYP` 不同。跨程序比较时按实际定义对齐，见[泛函与实现](../../../../notes/计算化学/跨程序比较与结果复查.md)。

## CM5 数据与后处理

进入 `water-opt`，用 ORCA 的 `orca_2mkl` 将最终波函数转换为 Molden，再运行随任务复制的菜单。命令中的软件路径按环境替换：

```bash
cd /tmp/solvation-parameters/water-opt
/path/to/orca_2mkl calc -molden > conversion.out
/path/to/Multiwfn calc.molden.input -nt 1 < cm5.menu > cm5.out
```

`cm5.menu` 对应主菜单 `7` → CM5 `16` → 内置球对称自由原子密度 `1`，随后按提示将原子布居归一化到实际电子数，并导出 `calc.chg`，最后退出。此菜单按该版本默认 `uESEinp=0` 组织；其他设置或版本出现不同提示时，应先查看界面再调整菜单，避免输入错位。

回到仓库根目录，分析全部原生输出：

```bash
python examples/orca/minimal/solvation-parameters/analyze.py \
  --work-root /tmp/solvation-parameters --output-dir /tmp/solvation-analysis
```

生成 `analysis.json`、`water.cm5-input` 与 `solvation-parameters.png`。已有的[完整数值](analysis.json)及[水的 CM5 输入模板](water.cm5-input)可直接查看。模板以最终 Å 坐标和归一化后的 CM5 电荷写出，原子序号、顺序和电荷总和相互对应。本脚本处理数据接口，输出不包含 uESE 程序算出的溶剂化自由能。

## 半径与能量怎样读

Br⁻ 的气相能量约 −2574.2774015352 Hartree。SMD 与 SMD18 的原生输出分别给出 Br 半径 3.06、2.60 Å，最终能量约 −2574.3633952189、−2574.3754852751 Hartree。相对于匹配气相结果的能量差为 −225.7764、−257.5188 kJ/mol。

两种输出的 CDS 项同为约 −8.8301 kJ/mol，静电项和溶质电子重排则不同。因此，最终 SMD 能差已经含 CDS，不再加一次；单独的 `CPCM Dielectric` 也不等于最终能差。这里展示单离子对半径的敏感性，未将数值与任何实验单离子标度或卤键平衡作等同。

独立 Born 球模型与原生对照放在[同一张方法图](../../../../notes/计算化学/assets/solvation-parameters.png)中，用来解释半径和介电常数的趋势。图中两部分来自不同模型，数值不要求相等。

## 自定义介质怎样核对

`water-gil.inp` 使用 SMD-GIL 平均物性，并由 `[EMIM][BF4]` 的化学式单元计算 $\phi=3/13$、$\psi=4/13$。输入中的合法 `SMDsolvent` 名称用于初始化，随后显式覆盖静态介电、折射率与全部 CDS 描述符；原生输出显示 `CUSTOM` 及实际数值。

检查输出中的 `Epsilon=11.5`、`Refrac=1.43`、`Soln=Soln25=1.43`、`Sola=0.229`、`Solb=0.265`、`Solg=61.24`，以及打印舍入后的 `Solc=0.2308`、`Solh=0.3077`。只有这些值与目标一致，才将该结果作为这套自定义参数的计算。

在同一气相水几何上，内置水与该 GIL 近似的最终能量减气相分别约为 −34.1086、−25.0982 kJ/mol。GIL 参数不是纯 `[EMIM][BF4]` 的完整实测参数集，这组差异也没有包含结构集合、局部离子配位或混合物效应。

## 标准态与数据边界

这些 SMD 能量差按模型的两相相同浓度约定解释，不额外叠加热化学或压力到浓度项。若组装 1 atm 气相热化学到 1 mol/L 溶液自由能，再按完整循环加入对应转换；298.15 K 单物种项约 7.92587 kJ/mol。反应量按化学计量求和，不能对所有反应一概只加一次固定数值。

水的三个内部频率约为 1616.82、3784.33、3888.99 $\mathrm{cm^{-1}}$，与当前气相极小点对应。频率检查支持这个结构的局部驻点性质；溶液最优结构与低频构象集合则需在相应环境中另行求得。

溶液能量的组合见[溶液自由能循环](../../../../notes/计算化学/隐式溶剂与溶液自由能.md)。
