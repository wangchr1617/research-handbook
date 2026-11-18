# VASP 单点能与受力

**适用环境：Windows、macOS、Linux（准备输入与分析）；Linux + PBS（VASP）。**

想知道一份硅结构是否还需要弛豫，可以先保持坐标不动，收敛电子态再看原子受力。这个两原子案例还会保存电荷密度和波函数，可作为后续分析的输入。

## 一、固定硅原胞，只求电子态

| 文件 | 本例内容 |
| --- | --- |
| [POSCAR](../../../examples/vasp/minimal/single-point/POSCAR) | 晶胞、元素顺序与分数坐标 |
| [INCAR](../../../examples/vasp/minimal/single-point/INCAR) | PBE 静态计算参数 |
| [KPOINTS](../../../examples/vasp/minimal/single-point/KPOINTS) | 3×3×3 Γ 中心均匀网格 |
| [POTCAR.spec](../../../examples/vasp/minimal/single-point/POTCAR.spec) | 需要从授权库准备的元素势 |

VASPKIT `101` 的 `ST` 可生成静态计算骨架，`102` 可生成 k 网格，`104` 可显式选择元素势。本例提供 [vaspkit-potcar.in](../../../examples/vasp/minimal/single-point/vaspkit-potcar.in)；使用前需配置自己的授权势库，并检查生成的 `POTCAR` 是否与 `POSCAR` 元素顺序一致。

本例主要参数为：

```text
ENCUT = 350
EDIFF = 1E-7
IBRION = -1
NSW = 0
ISMEAR = 0
SIGMA = 0.05
LREAL = .FALSE.
```

`NSW=0` 不推进离子；`EDIFF` 控制电子自洽精度；`ENCUT` 的单位为 eV。本例同时保存 `CHGCAR` 和 `WAVECAR`，便于衔接后续分析；不需要这些文件时可关闭 `LCHARG`、`LWAVE`。

## 二、用日志与结果文件交叉验收

将 [job.pbs](../../../examples/vasp/minimal/single-point/job.pbs) 和 [postprocess.py](../../../examples/vasp/minimal/single-point/postprocess.py) 一并放入工作目录，加载 VASP、MPI 和 Python 环境后执行：

```bash
qsub job.pbs
```

后处理从 `vasprun.xml` 汇总能量、受力与电子步数，再在 `OUTCAR` 检查 `EDIFF is reached` 和结束计时。单点的验收条件是电子收敛且获得完整的能量、力等结果。若力明显偏大，应回查结构和参数，或从同一构型开始优化。也应查看 `OUTCAR` 与 `OSZICAR`，确认没有电子迭代达到上限、结构异常或不合理占据。

`F` 是当前展宽方案下的电子自由能，`E0` 是向零展宽外推的能量，不能不加区分地混用，见 [OSZICAR 说明](https://vasp.at/wiki/OSZICAR)。比较结构能量时保持泛函、势、截断能、采样和能量定义一致。

该小案例的粗网格用于快速学习流程；正式计算需针对能量差、受力等目标量测试截断能与 k 点收敛。后续可进入[原子位置优化](VASP原子位置优化.md)、[晶胞优化](VASP晶胞优化.md)或[能带计算](../电子结构与成键/VASP能带计算.md)。
