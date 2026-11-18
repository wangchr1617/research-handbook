# VASP 密度泛函微扰振动频率

**适用环境：Windows、macOS、Linux（查看输入与绘图）；Linux + PBS（VASP、Phonopy 或频率计算）。**

硅原胞的有限差分结果会随位移幅度变化。要用另一种求导方式交叉检查，可在同一结构和电子设置上做密度泛函微扰理论（DFPT），通过线性响应求动力学矩阵。VASP 的 `IBRION=8` 使用对称性，`IBRION=7` 不使用这部分对称性。两者均属于 DFPT。

## 一、保留电子模型，改用线性响应

以两个原子的硅原胞为例，文件包括 [POSCAR](../../../examples/vasp/minimal/phonon-dfpt/POSCAR)、[INCAR](../../../examples/vasp/minimal/phonon-dfpt/INCAR)、[KPOINTS](../../../examples/vasp/minimal/phonon-dfpt/KPOINTS)、[job.pbs](../../../examples/vasp/minimal/phonon-dfpt/job.pbs) 和[检查脚本](../../../examples/vasp/minimal/phonon-dfpt/postprocess.py)。按 [POTCAR.spec](../../../examples/vasp/minimal/phonon-dfpt/POTCAR.spec) 准备授权势后，加载 VASP 与 MPI 环境并提交 `qsub job.pbs`。

```text
IBRION = 8
NSW = 1
EDIFF = 1E-8
```

两份案例的 POSCAR、KPOINTS 与势清单相同。DFPT 输入把 `IBRION` 从 6 改为 8，并移除有限差分的 `POTIM` 与 `NFREE`。仍需足够精确的电子自洽，并确认当前泛函与计算设置受该功能支持，见 [IBRION 官方说明](https://vasp.at/wiki/IBRION)。

使用 `IVDW` 原子对或多体色散方案时，还需核对完整模型是否支持 DFPT；当前 [IVDW 说明](https://vasp.at/wiki/IVDW)列出这类校正在 DFPT 声子中的限制。需要其受力贡献时，可按支持的[有限差分频率](VASP有限差分振动频率.md)流程处理，不能只让响应步骤忽略该项。

## 二、用相同自由度比较 Γ 点频率

在 `OUTCAR` 搜索 `THz` 读取频率。后处理将 `f/i` 标记的频率记为负数，本例要求六个模式且最小值不低于 −0.001 THz。这个检查阈值对应硅案例；其他体系应结合模式方向和目标精度判断。本例在相同结构、势、截断能和 k 网格下，可与[有限差分案例](VASP有限差分振动频率.md)比较：三支光学模式应接近，平移模式应接近零。方法间的差异还受有限差分步长、电子阈值等影响。

原胞计算只给出相应 Γ 点信息。若要通过超胞 DFPT 与 Phonopy 得到色散，应对超胞计算响应，再使用 Phonopy 的 VASP 力常数接口读取结果；不能直接将两个原子的 Γ 点矩阵当作长程力常数。
