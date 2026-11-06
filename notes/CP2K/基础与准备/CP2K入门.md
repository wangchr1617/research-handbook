# CP2K 入门

**适用环境：通用（输入格式）；Linux + PBS（提交计算）。**

CP2K 的输入按段组织。每段以 `&名称` 开头，以 `&END 名称` 结束；段内关键词每行一个，嵌套层级决定参数的含义。建议先用 [Multiwfn 生成骨架](用Multiwfn生成CP2K输入文件.md)，再对照具体任务理解与修改。

## 看懂输入的骨架

```text
&GLOBAL
  PROJECT water
  RUN_TYPE ENERGY_FORCE
  PRINT_LEVEL LOW
&END GLOBAL
&FORCE_EVAL
  METHOD Quickstep
  &DFT
    # 基组与势文件、网格、电子自洽、交换关联泛函
  &END DFT
  &SUBSYS
    # 晶胞、原子坐标、各元素的基组与势
  &END SUBSYS
&END FORCE_EVAL
```

`GLOBAL` 管任务名、计算类型和输出级别；`FORCE_EVAL` 定义电子结构与受力计算；`MOTION` 控制优化或动力学。示意骨架省略了具体参数，完整可运行输入见[水分子单点案例](../../../examples/cp2k/minimal/single-point/cp2k.inp)。

`PROJECT` 决定输出文件前缀。结构可以写在 `SUBSYS/COORD` 内，也可用 `SUBSYS/TOPOLOGY` 引用外部 XYZ。XYZ 不包含可靠的周期性晶胞定义，因此仍需正确设置 `CELL`；周期性同时涉及晶胞与泊松求解器，不能只改一处。

## 按计算类型阅读

| 任务 | `RUN_TYPE` | 笔记 |
| --- | --- | --- |
| 单点能与受力 | `ENERGY_FORCE` | [单点能与受力](../结构优化/CP2K单点能与受力.md) |
| 固定晶胞优化原子 | `GEO_OPT` | [几何优化](../结构优化/CP2K几何优化.md) |
| 优化晶胞与原子 | `CELL_OPT` | [晶胞优化](../结构优化/CP2K晶胞优化.md) |
| 第一性原理分子动力学 | `MD` | [AIMD](../动力学与反应/CP2K分子动力学.md) |
| 分子简谐振动 | `VIBRATIONAL_ANALYSIS` | [振动频率](../动力学与反应/CP2K振动频率.md) |
| 反应路径与势垒 | `BAND` | [NEB 过渡态搜索](../动力学与反应/CP2K过渡态搜索.md) |

电子计算遇到收敛问题时，参见[自洽收敛](CP2K自洽收敛.md)；多结构数据生成与汇总见[批量计算](../批量计算与训练数据/CP2K批量计算.md)。

## 单位与计算精度

CP2K 不同关键词的默认单位不同，不能统一当作原子单位。例如 `COORD` 坐标默认为 Å，`MGRID/CUTOFF` 默认为 Ry，`MD/TIMESTEP` 默认为 fs，输出总能常为 Hartree。以对应版本的关键词手册与输出表头为准；支持单位的关键词可显式指定，如 `EXTERNAL_PRESSURE [bar] 0`。

常见换算为 $1\,\mathrm{Ha}\approx27.2114\,\mathrm{eV}$，$1\,\mathrm{Bohr}\approx0.529177\,\mathrm{Å}$，$1\,\mathrm{bar}=10^5\,\mathrm{Pa}$。坐标单位参见 [COORD 手册](https://manual.cp2k.org/trunk/CP2K_INPUT/FORCE_EVAL/SUBSYS/COORD.html)。

基组控制原子轨道展开，`CUTOFF` 和 `REL_CUTOFF` 控制密度网格，k 点控制周期体系的布里渊区采样。它们需要分别收敛，不能用提高一个参数代替另一个。最小案例采用较小体系和短任务，正式计算应针对所关心的能量差、受力或压力确定精度。

## 提交与检查

各计算笔记都链接配套输入与 `job.pbs`。在集群加载 CP2K 和 MPI 环境，确认可找到基组、势文件后执行 `qsub job.pbs`。PBS 的资源语法按集群配置调整，申请核数与 MPI/OpenMP 配置应一致。

检查结果时区分电子自洽、任务自身的收敛，以及程序正常结束。优化需要确认优化收敛，MD 需要确认到达计划步数；单独看到 `PROGRAM ENDED` 或最后一行能量，都不足以证明目标计算成功。
