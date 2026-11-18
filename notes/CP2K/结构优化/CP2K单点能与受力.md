# CP2K 单点能与受力

**适用环境：Windows、macOS、Linux（查看和准备输入）；Linux + PBS（提交计算）。**

要给一份固定的水分子坐标计算能量和力，可以选 `ENERGY_FORCE`。这次计算不会移动原子。先核对输出里每个受力分量与哪个原子对应，再决定结果是用于比较结构、启动优化，还是生成训练标签。

## 一、把孤立水分子的边界和任务写清

先按[Multiwfn 输入生成方法](../基础与准备/用Multiwfn生成CP2K输入文件.md)建立计算骨架，任务选择 `Energy + force`。案例提供 [structure.xyz](../../../examples/cp2k/minimal/single-point/structure.xyz)、[cp2k.inp](../../../examples/cp2k/minimal/single-point/cp2k.inp)、[job.pbs](../../../examples/cp2k/minimal/single-point/job.pbs) 和[结果检查脚本](../../../examples/cp2k/minimal/single-point/postprocess.py)。

本例的主要设置如下：

| 设置 | 本例选择 | 用途 |
| --- | --- | --- |
| `RUN_TYPE` | `ENERGY_FORCE` | 同时计算能量和原子受力 |
| 泛函、基组 | PBE、DZVP-MOLOPT-SR-GTH | 基础 DFT 方案 |
| `PERIODIC` | `NONE` | 晶胞和静电边界都设为非周期 |
| `POISSON_SOLVER` | `MT` | 孤立体系的静电处理 |
| `CUTOFF`、`REL_CUTOFF` | 900、80 Ry | 本例网格精度 |
| `EPS_SCF` | `1E-7` | 电子迭代收敛阈值 |

`&FORCE_EVAL/PRINT/FORCES ON` 将受力写入输出。本例用 OT 求解闭壳层分子；对金属、较小带隙或需要展宽的体系，参见[SCF 设置](../基础与准备/CP2K自洽收敛.md)。

## 二、分别检查电子能、逐原子力与合力

把案例文件放在同一工作目录，按集群说明加载 CP2K，确认数据目录中有 `BASIS_MOLOPT` 与 `GTH_POTENTIALS`，执行：

```bash
qsub job.pbs
```

运行前安装案例 `requirements.txt` 中的依赖。作业脚本会在计算后调用 `postprocess.py`，生成 `results.json`；同时可打开 `cp2k.out`，核对 SCF 收敛、`ENERGY| Total FORCE_EVAL` 能量、原子受力和正常结束标记。

本例原始能量单位为 Hartree，受力单位为 Hartree/Bohr，XYZ 坐标单位为 Å。后处理将能量与力转换为 eV、eV/Å，并检查全部原子力及其合力。三原子应各有一行、每行三个分量，需与坐标文件的 O、H、H 顺序一致。后处理先逐分量求和再取模，作为孤立体系平移对称性的数值检查。最大原子力则是分别取三个原子的力模后，再找最大值。即使合力接近零，单个原子仍可能受力很大。判断几何是否到达驻点时应另看逐原子力。

同一体系的能量差必须使用一致的泛函、势、基组、边界与数值精度。网格参数只是小案例的起点，正式计算应测试能量差和受力随参数的变化。
