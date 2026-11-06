# CP2K 训练数据准备

**适用环境：Linux（CP2K 标注）；Windows / macOS / Linux（结构处理与数据检查）。**

训练数据先要覆盖目标问题，再追求数量。针对晶体振动、缺陷迁移、液体或反应过程，所需的构型范围不同；相邻 AIMD 帧也不是彼此独立的样本。

## 采样与标注

可以从平衡结构附近的小位移、小应变和目标温度下的 AIMD 结构开始。扰动幅度应结合键长与研究条件选择，筛除原子重叠等不合理结构，再逐步加入模型误差大的构型。随机结构方法可参考 [RAG 原始论文](https://pubs.acs.org/doi/10.1021/acs.jpcb.0c05075)。

同一批标签应采用一致的泛函、基组、赝势及数值设置。采样阶段可以使用较低成本的方法，但最终标注仍需按能量、受力和目标应力精度检查收敛，不能将某个低截断能当作所有体系的训练标准。若训练压力或弹性相关性质，应保存并核对应力与位力的定义、符号和单位。

[批量单点案例](../../../examples/cp2k/minimal/batch-single-points)给出了两个水分子结构的实际标注流程。它们用于演示数据格式；训练势函数还需扩充采样覆盖并保留独立验证数据。PBS 操作见[批量计算笔记](CP2K批量计算.md)。

## 能量与力的单位

案例 [cp2k.inp](../../../examples/cp2k/minimal/batch-single-points/cp2k.inp)使用 `ENERGY_FORCE`，并通过 `FORCE_EVAL/PRINT/FORCES` 输出原子力。[postprocess.py](../../../examples/cp2k/minimal/batch-single-points/postprocess.py)读取总能量与力，转换成常用的 eV 和 eV/Å 后写入 ExtXYZ：

$$E[\mathrm{eV}]=E[\mathrm{Ha}]\times E_h[\mathrm{eV}],\qquad
\mathbf F[\mathrm{eV/Å}]=\mathbf F[\mathrm{Ha/Bohr}]\times E_h/a_0.$$

转换常数取自 ASE，力分量按输出原子顺序对应输入坐标。该案例没有自动平移坐标，导出的结构与实际输入一致；孤立水分子的 `pbc` 为三个 `False`。周期体系应保留完整晶胞及真实周期边界，不能照搬分子设置。

导出内容含 `energy`、`forces` 和 `config_type`，脚本会回读并核对标签。本例还检查孤立水分子的净力，超过 `0.005 eV/Å` 时停止导出；这一阈值用于小案例检查，不是所有体系的训练精度标准。还应抽查结构、元素顺序、力的量级和总力；格式可以读取，并不自动说明标签精度满足训练目标。

## AIMD 与数据划分

使用 AIMD 轨迹时，同步保存坐标、力和晶胞，并按步数或时间对齐。改变输出间隔后，不能简单按行号拼接；也不要把优化中间帧与最终能量配对。

DeePMD 数据可用仓库中的 [dp2xyz.py](../../../scripts/structure/dp2xyz.py) 转为 ExtXYZ，但转换前要确认元素映射与位力是否存在。划分训练、验证和测试集时，尽量按独立轨迹、结构族或采样条件分组，避免高度相近的相邻帧同时进入训练集和测试集。
