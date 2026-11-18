# VASP 杂化泛函 HSE06

**适用环境：Linux + PBS（支持杂化泛函的 VASP）；Windows / macOS / Linux 可绘图。**

硅的 PBE 带隙算完后，想知道短程精确交换会把带边拉开多少，可以先保留原胞和 k 网格，换成 HSE06 重新收敛。仓库案例先做这个同网格对照，正式画路径前再解决采样。

## 一、用 PBE 波函数启动同网格 HSE06

[硅最小案例](../../../examples/vasp/minimal/hybrid-hse06)提供 [POSCAR](../../../examples/vasp/minimal/hybrid-hse06/POSCAR)、[KPOINTS](../../../examples/vasp/minimal/hybrid-hse06/KPOINTS)、[PBE 参数](../../../examples/vasp/minimal/hybrid-hse06/INCAR.pbe)与 [HSE06 参数](../../../examples/vasp/minimal/hybrid-hse06/INCAR.hse06)。采用两原子原胞、450 eV 和 `3×3×3` 网格。HSE06 的定义包含：

```text
LHFCALC = .TRUE.
GGA = PE
AEXX = 0.25
HFSCREEN = 0.2
```

`HFSCREEN` 的单位为 Å⁻¹。任意改动交换比例或屏蔽参数后，就不再是标准 HSE06。本例采用阻尼轨道优化 `ALGO = Damped`，`TIME = 0.4` 是优化参数，不是物理时间步长。

准备授权 PBE Si `POTCAR`，安装 [依赖](../../../examples/vasp/minimal/hybrid-hse06/requirements.txt)，加载 VASP 后提交 [PBS 作业](../../../examples/vasp/minimal/hybrid-hse06/job.pbs)：

```bash
qsub job.pbs
```

[run.py](../../../examples/vasp/minimal/hybrid-hse06/run.py)先完成 PBE，再以其波函数初始化 HSE06，随后重新自洽优化。PBE `WAVECAR` 只提供初始轨道；HSE06 的非局域交换依赖轨道，第二步必须检查自身的收敛。两阶段均检查电子收敛；[后处理](../../../examples/vasp/minimal/hybrid-hse06/postprocess.py)核对实际交换参数和相同 k 点上的占据、未占据本征值。[plot.py](../../../examples/vasp/minimal/hybrid-hse06/plot.py)生成对照图。

## 二、比较采到的带边，再决定是否加密

![硅的 PBE 与 HSE06 采样网格带隙](../assets/si-hse-gap.png)

本例 PBE、HSE06 的采样网格带隙分别为 0.6890、1.4436 eV，在这组采样点上相差约 0.7546 eV。若两种方法的极值出现在不同 k 点，报告时应分别给出带边位置。这里只在同一粗网格上寻找价带顶与导带底，可能漏过真正带边，不能把数值直接当作收敛的间接带隙或实验光学带隙。

绘制 HSE06 路径能带时，需采用适合杂化泛函的自洽/零权重路径或其他受支持方案，而非把 `ICHARG = 11` 的 PBE 输入机械替换为 HSE06。缺陷、磁性及金属体系还需另外测试初态和收敛算法。比较结构或反应能时，始终在同一泛函下保持一致精度。

参考：[VASP 杂化泛函列表](https://vasp.at/wiki/index.php/List_of_hybrid_functionals)、[官方杂化泛函教程](https://vasp.at/tutorials/latest/hybrids/part1/)。
