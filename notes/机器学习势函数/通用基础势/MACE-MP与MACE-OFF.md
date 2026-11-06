# MACE-MP 与 MACE-OFF

**适用环境：通用（原理与模型选择）。**

MACE-MP 与 MACE-OFF 使用相关架构，但训练域与参考方法不同。选择权重时先看数据与任务，再看网络大小。[MACE 架构](../等变图神经网络/MACE.md)与这些已训练模型应分别记录。

## 一、历史与开发团队

MACE-MP-0 的基础模型工作由 Ilyes Batatia、Gábor Csányi 及跨机构合作团队推进，预印本于 2023 年末公开，编号为 `2401.00096`。MACE-OFF 工作由 Dávid Péter Kovács 等与 Cambridge 及合作团队推进，2023 年发布预印本，后续正式发表于 JACS。编号年份、首发日期和期刊年份可能不同，引用时保留版本。[^mp][^off]

## 二、同一架构为什么会有不同适用域

MACE-MP-0 以 Materials Project 相关无机晶体数据为重要训练基础；MACE-OFF23 面向有机分子，其训练使用 SPICE-α 相关数据和指定量化计算口径。不同系列的元素、能量基准和化学环境不应混用。[^mp][^models]

| 需求 | 首先核对 |
| --- | --- |
| 无机晶体弛豫、缺陷或熔体 | MP 系列具体权重的训练域与参考泛函 |
| 中性有机分子及分子间作用 | OFF 具体版本的元素、电荷域与色散处理 |
| 含水界面、盐、带电体系 | 多域覆盖、长程项和电荷态是否明确支持 |

这张表是核对路线，不是适用性保证。新的 MP、MPA、OMAT 等后缀还可能标识不同数据或训练过程，不能都叫作同一套 MACE-MP-0。

## 三、短程模型与色散

有限截断神经网络可以在训练范围内拟合部分分子间相互作用，但不自动获得无限距离的正确渐近行为。添加外部色散修正前要核对训练标签已经包含什么，避免把相同贡献重复加两次。

微调时沿用一致的元素顺序、参考能与输出约定；目标标签若换泛函，先明确是在修正什么，而不是仅把新旧数据直接合并。

## 四、结果检查

记录完整权重名、版本或校验值、是否加色散、设备与精度。对目标体系比较相对能、力、曲率和关键构型；有机体系还需检查分子间能量曲线及电荷适用域。模型卡与调用接口见[官方基础模型文档](https://mace-docs.readthedocs.io/en/latest/guide/foundation_models.html)。

## 实践：两类权重在代码中明确选择

```python
from ase.build import bulk, molecule
from mace.calculators import mace_mp, mace_off
si = bulk("Si", "diamond", a=5.43)
si.calc = mace_mp(model="small", device="cpu", default_dtype="float64")
print("Si total energy (eV):", si.get_potential_energy())
water = molecule("H2O")
water.calc = mace_off(model="small", device="cpu", default_dtype="float64")
print("H2O total energy (eV):", water.get_potential_energy())
```

两次 `small` 属于不同系列；它们既不是同一个 checkpoint，也不具有可直接比较的绝对能量基准。调用实现见[MACE calculators 源码](https://github.com/ACEsuit/mace/blob/main/mace/calculators/foundations_models.py)。示例不另外叠加色散，若改变该选项要重新说明参考标签与总能组成。

完整[MACE 硅案例](../../../examples/machine-learning/atomistic-models/mace_silicon.py)保存实际权重的 SHA256，不只依赖会滚动变化的默认模型名。若已有本地权重，可通过 `--model /path/to/model` 运行同一套检查。

## 以有机分子间能量曲线为例

验证 OFF 对水二聚体或有机分子间作用时，对一组固定相对取向扫描分子间距离，计算 $E_{AB}-E_A-E_B$。三个计算需使用相同权重、精度和电子态约定，单体几何保持与二聚体中相同，否则混入形变能。

远离时相互作用应逐渐趋近该模型的渐近极限；局域模型截断后可能完全没有相互作用。若在此基础上额外加 D3，先核对训练标签、模型卡和官方建议，不能把开关打开后更深的势阱自动认为更准确。

## 参考资料

[^mp]: I. Batatia et al. A foundation model for atomistic materials chemistry. [预印本与版本历史](https://arxiv.org/abs/2401.00096)。
[^off]: D. P. Kovács et al. MACE-OFF: Transferable Short Range Machine Learning Force Fields for Organic Molecules. [预印本](https://arxiv.org/abs/2312.15211)、[JACS 论文](https://doi.org/10.1021/jacs.4c07099)。
[^models]: ACEsuit. [MACE-OFF 权重和数据说明](https://github.com/ACEsuit/mace-off)、[基础模型文档](https://mace-docs.readthedocs.io/en/latest/guide/foundation_models.html)。

返回[分类导航](README.md)或[专题首页](../README.md)。
