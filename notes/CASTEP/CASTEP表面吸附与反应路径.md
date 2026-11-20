# CASTEP 表面吸附与反应路径

想知道 H 是否容易停在某个表面位点，先核对洁净面、吸附态和供氢参考。若已找到两个位点，还要沿路径搜索它们之间的鞍点。下面用同一套薄片建模思路串起这两步。

## 一、先配平吸附比较的参考态

1. 从已优化的体相切出薄片，记录 Miller 指数、终止面、层数、真空和横向面积。优先采用法向独立的晶胞，表面平行方向取合适的 k 网格，法向通常取一个 k 点。用逐步增加层数与真空的方式核对目标能量差。
2. 弛豫干净表面与吸附态时，保持横向晶胞、固定层和电子设置一致。对单侧吸附记录覆盖度和法向偶极处理，按所用 CASTEP 版本核对边界及修正。
3. 统一参考态。以气相物种 A 作参考时，$E_{\rm ads}=E_{\rm slab+A}-E_{\rm slab}-E_{\rm A}$，本定义下负值表示相对分离参考放热。气相物种需要足够大的真空盒及正确自旋态；若 A 来自分子解离，按配平后的分数计量。
4. 同终止、对称且化学计量一致的薄片可用 $\gamma=(E_{\rm slab}-N E_{\rm bulk})/(2A)$。若两面终止不同，能量差对应两面贡献之和。非化学计量表面还需引入相关元素化学势。

仓库的 [H/Al(111) 案例](../VASP/表面与反应/VASP吸附能计算.md)以半个 H₂ 作为每个 H 的参考。若换成 CASTEP，保留这个计量关系，用自己的赝势和精度重新计算各态，再比较位点或覆盖度。

## 二、从两个已弛豫位点准备 NEB 路径

先分别优化初态和末态，两端点保持相同的晶胞、原子序号与固定原子约束，并选取与目标迁移通道相符的周期映像（最近映像可作为单跳的起点；若需经过中间位点或绕开障碍，则按实际路径选择）。在 CASTEP 中设置 NEB 任务时，需在 `.param` 中指定 `TASK : TRANSITIONSTATESEARCH` 和 `TSSEARCH_METHOD : NEB`，在 `.cell` 中提供初态、`POSITIONS_ABS_PRODUCT` 和 `POSITIONS_ABS_INTERMEDIATE`（中间构型用于为分段插值指定一处初始路径锚点），详见 [CASTEP NEB 接口](https://castep-docs.github.io/castep-docs/documentation/Transition_State_Search/neb/)。路径生成后，先逐帧检查键长和原子短接触，确认无误再启动路径优化。

查看 `.ts` 与主输出，检查每张图像的构型、路径连续性和力。加密图像或改变初始路径后复查最高点，比较相对于初态与末态的势垒。若研究化学反应的过渡态，可再检查局部振动模式及其位移方向。

参考 [CASTEP NEB 接口](https://castep-docs.github.io/castep-docs/documentation/Transition_State_Search/neb/)、[官方 NEB 教程](https://castep-docs.github.io/workshop/tutorials/NEB/neb_tutorial/)和[表面能的参考态](../VASP/表面与反应/VASP表面能与薄膜厚度.md)。
