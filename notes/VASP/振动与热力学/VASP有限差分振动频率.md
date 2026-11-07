# VASP 有限差分振动频率

**适用环境：Windows、macOS、Linux（查看输入与绘图）；Linux + PBS（VASP、Phonopy 或频率计算）。**

VASP 可在内部对原子施加小位移，从受力变化计算 Γ 点动力学矩阵。以两个原子的硅原胞为例，`IBRION=6` 使用对称性减少位移任务；`IBRION=5` 则不利用这部分对称性。

## 输入与提交

案例提供 [POSCAR](../../../examples/vasp/minimal/phonon-finite-displacement/POSCAR)、[INCAR](../../../examples/vasp/minimal/phonon-finite-displacement/INCAR)、[KPOINTS](../../../examples/vasp/minimal/phonon-finite-displacement/KPOINTS)、[job.pbs](../../../examples/vasp/minimal/phonon-finite-displacement/job.pbs) 和[检查脚本](../../../examples/vasp/minimal/phonon-finite-displacement/postprocess.py)。按 [POTCAR.spec](../../../examples/vasp/minimal/phonon-finite-displacement/POTCAR.spec) 准备授权势后，加载 VASP 与 MPI 环境，执行 `qsub job.pbs`。

关键参数为：

```text
IBRION = 6
NSW = 1
POTIM = 0.015
NFREE = 2
EDIFF = 1E-8
```

`POTIM` 在这一任务中是原子位移幅度，单位 Å；`NFREE=2` 使用正负位移做中心差分。`NSW=1` 用于触发振动计算，不是让位移结构弛豫一步。计算前应先优化结构，并根据目标频率检查电子与受力精度。

## 查看频率

在 `OUTCAR` 搜索 `THz`，可看到频率、波数和模式本征矢。`f/i` 标识虚频。本例的三支光学模式接近简并，另三支是接近零的整体平移模式。

本例采用小原胞与较粗电子网格，适合学习输入与频率输出。需要完整色散时应计算超胞力常数并交给 [Phonopy](VASP声子谱计算.md)；需要弹性常数时，`IBRION=6` 还需配合应变相关设置，不能把 `6` 单独理解为“弹性计算”。参数含义见 [IBRION 官方说明](https://vasp.at/wiki/IBRION)。

## 位移越小，频率就越准吗

由受力构造力常数时，例如

$$
H_{ij}\approx-\frac{F_i(\mathbf R+h\mathbf e_j)-F_i(\mathbf R-h\mathbf e_j)}{2h},
$$

中心差分的截断误差通常随 $h^2$ 减小，但若两个受力各含量级为 $\epsilon_F$ 的误差，差商中的噪声可达到量级 $\epsilon_F/h$。所以缩小 `POTIM` 需要同时保证受力精度，而不是把位移任意设小。直接用能量二阶差分还有不同的消减误差与步长依赖，不能把两种误差估计混用。

保持同一优化结构与电子设置，比较几个合理位移下的目标频率、近零模式和模式方向；必要时收紧 SCF、加密电子 k 点与截断设置，再复查位移稳定区间。只把力常数矩阵对称化或施加声学求和规则，不能补回受噪声污染的受力。操作定义见 [VASP 有限差分声子](https://vasp.at/wiki/Phonons_from_finite_differences)，正常模式与单位关系见 [Hessian 复核](../../计算化学/Hessian、正常模式与频率复核.md)。
