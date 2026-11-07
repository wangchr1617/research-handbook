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

`CUTOFF` 控制最细实空间网格，`REL_CUTOFF` 还影响高斯乘积分配到哪一级网格；只增加前者不代表后者已经合适。怎样区分积分、SCF、基组与响应误差，见[数值积分与性质收敛](../../计算化学/数值积分网格与性质收敛.md)。

## 基组与势要怎样配套

`DFT/BASIS_SET_FILE_NAME` 指定基组数据文件，每个 `KIND/BASIS_SET` 选择其中的条目；势文件与 `KIND/POTENTIAL` 也分别指定。以 PBE 氧原子的常见 GPW 配套为例，`DZVP-MOLOPT-GTH` 对应 `GTH-PBE-q6`，`q6` 表示 6 个显式价电子，不是原子电荷。改变芯大小时，基组与电子数均需重新核对。

`MOLOPT-SR` 等短程变体减少弥散性，常有利于凝聚相效率；阴离子、表面外侧电子和响应性质还需检查目标量。不同数据文件的可用条目随版本变化，应保存实际条目和数据版本，不能仅凭名称补全定义。原理见[基组与弥散函数](../../计算化学/基组、极化函数与弥散函数.md)，文件角色见 [CP2K 基组说明](https://manual.cp2k.org/trunk/methods/dft/basis_sets.html)。

从 GTH 价电子 GPW 转为全电子模型时，需要同时处理方法、全电子基组与核势，见 [GAPW 全电子计算](../电子结构与响应/CP2KGAPW全电子计算.md)；单独删除势或提高 `CUTOFF` 无法完成这一转换。

## 小晶胞的 k 点与功能兼容

小原胞、金属以及能带色散较强的体系，通常需要显式 k 点积分。对已配置对角化 SCF 的表面单点，可在 `&DFT` 中加入下面的采样片段；`4×4×1` 只是二维表面的教学起点，不是收敛结论：

```text
&KPOINTS
  SCHEME MONKHORST-PACK 4 4 1
  WAVEFUNCTIONS COMPLEX
&END KPOINTS
```

最后一维对应本例的真空方向。改变晶胞朝向后按真实周期方向设置；晶体三维采样另行收敛。能量差、受力、压力、DOS 与带边可能需要不同的网格密度，电子展宽和绘图展宽都不能代替采样检查。SCF 的积分网格与 `DFT/PRINT/BAND_STRUCTURE` 的高对称路径用途不同，不能把一条能带路径当成布里渊区积分。参数见 [KPOINTS 手册](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/KPOINTS.html)。

在 CP2K 2026.2 中，标准对角化支持 k 点，标准 OT 不支持这一路径；杂化泛函则使用相应的 RI-HFXk 实现。其他功能需分别核对兼容性：例如 k 点 DFT+U 的 Mulliken 路线、波函数导出和原生 STM，不能直接照搬 Γ 点设置。

选择组合前查[功能兼容表](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/k-points.html)与目标模块手册。“支持 k 点”说明存在相应计算路径，具体功能组合仍有条件；另一方面，该版本已支持 k 点路径的波函数外推，也不必因旧资料而一概关闭。

用 Γ 点超胞与原胞 k 网格交叉检查时，应保持相同物理结构、方法、占据和等效采样。对原胞的整数复制，超胞 Γ 点折回原胞形成的是特定网格；偶数 Monkhorst–Pack 网格可能带半格偏移，不能只按点数宣称完全等价。分别比较每化学单元的能量、原子映射后的受力及目标物性，并核对实际 k 坐标与权重。缺陷、覆盖度或允许的长波结构变化还会破坏简单复制关系，扩胞本身也有有限尺寸效应。

2026.2 的原子空间群约化标为实验性功能。启用 `SYMMETRY T` 前，用相同积分网格下的 `SYMMETRY F`、`FULL_GRID T` 作完整网格参照，比较能量、力和应力；复杂磁序、畸变与结构演化时尤其要核对实际使用的对称操作。普通 k/−k 约化与额外的原子空间群约化也应区分，不能仅看 `SYMMETRY F` 就认为已经计算了所有点。

## 提交与检查

各计算笔记都链接配套输入与 `job.pbs`。在集群加载 CP2K 和 MPI 环境，确认可找到基组、势文件后执行 `qsub job.pbs`。PBS 的资源语法按集群配置调整，申请核数与 MPI/OpenMP 配置应一致。

检查结果时区分电子自洽、任务自身的收敛，以及程序正常结束。优化需要确认优化收敛，MD 需要确认到达计划步数；单独看到 `PROGRAM ENDED` 或最后一行能量，都不足以证明目标计算成功。
