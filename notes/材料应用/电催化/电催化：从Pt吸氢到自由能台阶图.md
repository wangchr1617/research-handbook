# 电催化：从 Pt 吸氢到自由能台阶图

**适用环境：macOS / Linux，CPU 计算。**

## 从反应式到模型

电催化必须同时明确反应、中间体、活性位点、参考态及电位标尺。这里以 Pt(111) 吸氢和理想化两步 HER 为例，依次计算吸附电子能、H 振动零点能并构造 CHE 自由能台阶图。CHE 将质子—电子对化学势与氢气及电位联系，经典定义见原始研究[^1]。

## 计算链

```mermaid
flowchart LR
    accTitle: 电催化自由能计算路线
    accDescr: 在统一表面模型下优化洁净表面、吸附态与分子参考，计算振动修正后沿电位构造自由能图。
    model[表面、位点与覆盖度] --> energies[洁净面、H吸附态、H2优化]
    energies --> vibration[振动与零点能]
    vibration --> reference[温度与CHE电位参考]
    reference --> diagram[自由能台阶图]
    diagram --> kinetics[按需计算势垒和溶剂效应]
```

模型为 `2×2`、三层 Pt(111)，共 12 Pt，上表面一个 H，覆盖度 1/4 ML，表面法向两侧各留 8 Å 真空。底两层固定、顶层与 H 放松。Pt 晶格参数 3.98 Å、400 eV、`3×3×1` k 网格；H 初态在 fcc 位点。底层数、层数、真空、覆盖度和位点都需单独检验。

非对称 slab 使用 `LDIPOL=.TRUE., IDIPOL=3`，并把偶极中心放在 slab 中部。优化与吸附 H 的频率计算采用一致电场修正；原理与收敛注意事项见官方说明[^2]。

## 电子吸附能

统一定义

$$\Delta E_H=E(\mathrm{slab}+H)-E(\mathrm{slab})-\tfrac12 E(H_2).$$

洁净面、吸附态和 H₂ 分别优化。对于 slab，底层约束、面内胞、PAW 势与电子精度保持一致；对 H₂ 使用足够大的孤立盒子。$\Delta E_H<0$ 表示在这一电子能参考下吸附放热，单位 eV/H。若有多个 H，还应区分平均和增量吸附能。

## 振动、熵与自由能

H 吸附态采用“Pt 固定、仅位移 H”的局部 Hessian，H₂ 则计算分子振动：

```text
IBRION = 5
NFREE = 2
POTIM = 0.015
EDIFF = 1E-8
```

需要检查频率数、显著虚频及位移幅度敏感性。部分 Hessian 忽略 Pt 与 H 的耦合，不等同于完整 slab 振动计算。对于 H₂，用内部伸缩模作分子 ZPE，不把数值平移/转动频率当成真实振动。

$$\Delta G_H=\Delta E_H+\Delta ZPE-T\Delta S,$$

本例 $\Delta ZPE=ZPE_{H*}-\tfrac12ZPE_{H_2}$，忽略吸附态振动熵，用 $-T\Delta S\approx\tfrac12TS^\circ_{H_2}$。在 298.15 K、1 bar，$S^\circ_{H_2}=130.68$ J/(mol·K)，来源为 NIST[^3]；除以法拉第常数将 J/mol 转成每粒子 eV。该近似不能不加说明地套用到所有吸附分子。

## CHE 电位与台阶图

在 RHE 标尺下，吸氢还原步骤有 $\Delta G(U)=\Delta G(0)+eU$。还原步骤在更负电位下更有利；如果参考改为 SHE，则需按定义处理 pH，不可同时加两遍修正。

本例将两步写成：初态 `2(H⁺+e⁻)+*`，中间态 `H*+H⁺+e⁻`，末态 `H₂+*`。以各电位的初态为零，三个台阶依次为

$$0,\quad\Delta G_H+eU,\quad2eU.$$

在 $U=0$ 时末态回到零；在 $U\ne0$ 时不能仍强制把末态设为零。图中的连接线是状态顺序，不是过渡态势垒。吸氢描述符接近零也不自动保证最高实际电流。

## 从 HER 扩展到 OER/ORR 与多产物反应

先写配平的总反应，再列出每一步中间体、质子/电子数、吸附位与分子参考。每个态都计算相容的电子能和修正，再按同一电位标尺比较各步。OER/ORR 需注意 O₂ 参考误差及水参考；CO₂ 还原还涉及多条路径、竞争 HER、溶剂稳定与产物选择性。不能只替换台阶图标签而保留原有反应能。

需要动力学结论时，分别定义初末态与溶剂、电位环境，再进入[NEB](../../VASP/表面与反应/NEB过渡态搜索.md)、[CP2K 过渡态](../../CP2K/动力学与反应/CP2K过渡态搜索.md)或增强采样。真空 slab 的电子能、CHE 热力学和恒电位界面自由能是不同层次的模型。

## 检查与报告

至少列出 slab 层数、固定层、覆盖度、位点、真空、赝势、泛函、截断能、k 点、力阈值、振动修正、温度、气压、电位标尺及溶剂处理。本例没有显式溶剂或恒电位电子库，不把 CHE 曲线称为完整界面反应势垒。吸附、电荷与表面资料见 [VASP 表面与反应](../../VASP/表面与反应/README.md)。

[^1]: Nørskov et al. Trends in the Exchange Current for Hydrogen Evolution. Journal of The Electrochemical Society 152, J23 (2005). https://doi.org/10.1149/1.1856988
[^2]: VASP. Electrostatic corrections. https://vasp.at/wiki/Electrostatic_corrections
[^3]: NIST Chemistry WebBook. Hydrogen, gas-phase thermochemistry. https://webbook.nist.gov/cgi/cbook.cgi?ID=C1333740&Mask=1

## 配套案例

[Pt(111)吸氢、振动修正与 HER 台阶图](../../../examples/materials/electrocatalysis/README.md)提供参数、运行命令与数据说明。先检查[本机运行与结果检查](../本机运行与结果检查.md)，再运行案例；更换参数后使用新输出目录。

返回[电催化](README.md)或[材料应用](../README.md)。
