# CP2K 分子振动频率

**适用环境：Windows、macOS、Linux（查看和准备输入）；Linux + PBS（提交计算）。**

CP2K 可用有限差分受力构造 Hessian，求分子的简谐振动。以非线性的水分子为例，扣除整体平动和转动后有三个内部振动模式。

## 准备与提交

先做[几何优化](../结构优化/CP2K几何优化.md)，再计算频率。本例的 [structure.xyz](../../../examples/cp2k/minimal/vibrational-analysis/structure.xyz) 已采用优化后的水分子坐标；配套文件为 [cp2k.inp](../../../examples/cp2k/minimal/vibrational-analysis/cp2k.inp)、[job.pbs](../../../examples/cp2k/minimal/vibrational-analysis/job.pbs) 和[频率检查脚本](../../../examples/cp2k/minimal/vibrational-analysis/postprocess.py)。

在单点输入基础上设置 `RUN_TYPE VIBRATIONAL_ANALYSIS`，并加入顶层段：

```text
&VIBRATIONAL_ANALYSIS
  DX 0.01
  FULLY_PERIODIC FALSE
&END VIBRATIONAL_ANALYSIS
```

`DX` 默认单位为 Bohr，而不是 Å。`FULLY_PERIODIC FALSE` 适用于本例分子，并处理整体转动自由度；晶体频率不能直接沿用这一处理。将文件放到集群工作目录，加载 CP2K 后执行 `qsub job.pbs`。

## 判断振动结果

在 `cp2k.out` 中搜索 `VIB|Frequency (cm^-1)`。本例有三个正的内部频率，对应弯曲和两个伸缩模式；可用结构工具查看正常模式，不能仅凭频率排序识别任意复杂分子的振动类型。

小的负频率可能来自残余受力、网格或数值差分误差，明显的虚频则需要结合模式检查结构是否为鞍点。低频模式尤其要求更紧的几何优化和 SCF 收敛；官方建议采用例如 `EPS_SCF 1E-8` 的严格设置，见[振动分析手册](https://manual.cp2k.org/trunk/CP2K_INPUT/VIBRATIONAL_ANALYSIS.html)。

检查时同时保存模式与受力，不仅按虚频大小决定取舍，详见[低频振动与虚频](../../计算化学/低频振动与虚频的处理.md)。分子整体平转动、表面吸附物与周期晶体的自由度应分别处理。

本例演示简谐频率，不等同于含强度的 IR/Raman 光谱。计算强度还需输出偶极矩或极化率，并配置相应的响应计算。

观看模式时使用振动 Molden 数据，核对频率与参与原子；轨道 Molden 不能代替振动位移。两种文件与查看器选择见[结果文件与可视化](../基础与准备/CP2K结果文件与可视化.md#振动动画与光谱分开看)。

由有限差分受力到 Hessian、质量加权与内部模式的关系，见[频率复核](../../计算化学/Hessian、正常模式与频率复核.md)。差分步长和力的单位需一致，受约束或周期体系也不能直接按分子的前六个模式删除。

![优化后水分子的三个内部正常模式频率，约 1609.3、3716.5 和 3821.6 cm⁻¹；图中没有赋予 IR/Raman 强度。](../assets/water-frequencies.png)

图中为优化后水分子的三个内部正常模式，频率约为 1609.3、3716.5 和 3821.6 cm⁻¹，不含 IR/Raman 强度。配套 [plot.py](../../../examples/cp2k/minimal/vibrational-analysis/plot.py)读取实际输出生成，结果检查后自动绘图；需安装 [requirements.txt](../../../examples/cp2k/minimal/vibrational-analysis/requirements.txt) 中依赖。

振动 `.mol` 的 Bohr 坐标、模式归一化、可选强度与 GaussView 转换见[振动 Molden 与 MfakeG](CP2K振动Molden与MfakeG显示转换.md)，另有自有水模式的直接读取和逐帧显示案例。

## 晶体声子与冻结基底不能直接沿用分子判据

周期晶体的 Γ 点正常模式与整个布里渊区的声子谱不同。`FULLY_PERIODIC T` 避免按孤立分子清除转动，但不会自动生成一般 q 点的动力学矩阵。研究色散、声子态密度或晶格热容时，应通过适当超胞的位移—受力数据建立力常数，再检查超胞、位移、电子精度及声学支；不能只用原胞 Γ 点正频率断言全晶体动力学稳定。已有[声子流程](../../VASP/振动与热力学/VASP声子谱计算.md)可帮助理解数据组织，CP2K 的受力接口和单位则需分别核对。

冻结大部分基底能减少差分自由度，得到的是受限模型的局部或部分 Hessian。它适合定义清楚的吸附物局部振动近似，却会改变模式耦合和低频谱，不能直接作为完整晶体声子自由能。必要时逐步扩大活动区域，检查目标模式与热修正是否稳定；分子 RRHO 热化学也不能直接替代声子布里渊区积分。`THERMOCHEMISTRY` 的气相适用范围见[振动分析参数](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/VIBRATIONAL_ANALYSIS.html)。
