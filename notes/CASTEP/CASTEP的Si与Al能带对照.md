# CASTEP 的 Si 与 Al 能带对照

同一条能带曲线的零点，在 Si 和 Al 上回答的问题不同。Si 以价带顶为参照，便于比较带边的位置；Al 以费米能级为参照，便于看哪些带穿过零能。先用 Si 走通路径计算，再换成 FCC Al 观察部分占据。每种材料各自收敛结构、截断、赝势和自洽网格。已有输入可从[Si 单点练习](CASTEP首个单点计算.md)和[截断与 k 点收敛](CASTEP截断与k点收敛.md)接续。

## 一、沿 Si 的 Γ–X 路径定位带边

复制收敛的 Si 输入到新目录，保留其 `KPOINT_MP_GRID`。将 `.param` 中的任务改为下列两行。

```text
TASK : SPECTRAL
SPECTRAL_TASK : BANDSTRUCTURE
```

对单点笔记使用的原胞，下列路径沿立方晶体一个 Γ–X 方向。它适合观察 Si 的导带谷，完整能带图按原胞对称性添加其他路径段。倒格矢分数坐标依赖晶胞，换胞后重新生成路径。

```text
%BLOCK SPECTRAL_KPOINT_PATH
0.0 0.0 0.0
0.5 0.0 0.5
%ENDBLOCK SPECTRAL_KPOINT_PATH
```

运行同一种子名，检查 `.castep` 中自洽和谱计算的收敛信息，再用 `.bands` 中的本征值和路径信息绘图。图中将价带顶置零，标出 $\Gamma$ 和 X。Si 的价带顶位于 $\Gamma$，导带谷在 Γ–X 之间。沿此方向加密并用三维网格核对全局带边。若多个最低点挤在相邻采样点，报告 k 点步长和拟合范围。

## 二、换成 Al 后检查费米穿越

从 FCC 原胞开始，采用单个 Al 原子，晶格常数用自己的优化结果。分别测试自洽网格和电子展宽。画图时把费米能级置零，核对跨越零能的能带和部分占据。若短路径没出现交叉，先检查完整路径和均匀网格的费米附近态密度。需要确定哪些穿越点属于同一口袋时，再用完整三维网格做等能面，读图可参考[铝费米面案例](../VASP/电子结构与成键/VASP费米面计算.md)。

## 三、用规则网格核对路径没覆盖的区域

| 目标 | 任务与网格 | 看什么 |
| --- | --- | --- |
| 总 DOS | `SPECTRAL_TASK : DOS`，用更密的均匀谱网格 | 费米附近态数、峰位和积分 |
| 原子或轨道分解 | `SPECTRAL_TASK : PDOS`，保持相同能量参考与网格 | 各原子、自旋、轨道的相对贡献和投影残差 |
| 路径能带 | `SPECTRAL_TASK : BANDSTRUCTURE` 与路径 | 带边、简并、沿方向的色散 |

用独立目录保存 DOS 和 PDOS 的输入输出，将路径块换成相容的规则谱网格，并按目标能窗用 `SPECTRAL_NBANDS` 等参数控制空带数。DOS 与 PDOS 可共用同一能量零点，但应检查输出文件是否确实包含所需能窗内的本征值和投影。相关设置可查阅[CASTEP 谱任务关键词](https://castep-docs.github.io/castep-docs/documentation/Spectral/keywords/)；后处理可采用与输出相容的 OptaDOS 流程，并统一展宽、每胞或每原子归一化以及自旋通道。对于金属 DOS 的尖峰位置和半导体的带隙边缘，都应分别检查网格密度与展宽的影响。

比较 CASTEP 与 [VASP 的 Si 实例](../../examples/materials/semiconductor/README.md)时，先对齐原胞、赝势价电子数、k 点密度、泛函及能量零点。结果表至少记录带隙、带边位置和计算设置。公开练习见 [CASTEP Si 教程](https://castep-docs.github.io/castep-docs/tutorials/Bands_and_DOS/semiconductors/)、[金属教程](https://castep-docs.github.io/castep-docs/tutorials/Bands_and_DOS/metals/)及[能带和 DOS 教程](https://castep-docs.github.io/workshop/workshop/02_bands_dos/)。
