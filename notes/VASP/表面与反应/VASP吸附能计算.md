# H 在 Al(111) 上的吸附能

**适用环境：Linux + PBS（VASP）；Windows / macOS / Linux 可绘图。**

以 H/Al(111) 为例，吸附能定义为

$$E_\mathrm{ads}(n)=E(\mathrm{slab}+n\mathrm H)-E(\mathrm{slab})-\frac n2E(\mathrm H_2).$$

这里以气相 H₂ 为参考，负值表示放热；改用孤立 H 原子参考会得到不同数值。

## 输入与提交

[最小案例](../../../examples/vasp/minimal/adsorption-energy)包含 [洁净表面](../../../examples/vasp/minimal/adsorption-energy/POSCAR.clean)、[半覆盖](../../../examples/vasp/minimal/adsorption-energy/POSCAR.half)、[全覆盖](../../../examples/vasp/minimal/adsorption-energy/POSCAR.full)和 [H₂](../../../examples/vasp/minimal/adsorption-energy/POSCAR.h2)。两表面位点晶胞含 8 个 Al，固定全部 Al，仅优化 H；0.5 ML 与 1 ML 分别对应 1、2 个 H。

使用 [INCAR.clean](../../../examples/vasp/minimal/adsorption-energy/INCAR.clean)、[INCAR.ads](../../../examples/vasp/minimal/adsorption-energy/INCAR.ads)、[INCAR.h2](../../../examples/vasp/minimal/adsorption-energy/INCAR.h2)，以及 [薄膜 k 网格](../../../examples/vasp/minimal/adsorption-energy/KPOINTS.slab)和 [分子 k 网格](../../../examples/vasp/minimal/adsorption-energy/KPOINTS.h2)。准备授权的 `potentials/Al/POTCAR`、`potentials/H/POTCAR`，安装 [依赖](../../../examples/vasp/minimal/adsorption-energy/requirements.txt)，加载 VASP 后提交 [job.pbs](../../../examples/vasp/minimal/adsorption-energy/job.pbs)：

```bash
qsub job.pbs
```

[run.py](../../../examples/vasp/minimal/adsorption-energy/run.py)顺序计算四个状态，[postprocess.py](../../../examples/vasp/minimal/adsorption-energy/postprocess.py)核对电子与几何收敛、固定原子位移及参考态，再用 [plot.py](../../../examples/vasp/minimal/adsorption-energy/plot.py)绘图。能量统一取最终 XML 的 `e_0_energy`；金属高斯展宽的这一能量仍需检查展宽收敛。

## 读图与改进

![H/Al(111) 的每 H 吸附能](../assets/al-h-adsorption.png)

450 eV、薄膜 `4×7×1` 网格下，每 H 吸附能分别约 +0.2387、+0.3150 eV。两者相对于 H₂ 均吸热。该模型固定了理想基底，只比较 fcc 位点；实际研究应优化允许弛豫的表层，并检查吸附位点、层数、横向尺寸、k 点与自旋态。

VASPKIT 可辅助构建薄膜，VESTA 可检查位点与周期镜像；能量差的参考态、化学计量与归一化仍需自行明确。
