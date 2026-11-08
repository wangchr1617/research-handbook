# CASTEP 表面吸附与反应路径

以一个吸附物在周期薄片上的吸附和迁移为例。先验证干净表面和吸附参考态，再计算路径。吸附能、表面能与迁移势垒所用的能量差各自有明确的模型和计量关系。

## 薄片、真空与吸附能

1. 从已优化的体相切出薄片，记录 Miller 指数、终止面、层数、真空和横向面积。优先采用法向独立的晶胞，表面平行方向取合适的 k 网格，法向通常取一个 k 点。用逐步增加层数与真空的方式核对目标能量差。
2. 弛豫干净表面与吸附态时，保持横向晶胞、固定层和电子设置一致。对单侧吸附记录覆盖度和法向偶极处理，按所用 CASTEP 版本核对边界及修正。
3. 统一参考态。以气相物种 A 作参考时，$E_{\rm ads}=E_{\rm slab+A}-E_{\rm slab}-E_{\rm A}$，本定义下负值表示相对分离参考放热。气相物种需要足够大的真空盒及正确自旋态；若 A 来自分子解离，按配平后的分数计量。
4. 同终止、对称且化学计量一致的薄片可用 $\gamma=(E_{\rm slab}-N E_{\rm bulk})/(2A)$。若两面终止不同，能量差对应两面贡献之和。非化学计量表面还需引入相关元素化学势。

## 从两个吸附位点得到迁移势垒

先优化初态、末态。两端点用相同晶胞、原子序号与固定原子约束。沿真实最短路径处理跨周期边界的坐标。CASTEP 的 NEB 任务在 `.param` 中设置 `TASK : TRANSITIONSTATESEARCH` 和 `TSSEARCH_METHOD : NEB`。在 `.cell` 中提供初态、`POSITIONS_ABS_PRODUCT` 和 `POSITIONS_ABS_INTERMEDIATE`，中间结构应避开直线插值产生的原子重叠。

查看 `.ts` 与主输出，检查每张图像的构型、路径连续性和力。加密图像或改变初始路径后复查最高点，比较相对于初态与末态的势垒。若研究化学反应的过渡态，可再检查局部振动模式及其位移方向。

参考 [CASTEP NEB 接口](https://castep-docs.github.io/castep-docs/documentation/Transition_State_Search/neb/)、[官方 NEB 教程](https://castep-docs.github.io/workshop/tutorials/NEB/neb_tutorial/)和[表面能的参考态](../VASP/表面与反应/VASP表面能与薄膜厚度.md)。
