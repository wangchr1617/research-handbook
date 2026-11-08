# CASTEP 的 Si 与 Al 能带对照

先在 Si 上区分自洽 k 网格和路径采样，再换成 FCC Al 观察部分占据。每种材料各自收敛结构、截断、赝势和自洽网格。已有输入可从[Si 单点练习](CASTEP首个单点计算.md)和[截断与 k 点收敛](CASTEP截断与k点收敛.md)接续。

## 用 Si 查找间接带隙

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

## 用 Al 检查金属占据

从 FCC 原胞开始，采用单个 Al 原子，晶格常数用自己的优化结果。分别测试自洽网格和电子展宽。画图时把费米能级置零，核对跨越零能的能带和部分占据。若短路径没出现交叉，先检查完整路径和均匀网格的费米附近态密度。

## DOS 和 PDOS 单独取样

| 目标 | 任务与网格 | 看什么 |
| --- | --- | --- |
| 总 DOS | `SPECTRAL_TASK : DOS`，用更密的均匀谱网格 | 费米附近态数、峰位和积分 |
| 原子或轨道分解 | `SPECTRAL_TASK : PDOS`，保持相同能量参考与网格 | 各原子、自旋、轨道的相对贡献和投影残差 |
| 路径能带 | `SPECTRAL_TASK : BANDSTRUCTURE` 与路径 | 带边、简并、沿方向的色散 |

用独立目录保存 DOS 和 PDOS 输入输出，路径块换成相容的规则谱网格。按能窗用 `SPECTRAL_NBANDS` 等控制空带数。后处理可用与输出相容的 OptaDOS 流程，统一展宽、每胞或每原子归一化，以及自旋通道。金属 DOS 的尖峰位置和带隙边缘都要分别检查网格与展宽。

比较 CASTEP 与 [VASP 的 Si 实例](../../examples/materials/semiconductor/README.md)时，先对齐原胞、赝势价电子数、k 点密度、泛函及能量零点。结果表至少记录带隙、带边位置和计算设置。公开练习见 [CASTEP Si 教程](https://castep-docs.github.io/castep-docs/tutorials/Bands_and_DOS/semiconductors/)、[金属教程](https://castep-docs.github.io/castep-docs/tutorials/Bands_and_DOS/metals/)及[能带和 DOS 教程](https://castep-docs.github.io/workshop/workshop/02_bands_dos/)。
